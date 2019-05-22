import logging
import os
import unittest

import numpy as np
import pandas as pd

from mswh.tools.unit_converters import UnitConv, Utility

logging.basicConfig(level=logging.DEBUG)


class UnitConvTests(unittest.TestCase):
    """Unit conversion tests
    """

    def test_degF_degC(self):
        """Tests temperature conversion between degF and degC
        """
        # say we're using water
        t_degC_freeze = 0.
        t_degF_freeze = 32.

        # test to F
        self.assertAlmostEqual(
            UnitConv(t_degC_freeze).degF_degC(unit_in='degC'),
            t_degF_freeze,
            places=2)

        t_degC_boil = 100.
        t_degF_boil = 212.

        # test from F
        self.assertAlmostEqual(
            UnitConv(t_degF_boil).degF_degC(unit_in='degF'),
            t_degC_boil,
            places=2)

    def test_degC_K(self):
        """Tests temperature conversion between degC and K
        """
        # say we're using water
        t_degC_freeze = 0.
        t_K_freeze = 273.15

        # test to F
        self.assertAlmostEqual(
            UnitConv(t_degC_freeze).degC_K(unit_in='degC'),
            t_K_freeze,
            places=2)

        t_degC_boil = 100.
        t_K_boil = 373.15

        # test from F
        self.assertAlmostEqual(
            UnitConv(t_K_boil).degC_K(unit_in='K'),
            t_degC_boil,
            places=2)

    def test_m3_gal(self):
        """Tests volume conversion between m3 and gallon
        """

        v_m3 = .3785412
        v_gal = 100.

        # test to gal
        self.assertAlmostEqual(
            UnitConv(v_m3).m3_gal(unit_in='m3'),
            v_gal,
            places=2)

        # test to m3
        self.assertAlmostEqual(
            UnitConv(v_gal).m3_gal(unit_in='gal'),
            v_m3,
            places=2)

    def test_hp_W(self):
        """Tests power conversion between m3 and gallon
        """

        p_hp = 100.
        p_kW = 74.57

        # test to m3
        self.assertAlmostEqual(
            UnitConv(p_hp, scale_out='kilo').hp_W(unit_in='hp'),
            p_kW,
            places=2)

        # test to hp
        self.assertAlmostEqual(
            UnitConv(p_kW, scale_in='kilo').hp_W(unit_in='W'),
            p_hp,
            places=2)

    def test_Btu_J(self):
        """Tests work / energy / heat content conversion between Btu and joule
        """

        e_MMBtu = 2.
        e_GJ = 2. * 1.055056

        # test to GJ
        self.assertAlmostEqual(
            UnitConv(
                e_MMBtu,
                scale_in='MM',
                scale_out='G').Btu_J(unit_in='Btu'),
            e_GJ,
            places=2)

        # test to MMBtu
        self.assertAlmostEqual(
            UnitConv(
                e_GJ,
                scale_in='G',
                scale_out='MM').Btu_J(unit_in='J'),
            e_MMBtu,
            places=2)

    def test_therm_J(self):
        """Tests work / energy / heat content conversion between therm
        and joule
        """

        e_therm = 2.
        e_MJ = 211.

        # test to MJ
        self.assertAlmostEqual(
            UnitConv(
                e_therm,
                scale_out='M').therm_J(unit_in='therm'),
            e_MJ,
            places=2)

        # test to therm
        self.assertAlmostEqual(
            UnitConv(
                e_MJ,
                scale_in='M').therm_J(unit_in='J'),
            e_therm,
            places=2)

    def test_Wh_J(self):
        """Tests work / energy / heat content conversion
        """

        e_Wh = 1.
        e_J = 3600.

        self.assertAlmostEqual(
            UnitConv(e_Wh).Wh_J(unit_in='Wh'),
            e_J,
            places=2)

        self.assertAlmostEqual(
            UnitConv(e_J).Wh_J(unit_in='J'),
            e_Wh,
            places=2)

    def test_m3perh_m3pers(self):
        """Tests volume flow conversion
        """

        flow_m3perh = 3600.
        flow_m3pers = 1.

        self.assertAlmostEqual(
            UnitConv(flow_m3perh).m3perh_m3pers(unit_in='m3perh'),
            flow_m3pers,
            places=2)

        self.assertAlmostEqual(
            UnitConv(flow_m3pers).m3perh_m3pers(unit_in='m3pers'),
            flow_m3perh,
            places=2)

    def test_sqft_m2(self):
        """Tests area conversion
        """

        area_sqft = 1.
        area_m2 = 0.3048**2

        self.assertAlmostEqual(
            UnitConv(area_sqft).sqft_m2(unit_in='sqft'),
            area_m2,
            places=2)

        self.assertAlmostEqual(
            UnitConv(area_m2).sqft_m2(unit_in='m2'),
            area_sqft,
            places=2)

    def test_ft_m(self):
        """Tests length conversion
        """

        length_sqft = 1.
        length_m2 = 0.3048

        self.assertAlmostEqual(
            UnitConv(length_sqft).ft_m(unit_in='ft'),
            length_m2,
            places=2)

        self.assertAlmostEqual(
            UnitConv(length_m2).ft_m(unit_in='m'),
            length_sqft,
            places=2)


class UtilityTests(unittest.TestCase):
    """Gas and electricity consumption conversion tests
    """
    def test_gas(self):
        """Tests gas consumption conversion
        """
        gas_use_in_kJ = 1000000.
        gas_use_in_MMBtu = 0.9478169
        gas_use_in_therm = 9.47867
        gas_use_in_m3 = 26.3157894

        gas_use_in_kWh = 277.7778
        gas_use_in_cf = 929.23

        self.assertAlmostEqual(
            Utility(gas_use_in_kJ).gas(unit_out='MMBtu'),
            gas_use_in_MMBtu,
            places=5)

        self.assertAlmostEqual(
            Utility(gas_use_in_kJ).gas(unit_out='therm'),
            gas_use_in_therm,
            places=5)

        self.assertAlmostEqual(
            Utility(gas_use_in_kJ).gas(unit_out='m3'),
            gas_use_in_m3,
            places=5)

        self.assertAlmostEqual(
            Utility(gas_use_in_kWh).gas(unit_in='kWh', unit_out='cf'),
            gas_use_in_cf,
            places=2)
