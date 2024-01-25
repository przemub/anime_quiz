"""Wrapper that executes tasks on GCP instead of in Celery. Because I have a cert to prepare for."""
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
from django_cloud_tasks.tasks import Task
from django_cloud_tasks.views import GoogleCloudTaskView
from gcp_pilot.base import DEFAULT_SERVICE_ACCOUNT
from google.auth.transport import requests
from google.oauth2 import id_token

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


def make_gcp_task(task_base):
    class GCPTask(Task):
        def run(self, **kwargs):
            task = task_base()

            try:
                return task.run(**kwargs)
            finally:
                task.after_return(
                    None, None, None, (), kwargs, None
                )

        def delay(self, **kwargs):
            return self.asap(**kwargs)

        def apply_async(self, task_kwargs, eta=None, countdown=None):
            if (eta and countdown) or (eta and countdown) is None:
                raise ValueError("Use eta or countdown")
            return self.later(task_kwargs, eta or countdown)

    GCPTask.__name__ = task_base.__name__.replace("Base", "GCP")
    GCPTask.__qualname__ = task_base.__qualname__.replace("Base", "GCP")

    return GCPTask


def verify_oidc_token(request: HttpRequest):
    auth_header: str = request.headers.get("Authorization")

    if not auth_header:
        raise PermissionDenied("No auth header")

    auth_type, creds = auth_header.split(" ", 1)
    if auth_type.capitalize() != "Bearer":
        raise PermissionDenied("Wrong auth_type " + auth_type)

    claims = id_token.verify_token(creds, requests.Request())
    if claims['email'] != DEFAULT_SERVICE_ACCOUNT:
        raise PermissionDenied("Unauthorised user " + claims['user'])


class TaskView(GoogleCloudTaskView):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        verify_oidc_token(request)
        return super().dispatch(request, *args, **kwargs)

    dispatch.csrf_exempt = True
