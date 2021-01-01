"""
=================================
General imports
=================================
"""

from django.db import connection
import logging
import subprocess

log = logging.getLogger(__name__)

"""
=================================
Miscellaneous functions
=================================
"""

def reset_database():
    """
    This function is used to remotely restore the local database to its last commited state.
    """
    db_name = connection.settings_dict['NAME']
    # Using 'git restore' requires git 2.23 or later
    command = ['git', 'restore', db_name]
    log.info("Restoring local database to most recent commit")
    process = subprocess.run(command, capture_output=True)
    stdout = process.stdout.decode("utf-8")
    # If there is no output, command was invoked successfully
    if (not stdout):
        result = False
        log.info('Database successfully restored')
    else:
        result = stdout
        log.error(result)
    return result
