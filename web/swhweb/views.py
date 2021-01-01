from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings

from datetime import date, datetime

from .functions import reset_database

# Show the home page
def home(request):

    # Define data to be passed to the template
    data = {
        "footer": settings.FOOTER, \
        "home_domain": settings.HOME_DOMAIN, \
        "home_button": settings.HOME_BUTTON, \
    }

    # Return the html page as view including optional data
    return render(request, "home.html", data)

# Show the license page
def license(request):

    # Define data to be passed to the template
    data = {
        "footer": settings.FOOTER, \
        "license_title": settings.LICENSE_TITLE, \
        "license_text": settings.LICENSE_TEXT, \
        "license_url": settings.LICENSE_URL, \
    }

    # Return the html page as view including optional data
    return render(request, "license.html", data)

# Endpoint to restore the database to its default state.
def reset_db(request):
    reset_database()
    return redirect("home")
