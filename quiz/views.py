#      Copyright (c) 2021-26 Przemysław Buczkowski
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
import logging
import random as random_module

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic.base import View

from .mal import get_raw_mal, filter_mal, MAL_OPTIONS, MyanimelistException
from .tasks import GetUserThemesTask, find_cached_lyrics

random = random_module.SystemRandom()
logger = logging.getLogger()


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

        mal_key = f"user_mal_{user}"
        mal_data = cache.get(mal_key, None)
        if mal_data is None:
            mal_data = get_raw_mal(user)
            cache.set(mal_key, mal_data, 60 * 60 * 24 * 7)  # Expire in a week

        MAL_OPTIONS["statuses"] = statuses
        mal_data = filter_mal(mal_data)

        if not mal_data:
            return []

        cache_misses = []
        cache_hits = []

        cache_data = cache.get_many(
            f"themes-{mal_id}"
            for mal_id, _title
            in mal_data
        )

        for mal_id, title in mal_data:
            anime_data = cache_data.get(f"themes-{mal_id}", None)
            if anime_data is None:
                cache_misses.append({"mal_id": mal_id, "anime_title": title})
            else:
                cache_hits.extend(anime_data)

        started_key = f"started_user_{user}"
        if not cache_misses:
            # Fully retrieved, cache and return
            cache.set(result_key, cache_hits, 60 * 60 * 24 * 7)
            return cache_hits
        elif cache_hits and cache.get(started_key, False):
            # Already started, return partially retrieved results
            return cache_hits
        elif cache.get(started_key, False):
            # Already started but nothing retrieved, fail
            raise TaskStatus(f"User {user} has already been enqueued, please wait.")
        else:
            # Start tasks to retrieve themes for the user
            random.shuffle(cache_misses)
            GetUserThemesTask().add_tasks([
                (anime, i+len(cache_hits))
                for i, anime in enumerate(cache_misses)
            ])
            cache.set(started_key, True, 60 * 60 * 24)

            # Return songs already in the cache
            if cache_hits:
                return cache_hits
            raise TaskStatus(f"User {user} has been enqueued just now.")

    @staticmethod
    def _choose_theme(themes: list, last_chosen: list) -> dict:
        """Choose a theme avoiding recently played ones.

        Excludes the last len(themes) // 2 played songs from the
        candidates. If all themes have been played recently, picks
        randomly from the full list. It should happen only when
        len(themes) < 3.

        Appends the chosen theme's ID to last_chosen in place.
        """
        exclude_count = len(themes) // 2
        recently_played = set(last_chosen[-exclude_count:]) if exclude_count > 0 else set()
        new_themes = [
            theme for theme in themes if theme["id"] not in recently_played
        ]

        logger.info(
            "Theme selection: %d themes, %d candidates, %d last_chosen",
            len(themes), len(new_themes), len(last_chosen),
        )

        if new_themes:
            theme = random.choice(new_themes)
        else:
            if len(themes) > 3:
                logger.warning(
                    "Repeat avoidance failed with %d themes, "
                    "last_chosen has %d entries",
                    len(themes), len(last_chosen),
                )
            theme = random.choice(themes)
        last_chosen.append(theme["id"])
        return theme

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
        """Choose a random theme song for the user to guess.

        Song selection works as follows:
        1. Fetch theme lists for each requested user from the cache.
        2. For each user (in random order), apply filters (OP/ED, spoilers,
           NSFW, karaoke). Pick the first user whose list is non-empty
           after filtering. Fall back to przemub's list if none match.
        3. Exclude the last len(user themes) // 2 played songs (tracked in
           the session) to avoid immediate repeats. If all songs have been
           played recently, pick randomly from the full list.
           This should happen only when one of the users has a very small
           list (<3 themes).
        """
        users = request.GET.getlist("user", ["przemub"])

        # Get theme filters
        default = request.GET.get("default", "yes") == "yes"
        openings = default or request.GET.get("t-op", "off") == "on"
        endings = request.GET.get("t-ed", "off") == "on"
        spoilers = request.GET.get("sp", "off") == "on"
        nsfw = default or request.GET.get("nsfw", "on") == "on"
        karaoke = request.GET.get("karaoke", "off") == "on"

        # When refreshing, we need just the player part of the website
        send_just_player = request.GET.get("player_only", "no") == "yes"

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

        # Debugging context
        request._quiz_context = {
            "users": users,
        }

        users_shuffled = random.sample(users, len(users))
        themes = None
        alert = ""
        enqueued_users = []

        # Queue all users and collect available theme lists
        available_users = []
        for user in users_shuffled:
            try:
                user_themes = self._get_user_themes(user, statuses)
            except TaskStatus:
                enqueued_users.append(user)
            except MyanimelistException:
                alert += f"User {user} does not exist. <br />"
            else:
                if user_themes:
                    available_users.append((user, user_themes))
                else:
                    alert += f"User {user} has an empty list. <br />"

        request._quiz_context["available_users"] = [u for u, _ in available_users]
        request._quiz_context["enqueued_users"] = enqueued_users

        if enqueued_users:
            plural = len(enqueued_users) > 1
            alert += (
                f"User{'s' if plural else ''} "
                f"{', '.join(enqueued_users)} "
                f"{'have' if plural else 'has'} been enqueued.<br />"
            )

        # Try each user's themes with filters applied
        for user, user_themes in available_users:
            filtered = self._apply_themes_filters(
                user_themes, openings, endings, spoilers, nsfw, karaoke
            )
            if filtered:
                themes = filtered
            else:
                alert += f"After filtering, user {user} has an empty list. <br />"

        # Fallback to przemub's list
        if not themes:
            alert += "Playing przemub's list."
            try:
                przemub_themes = self._get_user_themes("przemub", statuses)
            except TaskStatus as status:
                return HttpResponse(
                    "quiz.moe is temporarily unavailable. "
                    "Come back in a minute!<br>Message:<br> "
                    + status.args[0],
                    status=503,
                )
            themes = self._apply_themes_filters(
                przemub_themes, openings, endings, spoilers, nsfw, karaoke
            )

        last_chosen = request.session.get("last_chosen", [])
        request._quiz_context["themes_count"] = len(themes)
        request._quiz_context["last_chosen_count"] = len(last_chosen)
        theme = self._choose_theme(themes, last_chosen)
        request.session["last_chosen"] = last_chosen

        # Get a random version of the theme
        url = random.choice(
            random.choice(theme["animethemeentries"])["videos"]
        )["link"].replace("staging.", "")

        lyrics = find_cached_lyrics(song_id=theme["id"]) or "Not found yet"

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
            "send_just_player": send_just_player,
        }

        return render(request, "quiz/quiz.html", context)
