#      Copyright (c) 2021-24 Przemysław Buczkowski
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
from unittest import mock

from django.test import TestCase, override_settings

from quiz.animethemes import request_anime
from quiz.views import UserThemesView, TaskStatus


def _make_theme(mal_id: int, anime_title: str):
    return {"mal_id": mal_id, "anime_title": anime_title}


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
)
class MyAnimeListTestCase(TestCase):
    """
    Call the function which pulls the anime to query from MAL and check
    if it queued the job to get themes from animethemes.moe.
    """

    @mock.patch("quiz.views.GetUserThemesTask.add_tasks")
    def test_get_watching_themes(self, mock_task):
        """
        Calls _get_user_themes and checks whether a task to pull
        anime being watched by our test user is created.
        """
        with self.assertRaises(TaskStatus):
            UserThemesView._get_user_themes("quiz_moe_testing", [1])
        mock_task.assert_called_once()
        self.assertEqual(
            [_make_theme(5114, "Fullmetal Alchemist: Brotherhood")],
            [theme for theme, _priority in mock_task.call_args.args[0]]
        )

    @mock.patch("quiz.views.GetUserThemesTask.add_tasks")
    def test_get_completed_themes(self, mock_task):
        """
        Calls _get_user_themes and checks whether a task to pull
        anime completed by our test user is created.
        """
        with self.assertRaises(TaskStatus):
            UserThemesView._get_user_themes("quiz_moe_testing", [2])
        mock_task.assert_called_once()
        self.assertEqual(
            [
                _make_theme(17074, "Monogatari Series: Second Season"),
                _make_theme(9253, "Steins;Gate"),
                _make_theme(7785, "Yojouhan Shinwa Taikei"),
            ],
            sorted((theme for theme, _priority in mock_task.call_args.args[0]), key=lambda theme: theme["anime_title"])
        )

    @mock.patch("quiz.views.GetUserThemesTask.add_tasks")
    def test_get_watching_and_completed_themes(self, mock_task):
        """
        Calls _get_user_themes and checks whether a task to pull
        anime being watched and completed by our test user is created.
        """
        with self.assertRaises(TaskStatus):
            UserThemesView._get_user_themes("quiz_moe_testing", [1, 2])
        mock_task.assert_called_once()
        self.assertEqual(
            [
                _make_theme(5114, "Fullmetal Alchemist: Brotherhood"),
                _make_theme(17074, "Monogatari Series: Second Season"),
                _make_theme(9253, "Steins;Gate"),
                _make_theme(7785, "Yojouhan Shinwa Taikei"),
            ],
            sorted((theme for theme, _priority in mock_task.call_args.args[0]), key=lambda theme: theme["anime_title"])
        )


class AnimeThemesMoeTestCase(TestCase):
    """
    Test if pulling the themes from animethemes.moe works.
    """

    def test_request_anime(self):
        anime = request_anime(9253, "Steins;Gate")

        self.assertEqual(len(anime), 5)  # 5 themes for this anime
        for theme in anime:
            self.assertEqual(theme["anime_title"], "Steins;Gate")

        self.assertEqual(
            [theme["song"]["title"] for theme in anime],
            [
                "Hacking to the Gate",
                "Toki Tsukasadoru Juuni no Meiyaku",
                "Fake Verthandi",
                "Sky Clad no Kansokusha",
                "Another Heaven",
            ],
        )
