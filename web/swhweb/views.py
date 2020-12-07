from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from datetime import date, datetime

# Function to format the date and time (see http://strftime.org/)
def time_format(date_time):
    return date_time.strftime("%H:%M")


# Show the home page
def home(request):

    # Define data to be passed to the template
    data = {"footer": settings.FOOTER, "home_domain": settings.HOME_DOMAIN}

    # Return the html page as view including optional data
    return render(request, "home.html", data)
