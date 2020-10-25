import logging
import os
import shutil

from sql import Sql

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Create a system input db by running this file as a python script

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This file contains the sql code to create the a database used
# in running the MSWH code:
# - code to create or update the database, including all the
#   values to populate the tables
# The database structure defines:
# - the variable dependencies
# - how the code handles the tables (through naming conventions)

# CEC weather data, alongside with the TMY3 data for CA are
# preloaded in the template db (mswh_input_weather_cons.db).
# There are example loads for 128 households with various
# occupancies in the template db as well.
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

test_db_name = 'mswh_system_input.db'

# set write_new to True if you'd like to reinitiate the db. A copy of the
# 'swh_system_input.db' will be saved with a 'bckp_' prefix.

# create database using python
sql_scripts = list()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# scripts to drop tabes if rewriting them

sql_scripts.append('''DROP TABLE IF EXISTS `sys_1_system_list`;
''')
sql_scripts.append('''DROP TABLE IF EXISTS `sys_2_system_configurations`;
''')
sql_scripts.append('''DROP TABLE IF EXISTS `sys_3_components`;
''')

# component sizing tables

sql_scripts.append('''DROP TABLE IF EXISTS `comp_1_sizing_regression`;
''')
sql_scripts.append('''DROP TABLE IF EXISTS `discrete_component_sizes`;
''')

# component performance parameters

sql_scripts.append('''DROP TABLE IF EXISTS `component_performance`;
''')

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# DB schema

# lists system configurations
sql_scripts.append('''CREATE TABLE `sys_1_system_list`
(
    `System ID` INTEGER NOT NULL,
    `System` TEXT NOT NULL,
    `System Description` TEXT NOT NULL,
    `Retrofit` BOOLEAN NOT NULL,

    PRIMARY KEY (`System ID`)
);''')

sql_scripts.append('''CREATE TABLE `sys_3_components`
(
    `Component ID` INTEGER NOT NULL,
    `Component` TEXT NOT NULL,
    `Component Technology` TEXT NOT NULL,
    `Component Size Unit` TEXT NOT NULL,

    PRIMARY KEY (`Component ID`)
);''')

# defines system configurations
sql_scripts.append('''CREATE TABLE `sys_2_system_configurations`
(
    `System ID` INTEGER NOT NULL,
    `Component ID` INTEGER NOT NULL,
    `Component Function` TEXT NOT NULL,

    FOREIGN KEY (`System ID`) REFERENCES `sys_1_system_list`(`System ID`),
    FOREIGN KEY (`Component ID`) REFERENCES `sys_3_components`(`Component ID`)
);''')

# components, technologies and performance parameters
sql_scripts.append('''CREATE TABLE `component_performance`
(
    `Component ID` INTEGER NOT NULL,
    `Performance Parameter` TEXT NOT NULL,
    `Performance Parameter Value` REAL NOT NULL,
    `Performance Parameter Unit` TEXT NOT NULL,

    FOREIGN KEY (`Component ID`) REFERENCES `sys_3_components`(`Component ID`)
);''')

# component sizing
sql_scripts.append('''CREATE TABLE `comp_1_sizing_regression`
(
    `Component ID` INTEGER NOT NULL,
    `Component Size Fit` TEXT NOT NULL,
    `Component Size Fit Parameters` TEXT NOT NULL,
    `Component Size Function Of` TEXT NOT NULL,

    FOREIGN KEY (`Component ID`) REFERENCES `sys_3_components`(`Component ID`)
);''')

# discrete component sizes available on the market
sql_scripts.append('''CREATE TABLE `discrete_component_sizes`
(
    `Component ID` INTEGER NOT NULL,
    `Discrete Size` TEXT NOT NULL,

    FOREIGN KEY (`Component ID`) REFERENCES `sys_3_components`(`Component ID`)
);''')

# populate tables
# Dynamic path implementation
# This check should always pass unless the git repo is restructured
if os.getcwd()[-4:] == 'comm':
    output_path = \
    r'W:\Non-APS\CEC PIER\PIER Solar Water Heating\Analysis\Results\Test'
else:
    msg = 'Not currently operating out of comm directory.'
    log.info(msg)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# scripts to populate the db

# component list
sql_scripts.append('''INSERT INTO `sys_3_components` (`Component ID`, `Component`, `Component Technology`, `Component Size Unit`) VALUES
(1, 'solar collector', 'flat plate', 'm2'),
(2, 'solar collector', 'tubular', 'm2'),
(3, 'pv', 'monocrystalline', 'W'),
(4, 'pv', 'polycrystalline', 'W'),
(5, 'gas tank WH', 'conventional gas tank water heater', 'm3'),
(6, 'electric resistance tank WH', 'conventional electric resistance tank water heater', 'm3'),
(7, 'thermal storage tank', 'thermal storage tank with an in-tank coil', 'm3'),
(8, 'gas burner', 'gas burner', 'W'),
(9, 'electric resistance heater', 'in-tank or instantaneous', 'W'),
(10, 'heat pump', 'in-tank', 'W'),
(11, 'battery storage', 'stores PV generated power', 'kWh'),
(12, 'distribution pump', 'fixed-speed circulator pump', 'W'),
(13, 'solar pump', 'fixed-speed circulator pump', 'W'),
(14, 'piping', 'dhw pipes', 'm'),
(15, 'inverter', 'dc-ac', 'W')
;''')

