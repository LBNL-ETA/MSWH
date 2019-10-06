import numpy as np
import pandas as pd


class UnitConv(object):
    '''Unit conversions using conversion parameters from
    ASHRAE Fundamentals 2017.

    Parameters:

    x_in: float, array
        Input value to be converted to a desired unit

    scale_in: str or 1.
        Scale of the input value, options: 'k', 'kilo',
        'mega', 'million', 'M', 'MM', 'giga', 'G', 'tera', 'T',
        'peta', 'P', 'mili', 'micro'.
        Default: 1.

    scale_out: str or 1.
        Scale of the input value, options: 'k', 'kilo',
        'mega', 'million', 'M', 'MM', 'giga', 'G', 'tera', 'T',
        'peta', 'P', 'mili', 'm', 'micro'.
        Default: 1.

    Examples:

    To convert temperature from degF to degC

    >>> t_in_degC = UnitConv(t_in_degF).degF_degC(unit_in='degF')

    To convert power in hp to kW:

    >>> p_in_kW = UnitConv(p_in_hp, scale_out='kilo').hp_W(unit_in='hp')

    To convert energy from GJ to MMBtu:

    >>> e_MMBtu = UnitConv(e_GJ, scale_in='G', scale_out='MM').Btu_J(unit_in='J')
    '''

    def __init__(self, x_in, scale_in=1., scale_out=1.):

        self.x_in = x_in

        if (scale_in == 'k') or (scale_in == 'kilo'):
            self.scale_in = 1000.
        elif ((scale_in == 'milion') or (scale_in == 'M') or
            (scale_in == 'MM') or (scale_in == 'mega')):
            self.scale_in = 1e6
        elif (scale_in == 'giga') or (scale_in == 'G'):
            self.scale_in = 1e9
        elif (scale_in == 'tera') or (scale_in == 'T'):
            self.scale_in = 1e12
        elif (scale_in == 'peta') or (scale_in == 'P'):
            self.scale_in = 1e15
        elif (scale_in == 'mili') or (scale_in == 'm'):
            self.scale_in = 1e-3
        elif scale_in == 'mikro':
            self.scale_in = 1e-6
        else:
            self.scale_in = scale_in


        if (scale_out == 'k') or (scale_out == 'kilo'):
            self.scale_out = 1000.
        elif ((scale_out == 'milion') or (scale_out == 'M') or
            (scale_out == 'MM') or (scale_out == 'mega')):
            self.scale_out = 1e6
        elif (scale_out == 'giga') or (scale_out == 'G'):
            self.scale_out = 1e9
        elif (scale_out == 'tera') or (scale_out == 'T'):
            self.scale_out = 1e12
        elif (scale_out == 'peta')  or (scale_out == 'P'):
            self.scale_out = 1e15
        elif (scale_out == 'mili') or (scale_out == 'm'):
            self.scale_out = 1e-3
        elif scale_out == 'mikro':
            self.scale_out = 1e-6
        else:
            self.scale_out = scale_out


    def degF_degC(self, unit_in='degF'):
        '''Converts temperature between degree Fahrenheit and Celsius

        Parameters:

            unit_in: string, options: 'degF', 'degC'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'degF':
            x_out = (self.x_in - 32.) * (5. / 9.)
        elif unit_in == 'degC':
            x_out = (self.x_in * 9. / 5.) + 32.
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def degC_K(self, unit_in='degC'):
        '''Converts temperature between degree Celsius and Kelvin

        Parameters:

            unit_in: string, options: 'K', 'degC'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        abs_zero = 273.15

        if unit_in == 'K':
            x_out = self.x_in - abs_zero
        elif unit_in == 'degC':
            x_out = self.x_in + abs_zero
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def m3_gal(self, unit_in='gal'):
        '''Converts volume between cubic meter and gallon

        Parameters:

            unit_in: string, options: 'm3', 'gal'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'gal':
            x_out =  self.x_in * 0.003785412
        elif unit_in == 'm3':
            x_out = self.x_in * (1. / 0.003785412)

        x_out /= self.scale_out

        return x_out

    def hp_W(self, unit_in='hp'):
        '''Converts power between watt and horsepower

        Parameters:

            unit_in: string, options: 'hp', 'W'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'hp':
            x_out =  self.x_in * 745.7
        elif unit_in == 'W':
            x_out = self.x_in * 1. / 745.7
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def Btu_J(self, unit_in='Btu'):
        '''Converts work / energy / heat content between Btu and joule

        Parameters:

            x: float, array
                Input value

            unit_in: string, options: 'Btu', 'J'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'Btu':
            x_out =  self.x_in * 1055.056
        elif unit_in == 'J':
            x_out = self.x_in * (1. / 1055.056)
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def therm_J(self, unit_in='therm'):
        '''Converts work / energy / heat content between therm and joule

        Parameters:

            x: float, array
                Input value

            unit_in: string, options: 'therm', 'J'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'therm':
            x_out =  self.x_in * 105.5 * 1e6
        elif unit_in == 'J':
            x_out = self.x_in / (1e6 * 105.5)
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def Wh_J(self, unit_in='J'):
        '''Converts work / energy / heat content between watthour and joule

        Parameters:

            x: float, array
                Input value

            unit_in: string, options: 'Wh', 'J'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'Wh':
            x_out =  self.x_in * 3600.
        elif unit_in == 'J':
            x_out = self.x_in / 3600.
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def m3perh_m3pers(self, unit_in='m3perh'):
        '''Converts volume flow between cubic meter
        per hour and cubic meter per second

        Parameters:

            x: float, array
                Input value

            unit_in: string, options: 'Wh', 'J'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'm3perh':
            x_out =  self.x_in / 3600.
        elif unit_in == 'm3pers':
            x_out = self.x_in * 3600.
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def sqft_m2(self, unit_in='sqft'):
        '''Converts area between square foot
        and square meter

        Parameters:

            x: float, array
                Input value

            unit_in: string, options: 'Wh', 'J'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'sqft':
            x_out = self.x_in * (0.3048 ** 2)
        elif unit_in == 'm2':
            x_out = self.x_in / (0.3048 ** 2)
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out

    def ft_m(self, unit_in='ft'):
        '''Converts length between foot
        and meter

        Parameters:

            x: float, array
                Input value

            unit_in: string, options: 'Wh', 'J'
                Unit of the input value

        Returns:

            x_out: float, array
                Output value
        '''
        self.x_in *= self.scale_in

        if unit_in == 'ft':
            x_out = self.x_in * 0.3048
        elif unit_in == 'm':
            x_out = self.x_in / 0.3048
        else:
            msg = 'User provided an unsupported input unit {}.'
            log.error(msg.format(unit_in))
            raise ValueError

        x_out /= self.scale_out

        return x_out


class Utility(object):
    """Converts gas or electricity
    consumption into commonly used units.

    Parameters:

        quantity_in: float, array
            Quantity to be converted.
            E.g. gas use in kJ
    """

    def __init__(self, quantity_in):
        self.quantity_in = quantity_in

        # Gas properties
        # heating value ASHRAE fundamentals 28.3.
        # usual range is 37.3 to 39.1 MJ/m3 at sea level
        # table 3: methane= 37.7, ethane 66.1 [MJ/m3]
        self.hea_val_gas = 38.  # [MJ/m3]


    def gas(self, unit_in='kJ', unit_out='MMBtu'):
        """Converts gas consumption.

        Parameters:

            unit_in: string
                Units of the input quantity that needs
                to be converted.
                Options: 'kWh', 'kJ'

            unit_out: string
                Desired output unit
                Options: 'm3', 'cf', 'therm', 'MMBtu'

        Returns:

            gas_use: float
                Gas use in output units
        """
        if unit_in == 'kWh':
            gas_use = UnitConv(
                self.quantity_in,
                scale_in='k',
                scale_out='k').Wh_J(unit_in='Wh')
            self.quantity_in = gas_use + 0.
            unit_in = 'kJ'

        if unit_in == 'kJ':
            if unit_out == 'm3':
                gas_use = self.quantity_in / (self.hea_val_gas * 1000.)
            elif unit_out == 'cf':
                gas_use = self.quantity_in / (
                    0.02832 * self.hea_val_gas * 1000.)
            elif unit_out == 'therm':
                gas_use = UnitConv(
                    self.quantity_in,
                    scale_in='k').therm_J(unit_in='J')
            elif unit_out == 'MMBtu':
                gas_use = UnitConv(
                    self.quantity_in,
                    scale_in='k',
                    scale_out='MM').Btu_J(unit_in='J')
            else:
                raise ValueError(\
                    '{} is not yet supported as output unit'.format(unit_out))

        if unit_in != 'kWh' and unit_in != 'kJ':
            raise ValueError(\
                '{} is not yet supported as input unit.'.format(unit_in))

        return gas_use
