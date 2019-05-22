from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.conf import settings

# Imports for Django application
from .models import Component, Configuration, Climate, Project
from .functions import Map, str2dict, load_weather, load_loads_indiv, store_pickle, load_pickle, delete_pickle, create_plot, create_filename_pickle, get_climate_zone_name, create_load
from .functions import SYSTEM_LABELS as s
from .functions import CONSUMER_LABELS as c

# For logging
import logging
log = logging.getLogger(__name__)

# *hg Move to functions.py
from mswh.comm.sql import Sql
from mswh.system.source_and_sink import SourceAndSink


"""
=================================
System views
=================================
"""

# Show the system home page
def home(request):
    return render(request, 'system/home.html')


"""
=================================
Component views
=================================
"""

# Show the components home page
def comp_list(request):
    # Get a list containing a list of components for each component class with the class name and a list of component type and readable name
    # Output form: [ ['component_class1', ['comp1', 'Component 1 - Readable']], ['component_class2', ['comp2', 'Component 2 - Readable']] ]
    types = Map().get_component_choices()

    # Retrieve a list of all Component objects in the DB
    components = Component.objects.all()

    return render(request, 'system/component/list.html', {'components' : components, 'types' : types})


# Show the detail view for the given component
def comp_detail(request, component_id):
    # Retrieve the requested component from the DB
    component = get_object_or_404(Component, pk=component_id)
    return render(request, 'system/component/detail.html', {'component': component})


# Show the edit view for the given component
def comp_edit(request, component_id):
    # Retrieve the requested component from the DB
    component = get_object_or_404(Component, pk=component_id)
    return render(request, 'system/component/edit.html', {'component' : component})


# Create new component
def comp_create(request, component_type):
    Component.objects.create_component(name=s[component_type], type=component_type)
    return redirect('sys:comp_list')


# Delete a component and return to component home screen
def comp_delete(request, component_id):
    # Retrieve the requested component from the DB
    component = get_object_or_404(Component, pk=component_id)
    component.delete()
    return redirect('sys:comp_list')


# Process the input from the form
def comp_form(request, component_id):
    # Retrieve the requested component from the DB
    component = get_object_or_404(Component, pk=component_id)
    errors = []
    par = dict()
    i = 0

    # Retrieve form entries from edit template and strip leading and trailing spaces
    # If value is not found, use 'undefined'
    name = request.POST.get('name', 'undefined').lstrip().rstrip()
    description = request.POST.get('description', 'undefined').lstrip().rstrip()
    size = request.POST.get('size', '1.0').lstrip().rstrip()

    # Retrieve all parameters
    while True:
        key = request.POST.get('param_key-{}'.format(i), 'undefined')
        val = request.POST.get('param_val-{}'.format(i), 'undefined')
        i+=1
        # Break the query as soon as all parameters have been retrieved
        if key == 'undefined':
            break
        # If key is empty or only whitespace(s), this results in the deletion of the paramter
        if key != '' and not key.isspace():
            # First remove leading and trailing spaces
            key = key.lstrip().rstrip()
            if key not in par:
                par[key] = val
            else:
                errors.append("Key '{}' appears more than once.".format(key))

    # Cycle through retrieved parameters for checks and conversions
    for key in par:
        # Check if value is of type int or float and convert it if yes
        try:
            par[key] = int(par[key])
        except Exception:
            try:
                par[key] = float(par[key])
            except Exception:
                # This means that par[key] will be stored as string
                # Check if it is empty or only whitespace(s)
                if par[key] == '' or par[key].isspace():
                    errors.append("Value of '{}' cannot be empty or only whitespace(s).".format(key))
                # Strip leading and tailing spaces
                par[key] = par[key].lstrip().rstrip()

    # Check if name is empty
    if name == '' or name.isspace():
        errors.append('Name field cannot be empty or only whitespace(s).')

    # Check if new component name does already exist in DB
    if Component.objects.filter(name = name).count() and name != component.name:
        errors.append("Object with the name '{}' already exists.".format(name))

    # Check if description is empty
    if description == '' or description.isspace():
        errors.append('Description field cannot be empty or only whitespace(s).')

    # Check if size is empty
    if size == '':
        errors.append('Size field cannot be empty.')
    else:
        # Check if size is of type float if not empty
        try:
            size = float(size)
        except Exception:
            errors.append('Size field must contain float value.')

    # Check other stuff and add it to the list of errors
    #if <check_for_error>:
    #    errors.append('Error message')

    # If there exist errors, display an error message for each
    if len(errors) > 0:
        return render(request, 'system/component/edit.html', {
                'component': component,
                'errors': errors,
        })
    else:
        # Convert the parameters to a string for storage in DB
        params = repr(par)

        # Updates retrieved values to object in DB
        Component.objects.filter(pk=component_id).update( \
            name=name, \
            params=params, \
            description=description, \
            size=size,\
            )

        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('sys:comp_detail', args=(component_id,)))


