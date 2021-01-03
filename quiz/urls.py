from django.urls import path

from quiz.views import UserThemesView

urlpatterns = [path("", UserThemesView.as_view())]
