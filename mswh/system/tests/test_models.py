import datetime
import logging
import os
import pickle
import unittest


import numpy as np
import pandas as pd

from mswh.system.components import Converter, Storage
from mswh.system.source_and_sink import SourceAndSink
from mswh.system.models import System
from mswh.system.source_and_sink import SourceAndSink

from mswh.tools.unit_converters import UnitConv, Utility
from mswh.comm.sql import Sql

from mswh.comm.label_map import SwhLabels
from mswh.tools.plots import Plot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SystemTests(unittest.TestCase):
    """Unit tests for the project level
    system models.
    """
    @classmethod
    def setUpClass(self):
        """Assigns values to test variables.
        """
        random_state = np.random.RandomState(123)

        self.plot_results = True
        # it will save under img on the test directory
        self.outpath = os.path.dirname(__file__)

        # get labels
        self.c = SwhLabels().set_hous_labels()
        self.s = SwhLabels().set_prod_labels()
        self.r = SwhLabels().set_res_labels()

        # generate weather data and annual hourly
        # water draw profile

        weather_db_path = os.path.join(
            os.getcwd(), 'mswh/comm/mswh_system_input.db')

        db = Sql(weather_db_path)

        try:
            # read table names for all tables in a
            # {table name : sheet name} form
            inputs = db.tables2dict(close=True)
        except:
            msg = 'Failed to read input tables from {}.'
            log.error(msg.format(inpath))

        source_and_sink = SourceAndSink(
            input_dfs=inputs)

        # SF climate is 03, 16 is cold
        self.weather = source_and_sink.irradiation_and_water_main(
            '03',
            method='isotropic diffuse')

        # community scale household occupancies for 4 households
        occ_com = [4, 4, 3, 5]
        # individual scale household occupancy
        occ_ind = [4]

        # are people at home during the day in any of the households:
        # 'y' or 'n'
        at_home_com = ['n', 'n', 'n', 'n']
        at_home_ind = ['n']

        loads_com, peakload_com = SourceAndSink._make_example_loading_inputs(
            inputs,
            self.c,
            random_state,
            occupancy=occ_com,
            at_home=at_home_com)

        loads_indiv, peakload_indiv = SourceAndSink._make_example_loading_inputs(
            inputs,
            self.c,
            random_state,
            occupancy=occ_ind,
            at_home=at_home_ind)

        # scaled loads to match 300 L/day
        load_array_val = (
            loads_indiv['End-Use Load'][0] *
            (300 * 365 * .001) /
            loads_indiv['End-Use Load'][0].sum())

        loads_indiv_val = pd.DataFrame(
            data=[[1, occ_ind[0], load_array_val]],
            columns=[self.c['id'], self.c['occ'], self.c['load_m3']])

        # performance parameters

        # solar thermal
        sol_the_sys_params = pd.DataFrame(
            data=[[self.s['the_sto'], self.s['f_upper_vol'], .5],
                  [self.s['the_sto'], self.s['ins_thi'], .085],
                  [self.s['the_sto'], self.s['spec_hea_con'], .04],
                  [self.s['the_sto'], self.s['t_tap_set'], 322.04],
                  [self.s['the_sto'], self.s['h_vs_r'], 6.],
                  [self.s['the_sto'], self.s['dt_appr'], 2.],
                  [self.s['the_sto'], self.s['t_max_tank'], 344.15],
                  [self.s['the_sto'], self.s['eta_coil'], .84],
                  [self.s['the_sto'], self.s['circ'], 0.],
                  [self.s['sol_col'], self.s['interc_hwb'], .753],
                  [self.s['sol_col'], self.s['slope_hwb'], -4.025],
                  [self.s['sol_pump'], self.s['eta_sol_pump'], .85],
                  [self.s['piping'], self.s['pipe_spec_hea_con'], .0175],
                  [self.s['piping'], self.s['pipe_ins_thick'], .008],
                  [self.s['piping'], self.s['flow_factor'], .8],
                  [self.s['piping'], self.s['dia_len_exp'],
                   0.43082708345352605],
                  [self.s['piping'], self.s['dia_len_sca'],
                   0.007911283766743384],
                  [self.s['piping'], self.s['discr_diam_m'],
                  '[0.0127, 0.01905, 0.0254, 0.03175, 0.0381,'\
                   '0.0508, 0.0635, 0.0762, 0.1016]'],
                  [self.s['piping'], self.s['circ'], False],
                  [self.s['piping'], self.s['long_br_len_fr'], 1.],
                  [self.s['dist_pump'], self.s['eta_dist_pump'], .85]],
            columns=[self.s['comp'], self.s['param'], self.s['param_value']])

        last_row_for_indiv = (
            sol_the_sys_params.shape[0] - 1 -
            sol_the_sys_params.loc[
                sol_the_sys_params[
                self.s['comp']] == self.s['dist_pump'], :].shape[0])

        # conventional gas tank wh
        # ~R2.1, EL 1 from the rulemaking analysis
        gas_tank_wh_params = pd.DataFrame(
            data=[[self.s['gas_tank'], self.s['tank_re'], .78],
                  [self.s['gas_tank'], self.s['ins_thi'], .03],
                  [self.s['gas_tank'], self.s['spec_hea_con'], .081],
                  [self.s['gas_tank'], self.s['t_tap_set'], 322.04]],
            columns=[self.s['comp'], self.s['param'], self.s['param_value']])

        # gas tankless backup
        sol_the_inst_gas_bckp_params = pd.DataFrame(
            data=[[self.s['gas_burn'], self.s['comb_eff'], .85]],
            columns=[self.s['comp'], self.s['param'], self.s['param_value']])

        # sizing

        # assume 4 occupants
        # basecase gas tank WH: DOE sizing rule based on
        # peak hourly demand +/-2 gal, assuming +/- 0
        gas_tank_size_indiv = UnitConv(
            peakload_indiv.loc[0, self.c['max_load']]).m3_gal(
                unit_in='gal')

        gas_tank_wh_size = pd.DataFrame(
            data=[[self.s['gas_tank'], gas_tank_size_indiv]],
            columns=[self.s['comp'], self.s['cap']])

        # individual scale retrofit backup
        sol_the_gas_tank_bckp_size = pd.DataFrame(
            data=[[1, self.s['gas_tank'], gas_tank_size_indiv]],
            columns=[self.c['id'], self.s['comp'], self.s['cap']])

        # CSI sizing rules
        def demand_estimate(occ):
            if occ == 1:
                return 20.
            if occ == 2:
                return 35.
            else:
                return 35. + 10. * (occ - 2.)

        peakload_com[self.c['dem_estimate']] = \
            loads_com[self.c['occ']].apply(lambda x: demand_estimate(x))

        demand_estimate_ind = demand_estimate(occ_ind[0])

        demand_estimate_com = \
            peakload_com[self.c['dem_estimate']].sum()

        col_area_scaler = 1.2  # (CSI sizing rule: upper limit 1.25)
        tank_vol_scaler = 1.3  # (CSI sizing rule: lower limit 1.25)

        col_area_ind_sqft = demand_estimate_ind * col_area_scaler
        col_area_com_sqft = demand_estimate_com * col_area_scaler

        tank_vol_ind_gal = col_area_ind_sqft * tank_vol_scaler
        tank_vol_com_gal = col_area_com_sqft * tank_vol_scaler

        col_area_ind = UnitConv(col_area_ind_sqft).sqft_m2()
        col_area_com = UnitConv(col_area_com_sqft).sqft_m2()

        tank_vol_ind = UnitConv(tank_vol_ind_gal).m3_gal(
            unit_in='gal')
        tank_vol_com = UnitConv(tank_vol_com_gal).m3_gal(
            unit_in='gal')

        # piping
        pipe_m_per_hhld = 3.048
        detached_k = 6.
        attached_k = 3.

        # distribution pump
        dist_pump_size = 10.4376 * len(occ_com) ** 0.9277

        # solar pump
        com_solar_pump_size = 7.5101 * sum(occ_com) ** 0.5322
        indiv_solar_pump_size = 7.5101 * sum(occ_ind) ** 0.5322

        # individual
        sol_the_sys_sizes_indiv = pd.DataFrame(
            data=[[self.s['sol_col'], col_area_ind],
                  [self.s['the_sto'], tank_vol_ind],
                  [self.s['sol_pump'], indiv_solar_pump_size],
                  [self.s['piping'], pipe_m_per_hhld]],
            columns=[self.s['comp'], self.s['cap']])

        sol_the_inst_gas_bckp_size = pd.DataFrame(
            data=[[1, self.s['gas_burn'], 50972]],
            columns=[self.c['id'], self.s['comp'], self.s['cap']])

        # piping for single family attached
        sol_the_sys_sizes_com = pd.DataFrame(
            data=[[self.s['sol_col'], col_area_com],
                  [self.s['the_sto'], tank_vol_com],
                  [self.s['sol_pump'], com_solar_pump_size],
                  [self.s['dist_pump'], dist_pump_size],
                  [self.s['piping'],
                  attached_k * pipe_m_per_hhld * len(occ_com)]],
            columns=[self.s['comp'], self.s['cap']])

        # gas tank backup
        sol_the_gas_tank_bckp_params = gas_tank_wh_params.copy()

        peakload_com['gas_tank_size_com'] = peakload_com[
            self.c['max_load']].apply(
                lambda x: UnitConv(x).m3_gal(unit_in='gal'))

        peakload_com.index = peakload_com[self.c['id']]

        sol_the_gas_tank_bckp_sizes_com = pd.DataFrame(
            columns=[self.c['id'], self.s['comp'], self.s['cap']],
            index=peakload_com.index)

        for i in peakload_com.index:
            sol_the_gas_tank_bckp_sizes_com.loc[i, self.c['id']] = i
            sol_the_gas_tank_bckp_sizes_com.loc[
                i, self.s['comp']] = self.s['gas_tank']
            sol_the_gas_tank_bckp_sizes_com.loc[i, self.s['cap']] =\
                peakload_com.loc[i, 'gas_tank_size_com']

        sol_the_gas_tank_bckp_sizes_com.index = \
            range(sol_the_gas_tank_bckp_sizes_com.shape[0])

        sol_the_inst_gas_bckp_sizes_com = pd.DataFrame(
            columns=[self.c['id'],  self.s['comp'],  self.s['cap']],
            index=peakload_com.index)

        def gas_tankles_size_W(occupancy):
            size = 24875. * occupancy ** 0.5175
            return size

        for i in peakload_com.index:
            sol_the_inst_gas_bckp_sizes_com.loc[i,  self.c['id']] = i
            sol_the_inst_gas_bckp_sizes_com.loc[
                i,  self.s['comp']] = self.s['gas_burn']
            sol_the_inst_gas_bckp_sizes_com.loc[i,  self.s['cap']] = \
                gas_tankles_size_W(occ_com[i - 1])

        sol_the_inst_gas_bckp_sizes_com.index =\
            range(sol_the_inst_gas_bckp_sizes_com.shape[0])

        # instantiate systems

        # individual system
        self.sol_wh_indiv_new = System(
            sys_params=sol_the_sys_params.loc[:last_row_for_indiv, :],
            backup_params=sol_the_inst_gas_bckp_params,
            sys_sizes=sol_the_sys_sizes_indiv,
            backup_sizes=sol_the_inst_gas_bckp_size,
            weather=self.weather,
            loads=loads_indiv)

        msg = 'Set up the individual solar thermal system with tankless '\
              'backup test case.'
        log.info(msg)

        self.sol_wh_indiv_retr = System(
            sys_params=sol_the_sys_params.loc[:last_row_for_indiv, :],
            backup_params=sol_the_gas_tank_bckp_params,
            sys_sizes=sol_the_sys_sizes_indiv,
            backup_sizes=sol_the_gas_tank_bckp_size,
            weather=self.weather,
            loads=loads_indiv)

        msg = 'Set up the individual solar thermal system with gas tank '\
              'backup test case.'
        log.info(msg)

        # community system
        self.sol_wh_com_new = System(
            sys_params=sol_the_sys_params,
            backup_params=sol_the_inst_gas_bckp_params,
            sys_sizes=sol_the_sys_sizes_com,
            backup_sizes=sol_the_inst_gas_bckp_sizes_com,
            weather=self.weather,
            loads=loads_com)

        msg = 'Set up the community solar thermal system with tankless '\
              'backup test case.'
        log.info(msg)

        self.sol_wh_com_retr = System(
            sys_params=sol_the_sys_params,
            backup_params=sol_the_gas_tank_bckp_params,
            sys_sizes=sol_the_sys_sizes_com,
            backup_sizes=sol_the_gas_tank_bckp_sizes_com,
            weather=self.weather,
            loads=loads_com)

        msg = 'Set up the community solar thermal system with gas tank '\
              'backup test case.'
        log.info(msg)

        # solar thermal validation

        # individual new with
        # tank and collector size from
        # https://secure.solar-rating.org/Certification/Ratings/#
        # RatingsReport.aspx?device=6926&units=METRICS
        # solar thermal retrofit solar fractions in the rating sheets are low
        # - for the same
        # size of collector and storage the new and retrofit should have the
        # same solar fraction
        # by definition https://en.wikipedia.org/wiki/Solar_savings_fraction

        # sizes based on several observed rated systems from OG-300
        # with an 80 gal tank and gas tankless backup
        sol_the_sys_sizes_val = pd.DataFrame(
            data=[[self.s['sol_col'], 3.9],
                  [self.s['the_sto'], UnitConv(80.).m3_gal(unit_in='gal')],
                  [self.s['sol_pump'], indiv_solar_pump_size],
                  [self.s['piping'], 0.]],
            columns=[self.s['comp'], self.s['cap']])

        self.val_sol_wh = System(
            sys_params=sol_the_sys_params.loc[:last_row_for_indiv, :],
            backup_params=sol_the_inst_gas_bckp_params,
            sys_sizes=sol_the_sys_sizes_val,
            backup_sizes=sol_the_inst_gas_bckp_size,
            weather=self.weather,
            loads=loads_indiv_val)

        msg = 'Set up the individual solar thermal system validation '\
            'test case.'
        log.info(msg)

        self.conv_wh = System(
            sys_params=gas_tank_wh_params,
            sys_sizes=gas_tank_wh_size,
            weather=self.weather,
            loads=loads_indiv)

        msg = 'Set up the conventional tank wh test case.'
        log.info(msg)

        # With baseline tank with a slightly higher RE and insulation set to
        # R12, as used for the solar tank
        gas_tank_wh_params_val = pd.DataFrame(
            data=[[self.s['gas_tank'], self.s['tank_re'], .82, '-'],
                  [self.s['gas_tank'], self.s['ins_thi'], .04, 'm'],
                  [self.s['gas_tank'], self.s['spec_hea_con'], .085, 'W/mK'],
                  [self.s['gas_tank'], self.s['t_tap_set'], 322.04, 'K']],
            columns=[self.s['comp'], self.s['param'],
                     self.s['param_value'], self.s['param_unit']])

        # with validation loads and validation parameters
        self.conv_wh_val = System(
            sys_params=gas_tank_wh_params_val,
            sys_sizes=gas_tank_wh_size,
            weather=self.weather,
            loads=loads_indiv_val)

        msg = 'Set up the conventional tank wh validation test case.'
        log.info(msg)

        # project level component parameter
        # dataframe for solar electric system
        # with an inst. gas backup
        sol_el_tank_params = pd.DataFrame(
            data=[[self.s['hp'], self.s['c1_cop'], 1.229E+00],
                  [self.s['hp'], self.s['c2_cop'], 5.549E-02],
                  [self.s['hp'], self.s['c3_cop'], 1.139E-04],
                  [self.s['hp'], self.s['c4_cop'], -1.128E-02],
                  [self.s['hp'], self.s['c5_cop'], -3.570E-06],
                  [self.s['hp'], self.s['c6_cop'], -7.234E-04],
                  [self.s['hp'], self.s['c1_heat_cap'], 7.055E-01],
                  [self.s['hp'], self.s['c2_heat_cap'], 3.945E-02],
                  [self.s['hp'], self.s['c3_heat_cap'], 1.433E-04],
                  [self.s['hp'], self.s['c4_heat_cap'], 2.768E-03],
                  [self.s['hp'], self.s['c5_heat_cap'], -1.069E-04],
                  [self.s['hp'], self.s['c6_heat_cap'], -2.494E-04],
                  [self.s['hp'], self.s['heat_cap_rated'], 2350.],
                  [self.s['hp'], self.s['cop_rated'], 2.43],
                  [self.s['pv'], self.s['eta_pv'], .16],
                  [self.s['pv'], self.s['f_act'], 1.],
                  [self.s['pv'], self.s['irrad_ref'], 1000.],
                  [self.s['inv'], self.s['eta_dc_ac'], .85],
                  [self.s['the_sto'], self.s['f_upper_vol'], .5],
                  [self.s['the_sto'], self.s['ins_thi'], .04],
                  [self.s['the_sto'], self.s['spec_hea_con'], .04],
                  [self.s['the_sto'], self.s['t_tap_set'], 322.04],
                  [self.s['the_sto'], self.s['h_vs_r'], 6.],
                  [self.s['the_sto'], self.s['dt_appr'], 2.],
                  [self.s['the_sto'], self.s['t_max_tank'], 344.15],
                  [self.s['piping'], self.s['pipe_spec_hea_con'], .0175],
                  [self.s['piping'], self.s['pipe_ins_thick'], .008],
                  [self.s['piping'], self.s['flow_factor'], .8],
                  [self.s['piping'], self.s['dia_len_exp'],
                   .43082708345352605],
                  [self.s['piping'], self.s['dia_len_sca'],
                   .007911283766743384],
                  [self.s['piping'], self.s['discr_diam_m'],
                  '[0.0127, 0.01905, 0.0254, 0.03175, 0.0381,'\
                   '0.0508, 0.0635, 0.0762, 0.1016]'],
                  [self.s['piping'], self.s['circ'], False],
                  [self.s['piping'], self.s['long_br_len_fr'], 1.]],
            columns=[self.s['comp'], self.s['param'], self.s['param_value']])

        # test sizing
        sol_el_tank_sizes_indiv = pd.DataFrame(
            data=[[self.s['hp'], 2350.],
                  [self.s['pv'], 6.25],
                  [self.s['the_sto'], UnitConv(80).m3_gal()],
                  [self.s['dist_pump'], dist_pump_size],
                  [self.s['piping'], pipe_m_per_hhld]],
            columns=[self.s['comp'], self.s['cap']])

        # electric resistance backup parameters
        sol_el_tank_inst_gas_bckp_params = pd.DataFrame(
            data=[[self.s['el_res'], self.s['eta_el_res'], 1.0]],
            columns=[self.s['comp'], self.s['param'], self.s['param_value']])

        # electric resistance backup size
        sol_el_tank_inst_el_res_bckp_size = pd.DataFrame(
            data=[[1, self.s['el_res'], 6500.]],
            columns=[self.c['id'], self.s['comp'], self.s['cap']])

        self.hp_wh = System(
            sys_params=sol_el_tank_params,
            backup_params=sol_el_tank_inst_gas_bckp_params,
            sys_sizes=sol_el_tank_sizes_indiv,
            backup_sizes=sol_el_tank_inst_el_res_bckp_size,
            weather=self.weather,
            loads=loads_indiv)

    def test_solar_thermal_individual_new(self):
        """Test solar thermal project level model with a
        tankless backup heater
        """

        # Default parameters, sizing and load for a 4 person
        # household.
        cons_total, proj_total, \
            [proj_total_dict, sol_fra, pump_el_use, pump_op_hour, ts_res,
             backup_ts_cons, rel_err] = self.sol_wh_indiv_new.solar_thermal(
                 backup='gas')

        self.assertAlmostEqual(
            proj_total[self.r['q_del_tank']],
            2451283.75,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_dump']],
            1370147.25,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['el_use']],
            54490.14,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            cons_total.at[0, self.r['q_del_bckp']],
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            215101.34,
            places=1)

        self.assertAlmostEqual(
            sol_fra['annual'],
            cons_total.at[0, self.r['sol_fra']],
            places=1)

        # Seasonal energy use
        self.assertAlmostEqual(
            cons_total[self.r['gas_use']][0],
            (cons_total[self.r['gas_use_s']][0] +
             cons_total[self.r['gas_use_w']][0]),
            places=1)

        self.assertAlmostEqual(
            cons_total[self.r['el_use']][0],
            (cons_total[self.r['el_use_s']][0] +
             cons_total[self.r['el_use_w']][0]),
            places=1)

        if self.plot_results:
            Plot(data_headers=['Demand', 'Delivered', 'Unmet', 'Coil'],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Heat rate [W]').series(
                     ts_res.loc[5112:5232, [self.r['q_dem'],
                      self.r['q_del_tank'],
                      self.r['q_unmet_tank'],
                      self.r['q_del_sol']]],
                      outfile='img/'\
                      'sol_tank_ind_new_heatrate_defpars_4per_summer.png',
                      modes='lines')

            Plot(data_headers=[self.r['t_tank_up'], self.r['t_tank_low']],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Temperature [K]').series(
                     ts_res.loc[5112:5232, [self.r['t_tank_up'],
                     self.r['t_tank_low']]],
                     outfile='img/'\
                     'sol_tank_ind_new_temp_defpars_4per_summer.png',
                     modes='lines')

        if self.plot_results:
            Plot(data_headers=['Demand', 'Delivered', 'Unmet', 'Coil'],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Heat rate [W]').series(
                     ts_res.loc[480:600, [self.r['q_dem'],
                     self.r['q_del_tank'],
                     self.r['q_unmet_tank'], self.r['q_del_sol']]],
                     outfile='img/'\
                     'sol_tank_ind_new_heatrate_defpars_4per_winter.png',
                     modes='lines')

            Plot(data_headers=[self.r['t_tank_up'], self.r['t_tank_low']],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Temperature [K]').series(
                     ts_res.loc[480:600, [self.r['t_tank_up'],
                     self.r['t_tank_low']]],
                     outfile='img/'\
                     'sol_tank_ind_new_temp_defpars_4per_winter.png',
                     modes='lines')

    def test_solar_thermal_community_new(self):
        """Test solar thermal project level model with a
        tankless backup heater
        """
        # Default parameters, sizing and load for a 4 person
        # household.
        cons_total, proj_total, \
            [proj_total_dict, sol_fra, pump_el_use, pump_op_hour, ts_res,
             backup_ts_cons, rel_err] = \
            self.sol_wh_com_new.solar_thermal(backup='gas')

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            cons_total[self.r['q_del_bckp']].sum(),
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            cons_total[self.r['q_del_bckp']].sum(),
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['el_use']],
            138084.38,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_tank']],
            10475486.74,
            places=1)

        self.assertAlmostEqual(
            ts_res[self.r['q_dump']].sum(),
            proj_total[self.r['q_dump']],
            places=1)

        self.assertAlmostEqual(
            sol_fra['annual'],
            cons_total.at[1, self.r['sol_fra']],
            places=1)

        if self.plot_results:
            Plot(data_headers=['Demand', 'Delivered', 'Unmet', 'Coil'],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Heat rate [W]').series(
                     ts_res.loc[4900:5000, [self.r['q_dem'],
                     self.r['q_del_tank'],
                     self.r['q_unmet_tank'], self.r['q_del_sol']]],
                     outfile='img/sol_tank_com_new_heatrate_defpars_4per.png',
                     modes='lines')

            Plot(data_headers=[self.r['t_tank_up'], self.r['t_tank_low']],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Temperature [K]').series(
                     ts_res.loc[4900:5000, [self.r['t_tank_up'],
                     self.r['t_tank_low']]],
                     outfile='img/sol_tank_com_new_temp_defpars_4per.png',
                     modes='lines')

    def test_solar_thermal_individual_retrofit(self):
        """Tests solar thermal project level model with
        a gas tank backup heater
        """
        cons_total, proj_total, \
            [proj_total_dict, sol_fra, pump_el_use, pump_op_hour, ts_res,
             backup_ts_cons, rel_err] = \
            self.sol_wh_indiv_retr.solar_thermal(backup='retrofit')

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            cons_total[self.r['q_del_bckp']].sum(),
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            214742.0,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['el_use']],
            cons_total[self.r['el_use']].sum(),
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['el_use']],
            54490.14,
            places=1)

        self.assertAlmostEqual(
            ts_res[self.r['q_dump']].sum(),
            proj_total[self.r['q_dump']],
            places=1)

        self.assertAlmostEqual(
            sol_fra['annual'],
            cons_total.at[0, self.r['sol_fra']],
            places=1)

        if self.plot_results:
            Plot(data_headers=['Demand', 'Delivered', 'Unmet', 'Coil'],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Heat rate [W]').series(
                     ts_res.loc[4900:5000, [self.r['q_dem'],
                     self.r['q_del_tank'],
                     self.r['q_unmet_tank'], self.r['q_del_sol']]],
                     outfile='img/sol_tank_retr_heatrate_defpars_4per.png',
                     modes='lines')

            Plot(data_headers=[self.r['t_tank_up'], self.r['t_tank_low']],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Temperature [K]').series(
                     ts_res.loc[4900:5000, [self.r['t_tank_up'],
                     self.r['t_tank_low']]],
                     outfile='img/sol_tank_retr_temp_defpars_4per.png',
                     modes='lines')

    def test_solar_thermal_community_retrofit(self):
        """Tests solar thermal project level model with
        a gas tank backup heater
        """
        # Default parameters, sizing and load for a 4 person
        # household, retrofit
        cons_total, proj_total, \
            [proj_total_dict, sol_fra, pump_el_use, pump_op_hour, ts_res,
             backup_ts_cons, rel_err] = \
            self.sol_wh_com_retr.solar_thermal(backup='retrofit')

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            cons_total[self.r['q_del_bckp']].sum(),
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            846306.03,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['el_use']],
            cons_total[self.r['el_use']].sum(),
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['el_use']],
            138084.38,
            places=1)

        self.assertAlmostEqual(
            proj_total[self.r['q_del_bckp']],
            846306.03,
            places=1)

        self.assertAlmostEqual(
            ts_res[self.r['q_dump']].sum(),
            proj_total[self.r['q_dump']],
            places=1)

        self.assertAlmostEqual(
            sol_fra['annual'],
            cons_total.at[1, self.r['sol_fra']],
            places=1)

        if self.plot_results:
            Plot(data_headers=['Demand', 'Delivered', 'Unmet', 'Coil'],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Heat rate [W]').series(
                     ts_res.loc[4900:5000, [self.r['q_dem'],
                     self.r['q_del_tank'],
                     self.r['q_unmet_tank'], self.r['q_del_sol']]],
                     outfile='img/'\
                     'sol_tank_com_retr_heatrate_defpars_4per.png',
                     modes='lines')

            Plot(data_headers=[self.r['t_tank_up'], self.r['t_tank_low']],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Solar tank',
                 label_v='Temperature [K]').series(
                     ts_res.loc[4900:5000, [self.r['t_tank_up'],
                     self.r['t_tank_low']]],
                     outfile='img/sol_tank_com_retr_temp_defpars_4per.png',
                     modes='lines')

        # proj_total.to_csv('community_retrofit.csv')

    def test_validate_solar_thermal(self):
        """Compares annual solar fraction and gas use savings
        with rating data (gas tankless backup)
        """
        # Validation with average results for solar thermal
        # systems with an instantaneous backup
        # provided in OG-300 rated data
        # (compiled in W:\Non-APS\CEC PIER\PIER Solar Water Heating\
        # Analysis\Model Validation\Solar thermal\
        # OG-300_rating_data_summary_gas_inst_backup.xlsx)

        # Using average savings and climate zone 3 solar fractions
        # for all systems from above referenced file

        rated_SF = .72

        rated_en_savings = 4707.18

        cons_total, proj_total, \
            [proj_total_dict, sol_fra, pump_el_use,
             pump_op_hour, ts_res, backup_ts_cons, rel_err] = \
            self.val_sol_wh.solar_thermal(backup='gas')

        self.assertTrue(
            abs((sol_fra['annual'] - rated_SF) /
                sol_fra['annual']) < .15)

        # Basecase gas tank wh
        bc_cons_total, bc_proj_total, bc_ts_proj = \
            self.conv_wh_val.conventional_gas_tank()

        self.assertTrue(
            abs(((bc_cons_total[self.r['gas_use']] -
                  cons_total[self.r['gas_use']]) / 1000. -
                 rated_en_savings) / rated_en_savings)[0] < .1)

        # Electricity consumption in kW
        self.assertAlmostEqual(
            pump_el_use['total'],
            62694.14,
            places=1)

    def test_solar_electric(self):
        """Test solar electric project level model
        """
        # Default parameters, sizing and load for a 4 person household.

        cons_total, proj_total, \
            [proj_total_dict, sol_fra, pump_el_use,
             pump_op_hour, ts_res, rel_err] = \
            self.hp_wh.solar_electric()

        if self.plot_results:
            Plot(
                data_headers=['Demand', 'HP del', 'Aux del',
                              'Tank del', 'Unmet', 'Error',
                              'PV', 'HP el. use', 'Aux el. use'],
                outpath=self.outpath,
                save_image=self.plot_results,
                title='Heat pump tank with PV',
                label_v='Power / Heatrate [W]').series(
                    ts_res.loc[4920:5000, [self.r['q_dem'],
                    self.r['q_del_hp'],
                    self.r['q_del_bckp'],
                    self.r['q_del_tank'],
                    self.r['q_unmet_tank'],
                    self.r['q_err_tank'],
                    self.r['p_pv_ac'],
                    self.r['p_hp_el_use'],
                    self.r['p_el_res_use']]],
                    outfile='img/'\
                    'hp_tank_pv_heatrate_defpars_4per_80gallons.png',
                    modes='lines')

            Plot(data_headers=['T_upper', 'T_lower'],
                 outpath=self.outpath,
                 save_image=self.plot_results,
                 title='Heat pump tank',
                 label_v='Temperature [K]').series(
                     ts_res.loc[4920:5000, [self.r['t_tank_up'],
                     self.r['t_tank_low']]],
                     outfile='img/hp_tank_temp_defpars_4per_80gallons.png',
                     modes='lines')

        self.assertAlmostEqual(
            sol_fra['annual'],
            0.328,
            places=2)

    def test_conventional_gas_tank(self):
        """Tests project level gas tank wh model
        """

        cons_total, proj_total, ts_proj = \
            self.conv_wh.conventional_gas_tank()

        Plot(data_headers=['Gas use'],
             outpath=self.outpath,
             save_image=self.plot_results,
             title='Gas tank water heater (WHAM)',
             label_v='Heat rate [W]').series(
                 [ts_proj[self.r['gas_use']][4900:5000]],
                 outfile='img/gas_use_4per.png',
                 modes='lines')

        # Gas use
        self.assertAlmostEqual(
            cons_total[self.r['gas_use']][0],
            4727451.89,
            places=1)

        # Seasonal gas use
        self.assertAlmostEqual(
            cons_total[self.r['gas_use']][0],
            (cons_total[self.r['gas_use_s']][0] +
            cons_total[self.r['gas_use_w']][0]),
            places=1)

    def test__split_utility(self):
        """Tests how cost or consumption gets
        assigned to households
        """
        df = pd.DataFrame(
            columns=[self.c['id'], self.c['occ'], ],
            data=[[1, 2], [2, 3], [3, 4], [4, 3]])

        df = System._split_utility(
            df,
            value=120,
            var=self.r['el_use'],
            on=self.c['occ'])

        self.assertEqual(df.at[3, self.r['el_use']],
                         30.)
