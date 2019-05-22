import logging

import numpy as np
import pandas as pd

from mswh.system.components import Converter, Storage, Distribution
from mswh.tools.unit_converters import UnitConv
from mswh.comm.label_map import SwhLabels

log = logging.getLogger(__name__)


class System(object):
    """Project level system models:

    * Assembles system configurations
    * Performs timestep simulation
    * Returns annual and timestep project and household
      level results, such as gas and electricity use, heat delivered,
      unmet demand and solar fraction.

    Parameters:

        sys_params: pd df
            Main system component performance parameters per project
            Default: None (default model parameters will get used)

        backup_params: pd df
            Backup system performance parameters per project.
            It should contain a household ID column, otherwise
            columns identical to params.

        sys_sizes: pd df
            Main system component sizes
            Default: 1. (see individual components for specifics)

        backup_sizes: pd df
            Backup system component sizes, contains household id column
            Default: 1. (see individual components for specifics)

        weather: pd df
            Weather data timeseries.
            Number of rows equals the number of timesteps. Can be
            generated using the Source.irradiation_and_water_main
            method

            Example:

            >>> sourceASource(read_from_input_dataframes = inputs)

            Oakland climate zone in CEC weather data is '03':

            >>> self.weather = source.irradiation_and_water_main('03', method='isotropic diffuse', use_in_test = True)

        loads: pd df
            A dataframe with loads for all individual household
            served by the project level system. It should
            contain 3 columns: household id, occupancy and a column
            with a load array in m3 for each household.

            Example:

            >>> loads_com = pd.DataFrame(data = [[1, occ_indiv - 1., 0.8 * load_array],[2, occ_indiv, 1. * load_array],[3, occ_indiv, 1.2 * load_array],[4, occ_indiv + 1., 1.4 * load_array]],\
                    columns = [self.c['id'], self.c['occ'], self.c['load_m3']])

        timestep: float, h
            Duration of a single timestep, in hours
            Default: 1. h

        log_level: None or python logger logging level,
            Default: logging.DEBUG
            This applies for a subset of the class functionality, mostly
            used to deprecate logger messages for certain calculations.
            For Example: log_level = logging.ERROR will only throw error
            messages and ignore INFO, DEBUG and WARNING.

    Examples:

        See ```swh.system.tests.test_models``` module and
        ```scripts/Project Level SWH System Tool.ipynb```
        for examples on how to set up models for simulation.
    """
    def __init__(self, sys_params=None, backup_params=None, \
            weather=None, sys_sizes=1., backup_sizes=1., \
        loads=None, timestep=1., log_level=logging.DEBUG):

        # log level (e.g. only partial functionality of the class
        # is being used and one does not desire to see all infos)
        self.log_level = log_level
        logging.getLogger().setLevel(log_level)

        self.s = SwhLabels().set_prod_labels()
        self.c = SwhLabels().set_hous_labels()
        self.r = SwhLabels().set_res_labels()

        # assume individual system unless the loads contain multiple
        # individual household loads
        self.community = False

        # main system performance parameters
        self.sys_params = sys_params
        # backup system performance parameters
        self.backup_params = backup_params
        self.weather = weather

        # prepare loads
        if loads is None:
            self.load = 0.01  # m3
            msg = 'The system did not receive any load requirement. '\
                  'Setting hot water draw to 0.01 m3/h.'
            log.info(msg)

            # initiate household level result df assuming 4
            # occupants
            self.cons_total = pd.DataFrame(
                data=[[1, 4]],
                columns=[self.c['id'], self.c['occ']])

            # for the distribution losses
            self.load_max = self.load * 1.

        else:
            # initiate household level result df
            self.cons_total = pd.DataFrame(
                columns=[self.c['id'], self.c['occ'], self.r['gas_use'],
                         self.r['gas_use_s'], self.r['gas_use_w'],
                         self.r['el_use'],
                         self.r['el_use_s'], self.r['el_use_w'],
                         self.r['sol_fra'],
                         self.r['q_del_bckp'], self.r['q_unmet']])

            self.cons_total[self.c['id']] = loads[self.c['id']]
            self.cons_total[self.c['occ']] = loads[self.c['occ']]

            self.indiv_loads = pd.DataFrame(loads)

            if loads.shape[0] > 1:
                self.community = True

            # set community load by summing individual loads
            sum_loads = pd.DataFrame([(loads * 1.).sum()])
            self.load = sum_loads[self.c['load_m3']].values[0] * 1.
            self.loads = loads * 1.

            # annual fractions for each household
            ann_cons_fract = loads[self.c['load_m3']].apply(
                    lambda x: x.sum()) / self.load.sum()

            # this is only to avoid division zero
            sum_loads.loc[0, self.c['load_m3']][
                sum_loads.loc[0, self.c['load_m3']] == 0] = np.inf

            # timeseries household load fractions in the
            # community load profile
            self.indiv_load_ratios = loads * 1.

            self.indiv_load_ratios[self.c['load_m3']] = (
                loads[self.c['load_m3']] /
                pd.concat(
                    [sum_loads[self.c['load_m3']]] * loads.shape[0],
                    ignore_index=True))

            self.indiv_load_ratios[self.c['id']] = loads[self.c['id']]
            self.indiv_load_ratios[self.c['occ']] = loads[self.c['occ']]
            # prepare for usage after simulation (+1 timestep)
            self.indiv_load_ratios[self.c['load_m3']] = \
                self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: np.nan_to_num(np.append(0, x)))
            # household load fractions in the total load
            self.indiv_load_ratios['ann_cons_fract'] = ann_cons_fract

            # for the distribution system
            self.load_max = self.load.max()

        # main system component sizes
        self.sys_sizes = sys_sizes
        # backup system component sizes
        self.backup_sizes = backup_sizes

        self.timestep = timestep
        self.num_timesteps = len(self.load)

    @property
    def weather(self):
        return self.__weather

    @weather.setter
    def weather(self, value):
        """Re-extracts weather timeseries if a new weather dataset
        is assigned to an instantiated class objectsolar_electric
        """
        self.__weather = value
        if isinstance(value, pd.DataFrame):
            self.t_amb = UnitConv(
                self.weather[self.c['t_amb_C']].values).degC_K(unit_in='degC')
            self.t_wet_bulb = UnitConv(
                self.weather[self.c['t_wet_bulb_C']].values).degC_K(unit_in='degC')
            self.inc_rad = self.weather[self.c['irrad_on_tilt']].values
            self.t_main = UnitConv(
                self.weather[self.c['t_main_C']].values).degC_K(unit_in='degC')
            self.month = np.append(1, self.weather[self.c['month']].values)
            self.season = np.append(
                'winter',
                self.weather[self.c['season']].values)
            self.it_is_summer = self.season == self.c['summer']
            self.it_is_winter = self.season == self.c['winter']

            self.day = np.append(1, self.weather[self.c['day']].values)
            self.hour = np.append(1, self.weather[self.c['hour']].values)

            msg = 'Assigned weather data timeseries.'
            log.info(msg)

        elif not value:
            self.t_amb = 293.15  # K
            self.t_wet_bulb = 283.15  # K
            self.inc_rad = 800  # W
            self.t_main = 291.15  # K
            self.month = None
            self.day = None
            self.season = None

            msg = 'No weather data got passed to converters. '\
                  'Setting default scalar values for ambient temperature, '\
                  '{}, and solar irradiation, {}.'
            log.info(msg.format(self.t_amb, self.inc_rad))

    def solar_thermal(self, backup='gas'):
        """Connects the components of the solar thermal system and
        simulates it in discrete timesteps.

        Parameters:

            backup: string
                retrofit - pulls from the basecase for each household
                gas, electric - instantaneous WHs (new installations)

        Returns:

            self.cons_total: pd df
                Consumer level energy use [W], heat rates [W],
                average temperatures [K],
                and solar fraction for the analysis period.

            proj_total: pd series
                Project level energy use [W], heat rates [W],
                average temperatures [K],
                and solar fraction for the analysis period.

            sol_fra: dict
                Solar fraction. Keys: 'annual', 'monthly'

            pump_el_use: dict
                Electricity use broken into end uses
                'dist_pump' - distribution pump, if present
                'sol_pump' - solar pump

            ts_res: pd df
                Timestep project level results for all energy uses [W],
                heat rates [W], temperatures [K], and the load.

            backup_ts_cons: dict of dicts
                Timestep household level results for energy uses [W],
                and heat rates [W].

            rel_err: float
                Balancing error due to limitations of finite
                timestep averaging.
        """

        # initiate a dataframe with hourly results
        ts_res = pd.DataFrame(index=range(0, self.num_timesteps + 1))

        # components
        converters = Converter(
            params=self.sys_params,
            weather=self.weather,
            sizes=self.sys_sizes,
            log_level=self.log_level)

        indirect_tank = Storage(
            params=self.sys_params,
            type='sol_tank',
            size=self.sys_sizes,
            timestep=self.timestep,
            log_level=self.log_level)

        # Initiate arrays to hold the results during calculation
        # (improved performance with arrays, assigning to df post-calc)

        T_coil_out = np.empty(self.num_timesteps + 1)
        Q_sol_col = np.zeros(self.num_timesteps + 1)

        # demand heat rate
        Q_dem = np.zeros(self.num_timesteps + 1)
        Q_dem_with_dist_loss = np.zeros(self.num_timesteps + 1)
        q_dem_balance = np.zeros(self.num_timesteps + 1)

        # input solar tank gain and loss heat rates
        Q_coil_sol_tank = np.zeros(self.num_timesteps + 1)
        Q_loss_lower_sol_tank = np.zeros(self.num_timesteps + 1)
        Q_loss_upper_sol_tank = np.zeros(self.num_timesteps + 1)

        # output solar tank heat rates
        Q_del_sol_tank = np.zeros(self.num_timesteps + 1)
        Q_unmet_sol_tank = np.zeros(self.num_timesteps + 1)
        Q_dump_sol_tank = np.zeros(self.num_timesteps + 1)
        Q_ovrcool_sol_tank = np.zeros(self.num_timesteps + 1)

        # tank temperature states
        T_upper_sol_tank = np.empty(self.num_timesteps + 1)
        T_lower_sol_tank = np.empty(self.num_timesteps + 1)
        T_set = np.empty(self.num_timesteps + 1)
        dT_dist_loss = np.empty(self.num_timesteps + 1)
        Q_dist_loss = np.empty(self.num_timesteps + 1)

        # instantaneous gas wh states
        Q_del_bckp = np.zeros(self.num_timesteps + 1)
        Q_gas_use_bckp = np.zeros(self.num_timesteps + 1)
        Q_unmet = np.zeros(self.num_timesteps + 1)

        # pump on time timestep fractions
        Q_pump_on_fraction = np.empty(self.num_timesteps + 1)

        # set values for the initial timestep
        T_coil_out[0] = self.t_main[0]
        T_upper_sol_tank[0] = self.t_main[0]
        T_lower_sol_tank[0] = self.t_main[0]

        # simulate main system
        for ts in range(self.num_timesteps):

            sol_col_res = converters.solar_collector(
                    T_coil_out[ts],
                    t_amb=self.t_amb[ts],
                    inc_rad=self.inc_rad[ts])

            # gross collector gain that gets fed into the tank coil
            Q_sol_col[ts] = sol_col_res['Q_gain']

            sto_res = indirect_tank.thermal_tank(
                pre_T_amb=self.t_amb[ts],
                pre_T_feed=self.t_main[ts],
                pre_T_upper=T_upper_sol_tank[ts],
                pre_T_lower=T_lower_sol_tank[ts],
                pre_V_tap=self.load[ts],
                pre_Q_in=Q_sol_col[ts],
                max_V_tap=self.load_max)

            # solar collector return temperature (from tank)
            T_coil_out[ts + 1] = sto_res[self.r['t_coil_out']]

            # demand heat rate
            Q_dem[ts + 1] = sto_res[self.r['q_dem']]
            Q_dem_with_dist_loss[ts + 1] = sto_res[self.r['q_dem_tot']]
            q_dem_balance[ts + 1] = sto_res[self.r['q_dem_balance']]

            # solar tank heat sources
            Q_coil_sol_tank[ts + 1] = sto_res[self.r['q_del_sol']]
            Q_ovrcool_sol_tank[ts + 1] = sto_res[self.r['q_ovrcool_tank']]

            # solar tank heat sinks
            Q_loss_lower_sol_tank[ts + 1] = sto_res[self.r['q_loss_low']]
            Q_loss_upper_sol_tank[ts + 1] = sto_res[self.r['q_loss_up']]
            Q_del_sol_tank[ts + 1] = sto_res[self.r['q_del_tank']]
            Q_unmet_sol_tank[ts + 1] = sto_res[self.r['q_unmet_tank']]
            Q_dump_sol_tank[ts + 1] = sto_res[self.r['q_dump']]

            # tank temperatures and set temperature
            T_upper_sol_tank[ts + 1] = sto_res[self.r['t_tank_up']]
            T_lower_sol_tank[ts + 1] = sto_res[self.r['t_tank_low']]
            T_set[ts + 1] = sto_res[self.r['t_set']]

            # distribution system
            dT_dist_loss[ts + 1] = sto_res[self.r['dt_dist']]
            Q_dist_loss[ts + 1] = sto_res[self.r['q_dist_loss']]
            Q_pump_on_fraction[ts + 1] = sto_res[self.r['flow_on_frac']]

        # simulate backup heater and assign household level gas
        # consumption
        if backup == 'gas':
            backup_proj_total, backup_ts_proj, backup_ts_cons = \
                self._gas_instantaneous_backup(
                    Q_unmet_sol_tank,
                    Q_dist_loss)
        elif backup == 'retrofit':
            backup_proj_total, backup_ts_proj, backup_ts_cons = \
                self._gas_tank_backup(
                    (np.append(0., T_upper_sol_tank[:self.num_timesteps]) -
                     np.append(0., dT_dist_loss[:self.num_timesteps])),
                    np.append(0., T_upper_sol_tank[:self.num_timesteps]))
        else:
            msg = 'Backup types supported are gas or retrofit. '\
                  'Please provide one of the supported types.'
            log.error(msg)
            raise ValueError

        # Please be aware that outputs in step (ts + 1) are results
        # for the inputs in step ts
        ts_res[self.r['q_dem']] = Q_dem
        ts_res[self.r['q_dem_tot']] = Q_dem_with_dist_loss
        ts_res[self.r['q_dem_balance']] = q_dem_balance
        ts_res[self.r['q_del_sol']] = Q_coil_sol_tank
        ts_res[self.r['q_loss_low']] = Q_loss_lower_sol_tank
        ts_res[self.r['q_loss_up']] = Q_loss_upper_sol_tank
        ts_res[self.r['q_del_tank']] = Q_del_sol_tank
        ts_res[self.r['q_unmet_tank']] = Q_unmet_sol_tank
        ts_res[self.r['q_dump']] = Q_dump_sol_tank
        ts_res[self.r['q_ovrcool_tank']] = Q_ovrcool_sol_tank
        ts_res[self.r['t_tank_up']] = T_upper_sol_tank
        ts_res[self.r['t_tank_low']] = T_lower_sol_tank
        ts_res[self.r['t_coil_out']] = T_coil_out
        ts_res[self.r['t_set']] = T_set
        ts_res[self.r['dt_dist']] = dT_dist_loss
        ts_res[self.r['q_dist_loss']] = Q_dist_loss
        ts_res[self.r['q_dist_loss_at_bckp']] = np.minimum(
            Q_dist_loss,
            Q_unmet_sol_tank) * (Q_unmet_sol_tank > 0.)
        ts_res[self.r['q_dist_loss_at_bckp_sum']] = np.minimum(
            Q_dist_loss,
            Q_unmet_sol_tank) * (Q_unmet_sol_tank > 0.) * self.it_is_summer
        ts_res[self.r['q_dist_loss_at_bckp_win']] = np.minimum(
            Q_dist_loss,
            Q_unmet_sol_tank) * (Q_unmet_sol_tank > 0.) * self.it_is_winter

        ts_res[self.r['q_del_bckp']] = backup_ts_proj[self.r['q_del_bckp']]
        ts_res[self.r['gas_use']] = backup_ts_proj[self.r['gas_use']]
        ts_res[self.r['gas_use_s']] = backup_ts_proj[self.r['gas_use_s']]
        ts_res[self.r['gas_use_w']] = backup_ts_proj[self.r['gas_use_w']]
        ts_res[self.r['gas_use_no_dist']] = backup_ts_proj[
            self.r['gas_use_no_dist']]
        ts_res[self.r['gas_use_s_no_dist']] = backup_ts_proj[
            self.r['gas_use_s_no_dist']]
        ts_res[self.r['gas_use_w_no_dist']] = backup_ts_proj[
            self.r['gas_use_w_no_dist']]
        ts_res[self.r['q_unmet']] = backup_ts_proj[self.r['q_unmet']]

        ts_res[self.r['q_del']] = (Q_del_sol_tank +
            backup_ts_proj[self.r['q_del_bckp']])

        # store timestep weather and water main inputs
        ts_res[self.c['t_amb']] = np.append(0., self.t_amb)
        ts_res[self.c['t_main']] = np.append(0., self.t_main)
        # store load
        ts_res[self.r['proj_load']] = np.append(0., self.load)

        # get average temperatures and total heat rates
        t_columns = [col for col in ts_res.columns if 'Temperature' in col]
        # all other columns contain timestep heat rate
        q_columns = [x for x in (set(ts_res.columns) - set(t_columns))]

        # project results
        proj_total = ts_res.sum()
        proj_total[t_columns] = ts_res[t_columns].mean()
        proj_total[self.r['proj_load']] = ts_res[self.r['proj_load']].mean()

        if not proj_total[self.r['gas_use']] == \
            backup_proj_total[self.r['gas_use']]:
            msg = 'Check project output of the backup - timestep '\
                  'sum preformed in this method and the total are '\
                  'not equal.'
            log.error(msg)
            raise Exception

        # household results (annual quantities split according
        # to individual loads)
        self.cons_total[self.r['q_dem']] = self.indiv_load_ratios[
            self.c['load_m3']].apply(
                lambda x: (x * Q_dem).sum())

        self.cons_total[self.r['q_del']] = (self.timestep *
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * Q_del_sol_tank).sum()) +
            self.cons_total[self.r['q_del_bckp']])

        self.cons_total[self.r['q_unmet_tank']] = (self.timestep *
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * Q_unmet_sol_tank).sum()))

        self.cons_total[self.r['q_del_tank']] = (self.timestep *
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * Q_del_sol_tank).sum()))

        self.cons_total[self.r['q_dist_loss']] = (self.timestep *
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * Q_dist_loss).sum()))

        self.cons_total[self.r['q_dist_loss_at_bckp']] = (self.timestep *\
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * ts_res[
                    self.r['q_dist_loss_at_bckp']].values).sum()))

        self.cons_total[self.r['q_dist_loss_at_bckp_win']] = (self.timestep *
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * ts_res[
                    self.r['q_dist_loss_at_bckp_win']].values).sum()))

        self.cons_total[self.r['q_dist_loss_at_bckp_sum']] = (self.timestep *
            self.indiv_load_ratios[self.c['load_m3']].apply(
                lambda x: (x * ts_res[
                    self.r['q_dist_loss_at_bckp_sum']].values).sum()))

        # Calculate pump electricity consumption
        if self.community:
            dist_pump_on_timestep_frac = Q_pump_on_fraction * 1.
        else:
            # single households do not require
            # a distribution pump due to the
            # water main pressure
            dist_pump_on_timestep_frac = None

        pump_ts_el_use, pump_el_use, pump_op_hour = self._get_pump_energy_use(
            dist_pump_on_timestep_frac=dist_pump_on_timestep_frac,
            gain_from_collector=Q_coil_sol_tank)

        # Store project level electricity consumption
        proj_total[self.r['el_use']] = pump_el_use['total']
        proj_total[self.r['el_use_s']] = (
            pump_ts_el_use['total'] * self.it_is_summer).sum()
        proj_total[self.r['el_use_w']] = (
            pump_ts_el_use['total'] * self.it_is_winter).sum()

        # Assign household level electricity consumption
        self.cons_total = self._split_utility(
            self.cons_total,
            value=proj_total[self.r['el_use']],
            var=self.r['el_use'],
            on=self.c['occ'],
            drop=False)

        self.cons_total = self._split_utility(
            self.cons_total,
            value=proj_total[self.r['el_use_s']],
            var=self.r['el_use_s'],
            on=self.c['occ'],
            drop=False)

        self.cons_total = self._split_utility(
            self.cons_total,
            value=proj_total[self.r['el_use_w']],
            var=self.r['el_use_w'],
            on=self.c['occ'],
            drop=False)

        # project level solar fraction
        sol_fra = dict()

        sol_fra['annual'] = (proj_total[self.r['q_dem']] -
            proj_total[self.r['q_del_bckp']]) / proj_total[self.r['q_dem']]

        proj_total[self.r['sol_fra']] = sol_fra['annual']

        # get annual and monthly project level solar fractions
        if self.month is not None:
            sol_fra_hourly = pd.DataFrame()
            sol_fra_hourly[self.c['month']] = self.month
            sol_fra_hourly[self.c['season']] = self.season
            sol_fra_hourly['hourly'] = (ts_res[self.r['q_dem']] -
                ts_res[self.r['q_del_bckp']]) / ts_res[self.r['q_dem']]

            sol_fra['monthly'] = sol_fra_hourly.groupby(
                self.c['month']).mean().rename(
                    columns={'hourly': self.r['month_sol_fra']})

            sol_fra['seasonal'] = sol_fra_hourly.groupby(
                self.c['season']).mean().rename(
                    columns={'hourly': self.r['season_sol_fra']})

            sol_fra['seasonal'] = sol_fra['seasonal'].drop(
                columns=self.c['month'])

        # household level solar fraction
        self.cons_total[self.r['sol_fra']] = \
            self.indiv_load_ratios.apply(
                lambda row: (row[self.c['load_m3']] * (
                    ts_res[self.r['q_dem']] -
                    ts_res[self.r['q_del_bckp']])).sum() /
                (row['ann_cons_fract'] *
                 proj_total[self.r['q_dem']]),
                axis=1)

        # check annual tank balance
        _in = proj_total[self.r['q_del_sol']]

        _outs = (proj_total[self.r['q_del_tank']] +
                 proj_total[self.r['q_dump']] +
                 proj_total[self.r['q_loss_up']] +
                 proj_total[self.r['q_loss_low']] -
                 proj_total[self.r['q_ovrcool_tank']])

        rel_err = abs(_in - _outs) / _in

        if rel_err > .01:
            msg = 'Solar tank balance error is {}.'
            log.warning(msg.format(rel_err))

        # time indices for timestep results only
        ts_res[self.c['month']] = self.month
        ts_res[self.c['season']] = self.season
        ts_res[self.c['day']] = self.day
        ts_res[self.c['hour']] = self.hour

        proj_total[self.c['max_load']] = UnitConv(self.load_max).m3_gal(
            unit_in='m3')

        return self.cons_total.round(2), proj_total.round(2), [
            proj_total.round(2).to_dict(), sol_fra, pump_el_use,
            pump_op_hour, ts_res,
            backup_ts_cons, rel_err]



    def solar_electric(self, backup='electric'):
        """Connects the components of the
        solar electric system and enables simulation.

        Parameters:

            backup: string
                electric - instantaneous WHs (new installations)

        Returns:

            sys_en_use: dict
                System level energy use for the analysis period:
                'electricity', Wh

            sol_fra: dict
                Solar fraction. Keys: 'annual', 'monthly'

            ts_res: pd df
                Colums populated with state variable timeseries, such as
                average timstep heat rates and temperatures

            res: dict
                Summarizes ts_res. Any heat rates are summed, while the
                temperatures are averaged for the analysis period
                (usually one year)

            el_use: dict
                Electricity use broken into end uses
                'dist_pump' - distribution pump, if present

            rel_err: float
                Balancing error due to limitations of finite
                timestep averaging. More precisely, due to
                selecting minimum tank temperature
                as the lower between the water main and the ambient.
        """

        # initiate a dataframe with hourly results
        ts_res = pd.DataFrame(index=range(0, self.num_timesteps + 1))

        # components
        converters = Converter(
            params=self.sys_params,
            weather=self.weather,
            sizes=self.sys_sizes)

        hp_tank = Storage(
            params=self.sys_params,
            size=self.sys_sizes,
            timestep=self.timestep,
            type='hp_tank')

        # Initiate arrays to hold the results during calculation
        # (improved performance with arrays, assigning to df post-calc)

        # Heat pump electricity usage
        P_hp = np.zeros(self.num_timesteps + 1)

        # Photovoltaic gain (before and after inverter)
        P_pv_ac = np.zeros(self.num_timesteps + 1)
        P_pv_dc = np.zeros(self.num_timesteps + 1)

        # Electric power generated by PV, usages
        P_pv_to_hp = np.zeros(self.num_timesteps + 1)
        P_pv_after_hp = np.zeros(self.num_timesteps + 1)

        # Electric power available for feeding back to grid or
        # powering e.g. household appliances
        P_surplus = np.zeros(self.num_timesteps + 1)

        # demand heat rate
        Q_dem = np.zeros(self.num_timesteps + 1)
        Q_dem_with_dist_loss = np.zeros(self.num_timesteps + 1)
        q_dem_balance = np.zeros(self.num_timesteps + 1)

        # input balance on the heat pump tank
        Q_hp = np.zeros(self.num_timesteps + 1)
        Q_loss_lower_hp_tank = np.zeros(self.num_timesteps + 1)
        Q_loss_upper_hp_tank = np.zeros(self.num_timesteps + 1)

        # output balance on the heat pump tank
        Q_del_hp_tank = np.zeros(self.num_timesteps + 1)
        Q_unmet_hp_tank = np.zeros(self.num_timesteps + 1)
        Q_dump_hp_tank = np.zeros(self.num_timesteps + 1)
        Q_ovrcool_hp_tank = np.zeros(self.num_timesteps + 1)

        # tank temperature states
        T_upper_hp_tank = np.zeros(self.num_timesteps + 1)
        T_lower_hp_tank = np.zeros(self.num_timesteps + 1)

        # set values for the initial timestep
        T_upper_hp_tank[0] = self.t_main[0]
        T_lower_hp_tank[0] = self.t_main[0]

        # ambient air and main water temperatures
        T_main = np.zeros(self.num_timesteps + 1)
        T_wet_bulb = np.zeros(self.num_timesteps + 1)
        T_amb = np.zeros(self.num_timesteps + 1)

        # set initial values
        T_main[0] = self.t_main[0]
        T_wet_bulb[0] = self.t_wet_bulb[0]
        T_amb[0] = self.t_amb[0]

        # intial HP status
        hp_status = True
        dt_hist = 5.

        T_limit = hp_tank.T_max

        for ts in range(self.num_timesteps):

            # Use upper tank temperature, since this will be tapped and has
            # to meet T_draw_set
            T_tank = T_upper_hp_tank[ts]

            # hp uses temperature hysteresis as on/off control
            if (((hp_status) and (T_tank < T_limit)) or
                ((not hp_status) and (T_tank < (T_limit - dt_hist)))):

                hp_res = converters.heat_pump(
                    T_wet_bulb=self.t_wet_bulb[ts],
                    T_tank=T_tank)

                # enable heat pump (or keep it on)
                hp_status = True
            else:
                # Set heat pump results to zero
                hp_res = {'heat_cap': 0.,
                          'el_use': 0.,
                          'cop': 0.}

                # disable heat pump (or leave it off)
                hp_status = False

            # hp heat gain to the tank (updated in
            # each timestep, recorded later as
            # output of the hp tank)
            Q_hp_cap = hp_res['heat_cap']

            # electricity use of the heat pump
            P_hp[ts] = hp_res['el_use']

            pv_res = converters.photovoltaic(
                use_p_peak=False,
                inc_rad=self.inc_rad[ts])

            # Electric power produced by photovoltaic module
            P_pv_ac[ts] = pv_res['ac']
            P_pv_dc[ts] = pv_res['dc']

            # Calculate electric power generated by PV used for supplying
            # the HP
            P_pv_to_hp[ts] = min(P_hp[ts], P_pv_ac[ts])

            # Calculate amount of electricity available for other
            # applications
            P_pv_after_hp[ts] = max((P_pv_ac[ts] - P_hp[ts]), 0.)

            sto_res = hp_tank.thermal_tank(
                pre_T_amb=self.t_amb[ts],
                pre_T_feed=self.t_main[ts],
                pre_T_upper=T_upper_hp_tank[ts],
                pre_T_lower=T_lower_hp_tank[ts],
                pre_V_tap=self.load[ts],
                pre_Q_in=Q_hp_cap,
                max_V_tap=self.load_max)

            # demand heat rate
            Q_dem[ts + 1] = sto_res[self.r['q_dem']]
            Q_dem_with_dist_loss[ts + 1] = sto_res[self.r['q_dem_tot']]
            q_dem_balance[ts + 1] = sto_res[self.r['q_dem_balance']]

            # heat pump tank heat sources
            Q_hp[ts + 1] = sto_res[self.r['q_del_hp']]
            Q_ovrcool_hp_tank[ts + 1] = sto_res[self.r['q_ovrcool_tank']]

            # heat pump tank heat sinks
            Q_loss_lower_hp_tank[ts + 1] = sto_res[self.r['q_loss_low']]
            Q_loss_upper_hp_tank[ts + 1] = sto_res[self.r['q_loss_up']]
            Q_del_hp_tank[ts + 1] = sto_res[self.r['q_del_tank']]
            Q_unmet_hp_tank[ts + 1] = sto_res[self.r['q_unmet_tank']]
            Q_dump_hp_tank[ts + 1] = sto_res[self.r['q_dump']]

            # resulting temperatures in the heat pump tank
            T_upper_hp_tank[ts + 1] = sto_res[self.r['t_tank_up']]
            T_lower_hp_tank[ts + 1] = sto_res[self.r['t_tank_low']]

            # set ambient air and main water temperatures
            T_main[ts + 1] = self.t_main[ts]
            T_wet_bulb[ts + 1] = self.t_wet_bulb[ts]
            T_amb[ts + 1] = self.t_amb[ts]

        # simulate backup heater and assign household level
        # electricity consumption
        if backup == 'electric':
            backup_proj_total, backup_ts_proj, \
            backup_ts_cons, P_pv_after_bckp = \
                self._electric_instantaneous_backup(
                    Q_unmet_hp_tank,
                    P_pv_after_hp)
        else:
            msg = 'Backup types supported are: \'electric\'. '\
                  'Please provide one of the supported types.'
            log.error(msg)
            raise ValueError

        # store timestep results in a dataframe
        ts_res[self.r['q_dem']] = Q_dem
        ts_res[self.r['q_del_hp']] = Q_hp
        ts_res[self.r['q_del_bckp']] = backup_ts_proj[self.r['q_del_bckp']]
        ts_res[self.r['q_loss_low']] = Q_loss_lower_hp_tank
        ts_res[self.r['q_loss_up']] = Q_loss_upper_hp_tank
        ts_res[self.r['q_del_tank']] = Q_del_hp_tank
        ts_res[self.r['q_unmet_tank']] = Q_unmet_hp_tank
        ts_res[self.r['q_dump']] = Q_dump_hp_tank
        ts_res[self.r['q_ovrcool_tank']] = Q_ovrcool_hp_tank
        ts_res[self.r['t_tank_up']] = T_upper_hp_tank
        ts_res[self.r['t_tank_low']] = T_lower_hp_tank
        # PV generated electricity (AC)
        ts_res[self.r['p_pv_ac']] = P_pv_ac
        # PV generated electricity (DC)
        ts_res[self.r['p_pv_dc']] = P_pv_dc

        # total heat gain (heat pump and electric resistance)
        ts_res[self.r['q_del']] = Q_hp + backup_ts_proj[self.r['q_del_bckp']]
        ts_res[self.r['q_unmet']] = backup_ts_proj[self.r['q_unmet']]

        # Usage of electric power generated by PV
        ts_res[self.r['p_pv_to_hp']] = P_pv_to_hp
        ts_res[self.r['p_pv_to_el_res']] = P_pv_after_bckp['used_for_bckp']

        # Electricity usage (from grid and PV)
        # Heat Pump
        ts_res[self.r['p_hp_el_use']] = P_hp
        # Electric Resistance
        ts_res[self.r['p_el_res_use']] = backup_ts_proj[self.r['grs_el_use']]

        # also include the water and air temperatures in the results
        ts_res[self.r['t_main']] = T_main
        ts_res[self.r['t_amb']] = T_amb
        ts_res[self.r['t_wet_bulb']] = T_wet_bulb

        # get average temperatures and total heat rates
        t_columns = [col for col in ts_res.columns if 'Temperature' in col]
        # all other columns contain timestep heat rate
        q_columns = [x for x in (set(ts_res.columns) - set(t_columns))]

        # project results
        proj_total = ts_res.sum()
        proj_total[t_columns] = ts_res[t_columns].mean()

        # household results (annual quantities split according
        # to individual loads)
        self.cons_total[self.r['q_dem']] = self.indiv_load_ratios[
            self.c['load_m3']].apply(
                lambda x: (x * Q_dem).sum())

        self.cons_total[self.r['q_del']] = (self.indiv_load_ratios[
            self.c['load_m3']].apply(
                lambda x: (x * Q_del_hp_tank).sum()) +
            self.cons_total[self.r['q_del_bckp']])

        self.cons_total[self.r['q_unmet_tank']] = self.indiv_load_ratios[
            self.c['load_m3']].apply(
                lambda x: (x * Q_unmet_hp_tank).sum())

        self.cons_total[self.r['q_del_tank']] = self.indiv_load_ratios[
            self.c['load_m3']].apply(
                lambda x: (x * Q_del_hp_tank).sum())

        # Calculate pump electricity use
        if self.community:
            dist_pump_on_timestep_frac = Q_del_hp_tank + 0.
        else:
            # single households do not require
            # a distribution pump due to the
            # water main pressure
            dist_pump_on_timestep_frac = None

        pump_ts_el_use, pump_el_use, pump_op_hour = \
            self._get_pump_energy_use(
                dist_pump_on_timestep_frac=dist_pump_on_timestep_frac)

        # if there is any PV power left, use it for the pumps
        pump_ts_el_use_after_pv = (pump_ts_el_use['total'] -
            P_pv_after_bckp['rem_after'])
        pump_ts_el_use_after_pv[pump_ts_el_use_after_pv < 0.] = 0.

        pump_el_use['after_pv'] = pump_ts_el_use_after_pv.sum()

        # Distribute pump el. use onto households and add to
        # total electricity use
        self.cons_total = self._split_utility(
            self.cons_total,
            value=pump_el_use['after_pv'],
            var='pump_el_use',
            on=self.c['occ'],
            drop=False)

        self.cons_total[self.r['el_use']] += self.cons_total['pump_el_use']
        self.cons_total = self.cons_total.drop(
            columns=['pump_el_use'])

        # Total electricity use
        ts_res[self.r['grs_el_use']] = (ts_res[self.r['p_hp_el_use']] +
                                        ts_res[self.r['p_el_res_use']] +
                                        pump_el_use['total'])

        # Electricity available after hp, backup heater and pumps
        P_surplus = P_pv_after_bckp['rem_after'] - pump_ts_el_use['total']
        P_surplus[P_surplus < 0.] = 0.
        ts_res[self.r['p_surplus']] = P_surplus

        # project level solar fraction (excludes pumping energy)
        sol_fra = dict()

        # Calculate the fraction of HP el. use that came from the PV

        # annual
        fraction_pv_to_hp = (proj_total[self.r['p_pv_to_hp']] /
                             proj_total[self.r['p_hp_el_use']])

        # annual
        fraction_pv_to_el_res = (proj_total[self.r['p_pv_to_el_res']] /
                                 proj_total[self.r['p_el_res_use']])
        # for each timestep

        # Calculate solar fraction between generated PV power and
        # total electricity use
        sol_fra['annual'] = ((proj_total[self.r['q_del_hp']] *
            fraction_pv_to_hp +
            proj_total[self.r['q_del_bckp']] * fraction_pv_to_el_res) /
            proj_total[self.r['q_dem']])

        # check annual tank balance
        _in = proj_total[self.r['q_del_hp']]

        _outs = (proj_total[self.r['q_del_tank']] +
                 proj_total[self.r['q_dump']] +
                 proj_total[self.r['q_loss_up']] +
                 proj_total[self.r['q_loss_low']] -
                 proj_total[self.r['q_ovrcool_tank']])

        rel_err = abs(_in - _outs) / _in

        if rel_err > .01:
            msg = 'Heat pump tank balance error is {}.'
            log.warning(msg.format(rel_err))

        return self.cons_total, proj_total.round(2), [
            proj_total.round(2).to_dict(),
            sol_fra, pump_el_use,
            pump_op_hour, ts_res, rel_err]

    def conventional_gas_tank(self):
        """Basecase conventional gas tank water heater.
        Make sure to size the tank according to the recommended
        sizing rules, since the WHAM model does not apply to
        tanks that are not appropriately sized.

        Returns:

            ts_proj: dict of arrays, W
                Heat:
                self.r['q_del']: delivered
                self.r['gas_use']: gas consumed
        """
        # components
        heater = Storage(
            params=self.sys_params,
            size=self.sys_sizes,
            timestep=self.timestep,
            type='wham_tank',
            log_level=self.log_level)

        # indoor air temperature is 291.48 K
        res = heater.gas_tank_wh(
            self.load,
            self.t_main,
            T_amb=291.48)

        # household/project level timestep results
        ts_proj = {self.r['q_del']: res[self.r['q_del']],
                   self.r['gas_use']: res[self.r['gas_use']],
                   self.r['gas_use_no_dist']: res[self.r['gas_use']],
                   self.r['q_dem']: res[self.r['q_dem']]}

        ts_proj[self.c['season']] = self.season

        # household/project level analysis period results
        self.cons_total.at[0, self.r['el_use']] = 0.
        self.cons_total.at[0, self.r['el_use_s']] = 0.
        self.cons_total.at[0, self.r['el_use_w']] = 0.

        self.cons_total.at[0, self.r['gas_use']] = \
            res[self.r['gas_use']].sum() * self.timestep

        self.cons_total.at[0, self.r['gas_use_w']] = (
            res[self.r['gas_use']] *
            self.it_is_winter[1:]).sum() * self.timestep

        self.cons_total.at[0, self.r['gas_use_s']] = (
            res[self.r['gas_use']] *
            self.it_is_summer[1:]).sum() * self.timestep

        # these are just placeholders for consistency
        # the model considers only additional distribution piping
        # in case of a solar thermal system
        self.cons_total.at[0, self.r['gas_use_no_dist']] =\
            self.cons_total.at[0, self.r['gas_use']]
        self.cons_total.at[0, self.r['gas_use_s_no_dist']] =\
            self.cons_total.at[0, self.r['gas_use_s']]
        self.cons_total.at[0, self.r['gas_use_w_no_dist']] =\
            self.cons_total.at[0, self.r['gas_use_w']]

        self.cons_total.at[0, self.r['q_del']] =\
            res[self.r['q_del']].sum() * self.timestep

        self.cons_total.at[0, self.r['q_dem']] =\
            res[self.r['q_dem']].sum() * self.timestep

        # zero by WHAM model definition
        self.cons_total.at[0, self.r['q_unmet']] = 0.
        self.cons_total.at[0, self.r['q_dump']] = 0.
        self.cons_total.at[0, self.r['q_dist_loss']] = 0.
        self.cons_total.at[0, self.r['q_dist_loss_at_bckp']] = 0.
        self.cons_total.at[0, self.r['q_dist_loss_at_bckp_sum']] = 0.
        self.cons_total.at[0, self.r['q_dist_loss_at_bckp_win']] = 0.

        self.cons_total.at[0, self.r['sol_fra']] = 0.

        self.cons_total.at[0, self.c['max_load']] = UnitConv(
            self.load_max).m3_gal(unit_in='m3')

        return self.cons_total, self.cons_total.iloc[0,:], ts_proj

    def simulate(self, type='gas_tank_wh'):
            """Runs a 8760. hourly simulation of the
            provided system type.

            Parameters

                type: string
                    gas_tank_wh
                    solar_thermal_retrofit (gas tank backup at each household)
                    solar_thermal_new (gas tankless backup at each household)
                    solar_electric

            Returns

                en_use: dict
                    Total energy use for the analysis period:
                    'gas', Wh
                    'electricity', Wh

                sys_res: list
                    List containing detailed system level
                    output. See dedicated methods for details
            """

            # idealized instantaneous backup (type = see db for system names)
            if type == 'solar_thermal_new':
                cons_total, proj_total, sys_res = \
                    self.solar_thermal(backup='gas')

            elif type == 'solar_electric':
                cons_total, proj_total, sys_res = \
                    self.solar_electric()

            elif type == 'solar_thermal_retrofit':
                cons_total, proj_total, sys_res = \
                    self.solar_thermal(backup='retrofit')

            elif type == 'gas_tank_wh':
                cons_total, sys_res = \
                    self.conventional_gas_tank()
                proj_total = 0.
                sol_fra = 0.

            return cons_total, proj_total, sys_res

    def _gas_instantaneous_backup(self, Q_unmet_sol_tank,
                                  Q_dist_loss):
        """Simulates the performance of each individual household
        backup based on their hot water end-use load
        profile and the load unmet by the community solar system.

        Parameters:

            Q_unmet_sol_tank: array
                Unmet demand after the solar tank (set load for the
                backup)

            Q_dist_loss: array
                Distribution losses

        Returns:

            total_proj: pd df
                Project level backup energy use
                and heat rates.

            ts_proj: dict
                Timestep project level results for
                energy use (gas consumed) and heat rates
                (delivered, unmet)

            ts_cons: dict of dicts
                Timestep household level results for energy uses [W],
                and heat rates [W].

            Updates self.cons_total with the backup simulation
            energy use and heat rates results.
        """

        # project level backup delivered, gas use and unmet
        ts_proj = {self.r['q_del_bckp']: np.zeros(self.num_timesteps + 1),
                   self.r['gas_use']: np.zeros(self.num_timesteps + 1),
                   self.r['gas_use_no_dist']: np.zeros(self.num_timesteps + 1),
                   self.r['q_unmet']: np.zeros(self.num_timesteps + 1)}

        ts_cons = dict()

        # Distribution losses when the backup is on. The
        # actual loss covered by the backup is distributed over
        # individual households in the loop below
        Q_dist_loss_when_backup_on = (Q_dist_loss *
            (Q_unmet_sol_tank > 0.))

        Q_unmet_without_dist_loss = (Q_unmet_sol_tank -
            Q_dist_loss_when_backup_on)

        # distribution loss may be larger than
        # the backup demand (this occurs when a part of
        # the loss got covered by the solar source),
        # so impose zero as lower limit
        Q_unmet_without_dist_loss[
            Q_unmet_without_dist_loss < 0.] = 0.

        for cons_id in self.cons_total[self.c['id']].unique():
            # get the fraction of the remaining load
            # pertaining to a single household, which should
            # be met by that household's backup
            Q_unmet_sol_tank_ind_cons = (Q_unmet_sol_tank *
                self.indiv_load_ratios.loc[
                    self.indiv_load_ratios[
                        self.c['id']] == cons_id,
                    self.c['load_m3']].reset_index(drop=True)[0])

            Q_unmet_sol_tank_ind_cons_no_dist_loss = (
                Q_unmet_without_dist_loss *
                self.indiv_load_ratios.loc[
                    self.indiv_load_ratios[self.c['id']] == cons_id,
                self.c['load_m3']].reset_index(drop=True)[0])

            size = self.backup_sizes.loc[
                self.backup_sizes[self.c['id']] == cons_id,
                [self.s['comp'], self.s['cap']]]

            ind_backup = Converter(
                params=self.backup_params,
                weather=self.weather,
                sizes=size,
                log_level=self.log_level)

            ind_res = ind_backup.gas_burner(
                Q_unmet_sol_tank_ind_cons)

            ind_res_no_dist_loss = ind_backup.gas_burner(
                Q_unmet_sol_tank_ind_cons_no_dist_loss)

            for key in ind_res:
                ts_proj[key] += ind_res[key]

            ts_proj[self.r['gas_use_no_dist']] += (
                ind_res_no_dist_loss[self.r['gas_use']])

            ts_cons[cons_id] = {
                self.r['q_del_bckp']: ind_res[self.r['q_del_bckp']],
                self.r['gas_use']: ind_res[self.r['gas_use']],
                self.r['gas_use_s']: (ind_res[self.r['gas_use']] *
                                      self.it_is_summer),
                self.r['gas_use_w']: (ind_res[self.r['gas_use']] *
                                      self.it_is_winter),
                self.r['gas_use_no_dist']: ind_res_no_dist_loss[
                    self.r['gas_use']],
                self.r['gas_use_s_no_dist']: ind_res_no_dist_loss[
                    self.r['gas_use']] * self.it_is_summer,
                self.r['gas_use_w_no_dist']: ind_res_no_dist_loss[
                    self.r['gas_use']] * self.it_is_winter,
                self.r['q_unmet']: ind_res[self.r['q_unmet']]}

            ts_cons[cons_id][self.c['season']] = self.season
            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use']] = ind_res[
                    self.r['gas_use']].sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_s']] = (
                    ind_res[self.r['gas_use']] *
                    self.it_is_summer).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_w']] = (
                    ind_res[self.r['gas_use']] *
                    self.it_is_winter).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_no_dist']] = ind_res_no_dist_loss[
                    self.r['gas_use']].sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_s_no_dist']] = (
                    ind_res_no_dist_loss[self.r['gas_use']] *
                    self.it_is_summer).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_w_no_dist']] = (
                    ind_res_no_dist_loss[self.r['gas_use']] *
                    self.it_is_winter).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['q_del_bckp']] = ind_res[
                    self.r['q_del_bckp']].sum() * self.timestep

            self.cons_total.at[\
                self.cons_total[self.c['id']] == cons_id, \
                self.r['q_unmet']] = \
                ind_res[self.r['q_unmet']].sum() * self.timestep

        ts_proj[self.r['gas_use_s']] = (
            ts_proj[self.r['gas_use']] * self.it_is_summer)

        ts_proj[self.r['gas_use_w']] = (
            ts_proj[self.r['gas_use']] * self.it_is_winter)

        ts_proj[self.r['gas_use_s_no_dist']] = (
            ts_proj[self.r['gas_use_no_dist']] * self.it_is_summer)

        ts_proj[self.r['gas_use_w_no_dist']] = (
            ts_proj[self.r['gas_use_no_dist']] * self.it_is_winter)

        total_proj = pd.DataFrame.from_dict(ts_proj).sum().to_dict()

        ts_proj[self.c['season']] = self.season

        return total_proj, ts_proj, ts_cons

    def _electric_instantaneous_backup(self, Q_unmet_tank, P_pv):
        """Simulates the performance of each individual household
        backup based on their hot water end-use load
        profile and the load unmet by the community solar system.

        Parameters:

            Q_unmet_tank: array
                Unmet demand after the solar tank (set load for the
                backup)

            P_pv: array
                PV power available for the backup application
                Set to None if there is no PV in the system or
                if PV generated power should not be used
                to power the electric heater backup

            total_proj: pd df
                Project level backup energy use
                and heat rates.

            ts_proj: dict
                Timestep project level results for energy use [W],
                and delivered heat rate [W].

            ts_cons: dict of dicts
                Timestep household level results for energy use [W],
                and delivered heat rate [W].

            Updates self.cons_total with the backup simulation
            energy use and heat rates results.
        """
        if P_pv is None:
            P_pv = np.zeros(self.num_timesteps + 1)

        # project level backup delivered, gas use and unmet
        ts_proj = {self.r['q_del_bckp']: np.zeros(self.num_timesteps + 1),
                   self.r['el_use']: np.zeros(self.num_timesteps + 1),
                   self.r['grs_el_use']: np.zeros(self.num_timesteps + 1),
                   self.r['q_unmet']: np.zeros(self.num_timesteps + 1)}

        ts_cons = dict()

        for cons_id in self.cons_total[self.c['id']].unique():
            # get the fraction of the remaining load
            # pertaining to a single household, which should
            # be met by that household's backup
            Q_unmet_tank_ind_cons = (Q_unmet_tank *
                self.indiv_load_ratios.loc[
                    self.indiv_load_ratios[self.c['id']] == cons_id,
                    self.c['load_m3']].reset_index(drop=True)[0])

            # fraction of the PV generated power that can be allocated
            # to consumer cons_id
            P_pv_ind_cons = (P_pv *
                self.indiv_load_ratios.loc[
                    self.indiv_load_ratios[self.c['id']] == cons_id,
                    self.c['load_m3']].reset_index(drop=True)[0])

            size = self.backup_sizes.loc[
                self.backup_sizes[self.c['id']] == cons_id,
                [self.s['comp'], self.s['cap']]]

            ind_backup = Converter(
                params=self.backup_params,
                weather=self.weather,
                sizes=size)

            ind_res = ind_backup.electric_resistance(
                Q_unmet_tank_ind_cons)

            ind_res[self.r['grs_el_use']] = (
                ind_res[self.r['el_use']] * 1.)

            # power from PV if possible
            ind_res[self.r['el_use']] = (
                ind_res[self.r['grs_el_use']] - P_pv_ind_cons)
            ind_res[self.r['el_use']][
                ind_res[self.r['el_use']] < 0.] = 0.

            for key in ind_res:
                ts_proj[key] += ind_res[key]

            ts_cons[cons_id] = {
                self.r['q_del_bckp']: ind_res[self.r['q_del_bckp']],
                self.r['el_use']: ind_res[self.r['el_use']],
                self.r['q_unmet']: ind_res[self.r['q_unmet']]}

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['el_use']] = ind_res[
                    self.r['el_use']].sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['q_del_bckp']] = ind_res[
                    self.r['q_del_bckp']].sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['q_unmet']] = ind_res[
                    self.r['q_unmet']].sum() * self.timestep

        # PV power accounting
        P_pv_bckp = {}

        P_pv_bckp['rem_after'] = P_pv - ts_proj[self.r['grs_el_use']]
        P_pv_bckp['rem_after'][P_pv_bckp['rem_after'] < 0.] = 0.

        P_pv_bckp['used_for_bckp'] = P_pv - P_pv_bckp['rem_after']

        total_proj = pd.DataFrame.from_dict(ts_proj).sum().to_dict()

        return total_proj, ts_proj, ts_cons, P_pv_bckp

    def _gas_tank_backup(self, T_feed, T_feed_no_loss):
        """Backup gas tank water heater. Retrofit systems
        retain the original one.

        Currently we assume that the outdoor air temperature
        rarely drives the tank temperature below the water
        main. If the model is to be applied for colder climates,
        and the tanks are to be installed outdoors, a valve which
        switches the backup feed to main in case the feed from the
        tank is of a lower temperature should be implemented.

        Parameters:

            T_feed: array like, K
                Backup water heater inlet temperature

            T_feed_no_loss: array like, K
                Backup water heater inlet temperature
                assuming no temperature drop in the
                distribution system (adiabatic pipe)

        Returns:

            total_proj: pd df
                Project level backup energy use
                and heat rates.

            ts_proj: dict
                Timestep project level results for energy use [W],
                and delivered heat rate [W].

            ts_cons: dict of dicts
                Timestep household level results for energy use [W],
                and delivered heat rate [W].

            Updates self.cons_total with the backup simulation
            energy use and heat rates results.
        """

        ts_proj = {self.r['q_del_bckp']: np.zeros(self.num_timesteps + 1),
                   self.r['gas_use']: np.zeros(self.num_timesteps + 1),
                   self.r['gas_use_no_dist']: np.zeros(self.num_timesteps + 1),
                   self.r['q_unmet']: np.zeros(self.num_timesteps + 1)}

        ts_proj[self.c['season']] = self.season

        ts_cons = dict()

        for cons_id in self.cons_total[self.c['id']].unique():
            # extract backup size for the household
            size = self.backup_sizes.loc[
                self.backup_sizes[self.c['id']] == cons_id,
                self.s['cap']].values[0]

            backup_heater = Storage(
                params=self.backup_params,
                size=size,
                timestep=self.timestep,
                type='wham_tank',
                log_level=self.log_level)

            # assuming the tank is indoors and using default
            # tank surrounding temperature
            ind_load = np.append(
                0,
                self.loads.loc[self.loads[self.c['id']] == cons_id,
                               self.c['load_m3']].values[0])

            ind_res = backup_heater.gas_tank_wh(
                ind_load,
                T_feed,
                T_amb=291.48)

            ind_res_no_dist_loss = backup_heater.gas_tank_wh(
                ind_load,
                T_feed_no_loss,
                T_amb=291.48)

            # rename key
            ind_res[self.r['q_del_bckp']] = ind_res.pop(self.r['q_del'])
            # placeholder unmet load, not implemented in the comp. model
            ind_res[self.r['q_unmet']] = np.zeros(self.num_timesteps + 1)

            for key in ([self.r['gas_use'], self.r['q_del_bckp'],
                        self.r['q_unmet']]):
                ts_proj[key] += ind_res[key]

            ts_proj[self.r['gas_use_no_dist']] += (
                ind_res_no_dist_loss[self.r['gas_use']])

            ts_cons[cons_id] = {
                self.r['q_del_bckp']: ind_res[self.r['q_del_bckp']],
                self.r['gas_use']: ind_res[self.r['gas_use']],
                self.r['gas_use_s']: ind_res[
                    self.r['gas_use']] * self.it_is_summer,
                self.r['gas_use_w']: ind_res[
                    self.r['gas_use']] * self.it_is_winter,
                self.r['gas_use_no_dist']: ind_res_no_dist_loss[
                    self.r['gas_use']],
                self.r['gas_use_s_no_dist']: ind_res_no_dist_loss[
                    self.r['gas_use']] * self.it_is_summer,
                self.r['gas_use_w_no_dist']: ind_res_no_dist_loss[
                    self.r['gas_use']] * self.it_is_winter}

            ts_cons[cons_id][self.c['season']] = self.season

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use']] = ind_res[self.r['gas_use']].sum()

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_s']] = (
                    ind_res[self.r['gas_use']] *
                    self.it_is_summer).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_w']] = (
                    ind_res[self.r['gas_use']] *
                    self.it_is_winter).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_no_dist']] = ind_res_no_dist_loss[
                    self.r['gas_use']].sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_s_no_dist']] = (
                    ind_res_no_dist_loss[self.r['gas_use']] *
                    self.it_is_summer).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['gas_use_w_no_dist']] = (
                    ind_res_no_dist_loss[self.r['gas_use']] *
                    self.it_is_winter).sum() * self.timestep

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['q_del_bckp']] = ind_res[
                    self.r['q_del_bckp']].sum()

            self.cons_total.at[
                self.cons_total[self.c['id']] == cons_id,
                self.r['q_unmet']] = ind_res[
                    self.r['q_unmet']].sum() * self.timestep

        total_proj = pd.DataFrame.from_dict(ts_proj).sum().to_dict()

        ts_proj[self.r['gas_use_s']] = (
            ts_proj[self.r['gas_use']] * self.it_is_summer)

        ts_proj[self.r['gas_use_w']] = (
            ts_proj[self.r['gas_use']] * self.it_is_winter)

        ts_proj[self.r['gas_use_s_no_dist']] = (
            ts_proj[self.r['gas_use_no_dist']] * self.it_is_summer)

        ts_proj[self.r['gas_use_w_no_dist']] = (
            ts_proj[self.r['gas_use_no_dist']] * self.it_is_winter)

        return total_proj, ts_proj, ts_cons

    @staticmethod
    def _split_utility(df, value=1., var=None, on=None, drop=True):
        """Splits community level costs or energy use between the
        households based on a size defining variable,
        such as occupancy.

        Parameters

            df: pd df
                Contains household ID and split on column

            value: float
                Value to split among households

            var: str
                Label to store splitted values

            on: str
                Label for the column with weights
                (e.g. occupancy)

            drop: boolean
                Drops column used for calculating weights
                ('on' kwarg)
        """
        df[var] = df[on] * value / df[on].sum()

        if drop:
            df = df.drop(on, axis=1)

        # return with a value distributed onto households
        return df

    def _get_pump_energy_use(self, dist_pump_on_timestep_frac=None,
                             gain_from_collector=None):
        """Calculates pump energy use based on the load on the pump.
        We assume fixed_speed pumps and full load at each timestep when
        there is flow demand.

        Parameters:

            dist_pump_on_timestep_frac: array, W
                Array with the fraction of distribution
                pump on time for each timestep

            gain_from_collector: array, W
                Array with load delivered from collector.
                Determines the operating hours for the solar
                pump. Assumption is that for each timestep in
                which the load exists, the pump is on for the
                full duration of the timestep

        Returns:

            el_use: dict, Wh
                Electricity consumption for the analyzed period by:
                'dist_pump' - distribution pump
                'sol_pump' - solar pump
                'total' - total (all pumps in the system)

            op_hour: dict, h
                Operating hours for the analyzed period by:
                'dist_pump' - distribution pump
                'sol_pump' - solar pump
        """
        ts_el_use = dict()
        ts_el_use['total'] = np.zeros(self.num_timesteps + 1)

        el_use = dict()
        el_use['total'] = 0.

        op_hour = dict()

        pump = Distribution(
            params=self.sys_params,
            sizes=self.sys_sizes,
            log_level=self.log_level)

        if dist_pump_on_timestep_frac is not None:
            # get annual on hours
            op_hour['dist_pump'] = (dist_pump_on_timestep_frac.sum() *
                                    self.timestep)

            ts_el_use['dist_pump'], el_use['dist_pump'] = pump.pump(
                on_array=dist_pump_on_timestep_frac,
                role='distribution')

            ts_el_use['total'] += ts_el_use['dist_pump']

            el_use['total'] += el_use['dist_pump']

        if gain_from_collector is not None:
            # get annual on hours
            on_array = 1. * (gain_from_collector > 0)

            op_hour['sol_pump'] = ((gain_from_collector > 0).sum() *
                                   self.timestep)

            ts_el_use['sol_pump'], el_use['sol_pump'] = pump.pump(
                on_array=on_array,
                role='solar')

            ts_el_use['total'] += ts_el_use['sol_pump']

            el_use['total'] += el_use['sol_pump']

        return ts_el_use, el_use, op_hour
