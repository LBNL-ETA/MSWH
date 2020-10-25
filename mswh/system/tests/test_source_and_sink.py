import logging
import os
import unittest

import numpy as np
import pandas as pd

from mswh.comm.sql import Sql
from mswh.system.source_and_sink import SourceAndSink
from mswh.comm.label_map import SwhLabels

logging.basicConfig(level=logging.DEBUG)


class SourceAndSinkTests(unittest.TestCase):
    """Tests some of the functionality of the
    SourceAndSink class methods. Parts of the
    functionality are tested in test_analysis
    or test_draw_model test modules.
    """

    @classmethod
    def setUp(self):
        """Instantiates a test object"""
        # read in data from the database
        # assuming tests are run from swh
        # directory
        weather_db_path = os.path.join(
            os.getcwd(), "mswh/comm/mswh_system_input.db"
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

        # get labels
        self.c = SwhLabels().set_hous_labels()

    def test_irradiation_and_water_main(self):
        """Tests a day of irradiation on a tilted
        surface data in hot, mild, and cold
        climate zones.
        """
        # Cold climate, CZ16 (Blue Canyon), Jan 15

        # method 1: HDKR anisotropic sky

        cold = self.weather.irradiation_and_water_main(
            "16", method="HDKR anisotropic sky"
        )

        check_indices = (cold[self.c["month"]] == 1) & (
            cold[self.c["day"]] == 15
        )

        # expected result
        cold_irrad_on_tilt = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                3.62615245,
                349.78144662,
                601.93687406,
                823.2893731,
                898.07605806,
                927.52023249,
                825.36501459,
                714.4711444,
                463.85830573,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

        self.assertTrue(
            (
                cold.loc[check_indices, self.c["irrad_on_tilt"]].values.round(
                    5
                )
                == cold_irrad_on_tilt.round(5)
            ).all()
        )

        # method 2: isotropic diffuse
        cold = self.weather.irradiation_and_water_main(
            "16", method="isotropic diffuse"
        )

        # expected result
        cold_irrad_on_tilt = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                3.62615245,
                320.74657179,
                556.5606902,
                758.11329043,
                839.68165729,
                856.18368971,
                761.1499109,
                654.44447952,
                404.44499493,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

        self.assertTrue(
            (
                cold.loc[check_indices, self.c["irrad_on_tilt"]].values.round(
                    5
                )
                == cold_irrad_on_tilt.round(5)
            ).all()
        )

        # Mild climate, CZ03, Oakland, Sep 15

        # method 1: HDKR anisotropic sky
        mild = self.weather.irradiation_and_water_main(
            "03", method="HDKR anisotropic sky"
        )

        check_indices = (mild[self.c["month"]] == 9) & (
            mild[self.c["day"]] == 15
        )

        # expected result
        mild_irrad_on_tilt = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                20.97839,
                84.83442,
                298.0112,
                641.07024,
                814.68078,
                871.40743,
                670.20769,
                830.07588,
                719.7384,
                543.90547,
                333.02575,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

        self.assertTrue(
            (
                mild.loc[check_indices, self.c["irrad_on_tilt"]].values.round(
                    5
                )
                == mild_irrad_on_tilt.round(5)
            ).all()
        )

        # method 2: isotropic diffuse
        mild = self.weather.irradiation_and_water_main(
            "03", method="isotropic diffuse"
        )

        # expected result
        mild_irrad_on_tilt = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                20.97839,
                84.83442,
                288.16882,
                611.68563,
                776.70808,
                827.89875,
                638.56434,
                789.2915,
                689.46817,
                519.90061,
                318.61377,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

        self.assertTrue(
            (
                mild.loc[check_indices, self.c["irrad_on_tilt"]].values.round(
                    5
                )
                == mild_irrad_on_tilt.round(5)
            ).all()
        )

        # Hot climate, CZ14, Palmdale, Jul 15

        # method 1: HDKR anisotropic sky
        hot = self.weather.irradiation_and_water_main(
            "14", method="HDKR anisotropic sky"
        )

        check_indices = (hot[self.c["month"]] == 7) & (
            hot[self.c["day"]] == 15
        )

        # expected result
        hot_irrad_on_tilt = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                123.27177,
                350.68287,
                575.31534,
                770.49835,
                904.73286,
                953.94699,
                979.061,
                852.59577,
                744.13851,
                547.8981,
                335.91189,
                140.80723,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

        self.assertTrue(
            (
                hot.loc[check_indices, self.c["irrad_on_tilt"]].values.round(5)
                == hot_irrad_on_tilt.round(5)
            ).all()
        )

        # method 2: isotropic diffuse
        hot = self.weather.irradiation_and_water_main(
            "14", method="isotropic diffuse"
        )

        # expected result
        hot_irrad_on_tilt = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                134.4729,
                357.8465,
                578.28188,
                770.22842,
                902.17976,
                948.46886,
                975.20171,
                848.14553,
                743.9827,
                552.66091,
                347.66338,
                163.67964,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

        self.assertTrue(
            (
                hot.loc[check_indices, self.c["irrad_on_tilt"]].values.round(5)
                == hot_irrad_on_tilt.round(5)
            ).all()
        )

        # Testing wet bulb temperature approximation
        # (only applicable for TMY3 weather data source)

        hot = self.weather.irradiation_and_water_main(
            "14", method="isotropic diffuse", weather_data_source="tmy3"
        )

        # expected result
        wet_bulb_C = np.array(
            [
                16.55206,
                16.3068,
                16.21351,
                16.17312,
                16.27864,
                16.68113,
                17.54151,
                18.2606,
                18.89111,
                19.62333,
                20.07855,
                20.7989,
                20.7989,
                20.7989,
                20.35101,
                20.13804,
                18.41353,
                17.82904,
                17.87381,
                16.50567,
                17.02224,
                17.04635,
                17.1384,
                16.71456,
            ]
        )

        self.assertTrue(
            (
                hot.loc[check_indices, self.c["t_wet_bulb_C"]].values.round(5)
                == wet_bulb_C.round(5)
            ).all()
        )
