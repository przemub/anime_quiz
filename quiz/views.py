import random

import animethemes_dl.parsers as parsers
from django.core.cache import cache
from django.shortcuts import render
from django.views.generic.base import View


class UserThemesView(View):
    def _get_user_themes(self, user):
        key = f"user_themes_{user}"
        print(key)
        themes_cache = cache.get(key, None)
        if themes_cache is not None:
            return themes_cache

        themes = parsers.get_download_data(user)
        cache.set(key, themes)

        return themes

    def get(self, request):
        users = request.GET.getlist("user", ["przemub"])
        themes = self._get_user_themes(random.choice(users))

        default = request.GET.get("default", "yes") == "yes"
        openings = default or request.GET.get("t-op", "off") == "on"
        endings = default or request.GET.get("t-ed", "off") == "on"
        print(default, openings, endings)

        # Something must be enabled
        if not (openings or endings):
            openings, endings = True, True

        def check_if_right_type(theme):
            if openings and theme['metadata']['themetype'].startswith('OP'):
                return True
            if endings and theme['metadata']['themetype'].startswith('ED'):
                return True
            return False
        themes = list(filter(check_if_right_type, themes))

        theme = random.choice(themes)

        artists = ", ".join(theme['metadata']['artists'])

        context = {
            'theme': theme,
            'artists': artists,
            'users': users,
            'openings': openings,
            'endings': endings
        }
        print(context)

        return render(request, 'quiz/quiz.html', context)
