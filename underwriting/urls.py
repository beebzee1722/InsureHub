from django.urls import path

from .views import (
    application_confirmation_view,
    application_create_view,
    application_form_view,
    home_view,
    risk_preview_view,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("applications/new/", application_form_view, name="application_form"),
    path("applications/create/", application_create_view, name="application_create"),
    path("applications/preview/", risk_preview_view, name="risk_preview"),
    path(
        "applications/<int:application_id>/confirmation/",
        application_confirmation_view,
        name="application_confirmation",
    ),
]
