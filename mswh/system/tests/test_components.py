import logging
import os
import unittest

import numpy as np
import pandas as pd

from mswh.system.components import Converter, Storage, Distribution
from mswh.system.source_and_sink import SourceAndSink
from mswh.comm.label_map import SwhLabels
from mswh.tools.plots import Plot
from mswh.tools.unit_converters import UnitConv
from mswh.comm.sql import Sql

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class ConverterTests(unittest.TestCase):
    """Unit tests for the system component models."""

    @classmethod
    def setUpClass(self):
        """Assigns values to test variables."""
        # Save plot images
        self.plot_results = True

        # get labels
        self.c = SwhLabels().set_hous_labels()
        self.s = SwhLabels().set_prod_labels()
        self.r = SwhLabels().set_res_labels()

        # gross collector area
        self.gross_area = 1.0  # [m3]

        # get solar radiation on 1m2 of a collector
        # with orientation (tilt, azimuth) = (latitude, 0)
        # for representative climate zones
        # read in data from the database
        # assuming test are run from ```MSWH``` directory
        weather_db_path = os.path.join(
            os.getcwd(), "mswh/comm/weather_and_loads.db"
        )

        # connect to the database
        db = Sql(weather_db_path)

        try:
            # read table names for all tables in a
            # {table name : sheet name} form
            inputs = db.tables2dict(close=True)
        except:
            msg = "Failed to read input tables from {}."
            log.error(msg.format(inpath))

        self.weather = SourceAndSink(input_dfs=inputs)

        # Arcata
        cold = self.weather.irradiation_and_water_main(
            "01", method="isotropic diffuse"
        )

        self.cold = cold[[self.c["irrad_on_tilt"], self.c["t_amb_C"]]]

        # LBNL
        mild = self.weather.irradiation_and_water_main(
            "03", method="isotropic diffuse"
        )
        self.mild = mild[[self.c["irrad_on_tilt"], self.c["t_amb_C"]]]

        # Palm Springs
        hot = self.weather.irradiation_and_water_main(
            "15", method="isotropic diffuse"
        )
        self.hot = hot[[self.c["irrad_on_tilt"], self.c["t_amb_C"]]]

        # average collector inlet temperature
        self.t_col_in = UnitConv(35.0).degC_K(unit_in="degC")  # [K]

        # for single time step
        self.inc_rad = 1000.0  # [W/m2]
        self.t_amb = UnitConv(25.0).degC_K(unit_in="degC")  # [K]

        # PV size (the parameters will follow below)
        pv_size = 1000.0

        sizes = pd.DataFrame(
            data=[
                [self.s["sol_col"], self.gross_area],
                [self.s["pv"], pv_size],
            ],
            columns=[self.s["comp"], self.s["cap"]],
        )

        sol_cd_params = pd.DataFrame(
            data=[
                [self.s["sol_col"], self.s["interc_cd"], 0.75],
                [self.s["sol_col"], self.s["a1_cd"], -3.688],
                [self.s["sol_col"], self.s["a2_cd"], -0.0055],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        sol_hwb_params = pd.DataFrame(
            data=[
                [self.s["sol_col"], self.s["interc_hwb"], 0.753],
                [self.s["sol_col"], self.s["slope_hwb"], -4.025],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        pv_simple_params = pd.DataFrame(
            data=[
                [self.s["pv"], self.s["eta_pv"], 0.16],
                [self.s["inv"], self.s["eta_dc_ac"], 0.85],
                [self.s["pv"], self.s["f_act"], 1.0],
                [self.s["pv"], self.s["irrad_ref"], 1000.0],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        self.hp_params = pd.DataFrame(
            data=[
                [self.s["hp"], self.s["c1_cop"], 1.229e00],
                [self.s["hp"], self.s["c2_cop"], 5.549e-02],
                [self.s["hp"], self.s["c3_cop"], 1.139e-04],
                [self.s["hp"], self.s["c4_cop"], -1.128e-02],
                [self.s["hp"], self.s["c5_cop"], -3.570e-06],
                [self.s["hp"], self.s["c6_cop"], -7.234e-04],
                [self.s["hp"], self.s["c1_heat_cap"], 7.055e-01],
                [self.s["hp"], self.s["c2_heat_cap"], 3.945e-02],
                [self.s["hp"], self.s["c3_heat_cap"], 1.433e-04],
                [self.s["hp"], self.s["c4_heat_cap"], 2.768e-03],
                [self.s["hp"], self.s["c5_heat_cap"], -1.069e-04],
                [self.s["hp"], self.s["c6_heat_cap"], -2.494e-04],
                [self.s["hp"], self.s["heat_cap_rated"], 2350.0],
                [self.s["hp"], self.s["cop_rated"], 2.43],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        pv_size = 1000.0

        # Set the heating capacity of the heat pump
        self.hp_size = 2350.0

        sizes = pd.DataFrame(
            data=[
                [self.s["sol_col"], self.gross_area],
                [self.s["pv"], pv_size],
                [self.s["hp"], self.hp_size],
            ],
            columns=[self.s["comp"], self.s["cap"]],
        )

        # 6.25 m2 corresponds to 1000 Wdc peak power (with eta_pv = 16% and
        # f_act = 1.)
        sm_pv_area = pd.DataFrame(
            data=[[self.s["pv"], 6.25]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        gas_burn_params = pd.DataFrame(
            data=[[self.s["gas_burn"], self.s["comb_eff"], 0.85]],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        gas_burn_size = pd.DataFrame(
            data=[[self.s["gas_burn"], 24000.0]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        el_res_params = pd.DataFrame(
            data=[[self.s["el_res"], self.s["eta_el_res"], 1.0]],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        el_res_size = pd.DataFrame(
            data=[[self.s["el_res"], 6500.0]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        # without any parameters to call static methods
        self.comp = Converter()

        # for a year of operation
        self.hwb_col = Converter(params=sol_hwb_params, sizes=sizes)
        self.cd_col = Converter(params=sol_cd_params, sizes=sizes)
        self.simple_pv_kWpeak = Converter(params=pv_simple_params, sizes=sizes)

        self.simple_pv_area = Converter(
            params=pv_simple_params, sizes=sm_pv_area
        )

        self.hp = Converter(params=self.hp_params, weather=mild, sizes=sizes)

        self.inst_gas_wh = Converter(
            params=gas_burn_params, sizes=gas_burn_size
        )

        self.el_res = Converter(params=el_res_params, sizes=el_res_size)

        # functional test for initiation with default inputs
        self.params_none = Converter(params=None, sizes=1.0)

        # save under the test directory
        self.outpath = os.path.dirname(__file__)

    def test_electric_resistance(self):
        """Tests parameter extraction"""
        demand = np.array([8000.0, 6500.0, 3000.0])
        delivery = np.array([6500.0, 6500.0, 3000.0])
        array_electric_resistance = self.el_res.electric_resistance(demand)

        self.assertTrue(
            (array_electric_resistance[self.r["q_del_bckp"]] == delivery).all()
        )

    def test__heat_pump(self):
        """Single timestep performance"""

        # Use the values stated as rated conditions in the report
        T_wet_bulb = 293.15  # K  (20 degC)
        T_tank = 322.05  # K  (48.9 degC)

        # Use the coefficients of Unit A
        C1 = 1.229e00
        C2 = 5.549e-02
        C3 = 1.139e-04
        C4 = -1.128e-02
        C5 = -3.570e-06
        C6 = -7.234e-04

        # The formula needs temperatures in Celsius
        T_wet_bulb_C = UnitConv(T_wet_bulb).degC_K(unit_in="K")
        T_tank_C = UnitConv(T_tank).degC_K(unit_in="K")

        # Calculate performance factor
        performance = (
            C1
            + C2 * T_wet_bulb_C
            + C3 * T_wet_bulb_C * T_wet_bulb_C
            + C4 * T_tank_C
            + C5 * T_tank_C * T_tank_C
            + C6 * T_wet_bulb_C * T_tank_C
        )

        self.assertEqual(
            self.comp._heat_pump(T_wet_bulb, T_tank, C1, C2, C3, C4, C5, C6),
            performance,
        )

    def test_heat_pump(self):
        """Single timestep performance"""

        # Use the values stated as rated conditions in the report
        T_wet_bulb = 293.15  # K  (20 degC)
        T_tank = 322.05  # K  (48.9 degC)

        # Use the coefficients of Unit A
        C1 = self.hp_params.loc[
            self.hp_params[self.s["param"]] == self.s["c1_heat_cap"],
            self.s["param_value"],
        ].values[0]
        C2 = self.hp_params.loc[
            self.hp_params[self.s["param"]] == self.s["c2_heat_cap"],
            self.s["param_value"],
        ].values[0]
        C3 = self.hp_params.loc[
            self.hp_params[self.s["param"]] == self.s["c3_heat_cap"],
            self.s["param_value"],
        ].values[0]
        C4 = self.hp_params.loc[
            self.hp_params[self.s["param"]] == self.s["c4_heat_cap"],
            self.s["param_value"],
        ].values[0]
        C5 = self.hp_params.loc[
            self.hp_params[self.s["param"]] == self.s["c5_heat_cap"],
            self.s["param_value"],
        ].values[0]
        C6 = self.hp_params.loc[
            self.hp_params[self.s["param"]] == self.s["c6_heat_cap"],
            self.s["param_value"],
        ].values[0]
        rated_performance = self.hp_size

        # The formula needs temperatures in Celsius
        T_wet_bulb_C = UnitConv(T_wet_bulb).degC_K(unit_in="K")
        T_tank_C = UnitConv(T_tank).degC_K(unit_in="K")

        # Calculate performance factor
        performance_factor = (
            C1
            + C2 * T_wet_bulb_C
            + C3 * T_wet_bulb_C * T_wet_bulb_C
            + C4 * T_tank_C
            + C5 * T_tank_C * T_tank_C
            + C6 * T_wet_bulb_C * T_tank_C
        )

        # Calculate the resulting performance
        current_performance = rated_performance * performance_factor

        # Calculate the resulting performance with heat pump model
        hp_res = self.hp.heat_pump(T_wet_bulb, T_tank)

        # msg = ' Heating capacity of heat pump: {}'
        # log.info(msg.format(hp_res['heat_cap'].round(2)))
        #
        # msg = ' COP of heat pump: {}'
        # log.info(msg.format(hp_res['cop'].round(2)))
        #
        # msg = ' Electricity use of heat pump: {}'
        # log.info(msg.format(hp_res['el_use'].round(2)))

        # Check if all elements of both arrays are equal
        self.assertTrue(np.allclose(hp_res["heat_cap"], current_performance))

    def test_heat_pump_validate(self):
        """Validate heat pump performance for different scenarios"""

        # Define number of data samples withing provided ranges
        values = 50

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Scenario 1 - Constant T_wet_bulb
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # T_tank range
        T_tank_start = 293.15  # 20 degC
        T_tank_end = 343.15  # 70 degC

        # T_wet_bulb (indoor temperature)
        T_wb_const_dict = {
            "T_wb = 35 °C": 308.15,
            "T_wb = 30 °C": 303.15,
            "T_wb = 25 °C": 298.15,
            "T_wb = 20 °C": 293.15,
            "T_wb = 15 °C": 288.15,
            "T_wb = 10 °C": 283.15,
            "T_wb =  5 °C": 278.15,
            "T_wb =  0 °C": 273.15,
        }

        # Create numpy array with 50 values for given range
        T_tank = np.linspace(T_tank_start, T_tank_end, values)

        # List holding the result arrays
        cop_res = []

        for T_wb_static in T_wb_const_dict.values():

            # Create numpy array with 50 values all being the static value
            T_wet_bulb = np.linspace(T_wb_static, T_wb_static, values)

            # Calculate performance for given range
            cop_res.append(self.hp.heat_pump(T_wet_bulb, T_tank)["cop"])

        # Convert to celsius for plotting
        T_tank_C = UnitConv(T_tank).degC_K(unit_in="K")

        # Headers for plotting
        T_wb_headers = list(T_wb_const_dict)

        # Create a list with correlation pairs used by the Plot() class
        plot_headers = []
        for T_wb_header in T_wb_headers:
            plot_headers += ["-", T_wb_header]

        correlation_pairs = []
        for cop in cop_res:
            correlation_pairs += [T_tank_C, cop]

        # Create the plot
        Plot(
            data_headers=plot_headers,
            outpath=self.outpath,
            save_image=self.plot_results,
            title="COP & Tank Temperature",
            label_v="COP",
            label_h="T_tank [°C]",
        ).scatter(
            correlation_pairs,
            outfile="img/hp_validation_cop_t_tank.png",
            modes="markers",
        )

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Scenario 2 - Constant T_tank
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # T_wet_bulb range
        T_wb_start = 273.15  # 0 degC
        T_wb_end = 308.15  # 35 degC

        # T_tank (indoor temperature)
        T_tank_static_dict = {
            "T_tank = 20 °C": 293.15,
            "T_tank = 30 °C": 303.15,
            "T_tank = 40 °C": 313.15,
            "T_tank = 50 °C": 323.15,
            "T_tank = 60 °C": 333.15,
            "T_tank = 70 °C": 343.15,
        }

        # Create numpy array with 50 values for given range
        T_wet_bulb = np.linspace(T_wb_start, T_wb_end, values)

        # List holding the result arrays
        cop_res = []

        for T_tank_static in T_tank_static_dict.values():

            # Create numpy array with 50 values all being the static value
            T_tank = np.linspace(T_tank_static, T_tank_static, values)

            # Calculate performance for given range
            cop_res.append(self.hp.heat_pump(T_wet_bulb, T_tank)["cop"])

        # Convert to celsius for plotting
        T_wet_bulb_C = UnitConv(T_wet_bulb).degC_K(unit_in="K")

        # Headers for plotting
        T_tank_headers = list(T_tank_static_dict)

        # Create a list with correlation pairs used by the Plot() class
        plot_headers = []
        for T_tank_header in T_tank_headers:
            plot_headers += ["-", T_tank_header]

        correlation_pairs = []
        for cop in cop_res:
            correlation_pairs += [T_wet_bulb_C, cop]

        # Create the plot
        Plot(
            data_headers=plot_headers,
            outpath=self.outpath,
            save_image=self.plot_results,
            title="COP & Wet Bulb Temperature",
            label_v="COP",
            label_h="T_wet_bulb [°C]",
        ).scatter(
            correlation_pairs,
            outfile="img/hp_validation_cop_t_wet_bulb.png",
            modes="markers",
        )

    def test__heater(self):
        """Tests heater as gas burner and el. resistance
        element
        """
        # as gas burner

        # single timestep
        nom_size = 24000.0
        demand = 26000.0
        delivery = min(demand, nom_size)
        unmet = demand - delivery
        eta = 0.85
        consumed = delivery / eta

        Q_del, Q_gas_use, Q_unmet = self.comp._heater(demand, Q_nom=nom_size)

        self.assertAlmostEqual(Q_del, delivery, places=5)
        self.assertAlmostEqual(Q_unmet, unmet, places=5)
        self.assertAlmostEqual(Q_gas_use, consumed, places=5)

        # array
        demand = np.array([26000.0, 24000.0, 20000.0])
        delivery = np.array([24000.0, 24000.0, 20000.0])
        unmet = np.array([2000.0, 0.0, 0.0])
        consumed = delivery / eta

        Q_del, Q_gas_use, Q_unmet = self.comp._heater(
            demand, eff=eta, Q_nom=nom_size
        )

        self.assertTrue((Q_del == delivery).all())
        self.assertTrue((Q_unmet == unmet).all())
        self.assertTrue((Q_gas_use == consumed).all())

        # as electric resistance
        nom_size = 6500.0
        demand = 7000.0
        delivery = min(demand, nom_size)
        unmet = demand - delivery
        eta = 1.0
        consumed = delivery / eta

        Q_del, P_el_use, Q_unmet = self.comp._heater(
            demand, eff=eta, Q_nom=nom_size
        )

        self.assertAlmostEqual(Q_del, delivery, places=5)
        self.assertAlmostEqual(Q_unmet, unmet, places=5)
        self.assertAlmostEqual(P_el_use, consumed, places=5)

        # array
        demand = np.array([8000.0, 6500.0, 3000.0])
        delivery = np.array([6500.0, 6500.0, 3000.0])
        unmet = np.array([1500.0, 0.0, 0.0])
        consumed = delivery / eta

        Q_del, P_el_use, Q_unmet = self.comp._heater(
            demand, eff=eta, Q_nom=nom_size
        )

        self.assertTrue((Q_del == delivery).all())
        self.assertTrue((Q_unmet == unmet).all())
        self.assertTrue((P_el_use == consumed).all())

    def test_gas_burner(self):
        """Tests parameter extraction"""
        demand = np.array([26000.0, 24000.0, 20000.0])
        delivery = np.array([24000.0, 24000.0, 20000.0])
        array_burner = self.inst_gas_wh.gas_burner(demand)

        self.assertTrue((array_burner[self.r["q_del_bckp"]] == delivery).all())

    def test__hwb_solar_collector(self):
        """Single timestep performance"""

        intercept = 0.753
        slope = -4.025

        gain = (
            self.gross_area
            * self.inc_rad
            * (
                intercept
                + slope * ((self.t_col_in - self.t_amb) / self.inc_rad)
            )
        )

        self.assertAlmostEqual(
            self.comp._hwb_solar_collector(
                self.gross_area, self.inc_rad, self.t_amb, self.t_col_in
            )[0],
            gain,
            places=2,
        )

    def test__cd_solar_collector(self):
        """Single timestep performance"""

        intercept = 0.75
        a_1 = -3.688
        a_2 = -0.0055

        gain = (
            self.gross_area
            * self.inc_rad
            * (
                intercept
                + a_1 * ((self.t_col_in - self.t_amb) / self.inc_rad)
                + a_2 * ((self.t_col_in - self.t_amb) / self.inc_rad ** 2)
            )
        )

        self.assertAlmostEqual(
            self.comp._cd_solar_collector(
                self.gross_area, self.inc_rad, self.t_amb, self.t_col_in
            )[0],
            gain,
            places=2,
        )

    def test_compare_annual_sol_col_perf(self):
        """Annual performance comparison"""
        # annual (8760 time steps)
        t_col_in = self.t_col_in * np.ones(8760)

        # cold climate

        self.hwb_col.weather = self.cold
        self.cd_col.weather = self.cold

        self.hwb_col.solar_collector(t_col_in)
        self.cd_col.solar_collector(t_col_in)

        # plot annual duration curve
        if self.plot_results:
            Plot(
                data_headers=["HWB", "CD"],
                outpath=self.outpath,
                save_image=self.plot_results,
                title="HWB and CD model results duration curve for CZ01 (cold)",
                label_v="Solar gain [W/m^2]",
                duration_curve=True,
            ).series(
                [self.hwb_col.sol_col_gain, self.cd_col.sol_col_gain],
                outfile="img/solar_gain_comp_cold.png",
                modes="markers",
            )

        # check annual relative error between the two models is
        # under 10%
        both_gain = np.logical_and(
            self.hwb_col.sol_col_gain, self.cd_col.sol_col_gain
        )

        hwb = self.hwb_col.sol_col_gain[both_gain]
        cd = self.cd_col.sol_col_gain[both_gain]

        err = cd - hwb
        rel_err = abs(err / cd)
        self.assertTrue(np.mean(rel_err) < 0.1)

        # mild climate

        self.hwb_col.weather = self.mild
        self.cd_col.weather = self.mild

        self.hwb_col.solar_collector(t_col_in)
        self.cd_col.solar_collector(t_col_in)

        # plot annual duration curve
        if self.plot_results:
            Plot(
                data_headers=["HWB", "CD"],
                outpath=self.outpath,
                save_image=self.plot_results,
                title="HWB and CD model results duration curve for CZ03 (mild)",
                label_v="Solar gain [W/m^2]",
                duration_curve=True,
            ).series(
                [self.hwb_col.sol_col_gain, self.cd_col.sol_col_gain],
                outfile="img/solar_gain_comp_mild.png",
                modes="markers",
            )

        # check annual relative error between the two models
        both_gain = np.logical_and(
            self.hwb_col.sol_col_gain, self.cd_col.sol_col_gain
        )

        hwb = self.hwb_col.sol_col_gain[both_gain]
        cd = self.cd_col.sol_col_gain[both_gain]

        err = cd - hwb
        rel_err = abs(err / cd)

        self.assertTrue(np.mean(rel_err) < 0.1)

        # hot climate

        self.hwb_col.weather = self.hot
        self.cd_col.weather = self.hot

        self.hwb_col.solar_collector(t_col_in)
        self.cd_col.solar_collector(t_col_in)

        # plot annual duration curve
        if self.plot_results:
            Plot(
                data_headers=["HWB", "CD"],
                outpath=self.outpath,
                save_image=self.plot_results,
                title="HWB and CD model results duration curve for CZ15 (hot)",
                label_v="Solar gain [W/m^2]",
                duration_curve=True,
            ).series(
                [self.hwb_col.sol_col_gain, self.cd_col.sol_col_gain],
                outfile="img/solar_gain_comp_hot.png",
                modes="markers",
            )

        # check annual relative error between the two models
        both_gain = np.logical_and(
            self.hwb_col.sol_col_gain, self.cd_col.sol_col_gain
        )

        hwb = self.hwb_col.sol_col_gain[both_gain]
        cd = self.cd_col.sol_col_gain[both_gain]

        err = cd - hwb
        rel_err = abs(err / cd)

        self.assertTrue(np.mean(rel_err) < 0.1)

    def test__simple_photovoltaic(self):
        """Single timestep performance"""

        panel_area = 1.67
        f_act = 1.0
        irrad = 240.0
        irrad_ref = 1000.0
        p_peak = 1200.0
        eta_pv = 0.15
        eta_dc_ac = 0.82

        # Test case 1: with panel area, pv efficieny and f_act
        power = panel_area * f_act * eta_pv * irrad * eta_dc_ac

        self.assertEqual(
            self.comp._simple_photovoltaic(
                irrad,
                panel_area=panel_area,
                f_act=f_act,
                eta_pv=eta_pv,
                eta_dc_ac=eta_dc_ac,
            )["ac"],
            power,
        )

        # Test case 2: with peak power and reference irradiation
        power = (p_peak / irrad_ref) * irrad * eta_dc_ac

        self.assertEqual(
            self.comp._simple_photovoltaic(
                irrad=irrad,
                eta_dc_ac=eta_dc_ac,
                irrad_ref=irrad_ref,
                p_peak=p_peak,
            )["ac"],
            power,
        )

    def test_sol_col_validate_with_SAM(self):
        """Solar collector validation with SAM simulation
        results, which are stored in a CSV file in this
        test folder.
        """

        # SF tmy3 for validation with SAM
        sf = self.weather.irradiation_and_water_main(
            "03", method="isotropic diffuse", weather_data_source="tmy3"
        )

        self.sf = sf.loc[
            :, [self.c["irrad_on_tilt"], self.c["t_amb_C"], self.c["month"]]
        ]

        sam_data = pd.read_csv(
            os.path.join(self.outpath, "data/sam_sol_col.csv")
        )

        t_col_in = UnitConv(sam_data["T_cold_C"].values).degC_K(unit_in="degC")

        self.hwb_col.weather = self.sf
        self.hwb_col.solar_collector(t_col_in)

        self.hwb_col.sol_col_gain[np.isnan(self.hwb_col.sol_col_gain)] = 0.0

        self.sf.loc[:, "sol_gain"] = self.hwb_col.sol_col_gain
        self.sf.to_csv(
            os.path.join(self.outpath, "data/validation_sol_col_mswh_hwb.csv")
        )

        err = abs(
            (
                self.sf.sum()["sol_gain"] / 1000.0
                - sam_data.sum()["solar net gain SAM"]
            )
            / (self.sf.sum()["sol_gain"] / 1000.0)
        )

        # check if the error is less than
        perc = 10.0

        self.assertTrue(err < perc / 100.0, "Error is {}!".format(err))

        if self.plot_results:
            # plot duration curves
            Plot(
                data_headers=["HWB", "SAM"],
                outpath=self.outpath,
                save_image=self.plot_results,
                title="HWB and SAM model duration curves",
                label_v="Solar gain [W/m^2]",
                duration_curve=True,
            ).series(
                [
                    self.hwb_col.sol_col_gain,
                    1000.0 * sam_data["solar net gain SAM"].values,
                ],
                outfile="img/hwb_vs_sam_validation_duration.png",
                modes="markers",
            )

            # plot correlation
            Plot(
                data_headers=["-", "Correlation"],
                outpath=self.outpath,
                save_image=self.plot_results,
                title="HWB vs. SAM",
                label_v="SAM model solar gain [W/m^2]",
                label_h="HWB model solar gain [W/m^2]",
                duration_curve=True,
            ).scatter(
                [
                    self.hwb_col.sol_col_gain,
                    1000.0 * sam_data["solar net gain SAM"].values,
                ],
                outfile="img/hwb_vs_sam_validation_correlation.png",
                modes="markers",
            )

    def test_pv_validate_with_SAM(self):
        """See V:/Non-APS/CEC PIER/PIER Solar Water Heating/
        Analysis/Model Validation for SAM simulation parameters.
        SAM simulation results are stored in a CSV file in this
        test folder.
        """

        # Set output file name bases
        dur_file = "pv_mswh_vs_sam_validation_duration_"
        cor_kWpeak_file = "pv_vs_sam_validation_correlation_kWpeak_"
        cor_area_file = "pv_vs_sam_validation_correlation_area_"
        csv_file = "mswh_pv_"

        # Validate for an example smaller (peak power = 1 kWdc)
        # and an example bigger (peak power = 4 kWdc) PV system,
        # both simulated in NREL's SAM with reference results saved
        # in the data folder
        cases = ["1kWdc", "4kWdc"]

        # sizes df in setup uses the smaller PV, here we'll need the
        # larger one as well
        lg_pv_peakpower = pd.DataFrame(
            data=[[self.s["pv"], 4000.0]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        # sizing dfs for running the model based on the panel area

        # 25 m2 corresponds to 4000 Wdc peak power (with eta_pv = 16%)
        lg_pv_area = pd.DataFrame(
            data=[[self.s["pv"], 25.0]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        for case in cases:

            # initiate a dictionary to store the PV power yield timeseries
            pv_yields = pd.DataFrame()

            # fetch SAM validation reference timeseries
            sam_data = pd.read_csv(
                os.path.join(self.outpath, "data/sam_pv_" + case + ".csv")
            )

            # extract weather data in order to use the identical incident
            # irradiation and ambient temperature
            weather = pd.DataFrame()
            weather["global_tilt_radiation_Wm2"] = sam_data[
                "Beam irradiance | (W/m2)"
            ]
            weather["dry_bulb_C"] = sam_data["Ambient temperature | (C)"]

            pv_yields["sam"] = sam_data["System power generated | (kW)"]

            if case == "4kWdc":  # reasign size
                self.simple_pv_kWpeak.size = lg_pv_peakpower
                self.simple_pv_area.size = lg_pv_area

            # Calculate MSWH PV peak power based model yield, in kW
            self.simple_pv_kWpeak.weather = weather
            pv_yields["mswh_kWpeak_pv"] = (
                self.simple_pv_kWpeak.photovoltaic(use_p_peak=True)["ac"]
                / 1000.0
            )

            # Calculate MSWH PV area based model yield, in kW
            self.simple_pv_area.weather = weather
            pv_yields["mswh_area_pv"] = (
                self.simple_pv_area.photovoltaic(use_p_peak=False)["ac"]
                / 1000.0
            )

            # write to csv file
            pv_yields.to_csv(
                os.path.join(self.outpath, "data/" + csv_file + case + ".csv")
            )

            # Check relative error of the annual cumulative value
            # below 10% compared to SAM
            perc = 10.0

            err_kWpeak = abs(
                (pv_yields["mswh_kWpeak_pv"].sum() - pv_yields["sam"].sum())
                / (pv_yields["mswh_kWpeak_pv"].sum())
            )

            self.assertTrue(
                err_kWpeak < perc / 100.0,
                "Relative Error on the annual cumulative is {}%!".format(
                    err_kWpeak * 100.0
                ),
            )

            err_area = abs(
                (pv_yields["mswh_area_pv"].sum() - pv_yields["sam"].sum())
                / (pv_yields["mswh_area_pv"].sum())
            )

            self.assertTrue(
                err_area < perc / 100.0,
                "Relative Error on the annual cumulative is {}%!".format(
                    err_area * 100.0
                ),
            )

            if self.plot_results:
                # plot duration curves
                Plot(
                    data_headers=["SAM", "MSWH PV - kWPeak", "MSWH PV - Area"],
                    outpath=self.outpath,
                    save_image=self.plot_results,
                    title=(
                        "MSWH PV vs. SAM duration curves for Ppeak = " + case
                    ),
                    label_v="Generated power [kW]",
                    duration_curve=True,
                ).series(
                    [
                        pv_yields["sam"].values,
                        pv_yields["mswh_kWpeak_pv"].values,
                        pv_yields["mswh_area_pv"].values,
                    ],
                    outfile="img/" + dur_file + case + ".png",
                    modes="markers",
                )

                # plot correlation for peak power based model
                Plot(
                    data_headers=["-", "Correlation"],
                    outpath=self.outpath,
                    save_image=self.plot_results,
                    title=("MSWH PV vs. SAM for Ppeak = " + case),
                    label_v="SAM model, generated power [kW]",
                    label_h="MSWH PV model, generated power [kW]",
                    duration_curve=True,
                ).scatter(
                    [pv_yields["mswh_kWpeak_pv"], pv_yields["sam"]],
                    outfile="img/" + cor_kWpeak_file + case + ".png",
                    modes="markers",
                )

                # plot correlation for area based model
                Plot(
                    data_headers=["-", "Correlation"],
                    outpath=self.outpath,
                    save_image=self.plot_results,
                    title=("Simple PV vs. SAM for Area = " + case),
                    label_v="SAM model, generated power [kW]",
                    label_h="MSWH PV model, generated power [kW]",
                    duration_curve=True,
                ).scatter(
                    [pv_yields["mswh_area_pv"], pv_yields["sam"]],
                    outfile="img/" + cor_area_file + case + ".png",
                    modes="markers",
                )


class StorageTests(unittest.TestCase):
    """Unit tests for the storage component models."""

    @classmethod
    def setUp(self):
        """Assigns values to test variables."""
        self.random_state = np.random.RandomState(123)

        self.s = SwhLabels().set_prod_labels()
        self.r = SwhLabels().set_res_labels()
        self.c = SwhLabels().set_hous_labels()

        # for testing generic tank submethods
        self.tank = Storage(
            size=UnitConv(30).m3_gal(), type="sol_tank"
        )  # .11356236 m3

    def test__tank_area(self):
        """Test lower and upper tank area calculation
        based on the tank volume and height assigned
        to the upper/lower model volume
        """
        h_vs_r = 6
        vol = self.tank.size
        rad = np.cbrt(vol / (h_vs_r * np.pi))
        hei = rad * h_vs_r

        tank_A = 2 * (vol / hei + np.sqrt(vol * hei * np.pi))

        half_tank_A = tank_A / 2.0

        area = rad ** 2 * np.pi + 2 * rad * np.pi * hei

        # test upper and lower tank area
        self.assertAlmostEqual(
            self.tank._tank_area()["upper"], half_tank_A, places=5
        )

        self.assertAlmostEqual(
            self.tank._tank_area()["lower"], half_tank_A, places=5
        )

        # test whole tank area
        self.assertAlmostEqual(
            self.tank._tank_area(split_tank=False), tank_A, places=5
        )

    def test__thermal_transmittance(self):
        """Tests U-value calculation based
        on insulation thickness and its
        specific heat conductivity
        """
        insul_thickness = 0.04
        spec_hea_conductivity = 0.04

        self.assertEqual(
            self.tank._thermal_transmittance(),
            spec_hea_conductivity / insul_thickness,
        )

    def test__thermal_loss(self):
        """Calculates heat loss rate through a tank wall"""
        insul_thick = 0.04
        spec_hea_c = 0.04

        therm_transm_coef = spec_hea_c / insul_thick

        T_tank = 55.0  # degC
        T_amb = 15.0  # degC

        area = 2.0  # m2

        Q_loss = (
            self.tank._thermal_transmittance(
                insul_thickness=insul_thick, spec_hea_cond=spec_hea_c
            )
            * (T_tank - T_amb)
            * area
        )

        self.assertEqual(
            self.tank._thermal_loss(therm_transm_coef, area, T_amb, T_tank),
            Q_loss,
        )

    def test_tap(self):
        """Tests volume tapped from the tank
        to households and its heat content
        based on hot water demand and tank temperature
        """

        V_draw_load = 0.02  # m3/h

        T_feed = 293.15  # 20 degC for the main
        T_draw_nom = 322.04  # 48.89 degC

        # draw when tank below demand temperature
        # and assert volume drawn equals demand and
        # there exists unmet load
        T_tank_low = 313.15  # the tank is at 40 degC

        self.assertAlmostEqual(
            self.tank.tap(V_draw_load, T_tank_low, T_feed, T_draw_min=None)[
                "vol"
            ],
            V_draw_load,
            places=5,
        )

        self.assertTrue(
            self.tank.tap(V_draw_load, T_tank_low, T_feed, T_draw_min=None)[
                "unmet_heat_rate"
            ]
            > 0.0
        )

        # draw when tank above demand temperature
        T_tank_high = 353.15  # the tank is at 70 degC
        V_high = V_draw_load * (T_draw_nom - T_feed) / (T_tank_high - T_feed)

        self.assertAlmostEqual(
            self.tank.tap(V_draw_load, T_tank_high, T_feed, T_draw_min=None)[
                "vol"
            ],
            V_high,
            places=5,
        )

        # assert that the heat flow is the same as
        # if the demanded volume was drawn at the
        # nominal draw temperature (which is the
        # temperature used to define the draw volume)
        ro = 998.2  # kg/m3
        shc = 4180.0  # J/(kgK)

        Q_at_T_nom = round(
            (T_draw_nom - T_feed)
            * ro
            * shc
            * UnitConv(V_draw_load).m3perh_m3pers(unit_in="m3perh"),
            2,
        )

        self.assertAlmostEqual(
            self.tank.tap(V_draw_load, T_tank_high, T_feed, T_draw_min=None)[
                "tot_dem"
            ],
            Q_at_T_nom,
            places=2,
        )

    def test_thermal_tank_dynamics(self):
        """Tests the thermal storage model"""

        T_tank_upper = 65.0 + 273.15  # K
        T_tank_lower = 55.0 + 273.15  # K
        T_amb = 25.0 + 273.15  # K
        T_main = 18.0 + 273.15  # K
        Q_in = 500.0  # W
        draw_V = 0.0037  # m3/h
        Q_loss_upper = self.tank._thermal_loss(
            self.tank.therm_transm_coef, self.tank.A_upper, T_amb, T_tank_upper
        )

        Q_loss_lower = self.tank._thermal_loss(
            self.tank.therm_transm_coef, self.tank.A_lower, T_amb, T_tank_lower
        )

        Q_draw = self.tank.tap(draw_V, T_tank_upper, T_main)["heat_rate"]

        res = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_draw,
        )

        # Test steady state - in each timestep the losses from equal
        # gains to the tank. There should be no changes to tank temperature.

        T_tank_upper = 60.0 + 273.15  # K
        T_tank_lower = 55.0 + 273.15  # K

        Q_loss_upper = 150.0  # W
        Q_loss_lower = 100.0  # W
        Q_tap = 250.0  # W

        steady = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_tap,
        )

        self.assertEqual(steady[self.r["t_tank_up"]], T_tank_upper)
        self.assertEqual(steady[self.r["t_tank_low"]], T_tank_lower)

        # Tests allocation of heat gains and losses depending on
        # the conditions in the upper and lower part of the tank

        # Charge to upper only, dQ > 0
        T_tank_upper = 55.0 + 273.15  # K
        T_tank_lower = 55.0 + 273.15  # K

        Q_loss_upper = 50.0  # W
        Q_loss_lower = 30.0  # W
        Q_tap = 150.0  # W

        charge_upper = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_tap,
        )

        self.assertTrue(
            charge_upper[self.r["t_tank_up"]]
            == (
                T_tank_upper
                + self.tank.dT_approach
                + charge_upper[self.r["t_tank_low"]]
                - T_tank_lower
            )
        )
        self.assertEqual(
            charge_upper[self.r["t_tank_up"]] - self.tank.dT_approach,
            charge_upper[self.r["t_tank_low"]],
        )

        # Charge both, dQ > 0
        T_tank_upper = 57.0 + 273.15  # K
        T_tank_lower = 55.0 + 273.15  # K

        charge_both = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_tap,
        )

        self.assertEqual(
            charge_both[self.r["t_tank_up"]]
            - charge_both[self.r["t_tank_low"]],
            self.tank.dT_approach,
        )

        # Charge when tank upper temperature is already at
        # the maximum allowed tank temperature, dQ > 0

        T_tank_upper = self.tank.T_max  # K
        T_tank_lower = self.tank.T_max - self.tank.dT_approach  # K

        charge_max = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_tap,
        )

        self.assertEqual(charge_max[self.r["t_tank_up"]], T_tank_upper)
        self.assertEqual(charge_max[self.r["t_tank_low"]], T_tank_lower)
        self.assertAlmostEqual(
            charge_max["Q_net"], charge_max[self.r["q_dump"]], places=5
        )

        # dQ < 0
        Q_in = 0.0  # W

        # Cool off lower part of the tank
        Q_loss_upper = 100.0  # W
        Q_loss_lower = 100.0  # W
        Q_tap = 0.0  # W

        T_tank_upper = 57.0 + 273.15  # K
        T_tank_lower = 55.0 + 273.15  # K

        cool_lower = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_tap,
        )

        self.assertEqual(cool_lower[self.r["t_tank_up"]], T_tank_upper)
        self.assertTrue(cool_lower[self.r["t_tank_low"]] < T_tank_lower)

        T_tank_lower = 22.0 + 273.15  # K

        cool_lower_then_upper = self.tank.thermal_tank_dynamics(
            T_amb,
            T_tank_upper,
            T_tank_lower,
            Q_in,
            Q_loss_upper,
            Q_loss_lower,
            T_main,
            Q_tap,
        )

        self.assertTrue(
            cool_lower_then_upper[self.r["t_tank_up"]] < T_tank_upper
        )
        self.assertTrue(
            cool_lower_then_upper[self.r["t_tank_low"]] < T_tank_lower
        )

    def test__gas_tank_wh(self):
        """Single timestep performance"""

        V_draw = 0.00946353  # m3/hour (corresponds to 2.5 gal/h)
        tank_V = 0.208198  # m3 (corresponds to 55 gal)
        tank_input_power = (63560.0 * tank_V) + 1777.9  # W
        tank_A = 3.3  # m2 (based on dimensions of a 55-gallon tank online)
        tank_U = 1.0  # W/m2K (based on default inputs to
        # _thermal_transmittance() method)
        tank_re = 0.76
        T_setpoint = 322.039  # K (corresponds to 120 F)
        T_feed = 283.15  # K (corresponds to 50 F)
        T_amb = 291.48  # K (corresponds to 65 F)
        water_density = 998.2  # kg/m3
        water_specheat = 4180.0  # J/kgK

        # Calculate expected result assuming timestep = 1 h
        term1 = UnitConv(
            V_draw
            * water_density
            * water_specheat
            * (T_setpoint - T_feed)
            / tank_re
        ).Wh_J(unit_in="J")
        term2 = 1.0 - (
            tank_U * tank_A * (T_setpoint - T_amb) / tank_input_power
        )
        term3 = tank_U * tank_A * (T_setpoint - T_amb)
        result = (term1 * term2) + term3

        self.assertAlmostEqual(
            self.tank._gas_tank_wh(
                Q_nom=tank_input_power,
                V_draw=V_draw,
                tank_V=tank_V,
                tank_A=tank_A,
                tank_U=tank_U,
                tank_re=tank_re,
                T_set=T_setpoint,
                T_feed=T_feed,
                T_amb=T_amb,
                water_density=water_density,
                water_specheat=water_specheat,
            )[1],
            result,
            places=5,
        )

    def test_gas_tank_wh(self):
        """Tests instantiation with db extracted and default parameters.
        Validates the model using 2010 energy conservation standard analysis
        for household water heaters
        (https://www.regulations.gov/docket?D=EERE-2006-STD-0129).
        """
        # read in input db
        weather_db_path = os.path.join(
            os.getcwd(), "mswh/comm/weather_and_loads.db"
        )

        db = Sql(weather_db_path)

        try:
            # read table names for all tables in a
            # {table name : sheet name} form
            inputs = db.tables2dict(close=True)
        except:
            msg = "Failed to read input tables from {}."
            log.error(msg.format(inpath))

        # validation

        # generate a test load profile
        occ = [2]
        at_home = ["n"]

        (
            hourly_load_df,
            loadid_peakload,
        ) = SourceAndSink._make_example_loading_inputs(
            inputs, self.c, self.random_state, occupancy=occ, at_home=at_home
        )

        # scale the test load profile to match the reference data:
        # average hourly draw of 35.7 gal/day
        rule_draw_per_day_m3 = UnitConv(35.7).m3_gal(unit_in="gal")

        hourly_m3 = (
            hourly_load_df["End-Use Load"].values[0]
            * (rule_draw_per_day_m3 * 365)
            / hourly_load_df["End-Use Load"].values[0].sum()
        )

        # create reference hourly temperature profiles
        df_T = pd.DataFrame(
            {
                "water_main_t_F": [61.4, 51.8, 66.6, 46.2],
                "t_around_tank_F": [70.3, 70.3, 71.1, 70.3],
                "season": ["fall", "spring", "summer", "winter"],
            }
        )

        df_seasons = pd.DataFrame(
            [
                "winter",
                "winter",
                "spring",
                "spring",
                "spring",
                "summer",
                "summer",
                "summer",
                "fall",
                "fall",
                "fall",
                "winter",
            ],
            index=range(1, 13),
            columns=["season"],
        )

        df_seasons["month"] = df_seasons.index
        seasons_and_temps = df_seasons.merge(df_T, on="season", how="left")

        # get hourly month column from the weather data
        # (climate zone is just a placeholder)
        month_index_hourly = pd.DataFrame()
        month_index_hourly["month"] = SourceAndSink(
            input_dfs=inputs
        ).irradiation_and_water_main("16", method="isotropic diffuse")["month"]

        temps = month_index_hourly.merge(
            seasons_and_temps, on="month", how="left"
        )

        # convert units
        average_T_feed = (
            UnitConv(temps.water_main_t_F).degF_degC(unit_in="degF") + 273.15
        )
        T_around_tank = (
            UnitConv(temps.t_around_tank_F).degF_degC(unit_in="degF") + 273.15
        )

        # set up a tank

        # conventional gas tank water heater: T_set is 138 degF,
        # tank size is 30 gal.
        # U value parameters (insulation thickness and specific
        # heat conductivity of tank walls) is equivalent to
        # UA = 7.45 Btu/(h*degF) ==> 2.7 W/m2K for 30 gal tank
        # with the default height radius ratio
        params_gas_tank_wh = pd.DataFrame(
            data=[
                [self.s["gas_tank"], self.s["tank_re"], 0.76],
                [self.s["gas_tank"], self.s["ins_thi"], 0.03],
                [self.s["gas_tank"], self.s["spec_hea_con"], 0.081],
                [self.s["gas_tank"], self.s["t_tap_set"], 332.0389],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        size_gas_tank_wh = pd.DataFrame(
            data=[[self.s["gas_tank"], UnitConv(30).m3_gal()]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        self.conv_tank = Storage(
            params=params_gas_tank_wh, size=size_gas_tank_wh, type="wham_tank"
        )

        # get annual water heater energy use [kWh]
        annual_kwh_model = (
            self.conv_tank.gas_tank_wh(
                V_draw=hourly_m3, T_feed=average_T_feed, T_amb=T_around_tank
            )[self.r["gas_use"]].sum()
            / 1000.0
        )

        # compare modeled and reference energy use result
        annual_kwh_reference = 4629.0  # kWh

        # check if model result is within 10% of the reference value
        err = annual_kwh_reference - annual_kwh_model
        rel_err = abs(err / annual_kwh_reference)

        self.assertTrue(rel_err < 0.1)

        # test if a tank can be initiated with default values
        default_gas_tank = Storage(type="wham_tank")

        self.assertAlmostEqual(
            default_gas_tank.gas_tank_wh(
                V_draw=hourly_m3, T_feed=average_T_feed, T_amb=T_around_tank
            )[self.r["gas_use"]].sum()
            / 1000.0,
            3360.12,
            places=2,
        )

    def test_thermal_tank(self):
        """Tests as a solar thermal tank"""
        res_default = self.tank.thermal_tank()
        res_no_gain = self.tank.thermal_tank(pre_Q_in=0.0)

        self.assertTrue(
            res_default[self.r["t_tank_up"]] > res_no_gain[self.r["t_tank_up"]]
        )

        res_no_gain_and_colder_than_set = self.tank.thermal_tank(
            pre_T_upper=310.15, pre_T_lower=305.15, pre_Q_in=0.0
        )

        self.assertAlmostEqual(
            res_default[self.r["q_del_tank"]],
            res_no_gain[self.r["q_del_tank"]]
            + res_no_gain[self.r["q_unmet_tank"]],
            places=5,
        )

        # tests parameter extraction, includes the distribution
        params_the_sto = pd.DataFrame(
            data=[
                [self.s["the_sto"], self.s["f_upper_vol"], 0.5],
                [self.s["the_sto"], self.s["ins_thi"], 0.085],
                [self.s["the_sto"], self.s["spec_hea_con"], 0.04],
                [self.s["the_sto"], self.s["t_tap_set"], 322.04],
                [self.s["the_sto"], self.s["h_vs_r"], 6.0],
                [self.s["the_sto"], self.s["dt_appr"], 2.0],
                [self.s["the_sto"], self.s["t_max_tank"], 344.15],
                [self.s["the_sto"], self.s["eta_coil"], 0.84],
                [self.s["piping"], self.s["pipe_spec_hea_con"], 0.0175],
                [self.s["piping"], self.s["pipe_ins_thick"], 0.008],
                [self.s["piping"], self.s["flow_factor"], 0.5],
                [self.s["piping"], self.s["dia_len_exp"], 0.5],
                [
                    self.s["piping"],
                    self.s["dia_len_sca"],
                    0.007332348418708248,
                ],
                [
                    self.s["piping"],
                    self.s["discr_diam_m"],
                    "[0.0127, 0.01905, 0.0254, 0.03175, 0.0381, 0.0508, 0.0635, 0.0762, 0.1016]",
                ],
                [self.s["piping"], self.s["circ"], False],
                [self.s["piping"], self.s["long_br_len_fr"], 1.0],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        size_the_sto = pd.DataFrame(
            data=[
                [self.s["the_sto"], UnitConv(30).m3_gal()],
                [self.s["piping"], 20.0],
            ],
            columns=[self.s["comp"], self.s["cap"]],
        )

        the_sto = Storage(
            params=params_the_sto, size=size_the_sto, type="sol_tank"
        )

        passing_params_in = the_sto.thermal_tank(
            pre_T_upper=310.15, pre_T_lower=305.15, pre_Q_in=0.0
        )

        self.assertDictEqual(
            passing_params_in, res_no_gain_and_colder_than_set
        )

    def test_heat_pump_tank(self):
        """Tests thermal storage as a heat pump tank"""
        the_sto_params = pd.DataFrame(
            data=[
                [self.s["the_sto"], self.s["f_upper_vol"], 0.5],
                [self.s["the_sto"], self.s["ins_thi"], 0.085],
                [self.s["the_sto"], self.s["spec_hea_con"], 0.04],
                [self.s["the_sto"], self.s["f_upper_vol"], 0.5],
                [self.s["the_sto"], self.s["h_vs_r"], 2.56],
                [self.s["the_sto"], self.s["dt_appr"], 2.0],
                [self.s["the_sto"], self.s["t_tap_set"], 322.04],
                [self.s["the_sto"], self.s["t_max_tank"], 333.15],
                [self.s["piping"], self.s["pipe_spec_hea_con"], 0.0175],
                [self.s["piping"], self.s["pipe_ins_thick"], 0.008],
                [self.s["piping"], self.s["flow_factor"], 0.5],
                [self.s["piping"], self.s["dia_len_exp"], 0.5],
                [
                    self.s["piping"],
                    self.s["dia_len_sca"],
                    0.007332348418708248,
                ],
                [
                    self.s["piping"],
                    self.s["discr_diam_m"],
                    "[0.0127, 0.01905, 0.0254, 0.03175, 0.0381, 0.0508, 0.0635, 0.0762, 0.1016]",
                ],
                [self.s["piping"], self.s["circ"], False],
                [self.s["piping"], self.s["long_br_len_fr"], 1.0],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        size_the_sto = pd.DataFrame(
            data=[
                [self.s["the_sto"], UnitConv(80).m3_gal()],
                [self.s["piping"], 20.0],
            ],
            columns=[self.s["comp"], self.s["cap"]],
        )

        the_sto = Storage(
            params=the_sto_params, size=size_the_sto, type="hp_tank"
        )  # .302833 m3

        res = the_sto.thermal_tank(
            pre_T_amb=293.15,  # 20 degC
            pre_T_feed=291.15,  # 18 degC
            pre_T_upper=321.15,  # 48 degC
            pre_T_lower=320.15,  # 47 degC
            pre_V_tap=0.00757,
            pre_Q_in=2350.0,
        )  # heat cap of unit A of NRELs heat pump\
        # performance analysis document

        # for key, val in res.items():
        #     print("{} : {}".format(key, val) )

        self.assertAlmostEqual(
            (res[self.r["q_dem_tot"]] - res[self.r["q_dem"]]),
            res[self.r["q_dist_loss"]],
            2,
        )


class DistributionTests(unittest.TestCase):
    """Unit tests for the distribution component models."""

    @classmethod
    def setUp(self):
        """Setup"""
        self.s = SwhLabels().set_prod_labels()

    def test__dc_to_ac(self):
        """Check dc to ac losses"""
        total_conv_eff = 0.8
        in_power = 1000.0

        self.assertTrue(
            Distribution._dc_to_ac(in_power, conv_eff=total_conv_eff),
            total_conv_eff * in_power,
        )

    def test_pipe_losses(self):
        """Pipe losses method with parameters from database"""
        # tests parameter extraction
        params_pipes = pd.DataFrame(
            data=[
                [self.s["piping"], self.s["pipe_spec_hea_con"], 0.0175],
                [self.s["piping"], self.s["pipe_ins_thick"], 0.008],
                [self.s["piping"], self.s["flow_factor"], 0.5],
                [self.s["piping"], self.s["dia_len_exp"], 0.5],
                [
                    self.s["piping"],
                    self.s["dia_len_sca"],
                    0.007332348418708248,
                ],
                [
                    self.s["piping"],
                    self.s["discr_diam_m"],
                    "[0.0127, 0.01905, 0.0254, 0.03175, 0.0381, 0.0508, 0.0635, 0.0762, 0.1016]",
                ],
                [self.s["piping"], self.s["circ"], False],
                [self.s["piping"], self.s["long_br_len_fr"], 1.0],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        sizes_pipes = pd.DataFrame(
            data=[[self.s["piping"], 20.0]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        res = Distribution(
            params=params_pipes, sizes=sizes_pipes
        ).pipe_losses()

        self.assertAlmostEqual(res["heat_rate"], 294.3, places=2)
        self.assertAlmostEqual(res["heat_loss"], 48.6, places=2)
        self.assertAlmostEqual(res["dt_dist"], 0.84, places=2)

    def test__pipe_losses(self):
        """Pipe losses"""
        length1 = 20.0
        length2 = 10.0

        (
            loss_heat_rate1,
            heat_loss1,
            dT_drop1,
            flow_on_frac1,
        ) = Distribution()._pipe_losses(
            T_in=333.15,
            T_amb=293.15,
            length=length1,
            diameter=0.0381,
            insul_thickness=0.008,
            spec_hea_cond=0.0175,
            V_tap=0.05,
            max_V_tap=0.1514,
            flow_factor=0.8,
            circulation=False,
            longest_branch_length_ratio=None,
        )

        (
            loss_heat_rate2,
            heat_loss2,
            dT_drop2,
            flow_on_frac2,
        ) = Distribution()._pipe_losses(
            T_in=333.15,
            T_amb=293.15,
            length=length2,
            diameter=0.0381,
            insul_thickness=0.008,
            spec_hea_cond=0.0175,
            V_tap=0.05,
            max_V_tap=0.1514,
            flow_factor=0.8,
            circulation=False,
            longest_branch_length_ratio=None,
        )

        self.assertAlmostEqual(heat_loss1 - heat_loss2, 38.30, places=2)
        self.assertAlmostEqual(
            loss_heat_rate1 - loss_heat_rate2, 144.98, places=2
        )

        # with branches
        (
            loss_heat_rate1_branches,
            heat_loss1_branches,
            dT_drop1_branches,
            flow_on_frac1_branches,
        ) = Distribution()._pipe_losses(
            T_in=333.15,
            T_amb=293.15,
            length=length1,
            diameter=0.0381,
            insul_thickness=0.008,
            spec_hea_cond=0.0175,
            V_tap=0.05,
            max_V_tap=0.1514,
            flow_factor=0.8,
            circulation=False,
            longest_branch_length_ratio=0.5,
        )

        self.assertAlmostEqual(dT_drop1 - dT_drop1_branches, 0.66, places=2)

        # with circulation
        (
            loss_heat_rate1_circ,
            heat_loss1_circ,
            dT_drop1_circ,
            flow_on_frac1_circ,
        ) = Distribution()._pipe_losses(
            T_in=333.15,
            T_amb=293.15,
            length=length1,
            diameter=0.0381,
            insul_thickness=0.008,
            spec_hea_cond=0.0175,
            V_tap=0.05,
            max_V_tap=0.1514,
            flow_factor=0.8,
            circulation=1.0,
            longest_branch_length_ratio=None,
        )

        # since test timestep is 1
        self.assertEqual(heat_loss1_circ, loss_heat_rate1_circ)

        self.assertTrue(heat_loss1 < heat_loss1_circ)

        self.assertEqual(dT_drop1_circ, dT_drop1)

        self.assertEqual(flow_on_frac1_circ, 1.0)

    def test__pipe_loss_rate(self):
        """Pipe losses"""
        length1 = 20.0
        length2 = 10.0

        loss_rate1 = Distribution._pipe_loss_rate(length=length1)
        loss_rate2 = Distribution._pipe_loss_rate(length=length2)

        self.assertAlmostEqual(loss_rate1, loss_rate2 * 2, places=2)

    def test_pump(self):
        """Tests pump model"""
        # tests parameter extraction
        params_pumps = pd.DataFrame(
            data=[
                [self.s["sol_pump"], self.s["eta_sol_pump"], 0.8],
                [self.s["dist_pump"], self.s["eta_dist_pump"], 0.85],
            ],
            columns=[self.s["comp"], self.s["param"], self.s["param_value"]],
        )

        sizes_pumps = pd.DataFrame(
            data=[[self.s["sol_pump"], 40], [self.s["dist_pump"], 80]],
            columns=[self.s["comp"], self.s["cap"]],
        )

        pump_modeler = Distribution(params=params_pumps, sizes=sizes_pumps)

        sol_pump_en_use_array, sol_pump_en_use_total = pump_modeler.pump(
            role="solar"
        )
        dist_pump_en_use_array, dist_pump_en_use_total = pump_modeler.pump(
            role="distribution"
        )

        self.assertAlmostEqual(
            sol_pump_en_use_total / dist_pump_en_use_total,
            (
                sizes_pumps.at[0, self.s["cap"]]
                / params_pumps.at[0, self.s["param_value"]]
            )
            / (
                sizes_pumps.at[1, self.s["cap"]]
                / params_pumps.at[1, self.s["param_value"]]
            ),
            places=2,
        )

    def test__pump(self):
        """Tests stand alone pump model"""
        distrib = Distribution()

        P_nom = 45.0
        eta_nom = 0.7
        on_array = np.ones(8760)
        plr = 1.0

        # Using total operation time
        en_use_array = P_nom * np.ones(8760) * plr / eta_nom
        en_use_total = en_use_array.sum()

        self.assertAlmostEqual(
            en_use_total,
            distrib._pump(P_nom=P_nom, eta_nom=eta_nom, on_array=on_array)[1],
            places=1.0,
        )
