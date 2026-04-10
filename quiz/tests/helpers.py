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
from quiz.animethemes import Theme


def make_mal_theme(mal_id: int, anime_title: str) -> dict:
    """Build a minimal MAL theme dict for use in _get_user_themes tests."""
    return {"mal_id": mal_id, "anime_title": anime_title}


def make_theme(id, type="OP", spoiler=False, nsfw=False, lyrics=False) -> Theme:
    """Build a full theme dict matching the animethemes.moe API shape."""
    return {
        "id": id,
        "type": type,
        "animethemeentries": [
            {
                "spoiler": spoiler,
                "nsfw": nsfw,
                "videos": [{"lyrics": lyrics, "link": "https://example.com"}],
            }
        ],
        "song": {"title": f"Song {id}", "artists": [{"name": f"Artist {id}"}]},
    }
