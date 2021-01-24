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
import os

from .settings import *  # noqa

DEBUG = False

if os.environ.get('QUIZ_SECRET_KEY', None):
    SECRET_KEY = os.environ["QUIZ_SECRET_KEY"]
else:
    raise Exception("QUIZ_SECRET_KEY environment variable is not set!")

if os.environ.get('QUIZ_BUGSNAG', None):
    BUGSNAG = {
        'api_key': os.environ["QUIZ_BUGSNAG"],
        'project_root': '/usr/src/app',
    }

    LOGGING["handlers"]["bugsnag"] = {
        'level': 'INFO',
        'class': 'bugsnag.handlers.BugsnagHandler',
    }
    LOGGING["loggers"]["django"]["handlers"].append("bugsnag")

MIDDLEWARE += ["bugsnag.django.middleware.BugsnagMiddleware"]