# system list
sql_scripts.append('''INSERT INTO `sys_1_system_list` (`System ID`, `System`, `System Description`, `Retrofit`) VALUES
(1, 'gas tank wh', 'basecase', 'false'),
(2, 'electric tank wh', 'basecase', 'false'),
(3, 'gas inst wh', 'basecase', 'false'),
(4, 'electric inst wh', 'basecase', 'false'),
(5, 'solar thermal retrofit', 'solar thermal collector, solar tank, backup: tank or instantaneous WH (whichever exists in the household)', 'true'),
(6, 'solar thermal new', 'solar thermal collector, solar tank, instantaneous gas WH', 'false'),
(7, 'solar thermal electric backup', 'solar thermal collector, solar tank, instantaneous electric WH', 'false'),
(8, 'solar electric', 'PV, HP tank WH with electric in-tank backup', 'false')
;''')

# system configuration
# any components that exist in both the base and policy cases are omited in the list
# any components inherited from the basecase (case: retrofits) are omited in the list
sql_scripts.append('''INSERT INTO `sys_2_system_configurations` (`System ID`, `Component ID`, `Component Function`) VALUES
(1, 5, 'stores domestic hot water, adds heat through gas combustion'),
(5, 1, 'solar thermal collector'),
(5, 7, 'solar storage tank'),
(5, 12, 'circulates dhw in the secondary (distribution) loop, if community scale'),
(5, 13, 'circulates dhw in the primary (solar) loop'),
(5, 14, 'distribution pipes'),
(6, 1, 'solar thermal collector'),
(6, 7, 'solar storage tank'),
(6, 8, 'backup'),
(6, 12, 'circulates dhw in the secondary (distribution) loop, if community scale'),
(6, 13, 'circulates dhw in the primary (solar) loop'),
(6, 14, 'distribution pipes')
;''')

# Notes:
# Performance Parameter string may be repeated only for storage components.
# U-value = 1/ R-value = specific heat conductivity / insulation thickness
# unit conversions http://www.fomicom.com/files/insulation%20values.pdf:
# 1 ft²·°F·h/Btu ≈ 0.1761 K·m²/W, or 1 K·m²/W ≈ 5.67446ft²·°F·h/Btu
# values chosen for piping loss equal R2.6, in line with CSI recommendation
# values chosen for solar tank loss equal R12, in line with CSI recommendation
# values chosen for gas tank WH are in line with EL1 WH rule 2010, 30 gal tank
# with ~R2.1
# pipe diameter sizing paremeters are derived in the pipe sizing and
# pricing notebook (see scripts folder), the first
# higher value gets chosen. Discrete diameters taken from RS Means
# pipe pricing parameters include insulation cost.
# They are provided in this table and not in the component
# sizing table, since the price depends both on the diameter and the length
# Coil efficiency for any indirect tank excludes the approach temperature
# Inverter efficiency includes all losses related to dc-ac conversion

sql_scripts.append('''INSERT INTO `component_performance` (`Component ID`, `Performance Parameter`, `Performance Parameter Value`, `Performance Parameter Unit`) VALUES
(1, 'interc hwb', .753, '-'),
(1, 'slope hwb', -4.025, 'W/m2K'),
(1, 'interc cd', .75, '-'),
(1, 'a1 cd', -3.688, 'W/m2K'),
(1, 'a2 cd', -.0055, 'W/m2K2'),
(4, 'PV efficiency', .16, '-'),
(4, 'fraction of active PV area', 1., '-'),
(4, 'reference irradiation', 1000., 'W/m2'),
(5, 'tank recovery efficiency', .78, '-'),
(5, 'tap temperature setpoint', 322.04, 'K'),
(5, 'insulation thickness', .03, 'm'),
(5, 'specific heat conductivity', .081, 'W/mK'),
(7, 'insulation thickness', .085, 'm'),
(7, 'specific heat conductivity', .04, 'W/mK'),
(7, 'upper volume fraction', .5, '-'),
(7, 'height vs. radius', 6., '-'),
(7, 'temperature difference (approach)', 2., 'K'),
(7, 'maximum temperature', 344.15, 'K'),
(7, 'tap temperature setpoint', 322.04, 'K'),
(7, 'coil efficiency', .84, '-'),
(8, 'combustion efficiency', .85, '-'),
(9, 'efficiency', 1., '-'),
(10, 'rated heating capacity', 2350., 'W'),
(10, 'rated COP', 2.43, '-'),
(10, 'c1_cop', 1.229E+00, '-'),
(10, 'c2_cop', 5.549E-02, '1/degC'),
(10, 'c3_cop', 1.139E-04, '1/degC2'),
(10, 'c4_cop', -1.128E-02, '-'),
(10, 'c5_cop', -3.570E-06, '1/degC'),
(10, 'c6_cop', -7.234E-04, '1/degC2'),
(10, 'c1_heat_cap', 7.055E-01, '-'),
(10, 'c2_heat_cap', 3.945E-02, '-'),
(10, 'c3_heat_cap', 1.433E-04, '-'),
(10, 'c4_heat_cap', 2.768E-03, '-'),
(10, 'c5_heat_cap', -1.069E-04, '-'),
(10, 'c6_heat_cap', -2.494E-04, '-'),
(12, 'nominal distribution pump efficiency', .85, '-'),
(13, 'nominal solar pump efficiency', .85, '-'),
(14, 'piping insulation specific heat conductivity', .0175, 'W/mK'),
(14, 'piping insulation thickness', 0.008, 'm'),
(14, 'diameter vs. length scaler', 0.007911283766743384, 'm'),
(14, 'diameter vs. length exponent', 0.43082708345352605, 'm'),
(14, 'single-family attached scaler', 3., '-'),
(14, 'single-family detached scaler', 6., '-'),
(14, 'discrete diameters', '[0.0127, 0.01905, 0.0254, 0.03175, 0.0381, 0.0508, 0.0635, 0.0762, 0.1016]', 'm'),
(14, 'flow factor', .8, '-'),
(14, 'circulation', 0., '-'),
(14, 'longest branch length fraction', 1., '-'),
(15, 'DC to AC efficiency', .85, '-')
;''')

