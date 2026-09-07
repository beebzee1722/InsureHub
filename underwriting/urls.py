from django.urls import path

from .views import application_form_view, home_view

urlpatterns = [
    path("", home_view, name="home"),
    path("applications/new/", application_form_view, name="application_form"),
]
