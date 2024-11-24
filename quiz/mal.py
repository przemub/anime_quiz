"""
Adapted from https://github.com/przemub/animethemes-dl/blob/master/animethemes_dl/parsers/myanimelist.py

Copyright (c) 2020 sadru
Copyright (c) 2024 Przemysław Buczkowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import logging

import requests


logger = logging.getLogger(__name__)
MALURL = "https://myanimelist.net/animelist/{user}/load.json"
MAL_OPTIONS = {
    "animelist": {
        "minpriority": 0,
        "minscore": 0,  # TODO: Add a filter based on that
    },
    "statuses": [1, 2],
}


class MyanimelistException(Exception):
    pass


def add_url_kwargs(url, kwargs=None):
    if not kwargs:
        kwargs = {}

    kwargs = "&".join(f"{k}={v}" for k, v in kwargs.items())
    return url + "?" + kwargs


def parse_priority(priority: str) -> int:
    """
    Parses MAL priority string into a 1-3 range
    """
    return ("low", "medium", "high").index(priority.lower())


def get_mal_part(username: str, **kwargs) -> list:
    """
    Gets a MAL list with a username.
    Kwargs reffer to the arguments `(sort=3,x='w') -> ?sort=3&x=w`.
    If a list is longer than 300 entries, you must set an offset.
    """
    url = MALURL.format(user=username)
    url = add_url_kwargs(url, kwargs)

    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 400:
        logger.info(f"User %s does not exist on MAL. Error: %s", username, r.json())
        raise MyanimelistException(f"User {username} does not exist on MAL.")
    else:
        logger.error(f"Failed to download user %s from MAL. Error: %s", username, r.json())
        raise MyanimelistException(f"Failed to download user {username} from MAL.", username)


def get_raw_mal(username: str, **kwargs) -> list:
    """
    Gets a MAL list with a username.
    Sends multiple requests if the list is longer than 300 entries.
    """
    out = []
    offset = 0
    while True:
        kwargs["offset"] = offset
        data = get_mal_part(username, **kwargs)
        out.extend(data)
        if len(data) < 300:  # no more anime
            logger.debug(f"Got {len(data)} entries from MAL.")
            return out
        offset += 300


def filter_mal(data: list) -> list[tuple[int, str]]:
    """
    Filters a MAL list and returns a list of malids and titles.
    Removes all unwanted statuses, scores, priorities.
    Also filters out unreleased anime.
    """
    titles = []
    for entry in data:
        status = entry["status"]
        score = entry["score"]
        priority = parse_priority(entry["priority_string"])
        start_date = entry["anime_start_date_string"]
        malid = entry["anime_id"]
        title = entry["anime_title"]

        if not (  # animelist options
            status in MAL_OPTIONS["statuses"]
            and score >= MAL_OPTIONS["animelist"]["minscore"]
            and priority >= MAL_OPTIONS["animelist"]["minpriority"]
        ):
            continue

        if start_date is None:
            continue

        titles.append((malid, title))

    return titles
