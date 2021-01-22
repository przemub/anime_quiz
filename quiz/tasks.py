import time

from animethemes_dl import AnimeThemesTimeout
from animethemes_dl.parsers import animethemes
from animethemes_dl.parsers.dldata import parse_anime
from celery.utils.log import get_task_logger
from django.core.cache import cache

from anime_quiz.celery import app

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
                _, result = animethemes.request_anime((anime_id, anime_title))

                if isinstance(result, AnimeThemesTimeout):
                    new_themes.append((anime_id, anime_title))
                    print("Timeout. Trying again in 10 seconds.")
                    time.sleep(10)
                else:
                    anime_key = f"themes-{anime_id}"

                    result = list(parse_anime(result)) if result else MISSING_IN_ANIMETHEMES
                    # Expire in a month
                    cache.set(anime_key, result, 60 * 60 * 24 * 30)
                    print(f"{count}/{total}")
                    count += 1

            themes = new_themes
            new_themes = []


app.tasks.register(GetUserThemesTask)
