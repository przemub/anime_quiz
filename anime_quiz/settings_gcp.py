#      Copyright (c) 2024 Przemysław Buczkowski
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
import google.cloud.logging
import warnings

from .settings import *  # noqa

warnings.warn("GCP tasks backend is not currently working!")

DEBUG = False

if os.environ.get("QUIZ_SECRET_KEY", None):
    SECRET_KEY = os.environ["QUIZ_SECRET_KEY"]
else:
    raise Exception("QUIZ_SECRET_KEY environment variable is not set!")

TASK_BACKEND = "gcp"
INSTALLED_APPS += ["django_cloud_tasks"]
REST_FRAMEWORK = {}
DJANGO_CLOUD_TASKS_APP_NAME = "quiz-moe"

# Close Redis connections, so we don't run out of connections on free-tier Redis Cloud
DJANGO_REDIS_CLOSE_CONNECTION = True

# Set up logging

client = google.cloud.logging.Client()
client.setup_logging()
