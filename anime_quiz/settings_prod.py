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
from .settings import *  # noqa
from anime_quiz.logging_config import build_logging

DEBUG = False

LOGGING = build_logging(json_logs=True, bugsnag=BUGSNAG is not None)

if os.environ.get("QUIZ_SECRET_KEY", None):
    SECRET_KEY = os.environ["QUIZ_SECRET_KEY"]
else:
    raise Exception("QUIZ_SECRET_KEY environment variable is not set!")

if BUGSNAG is not None:
    BUGSNAG["release_stage"] = "production"
