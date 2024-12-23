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
from django.urls import path
from django.views.generic.base import TemplateView

from quiz.views import UserThemesView

urlpatterns = [
    path("", UserThemesView.as_view()),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="quiz/robots.txt", content_type="type/plain"
        ),
    ),
]
