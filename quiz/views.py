import random as random_module

import animethemes_dl.parsers as parsers
from animethemes_dl import OPTIONS as ANIMETHEMES_OPTIONS
from django.core.cache import cache
from django.shortcuts import render
from django.views.generic.base import View


random = random_module.SystemRandom()


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
        print(key)
        themes_cache = cache.get(key, None)
        if themes_cache is not None:
            return themes_cache

        ANIMETHEMES_OPTIONS["statuses"] = statuses

        for key in ANIMETHEMES_OPTIONS["filter"]:
            ANIMETHEMES_OPTIONS["filter"][key] = None
        ANIMETHEMES_OPTIONS["filter"]['resolution'] = 0

        themes = parsers.get_download_data(user)
        cache.set(key, themes)

        return themes

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

        themes = self._get_user_themes(random.choice(users), statuses)

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
