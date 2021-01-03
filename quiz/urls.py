from django.urls import path

from quiz.views import UserThemesView

urlpatterns = [
    path('user', UserThemesView.as_view())
]