# Show the edit view for the given component
def comp_add_par(request, component_id):

    # Retrieve the requested component from the DB
    component = get_object_or_404(Component, pk=component_id)

    params = str2dict(component.params)

    # Add parameters
    i = 2
    while True:
        if 'param' not in params:
            params['param'] = 'undefined'
            break
        elif 'param_{}'.format(i) not in params:
            params['param_{}'.format(i)] = 'undefined'
            break
        else:
            i+=1

    # Store new parameters in the DB
    Component.objects.filter(pk=component_id).update( \
        params=repr(params), \
        )

    # Return to the edit page
    return HttpResponseRedirect(reverse('sys:comp_edit', args=(component_id,)))


"""
=================================
Climate views
=================================
"""

# Populate all climates retrieved from external database
def climate_populate(request):

    # Use path to SWH database defined in settings.py
    swh_db_path = settings.SWH_DATABASE
    log.info('Using SWH database "{}"'.format(swh_db_path))

    db = Sql(swh_db_path)
    log.info('Connected to database.')

    try:
        inputs = db.tables2dict(close = True)
        log.info('Converted sql to pandas DataFrame.')
    except:
        msg = 'Failed to read input tables from {}.'
        log.info(msg.format(inputs))

    weather = SourceAndSink(\
        input_dfs = inputs)
    log.info('Created SourceAndSink object')

    # Delete all previously stored climate objects before populating them
    n_climate_zones = Climate.objects.all().count()
    if n_climate_zones > 0:
        Climate.objects.all().delete()
        log.info('Deleted {} Climate object(s) from database.'.format(n_climate_zones))
        n_climate_zones = 0

    # Use climate data source as defined in settings.py
    data_source = settings.CLIMATE_DATA_SOURCE

    # Cycle from 1 to 16 (these are the climate zone IDs in the external database)
    for climate_zone_id in range(1, 17):

        climate_zone_id_str = '{:02d}'.format(climate_zone_id)

        climate_data = weather.irradiation_and_water_main( \
            climate_zone_id_str, \
            method='isotropic diffuse', \
            weather_data_source=data_source)

        climate = Climate.objects.create_climate( \
              name=get_climate_zone_name(climate_zone_id_str), \
              climate_zone=climate_zone_id_str, \
              data_source=data_source)
        log.info('\nCreated Climate object {} successfully.'.format(climate))

        climate.populate_data(climate_data)
        log.info('Populated data of Climate object {} successfully.'.format(climate))

        n_climate_zones += 1

    msg = '\nPopulated {} climate zones.'.format(n_climate_zones)
    log.info(msg)

    return redirect('sys:config_home')


"""
=================================
Project views
=================================
"""

# Show the project home page
def proj_list(request):

    # Retrieve a list of all Project objects in the DB
    projects = Project.objects.all()

    return render(request, 'system/project/list.html', {'projects' : projects})