# component sizing

# `linear` fits (y = b + m * x) have parameters in order of [b, m]
# `power` fits (y = m * (x ^ b)) have parameters in order of [m, b]

# a) solar collector (solar thermal panel area) - CSI sizing rule:
# upper limit 1.25 * GPD [sqft]
# b) conventional storage tanks: (https://www.energy.gov/energysaver/water-heating/sizing-new-water-heater) peak hourly demand +/- 2 gal, using +/- 0 gal.
# c) solar storage tank: CSI sizing rule lower limit
# 1.25 * collector_area_sqft [gal]
# d) instantaneous water heaters: based on email from Victor and standard input powers taken from homedepot.com

# note that for the retrofits the size of the backup tank WHs gets taken
# from the basecase, since they remain in each of the households
# units: SI
sql_scripts.append('''INSERT INTO `comp_1_sizing_regression` (`Component ID`, `Component Size Fit`, `Component Size Fit Parameters`, `Component Size Function Of`) VALUES
(1, 'linear', '[0., 0.111483648]', 'Demand Estimate [GPD]'),
(2, 'linear', '[2.2297, 0.7432]', 'Occupancy'),
(5, 'linear', '[0., 0.003785412]', 'Peak End-Use Load [gal]'),
(6, 'linear', '[0., 0.003785412]', 'Peak End-Use Load [gal]'),
(7, 'linear', '[0., 0.00590524272]', 'Demand Estimate [GPD]'),
(8, 'power', '[24875., 0.5175]', 'Occupancy'),
(9, 'power', '[18020., 0.4204]', 'Occupancy'),
(12, 'power', '[10.4376, 0.9277]', 'Households Per Project'),
(13, 'power', '[7.5101, 0.5322]', 'Occupancy'),
(14, 'linear', '[0., 3.048]', 'Households Per Project'),
(15, 'linear', '[0., 11111.]', 'Occupancy')
;''')

# Discrete sizes for component 5 are the union of sizes
# available in public CEC, CCMS, and AHRI certification datasets
sql_scripts.append('''INSERT INTO `discrete_component_sizes` (`Component ID`, `Discrete Size`) VALUES
(5, '[20, 28, 29, 30, 33, 34, 37, 38, 39, 40, 46, 47, 48, 49, 50, 53, 55, 60, 63, 65, 71, 72, 73, 75, 80, 81, 93, 95, 96, 98, 100, 112]')
;''')

sql_scripts.append('''PRAGMA foreign_keys = OFF;''');

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# writing and saving the db

answer = input(
    '\nAre you ok with overwriting the \'bckp_*.db\' file? \'y/n\' ')
if answer != 'y':
    msg = 'Canceled, please save the backup file under a different name and run again.'
    log.error(msg)
    raise Exception

weather_cons_db_name = 'weather_and_loads.db'

template_db_fulpath = os.path.join(
    os.path.dirname(__file__), test_db_name)

weather_cons_db_name_fulpath = os.path.join(
    os.path.dirname(__file__), weather_cons_db_name)


if os.path.exists(template_db_fulpath):
    bckp_filename = 'bckp_' + test_db_name
    if os.path.exists(bckp_filename):
        os.remove(os.path.join(
            os.path.dirname(__file__),
            bckp_filename))
    os.rename(template_db_fulpath,
              os.path.join(
                  os.path.dirname(__file__),
                  bckp_filename))
os.rename(weather_cons_db_name_fulpath,
          template_db_fulpath)
shutil.copy(template_db_fulpath, weather_cons_db_name_fulpath)

# open the connection with the db
mswh_input_template = Sql(template_db_fulpath)

# write to db

# from above sql scripts
for script in sql_scripts:
    mswh_input_template.commit(script)
