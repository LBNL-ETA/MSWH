import calendar
import csv
import datetime
import logging
import os

import numpy as np
import pandas as pd

from mswh.tools.unit_converters import UnitConv

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SourceAndSink(object):
    """Generates timeseries that are inputs to the simulation
    model and are known prior to the simulation, such as
    outdoor air temperature and end use load profiles.

    Parameters:

        input_dfs: a dict of pd dfs
            Dictionary of input dataframes
            as read in from the input db by the :func:`Sql <Sql>` class
            (see example in :func:`test_source_and_sink.SourceAndSinkTests.setUp <test_source_and_sink.SourceAndSinkTests.setUp>`)

        random_state: numpy random state object or an integer
             numpy random state object : if there is a need
             to maintain the same random seed throughout the
             analysis.

             integer : a new random state object gets
             instanteated at init
    """
    def __init__(self, input_dfs=None, random_state=123):

        self.data = input_dfs

        # define the random state object which enbles random draw
        # repeatability
        if isinstance(random_state, int):
            msg = 'The user did not provide a numpy random state ' \
                   'object. Initiating one with a provided or default' \
                   ' seed value = {}.'
            log.info(msg.format(random_state))
            self.random_state = np.random.RandomState(random_state)
        else:
            self.random_state = random_state


    def irradiation_and_water_main(self,
                                   climate_zone,
                                   collector_tilt='latitude',
                                   tilt_standard_deviation=None,
                                   collector_azimuth=0.,
                                   azimuth_standard_deviation=None,
                                   location_ground_reflectance=0.16,
                                   solar_constant_Wm2=1367.,
                                   method='isotropic diffuse',
                                   weather_data_source='cec',
                                   single_row_with_arrays = False):
        """Calculates the hourly total incident radiation on a tilted surface
        for any climate zone in California. If weather data from the provided
        database are passed as `input_dfs`, the user can specify a single
        climate.

        Two separate methods are available for use, with all equations
        (along with the equation numbers provided in comments) as provided in
        J. A. Duffie and W. A. Beckman, Solar engineering of thermal
        processes, 3rd ed. Hoboken, N.J: Wiley, 2006.

        Parameters:

            climate_zone: string
                String of two digits to indicate the CEC climate zone
                being analyzed ('01' to '16').

            collector_azimuth: float, default: 0.
                The deviation of the projection on a horizontal
                plane of the normal to the collector surface from
                the local meridian, in degrees.  Allowable values
                are between +/- 180 degrees (inclusive).  0 degrees
                corresponds to due south, east is negative, and west
                is positive.  Default value is 0 degrees (due south).

            azimuth_standard_deviation: float, default: 'None'
                Final collector azimuth is a value drawn using a normal
                distribution around the collector_azimuth value
                with a azimuth_standard_deviation standard deviation.
                If set to 'None' the final collector azimuth
                equals collector_azimuth

            collector_tilt: float, default: 'latitude'
                The angle between the plane of the collector and the
                horizontal, in degrees.  Allowable values are between
                0 and 180 degrees (inclusive), and values greater than
                90 degrees mean that the surface has a downward-facing
                component. If a default flag is left unchanged, the code
                will assign latitude value to the tilt as a good
                approximation of a design collector or PV tilt.

            tilt_standard_deviation: float, default: 'None'
                Final collector tilt is a value drawn using a normal
                distribution around the collector_tilt value
                with a tilt_standard_deviation standard deviation.
                If set to 'None' the final collector tilt
                equals collector_tilt

            location_ground_reflectance: float, default: 0.16
                The degree of ground reflectance.  Allowable
                values are 0-1 (inclusive), with 0 meaning
                no reflectance and 1 meaning very high
                reflectance.  For reference, fresh snow has
                a high ground reflectance of ~ 0.7.  Default
                value is 0.16, which is the annual average surface
                albedo averaged across the 16 CEC climate zones.

            method: string, default: 'HDKR anisotropic sky'
                Calculation method to use for estimating the total irradiance
                on the tilted collector surface. See notes below. Default
                value is 'HDKR anisotropic sky.'

            solar_constant_Wm2: float, default: 1367.
                Energy from the sun per unit time received on a unit
                area of surface perpendicular to the direction of
                propagation of the radiation at mean earth-sun distance
                outside the atmosphere.  Default value is 1367 W/m^2.

            weather_data_source: string, default: 'cec'
                The type of weather data being used to analyze the
                climate zone for solar insolation.  Allowable values
                are 'cec' and 'tmy3.'  Default value is 'cec.'

            single_row_with_arrays : boolean
                A flag to reformat the resulting dataframe in a row
                of data where each resulting 8760 is stored as an
                array

        Returns:

            data: pd df
                  Weather data frame with appended columns:
                  'global_tilt_radiation_Wm2', 'water_main_t_F',
                  'water_main_t_C', 'dry_bulb_C', 'wet_bulb_C', 'Tilt',
                  'Azimuth']

        Notes:

            The user can select one of two methods to use for
            this calculation:

            1) 'isotropic diffuse':
                   This model was derived by Liu and Jordan (1963).
                   All diffuse radiation is assumed to be isotropic.
                   It is the simpler and more conservative model,
                   and it has been widely used.

            2) 'HDKR anisotropic sky':
                   This model combined methods from Hay and Davies (1980),
                   Klucher (1979), and Reindl, et al. (1990).
                   Diffuse radiation in this model is represented in two
                   parts: isotropic and circumsolar. The model also accounts
                   for horizon brightening.
                   This is also a simple model, but it has been found to be
                   slightly more accurate (and less conservative) than the
                   'isotropic diffuse' model.  For collectors tilted toward
                   the equator, this model is suggested.
        """
        # Read in CEC weather data
        # Ensure climate_zone is a string and has a leading '0,' if needed
        climate_zone = str(climate_zone)

        if len(climate_zone) == 1:
            climate_zone = '0' + climate_zone

        # There are only 16 climate zones in CA, so ensure a valid zone
        # is provided.
        try:
            climate_zone_int = int(climate_zone)
        except:
            msg = 'Climate zone value ({}) is not a number.  Please' \
            ' ensure the climate zone is a number from 1-16, represented' \
            ' as a string.'
            log.error(msg.format(climate_zone))
            raise ValueError

        if (climate_zone_int > 16) | (climate_zone_int < 1):
            msg = 'Climate zone must be a number from 1-16.'
            log.error(msg)
            raise ValueError

        # draw azimuth value from a distribution if standard
        # deviation provided
        if azimuth_standard_deviation:
            azimuth_mean = collector_azimuth
            collector_azimuth = self.random_state.normal(
                azimuth_mean,
                azimuth_standard_deviation)

        # Ensure collector_azimuth is between -180 (due east) and
        # +180 (due west)
        if (collector_azimuth > 180.) | (collector_azimuth < -180.):
            msg = 'Collector azimuth angle must be a number between' \
            ' -180 degrees (due east) and +180 degrees (due west).'
            log.error(msg)
            raise ValueError

        # Ensure location_ground_reflectance is between 0 and 1.
        if ((location_ground_reflectance > 1.)
            | (location_ground_reflectance < 0.)):
            msg = 'The annual average location ground reflectance must' \
            ' be a number between 0. (no reflectance) and 1 (perfect' \
            ' reflectance).'
            log.error(msg)
            raise ValueError

        # Ensure the provided solar constant is reasonable
        if ((solar_constant_Wm2 > 1450.) | (solar_constant_Wm2 < 1300.)):
            msg = 'The accepted solar constant is near 1367. W/m^2.' \
            ' Please select a reasonable solar constant value that is' \
            ' between 1300. and 1450. W/m^2.'
            log.error(msg)
            raise ValueError

        # Ensure selected method type is valid
        if ((method != 'isotropic diffuse') &
            (method != 'HDKR anisotropic sky')):
            msg = 'This model only calculated results for two models:' \
            ' \'isotropic diffuse\' and \'HDKR anisotropic sky\'.'
            log.error(msg)
            raise ValueError

        # Read in header data to get latitude and longitude of given
        # climate zone
        if weather_data_source == 'cec':

            key = 'CTZ' + climate_zone + 'S13b'
            header = pd.DataFrame(
                data=self.data[key].iloc[:20, :2])
            header_data = pd.Series(
                data=header.iloc[:,1].values,
                index=header.iloc[:,0])
            # latitude in degrees, north = positive
            latitude = float(header_data['Latitude'])
            # longitude in degrees, west = positive
            longitude = abs(float(header_data['Longitude']))


        elif weather_data_source == 'tmy3':

            # Map CEC climate zone to proper tmy3 weather file
            climate_zone_to_tmy3 = {
                '01': '725945',
                '02': '724957',
                '03': '724930',
                '04': '724945',
                '05': '723940',
                '06': '722970',
                '07': '722900',
                '08': '722976',
                '09': '722880',
                '10': '722869',
                '11': '725910',
                '12': '724830',
                '13': '723890',
                '14': '723820',
                '15': '722868',
                '16': '725845'
            }

            key = climate_zone_to_tmy3[climate_zone] + 'TY'
            # latitude in degrees, north = positive
            latitude = float(self.data[key].iloc[0, 4])
            # longitude in degrees, west = positive
            longitude = abs(float(self.data[key].iloc[0, 5]))


        # set the tilt to latitude if no custom tilt got provided
        if collector_tilt == 'latitude':
            collector_tilt = latitude

        # check tilt data type
        elif not isinstance(collector_tilt, float):
            msg = 'Collector tilt value ({}) is neither a float nor' \
            ' \'latitude\'. Please use an allowed value.'
            log.error(msg.format(collector_tilt))
            raise ValueError

        # draw tilt value from a distribution if standard deviation provided
        if tilt_standard_deviation:
            tilt_mean = collector_tilt
            collector_tilt = self.random_state.normal(
                tilt_mean,
                tilt_standard_deviation)

        # Read in actual weather data for the given climate zone
        if weather_data_source == 'cec':

            key = 'CTZ' + climate_zone + 'S13b'
            solar_data = pd.DataFrame(
                data=self.data[key].iloc[26:, :].values,
                columns=self.data[key].iloc[25, :])

            solar_data.columns = [x.lower() for x in solar_data.columns]

            # deal with data formats as needed
            solar_data = solar_data.astype(float)
            solar_data[solar_data.columns[:3]] = \
                solar_data[solar_data.columns[:3]].astype(int)

            # Rename solar columns
            solar_data.rename(columns={
                'global horizontal radiation': 'global_horizontal_radiation_Wm2',
                'direct normal radiation': 'direct_normal_radiation_Wm2',
                'diffuse horiz radiation': 'diffuse_horizontal_radiation_Wm2'},
                inplace=True)
            # Convert solar units from Btu/hr/ft^2 to W/m^2
            solar_data.global_horizontal_radiation_Wm2 *= 3.15459075
            solar_data.direct_normal_radiation_Wm2 *= 3.15459075
            solar_data.diffuse_horizontal_radiation_Wm2 *= 3.15459075

            solar_data['climate_zone'] = climate_zone
            # The hour data from the CEC is for the end of the hour;
            # we're setting it to be the start of the hour
            solar_data.hour -= 1

        elif weather_data_source == 'tmy3':

            solar_data = self.data[key].iloc[2:, :]
            solar_data = solar_data.apply(pd.to_numeric, errors='ignore')
            solar_data.columns = self.data[key].iloc[1, :]

            solar_data.columns = [x.lower() for x in solar_data.columns]
            # Rename solar columns
            solar_data.rename(columns={
                'etr (w/m^2)': 'extraterrestrial_horizontal_radiation_Wm2',
                'etrn (w/m^2)': 'extraterrestrial_normal_radiation_Wm2',
                'ghi (w/m^2)': 'global_horizontal_radiation_Wm2',
                'dni (w/m^2)': 'direct_normal_radiation_Wm2',
                'dhi (w/m^2)': 'diffuse_horizontal_radiation_Wm2',
                'alb (unitless)': 'surface_albedo'},
                inplace=True)

            solar_data['month'] = solar_data.apply(
                lambda x: int(x['date (mm/dd/yyyy)'][:2]), axis=1)
            solar_data['day'] = solar_data.apply(
                lambda x: int(x['date (mm/dd/yyyy)'][3:5]), axis=1)
            solar_data['hour'] = solar_data.apply(
                lambda x: int(x['time (hh:mm)'][:2])-1, axis=1)

            # The TMY3 data contain surface albedo values that can be used
            # Ensure missing values (coded as -9900) are replaced with the
            # average of the available data
            solar_data.surface_albedo = np.where(
                solar_data.surface_albedo == -9900.0,
                np.nan,
                solar_data.surface_albedo)

            solar_data.surface_albedo = np.where(
                np.isnan(solar_data.surface_albedo),
                solar_data.surface_albedo.mean(),
                solar_data.surface_albedo)
            location_ground_reflectance = solar_data.surface_albedo.values

        solar_data['day_number_of_year'] = solar_data.apply(lambda x:
            datetime.datetime(2018, x.month, x.day).timetuple().tm_yday,
            axis=1)

        solar_data = self._add_season_column(solar_data)

        # Calculate solar time:
        # Solar time - standard time [minutes]= 4 *
        #     (longitude_standard - longitude_location) + E
        #    where: longitude_standard = 15 * (PST-GMT),
        # and PST-GMT is always -8 hours
        # Calculate E (equation of time, in minutes)
        B = (solar_data.day_number_of_year - 1) * 360. / 365. # Equation 1.4.2
        E_minutes = 229.2 * (0.000075 +
            (0.001868 * np.cos(B)) -
            (0.032077 * np.sin(B)) -
            (0.014615 * np.cos(2 * B)) -
            (0.04089 * np.sin(2 * B))) # Equation 1.5.3

        # REMEMBER: longitudes are in degrees West, meaning they should
        # both be positive here for California!
        minutes_to_add = (4. * ((15. * 8.) - longitude)) + E_minutes
        solar_time = solar_data.hour + minutes_to_add / 60. # in hours

        # Calculate the hour angle
        # hour_angle = 15 degrees per hour away from solar noon (12),
        # with morning being negative
        hour_angle_start = 15. * (solar_time - 12.)
        hour_angle_end = 15. * (solar_time + 1. - 12.)

        # Calculate the declination angle for the day (declination_angle)
        declination_angle = (180. / np.pi) * (0.006918 -
            (0.399912 * np.cos(np.radians(B))) +
            (0.070257 * np.sin(np.radians(B))) -
            (0.006758 * np.cos(2 * np.radians(B))) +
            (0.000907 * np.sin(2 * np.radians(B))) -
            (0.002697 * np.cos(3 * np.radians(B))) +
            (0.001480 * np.sin(3 * np.radians(B)))) # Equation 1.6.1b

        # Calculate the ratio of beam radiation to that on a horizontal
        # surface for the collector, averaged over the hour of consideration
        # (to avoid mathematical issues that can arise for hours in which
        # sunrise or sunset occurs)
        R_b_a = (
            (((np.sin(np.radians(declination_angle)) *
             np.sin(np.radians(latitude)) *
             np.cos(np.radians(collector_tilt))) -
            (np.sin(np.radians(declination_angle)) *
             np.cos(np.radians(latitude)) *
             np.sin(np.radians(collector_tilt)) *
             np.cos(np.radians(collector_azimuth)))) *
             np.radians(hour_angle_end - hour_angle_start)) +
            (((np.cos(np.radians(declination_angle)) *
             np.cos(np.radians(latitude)) *
             np.cos(np.radians(collector_tilt))) +
            (np.cos(np.radians(declination_angle)) *
             np.sin(np.radians(latitude)) *
             np.sin(np.radians(collector_tilt)) *
             np.cos(np.radians(collector_azimuth)))) *
            (np.sin(np.radians(hour_angle_end)) -
             np.sin(np.radians(hour_angle_start)))) -
            (np.cos(np.radians(declination_angle)) *
             np.sin(np.radians(collector_tilt)) *
             np.sin(np.radians(collector_azimuth)) *
            (np.cos(np.radians(hour_angle_end)) -
             np.cos(np.radians(hour_angle_start)))))
        R_b_b = (
            ((np.cos(np.radians(latitude)) *
              np.cos(np.radians(declination_angle))) *
             (np.sin(np.radians(hour_angle_end)) -
              np.sin(np.radians(hour_angle_start)))) +
            ((np.sin(np.radians(latitude)) *
              np.sin(np.radians(declination_angle))) *
             (np.radians(hour_angle_end - hour_angle_start))))
        R_b_ave = R_b_a / R_b_b # Equation 2.14.6


        # Calculate horizontal radiation in absense of atmosphere
        # (Equation 1.10.4, [J/m^2])
        if weather_data_source == 'cec':
            extraterrestrial_horizontal_radiation_Jm2 = (
                12. * 3600. / np.pi * solar_constant_Wm2 *
                (1. + 0.033 * np.cos(360. *
                 solar_data.day_number_of_year / 365.)) *
                ((np.cos(np.radians(latitude)) *
                  np.cos(np.radians(declination_angle)) *
                 (np.sin(np.radians(hour_angle_end)) -
                  np.sin(np.radians(hour_angle_start)))) +
                 (np.pi / 180. * (hour_angle_end - hour_angle_start) *
                  np.sin(np.radians(latitude)) *
                  np.sin(np.radians(declination_angle)))))
            # Convert to W/m^2 and ensure the values aren't less than 0.
            solar_data['extraterrestrial_horizontal_radiation_Wm2'] = (
                extraterrestrial_horizontal_radiation_Jm2 * 0.000277777778)
            solar_data.extraterrestrial_horizontal_radiation_Wm2 = np.where(
                solar_data.extraterrestrial_horizontal_radiation_Wm2 < 0.,
                0.,
                solar_data.extraterrestrial_horizontal_radiation_Wm2)

        # Calculate beam radiation on a horizontal plane
        solar_data['beam_horizontal_radiation_Wm2'] = (
            solar_data.global_horizontal_radiation_Wm2 -
            solar_data.diffuse_horizontal_radiation_Wm2)

        # Calculate total radiation on a tilted surface using the isotropic
        # diffuse model.
        if method == 'isotropic diffuse':
            solar_data['global_tilt_radiation_Wm2'] = (
                (solar_data.beam_horizontal_radiation_Wm2 * R_b_ave) +
                (solar_data.diffuse_horizontal_radiation_Wm2 * ((1 +
                 np.cos(np.radians(collector_tilt))) / 2.0)) +
                (solar_data.global_horizontal_radiation_Wm2 *
                 location_ground_reflectance * ((1 -
                 np.cos(np.radians(collector_tilt))) / 2.0)))
                 # Equation 2.15.1
        elif method == 'HDKR anisotropic sky':
            # Calculate the anisotropy index
            anisotropy_index = (solar_data.beam_horizontal_radiation_Wm2 /
            solar_data.extraterrestrial_horizontal_radiation_Wm2)
            # Equation 2.16.3
            # Calculate the modulating factor, f
            f = (solar_data.beam_horizontal_radiation_Wm2 /
                solar_data.global_horizontal_radiation_Wm2) ** 0.5
                # Equation 2.16.6
            solar_data['global_tilt_radiation_Wm2'] = (
                ((solar_data.beam_horizontal_radiation_Wm2 +
                (solar_data.diffuse_horizontal_radiation_Wm2 *
                 anisotropy_index)) *
                R_b_ave) + (solar_data.diffuse_horizontal_radiation_Wm2 *
                (1 - anisotropy_index) *
                ((1 + np.cos(np.radians(collector_tilt))) / 2.0)
                * (1 + (f * (np.sin(np.radians(collector_tilt / 2.0)) **
                3)))) +
                (solar_data.global_horizontal_radiation_Wm2 *
                location_ground_reflectance *
                ((1 - np.cos(np.radians(collector_tilt))) / 2.0)))
                # Equation 2.16.7

        # You can't get negative energy collection
        # It's also probably unreasonable to expect > 2000 W/m^2
        # In comparisons with PVWatts results, when our model predicts
        # > 2000 W/m^2, it is due to a mathematical
        # anomaly where the actual result should be closer to 0.
        solar_data.global_tilt_radiation_Wm2 = np.where(
            (solar_data.global_tilt_radiation_Wm2 < 0.) |
            (solar_data.global_tilt_radiation_Wm2 >= 2000.),
            0.,
            solar_data.global_tilt_radiation_Wm2)

        # To avoid NaNs and other weird values, set the result to 0 if global
        # and diffuse horizontal are both 0
        solar_data.global_tilt_radiation_Wm2 = np.where(
            (solar_data.global_horizontal_radiation_Wm2 == 0.) &
            (solar_data.diffuse_horizontal_radiation_Wm2 == 0.),
            0.,
            solar_data.global_tilt_radiation_Wm2)

        # Read in water mains temperature data
        # We only need one hour's worth of data for each month and location
        # because the provided
        # temperatures are equal for each hour of the day.
        water_mains_data = \
            self.data['Appendix_54B_Schedules_WaterMain'].\
            iloc[3:, 0:3]

        water_mains_data.columns = ['climate_zone_water', 'month_abb',
                                    'water_main_t_F']

        # Fill the climate zone forward
        # Only get water mains data for the climate zone we are analyzing
        water_mains_data = water_mains_data.fillna(method='ffill')
        water_mains_data = water_mains_data.loc[
            water_mains_data.climate_zone_water == 'WaterMainCZ' + climate_zone]

        # Convert calendar abbreviation to calendar number
        water_mains_data['month_num'] = water_mains_data.apply(
            lambda x: list(calendar.month_abbr).index(x.month_abb),
            axis=1)

        # Drop unused columns and merge with the weather data
        data = pd.merge(
            left=solar_data,
            right=water_mains_data,
            how='left',
            left_on='month',
            right_on='month_num')

        # convert temperatures from F to C
        data['water_main_t_C'] = UnitConv(data['water_main_t_F']).degF_degC(
             unit_in='degF')
        if weather_data_source == 'cec':
            data['dry_bulb_C'] = UnitConv(data['dry bulb']).degF_degC(
            unit_in='degF')
            data['wet_bulb_C'] = UnitConv(data['wet bulb']).degF_degC(
            unit_in='degF')
        elif weather_data_source == 'tmy3':
            data['dry_bulb_C'] = data['dry-bulb (c)']
            # Derive wet bulb temperature from dry bulb temperature and
            # relative humidity
            data['wet_bulb_C'] = self._wet_bulb_approx(
                data['dry_bulb_C'],
                data['rhum (%)'])

        # add collector tilt value
        data['Tilt'] = collector_tilt
        data['Azimuth'] = collector_azimuth

        data.drop(
            columns=['climate_zone_water',
                     'month_abb',
                     'month_num'],
            inplace=True)

        if single_row_with_arrays:
            data = self._pack_timeseries(data)

        return data

    @staticmethod
    def _wet_bulb_approx(dry_bulb_C, rel_hum):
        """Converts dry bulb temperature to wet bulb by using an approximation
        provided in this paper (Roland Stull):
        https://journals.ametsoc.org/doi/pdf/10.1175/JAMC-D-11-0143.1

        The provided formula is designed for a pressure like at sea level
        of 1013.25 hPa.

        Parameters:

            dry_bulb_C: pd df
                Timeseries containing dry bulb temperature in Celsius [degC]
            rel_hum: pd df
                Timeseries containing relative Humidity in percent (0 - 100)

        Returns:

            wet_bulb_C: pd df
                Timeseries containing wet bulb temperature in Celcius [degC]
        """
        # Calculate wet bulb temperature
        wet_bulb_C = (dry_bulb_C * np.arctan(
            0.151977 * np.power((rel_hum + 8.313659),0.5)) +
            np.arctan(dry_bulb_C + rel_hum) -
            np.arctan(rel_hum - 1.676331) +
            0.00391838 * np.power(rel_hum, 1.5) *
            np.arctan(0.023101 * rel_hum) - 4.686035)

        return wet_bulb_C

    @staticmethod
    def _pack_timeseries(df, row_index=0):
        """Converts a dataframe of timeseries data
        with timestep values in each row to
        a dataframe with a single row such that the timeseries
        are packed as a list into each cell in that single row.

        Parameters:

            df: pd df
                Timeseries data with timeseries headers
                as column labels and timestep indices as
                row indices

            row_index: int or str
                Default: 0
                Row index for the returned single row of data

        Returns:

            single_row_df: pd df
                Timeseries data packed as a list in each cell of
                a single df row
        """
        single_row_df = pd.DataFrame(
            columns=df.columns,
            index=[row_index])

        for col in df.columns:
            single_row_df[col] = [df[col]]

        return single_row_df

    @staticmethod
    def _add_season_column(df):
        """Adds a season column to a timeseries
        dataframe containing a month column.

        Parameters:

            df : pd df
                Timeseries data with a month column
        """
        map = {1: 'winter', 2: 'winter',
               3: 'winter', 4: 'winter',
               5: 'summer', 6: 'summer',
               7: 'summer', 8: 'summer',
               9: 'summer', 10: 'winter',
               11: 'winter', 12: 'winter'}

        df['season'] = df['month'].apply(lambda x: map[x])

        return df

    @staticmethod
    def _make_example_loading_inputs(inputs, labels, random_state,
                                     occupancy = [4., 4., 4., 4.],
                                     at_home = ['n', 'n', 'n', 'n']):
        """Creates example end-use load profile inputs using the example
        load database (sample of 128 households).

        Parameters:

            inputs: dict of dfs
                Inputs read from the input database

            labels: dist
                Consumer label map

            random_state: np.RandomState object

            occupancy: list
                List of household occupancies. Any occupancy
                above 6 is considered as an occupancy of 6
                for simplicity. If occupancies significantly larger
                than 6 are needed, please aggregate example loads
                in postprocessing

            at_home: list
                List of at home during the day info, 'y' or 'n'

        Returns:

            loading_input : df
                Contains household id, occupancy and load array input
                (see models.py for details)

            household_info: df
                Contains load id and maximum load in [gal] for
                sizing purposes.
        """
        # reformat the example end-use loads table
        loads_df = inputs[labels['exmp_loads']].copy()
        # drop hour column
        loads_df = loads_df.drop(labels['hour'], axis=1)
        # convert loads into gallons
        loads_df_m3 = loads_df.apply(
            lambda x: UnitConv(x).m3_gal(unit_in='gal'))
        single_row_loads = SourceAndSink._pack_timeseries(
            loads_df_m3,
            row_index=labels['load_m3'])
        example_cons = single_row_loads.transpose().reset_index()
        example_cons[labels['ld_id']] = inputs[
                labels['exmp_consload']].loc[:, labels['ld_id']]
        example_cons[labels['occ']] = inputs[
                labels['exmp_consload']].loc[:, labels['occ']]
        example_cons[labels['at_hm']] = inputs[
                labels['exmp_consload']].loc[:, labels['at_hm']]
        example_cons[labels['max_load']] = loads_df.max(axis=0).values

        example_cons = example_cons.drop(
            columns='index',
            axis=1)

        if len(occupancy) != len(at_home):
            mg = 'Occupancy and at home arrays should have the same length.'
            log.error(msg)
            raise Exception

        if (np.array(occupancy) > 6).any():
            occ_arr = np.array(occupancy)
            max_occ = occ_arr.max()
            occ_arr[occ_arr > 6] = 6.
            occupancy = list(occ_arr)
            msg = 'Any occupancy above 6 is considered as occupancy of 6.'\
            ' Maximum provided is {}. Consider aggregating loads if this is'\
            ' of concern.'
            log.warning(msg.format(max_occ))

        uniq_occupancy = set(occupancy)

        uniq_at_home = set(at_home)

        available_example_cons = example_cons.loc[
            (example_cons[labels['occ']].isin(uniq_occupancy)) &
            (example_cons[labels['at_hm']].isin(uniq_at_home))]

        if available_example_cons.shape[0] == 0:
            msg = 'We don\'t have any households matching your inputs in'\
                  ' the database.'
            log.error(meg.format)
            raise Exception

        selected_load_ids = []

        cons_id = 1

        for cons in range(len(occupancy)):

            occ = occupancy[cons]
            at_hm = at_home[cons]

            pick_from = available_example_cons.loc[
                (example_cons[labels['occ']].isin([occ])) &
                (example_cons[labels['at_hm']].isin([at_hm]))]

            load_id = random_state.choice(
                pick_from[labels['ld_id']].values, 1)[0]

            while ((load_id in selected_load_ids) and
                (len(selected_load_ids) < len(
                    pick_from[labels['ld_id']].unique()))):

                load_id = random_state.choice(
                    pick_from[labels['ld_id']].values, 1)[0]

            selected_load_ids.append(load_id)

            load_row = pick_from.loc[
                pick_from[labels['ld_id']] == load_id, :].reset_index()

            cons_id += 1

        indxs = available_example_cons.loc[
            available_example_cons[labels['ld_id']].isin(
                selected_load_ids)].index

        loading_input = available_example_cons.loc[indxs, :].reset_index()
        loading_input[labels['load_m3']] = \
            loading_input[labels['load_m3']].apply(lambda x: x.values)

        loading_input = loading_input.drop(
            columns='index',
            axis=1)

        loading_input[labels['id']] = range(1, loading_input.shape[0] + 1)

        columns_expected_by_system_model = \
            [labels['id'], labels['occ'], labels['load_m3']]

        info_columns = [labels['id'], labels['ld_id'], labels['max_load']]

        household_info = loading_input.loc[:, info_columns]
        loading_input = loading_input.loc[
            :, columns_expected_by_system_model]

        return loading_input, household_info

    @staticmethod
    def demand_estimate(occ):
        """Estimates gal/day demand as provided in the
        CSI-Thermal Program Handbook, April 2016 for
        installations with a known occupancy

        Parameters:

            occ: float
                Number of individual household occupants
        """
        if occ == 1:
            return 20.
        if occ == 2:
            return 35.
        else:
            return 35. + 10. * (occ - 2.)
