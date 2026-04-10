#      Copyright (c) 2026 Przemysław Buczkowski
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
from django.test import TestCase

from quiz.views import UserThemesView
from quiz.tests.helpers import make_theme


class ChooseThemeTestCase(TestCase):
    """Tests for the repeat-avoidance algorithm in _choose_theme."""

    def test_picks_from_available(self):
        """Chosen theme is one of the available themes."""
        themes = [make_theme(1), make_theme(2), make_theme(3)]
        last_chosen = []
        theme = UserThemesView._choose_theme(themes, last_chosen)
        self.assertIn(theme["id"], {1, 2, 3})
        self.assertEqual(last_chosen, [theme["id"]])

    def test_avoids_recently_played(self):
        """Recently played themes (within window) are skipped."""
        themes = [make_theme(1), make_theme(2), make_theme(3), make_theme(4)]
        # Window = 4 // 2 = 2, so IDs 3 and 4 are excluded
        last_chosen = [3, 4]
        theme = UserThemesView._choose_theme(themes, last_chosen)
        self.assertIn(theme["id"], {1, 2})

    def test_exhausted_falls_back_to_full_list(self):
        """When all themes are in last_chosen, still picks one."""
        themes = [make_theme(1), make_theme(2)]
        # Window = 2 // 2 = 1, only last entry (2) excluded → picks 1
        last_chosen = [1, 2]
        theme = UserThemesView._choose_theme(themes, last_chosen)
        self.assertEqual(theme["id"], 1)

    def test_single_theme_zero_window(self):
        """With 1 theme, window is 0 so it's always pickable."""
        themes = [make_theme(1)]
        last_chosen = [1]
        theme = UserThemesView._choose_theme(themes, last_chosen)
        self.assertEqual(theme["id"], 1)

    def test_window_is_half_of_themes(self):
        """Exclusion window is len(themes) // 2."""
        themes = [make_theme(i) for i in range(1, 11)]  # 10 themes
        # Window = 5, so IDs 6-10 are excluded
        last_chosen = [6, 7, 8, 9, 10]
        theme = UserThemesView._choose_theme(themes, last_chosen)
        self.assertIn(theme["id"], {1, 2, 3, 4, 5})

    def test_foreign_ids_ignored(self):
        """IDs from other users' themes don't affect filtering."""
        themes = [make_theme(1), make_theme(2)]
        last_chosen = [99, 100]
        theme = UserThemesView._choose_theme(themes, last_chosen)
        self.assertIn(theme["id"], {1, 2})

    def test_appends_choice_to_last_chosen(self):
        """Chosen theme ID is appended to last_chosen in place."""
        themes = [make_theme(1)]
        last_chosen = [5, 6, 7]
        UserThemesView._choose_theme(themes, last_chosen)
        self.assertEqual(last_chosen, [5, 6, 7, 1])

    def test_never_falls_back_with_more_than_3_themes(self):
        """With >3 themes, new_themes is never empty regardless of last_chosen."""
        for size in [4, 5, 10, 50]:
            themes = [make_theme(i) for i in range(1, size + 1)]
            # Worst case: last_chosen contains all theme IDs
            last_chosen = list(range(1, size + 1))
            with self.assertNoLogs(level="WARNING"):
                UserThemesView._choose_theme(themes, last_chosen)

    def test_small_list_may_fall_back(self):
        """With <=3 themes, falling back is acceptable (no warning)."""
        for size in [1, 2, 3]:
            themes = [make_theme(i) for i in range(1, size + 1)]
            last_chosen = list(range(1, size + 1))
            # Should not log a warning even if fallback triggers
            theme = UserThemesView._choose_theme(themes, last_chosen)
            self.assertIn(theme["id"], set(range(1, size + 1)))


class ApplyThemesFiltersTestCase(TestCase):
    """Tests for _apply_themes_filters."""

    def test_openings_only(self):
        """Only OPs are returned when endings=False."""
        themes = [make_theme(1, type="OP"), make_theme(2, type="ED")]
        result = UserThemesView._apply_themes_filters(
            themes, openings=True, endings=False, spoilers=True, nsfw=True, karaoke=False
        )
        self.assertEqual([t["id"] for t in result], [1])

    def test_endings_only(self):
        """Only EDs are returned when openings=False."""
        themes = [make_theme(1, type="OP"), make_theme(2, type="ED")]
        result = UserThemesView._apply_themes_filters(
            themes, openings=False, endings=True, spoilers=True, nsfw=True, karaoke=False
        )
        self.assertEqual([t["id"] for t in result], [2])

    def test_both_types(self):
        """Both OPs and EDs are returned."""
        themes = [make_theme(1, type="OP"), make_theme(2, type="ED")]
        result = UserThemesView._apply_themes_filters(
            themes, openings=True, endings=True, spoilers=True, nsfw=True, karaoke=False
        )
        self.assertEqual([t["id"] for t in result], [1, 2])

    def test_exclude_spoilers(self):
        """Spoiler entries are removed when spoilers=False."""
        themes = [make_theme(1, spoiler=False), make_theme(2, spoiler=True)]
        result = UserThemesView._apply_themes_filters(
            themes, openings=True, endings=True, spoilers=False, nsfw=True, karaoke=False
        )
        self.assertEqual([t["id"] for t in result], [1])

    def test_exclude_nsfw(self):
        """NSFW entries are removed when nsfw=False."""
        themes = [make_theme(1, nsfw=False), make_theme(2, nsfw=True)]
        result = UserThemesView._apply_themes_filters(
            themes, openings=True, endings=True, spoilers=True, nsfw=False, karaoke=False
        )
        self.assertEqual([t["id"] for t in result], [1])

    def test_karaoke_only(self):
        """Only themes with lyrics videos are kept when karaoke=True."""
        themes = [make_theme(1, lyrics=True), make_theme(2, lyrics=False)]
        result = UserThemesView._apply_themes_filters(
            themes, openings=True, endings=True, spoilers=True, nsfw=True, karaoke=True
        )
        self.assertEqual([t["id"] for t in result], [1])

    def test_all_filtered_out(self):
        """Returns empty list when no themes match filters."""
        themes = [make_theme(1, type="ED")]
        result = UserThemesView._apply_themes_filters(
            themes, openings=True, endings=False, spoilers=True, nsfw=True, karaoke=False
        )
        self.assertEqual(result, [])
