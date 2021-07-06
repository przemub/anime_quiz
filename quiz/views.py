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

import random as random_module

from animethemes_dl import OPTIONS as ANIMETHEMES_OPTIONS, MyanimelistException
from animethemes_dl.parsers.myanimelist import get_raw_mal, filter_mal
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic.base import View

from .tasks import GetUserThemesTask, MISSING_IN_ANIMETHEMES

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
        result_key = f"result_{user}_{'-'.join(str(s) for s in statuses)}"
        if result := cache.get(result_key, None):
            return result

        started_key = f"started_user_{user}"
        if cache.get(started_key, False):
            raise TaskStatus(f"User {user} has been already enqueued. Please "
                             "wait.")

        mal_key = f"user_mal_{user}"
        mal_data = cache.get(mal_key, None)
        if mal_data is None:
            mal_data = get_raw_mal(user)
            cache.set(mal_key, mal_data, 60 * 60 * 24 * 7)  # Expire in a week

        ANIMETHEMES_OPTIONS["statuses"] = statuses
        mal_data = filter_mal(mal_data)

        cache_misses = []
        cache_hits = []

        for mal_id, title in mal_data:
            anime_key = f"themes-{mal_id}"
            anime_data = cache.get(anime_key, None)
            if anime_data is None:
                cache_misses.append((mal_id, title))
            else:
                cache_hits.extend(anime_data)

        started_key = f"started_user_{user}"
        if not cache_misses:
            cache.set(result_key, cache_hits, 60 * 60 * 24 * 7)
            return cache_hits
        elif cache.get(started_key, False):
            raise TaskStatus(f"User {user} has been already enqueued. Please "
                             "wait.")
        else:
            GetUserThemesTask().delay(user, cache_misses)
            raise TaskStatus(f"User {user} has been enqueued just now.")

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

        users_shuffled = random.sample(users, len(users))
        themes = None
        alert = ""
        enqueued_users = []
        playing_user = "przemub"

        for user in users_shuffled:
            try:
                user_themes = self._get_user_themes(user, statuses)
            except TaskStatus:
                enqueued_users.append(user)
            except MyanimelistException:
                alert += f"User {user} does not exist. <br />"
            else:
                if user_themes:
                    playing_user = user
                    themes = user_themes
                else:
                    alert += f"User {user} has an empty list. <br />"

        if enqueued_users:
            plural = len(enqueued_users) > 1
            alert += f"User{'s' if plural else ''} " \
                     f"{', '.join(enqueued_users)} " \
                     f"{'have' if plural else 'has'} been enqueued.<br />" \
                     "For the time being, choosing a theme from " \
                     f"{playing_user}'s list."

            if themes is None:
                try:
                    themes = self._get_user_themes("przemub", statuses)
                except TaskStatus as status:
                    return HttpResponse("quiz.moe is temporarily unavailable. Come back in 10 minutes!<br>Message:<br> " + status.args[0], status=503)

        if not themes:
            alert += "Playing przemub's list."
            try:
                themes = self._get_user_themes("przemub", statuses)
            except TaskStatus as status:
                return HttpResponse(
                "quiz.moe is temporarily unavailable. Come back in 10 minutes!<br>Message:<br> " + status.args[0], status=503)

        def check_if_right_type(local_theme):
            if openings and local_theme["type"] == "OP":
                return True
            if endings and local_theme["type"] == "ED":
                return True
            return False

        themes = list(filter(check_if_right_type, themes))
        theme = random.choice(themes)

        # Get a random version of the theme
        url = random.choice(random.choice(theme['entries'])['videos'])['link'].replace('staging.', '')

        context = {
            "url": url,
            "theme": theme,
            "users": users,
            "openings": openings,
            "endings": endings,
            "statuses": statuses,
            "all_statuses": self.ALL_STATUSES,
            "alert": mark_safe(alert)
        }

        return render(request, "quiz/quiz.html", context)
