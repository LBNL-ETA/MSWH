"""
=================================
General imports
=================================
"""

import pickle, ast, json
import os
from datetime import timedelta, datetime
import numpy as np
import pandas as pd
import logging
log = logging.getLogger(__name__)

"""
=================================
External project related content
=================================
"""

# Import swh_sys classes
from mswh.system.components import Converter, Storage, Distribution
from mswh.system.models import System
from mswh.tools.unit_converters import UnitConv
from mswh.system.source_and_sink import SourceAndSink
from mswh.comm.sql import Sql

# Get labels associated with swh_sys project
from mswh.comm.label_map import SwhLabels
SYSTEM_LABELS = SwhLabels().set_prod_labels()
CONSUMER_LABELS = SwhLabels().set_hous_labels()

# Edit this dictionary to add new components
COMPONENTS = {
    'converter' : { \
        'class' : Converter, \
        'types' : ['hp', 'pv', 'sol_col', 'el_res', 'gas_burn'] \
    },
    'storage' : { \
        'class' : Storage, \
        'types' : ['the_sto'] \
    },
    'distribution' : { \
        'class' : Distribution, \
        'types' : ['inv', 'dist_pump', 'sol_pump', 'piping'] \
    },
}

# Edit this dictionary to add new systems
SYSTEMS = {
    'solar_electric' : { \
        'class'     : System, \
        'components' : ['hp', 'pv', 'the_sto', 'inv', 'piping', 'dist_pump'], \
        'backup'     : ['el_res'], \
    },
    'solar_thermal_new' : { \
        'class'      : System, \
        'components' : ['sol_col', 'the_sto', 'sol_pump', 'piping', 'dist_pump'], \
        'backup'     : ['gas_burn'], \
    },
}

# These keys are not added to the web plot
FILTER = [
    'hour',
    'day',
    'month',
    'season',
]

"""
=================================
Mapping class
=================================
"""

class Map:
    def __init__(self, components=COMPONENTS, systems=SYSTEMS, consumer_labels=CONSUMER_LABELS, system_labels=SYSTEM_LABELS):
        self.components = components
        self.systems = systems
        self._c = consumer_labels
        self._s = system_labels

    def __str__(self):
        return "Components:\n{}\nSystems:\n{}".format(str(self.components), str(self.systems))

    # @property
    # def components(self):
    #     return self._components
    #
    # @components.setter
    # def components(self, value):
    #     self._components = value

    # Used in Component class for choices of type field
    # Output form: [ ['component_class1', ['comp1', 'Component 1 - Readable']], ['component_class2', ['comp2', 'Component 2 - Readable']] ]
    def get_component_choices(self):
        li = []
        for key, val in self.components.items():
            pairs = []
            for t in val['types']:
                pairs.append([t,self._s[t] if t in self._s else 'Undefined'])
            li.append([key, pairs])
        return li

    # Used in Configuration class for choices of type field
    # Output form: [ ['system1', 'System 1 - Readable'], ['system2', 'System 2 - Readable'] ]
    def get_system_choices(self):
        li = []
        for sys in self.systems:
            li.append([sys, self._s[sys] if sys in self._s else 'Undefined'])
        return li

    # Used for listing components in comp_list view function
    # Output form: {'component_class1': ['comp1', 'comp2'], 'component_class2': ['comp3', 'comp4']}
    def get_component_types(self):
        dic = {}
        for key, val in self.components.items():
            dic[key] = val['types']
        return dic

    # Returns a list of components for a given system
    # Output form: ['comp1', 'comp2', 'comp3']
    def get_system_components(self, system):
        return self.systems[system]['components'] if system in self.systems else None

    # Returns a list of backup components for a given system
    # Output form: ['comp1', 'comp2', 'comp3']
    def get_system_backup(self, system):
        return self.systems[system]['backup'] if system in self.systems else None

    # Used for instantiating external classes
    # Use like this: sys = Map().get_system_class()[<type of system>]( ... )
    def get_system_class(self):
        dic = {}
        for key, val in self.systems.items():
            dic[key] = val['class']
        return dic

    # This will be deprecated, when using simulate()    -> maybe still leave it hear, for generalizability ???
    #def get_system_function(self, system):
    #    return self.systems[system]['function'] if system in self.systems else None


    ######################
    # Not in use currently
    ######################
    # def get_classes_dict(self):
    #     dic = {'components': [], 'systems': []}
    #     for key, val in self.components.items():
    #         dic['components'].append(val['class'])
    #     for key, val in self.systems.items():
    #         dic['systems'].append(val['class'])
    #     return dic

    ######################
    # Not in use currently
    ######################
    # def get_swh_label(self, t):
    #     label = 'Undefined'
    #     if t in self._s:
    #         label = self._s[t]
    #     return label

    ######################
    # Not in use currently
    ######################
    # def get_class(self, t):
    #     c = None
    #     for key, val in self.components.items():
    #         if t in val['types']:
    #             c = key
    #             break
    #     return c


