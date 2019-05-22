from django.contrib import admin

# Import the model class
from .models import Component, Configuration, Climate, Project

# Register the model classes for the admin page.
admin.site.register(Component)
admin.site.register(Configuration)
admin.site.register(Climate)
admin.site.register(Project)
