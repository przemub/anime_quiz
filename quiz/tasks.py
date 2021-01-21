import animethemes_dl.parsers as parsers
from animethemes_dl import OPTIONS as ANIMETHEMES_OPTIONS
from celery.app.control import Inspect
from celery.utils.log import get_task_logger
from django.core.cache import cache

from anime_quiz.celery import app

logger = get_task_logger(__name__)


class GetUserThemesTask(app.Task):
    name = "get_user_themes_task"

    def __init__(self):
        self.started_key = None

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self.started_key:
            cache.delete(self.started_key)

    def run(self, user, statuses):
        key = f"user_themes_{user}_{'-'.join(str(s) for s in statuses)}"
        self.started_key = f"started_{key}"

        themes_cache = cache.get(key, None)
        if themes_cache is not None:
            return themes_cache

        cache.set(self.started_key, True, 30 * 60)

        ANIMETHEMES_OPTIONS["statuses"] = statuses

        themes = parsers.get_download_data(user)
        cache.set(key, themes)

        return themes


app.tasks.register(GetUserThemesTask)
