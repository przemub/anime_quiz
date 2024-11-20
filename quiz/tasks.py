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
import abc
import time
from urllib.error import HTTPError

import animelyrics
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from first import first

from quiz.animethemes import request_anime, AnimeThemesTryLater

logger = get_task_logger(__name__)

MISSING_IN_ANIMETHEMES = 1


class TaskBase(abc.ABC):
    name: str

    def __init__(self):
        super().__init__()

    def after_return(self, _status, _retval, _task_id, _args, _kwargs, _einfo):
        pass

    def run(self, **kwargs):
        raise NotImplementedError()


class GetUserThemesTaskBase(TaskBase):
    name = "get_user_themes_task"

    def __init__(self):
        super().__init__()
        self.started_key = None

    def after_return(self, _status, _retval, _task_id, _args, _kwargs, _einfo):
        if self.started_key:
            cache.delete(self.started_key)

    def run(self, *, user, themes):
        self.started_key = f"started_user_{user}"
        cache.set(self.started_key, True, 60 * 60)

        count, total = 1, len(themes)
        new_themes = []
        while themes:
            for anime_id, anime_title in themes:
                anime_key = f"themes-{anime_id}"

                # Check if the anime has not been fetched in the meantime
                if (
                    cache.get(anime_key, None) is not None
                    and cache.ttl(anime_key) >= settings.NEAR_CACHE_MISS_SECS
                ):
                    continue

                try:
                    result = request_anime(anime_id, anime_title)

                    # Expire in a month
                    cache.set(
                        anime_key,
                        result,
                        60 * 60 * 24 * 30,
                    )
                    logger.info(f"{count}/{total}")
                    count += 1

                    for theme in result:
                        GetLyricsTask().delay(theme=theme)
                except AnimeThemesTryLater as e:
                    new_themes.append((anime_id, anime_title))
                    logger.info(e.message())
                    time.sleep(e.retry_after)

            themes = new_themes
            new_themes = []


def find_cached_lyrics(theme) -> str:
    cache_key = f"lyrics-{theme['song']['id']}"

    return cache.get(cache_key, None)


class TryAfterException(Exception):
    """The exception raised when there is a 429 returned from the API."""

    def __init__(self, retry_after: int):
        """
        :param retry_after: Seconds to wait requested by the server.
        """
        self.retry_after = retry_after

    def message(self):
        return f"Throttled. Trying again in {self.retry_after} seconds."


class GetLyricsTaskBase(TaskBase):
    name = "get_lyrics_task"

    def run(self, *, theme):
        cache_key = f"lyrics-{theme['song']['id']}"

        queries = [
            f'"{theme["anime_title"]}" "{theme["song"]["title"]}"',
            f"{theme['anime_title']} {theme['song']['title']}",
            f'"{theme["song"]["title"]}"',
            theme["song"]["title"]
        ]

        def run_query(query: str):
            try:
                return animelyrics.search_lyrics(query, lang="jp")
            except animelyrics.NoLyricsFound:
                return None
            except HTTPError as he:
                if he.code == 429:
                    return "Not found yet"
                raise Exception("Failed to query lyrics") from he

        lyrics = first(run_query(q) for q in queries) or "Not found"
        lyrics = lyrics.replace("\n", "<br>")

        cache.set(cache_key, lyrics, 60 * 60 * 24 * 30)

        return lyrics


if settings.TASK_BACKEND == "celery":
    from anime_quiz.celery import app


    class GetLyricsTask(GetLyricsTaskBase, app.Task):
        pass


    class GetUserThemesTask(GetUserThemesTaskBase, app.Task):
        pass


    app.register_task(GetLyricsTask())
    app.register_task(GetUserThemesTask())

elif settings.TASK_BACKEND == "gcp":
    from quiz.gcp import make_gcp_task
    from django_cloud_tasks.tasks import task

    GetLyricsTask = make_gcp_task(GetLyricsTaskBase)
    GetUserThemesTask = make_gcp_task(GetUserThemesTaskBase)
    task.register(GetLyricsTask)
    task.register(GetUserThemesTask)
else:
    raise ValueError("Unsupported task backend")
