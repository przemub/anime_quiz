#      Copyright (c) 2021-22 Przemysław Buczkowski
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

import animelyrics
from animethemes_dl import OPTIONS as ANIMETHEMES_OPTIONS, MyanimelistException
from animethemes_dl.parsers.myanimelist import get_raw_mal, filter_mal
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic.base import View
from first import first

from .tasks import GetUserThemesTask, GetLyricsTask

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

    @staticmethod
    def _get_user_themes(user: str, statuses: list[int]):
        result_key = f"result_{user}_{'-'.join(str(s) for s in statuses)}"
        if result := cache.get(result_key, None):
            return result

        started_key = f"started_user_{user}"
        if cache.get(started_key, False):
            raise TaskStatus(
                f"User {user} has been already enqueued. Please wait."
            )

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
            raise TaskStatus(
                f"User {user} has been already enqueued. Please wait."
            )
        else:
            GetUserThemesTask().delay(user, cache_misses)
            raise TaskStatus(f"User {user} has been enqueued just now.")

    @staticmethod
    def _apply_themes_filters(
        themes, openings, endings, spoilers, nsfw, karaoke
    ):
        """
        Apply filters to themes.
        Filters: openings, endings, spoilers, NSFW.
        """

        if not spoilers:
            # If asked, exclude videos with spoilers.
            for theme in themes:
                theme["animethemeentries"] = list(
                    entry
                    for entry in theme["animethemeentries"]
                    if entry["spoiler"] is False
                )

        if not nsfw:
            # If asked, exclude lewds.
            for theme in themes:
                theme["animethemeentries"] = list(
                    entry
                    for entry in theme["animethemeentries"]
                    if entry["nsfw"] is False
                )

        def check_if_right_type(local_theme):
            if openings and local_theme["type"] == "OP":
                return True
            if endings and local_theme["type"] == "ED":
                return True
            return False

        themes = list(filter(check_if_right_type, themes))

        if karaoke:
            for theme in themes:
                for entry in theme["animethemeentries"]:
                    entry["videos"] = list(
                        video
                        for video in entry["videos"]
                        if video["lyrics"] is True
                    )
                theme["animethemeentries"] = [
                    entry
                    for entry in theme["animethemeentries"]
                    if entry["videos"]
                ]

        # Exclude themes with only hentai or spoiler videos
        themes = [theme for theme in themes if theme["animethemeentries"]]

        return themes


    def get(self, request):
        users = request.GET.getlist("user", ["przemub"])

        # Get theme filters
        default = request.GET.get("default", "yes") == "yes"
        openings = default or request.GET.get("t-op", "off") == "on"
        endings = request.GET.get("t-ed", "off") == "on"
        spoilers = request.GET.get("sp", "off") == "on"
        nsfw = default or request.GET.get("nsfw", "on")
        karaoke = request.GET.get("karaoke", "off") == "on"

        # Something must be enabled
        if not (openings or endings):
            openings, endings = True, False

        # Get anime filters (Watching, completed, on-hold, dropped, PTW)
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

        # Queue all users and choose a random user list to choose an anime from
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
            alert += (
                f"User{'s' if plural else ''} "
                f"{', '.join(enqueued_users)} "
                f"{'have' if plural else 'has'} been enqueued.<br />"
                "For the time being, choosing a theme from "
                f"{playing_user}'s list."
            )

            if themes is None:
                try:
                    themes = self._get_user_themes("przemub", statuses)
                except TaskStatus as status:
                    return HttpResponse(
                        "quiz.moe is temporarily unavailable. "
                        "Come back in 10 minutes!<br>Message:<br> "
                        + status.args[0],
                        status=503,
                    )

        if not themes:
            alert += "Playing przemub's list."
            try:
                themes = self._get_user_themes("przemub", statuses)
            except TaskStatus as status:
                return HttpResponse(
                    "quiz.moe is temporarily unavailable. "
                    "Come back in 10 minutes!<br>Message:<br> "
                    + status.args[0],
                    status=503,
                )

        themes = self._apply_themes_filters(
            themes, openings, endings, spoilers, nsfw, karaoke
        )

        # Remove themes which appeared lastly, and choose one left!
        last_chosen = request.session.get("last_chosen", [])
        last_chosen_max_count = len(themes) // 2 - 1
        last_chosen = last_chosen[-last_chosen_max_count:]

        last_chosen_set = set(last_chosen)
        themes = [
            theme for theme in themes if theme["id"] not in last_chosen_set
        ]
        theme = random.choice(themes)
        last_chosen.append(theme["id"])
        request.session["last_chosen"] = last_chosen

        # Get a random version of the theme
        url = random.choice(
            random.choice(theme["animethemeentries"])["videos"]
        )["link"].replace("staging.", "")

        lyrics = GetLyricsTask().run(theme)

        context = {
            "url": url,
            "theme": theme,
            "artists": ", ".join(
                artist["name"] for artist in theme["song"]["artists"]
            ),
            "users": users,
            "openings": openings,
            "endings": endings,
            "spoilers": spoilers,
            "nsfw": nsfw,
            "karaoke": karaoke,
            "statuses": statuses,
            "lyrics": mark_safe(lyrics),
            "all_statuses": self.ALL_STATUSES,
            "alert": mark_safe(alert),
        }

        return render(request, "quiz/quiz.html", context)