# Create new project
def proj_create(request):

    # Retrieve form entries from edit template and strip leading and trailing spaces
    # If value is not found, use 'undefined'
    name = request.POST.get('name', 'undefined').lstrip().rstrip()
    size = request.POST.get('size', '1').lstrip().rstrip()

    # Ensure, that size is a valid integer
    try:
        int(size)
    except:
        log.error("Invalid size value. Setting to default size = 4.")
        size = '4'

    # If name is empty string or only whitespace(s)
    if name.isspace() or name == '':
        name = 'new project'

    # Create the Project object
    Project.objects.create_project(name=name, size=size)

    return redirect('sys:proj_list')

# Delete a project
def proj_delete(request, project_id):
    # Retrieve the requested project from the DB
    project = get_object_or_404(Project, pk=project_id)

    # Delete the Project object
    project.delete()
    return redirect('sys:proj_list')

# Set the project name
def proj_set_name(request, project_id):
    # Retrieve the requested project from the DB
    project = get_object_or_404(Project, pk=project_id)

    # Retrieve form entries (if value is not found, use the previous value)
    name = request.POST.get('name_' + str(project.id), "undefined")

    if name != "undefined" and name and name != "":
        project.name = name
        project.save()

    return HttpResponseRedirect(reverse('sys:proj_list', args=()))

# Show the edit view for the given project
def proj_edit(request, project_id):
    # Retrieve the requested project from the DB
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'system/project/edit.html', {'project' : project})

# Process the input from the form
def proj_form(request, project_id):
    # Retrieve the requested component from the DB
    project = get_object_or_404(Project, pk=project_id)
    occupancy = []
    at_home = []
    i = 0

    # Retrieve all households
    while True:
        occ = request.POST.get('occ-{}'.format(i), 'undefined')
        ah = request.POST.get('at_home-{}'.format(i), 'undefined')
        i+=1
        # Break the query as soon as all values have been retrieved
        if occ == 'undefined':
            break

        # Append the current household
        occupancy.append(int(occ))
        at_home.append(ah)

    # Change the retrieved data
    project.set_occupancy(occupancy)
    project.set_at_home(at_home)

    # Repopulate the data field
    project.populate_data(create_load(occupancy, at_home))

    return HttpResponseRedirect(reverse('sys:proj_list', args=()))


"""
=================================
Configuration views
=================================
"""

# Show the configuration home page
def config_home(request):
    # Get a list containing each a list of configuration type and readable name
    # Output form: [ ['system1', 'System 1 - Readable'], ['system2', 'System 2 - Readable'] ]
    types = Map().get_system_choices()

    # Retrieve a list of all Model objects in the DB
    configs = Configuration.objects.all()

    # Retrieve a list of all Model objects in the DB
    climates = Climate.objects.all()

    # Retrieve a list of all Model objects in the DB
    projects = Project.objects.all()

    # Retrieve a list of all Model objects in the DB
    components = Component.objects.all()

    # Assemble the list of arguments to pass to template
    args = {\
        'configs': configs, \
        'climates': climates, \
        'projects' : projects, \
        'components':components, \
        'types': types}

    return render(request, 'system/configuration/home.html', args)

# Create new configuration
def config_create(request, configuration_type):
    Configuration.objects.create_configuration(type=configuration_type)
    return redirect('sys:config_home')

# Delete a configuration and return to configuration home page
def config_delete(request, configuration_id):
    # Retrieve the requested configuration from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Delete the pickle file containing results (if existing)
    if config.results_path != 'undefined':
        delete_pickle('data/' + config.results_path)

    # Delete the Configuration object
    config.delete()
    return redirect('sys:config_home')

# Set the configuration name
def config_set_name(request, configuration_id):
    # Retrieve the requested configuration from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Retrieve form entries (if value is not found, use the previous value)
    name = request.POST.get('name_' + str(config.id), "undefined")

    if name != "undefined" and name and name != "":
        config.name = name
        config.save()

    return HttpResponseRedirect(reverse('sys:config_home', args=()))

# Set a climate for the configuration
def config_set_climate(request, configuration_id, climate_id):
    # Retrieve the requested configuration from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Retrieve the requested climate from the DB
    climate = get_object_or_404(Climate, pk=climate_id)

    # Set climate for the given configuration
    Configuration.objects.filter(pk=configuration_id).update( \
        climate=climate,\
        )

    return redirect('sys:config_home')

