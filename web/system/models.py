from django.db import models

import ast
import pandas as pd
import numpy as np

from .functions import (
    Map,
    load_weather,
    check_params,
    str2dict,
    df2dict,
    dict2df,
    simulate_system,
    get_random_project,
    create_load,
)
from .functions import SYSTEM_LABELS as s
from .functions import CONSUMER_LABELS as c

# A manager class for the Component class
class ComponentManager(models.Manager):

    # Create a new component object with given parameters
    def create_component(self, name, type):
        component = self.create(name=name, type=type)
        return component


# Component class
class Component(models.Model):

    # Name of the model
    name = models.CharField(max_length=255, default="undefined")

    # Type of the model
    type = models.CharField(
        max_length=255,
        choices=Map().get_component_choices(),
        default="undefined",
    )

    # Timestamp when the model was created (this value is automatically converted into the correct time zone)
    created = models.DateTimeField(auto_now_add=True)

    # Short description what the model does
    description = models.TextField(
        default="This is an example description what the model is doing, how it is implemented and anything else, which might be of interest to know about the model.\n\nThis can be a rather longer text, since it may contain relevant information about the model, which can't be stored elsewhere."
    )

    # Parameters of the model (stored as dictionary formatted string)
    params = models.TextField(default="{'param' : 123., 'param_2' : 'abc'}")

    # Size of the component
    size = models.FloatField(default=1.0)

    # To use the manager class just call manager functions like this
    # new_comp = Component.objects.create_component(name='new_name', type='new_type')
    objects = ComponentManager()

    # Returns the name of the model
    def __str__(self):
        return self.name

    # Store parameters as string (p is a dictionary)
    def set_params(self, p):
        self.params = repr(p)
        self.save()

    # Load parameters as dictionary
    def get_params(self):
        return ast.literal_eval(self.params)


# A manager class for the Climate class
class ClimateManager(models.Manager):

    # Create a new weather object with given parameters
    def create_climate(self, name, climate_zone, data_source):
        climate = self.create(
            name=name, climate_zone=climate_zone, data_source=data_source
        )
        return climate


# Climate class
class Climate(models.Model):

    # Name of the model
    name = models.CharField(max_length=255, default="undefined")

    # Climate of the model
    climate_zone = models.CharField(max_length=255, default="undefined")

    # Climate data source (cec or tmy3)
    data_source = models.CharField(max_length=255, default="undefined")

    # Weather data of the model (stored as dictionary formatted string)
    data = models.TextField(default="undefined")

    # To use the manager class just call manager functions like this
    # new_weater = Climate.objects.create_climate(name='name', climate_zone=climate_zone, data_source=data_source)
    objects = ClimateManager()

    # Returns the name of the model
    def __str__(self):
        return self.name

    # Populate the data field, using a pandas DataFrame as input parameter
    def populate_data(self, df):
        self.data = str(df2dict(df))
        self.save()

    # Retrieve data from the climate object
    def get_data(self):
        data = ast.literal_eval(self.data)
        return dict2df(data)


# A manager class for the Project class
class ProjectManager(models.Manager):

    # Create a new project object with given parameters
    def create_project(self, name, size):
        project = self.create(name=name, size=size)

        # Create random project set up
        proj = get_random_project(int(size))
        project.set_at_home(proj["at_home"])
        project.set_occupancy(proj["occ"])

        # Populate the data field
        project.populate_data(create_load(proj["occ"], proj["at_home"]))

        return project


# Project class
class Project(models.Model):

    # Name of the model
    name = models.CharField(max_length=255, default="undefined")

    # Occupancy of the households belonging to the project
    # (stored as list formated string)
    occupancy = models.TextField(default="undefined")

    # Flags indicating if the occupants of the households of this project
    # are at home during the day (stored as list formated string)
    at_home = models.TextField(default="undefined")

    # Number of households in the project
    size = models.PositiveSmallIntegerField(default=1)

    # Load data of the model (stored as dictionary formatted string)
    data = models.TextField(default="undefined")

    # To use the manager class just call manager functions like this
    # new_project = Project.objects.create_project(name='name')
    objects = ProjectManager()

    # Returns the name of the model
    def __str__(self):
        return self.name

    # Set the occupancy field, using a list as input parameter
    def set_occupancy(self, lst):
        self.occupancy = str(lst)
        self.save()

    # Get the occupancies from the project object as list
    def get_occupancy(self):
        return ast.literal_eval(self.occupancy)

    # Set the at_home field, using a list as input parameter
    def set_at_home(self, lst):
        self.at_home = str(lst)
        self.save()

    # Get the at_home fields from the project object as list
    def get_at_home(self):
        return ast.literal_eval(self.at_home)

    # Populate the data field, using a pandas DataFrame as input parameter
    def populate_data(self, df):
        # Convert pandas DataFrame to JSON (numpy.array will be converted to Python List)
        self.data = df.to_json()
        self.save()

    # Get dictionary with households' configuration
    def get_households(self):
        households = {}

        # Create a dictionary containing the configuration of the households
        for id in range(self.size):
            households.update(
                {
                    id: {
                        "occupancy": self.get_occupancy()[id],
                        "at_home": self.get_at_home()[id],
                    }
                }
            )

        return households

    # Retrieve data from the project object
    def get_data(self):
        # Create the pandas Dataframe from the json formatted string
        data = pd.read_json(self.data)

        # Convert Python List back to numpy.array
        for i in data["End-Use Load"].index:
            data.at[i, "End-Use Load"] = np.asarray(data["End-Use Load"][i])

        return data


