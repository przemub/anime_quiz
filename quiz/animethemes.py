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
from typing import TypedDict, List, Dict, Optional, Union

import requests

BASE = "https://api.animethemes.moe"
SESSION = requests.session()
SESSION.headers = {
    "User-Agent": "quiz.moe (contact: prem@prem.moe)",
}

MISSING_IN_ANIMETHEMES = 1


class AnimeThemesTryLater(Exception):
    """Request the caller to try after retry_after seconds."""

    retry_after: int

    def __init__(self):
        raise NotImplementedError()

    def message(self) -> str:
        raise NotImplementedError()


class AnimeThemesThrottled(AnimeThemesTryLater):
    """The exception raised when there is a 429 returned from the API."""

    def __init__(self, retry_after: int):
        """
        :param retry_after: Seconds to wait requested by the server.
        """
        self.retry_after = retry_after

    def message(self):
        return f"Throttled. Trying again in {self.retry_after} seconds."


class AnimeThemesDown(AnimeThemesTryLater):
    """animethemes.moe is down. Try later."""

    def __init__(self, status_code: int, retry_after: int = 30):
        self.status_code = status_code
        self.retry_after = retry_after

    def message(self):
        return (
            f"animethemes.moe is down with code {self.status_code}. "
            f"Trying again in {self.retry_after} seconds."
        )


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


class Song(TypedDict):
    id: int
    title: str


class Theme(TypedDict):
    anime_title: str
    song: Song


class Anime(AnimeSearchResult):
    """
    Dictionary returned from /anime/{slug} method.
    The difference to AnimeSearchResult is that it can include additional information.
    """

    resources: Optional[List[Resource]]
    animethemes: List[Theme]


GET_PARAM = Union[str, int, float, List[Union[str, int, float]]]


def _query_api(path: str, params: Dict[str, GET_PARAM]) -> dict:
    if path[0] != "/":
        path = "/" + path
    r = SESSION.get(BASE + path, params=params)

    if r.status_code == 429:
        raise AnimeThemesThrottled(int(r.headers["Retry-After"]))
    elif r.status_code in (502, 504):
        raise AnimeThemesDown(r.status_code)
    else:
        r.raise_for_status()

    return r.json()


def request_anime(mal_id: int, title: str) -> list[Theme]:
    """Looks up a MAL id on animethemes and returns an animethemes id."""

    animes: List[AnimeSearchResult] = _query_api(
        "/search/", params={"q": title, "fields[search]": "anime"}
    )["search"]["anime"]

    for anime in animes:
        anime_full_data: Anime = _query_api(
            "/anime/" + anime["slug"],
            params={
                "include": "resources,"
                "animethemes.animethemeentries.videos,"
                "animethemes.song,"
                "animethemes.song.artists"
            },
        )["anime"]

        if mal_id in (
            res["external_id"]
            for res in anime_full_data["resources"]
            if res["site"] == "MyAnimeList"
        ):
            # Add some needed data to each theme
            for theme in anime_full_data["animethemes"]:
                theme["anime_title"] = title

            return anime_full_data["animethemes"]
    return []