# Set a project for the configuration
def config_set_project(request, configuration_id, project_id):
    # Retrieve the requested configuration from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Retrieve the requested project from the DB
    project = get_object_or_404(Project, pk=project_id)

    # Set project for the given configuration
    Configuration.objects.filter(pk=configuration_id).update( \
        project=project,\
        )

    return redirect('sys:config_home')

# Remove a given component from a given configuration
def config_remove_component(request, configuration_id, component_id):
    # Retrieve the requested configuration from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Retrieve the requested component from the DB
    #component = get_object_or_404(Component, pk=component_id)      # This is an alternative to retrieve the object
    component = config.components.filter(id=component_id)

    # Remove the component from this configuration (but keep it as object in the DB)
    # This query set will always contain only one element (since the id is unique)
    config.components.remove(component[0])

    return redirect('sys:config_home')

# Set a component for the configuration
def config_add_component(request, configuration_id, component_id):
    # Retrieve the requested configuration from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Retrieve the requested component from the DB
    component = get_object_or_404(Component, pk=component_id)

    # Add the given component to this configuration
    config.components.add(component)

    return redirect('sys:config_home')

# Test function to invoke a simulation
def config_invoke(request, configuration_id):
    # Retrieve the requested component from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Check if config has been assigned
    errors = config.check_config()
    if errors:
        for error in errors:
            log.error(error)

        return redirect('sys:config_home')
    else:

        # *hg Add check if config already has been assigned a project object
        try:
            loads = config.project.get_data()
        except:
            log.error("No project data found, falling back to default (4 persons)")
            loads = load_loads_indiv()

        # *hg Add check if config already has been assigned a climate object
        try:
            weather = config.climate.get_data()
        except:
            log.error("No climate data found, falling back to default (San Francisco)")
            weather = load_weather()

        # Component Parameters
        # *hg Add check if config has been assigned all required parameters
        params = config.get_params_pd()

        # Backup Parameters
        # *hg Add check if config has been assigned all required backup parameters
        bckp_params = config.get_params_pd(backup=True)

        # Sizes
        sizes = config.get_sizes_pd()

        # Backup Sizes
        bckp_sizes = config.get_sizes_pd(backup=True)

        # Pack simulation parameters in a dictionary
        args = dict()
        args['type'] = config.type
        args['sizes'] = sizes
        args['loads'] = loads
        args['weather'] = weather
        args['params'] = params
        args['bckp_sizes'] = bckp_sizes
        args['bckp_params'] = bckp_params

        try:
            # Invoke the system simulation
            results = config.invoke_simulation(args)

            # Store results in pickle file and set path to results
            file_name = create_filename_pickle(['results', str(config.type), str(config.id)])
            store_pickle(results, 'data/' + file_name)
            config.set_results_path(file_name)

            # Redirect to the visualization page
            return redirect('sys:vi_list')

        except Exception as ex:
            log.error('Simulation could not be invoked: {}'.format(ex))
            return redirect('sys:config_home')


"""
=================================
Visualization views
=================================
"""

# Show the visualization list page
def vi_list(request):
    # Load all configurations from the database
    configs = Configuration.objects.all()

    # List containing all the plots to send to visualization page
    plots = []

    # Extract all found stored results
    for config in configs:
        if config.results_path != 'undefined':
            file_name = config.results_path
            try:
                plots.append(create_plot(results=load_pickle('data/' + file_name), name=config.name, id="{}".format(config.id)))
            except Exception as ex:
                log.error(ex)

    return render(request, 'system/visualization/list.html', {'plots': plots})

# Show only the results for a given configuration
def vi_plot(request, configuration_id):
    # Retrieve the requested component from the DB
    config = get_object_or_404(Configuration, pk=configuration_id)

    # Create the plot to send to template
    try:
        file_name = config.results_path
        plot = create_plot(results=load_pickle('data/' + file_name), name=config.name, id="{}".format(config.id))
    except Exception as ex:
        log.error(ex)

    return render(request, 'system/visualization/plot.html', {'plot': plot})
