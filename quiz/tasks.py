#      Copyright (c) 2021 Przemysław Buczkowski
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

import time

from celery.utils.log import get_task_logger
from django.core.cache import cache

from anime_quiz.celery import app
from quiz.animethemes import request_anime, AnimeThemesThrottled

logger = get_task_logger(__name__)

MISSING_IN_ANIMETHEMES = 1


class GetUserThemesTask(app.Task):
    name = "get_user_themes_task"

    def __init__(self):
        self.started_key = None

    def after_return(self, _status, _retval, _task_id, _args, _kwargs, _einfo):
        if self.started_key:
            cache.delete(self.started_key)

    def run(self, user, themes):
        self.started_key = f"started_user_{user}"
        cache.set(self.started_key, True, 60 * 60)

        count, total = 1, len(themes)
        new_themes = []
        while themes:
            for anime_id, anime_title in themes:
                anime_key = f"themes-{anime_id}"

                # Check if the anime has not been fetched in the meantime
                if cache.get(anime_key, None) is not None:
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
                except AnimeThemesThrottled as e:
                    new_themes.append((anime_id, anime_title))
                    logger.info(
                        f"Throttled. Trying again in {e.retry_after} seconds."
                    )
                    time.sleep(e.retry_after)

            themes = new_themes
            new_themes = []


app.tasks.register(GetUserThemesTask)
