import random as random_module

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View

from .tasks import GetUserThemesTask

random = random_module.SystemRandom()


class TaskStatus(Exception):
    pass


class UserThemesView(View):
    ALL_STATUSES = [
        "Watching",
        "Completed",
        "On-Hold",
        "Dropped",
        None,
        "Plan to Watch",
    ]

    def _get_user_themes(self, user, statuses):
        key = f"user_themes_{user}_{'-'.join(str(s) for s in statuses)}"
        started_key = f"started_user_themes_{user}_{'-'.join(str(s) for s in statuses)}"
        themes_cache = cache.get(key, None)
        if themes_cache is not None:
            return themes_cache

        if cache.get(started_key, False):
            raise TaskStatus(f"User {user} has been already enqueued. Please wait.")
        else:
            print("aaa")
            GetUserThemesTask().delay(user, statuses)
            print("bbb")
            raise TaskStatus(f"User {user} has been enqueued now.")

    def get(self, request):
        users = request.GET.getlist("user", ["przemub"])

        default = request.GET.get("default", "yes") == "yes"
        openings = default or request.GET.get("t-op", "off") == "on"
        endings = request.GET.get("t-ed", "off") == "on"

        # Something must be enabled
        if not (openings or endings):
            openings, endings = True, False

        if default:
            statuses = [1, 2]  # Watching, completed
        else:
            statuses = []
            for i in range(1, len(self.ALL_STATUSES) + 1):
                if request.GET.get(f"l-{i}", "off") == "on":
                    statuses.append(i)

            if not statuses:
                statuses = [1, 2]

        user = random.choice(users)

        try:
            themes = self._get_user_themes(user, statuses)
        except TaskStatus as ts:
            return HttpResponse(str(ts))

        def check_if_right_type(local_theme):
            if openings and local_theme["metadata"]["themetype"].startswith(
                "OP"
            ):
                return True
            if endings and local_theme["metadata"]["themetype"].startswith(
                "ED"
            ):
                return True
            return False

        themes = list(filter(check_if_right_type, themes))
        print(len(themes))

        theme = random.choice(themes)

        artists = ", ".join(theme["metadata"]["artists"])

        context = {
            "theme": theme,
            "artists": artists,
            "users": users,
            "openings": openings,
            "endings": endings,
            "statuses": statuses,
            "all_statuses": self.ALL_STATUSES,
        }
        print(context)

        return render(request, "quiz/quiz.html", context)
