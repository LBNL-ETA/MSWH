## What is in here?

This folder contains the Django source code for the web app.

File/Folder | Content
------ | ------
[data](data) | This folder contains the simulation results stored as pickled files.
[swhweb](swhweb) | This folder contains high-level, Django project related configuration files.
[system](system) | Here, the Django app data lives in.
[templates](templates) | This folder contains html files associated with general, project related content.
[db.sqlite3](db.sqlite3) | This is the Django project database.
[manage.py](manage.py) | This is the main Django utility file used to run the server, add a new Django application, etc.

The basic structure of the web app is split into the following sections available through the tabs in the navigation bar at the top of the page:

* **Home:** Overview of the functionality
* **Configurations:** A list of preconfigured systems. The user can edit, delete and create new configurations and place the system in a climate zone
* **Components:** A list of available system components, grouped in their respective class. The user can edit, delete and create new components
* **Projects:** Any system configuration can be deployed for a specific project. A project can be a single household or a community consisting of multiple households. On the _Project_ page, the user sees all available project, can edit or delete them as well as create new project configurations
* **Visualization:** After having invoked the simulation on the _Configurations_ page, this page provides a list with available simulation results for a respective system configuration. When clicking on an item, the interactive plot as well as a table with annual totals can be accessed for further analyses of the system's performance
* **Admin:** Django provides an administration interface, which can be reached through this tab. A super user has been created as follows:

      User name:  admin
      Password:   $SWH2019
