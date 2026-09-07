from django.shortcuts import render

from .forms import ApplicationForm


def home_view(request):
    return render(request, "home.html")


def application_form_view(request):
    form = ApplicationForm()
    return render(request, "intake/form.html", {"form": form})
