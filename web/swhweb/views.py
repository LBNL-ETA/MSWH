from django.http import HttpResponse
from django.shortcuts import render

from datetime import date, datetime

# Function to format the date and time (see http://strftime.org/)
def time_format(date_time):
    return date_time.strftime("%H:%M")


# Show the home page
def home(request):

    # Just some sample date to pass through
    now = datetime.today()

    # Dictionary
    data = {"date_today": date.today(), "time_now": time_format(now)}

    # Return the html page as view including optional data
    return render(request, "home.html", data)
