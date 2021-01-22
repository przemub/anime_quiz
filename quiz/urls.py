from django.urls import path
from django.views.generic.base import TemplateView

from quiz.views import UserThemesView

urlpatterns = [
    path("", UserThemesView.as_view()),
    path("robots.txt", TemplateView.as_view(
        template_name="quiz/robots.txt", content_type="type/plain"
    ))
]