"""
=================================
Helper functions
=================================
"""

# Run the system simulation with a given set of simulation parameters
def simulate_system(args):

    # Create an object of the swh_sys System class
    sys = Map().get_system_class()[args['type']](\
        sys_sizes = args['sizes'], \
        loads = args['loads'], \
        weather = args['weather'], \
        sys_params = args['params'], \
        backup_sizes = args['bckp_sizes'], \
        backup_params = args['bckp_params'], \
        timestep = 1.0, \
        )

    # Invoke simulation of the respective system configuration
    cons_total, proj_total, sys_res = sys.simulate(type=args['type'])

    # Results are packed like this:
    # cons_total : [pd DataFrame]
    # proj_total : [pd Series]
    # sys_res    : [list] = 0 proj_total_dict,
    #                       1 sol_fra,
    #                       2 pump_el_use,
    #                       3 pump_op_hour,
    #                       4 ts_res,
    #                       5 backup_ts_cons,     -> only for solar_thermal
    #                       6 rel_err

    # Create dictionary with only the used components of the results
    results = dict()
    # results['cons_total'] = cons_total
    results['proj_total'] = sys_res[0]
    results['ts_res'] = sys_res[4]
    results['sol_fra'] = sys_res[1]

    return results

# Create a dictionary containing all plot data in the form of 'plot_data'
def create_plot(results, name, id):
    """
    plot_data = {
            'name': 'Empty Plot', \
            'id': '2',
            'index' : [0], \
            'series': {\
                'Q_hp' : {\
                    'data': [0], \
                    'name': 'Q_hp'}, \
                'Q_dem' : {\
                    'data': [0], \
                    'name': 'Q_dem'}, \
                }, \
            'totals': {\
                'Sol_Fra': {\
                    'name': 'Sol_Fra', \
                    'data': 0.5}, \
                'Q_hp' : {\
                    'data': 1000., \
                    'name': 'Q_hp'}, \
                'Q_dem' : {\
                    'data': 1000., \
                    'name': 'Q_dem'}, \
                }
            }
    """

    # Create totals data
    totals_data = {'Solar Fraction': round(results['sol_fra']['annual'], 3) * 100}

    # Add the project totals to totals_data
    totals_data.update(results['proj_total'])

    for key, val in results['proj_total'].items():
        # Convert from Kelvin to Celsius
        if ('Temperature' in key) and ('Drop' not in key) and (key not in FILTER):
            totals_data.update({key: round(UnitConv(val).degC_K(unit_in = 'K'),2)})


    totals = {'totals': totals_data}

    # Load timestep results
    ts_res = results['ts_res']

    # Insert the time series data
    series = {'series': {}}
    for key, val in ts_res.items():
        # Convert from Kelvin to Celsius
        if ('Temperature' in key) and ('Drop' not in key):
            ts_res[key] = round(UnitConv(ts_res[key]).degC_K(unit_in = 'K'),2)
        if key not in FILTER:
            series['series'][key] = {'name': key, 'data': ts_res[key].tolist()}

    # Create a dictionary containing the graph data (id holds the config id)
    plot = {'name': name, 'id': id, 'index' : json.dumps(hours2datetime(2018, len(ts_res.index)))}

    # Add the data key value pairs
    plot.update(series)
    plot.update(totals)

    return plot

# Convert hours of year to strftime formated datetime string
# Used in visualization app
def hours2datetime(year, h_duration):
    dt_str = []

    # Length of data passed from swh_sys (8761 hours)
    hours = h_duration

    if year < 1800 or year > 2200:
        year = 2018

    start = datetime(year=year, month=1, day=1)

    for i in range(hours):
        d = start + timedelta(hours=i)
        dt_str.append(d.strftime('%Y-%m-%d %H:%M:%S'))

    return dt_str

