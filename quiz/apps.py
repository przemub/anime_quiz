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

import bugsnag
from django.apps import AppConfig
from structlog.contextvars import get_contextvars


def _add_quiz_context(event):
    # Correlate the Bugsnag event with the structured logs for the same
    # request: django-structlog binds request_id into the contextvars.
    request_id = get_contextvars().get("request_id")
    if request_id:
        event.add_tab("trace", {"request_id": request_id})

    if not hasattr(event.request_config, "django_request"):
        return
    request = event.request_config.django_request
    quiz_context = getattr(request, "_quiz_context", None)
    if quiz_context:
        event.add_tab("quiz", quiz_context)


class QuizConfig(AppConfig):
    name = "quiz"

    def ready(self):
        bugsnag.before_notify(_add_quiz_context)
