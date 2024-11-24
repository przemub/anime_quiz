#      Copyright (c) 2021-24 Przemysław Buczkowski
#
#      This file is part of Anime Quiz.
#
#      Anime Quiz is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as
#      published by the Free Software Foundation, either version 3 of
#      the License, or (at your option) any later version.
#
#      Anime Quiz is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with Anime Quiz.  If not, see <https://www.gnu.org/licenses/>.
import json
import logging
import os
import threading
import time
from typing import NoReturn
from urllib.error import HTTPError

import animelyrics
import bugsnag
import redis
from django.conf import settings
from django.core.cache import cache
from first import first

from quiz.animethemes import request_anime, AnimeThemesTryLater

logger = logging.getLogger(__name__)


MISSING_IN_ANIMETHEMES = 1


def redis_client() -> redis.Redis:
    return redis.from_url(
        settings.QUEUE_DB,
        decode_responses=True,
        protocol=3
    )


class TaskBase:
    name: str
    _current_priority: int

    def __init__(self):
        self._client = redis_client()
        super().__init__()

    def run(self, **kwargs) -> None:
        raise NotImplementedError()

    def after_return(self, **kwargs) -> None:
        pass

    def add_tasks(self, tasks: list[tuple[dict[str, object], int]]) -> None:
        logger.info(
            f"Received tasks %s: %s",
            self.name,
            tasks
        )

        serialized_mapping = {
            json.dumps(kwargs): priority
            for kwargs, priority in tasks
        }
        self._client.zadd(self.name, serialized_mapping, lt=True)

    def listen_for_tasks(self) -> NoReturn:
        logger.info(f"Listening for tasks %s", self.name)

        while True:
            _name, serialized_kwargs, self._current_priority = self._client.bzpopmin(self.name)
            kwargs = json.loads(serialized_kwargs)

            logger.info(
                f"Executing task %s, kwargs %s, priority %s",
                self.name,
                kwargs,
                self._current_priority
            )

            try:
                self.run(**kwargs)
            except Exception as e:  # noqa
                logger.exception(
                    "Failed to execute task %s, kwargs %s!",
                    self.name,
                    kwargs
                )
                if settings.BUGSNAG is not None:
                    bugsnag.notify(
                        e,
                        metadata={
                            "task": self.name,
                            "task_kwargs": kwargs
                        }
                    )
            else:
                logger.info(
                    "Executed task %s, kwargs %s successfully!",
                    self.name,
                    kwargs
                )
            finally:
                self.after_return(**kwargs)


class GetUserThemesTask(TaskBase):
    name = "get_user_themes_task"

    def __init__(self):
        super().__init__()

    def run(self, *, mal_id, anime_title):
        anime_key = f"themes-{mal_id}"

        # Check if the anime has not been fetched in the meantime
        if (
            cache.get(anime_key, None) is not None
        ):
            logger.debug("%s already fetched", anime_title)
            return

        while True:
            try:
                result = request_anime(mal_id, anime_title)
                break
            except AnimeThemesTryLater as atl:
                logger.info(atl.message())
                time.sleep(atl.retry_after)

        # Expire in a month
        cache.set(
            anime_key,
            result,
            60 * 60 * 24 * 30,
        )

        if result:
            GetLyricsTask().add_tasks([
                ({
                    "song_id": theme["song"]["id"],
                    "anime_title": theme["anime_title"],
                    "song_title": theme["song"]["title"]
                }, self._current_priority)
                for theme in result
            ])


def find_cached_lyrics(song_id) -> str | None:
    cache_key = f"lyrics-{song_id}"

    return cache.get(cache_key, None)


class GetLyricsTask(TaskBase):
    name = "get_lyrics_task"

    def __init__(self):
        self.waiting_time = 15
        super().__init__()

    def run(self, *, song_id, anime_title, song_title):
        cache_key = f"lyrics-{song_id}"

        cached_lyrics = find_cached_lyrics(song_id)
        if cached_lyrics is not None:
            return cached_lyrics

        # Less-and-less strict Google queries
        queries = [
            f'"{anime_title}" "{song_title}"',
            f"{anime_title} {song_title}",
            f'"{song_title}"',
            song_title
        ]

        def run_query(query: str):

            while True:
                try:
                    lyrics = animelyrics.search_lyrics(query, lang="jp")
                except animelyrics.NoLyricsFound:
                    return None
                except HTTPError as he:
                    if he.code == 429:
                        logger.info("Google hates us now. Waiting for %d secs.", self.waiting_time)
                        time.sleep(self.waiting_time)
                        self.waiting_time *= 2
                        continue
                    raise Exception("Failed to query /lyrics") from he

                self.waiting_time /= 2
                return lyrics

        lyrics = first(run_query(q) for q in queries) or "Not found"
        lyrics = lyrics.replace("\n", "<br>")

        cache.set(cache_key, lyrics, 60 * 60 * 24 * 30)

        return lyrics


def listen_for_tasks():
    """
    When started from command line, listen for tasks.
    """
    tasks = [GetUserThemesTask(), GetLyricsTask()]
    threads = [threading.Thread(target=task.listen_for_tasks) for task in tasks]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anime_quiz.settings")
    django.setup()
    if settings.BUGSNAG is not None:
        bugsnag.configure(**settings.BUGSNAG)

    try:
        listen_for_tasks()
    except KeyboardInterrupt:
        pass
