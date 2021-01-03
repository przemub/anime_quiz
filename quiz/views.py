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
        print(users)
        theme = random.choice(self._get_user_themes(random.choice(users)))
        print(theme)

        artists = ", ".join(theme['metadata']['artists'])

        return render(request, 'quiz/quiz.html', {'theme': theme, 'artists': artists, 'users': users})
