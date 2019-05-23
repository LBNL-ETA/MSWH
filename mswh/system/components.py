import logging

import numpy as np
import pandas as pd

from mswh.comm.label_map import SwhLabels
from mswh.tools.unit_converters import UnitConv

log = logging.getLogger(__name__)


class Converter(object):
    """Contains energy converter models, such as
    solar collectors, electric resistance heaters, gas burners,
    photovoltaic panels, and heat pumps. Depending on the intended
    usage, the models can be used to determine either a time period
    of component operation (for example an entire year), or a single
    timestep of component performance.

    Parameters:

        params: pd df
            Component performance parameters per project
            Default: None (default model parameters will get used)

        weather: pd df
            Weather data timeseeries with columns: amb. temp,
            solar irradiation. Number of rows equals the number of timesteps.
            Default: None (constant values will be set - use for
            a single timestep calculation, or if passing arguments
            directly to static methods)

        sizes: pd df
            Component sizes per project.
            Default: 1. (see individual components for specifics)

        log_level: None or python logger logging level,
            Default: logging.DEBUG
            This applies for a subset of the class functionality, mostly
            used to deprecate logger messages for certain calculations.
            For Example: log_level = logging.ERROR will only throw error
            messages and ignore INFO, DEBUG and WARNING.

    Note:

        If more than one of the same component is a part of the
        system, a separate instance of the converter should
        be created for each instance of the component.

        Each component is also implemented as a static method that
        can be used outside of this framework.

    Examples:

        See :func:`swh.system.tests.test_components <swh.system.tests.test_components>` module and
        :func:`scripts/Project Level SWH System Tool.ipynb <scripts/Project Level SWH System Tool.ipynb>`
        for examples on how to use the methods as stand alone and
        in a system model simulation.
    """

    def __init__(self, params=None, weather=None, sizes=1.,
                 log_level=logging.DEBUG):

        # log level (e.g. only partial functionality of the class
        # is being used and one does not desire to see all infos)
        self.log_level = log_level
        logging.getLogger().setLevel(log_level)

        # extract labels
        self.c = SwhLabels().set_hous_labels()
        self.s = SwhLabels().set_prod_labels()
        self.r = SwhLabels().set_res_labels()

        if isinstance(params, pd.DataFrame):

            self.use_defaults = False

            # extract components and their performance parameters
            self.components = []

            # extract components provided in params
            components = params[self.s['comp']].unique().tolist()

            if self.s['sol_col'] in components:
                self.components.append(self.s['sol_col'])

                self.params_sol_col = dict()
                # this method of collector model selection prefers the
                # model under ```try:``` as long as the parameters were
                # found in the parameter table
                try: # HWB
                    self.params_sol_col[self.s['interc_hwb']] = params.loc[
                        params[self.s['param']] == self.s['interc_hwb'],
                        self.s['param_value']].values[0]

                    self.params_sol_col[self.s['slope_hwb']] = params.loc[
                        params[self.s['param']] == self.s['slope_hwb'],
                        self.s['param_value']].values[0]
                    self.solar_model = 'HWB'
                except: # CD
                    self.params_sol_col[self.s['interc_cd']] = params.loc[
                        params[self.s['param']] == self.s['interc_cd'],
                        self.s['param_value']].values[0]

                    self.params_sol_col[self.s['a1_cd']] = params.loc[
                        params[self.s['param']] == self.s['a1_cd'],
                        self.s['param_value']].values[0]

                    self.params_sol_col[self.s['a2_cd']] = params.loc[
                        params[self.s['param']] == self.s['a2_cd'],
                        self.s['param_value']].values[0]

                    self.solar_model = 'CD'


            if self.s['pv'] in components:
                self.components.append(self.s['pv'])

                self.params_pv = dict()

                # Extract the model parameters
                self.params_pv[self.s['eta_pv']] = params.loc[
                    params[self.s['param']] == self.s['eta_pv'],
                    self.s['param_value']].values[0]

                self.params_pv[self.s['f_act']] = params.loc[
                    params[self.s['param']] == self.s['f_act'],
                    self.s['param_value']].values[0]

                self.params_pv[self.s['irrad_ref']] = params.loc[
                    params[self.s['param']] == self.s['irrad_ref'],
                    self.s['param_value']].values[0]

                msg = 'Photovoltaic is setup.'
                log.info(msg)

            if self.s['inv'] in components:
                self.components.append(self.s['inv'])

                self.params_inv = dict()

                # extract the total dc-ac conversion efficiency
                self.params_inv[self.s['eta_dc_ac']] = params.loc[
                    params[self.s['param']] == self.s['eta_dc_ac'],
                    self.s['param_value']].values[0]

                msg = 'Inverter is setup.'
                log.info(msg)

            if self.s['hp'] in components:
                self.components.append(self.s['hp'])
                self.params_hp = dict()
                # Extract the model parameters
                self.params_hp[self.s['c1_cop']] = params.loc[
                    params[self.s['param']] == self.s['c1_cop'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c2_cop']] = params.loc[
                    params[self.s['param']] == self.s['c2_cop'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c3_cop']] = params.loc[
                    params[self.s['param']] == self.s['c3_cop'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c4_cop']] = params.loc[
                    params[self.s['param']] == self.s['c4_cop'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c5_cop']] = params.loc[
                    params[self.s['param']] == self.s['c5_cop'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c6_cop']] = params.loc[
                    params[self.s['param']] == self.s['c6_cop'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c1_heat_cap']] = params.loc[
                    params[self.s['param']] == self.s['c1_heat_cap'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c2_heat_cap']] = params.loc[
                    params[self.s['param']] == self.s['c2_heat_cap'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c3_heat_cap']] = params.loc[
                    params[self.s['param']] == self.s['c3_heat_cap'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c4_heat_cap']] = params.loc[
                    params[self.s['param']] == self.s['c4_heat_cap'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c5_heat_cap']] = params.loc[
                    params[self.s['param']] == self.s['c5_heat_cap'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['c6_heat_cap']] = params.loc[
                    params[self.s['param']] == self.s['c6_heat_cap'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['heat_cap_rated']] = params.loc[
                    params[self.s['param']] == self.s['heat_cap_rated'],
                    self.s['param_value']].values[0]
                self.params_hp[self.s['cop_rated']] = params.loc[
                    params[self.s['param']] == self.s['cop_rated'],
                    self.s['param_value']].values[0]

                msg = 'Heat pump is setup.'
                log.info(msg)

            if self.s['el_res'] in components:
                self.components.append(self.s['el_res'])

                self.params_el_res = dict()

                # Extract electric resistance parameters
                self.params_el_res[self.s['eta_el_res']] = params.loc[
                    params[self.s['param']] == self.s['eta_el_res'],
                    self.s['param_value']].values[0]

            if self.s['gas_burn'] in components:
                self.components.append(self.s['gas_burn'])

                self.params_gas_burn = dict()

                # Extract gas burner parameters
                self.params_gas_burn[self.s['comb_eff']] = params.loc[
                    params[self.s['param']] == self.s['comb_eff'],
                    self.s['param_value']].values[0]

            # when adding components, extract parameters similarly

        elif not isinstance(params, pd.DataFrame):
            self.use_defaults = True

        # extract component size/capacity (see setter for details)
        self.size = sizes

        # extract weather and irradiation data
        self.weather = weather

    @property
    def weather(self):
        return self.__weather

    @weather.setter
    def weather(self, value):
        """Re-extracts weather timeseries if a new weather dataset
        is assigned to an instantiated class object
        """
        self.__weather = value
        if isinstance(value, pd.DataFrame):
            self.t_amb = UnitConv(
                self.weather[self.c['t_amb_C']].values).degC_K(unit_in='degC')
            self.inc_rad = self.weather[self.c['irrad_on_tilt']].values
            msg = 'Assigned weather data timeseries.'
            log.info(msg)

        elif value is None:
            self.t_amb = 293.15  # K
            self.inc_rad = 800  # W
            msg = 'No weather data got passed to converters. '\
                  'Setting default scalar values for ambient temperature, '\
                  '{}, and solar irradiation, {}.'
            log.info(msg.format(self.t_amb, self.inc_rad))

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        """Re-extracts sizes from a dataframe
        """
        set_sizes = dict()

        if (not isinstance(value, pd.DataFrame)) and (value == 1.):
            # assign unit size
            set_sizes = value

        elif isinstance(value, pd.DataFrame):

            if self.s['gas_tank'] in self.components:
                set_sizes[self.s['gas_tank']] = \
                value.loc[value[self.s['comp']] == self.s['gas_tank'],
                          self.s['cap']].values[0]

            if self.s['sol_col'] in self.components:
                set_sizes[self.s['sol_col']] = \
                value.loc[value[self.s['comp']] == self.s['sol_col'],
                          self.s['cap']].values[0]

            if self.s['pv'] in self.components:
                set_sizes[self.s['pv']] = \
                value.loc[value[self.s['comp']] == self.s['pv'],
                          self.s['cap']].values[0]

            if self.s['hp'] in self.components:
                set_sizes[self.s['hp']] = \
                value.loc[value[self.s['comp']] == self.s['hp'],
                          self.s['cap']].values[0]

            if self.s['el_res'] in self.components:
                set_sizes[self.s['el_res']] = \
                value.loc[value[self.s['comp']] == self.s['el_res'],
                          self.s['cap']].values[0]

            if self.s['gas_burn'] in self.components:
                try:
                    set_sizes[self.s['gas_burn']] = \
                    value.loc[value[self.s['comp']] == self.s['gas_burn'],
                              self.s['cap']].values[0]
                except:
                    set_sizes[self.s['gas_burn']] = None
                    msg = 'Could not find the size for the '\
                          'gas instantaneous water heater, '\
                          'Setting size to infinite.'
                    log.info(msg)

        else:
            msg = 'Provided sizes format is not supported.'
            log.error(msg)
            raise ValueError

        self.__size = set_sizes

    def heat_pump(self, T_wet_bulb, T_tank):
        """Returns the current heating performance and electricity usage
        in the current conditions depending on wet bulb temperature,
        average tank water temperature, and the rated heating performance.

        Rated conditions are: wet bulb = 14 degC, tank = 48.9 degC

        Parameters:

            T_wet_bulb: real, array
                Inlet air wet bulb temperature [K]

            T_tank: real, array
                Water temperature in the storage tank [K]

            C1: real
                Coefficient 1, either for normalized COP or heating
                capacity curve [-]

            C2: real
                Coefficient 2, either for normalized COP or heating
                capacity curve [1/degC]

            C3: real
                Coefficient 3, either for normalized COP or heating
                capacity curve [1/degC2]

            C4: real
                Coefficient 4, either for normalized COP or heating
                capacity curve [1/degC]

            C5: real
                Coefficient 5, either for normalized COP or heating
                capacity curve [1/degC2]

            C6: real
                Coefficient 6, either for normalized COP or heating
                capacity curve [1/degC2]

        Returns:

            performance: dict
                * 'cop': current Coefficient Of Performance (COP), [-]
                * 'heat_cap': current heating capacity of heat pump, [W]
                * 'el_use': current electricity use of heat pump [W]
        """

        # Set rated heating capacity
        heat_cap_rated = self.params_hp[self.s['heat_cap_rated']]

        # Set rated COP (coefficient of performance)
        cop_rated = self.params_hp[self.s['cop_rated']]

        # Calculate actual heating capacity under current conditions
        # (T_wet_bulb and T_tank)
        heat_cap = heat_cap_rated * self._heat_pump(
            T_wet_bulb,
            T_tank,
            self.params_hp[self.s['c1_heat_cap']],
            self.params_hp[self.s['c2_heat_cap']],
            self.params_hp[self.s['c3_heat_cap']],
            self.params_hp[self.s['c4_heat_cap']],
            self.params_hp[self.s['c5_heat_cap']],
            self.params_hp[self.s['c6_heat_cap']])

        # if the temperature difference between the tank and the
        # ambient is large (e.g. an outside tank in a cold climate)
        # negative heat_cap values may occur based on the
        # equation in _heat_pump. Assuming that the device is
        # disabled at those times, we impose a lower limit at 0:
        if isinstance(heat_cap, np.ndarray):
            heat_cap[heat_cap < 0.] = 0.
        elif isinstance(heat_cap, float):
            heat_cap = abs(heat_cap * (heat_cap > 0))

        # Calculate actual COP under current conditions
        # (T_wet_bulb and T_tank)
        cop = cop_rated * self._heat_pump(
            T_wet_bulb,
            T_tank,
            self.params_hp[self.s['c1_cop']],
            self.params_hp[self.s['c2_cop']],
            self.params_hp[self.s['c3_cop']],
            self.params_hp[self.s['c4_cop']],
            self.params_hp[self.s['c5_cop']],
            self.params_hp[self.s['c6_cop']])

        # Dictionary containing the results
        res = {}
        res['cop'] = cop
        res['heat_cap'] = heat_cap
        res['el_use'] = heat_cap / cop

        return res

    @staticmethod
    def _heat_pump(T_wet_bulb, T_tank, C1 = 1.229E+00,
                   C2 = 5.549E-02, C3 = 1.139E-04,
                   C4 = -1.128E-02, C5 = -3.570E-06,
                   C6 = -7.234E-04):
        """Heat pump model. Source:
        B. Sparn, K. Hudon, and D. Christensen, “Laboratory Performance Evaluation of Residential Integrated Heat Pump Water Heaters,” Renew. Energy, p. 77, 2014.

        https://www1.eere.energy.gov/buildings/publications/pdfs/building_america/evaluation_hpwh.pdf

        Parameters:

            T_wet_bulb: real, array
                Inlet air wet bulb temperature [K]

            T_tank: real, array
                Water temperature in the storage tank [K]

            C1: real
                Coefficient 1, either for normalized COP or heating capacity
                curve [-]

            C2: real
                Coefficient 2, either for normalized COP or heating capacity
                curve [1/degC]

            C3: real
                Coefficient 3, either for normalized COP or heating capacity
                curve [1/degC^2]

            C4: real
                Coefficient 4, either for normalized COP or heating capacity
                curve [1/deg^C]

            C5: real
                Coefficient 5, either for normalized COP or heating capacity
                curve [1/degC^2]

            C6: real
                Coefficient 6, either for normalized COP or heating capacity
                curve [1/degC^2]

        Returns:

            performance: real
                Performance factor
        """

        # The formula needs temperatures in Celsius
        T_wet_bulb_C = UnitConv(T_wet_bulb).degC_K(unit_in='K')
        T_tank_C = UnitConv(T_tank).degC_K(unit_in='K')

        # Calculate performance factor
        performance = (C1 + C2 * T_wet_bulb_C +
                       C3 * T_wet_bulb_C * T_wet_bulb_C +
                       C4 * T_tank_C + C5 * T_tank_C * T_tank_C +
                       C6 * T_wet_bulb_C * T_tank_C)

        return performance

    def electric_resistance(self, Q_dem):
        """Electric resistance heater model. Can be
        used both as an instantaneous electric WH and as
        an auxiliary heater within the thermal tank.

        Parameters:

            Q_dem: float or array like, [W]
                Heat demand

        Returns:

            res: dict
                * self.r['q_del_bckp'] : float,
                  array - delivered heat rate, [W]
                * self.r['q_el_use'] : float,
                  array - electricity use, [W]
                * self.r['q_unmet'] : float,
                  array - unmet demand heat rate, [W]
        """

        # return the heat rates for:
        # delivered heat, electricity use, and unmet demand
        Q_del, P_el_use, Q_unmet = self._heater(
            Q_dem,
            Q_nom=self.size[self.s['el_res']],
            eff=self.params_el_res[self.s['eta_el_res']])

        # return the heat rate of heat delivered and gas consumed
        res = {self.r['q_del_bckp']: Q_del,
               self.r['el_use']: P_el_use,
               self.r['q_unmet']: Q_unmet}

        return res

    def gas_burner(self, Q_dem):
        """Gas burner model. Used both
        as an instantaneous gas WH and as a
        gas backup for solar thermal.

        Parameters:

            Q_dem: float or array like, W
                Heat demand

        Returns:

            res: dict
                * self.r['q_del_bckp'] : float,
                  array - delivered heat rate, [W]
                * self.r['q_gas_use'] : float, array - gas use heat rate, [W]
                * self.r['q_unmet'] : float, array -
                  unmet demand heat rate, [W]

                Any further unit conversion should be performed
                using unit_converters.Utility class
        """
        # return the heat rates for:
        # delivered heat, gas use, and unmet demand
        Q_del, Q_en_use, Q_unmet = self._heater(
            Q_dem,
            eff=self.params_gas_burn[self.s['comb_eff']],
            Q_nom=self.size[self.s['gas_burn']])

        # return the heat rate of heat delivered and gas consumed
        res = {self.r['q_del_bckp']: Q_del,
               self.r['gas_use']: Q_en_use,
               self.r['q_unmet']: Q_unmet}

        return res

    @staticmethod
    def _heater(Q_dem, eff=0.85, Q_nom=None):
        """Simplified efficiency based model that can be
        used for an in-tank main or auxiliary gas and
        electric resistance heater.

        Parameters:

            Q_dem: float or array like, W
                Heat demand

            eff: float
                Energy conversion efficiency, such as
                combustion or electric resistance

            Q_nom: float, W
                Nominal capacity.
                Default: None - infinite capacity
                so that the heater can cover any load

        Returns:

            Q_del: float, array
                Delivered heat rate, [W]

            Q_gas_use: float, array
                Energy (gas, electricity) use heat rate, [W]

            Q_unmet: float, array
                Unmet demand heat rate, [W]
        """
        # start with assuming the heater capacity is infinite
        Q_del = Q_dem + 0.

        # limit the delivery if the heater has a limited capacity
        if Q_nom is not None:
            if not np.isscalar(Q_dem):
                Q_del[Q_del > Q_nom] = Q_nom
            elif np.isscalar(Q_dem):
                Q_del = min(Q_dem, Q_nom)
            else:
                msg = 'Heater demand data type {} seems not supported.'
                log.error(msg.format(type(Q_dem)))
                raise ValueError

        # Unmet demand
        Q_unmet = Q_dem - Q_del

        # Gas consumption (heat rate in W, use unit_converters.Utility class
        # for further conversions)
        Q_en_use = Q_del / eff

        return Q_del, Q_en_use, Q_unmet

    def solar_collector(self, t_in, t_amb=None, inc_rad=None):
        """Two commonly used empirical instantaneous collector
        efficiency models based on test data from standard
        test procedures (SRCC, ISO9806), found in
        J. A. Duffie and W. A. Beckman, Solar engineering of thermal processes, 3rd ed. Hoboken, N.J: Wiley, 2006., are:

        * Cooper and Dunkle (CD model, eq 6.17.7)
        * Hottel-Whillier-Bliss (HWB model, eq 6.16.1, 6.7.6)

        Parameters:

            t_in: float, array
                Collector inlet temperature (timeseries) [K]

            t_amb: float, array
                Ambient temperature (timeseries) [K]
                Default: None (to use data extracted from the weather df)

            inc_rad: float, array
                Incident radiation (timeseries) [W]
                Default: None (to use data extracted from the weather df)

        Returns:

            res: dict or floats or arrays

                {'Q_gain' : Solar gains from the gross collector area, [W]
                 'eff' : Efficiency of solar to heat conversion, [-]
        """
        try:
            gross_area = self.size[self.s['sol_col']]
        except:
            gross_area = 1.

            msg = 'Could not extract collector size. '\
                  'Setting it to {}.'
            log.info(msg.format(gross_area))

        # if t_in is output of the tank model, solar collector
        # model needs to be simulated step by step. In that
        # case the timestep ambient temperature and incident solar
        # radiation should be passed directly to this method
        if t_amb is None:
            msg = 'Using ambient temperature array to get solar '\
                'collector gains. This will result in an array calculation.'
            log.info(msg)
            t_amb = self.t_amb

        if inc_rad is None:
            msg = 'Using irradiation array to get solar collector'\
                  ' gains. This will result in an array calculation.'
            log.info(msg)
            inc_rad = self.inc_rad

        if self.use_defaults:
            msg = 'Solar collector parameters have not been passed to the'\
                  ' component model. Using HWB model with default parameters.'
            log.info(msg)

            self.sol_col_gain, self.sol_col_eff = self._hwb_solar_collector(
                gross_area,
                inc_rad,
                t_amb,
                t_in)

        # based on the keywords in self.params call one or the other method
        elif self.solar_model == 'HWB':
            self.sol_col_gain, self.sol_col_eff = self._hwb_solar_collector(
                gross_area,
                inc_rad,
                t_amb,
                t_in,
                intercept=self.params_sol_col[self.s['interc_hwb']],
                slope=self.params_sol_col[self.s['slope_hwb']])

        elif self.solar_model == 'CD':
            self.sol_col_gain, self.sol_col_eff = self._cd_solar_collector(
                gross_area,
                inc_rad,
                t_amb,
                t_in,
                intercept=self.params_sol_col[self.s['interc_cd']],
                a_1=self.params_sol_col[self.s['a1_cd']],
                a_2=self.params_sol_col[self.s['a2_cd']])

        if not isinstance(t_in, float):
            msg = '\nCalculated solar collector gain time series.\n'
            log.info(msg)

        res = {'Q_gain': self.sol_col_gain,\
               'eff': self.sol_col_eff}

        return res

    @staticmethod
    def _hwb_solar_collector(gross_area, inc_rad, t_amb, t_in,
                             intercept=.753, slope=-4.025):
        """HWB based model as applied in test procedures
        used in SRCC Standard 100-2006-09 (ASHRAE 93)

        Default parameters: Heliodyne, Inc, GOBI 410 001 Plus

        Parameters:

            gross_area: float
                Gross collector area [m2]

            inc_rad: float or array like
                Global solar radiation on 1 m2 of the
                collector tilted surface [W/m2]

            t_amb: float or array like
                Ambient temperature (timeseries) [K or degC]

            t_in: float or array like
                Collector inlet temperature (timeseries)
                [use same unit as t_amb]

            intercept: float
                Rating parameter

            slope: float
                Rating parameter

        Returns:

            solar_gain: float, array
                Solar gains from the gross collector area [W]

            conversion_efficiency: float, array
                Conversion efficiency [-]
        """
        # msg = 'Allow div 0.'
        # log.debug(msg)

        # avoid division by zero by creating a copy
        # of the irradiation data with infinity
        # instead of zero (see efficiency formula)
        if not np.isscalar(inc_rad):
            inc_rad_mod = inc_rad
            inc_rad_mod[inc_rad == 0] = -np.inf
        elif np.isscalar(inc_rad):
            if inc_rad == 0.:
                inc_rad_mod = -np.inf
            else:
                inc_rad_mod = inc_rad
        else:
            msg = 'Solar irradiation data type {} seems not supported.'
            log.error(msg.format(type(Q_dem)))
            raise ValueError

        # instantaneous collector efficiency, [-]
        eta = (intercept * (inc_rad != 0.) +
               slope * ((t_in - t_amb) / inc_rad_mod))

        # instantaneous solar gain, [W]
        calc_gain =  inc_rad * gross_area * eta

        # set negative gains that the model may yield at
        # cold weather to zero
        if isinstance(calc_gain, np.ndarray):
            calc_gain[calc_gain < 0.] = 0.
            gain = calc_gain
        elif isinstance(calc_gain, float):
            gain = calc_gain * (calc_gain > 0)

        return gain, eta

    @staticmethod
    def _cd_solar_collector(gross_area, inc_rad, t_amb, t_in,
                            intercept=.75, a_1=-3.688, a_2=-.0055):
        """CD based model as applied in test procedures
        used in SRCC Standard 100-2006-09 (ISO 12975 with dT = Tin - Tamb)

        Default parameters: `Heliodyne, Inc, GOBI 410 001 Plus <https://secure.solar-rating.org/Certification/Ratings/RatingsReport.aspx?device=6931&units=METRICS>`_

        Parameters:

            gross_area: float
                Gross collector area [m2]

            inc_rad: float, array
                Global solar radiation on 1 m2 of the
                collector tilted surface [W/m2]

            t_amb: float, array
                Ambient temperature (timeseries) [K or degC]

            t_in: float, array
                Collector inlet temperature (timeseries)
                [use same unit as t_amb]

            intercept: float
                Rating parameter

            a_1: float
                Rating parameter

            a_2: float
                Rating parameter
        """
        # avoid division by zero by creating a copy
        # of the irradiation data with infinity
        # instead of zero (see efficiency formula)
        if not np.isscalar(inc_rad):
            inc_rad_mod = inc_rad
            inc_rad_mod[inc_rad == 0] = -np.inf
        elif np.isscalar(inc_rad):
            if inc_rad == 0.:
                inc_rad_mod = -np.inf
            else:
                inc_rad_mod = inc_rad
        else:
            msg = 'Solar irradiation data type {} seems not supported.'
            log.error(msg.format(type(Q_dem)))
            raise ValueError

        # instantaneous collector efficiency, [-]
        eta = (intercept * (inc_rad != 0.) +
               a_1 * ((t_in - t_amb) / inc_rad_mod) +
               a_2 * ((t_in - t_amb) / inc_rad_mod ** 2))

        # instantaneous solar gain, [W]
        calc_gain = inc_rad * gross_area * np.nan_to_num(eta)

        # set negative gains that the model may yield at
        # cold weather to zero
        if isinstance(calc_gain, np.ndarray):
            calc_gain[calc_gain < 0.] = 0.
            gain = calc_gain
        elif isinstance(calc_gain, float):
            gain = calc_gain * (calc_gain > 0)

        return gain, eta

    def photovoltaic(self, use_p_peak=True, inc_rad=None):
        """Photovoltaic model

        Parameters:

            use_p_peak: boolean
                Boolean flag determining if peak power is used for sizing
                the pv panel (instead of area and efficiency)

        Returns:

            self.pv_power: dict of floats
                Generated power [W]

                * 'ac' : AC
                * 'dc' : DC
        """
        try:
            panel_size = self.size[self.s['pv']]

        except:
            # default to 1000. kW_peak or it's equivalent in m2 for
            # default efficiency
            panel_size = 1000. if use_p_peak else 6.25
            log.info(\
                'Could not get panel size. Setting it to {}'\
                .format(panel_size))

        # Set panel size according to use_p_peak value
        if use_p_peak:
            p_peak = panel_size
            panel_area = None
            # Uncomment this line, since it creates too much output
            # for system level simulation
            # log.info('Using peak power as a PV size parameter.')
        else:
            p_peak = None
            panel_area = panel_size
            # Uncomment this line, since it creates too much output
            # for system level simulation
            #log.info('Using area as a PV size parameter.')

        if inc_rad is None:
            msg = 'Using irradiation array to get photovoltaic'\
                  ' gains. This will result in an array calculation.'
            log.info(msg)
            inc_rad = self.inc_rad

        # if no input parameters have been passed to the class
        if self.use_defaults:
            msg = 'Photovoltaic parameters have not been passed to the'\
                  ' component model. Using default parameters.'
            log.info(msg)

            self.pv_power = self._simple_photovoltaic(
                irrad=inc_rad,
                panel_area=panel_area,
                p_peak=p_peak)

        # pass parameters from the param input dataframe
        else:
            self.pv_power = self._simple_photovoltaic(
                irrad=inc_rad,
                panel_area=panel_area,
                f_act=self.params_pv[self.s['f_act']],
                eta_pv=self.params_pv[self.s['eta_pv']],
                eta_dc_ac=self.params_inv[self.s['eta_dc_ac']],
                irrad_ref=self.params_pv[self.s['irrad_ref']],
                p_peak=p_peak)

        return self.pv_power

    @staticmethod
    def _simple_photovoltaic(irrad, p_peak=None, panel_area=None,
                             f_act=1., eta_pv=.16,
                             eta_dc_ac=0.85, irrad_ref=1000.):
        """Simple photovoltaic model based on
        http://simulationresearch.lbl.gov/modelica/releases/latest/help/Buildings_Electrical_AC_OnePhase_Sources.html#Buildings.Electrical.AC.OnePhase.Sources.PVSimple

        Parameters:

            irrad: float
                Total solar irradiation (direct and diffuse) [W/m2]

            panel_area: float or None
                Panel area (area of active cells) [m2].
                Set to None if using the peak power as a PV sizing variable.

            p_peak: float or None
                Peak power of the photovoltaic panel
                (also: nominal power, nameplate size) [W]
                Set to None if using the panel area as a PV sizing variable.

            irrad_ref: float
                Reference irradiation of the photovoltaic panel
                (default: 1000 W/m2) [W/m2]

            f_act: float
                Fraction of the aperature panel with active cells

            eta_pv: float
                Panel efficiency

            eta_dc_ac: float
                Efficiency of the dc-ac conversion
                (inverter + other system losses)

        Returns:

            pv_power: dict of floats
                Generated power [W]

                * 'ac' : AC
                * 'dc' : DC
        """
        # Calculate the generated power according to the given parameters:
        # Either panel area and panel efficiency
        # or peak power and reference irradiation are used for calculation
        if p_peak == None:
            pv_power_dc = panel_area * f_act * eta_pv * irrad
        else:
            pv_power_dc = (p_peak / irrad_ref) * irrad

        pv_power_ac = Distribution._dc_to_ac(
            pv_power_dc,
            conv_eff=eta_dc_ac)

        pv_power = {'ac': pv_power_ac,
                    'dc': pv_power_dc}

        return pv_power


class Storage(object):
    """Describes performance of storage components, such as
    solar thermal tank, heat pump thermal tank, conventional gas
    tank water heater.

    Parameters:

        params: pd df
            Component performance parameters per project
            Default: None. See tests and examples on how to
            structure this input.

        weather: pd df
            Weather data timeseeries (amb. temp, solar irradiation)
            Default: None. See tests and examples on how to
            structure this input.

        size: pd df or float, m3
            Tank size.
            Default 1. See tests and examples on how to
            structure this input.

        type: string
            Type of storage component. Options:
        
            * 'sol_tank' - indirect tank WH with a coil to circulate
              fluid heated by a solar collector
            * 'hp_tank' - tank with an inbuilt heat pump
              'wham_tank' - conventional gas tank water heater model
              based on a WH model from the efficiency standards analysis
            * 'gas_tank' - conventional gas tank water heater (currently not
              implemented)

        log_level: None or python logger logging level,
            Default: logging.DEBUG
            This applies for a subset of the class functionality, mostly
            used to deprecate logger messages for certain calculations.
            For Example: log_level = logging.ERROR will only throw error
            messages and ignore INFO, DEBUG and WARNING.

        timestep: float, h
            Duration of a single timestep, in hours, defaults to 1.

    Note:

        Create a new instance of the class for each storage component.

    Examples:

        See :func:`swh.system.tests.test_components <swh.system.tests.test_components>` module and
        :func:`scripts/Project Level SWH System Tool.ipynb <scripts/Project Level SWH System Tool.ipynb>`
        for examples on how to use the methods as stand alone and
        in a system model simulation.
    """

    def __init__(self, params=None, size=1., type='sol_tank',
                 timestep=1., log_level=logging.DEBUG):

        # log level (e.g. only partial functionality of the class
        # is being used and one does not desire to see all infos)
        self.log_level = log_level
        logging.getLogger().setLevel(log_level)

        self.s = SwhLabels().set_prod_labels()
        self.r = SwhLabels().set_res_labels()

        self.type = type

        if params is None:
            # extract component size/capacity (see setter for details)
            self.size = size
            # instantiate with defaut parameters
            if type in ['sol_tank', 'hp_tank']:
                split_tank = True
                gas_heater_autosize = False
            elif type == 'wham_tank':
                split_tank = False
                gas_heater_autosize = True
            else:
                msg = 'The thermal storage tank type {}'\
                      'is not implemented.'
                log.error(mgs.format(self.type))
                raise Exception

            self.setup_thermal(
                split_tank=split_tank,
                gas_heater_autosize=gas_heater_autosize)

            # on the hp branch
            self.setup_electric()

            msg = 'Storage parameters have not been passed to the class. '\
                  'Using default parameters.'
            log.info(msg)

        self.timestep = timestep  # [h]

        if isinstance(params, pd.DataFrame):

            self.components = []
            # get all components of the project level system
            components = params[self.s['comp']].unique().tolist()

            if self.s['the_sto'] in components:

                self.components.append(self.s['the_sto'])

                comp_params = params.loc[
                    params[self.s['comp']] == self.s['the_sto'],:]

                params_sol_tank = dict()

                params_sol_tank[self.s['ins_thi']] = params.loc[
                     params[self.s['param']] == self.s['ins_thi'],
                    self.s['param_value']].values[0]

                params_sol_tank[self.s['spec_hea_con']] = params.loc[
                    params[self.s['param']] == self.s['spec_hea_con'],
                    self.s['param_value']].values[0]

                params_sol_tank[self.s['f_upper_vol']] = params.loc[
                    params[self.s['param']] == self.s['f_upper_vol'],
                    self.s['param_value']].values[0]

                params_sol_tank[self.s['h_vs_r']] = params.loc[
                    params[self.s['param']] == self.s['h_vs_r'],
                    self.s['param_value']].values[0]

                params_sol_tank[self.s['dt_appr']] = params.loc[
                    params[self.s['param']] == self.s['dt_appr'],
                    self.s['param_value']].values[0]

                params_sol_tank[self.s['t_max_tank']] = params.loc[
                    params[self.s['param']] == self.s['t_max_tank'],
                    self.s['param_value']].values[0]

                params_sol_tank[self.s['t_tap_set']] = params.loc[
                    params[self.s['param']] == self.s['t_tap_set'],
                    self.s['param_value']].values[0]

                if type == 'sol_tank':
                    params_sol_tank[self.s['eta_coil']] = params.loc[
                        params[self.s['param']] == self.s['eta_coil'],
                        self.s['param_value']].values[0]
                elif type == 'hp_tank':
                    # based on the model definition (net performance of
                    # an inbuilt heat pump)
                    params_sol_tank[self.s['eta_coil']] = 1.
                else:
                    msg = 'The thermal storage tank type {}'\
                          'is not implemented.'
                    log.error(mgs.format(self.type))
                    raise Exception

                self.size = size

                # setup the solar storage tank with the given parameters
                self.setup_thermal(
                    vol_fra_upper=params_sol_tank[self.s['f_upper_vol']],
                    h_vs_r=params_sol_tank[self.s['h_vs_r']],
                    dT_param=params_sol_tank[self.s['dt_appr']],
                    T_max=params_sol_tank[self.s['t_max_tank']],
                    T_draw_set=params_sol_tank[self.s['t_tap_set']],
                    insul_thickness=params_sol_tank[self.s['ins_thi']],
                    spec_hea_cond=params_sol_tank[self.s['spec_hea_con']],
                    coil_eff=params_sol_tank[self.s['eta_coil']],
                    gas_heater_autosize=False)

                msg = '{} is set.'
                log.info(msg.format((self.s[self.type]).capitalize()))

            elif ((self.s['gas_tank'] in components) and
                  (type == 'wham_tank')):

                self.components.append(self.s['gas_tank'])

                comp_params = params.loc[
                    params[self.s['comp']] == self.s['gas_tank'],:]

                params_gas_tank_wh = dict()

                params_gas_tank_wh[self.s['tank_re']] = comp_params.loc[
                    params[self.s['param']] == self.s['tank_re'],
                    self.s['param_value']].values[0]

                params_gas_tank_wh[self.s['ins_thi']] = comp_params.loc[
                    params[self.s['param']] == self.s['ins_thi'],
                    self.s['param_value']].values[0]

                params_gas_tank_wh[self.s['spec_hea_con']] = comp_params.loc[
                    params[self.s['param']] == self.s['spec_hea_con'],
                    self.s['param_value']].values[0]

                params_gas_tank_wh[self.s['t_tap_set']] = comp_params.loc[
                    params[self.s['param']] == self.s['t_tap_set'],
                    self.s['param_value']].values[0]

                self.size = size

                # setup the gas tank water heater with the given parameters
                self.setup_thermal(
                    split_tank=False,
                    T_draw_set=params_gas_tank_wh[self.s['t_tap_set']],
                    insul_thickness=params_gas_tank_wh[self.s['ins_thi']],
                    spec_hea_cond=params_gas_tank_wh[self.s['spec_hea_con']],
                    tank_re=params_gas_tank_wh[self.s['tank_re']],
                    gas_heater_autosize=True)

                msg = 'Gas tank WH (WHAM) is set up.'
                log.info(msg)

            else:
                msg = 'Parameters passed to the class do not contain the '\
                      'desired storage type {}.'

                log.error(msg.format(type))
                raise Exception

        if not isinstance(size, pd.DataFrame):
            dist_sizes = pd.DataFrame(
                data=[[self.s['piping'], 0.]],
                columns=[self.s['comp'], self.s['cap']])

        self.distribution = Distribution(
            params=params,
            sizes=size)

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        """Re-extracts tank size from a dataframe
        """
        set_size = dict()

        if not isinstance(value, pd.DataFrame):
            # assign unit size
            set_size = value

        elif isinstance(value, pd.DataFrame):

            if self.s['the_sto'] in self.components:
                set_size = \
                value.loc[value[self.s['comp']] == self.s['the_sto'],
                          self.s['cap']].values[0]

            elif self.s['gas_tank'] in self.components:
                set_size = \
                value.loc[value[self.s['comp']] == self.s['gas_tank'],
                          self.s['cap']].values[0]

            elif self.s['hp_tank'] in self.components:
                set_size = \
                value.loc[value[self.s['comp']] == self.s['hp_tank'],
                          self.s['cap']].values[0]

        else:
            msg = 'Provided sizes format is not supported.'
            log.error(msg)
            raise Exception

        self.__size = set_size

    def setup_thermal(self, medium='water',
                      split_tank=True,
                      vol_fra_upper=.5, h_vs_r=6.,
                      dT_param=2.,
                      T_max=344.15, T_draw_set=322.04,
                      insul_thickness=.085,
                      spec_hea_cond=.04,
                      coil_eff=.84,
                      tank_re=.76,
                      dT_err_max=2.,
                      gas_heater_autosize=False):
        """Sets thermal storage variables related to:

        - loss calculation
        - distribution of net gains/losses within two
          tank volumes (upper and lower)

        Parameters:

            medimum: string
                Storage medium (for thermal defaults to 'water')

            vol_fra_upper: float
                Fraction of storage volume assigned to the upper
                tank volume (applies to 'thermal' only)
                If split_tank set to False, the value is ignored

            dT_param: float, K
                Used as:

                * Maximum temperature difference expected to occur
                  between the upper and the lower tank volume while charging

                * In-tank-coil approach

            h_vs_r: float
                Regression parameter - tank height/diameter ratio
                (based on web scraped data), default: 6.

            T_max: float, K
                Maximum allowed fluid temperature in the thermal
                storage tank, defaults to 344.15 K = 71 degC.

            T_draw_set: float, K
                Draw temperature used in the
                load calculation, defaults to
                120 degF = 322.04 K = 48.89 degC

            coil_eff: float
                Simplified efficiency of the coil heat exchanger
                Used in modeling of indirect coil-in-tank water heaters
                It excludes the approach temperature and represents
                the remaining heat transfer inefficiency

            tank_re: float
                Recovery efficiency of a gas tank water heater.
                Used for the Storage.gas_tank_wh model

            dT_err_max: float
                Allowed dT error below the minimum
                tank temperature due to finite timestep length
                approximation

            gas_heater_autosize: boolean
                There is a gas heater in the tank and it will be
                autosized based on the tank volume
        """

        # max allowed tank temperature (start with 160 degF, per TAC info)
        self.T_max = T_max  # K

        # draw setpoint temperature
        self.T_draw_set = T_draw_set  # K

        # fluid properties
        if medium == 'water':
            # Water properties, :cite:`ASHFund17` 33. table 2
            # density at 20 degC
            self.ro = 998.2  # kg/m3
            # specific heat content at 20 degC
            self.shc = 4180.  # J/(kgK)

        elif medium == 'glycol':
            pass

        # Recovery efficiency of gas tank water heater
        self.tank_re = tank_re

        # Maximum allowed temperature difference between the
        # upper and the lower tank volume while charging
        self.dT_approach = dT_param  # K

        # initiate allowed dT error below the minimum
        # tank temperature due to finite timestep length
        # approximation, in K
        self.dT_err = dT_err_max  # K

        # upper tank volume fraction
        self.vol_fra_upper = vol_fra_upper
        # tank height diametar ratio
        self.h_vs_r = h_vs_r

        # thus lower volume
        self.V_lower = self.size * (1. - self.vol_fra_upper)
        # and upper volume
        self.V_upper = self.size * self.vol_fra_upper

        # volume
        self.V = self.size

        # For tanks with a gas heater input:
        if gas_heater_autosize:
            # Calculate nominal water heater input power
            self.Q_nom = self.volume_to_power(self.V)

        # tank heat loss parameters

        # thermal transmittance through the tank walls
        self.therm_transm_coef = self._thermal_transmittance(
            insul_thickness=insul_thickness,
            spec_hea_cond=spec_hea_cond)

        # if there is a coil, this is its efficiency
        self.coil_eff = coil_eff

        # areas to calculate thermal losses to environment
        # e.g. to apply for a solar indirect tank
        if split_tank:
            self.A_lower = self._tank_area()['lower']
            self.A_upper = self._tank_area()['upper']
            self.A = self.A_lower + self.A_upper
        # e.g. to apply to the gas tank WH WHAM model
        else:
            self.A = self._tank_area(split_tank=False)

    def thermal_tank_dynamics(self, pre_T_amb, pre_T_upper,
                              pre_T_lower, pre_Q_in,
                              pre_Q_loss_upper, pre_Q_loss_lower,
                              pre_T_feed, pre_Q_tap):
        """Partial model of a thermal storage tank.
        Applies first order forward marching Euler method and updates
        the tank state for the current timestep
        based on the enthalpy balance and simplified
        assumptions about stratification. Thus, all
        input variables pertain to the previous timestep,
        while the outputs are solutions for the current timestep.

        For example partial model application see thermal_tank method.

        See inline comments for detailed explanation of the model.

        Parameters:

            pre_T_amb: float, K
                Ambient air temperature

            pre_T_upper: float, K
                Upper tank volume temperature

            pre_T_lower: float, K
                Lower tank volume temperature

                It is recommended to set equal initial values
                for pre_T_upper and pre_T_lower

            pre_Q_in: float, W
                Total heat gain (e.g. from a coil heat exchanger,
                a heating element, etc.)

            pre_Q_loss_upper: float, W
                Heat loss from the upper tank volume

            pre_T_lower: float, W
                Heat loss from the lower tank volume

            pre_T_feed: float, K
                Temperature of the water
                that replenishes the tapped volume
                (e.g. water main temperature)

            pre_Q_tap: float, W
                Heat loss that would occur if the tank
                volume at pre_T_upper was infinite

        Returns:

            res: dict of floats
                Represent averages in a single timestep.
                Average temperatures for tank volumes:

                * self.r[self.r['t_tank_low']] : lower, K
                * self.r['t_tank_up'] : upper, K

                Heat rates:

                * 'Q_net' : expected timestep net gain/loss based on inputs, W
                  self.r['q_dump'] : dumped heat, W
                * 'Q_draw' : delivered to load W
                * 'Q_draw_unmet' : unmet load due to finite tank volume, W
                  self.r['q_ovrcool_tank'] : error in balancing due to minimal
                  tank temperature limit assumption in each timestep

                Note: 'Q_draw' + 'Q_draw_unmet' = pre_Q_tap
        """
        # initiate the dumped heat content as zero:
        Q_dump = 0.
        # Initial assumption is that the tank can deliver the
        # load that can be tapped based on the upper tank
        # temperature (see Storage.tap method for details)
        Q_del = pre_Q_tap
        Q_unmet = 0.

        # initiate the resulting error in heat balance
        Q_overcool = 0.

        # Get the minimum tank temperature limit
        pre_T_min = min(pre_T_amb, pre_T_feed)

        # Get net heat gain/loss rate inside the tank
        dQ = (pre_Q_in - pre_Q_loss_lower -
              pre_Q_loss_upper - pre_Q_tap)

        # Get net heat gain/loss in a single timestep in J,
        # assuming timestep given in h!
        dE = UnitConv(dQ * self.timestep).Wh_J(unit_in='Wh')

        # Distribution of the net heat gain/loss

        # net charge
        if dQ > 0:
            Q_dump, Q_overcool, T_lower, T_upper = self._tank_charge(
                pre_Q_tap,
                dE,
                pre_T_lower,
                pre_T_upper,
                pre_T_min,
                Q_dump,
                Q_overcool,
                pre_T_amb,
                pre_T_feed)

        # net discharge or balanced
        elif dQ <= 0:
            Q_del, Q_unmet, Q_overcool, T_lower, T_upper = self._tank_discharge(
                pre_Q_tap,
                dE,
                pre_T_lower,
                pre_T_upper,
                pre_T_min,
                Q_unmet,
                Q_del,
                Q_overcool,
                pre_T_amb,
                pre_T_feed)

        # Check tapped water heat balance
        if pre_Q_tap != 0:
            rel_err = ((Q_unmet + Q_del) - pre_Q_tap) / pre_Q_tap
            if not rel_err < .01:
                msg = 'Tank delivered {} and unmet {} demand do not balance '\
                      'with the tank demand setpoint {}'
                log.error(msg.format(Q_del, Q_unmet, pre_Q_tap))
                raise Exception

        # did any part of the algorithm bring the lower tank
        # temperature above the upper
        if T_lower > T_upper:
            msg = 'Upper tank temperature is below the lower '\
                  'tank tamperature.'
            log.error(msg)
            raise Exception

        # pack results
        res = {self.r['t_tank_low']: T_lower,
               self.r['t_tank_up']: T_upper,
               'Q_net': dQ,
               self.r['q_dump']: Q_dump,
               self.r['q_ovrcool_tank']: Q_overcool,
               self.r['q_del_tank']: Q_del,
               self.r['q_unmet_tank']: Q_unmet}

        return res

    def _tank_charge(self, pre_Q_tap, dE, pre_T_lower, pre_T_upper,
                     pre_T_min, Q_dump, Q_overcool, pre_T_amb, pre_T_feed):
        """Storage charge partial model. While charging the tank
        assume that stratification happens up to a predefined
        "stratification limit when charging" temperature difference.
        This is taken as an empirical value based on observed
        literature.

        Assuming uniform tank temperature distribution at initiation,
        net heat gain is allocated to the upper tank volume until
        the difference between the temperatures in the upper and
        in the lower tank volume reaches the empirical temperature
        difference limit, after which both lower and upper
        volumes get allocated with heat gain

        If the upper tank volume reaches the maximum allowed tank
        temperature limit, the thermostat will prevent the storage
        from overcharging.

        See :func:`thermal_tank_dynamics <thermal_tank_dynamics>` method
        for parameters and returns description.
        """
        if dE <= 0:
            msg = 'This method does not apply if there are no net '\
                   'heat gains to the tank.'
            log.info(msg)

        if (pre_T_upper - pre_T_lower) < self.dT_approach:

            # Temperature increase to upper volume that would
            # be achieved should all the gain be allocated to it
            dT_upper = (dE /
                        (self.V_upper * self.ro * self.shc))

            # Nonetheless, allow heating only up to the predefined
            # charging temperature difference between the upper
            # and the lower tank volume
            dT_rem = ((dT_upper + pre_T_upper) -
                      (pre_T_lower + self.dT_approach))

            # Any remaining heat gain after reaching the temperature
            # difference limit gets allocated to both volumes:
            if dT_rem > 0:
                dT_rem_both = dT_rem * (self.V_upper / self.V)
                T_upper = pre_T_upper + dT_upper - dT_rem + dT_rem_both
                T_lower = pre_T_lower + dT_rem_both

            # otherwise heat up only the upper volume
            else:
                T_upper = pre_T_upper + dT_upper
                T_lower = pre_T_lower

        # Once stratification limit when charging has been
        # achieved, it remains maintained
        elif (pre_T_upper - pre_T_lower) >= self.dT_approach:

            # get the lower volume up to
            # pre_T_upper - self.dT_approach
            dT_lower_max = (pre_T_upper - self.dT_approach) - pre_T_lower
            dT_lower = (dE /
                        (self.V_lower * self.ro * self.shc))

            if dT_lower <= dT_lower_max:
                T_lower = pre_T_lower + dT_lower
                T_upper = pre_T_upper
            else:
                T_lower = pre_T_lower + dT_lower_max
                dT_rem = ((dT_lower - dT_lower_max) *
                          (self.V_lower / self.V))
                # after heating up the lower part of the tank
                # the temperature difference when charging
                # has been reached and the rest of the heat
                # should get assigned in parallel
                T_upper = pre_T_upper + dT_rem
                T_lower += dT_rem

        # Check the behavior of tank temperatures
        # related to the min tank temperature
        if (T_upper < pre_T_min) or (T_lower < pre_T_min):
            Q_overcool, T_upper, T_lower = self._overcooling(
                pre_T_min,
                T_upper,
                T_lower,
                pre_T_amb,
                pre_T_feed,
                discharge=False)

        # would the conditions overcharge the tank?
        if T_upper > self.T_max:
            T_upper, T_lower, Q_dump = self._thermostatic_safety_valve(
                T_upper,
                T_lower)

        return Q_dump, Q_overcool, T_lower, T_upper

    def _tank_discharge(self, pre_Q_tap, dE, pre_T_lower, pre_T_upper,
                        pre_T_min, Q_unmet, Q_del, Q_overcool, pre_T_amb,
                        pre_T_feed):
        """Storage discharge partial model. When there are no gains
        to the tank:

        * if there is water draw the model reduces temperature in both
          parts of the tank. This emulates the propagation of
          the water main as the DHW is tapped and shifting the
          temperature profile downwards in the entire tank.

        * if there is no water draw, assumes stagnation mode. Cools off
          the lower tank volume first, after which the upper tank volume
          starts cooling off, depending on the heat loss amount.

        Parameters:

            dE: float
                Timestep net heat balance inside the tank, this method assumes
                it not larger than zero.

        See :func:`thermal_tank_dynamics <thermal_tank_dynamics>` method
        for parameters and returns description.
        """

        if dE > 0:
            msg = 'This method cannot be called if the timestep heat '\
                   'balance is positive.'
            log.error(msg)
            raise Exception

        # water draw exists
        if pre_Q_tap > 0:
            # cool in parallel as low as possible (until the lower
            # volume hits the minimum). This mimics the bulk vertical
            # motion of the water with the hot being tapped from
            # the top and the water main entering from the bottom

            # theoretical temperature reduction if it would be
            # possible to satisfy the entire loss from the tank volume
            dT = -1. * (dE / (self.V  * self.ro * self.shc))

            # maximum possible temperature reduction to the lower volume
            dT_lower_max = max(0., (pre_T_lower - pre_T_min))

            if dT <= dT_lower_max:
                # The entire demand got satisfied
                T_upper = pre_T_upper - dT
                T_lower = pre_T_lower - dT

            else:
                # Cool in paralled until the lower volume is at
                # its minimum temperature
                T_upper = pre_T_upper - dT_lower_max
                T_lower = pre_T_lower - dT_lower_max

                # Try to take the rest of the loss from the
                # upper volume
                dT_upper = (dT - dT_lower_max) * (self.V / self.V_upper)

                dT_upper_max = max(0., (T_upper - pre_T_min))

                if dT_upper < dT_upper_max:
                    T_upper -= dT_upper
                else:
                    T_upper -= dT_upper_max

                    Q_unmet = UnitConv(
                        ((dT_upper - dT_upper_max) *
                         (self.V_upper  * self.ro * self.shc))).Wh_J(unit_in='J') / self.timestep
                    Q_del -= Q_unmet

            if (T_upper < pre_T_min) or (T_lower < pre_T_min):
                Q_overcool, T_upper, T_lower = self._overcooling(
                    pre_T_min,
                    T_upper,
                    T_lower,
                    pre_T_amb,
                    pre_T_feed,
                    discharge=True)

        # no water draw (stagnation)
        elif abs(pre_Q_tap) == 0.:
            # See what would be the temperature difference
            # should all the heat be lost from the lower
            # part of the tank
            dT_lower_max = (dE /
                            (self.V_lower * self.ro * self.shc))

            # allow cooling off of the lower part of the tank
            # either for the full amount of losses or down
            # to ambient temperature increased in the approach
            # temperature, whichever is larger
            T_lower = max((pre_T_lower + dT_lower_max),\
                          (pre_T_min + self.dT_approach))
            T_upper = pre_T_upper

            # Would this temperature difference bring
            # the lower part of the tank below the
            # minimal allowed temperature and how much lower?
            dT_lim_lower = ((pre_T_min + self.dT_approach) -
                            (pre_T_lower + dT_lower_max))

            # If exists, assign that remaining part of heat loss
            # to the upper part of the tank
            if dT_lim_lower > 0:
                # get the eqivalent temperature difference for the
                # upper part of the tank
                dT_to_upper = dT_lim_lower * (self.V_lower / self.V_upper)

                # allow cooling off of the upper part of the tank
                # either for the full amount of losses or down
                # to ambient temperature increased in the approach
                # temperature, whichever is larger
                T_upper = max((pre_T_upper - dT_to_upper),
                              (pre_T_min + self.dT_approach))

                # If any heat loss remains, cool both volumes equally
                dT_lim_upper = ((pre_T_min + self.dT_approach) -
                                (pre_T_upper - dT_to_upper))

                if dT_lim_upper > 0:
                    # Get temperature difference for both parts
                    # of the tank
                    dT_to_both = dT_lim_upper * (self.V_upper / self.V)
                    T_upper = T_upper - dT_to_both
                    T_lower = T_lower - dT_to_both

            if (T_upper < pre_T_min) or (T_lower < pre_T_min):
                Q_overcool, T_upper, T_lower = self._overcooling(
                    pre_T_min,
                    T_upper,
                    T_lower,
                    pre_T_amb,
                    pre_T_feed,
                    discharge=True)

        return Q_del, Q_unmet, Q_overcool, T_lower, T_upper

    def _thermostatic_safety_valve(self, T_upper, T_lower):
        """This emulates the behavior of a thermostatic
        safety valve placed at the top of the tank to prevent
        overheating.

        If the upper tank temperature exceeds the maximum
        tank temperature limit, charge the lower
        tank volume up to the temperature of the upper less the
        predifined tempearture difference if possible and
        dump any remaining heat.

        Parameters:

            T_upper: float, K
                Upper tank volume temperature at the end of
                a timestep

            T_lower: float, K
                Lower tank volume temperature at the end of
                a timestep

        Returns:

            T_upper: float, K
                Updated upper tank volume temperature

            T_lower: float, K
                Updated lower tank volume temperature

            Q_dump: float, W
                Heat dumped if the tank gets overcharged
        """
        # The thermostat got triggered!
        # Get the excess heat and stop charging the tank
        E_dump = ((self.V_upper * self.ro * self.shc) *
                  (T_upper - self.T_max))
        T_upper = self.T_max
        # Was the charge high enough to overcharge the
        # lower part of the tank as well?
        if T_lower > (self.T_max - self.dT_approach):
            E_dump += ((self.V_lower * self.ro * self.shc)
                       * (T_lower - (self.T_max - self.dT_approach)))
            T_lower = self.T_max - self.dT_approach

        # Convert to average timestep heat rate
        Q_dump = UnitConv(E_dump).Wh_J(unit_in='J') / self.timestep

        return T_upper, T_lower, Q_dump

    def _overcooling(self, pre_T_min, T_upper, T_lower,
                     pre_T_amb, pre_T_feed, discharge=True):
        """Overcooling is an event when the
        resulting tank temperature is below the
        assumed minimum (smaller of the tank feed and
        the ambient temperature). It can occur if:

        * Heat loss and tap from the tank is too high,
          in which case we declare some unmet demand
          and limit the tank temperatures
        * The tank is slightly colder due to a lower
          ambient or water main temperature in the
          previous timesteps. This is allowed.

        Parameters:

            pre_T_min: float, K
                Minimum tank temperature limit

            T_upper: float, K
                Upper tank volume temperature

            T_lower: float, K
                Lower tank volume temperature

            pre_T_amb, pre_T_feed: floats, K
                Carried through for error handling

            discharge: boolean
                If true, resets any temperatures
                below the theoretical limit to that
                limit

        Returns:

            T_upper: float, K
                Updated upper tank volume temperature

            T_lower: float, K
                Updated lower tank volume temperature

            Q_overcool: float, W
                Error in balancing due to minimal tank
                temperature limit assumption for the
                timestep
        """
        # check the extent of 2nd law violation
        # and record it as an error in balancing
        dT_overcool = max((pre_T_min - T_upper),
                          (pre_T_min - T_lower))

        # How much of the assumed heat loss
        # did not occur
        # due to physical constraints
        E_overcool = (self.ro * self.shc *
                      (self.V_upper * max(0., (pre_T_min - T_upper)) +
                      self.V_lower * max(0., (pre_T_min - T_lower))))

        Q_overcool = UnitConv(E_overcool).Wh_J(unit_in='J') / self.timestep

        if discharge:
            # set the achieved tank temperature
            T_upper = max(pre_T_min, T_upper)
            T_lower = max(pre_T_min, T_lower)

        # if the tank is well sized for the load, the
        # allowed overcooling will be small, however
        # a fraction of a degree is likely to occur.
        # the warning is provided if the overcooling
        # temperature difference is unusually high
        if dT_overcool > self.dT_err:
            msg = 'Cooling off {} K below temperature'\
                  ' limit. This is balanced as:'\
                  ' a) allowed, since charging: {}, '\
                  ' b) declared unmet demand, since discharging: {};'\
                  ' Ambient T: {}, Feed T: {}.'
            log.warning(msg.format(
                round(dT_overcool,1),
                not discharge,
                discharge,
                pre_T_amb,
                pre_T_feed))

        return Q_overcool, T_upper, T_lower

    def thermal_tank(self, pre_T_amb=293.15, pre_T_feed=291.15,
                     pre_T_upper=328.15, pre_T_lower=323.15,
                     pre_V_tap=.00757, pre_Q_in=400.,
                     max_V_tap=0.1514):
        """Model of a thermal storage tank with:

        * Coil heat exchanger for the solar gains
        * DHW tap at the top of the tank
        * Recharge tap at the bottom of the tank

        The model can be instantiated as a:

        * Solar thermal tank
        * Heat pump tank

        Parameters:

            type: string
                * 'solar' - solar tank (assumes
                  that heated fluid from a solar collector is circulated
                  through an in-tank-coil)
                * 'hp' - heat pump tank (assumes an inbuilt heat pump
                  as a main heat source)

                The type will affect output labeling and heat transfer
                efficiency.


            pre_T_amb: float, K
                Ambient temperature

            pre_T_feed: float, K
                Temperature of the water
                that replenishes the tapped volume
                (e.g. water main temperature)

            pre_T_upper: float, K
                Upper tank volume temperature

            pre_T_lower: float, K
                Lower tank volume temperature

            pre_Q_in: float, W
                Heat gain passed to in-tank coil from solar collector
                or from a heat pump, depending on the type

            pre_V_tap: float, m3/h
                Volume of water tapped from the top of the tank

            max_V_tap: float, m3/h
                Annual peak flow

        Returns:

            res: dict
                Single timestep input and output values for temperatures [K]
                and heat rates [W]:

                >>> {net_gain_label : pre_Q_in_net,
                self.r['q_loss_low'] : pre_Q_loss_lower,
                self.r['q_loss_up'] : pre_Q_loss_upper,
                # demand, delivered and unmet heat
                # (between tap setpoint and water main)
                self.r['q_dem'] : tap['net_dem'],
                self.r['q_dem_tot'] : tap['tot_dem'],
                self.r['q_del_tank'] : tank[self.r['q_del_tank']],
                self.r['q_unmet_tank'] : np.round(
                tank[self.r['q_unmet_tank']] + tap['unmet_heat_rate'], 2),
                self.r['q_dump'] : tank[self.r['q_dump']],
                self.r['q_ovrcool_tank'] : tank[self.r['q_ovrcool_tank']],
                self.r['q_dem_balance'] : np.round(Q_dem_balance),
                # average temperatures for tank volumes
                self.r['t_tank_low'] : tank[self.r['t_tank_low']],
                self.r['t_tank_up'] : tank[self.r['t_tank_up']],
                self.r['dt_dist'] : dist['dt_dist'],
                self.r['t_set'] : self.T_draw_set,
                self.r['q_dist_loss'] : dist['heat_loss'],
                self.r['flow_on_frac'] : dist['flow_on_frac']}
                Temperatures in K, heat rates in W
        """
        # Heat loss from the upper tank volume
        pre_Q_loss_upper = self._thermal_loss(
            self.therm_transm_coef,
            self.A_upper,
            pre_T_amb,
            pre_T_upper)

        # Heat loss from the lower tank volume
        pre_Q_loss_lower = self._thermal_loss(
            self.therm_transm_coef,
            self.A_lower,
            pre_T_amb,
            pre_T_lower)

        # distribution system temperature drop and heat loss
        dist = self.distribution.pipe_losses(
            T_amb=pre_T_amb,
            T_in=pre_T_upper,
            V_tap=pre_V_tap,
            max_V_tap=max_V_tap)

        # Heat loss due to tapping water from
        # the upper tank volume and
        # replenishing it by water main. This
        # method also calculates any upfront unmet load
        # if the upper tank temperature is below the
        # dhw setpoint + the estimated distribution temperature drop
        tap = self.tap(
            pre_V_tap,
            pre_T_upper,
            pre_T_feed,
            dT_loss=dist['dt_dist'],
            T_draw_min=pre_T_feed + dist['dt_dist'])

        pre_Q_tap = tap['heat_rate']

        # Net heat gains to the tank
        if self.type == 'sol_tank':
            # assumes a simple coil efficiency multiplier
            pre_Q_in_net = pre_Q_in * self.coil_eff
            net_gain_label = self.r['q_del_sol']

        elif self.type == 'hp_tank':
            # empirical data used describes net gain from
            # a heat pump evaporator
            pre_Q_in_net = pre_Q_in * 1.
            net_gain_label = self.r['q_del_hp']

        # run a single timestep of tank behavior
        tank = self.thermal_tank_dynamics(
            pre_T_amb,
            pre_T_upper,
            pre_T_lower,
            pre_Q_in_net,
            pre_Q_loss_upper,
            pre_Q_loss_lower,
            pre_T_feed,
            tap['heat_rate'])

        if self.type == 'sol_tank':
            # Get the collector return temperature
            T_sol_col_return = tank[self.r['t_tank_low']] + self.dT_approach

        # check total demand balance (compare total heat
        # requirement needed to increase the water temperature of the
        # timestep's draw volume up to the setpoint temperature increased
        # in any distribution losses with the sum of heat delivered by the
        # tank, heat unmet due to finite tank volume and thermal losses,
        # and heat unmet due to the tank temperature at the upper tank volume)
        Q_del_and_unmet = (tank[self.r['q_del_tank']] +
                           tank[self.r['q_unmet_tank']] +
                           tap['unmet_heat_rate'])

        Q_dem_balance = tap['tot_dem'] - Q_del_and_unmet

        # Include all states
        res = {net_gain_label: pre_Q_in_net,
               self.r['q_loss_low']: pre_Q_loss_lower,
               self.r['q_loss_up']: pre_Q_loss_upper,
               # demand, delivered and unmet heat
               # (between tap setpoint and water main)
               self.r['q_dem']: tap['net_dem'],
               self.r['q_dem_tot']: tap['tot_dem'],
               self.r['q_del_tank']: tank[self.r['q_del_tank']],
               self.r['q_unmet_tank']: np.round(
                   tank[self.r['q_unmet_tank']] + tap['unmet_heat_rate'], 2),
               self.r['q_dump']: tank[self.r['q_dump']],
               self.r['q_ovrcool_tank']: tank[self.r['q_ovrcool_tank']],
               self.r['q_dem_balance']: np.round(Q_dem_balance),
               # average temperatures for tank volumes
               self.r['t_tank_low']: tank[self.r['t_tank_low']],
               self.r['t_tank_up']: tank[self.r['t_tank_up']],
               self.r['dt_dist']: dist['dt_dist'],
               self.r['t_set']: self.T_draw_set,
               self.r['q_dist_loss']: dist['heat_loss'],
               self.r['flow_on_frac']: dist['flow_on_frac']}

        if self.type == 'sol_tank':
           # to heat source (e.g. collector)
           res.update({self.r['t_coil_out'] : T_sol_col_return})

        return res


    def _tank_area(self, split_tank=True):
        """Calculates tank area associated with
        thermal losses using the tank volume and a regressed
        ratio between the tank height and its radius.
        If the tank is modeled as split into two volumes,
        it calculates lower and upper tank area based on the
        fraction of volume assigned to the upper volume.

        Parameters:

            split_tank: boolean
                If true, the method calculates the
                areas associated with the upper
                and lower tank volume. If false,
                it returns the area of the whole tank

        Returns:

            areas: float or dict
                Tank area. If split_tank, the area is
                split into two areas:

                * 'upper' : upper_area
                * 'lower' : lower_area

        Note: We disregard the difference between the
        internal and the external tank volume.
        """
        # radius and height based on their
        # ratio and tank volume
        rad = np.cbrt(self.size / (self.h_vs_r * np.pi))
        hei = rad * self.h_vs_r

        if split_tank:

            h_upper = self.vol_fra_upper * hei
            h_lower = hei - h_upper

            upper_area = rad ** 2 * np.pi + 2 * rad * np.pi * h_upper
            lower_area = rad ** 2 * np.pi + 2 * rad * np.pi * h_lower

            areas = {'upper': upper_area,
                     'lower': lower_area}

            return areas

        else:
            area = 2 * rad ** 2 * np.pi + 2 * rad * np.pi * hei

            return area


    def tap(self, V_draw_load, T_tank, T_feed,
            dT_loss=0., T_draw_min=None):
        """Calculates the water draw volume and
        heat content drawn from the top of an infinitely
        large adiabatic tank given the hot water demand,
        tank temperature and the water main temperature.

        It functions somewhat similarly to a
        thermostatic valve since it regulates the
        tap flow from the tank as follows:

            * Limits above if the tank temperature is
              higher than the nominal draw temperature

            * Tap flow equals V_draw_load for any tank
              temperature between T_draw_min
              and T_draw_nom

            * Tap flow is zero if tank temperature
              is below T_draw_min and T_draw_min is
              provided

        The results represent the theoretical limit
        for the draw. The tank model will check if the
        full amount can be delivered or only a
        part of the demand, due to the limited
        tank volume and thermal losses from the tank,
        and adjust the values.

        Parameters:

            V_draw_load: float, m3/h
                Volume of DHW drawn at the nominal
                end-use load temperature.

            T_tank: float, K
                Tank node temperature from which the
                DHW is being tapped (usually the
                upper volume)

            T_feed: float or array, K
                Temperature of water heater inlet water

            dT_loss: float, K
                Distribution loss temperature difference

            T_draw_min: float, K
                Minimal temperature that needs to
                be achieved in the tank in order
                to allow tapping.

                Default: None - tapping is always
                enabled

                Recommended usage - in colder climates
                where an outdoors tank may be cooler
                than the water main.

        Returns:

            draw: dict
                * Draw volume: 'vol', m3/h
                * Total demand heat rate: 'tot_dem', W
                * Infinite volume delivered heat rate: 'heat_rate', W
                * Infinite volume unmet heat rate: 'unmet_heat_rate', W
        """
        # Get nominal draw temperature
        T_draw_nom = self.T_draw_set

        # draw a volume with the same heat content as
        # the required load. Enthalpy balance,
        # assuming c and ro constant
        if T_tank > (T_draw_nom + dT_loss):
            V_tap = (V_draw_load *
                     (T_draw_nom + dT_loss - T_feed) / (T_tank - T_feed))

        # draw the demand volume if the tank temperature
        # is below or just at the nominal draw temperature
        elif T_tank <= (T_draw_nom + dT_loss):
            V_tap = V_draw_load

        else:
            msg = 'Not able to calculate V_tap based on: '\
                  'dT_loss = {}, T_tank = {}, T_draw_nom = {}'
            log.error(msg.format(dT_loss, T_tank, T_draw_nom))
            raise Exception

        if T_draw_min is not None:

            if T_tank <= T_draw_min:
                # do not draw
                V_tap = 0.

        Q_dem = (UnitConv(V_draw_load).m3perh_m3pers(unit_in='m3perh') *
                 self.ro * self.shc * (T_draw_nom - T_feed))

        Q_dem_with_dist_loss = (UnitConv(V_draw_load).m3perh_m3pers(
            unit_in='m3perh') * self.ro * self.shc *
            (T_draw_nom + dT_loss - T_feed))

        Q_tap = (UnitConv(V_tap).m3perh_m3pers(unit_in='m3perh') *
                 self.ro * self.shc * (T_tank - T_feed))

        # rounding
        try: # array
            Q_dem = Q_dem.round(2)
            Q_dem_with_dist_loss = Q_dem_with_dist_loss.round(2)
            Q_tap = Q_tap.round(2)
        except: # float
            Q_dem = round(Q_dem, 2)
            Q_dem_with_dist_loss = round(Q_dem_with_dist_loss, 2)
            Q_tap = round(Q_tap, 2)

        Q_unmet = Q_dem_with_dist_loss - Q_tap

        tap = {'vol': V_tap,
               'tot_dem': Q_dem_with_dist_loss,
               'net_dem': Q_dem,
               'heat_rate': Q_tap,
               'unmet_heat_rate': Q_unmet}

        return tap

    @staticmethod
    def _thermal_transmittance(insul_thickness=.04, spec_hea_cond=.04):
        """Returns the coefficient
        of thermal transmittance for the
        a unit of area of tank wall - U-value.

        CA Title 24 recommends at least R-12 (ft²·°F·h/Btu)
        for water heater storage tanks and backup tanks;

        Parameters:

            insul_thickness: float, m
                Insulation thickness
                Default: .04 m (1-2 inch gas,
                2-3 inch electric, :cite:`WH rule`)

            spec_hea_cond: float, W/mK
                Specific heat conductivity
                of the insulation
                Default: .04 W/mK (:cite:`ModelicaBuidlings`)

        Returns:

            therm_transm_coef: float, W/m2K
                Heat flow through a meter sqare of
                the tank wall for each kelvin
                of temperature difference
        """
        therm_transm_coef = spec_hea_cond/insul_thickness

        return therm_transm_coef  # W/m2K


    @staticmethod
    def _thermal_loss(therm_transm_coef, area, T_low, T_high):
        """Thermal loss to the environment through the
        tank walls

        Parameters:

            therm_transm_coef: float, W/m2K
                Heat flow through a meter sqare of
                the tank wall for each kelvin
                of temperature difference

            area: float, m2
                Wall area

            T_high: float, K
                Ambient air temperature

            T_low: float, K
                Tank node temperature

        Returns:

            Q_loss: float, W
                Heat loss rate
        """
        Q_loss = therm_transm_coef * area * (T_high - T_low)

        return Q_loss

    def volume_to_power(self, tank_volume):
        """Method to convert a gas water heater's volume input power
        based on a linear regression of Prospector data.
        Look in the X drive Data/Water Heaters/Regressions folder
        for the WaterHeater_ScrapeData_Python.xlsx file.
        Parameters:

            tank_volume: float or int
                Water heater tank volume [m3]

        Returns

            tank_input_power: float
                Water heater input (rated) power [W]
        """
        tank_input_power = (63560. * tank_volume) + 1777.9

        return tank_input_power

    def gas_tank_wh(self, V_draw, T_feed, T_amb=291.48):
        """Gas storage water heater model
        (`_gas_tank_wh`) wrapper.

        Parameters:

            V_draw: float or array like, m3/h
                Hourly water draw for a single timestep of
                an entire analysis period

            T_feed: float or array like, K
                Temperature of water heater inlet water for
                a single timestep of an entire analysis period

            T_amb: float or array like, K
                Temperature of space surrounding water heater
                Default: 65 degF

        Returns:

            res: dict
                * self.r['q_del'] : float, array - delivered heat rate, [W]
                * self.r['q_dem'] : float, array - demand heat rate, [W]
                * self.r['q_gas_use'] : float, array - gas use heat rate, [W]
                * self.r['q_unmet'] : float, array - unmet demand, [w]
                * self.r['q_dump'] : float, array - dumped heat, [W]

        Note:

            Assuming no electricity consumption in this version.

            Make sure to size the tank according to the recommended
            sizing rules, since the WHAM model does not apply to
            tanks that are not appropriately sized.
        """
        res = dict()

        Q_del, Q_gas_use = self._gas_tank_wh(
            Q_nom=self.Q_nom,
            V_draw=V_draw,
            tank_V=self.V,
            tank_A=self.A,
            tank_U=self.therm_transm_coef,
            tank_re=self.tank_re,
            T_set=self.T_draw_set,
            T_feed=T_feed,
            T_amb=T_amb,
            water_density=self.ro,
            water_specheat=self.shc)

        Q_dem = Q_del * 1.

        # return the heat rate of heat delivered and gas consumed
        res = {self.r['q_del']: Q_del,
               self.r['gas_use']: Q_gas_use,
               self.r['q_dem']: Q_dem}

        return res

    @staticmethod
    def _gas_tank_wh(Q_nom=8996., V_draw=0.01, tank_V=.11356,
                     tank_A=1.3522, tank_U=1., tank_re=0.78,
                     T_set=322.039, T_feed=291.15, T_amb=291.48,
                     water_density=998.2, water_specheat=4180.):
        """Implementation of the gas storage water heater
        based on the WHAM model (J. D. Lutz, C. Dunham Whitehead, A. Lekov,
        D. Winiarski, and G. Rosenquist, “WHAM: A Simplified Energy Consumption Equation for Water Heaters,” in 472246,
        1998, vol. 1, pp. 171–183.):

        Q_dot_cons [W] =
            = (V_dot_draw * rho * c * (T_draw,set - T_feed)) / n_re
            * (1-(U*A*(T_draw,set - T_amb))/P_rated)
            + U*A*(T_draw,set - T_amb)

        The model in the source cited calculates the total
        energy consumed during a day of water draw, whereas
        this model provides consumption rate in W

        Parameters:

            V_draw: float or array like, m3/h
                Water draw rate

            Q_nom: float, W
                Tank nominal power

            tank_V: float, m3
                Water tank volume

            tank_A: float, m2
                Surface area of water tank

            tank_U: float, W/m2K
                Thermal transmittance of water tank

            tank_re: float
                Water tank recovery efficiency
                Default: 0.78

            T_set: float or array, K
                Temperature setpoint of water heater
                Default: 120 degF

            T_feed: float or array, K
                Temperature of water heater inlet water
                Default: 64.4 degF

            T_amb: float, K
                Temperature of space surrounding water heater
                Default: 65 degF

            water_density: float, kg/m3
                Density of water
                Default: 998.2 kg/m3

            water_specheat: float, J/kgK
                Specific heat of water
                Default: 4180. J/kgK

        Returns:

            Q_del: float, array, W
                Delivered heat rate

            Q_gas_use: float or array, W
                Gas consumption rate

        Note:

            This model, as described in the literature,
            assumes realistic volume/input power
            ratios and will not perform as expected outside
            those.
        """
        dT = (T_set - T_feed)
        try: # array
            dT[dT < 0.] = 0.
        except: # float
            dT = max(dT, 0.)

        # heat delivered to user
        Q_del = (UnitConv(V_draw).m3perh_m3pers(unit_in='m3perh') *
                 water_density * water_specheat * dT)

        # energy content of the hot water drawn
        consumption_rate = Q_del / tank_re
        # to avoid double counting of the loss amount
        thermal_loss_adjustment = (
            1. - (tank_U * tank_A * (T_set - T_amb) / Q_nom))
        # thermal loss rate
        thermal_loss_rate = tank_U * tank_A * (T_set - T_amb)

        # Average timestep gas use rate in W
        Q_gas_use = (consumption_rate * thermal_loss_adjustment +
                     thermal_loss_rate)

        return Q_del, Q_gas_use

    def setup_electric(self):
        """
        Currently not implemented.
        """
        pass

    @staticmethod
    def _electric(cap, min_cap, charge, discharge,
                  pre_state_of_charge, eff_ch, eff_disch,
                  eff_sta, timestep=1.):
        """Simple electric storage model.

        Parameters:

            cap: float, Wh
                Maximum charge capacity

            min_cap: float, Wh
                Minimum charge capacity (not able to usefully
                discharge below this value)

            charge: float, W
                Timestep charge rate

            discharge: float, Wh
                Timestep discharge rate

            pre_state_of_charge: float, Wh
                State of charge in the previous timestep

            eff_ch: float
                Charging efficiency

            eff_disch: float
                Discharging efficiency

            eff_sta: float
                Stagnation efficiency

            timestep: float, h
                Default: 1.

        Returns:

            state_of_charge: Wh
                State of charge at this timestep

            unmet: float, Wh
                Unmet demand

            dumped: float, Wh
                Dumped demand
        """
        state_of_charge = (
            pre_state_of_charge * eff_sta +
            (charge * eff_ch - discharge / eff_disch) * timestep)

        # charged more than possible
        if state_of_charge > cap:
            dumped = state_of_charge - cap
            state_of_charge = cap
        else:
            unused = 0.

        # discharged more that possible
        if state_of_charge < min_cap:
            unmet = min_cap - state_of_charge
            state_of_charge = min_cap
        else:
            unmet = 0.

        return state_of_charge, unmet, dumped

    def electric_tank_wh(self):
        """
        Currently not implemented.
        """
        pass


class Distribution(object):
    """Describes performance of distribution system components.

    Parameters:
        sizes: pd df
            Pandas dataframe with component sizes, or 1.

        fluid_medium: string
            Default: 'water'. No other options implemented

        timestep: float, h
            Duration of a single timestep, in hours, defaults to 1.

        log_level: None or python logger logging level,
            Default: logging.DEBUG
            This applies for a subset of the class functionality, mostly
            used to deprecate logger messages for certain calculations.
            For Example: log_level = logging.ERROR will only throw error
            messages and ignore INFO, DEBUG and WARNING.

    Note:

        Each component is also implemented as a static method that
        can be used outside of this framework.

    Examples:

        See :func:`swh.system.tests.test_components <swh.system.tests.test_components>` module and
        for examples on how to use the methods.
    """
    def __init__(self, params=None, sizes=1., fluid_medium='water',
                 timestep=1., log_level=logging.DEBUG):

        # log level (e.g. only partial functionality of the class
        # is being used and one does not desire to see all infos)
        self.log_level = log_level
        logging.getLogger().setLevel(log_level)

        # extract labels
        self.s = SwhLabels().set_prod_labels()

        # fluid properties
        if fluid_medium == 'water':
            # Water properties, :cite:`ASHFund17` 33. table 2
            # density at 20 degC
            self.ro = 998.2  # kg/m3
            # specific heat content at 20 degC
            self.shc = 4180.  # J/(kgK)

        # extract component parameters
        if isinstance(params, pd.DataFrame):

            self.use_defaults = False

            # extract components and their performance parameters
            self.components = []

            # components are listed n the label map - extract each if
            # present in this list:
            components = params[self.s['comp']].unique().tolist()

            if self.s['sol_pump'] in components:

                self.components.append(self.s['sol_pump'])

                self.params_sol_pump = dict()

                self.params_sol_pump[self.s['eta_sol_pump']] = params.loc[
                    params[self.s['param']] == self.s['eta_sol_pump'],
                    self.s['param_value']].values[0]

            if self.s['dist_pump'] in components:
                self.components.append(self.s['dist_pump'])

                self.params_dist_pump = dict()

                self.params_dist_pump[self.s['eta_dist_pump']] = params.loc[
                    params[self.s['param']] == self.s['eta_dist_pump'],
                    self.s['param_value']].values[0]

            if self.s['piping'] in components:
                self.components.append(self.s['piping'])

                self.params_piping = dict()

                self.params_piping[self.s['pipe_spec_hea_con']] =\
                    params.loc[params[self.s['param']] == self.s['pipe_spec_hea_con'],
                               self.s['param_value']].values[0]

                self.params_piping[self.s['pipe_ins_thick']] = params.loc[
                    params[self.s['param']] == self.s['pipe_ins_thick'],
                    self.s['param_value']].values[0]

                self.params_piping[self.s['dia_len_exp']] = params.loc[
                    params[self.s['param']] == self.s['dia_len_exp'],
                    self.s['param_value']].values[0]

                self.params_piping[self.s['dia_len_sca']] = params.loc[
                    params[self.s['param']] == self.s['dia_len_sca'],
                    self.s['param_value']].values[0]

                self.params_piping[self.s['discr_diam_m']] = \
                    eval(np.array(params.loc[
                    params[self.s['param']] == self.s['discr_diam_m'],
                    self.s['param_value']])[0])

                self.params_piping[self.s['flow_factor']] = \
                    params.loc[params[self.s['param']] == self.s['flow_factor'],
                               self.s['param_value']].values[0]

                self.params_piping[self.s['circ']] = \
                    params.loc[
                        params[self.s['param']] == self.s['circ'],
                        self.s['param_value']].values[0]

                self.params_piping[self.s['long_br_len_fr']] = \
                    params.loc[
                        params[self.s['param']] == self.s['long_br_len_fr'],
                        self.s['param_value']].values[0]

        elif not isinstance(params, pd.DataFrame):
            self.use_defaults = True

        self.timestep = timestep

        # extract component size/capacity (see setter for details)
        self.size = sizes

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        """Extracts sizes from a dataframe
        """
        set_sizes = dict()

        if not isinstance(value, pd.DataFrame):
            # assign unit size, please see individual
            # methods for any modifications
            set_sizes = 1.

        elif isinstance(value, pd.DataFrame):

            if self.s['sol_pump'] in self.components:
                set_sizes[self.s['sol_pump']] = \
                value.loc[value[self.s['comp']] == self.s['sol_pump'],
                          self.s['cap']].values[0]

            if self.s['dist_pump'] in self.components:
                set_sizes[self.s['dist_pump']] = \
                value.loc[value[self.s['comp']] == self.s['dist_pump'],
                          self.s['cap']].values[0]

            if self.s['piping'] in self.components:
                set_sizes[self.s['piping']] = \
                value.loc[value[self.s['comp']] == self.s['piping'],
                          self.s['cap']].values[0]

        else:
            msg = 'Provided sizes format is not supported.'
            log.error(msg)
            raise Exception

        self.__size = set_sizes

    def pump(self, on_array=np.ones(8760), role='solar'):
        """Solar and distribution pump energy use.
        Assumes a fixed speed pump.

        Parameters:

            on_array: array
                Pump on/off status for the chosen number of discrete
                timesteps
                Default: np.ones(8760) - on for a year in hourly timesteps.

            role: string
                'solar' : primary (solar collector) loop
                'distribution' : secondary (distribution) loop

        Returns:

            en_use: float or array like
        """
        if role == 'solar':
            role_label = self.s['sol_pump']
        elif role == 'distribution':
            role_label = self.s['dist_pump']

        try:
            P_nom = self.size[role_label]
        except:
            P_nom = 1.

            msg = 'Could not extract ' + role + ' pump size. '\
                  'Setting it to {}.'
            log.info(msg.format(P_nom))

        if self.use_defaults:
            msg = role.capitalize() + \
                  ' pump parameters have not been passed to the'\
                  ' component model. Using defaults.'
            log.info(msg)

            en_use = self._pump(
                P_nom=P_nom,
                on_array=on_array,
                timestep=self.timestep)

        elif role == 'solar':
            en_use = self._pump(
                P_nom=P_nom,
                eta_nom=self.params_sol_pump[self.s['eta_sol_pump']],
                on_array=on_array,
                timestep=self.timestep)

        elif role == 'distribution':
            en_use = self._pump(
                P_nom=P_nom,
                eta_nom=self.params_dist_pump[self.s['eta_dist_pump']],
                on_array=on_array,
                timestep=self.timestep)

        return en_use

    @staticmethod
    def _pump(P_nom=45., eta_nom=0.7, control='fixed_speed',
              on_array=np.ones(8760), timestep=1.):
        """Calculates pump energy use during the operating time.

        Parameters:

            P_nom: float
                Nominal pump power, W

            eta_nom: float
                Nominal pump efficiency

            on_array: array
                Pump on/off status for the chosen number of discrete
                timesteps. Each value should belong to interval [0, 1].
                For example, 0.5 means that the pump was on for half of
                the timestep.
                Default: np.ones(8760) - on all the time.

            control: string, options: 'fixed_speed'
                Pump control type
                Default: 'fixed_speed' - Part load ratio equals 1
                for all operating hours

            timestep: float, h
                Duration of a single timestep in hours

        Returns:

            el_use: array, Wh
                Energy use for each timestep

            el_use_total: float, Wh
                Energy use for the duration of the operating time
        """
        if control == 'fixed_speed':
            el_use = P_nom * on_array / eta_nom

        el_use_total = el_use.sum() * timestep

        return el_use, el_use_total

    @staticmethod
    def _dc_to_ac(in_power, conv_eff=0.8):
        """Models the performance of the
        DC - AC conversion, including
        inverter, cable and any other
        conversion related losses.

        Parameters:

            in_power: float
                Input power of DC electricity [W, kW]

            conv_eff: float
                Total efficiency of the dc-ac conversion
                Default: 0.8

        Returns:

            out_power: float
                Output power of AC electricity [W, kW]
        """

        # Calculate the output power
        out_power = conv_eff * in_power

        return out_power


    def pipe_losses(self, T_in=333.15, T_amb=293.15,
                    V_tap=.05, max_V_tap=0.1514):
        """Thermal losses from distribution pipes.

        Parameters:

            T_in: float, K
                Hot water temperature at distribution pipe inlet

            T_amb: float, K
                Ambient temperature

            V_tap: float, m3/h
                Timestep draw volume

            max_V_tap: float, m3/h
                Maximum draw volume, m3/h (design variable)

        Returns:

            res: dict
                ['heat_rate']: Loss heat rate, W
        """

        if not self.use_defaults:

            diameter = (self.params_piping[self.s['dia_len_sca']] *
                        self.size[self.s['piping']] **
                        self.params_piping[self.s['dia_len_exp']])

            discrete_diameters_m = (
                self.params_piping[self.s['discr_diam_m']])

            diameter = self._pick_first_larger_size(
                diameter,
                discrete_diameters_m,
                limits=True)

            loss_heat_rate, heat_loss, dT_drop, flow_on_timestep_fraction =\
                self._pipe_losses(
                    T_in=T_in,
                    T_amb=T_amb,
                    length=self.size[self.s['piping']],
                    diameter=diameter,
                    insul_thickness=self.params_piping[self.s['pipe_ins_thick']],
                    spec_hea_cond=self.params_piping[self.s['pipe_spec_hea_con']],
                    V_tap=V_tap,
                    max_V_tap=max_V_tap,
                    flow_factor=self.params_piping[self.s['flow_factor']],
                    circulation=self.params_piping[self.s['circ']],
                    longest_branch_length_ratio=self.params_piping[self.s['long_br_len_fr']])

        else:
            loss_heat_rate, heat_loss, dT_drop, flow_on_timestep_fraction =\
                self._pipe_losses(T_in=T_in, T_amb=T_amb)

        res = dict()
        res['heat_rate'] = loss_heat_rate
        res['dt_dist'] = dT_drop
        res['heat_loss'] = heat_loss
        res['flow_on_frac'] = flow_on_timestep_fraction

        return res

    def _pipe_losses(self, T_in=333.15, T_amb=293.15, length=20.,
                     diameter=0.0381, insul_thickness=.008,
                     spec_hea_cond=.0175, V_tap=.00757,
                     max_V_tap=0.1514, flow_factor=0.5,
                     circulation=False,
                     longest_branch_length_ratio=None):
        """For the distribution piping network estimates:
        * heat loss rate
        * timestep heat loss
        * pipe temperature drop assuming flow through the
          full provided pipe length

        Parameters:

            T_in: float
                Pipe inlet tempearture, K

            T_amb: float
                Pipe outlet temperature, K

            length: float
                Pipe length, m

            diameter: float
                Pipe diameter, m

            insul_thickness: float, m
                Insulation thickness
                Default: .008 m

            spec_hea_cond: float, W/mK
                Specific heat conductivity of the insulation
                Default: .0175 W/mK

            V_tap: float, m3/h
                Timestep draw volume

            max_V_tap: float, m3/h
                Maximum draw volume, m3/h (design variable)

            flow_factor: float
                Multiplier to account for:

                    * Intial peak sizing. If equal 1. the pipe is sized such
                      that maximum hourly flow in a representative year equals
                      pipe design flow. Values < 1. represent oversizing.

                    * For large distribution networks a higher
                      flow_factor can be used to account for
                      any heated volume that remains stagnant in the
                      pipe after a draw

            longest_branch_length_ratio: float or None
                If the network has a number of paralel branches rather than
                one main pipe or a circulaton pipe, provide the ratio between
                the length of the longest pipe and the total pipe length. It
                gets used in the average pipe temperature and temperature
                drop estimation.
                Default: None (equivalent to 1.)

            circulation: boolean
                True: has circulation

        Returns:

            loss_heat_rate: float, W
                Heat loss rate from the pipe

            heat_loss: float, Wh
                Heat lost from the pipe for the
                duration of a single timestep

            dT_drop: float, K
                Estimated temperature drop through the
                entire length of the pipe
        """
        if length > 0.:
            U_value = spec_hea_cond / insul_thickness

            # fraction of timestep during which the flow was on
            if int(circulation) > 0.:
                flow_on_timestep_fraction = 1.
                # assuming constant nominal speed circulation
                V_tap = max_V_tap / flow_factor
            else:
                # at some constant nominal pump speed only the tapped
                # volume of water is assumed to flow through the pipe,
                # which lasts for a fraction of the timestep:
                flow_on_timestep_fraction = (
                    V_tap * flow_factor / max_V_tap)

            if V_tap > 0.:
                # effective flowrate [in m3/s] to calculate average pipe
                # temperature and temperature drop
                V_eff = (V_tap / flow_on_timestep_fraction) / 3600.
                # the same as
                # V_eff = (max_V_tap/flow_factor)/3600.

                # area
                if longest_branch_length_ratio is not None:
                    length_eff = longest_branch_length_ratio * length
                else:
                    length_eff = length * 1.

                area_for_t_avg = (
                    diameter + 2 * insul_thickness) * np.pi * length_eff

                # average pipe temperature
                # derived using equations from
                # Incropera/DeWitt/Bergman/Lavine:
                # Fundamentals of Heat and Mass Transfer
                k = U_value * area_for_t_avg / (self.ro * V_eff * self.shc)

                T_avg = (T_in - T_amb) * ((1. - np.exp(-k)) / k) + T_amb

                loss_heat_rate = self._pipe_loss_rate(
                    T_avg=T_avg,
                    T_amb=T_amb,
                    length=length,
                    diameter=diameter,
                    U_value=U_value)

                # estimated temperature drop in the distribution system
                if V_tap != 0.:
                    dT_drop = (loss_heat_rate * (length_eff / length) /
                               (self.ro * V_eff * self.shc))
                else:
                    dT_drop = 0.

                # Heat loss in Wh during the timestep [h]
                heat_loss = (loss_heat_rate * self.timestep *
                             flow_on_timestep_fraction)

            else:
                loss_heat_rate = 0.
                heat_loss = 0.
                dT_drop = 0.
                flow_on_timestep_fraction = 0.

        else:
            loss_heat_rate = 0.
            heat_loss = 0.
            dT_drop = 0.
            flow_on_timestep_fraction = 0.

        return loss_heat_rate, heat_loss, dT_drop, flow_on_timestep_fraction

    @staticmethod
    def _pipe_loss_rate(T_avg=333.15, T_amb=293.15, length=20.,
                        diameter=0.0381, U_value=2.1875,
                        insul_thickness=.008):
        """Thermal losses from distribution pipes.
        Approximates the thermal loss as the product of U-value,
        total pipe area and the difference between
        average pipe and the ambient temperatures.

        Parameters:

            T_avg: float, K
                Average hot water distribution pipe temperature.

                To estimate losses without any flow information one
                could, given one knows the tank outlet (pipe inlet)
                temperature, pass pipe inlet temperature instead of pipe
                average temperature, which would yield losses slightly
                higher than actual, but may be a useful conservative
                first approximation.

            T_amb: float, K
                Ambient temperature

            length: float, m
                Total length of pipes

            diameter: float, m
                Pipe diameter

            U_value: float, W/m2K
                U value of the pipe (coefficient of thermal transmittance)

            insul_thickness: float, m
                Insulation thickness
                Default: .008 m

        Returns:

            loss_heat_rate: float, W
                Thermal loss rate from the pipes
        """
        # pipe area
        area = (diameter + 2 * insul_thickness) * np.pi * length

        # pipe heat loss rate
        loss_heat_rate = area * U_value * (T_avg - T_amb)

        return loss_heat_rate

    @staticmethod
    def _pick_first_larger_size(theor_size, discrete_sizes, limits=True):
        """Extracts the smallest discrete size larger than the
        theoretically required size.

        Parameters:

            theor_size: float, list
                Theoretically required component size (defined e.g. using
                a rule of a thumb, a fit, or based on the load
                characteristics)

            discrete_sizes: numpy array
                An array of market available component sizes

            limits: boolean
                If theor_size less than min or larger than max, pick
                the limit

        Returns:

            result: float
                First larger market available size
        """
        if type(discrete_sizes) == list:
            discrete_sizes = np.array(discrete_sizes)

        if theor_size > discrete_sizes.max():
            result =  discrete_sizes.max()
        else:
            result = discrete_sizes[theor_size <= discrete_sizes].min()

        return result
