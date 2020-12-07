# =====
# This file is just a template.
# !! Rename this file to local_settings.py and update variables !!
# =====

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'zd6^l28fyl08rd!$f9g1g!r!8oak+a6n9drke3+(@ht*sgp(gt'

# Override debug to be False
DEBUG = False

# add the Django project path into the sys.path
DJANGO_PROJECT_PATH = '<path_to_directory_of_this_file>'

# add the virtualenv site-packages path to the sys.path
VIRTUALENV_PACKAGES_PATH = '<path_to_virtualenv_packages>'

# add the path to the mswh Python package
MSWH_PROJECT_PATH = '<path_to_mswh_repo>'

# add the landing page if the web app is deployed on a subdomain
HOME_DOMAIN = 'https://domain.com'