# Load data from pickle file
def load_pickle(file_name):
    with open(file_name, 'rb') as handle:
        results = pickle.load(handle)
    return results

# Store data to local pickle file
def store_pickle(data, file_name):
    res = False
    try:
        with open(file_name, 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        res = True
    except Exception as ex:
        log.error(ex)
    return res

# Delete a local pickle file
def delete_pickle(file_name):
    try:
        os.remove(file_name)
    except:
        log.error('File "{}" not found.'.format(file_name))

# Create a file name to pickle data
def create_filename_pickle(str_list):
    return '_'.join(str_list) + '.p'

# Load loads data from pickle file
def load_loads_indiv():
    with open('data/loads_indiv_val.p', 'rb') as handle:
        loads = pickle.load(handle)
    return loads

# Load weather data from pickle file
def load_weather():
    with open('data/sf_weather_test.p', 'rb') as handle:
        weather = pickle.load(handle)
    return weather

# Check validity of parameters
def check_params(p):
    try:
        p_string = ast.literal_eval(p)
        res = isinstance(p_string, dict)
    except:
        res = isinstance(p, dict)
    return res

# Convert dictionary formatted string to a dictionary
def str2dict(s):
    if (check_params(s)):
        d = ast.literal_eval(s)
    else:
        d = {'not_valid':'not_valid'}
    return d

# Convert pandas DataFrame to a dictionary
def df2dict(df):
    return df.to_dict()

# Convert dictionary to pandas DataFrame
def dict2df(dict):
    return pd.DataFrame.from_dict(dict)

# Return the name for a specific climate zone
def get_climate_zone_name(climate_zone):

    # These are the climate zones available in the external database
    climate_zone_to_name = {
        '01': 'Arcata, CA',         # TMY3 code: 725945
        '02': 'Santa Rosa, CA',     # TMY3 code: 724957
        '03': 'Oakland, CA',        # TMY3 code: 724930
        '04': 'San Jose, CA',       # TMY3 code: 724945
        '05': 'Santa Maria, CA',    # TMY3 code: 723940
        '06': 'Torrance, CA',       # TMY3 code: 722970
        '07': 'San Diego, CA',      # TMY3 code: 722900
        '08': 'Fullerton, CA',      # TMY3 code: 722976
        '09': 'Burbank, CA',        # TMY3 code: 722880
        '10': 'Riverside, CA',      # TMY3 code: 722869
        '11': 'Red Bluff, CA',      # TMY3 code: 725910
        '12': 'Sacramento, CA',     # TMY3 code: 724830
        '13': 'Fresno, CA',         # TMY3 code: 723890
        '14': 'Palmdale, CA',       # TMY3 code: 723820
        '15': 'Palm Springs, CA',   # TMY3 code: 722868
        '16': 'Blue Canyon, CA'     # TMY3 code: 725845
    }

    # Return the name if climate_zone is in dictionary, else return False
    return climate_zone_to_name.get(climate_zone, False)

# Return a numpy random state
def get_np_random_state():
    return np.random.RandomState(123)

# Return a random project configuration
def get_random_project(size):
    proj = {'occ': [], 'at_home': []}

    for i in range(size):
        proj['occ'].append(np.random.randint(1,7))
        proj['at_home'].append('y' if np.random.randint(1,100) <= 50 else 'n')

    return proj

# Create the hot water load data for project objects
def create_load(occupancy, at_home):

    # *hg Decide for either relative or absolute path
    if False:
        db_path = os.path.join(os.getcwd(), \
            'data/swh_input_weather_cons.db')
    else:
        db_path = 'data/swh_input_weather_cons.db'

    # Connecting to database
    try:
        db = Sql(db_path)
    except:
        log.error('Failed to connect to database.')

    # Converting sql to pandas DataFrame
    try:
        inputs = db.tables2dict(close = True)
    except:
        log.error('Failed to read input tables from DataFrame.')

    load, loadid_peakload = SourceAndSink._make_example_loading_inputs(\
        inputs, CONSUMER_LABELS, get_np_random_state(), \
        occupancy = occupancy, at_home = at_home)
    return load
