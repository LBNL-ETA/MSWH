"""
WSGI config for swhweb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import sys

# import paths from settings.py
from .local_settings import DJANGO_PROJECT_PATH, VIRTUALENV_PACKAGES_PATH, MSWH_PROJECT_PATH

# add the path to this file
sys.path.append(DJANGO_PROJECT_PATH)

# add the virtualenv site-packages path
sys.path.append(VIRTUALENV_PACKAGES_PATH)

# add the path to the mswh Python package
sys.path.append(MSWH_PROJECT_PATH)

# import Django wsgi implementation only after appending all paths to SYS paths
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swhweb.settings")

application = get_wsgi_application()
