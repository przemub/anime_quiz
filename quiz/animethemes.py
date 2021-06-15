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
from typing import TypedDict, List, Dict, Optional, Union

import requests

BASE = "https://staging.animethemes.moe/api"
SESSION = requests.session()
SESSION.headers = {
    "User-Agent": "quiz.moe (contact: prem@prem.moe)",
}

MISSING_IN_ANIMETHEMES = 1


class AnimeThemesTimeout(Exception):
    """The exception raised when there is a 429 returned from the API."""


class AnimeSearchResult(TypedDict):
    """Dictionary returned from /search API method."""

    id: int
    name: str
    slug: str


class Resource(TypedDict):
    """animethemes.moe speak for external reference to the anime."""

    id: str
    external_id: str
    site: str


class Theme(TypedDict):
    anime_title: str


class Anime(AnimeSearchResult):
    """
    Dictionary returned from /anime/{slug} method.
    The difference to AnimeSearchResult is that it can include additional information.
    """

    resources: Optional[List[Resource]]
    themes: List[Theme]


GET_PARAM = Union[str, int, float, List[Union[str, int, float]]]


def _query_api(path: str, params: Dict[str, GET_PARAM]) -> dict:
    r = SESSION.get(BASE + path, params=params)

    if r.status_code == 429:
        raise AnimeThemesTimeout()
    else:
        r.raise_for_status()

    return r.json()


def request_anime(mal_id: int, title: str) -> list[Theme]:
    """Looks up a MAL id on animethemes and returns an animethemes id."""

    animes: List[AnimeSearchResult] = _query_api(
        "/search/", params={"q": title, "fields": "anime"}
    )["search"]["anime"]

    for anime in animes:
        anime_full_data: Anime = _query_api(
            "/anime/" + anime["slug"],
            params={"include": "externalResources,themes.entries.videos"},
        )["anime"]

        if mal_id in (
                res["external_id"]
                for res in anime_full_data["resources"]
                if res["site"] == "MyAnimeList"
        ):
            # Add some needed data to each theme
            for theme in anime_full_data['themes']:
                theme['anime_title'] = title

            return anime_full_data['themes']
    return []