# A manager class for the Model class
class ConfigurationManager(models.Manager):

    # Create a new configuration object with given parameters
    def create_configuration(self, type):
        config = self.create(name=s[type], type=type)
        return config


# Model class
class Configuration(models.Model):

    # Name of the model
    name = models.CharField(max_length=255, default="undefined")

    # Mapping to external system function
    type = models.CharField(
        max_length=255, default="undefined", choices=Map().get_system_choices()
    )

    # Short description what the model does
    description = models.TextField(
        default="This is an example description what the model is doing, how it is implemented and anything else, which might be of interest to know about the model.\n\nThis can be a rather longer text, since it may contain relevant information about the model, which can't be stored elsewhere."
    )

    # List of all components
    components = models.ManyToManyField(Component, blank=True)

    # Climate
    climate = models.ForeignKey(
        "Climate", on_delete=models.SET_NULL, blank=True, null=True
    )

    # Community
    project = models.ForeignKey(
        "Project", on_delete=models.SET_NULL, blank=True, null=True
    )

    # Path to results file
    results_path = models.CharField(max_length=255, default="undefined")

    # To use the manager class just call manager functions like this
    # new_comp = Configuration.objects.create_configuration(type='type')
    objects = ConfigurationManager()

    # Returns the name of the model
    def __str__(self):
        return self.name

    # Set the path to results
    def set_results_path(self, res):
        self.results_path = res
        self.save()

    # Invoke the system simulation
    def invoke_simulation(self, args):
        # Call the simulation function in functions.py
        return simulate_system(args)

    # Check if config is ready for simulation (project and components assigned)
    def check_config(self):
        errors = []

        if not self.climate:
            errors.append("No climate assigned.")
        if not self.project:
            errors.append("No project assigned.")

        # *hg Replace this with a proper check which components are missing if any
        if len(self.components.all()) == 0:
            errors.append("No components assigned.")

        return False if len(errors) == 0 else errors

    # Return all component parameters as pandas DataFrame
    def get_params_pd(self, backup=False):
        # Retrieve all components of this configuration
        component_set = self.components.all()

        if len(list(component_set)) == 0:
            return False

        # Define which components to fetch
        component_list = (
            Map().get_system_backup(system=self.type)
            if backup
            else Map().get_system_components(system=self.type)
        )

        # Create empty DataFrame for holing the parameters
        params_pd = pd.DataFrame(
            data=[], columns=[s["comp"], s["param"], s["param_value"]]
        )

        # Copy component list in new list containing missing components
        missing_components = component_list.copy()

        # Cycle through components and extract parameters
        for comp in component_set:
            # If component in component_list, add it to params_pd and remove it from component_list
            if comp.type in component_list:
                missing_components.remove(comp.type)
            else:
                continue
            params_rows = []
            for key, val in comp.get_params().items():
                params_rows.append(
                    {
                        s["comp"]: s[comp.type],
                        s["param"]: s[key] if key in s else "Undefined",
                        s["param_value"]: val,
                    }
                )

            # Fill DataFrame with retrieved parameters
            params_pd = params_pd.append(params_rows, ignore_index=True)

        # Return parameters as dataframe if all components have been found, if not return missing components as list
        return (
            params_pd if len(missing_components) == 0 else missing_components
        )

    # Return all component sizes as pandas DataFrame
    def get_sizes_pd(self, backup=False):
        # Retrieve all components of this configuration
        component_set = self.components.all()

        if len(list(component_set)) == 0:
            return False

        # Define which components to fetch
        component_list = (
            Map().get_system_backup(system=self.type)
            if backup
            else Map().get_system_components(system=self.type)
        )

        # Create empty DataFrame for holing the sizes
        if backup:
            sizes_pd = pd.DataFrame(
                data=[], columns=[c["id"], s["comp"], s["cap"]]
            )
        else:
            sizes_pd = pd.DataFrame(data=[], columns=[s["comp"], s["cap"]])

        # Copy component list in new list containing missing components
        missing_components = component_list.copy()

        for comp in component_set:
            # If component in component_list, add it to params_pd and remove it from component_list
            if comp.type in component_list:
                missing_components.remove(comp.type)
            else:
                continue
            sizes_rows = []

            if backup:
                # Create a backup size for each individual household
                for id in range(1, self.project.size + 1):
                    sizes_rows.append(
                        {
                            c["id"]: id,
                            s["comp"]: s[comp.type],
                            s["cap"]: comp.size,
                        }
                    )
            else:
                sizes_rows.append(
                    {s["comp"]: s[comp.type], s["cap"]: comp.size}
                )

            # Fill DataFrame with retrieved sizes
            sizes_pd = sizes_pd.append(sizes_rows, ignore_index=True)

        # Return parameters as dataframe if all components have been found, if not return missing components as list
        return sizes_pd if len(missing_components) == 0 else missing_components
