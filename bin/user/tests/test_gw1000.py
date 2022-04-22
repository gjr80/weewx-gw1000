"""
Test suite for the GW1000 driver.

Copyright (C) 2020-21 Gary Roderick                gjroderick<at>gmail.com

A python unittest based test suite for aspects of the GW1000 driver. The test
suite tests correct operation of:

-

Version: 0.4.1                                   Date: 14 October 2021

Revision History
    14 October 2021     v0.4.1
        -   no change, version increment only
    27 September 2021   v0.4.0
        -   updated to work with GW1000 driver v0.4.0

    20 March 2021       v0.3.0
        -   incomplete but works with release v0.3.0 under python3
        -   initial release

To run the test suite:

-   copy this file to the target machine, nominally to the $BIN/user/tests
    directory

-   run the test suite using:

    $ PYTHONPATH=$BIN python3 -m user.tests.test_gw1000 [-v]
"""
# python imports
import socket
import struct
import time
import unittest
from unittest.mock import patch

# Python 2/3 compatibility shims
import six

# WeeWX imports
import weewx
import user.gw1000

# TODO. Check speed_data data and result are correct
# TODO. Check rain_data data and result are correct
# TODO. Check rainrate_data data and result are correct
# TODO. Check big_rain_data data and result are correct
# TODO. Check light_data data and result are correct
# TODO. Check uv_data data and result are correct
# TODO. Check uvi_data data and result are correct
# TODO. Check datetime_data data and result are correct
# TODO. Check leak_data data and result are correct
# TODO. Check batt_data data and result are correct
# TODO. Check distance_data data and result are correct
# TODO. Check utc_data data and result are correct
# TODO. Check count_data data and result are correct
# TODO. Add decode firmware check refer issue #31

TEST_SUITE_NAME = "GW1000 driver"
TEST_SUITE_VERSION = "0.4.0"


class SensorsTestCase(unittest.TestCase):
    """Test the Sensors class."""

    def setUp(self):

        # get a Sensors object
        self.sensors = user.gw1000.GatewayCollector.Sensors()

    def test_battery_methods(self):
        """Test battery state methods"""

        # binary battery states (method batt_binary())
        self.assertEqual(self.sensors.batt_binary(255), 1)
        self.assertEqual(self.sensors.batt_binary(4), 0)

        # integer battery states (method batt_int())
        for int_batt in range(7):
            self.assertEqual(self.sensors.batt_int(int_batt), int_batt)

        # voltage battery states (method batt_volt())
        self.assertEqual(self.sensors.batt_volt(0), 0.00)
        self.assertEqual(self.sensors.batt_volt(100), 2.00)
        self.assertEqual(self.sensors.batt_volt(101), 2.02)
        self.assertEqual(self.sensors.batt_volt(255), 5.1)

        # voltage battery states (method batt_volt_tenth())
        self.assertEqual(self.sensors.batt_volt_tenth(0), 0.00)
        self.assertEqual(self.sensors.batt_volt_tenth(15), 1.5)
        self.assertEqual(self.sensors.batt_volt_tenth(17), 1.7)
        self.assertEqual(self.sensors.batt_volt_tenth(255), 25.5)

        # binary description
        self.assertEqual(self.sensors.battery_desc(b'\x00', 0), 'OK')
        self.assertEqual(self.sensors.battery_desc(b'\x00', 1), 'low')
        self.assertEqual(self.sensors.battery_desc(b'\x00', 2), 'Unknown')
        self.assertEqual(self.sensors.battery_desc(b'\x00', None), 'Unknown')

        # int description
        self.assertEqual(self.sensors.battery_desc(b'\x16', 0), 'low')
        self.assertEqual(self.sensors.battery_desc(b'\x16', 1), 'low')
        self.assertEqual(self.sensors.battery_desc(b'\x16', 4), 'OK')
        self.assertEqual(self.sensors.battery_desc(b'\x16', 6), 'DC')
        self.assertEqual(self.sensors.battery_desc(b'\x16', 7), 'Unknown')
        self.assertEqual(self.sensors.battery_desc(b'\x16', None), 'Unknown')

        # voltage description
        self.assertEqual(self.sensors.battery_desc(b'\x20', 0), 'low')
        self.assertEqual(self.sensors.battery_desc(b'\x20', 1.2), 'low')
        self.assertEqual(self.sensors.battery_desc(b'\x20', 1.5), 'OK')
        self.assertEqual(self.sensors.battery_desc(b'\x20', None), 'Unknown')


class ParseTestCase(unittest.TestCase):
    """Test the GatewayCollector Parser class."""

    batt_fields = ('multi', 'wh31', 'wh51', 'wh57', 'wh68', 'ws80',
                   'unused', 'wh41', 'wh55')
    response_struct = {
        b'\x01': ('decode_temp', 2, 'intemp'),
        b'\x02': ('decode_temp', 2, 'outtemp'),
        b'\x03': ('decode_temp', 2, 'dewpoint'),
        b'\x04': ('decode_temp', 2, 'windchill'),
        b'\x05': ('decode_temp', 2, 'heatindex'),
        b'\x06': ('decode_humid', 1, 'inhumid'),
        b'\x07': ('decode_humid', 1, 'outhumid'),
        b'\x08': ('decode_press', 2, 'absbarometer'),
        b'\x09': ('decode_press', 2, 'relbarometer'),
        b'\x0A': ('decode_dir', 2, 'winddir'),
        b'\x0B': ('decode_speed', 2, 'windspeed'),
        b'\x0C': ('decode_speed', 2, 'gustspeed'),
        b'\x0D': ('decode_rain', 2, 'rainevent'),
        b'\x0E': ('decode_rainrate', 2, 'rainrate'),
        b'\x0F': ('decode_rain', 2, 'rainhour'),
        b'\x10': ('decode_rain', 2, 'rainday'),
        b'\x11': ('decode_rain', 2, 'rainweek'),
        b'\x12': ('decode_big_rain', 4, 'rainmonth'),
        b'\x13': ('decode_big_rain', 4, 'rainyear'),
        b'\x14': ('decode_big_rain', 4, 'raintotals'),
        b'\x15': ('decode_light', 4, 'light'),
        b'\x16': ('decode_uv', 2, 'uv'),
        b'\x17': ('decode_uvi', 1, 'uvi'),
        b'\x18': ('decode_datetime', 6, 'datetime'),
        b'\x19': ('decode_speed', 2, 'daymaxwind'),
        b'\x1A': ('decode_temp', 2, 'temp1'),
        b'\x1B': ('decode_temp', 2, 'temp2'),
        b'\x1C': ('decode_temp', 2, 'temp3'),
        b'\x1D': ('decode_temp', 2, 'temp4'),
        b'\x1E': ('decode_temp', 2, 'temp5'),
        b'\x1F': ('decode_temp', 2, 'temp6'),
        b'\x20': ('decode_temp', 2, 'temp7'),
        b'\x21': ('decode_temp', 2, 'temp8'),
        b'\x22': ('decode_humid', 1, 'humid1'),
        b'\x23': ('decode_humid', 1, 'humid2'),
        b'\x24': ('decode_humid', 1, 'humid3'),
        b'\x25': ('decode_humid', 1, 'humid4'),
        b'\x26': ('decode_humid', 1, 'humid5'),
        b'\x27': ('decode_humid', 1, 'humid6'),
        b'\x28': ('decode_humid', 1, 'humid7'),
        b'\x29': ('decode_humid', 1, 'humid8'),
        b'\x2A': ('decode_pm25', 2, 'pm251'),
        b'\x2B': ('decode_temp', 2, 'soiltemp1'),
        b'\x2C': ('decode_moist', 1, 'soilmoist1'),
        b'\x2D': ('decode_temp', 2, 'soiltemp2'),
        b'\x2E': ('decode_moist', 1, 'soilmoist2'),
        b'\x2F': ('decode_temp', 2, 'soiltemp3'),
        b'\x30': ('decode_moist', 1, 'soilmoist3'),
        b'\x31': ('decode_temp', 2, 'soiltemp4'),
        b'\x32': ('decode_moist', 1, 'soilmoist4'),
        b'\x33': ('decode_temp', 2, 'soiltemp5'),
        b'\x34': ('decode_moist', 1, 'soilmoist5'),
        b'\x35': ('decode_temp', 2, 'soiltemp6'),
        b'\x36': ('decode_moist', 1, 'soilmoist6'),
        b'\x37': ('decode_temp', 2, 'soiltemp7'),
        b'\x38': ('decode_moist', 1, 'soilmoist7'),
        b'\x39': ('decode_temp', 2, 'soiltemp8'),
        b'\x3A': ('decode_moist', 1, 'soilmoist8'),
        b'\x3B': ('decode_temp', 2, 'soiltemp9'),
        b'\x3C': ('decode_moist', 1, 'soilmoist9'),
        b'\x3D': ('decode_temp', 2, 'soiltemp10'),
        b'\x3E': ('decode_moist', 1, 'soilmoist10'),
        b'\x3F': ('decode_temp', 2, 'soiltemp11'),
        b'\x40': ('decode_moist', 1, 'soilmoist11'),
        b'\x41': ('decode_temp', 2, 'soiltemp12'),
        b'\x42': ('decode_moist', 1, 'soilmoist12'),
        b'\x43': ('decode_temp', 2, 'soiltemp13'),
        b'\x44': ('decode_moist', 1, 'soilmoist13'),
        b'\x45': ('decode_temp', 2, 'soiltemp14'),
        b'\x46': ('decode_moist', 1, 'soilmoist14'),
        b'\x47': ('decode_temp', 2, 'soiltemp15'),
        b'\x48': ('decode_moist', 1, 'soilmoist15'),
        b'\x49': ('decode_temp', 2, 'soiltemp16'),
        b'\x4A': ('decode_moist', 1, 'soilmoist16'),
        b'\x4C': ('decode_batt', 16, 'lowbatt'),
        b'\x4D': ('decode_pm25', 2, 'pm251_24h_avg'),
        b'\x4E': ('decode_pm25', 2, 'pm252_24h_avg'),
        b'\x4F': ('decode_pm25', 2, 'pm253_24h_avg'),
        b'\x50': ('decode_pm25', 2, 'pm254_24h_avg'),
        b'\x51': ('decode_pm25', 2, 'pm252'),
        b'\x52': ('decode_pm25', 2, 'pm253'),
        b'\x53': ('decode_pm25', 2, 'pm254'),
        b'\x58': ('decode_leak', 1, 'leak1'),
        b'\x59': ('decode_leak', 1, 'leak2'),
        b'\x5A': ('decode_leak', 1, 'leak3'),
        b'\x5B': ('decode_leak', 1, 'leak4'),
        b'\x60': ('decode_distance', 1, 'lightningdist'),
        b'\x61': ('decode_utc', 4, 'lightningdettime'),
        b'\x62': ('decode_count', 4, 'lightningcount'),
        # WH34 battery data is not obtained from live data rather it is
        # obtained from sensor ID data
        b'\x63': ('decode_wh34', 3, 'temp9'),
        b'\x64': ('decode_wh34', 3, 'temp10'),
        b'\x65': ('decode_wh34', 3, 'temp11'),
        b'\x66': ('decode_wh34', 3, 'temp12'),
        b'\x67': ('decode_wh34', 3, 'temp13'),
        b'\x68': ('decode_wh34', 3, 'temp14'),
        b'\x69': ('decode_wh34', 3, 'temp15'),
        b'\x6A': ('decode_wh34', 3, 'temp16'),
        b'\x70': ('decode_wh45', 16, ('temp17', 'humid17', 'pm10',
                                      'pm10_24h_avg', 'pm255', 'pm255_24h_avg',
                                      'co2', 'co2_24h_avg')),
        b'\x71': (None, None, None),
        b'\x72': ('decode_wet', 1, 'leafwet1'),
        b'\x73': ('decode_wet', 1, 'leafwet2'),
        b'\x74': ('decode_wet', 1, 'leafwet3'),
        b'\x75': ('decode_wet', 1, 'leafwet4'),
        b'\x76': ('decode_wet', 1, 'leafwet5'),
        b'\x77': ('decode_wet', 1, 'leafwet6'),
        b'\x78': ('decode_wet', 1, 'leafwet7'),
        b'\x79': ('decode_wet', 1, 'leafwet8')
    }
    rain_field_codes = (b'\x0D', b'\x0E', b'\x0F', b'\x10',
                        b'\x11', b'\x12', b'\x13', b'\x14')
    wind_field_codes = (b'\x0A', b'\x0B', b'\x0C', b'\x19')

    response_data = 'FF FF 27 00 40 01 01 40 06 26 08 27 D2 09 27 D2 2A 00 5A ' \
                    '4D 00 65 2C 27 2E 14 1A 00 ED 22 3A 1B 01 0B 23 3A 4C 06 ' \
                    '00 00 00 05 FF FF 00 F6 FF FF FF FF FF FF FF 62 00 00 00 ' \
                    '00 61 FF FF FF FF 60 FF EC'
    parsed_response = {'intemp': 32.0,
                       'inhumid': 38,
                       'absbarometer': 1019.4,
                       'relbarometer': 1019.4,
                       'pm251': 9.0,
                       'pm251_24h_avg': 10.1,
                       'soilmoist1': 39,
                       'soilmoist2': 20,
                       'temp1': 23.7,
                       'humid1': 58,
                       'temp2': 26.7,
                       'humid2': 58,
                       'lightningcount': 0,
                       'lightningdettime': None,
                       'lightningdist': None,
                       'datetime': 1599021263}
    temp_data = {'hex': '00 EA', 'value': 23.4}
    humid_data = {'hex': '48', 'value': 72}
    press_data = {'hex': '27 4C', 'value': 1006.0}
    dir_data = {'hex': '00 70', 'value': 112}
    speed_data = {'hex': '00 70', 'value': 11.2}
    rain_data = {'hex': '01 70', 'value': 36.8}
    rainrate_data = {'hex': '00 34', 'value': 5.2}
    big_rain_data = {'hex': '01 70 37 21', 'value': 2413136.1}
    light_data = {'hex': '02 40 72 51', 'value': 3777800.1}
    uv_data = {'hex': '32 70', 'value': 1291.2}
    uvi_data = {'hex': '0C', 'value': 12}
    datetime_data = {'hex': '0C AB 23 41 56 37', 'value': (12, 171, 35, 65, 86, 55)}
    pm25_data = {'hex': '00 39', 'value': 5.7}
    moist_data = {'hex': '3A', 'value': 58}
    leak_data = {'hex': '3A', 'value': 58}
    distance_data = {'hex': '1A', 'value': 26}
    utc_data = {'hex': '5F 40 72 51', 'value': 1598059089}
    count_data = {'hex': '00 40 72 51', 'value': 4223569}
    wh34_data = {'hex': '00 EA 4D',
                 'field': 't',
                 'value': {'t': 23.4}
                 }
    wh45_data = {'hex': '00 EA 4D 35 6D 28 78 34 3D 62 7E 8D 2A 39 9F 04',
                 'field': ('t', 'h', 'p10', 'p10_24', 'p25', 'p25_24', 'c', 'c_24'),
                 'value': {'t': 23.4, 'h': 77, 'p10': 1367.7, 'p10_24': 1036.0,
                           'p25': 1337.3, 'p25_24': 2521.4, 'c': 36138, 'c_24': 14751}
                 }

    def setUp(self):

        # get a Parser object
        self.parser = user.gw1000.GatewayCollector.Parser()
        self.maxDiff = None

    def tearDown(self):

        pass

    def test_constants(self):
        """Test constants"""

        # test battery mask dicts

        # multi_batt
        self.assertEqual(self.parser.multi_batt['wh40']['mask'], 1 << 4)
        self.assertEqual(self.parser.multi_batt['wh26']['mask'], 1 << 5)
        self.assertEqual(self.parser.multi_batt['wh25']['mask'], 1 << 6)
        self.assertEqual(self.parser.multi_batt['wh65']['mask'], 1 << 7)

        # response_struct
        self.assertEqual(self.parser.addressed_data_struct, self.response_struct)

        # rain_field_codes
        self.assertEqual(self.parser.rain_field_codes, self.rain_field_codes)

        # wind_field_codes
        self.assertEqual(self.parser.wind_field_codes, self.wind_field_codes)

    def test_decode(self):
        """Test methods used to decode observation byte data"""

        # test temperature decode (method decode_temp())
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(self.temp_data['hex'])),
                         self.temp_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(3))), None)

        # test humidity decode (method decode_humid())
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(self.humid_data['hex'])),
                         self.humid_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(2))), None)

        # test pressure decode (method decode_press())
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.press_data['hex'])),
                         self.press_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(3))), None)

        # test direction decode (method decode_dir())
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['hex'])),
                         self.dir_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(3))), None)

        # test big rain decode (method decode_big_rain())
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(self.big_rain_data['hex'])),
                         self.big_rain_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(5))), None)

        # test datetime decode (method decode_datetime())
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(self.datetime_data['hex'])),
                         self.datetime_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(7))), None)

        # test distance decode (method decode_distance())
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(self.distance_data['hex'])),
                         self.distance_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(2))), None)

        # test utc decode (method decode_utc())
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(self.utc_data['hex'])),
                         self.utc_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(5))), None)

        # test count decode (method decode_count())
        self.assertEqual(self.parser.decode_count(hex_to_bytes(self.count_data['hex'])),
                         self.count_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(5))), None)

        # test speed decode (method decode_speed())
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(self.speed_data['hex'])),
                         self.speed_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(xbytes(3))), None)

        # test rain decode (method decode_rain())
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(self.rain_data['hex'])),
                         self.rain_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(xbytes(3))), None)

        # test rain rate decode (method decode_rainrate())
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(self.rainrate_data['hex'])),
                         self.rainrate_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(xbytes(3))), None)

        # test light decode (method decode_light())
        self.assertEqual(self.parser.decode_light(hex_to_bytes(self.light_data['hex'])),
                         self.light_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(5))), None)

        # test uv decode (method decode_uv())
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(self.uv_data['hex'])),
                         self.uv_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(xbytes(3))), None)

        # test uvi decode (method decode_uvi())
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(self.uvi_data['hex'])),
                         self.uvi_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(2))), None)

        # test moisture decode (method decode_moist())
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(self.moist_data['hex'])),
                         self.moist_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(2))), None)

        # test pm25 decode (method decode_pm25())
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(self.pm25_data['hex'])),
                         self.pm25_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(xbytes(3))), None)

        # test leak decode (method decode_leak())
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(self.leak_data['hex'])),
                         self.leak_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(2))), None)

        # test wh34 decode (method decode_pm10())
        pass

        # test wh34 decode (method decode_co2())
        pass

        # test wh34 decode (method decode_wh34())
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(self.wh34_data['hex']), field=self.wh34_data['field']),
                         self.wh34_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(xbytes(1)), field=self.wh34_data['field']), {})
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(xbytes(4)), field=self.wh34_data['field']), {})

        # test wh45 decode (method decode_wh45())
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(self.wh45_data['hex']), fields=self.wh45_data['field']),
                         self.wh45_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(1)), fields=self.wh45_data['field']),
                         {})
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(17)), fields=self.wh45_data['field']),
                         {})

        # test parsing of all possible sensors
        self.assertDictEqual(self.parser.parse_live_data(raw_data=hex_to_bytes(self.response_data), timestamp=1599021263),
                             self.parsed_response)


class UtilitiesTestCase(unittest.TestCase):
    """Unit tests for utility functions."""

    unsorted_dict = {'leak2': 'leak2',
                     'inHumidity': 'inhumid',
                     'wh31_ch3_batt': 'wh31_ch3_batt',
                     'leak1': 'leak1',
                     'wh31_ch2_batt': 'wh31_ch2_batt',
                     'windDir': 'winddir',
                     'inTemp': 'intemp'}
    sorted_dict_str = "{'inHumidity': 'inhumid', 'inTemp': 'intemp', " \
                      "'leak1': 'leak1', 'leak2': 'leak2', " \
                      "'wh31_ch2_batt': 'wh31_ch2_batt', " \
                      "'wh31_ch3_batt': 'wh31_ch3_batt', " \
                      "'windDir': 'winddir'}"
    sorted_keys = ['inHumidity', 'inTemp', 'leak1', 'leak2',
                   'wh31_ch2_batt', 'wh31_ch3_batt', 'windDir']
    bytes_to_hex_fail_str = "cannot represent '%s' as hexadecimal bytes"

    def test_utilities(self):
        """Test utility functions

        Tests:
        1. natural_sort_keys()
        2. natural_sort_dict()
        3. bytes_to_hex()
        """

        # test natural_sort_keys()
        self.assertEqual(user.gw1000.natural_sort_keys(self.unsorted_dict),
                         self.sorted_keys)

        # test natural_sort_dict()
        self.assertEqual(user.gw1000.natural_sort_dict(self.unsorted_dict),
                         self.sorted_dict_str)

        # test bytes_to_hex()
        # with defaults
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2')),
                         'FF 00 66 B2')
        # with defaults and a separator
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=':'),
                         'FF:00:66:B2')
        # with defaults using lower case
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), caps=False),
                         'ff 00 66 b2')
        # with a separator and lower case
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=':', caps=False),
                         'ff:00:66:b2')
        # and check exceptions raised
        # TypeError
        self.assertEqual(user.gw1000.bytes_to_hex(22), self.bytes_to_hex_fail_str % 22)
        # AttributeError
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=None),
                         self.bytes_to_hex_fail_str % hex_to_bytes('ff 00 66 b2'))

        # test obfuscate()
        # > 8 character string, should see trailing 4 characters
        self.assertEqual(user.gw1000.obfuscate('1234567890'), '******7890')
        # 7 character string, should see trailing 3 characters
        self.assertEqual(user.gw1000.obfuscate('1234567'), '****567')
        # 5 character string, should see trailing 2 characters
        self.assertEqual(user.gw1000.obfuscate('12345'), '***45')
        # 3 character string, should see last character
        self.assertEqual(user.gw1000.obfuscate('123'), '**3')
        # 2 character string, should see no characters
        self.assertEqual(user.gw1000.obfuscate('12'), '**')
        # check obfuscation character
        self.assertEqual(user.gw1000.obfuscate('1234567890', obf_char='#'),
                         '######7890')


class ListsAndDictsTestCase(unittest.TestCase):
    """Test case to test list and dict consistency."""

    def setUp(self):

        # construct the default field map
        default_field_map = dict(user.gw1000.Gateway.default_field_map)
        # now add in the rain field map
        default_field_map.update(user.gw1000.Gateway.rain_field_map)
        # now add in the wind field map
        default_field_map.update(user.gw1000.Gateway.wind_field_map)
        # now add in the battery state field map
        default_field_map.update(user.gw1000.Gateway.battery_field_map)
        # now add in the sensor signal field map
        default_field_map.update(user.gw1000.Gateway.sensor_signal_field_map)
        # and save it for later
        self.default_field_map = default_field_map

    def test_dicts(self):
        """Test dicts for consistency"""

        # test that each entry in the GW1000 default field map appears in the
        # observation group dictionary
        for w_field, g_field in six.iteritems(self.default_field_map):
            self.assertIn(g_field,
                          user.gw1000.DirectGateway.gateway_obs_group_dict.keys(),
                          msg="A field from the GW1000 default field map is "
                              "missing from the observation group dictionary")

        # test that each entry in the observation group dictionary is included
        # in the GW1000 default field map
        for g_field, group in six.iteritems(user.gw1000.DirectGateway.gateway_obs_group_dict):
            self.assertIn(g_field,
                          self.default_field_map.values(),
                          msg="A key from the observation group dictionary is "
                              "missing from the GW1000 default field map")


class StationTestCase(unittest.TestCase):

    fake_ip = '192.168.99.99'
    fake_port = 44444
    fake_mac = b'\xdcO"X\xa2E'
    cmd_read_fware_ver = b'\x50'
    read_fware_cmd_bytes = b'\xff\xffP\x03S'
    read_fware_resp_bytes = b'\xff\xffP\x11\rGW1000_V1.6.1v'
    read_fware_resp_bad_checksum_bytes = b'\xff\xffP\x11\rGW1000_V1.6.1w'
    read_fware_resp_bad_cmd_bytes = b'\xff\xffQ\x11\rGW1000_V1.6.1v'
    broadcast_response_data = 'FF FF 12 00 26 50 02 91 E3 FD 32 C0 A8 02 20 AF ' \
                              'C8 16 47 57 31 30 30 30 2D 57 49 46 49 46 44 33 ' \
                              '32 20 56 31 2E 36 2E 38 5F'
    decoded_broadcast_response = {'mac': '50:02:91:E3:FD:32',
                                  'ip_address': '192.168.2.32',
                                  'port': 45000,
                                  'ssid': 'GW1000-WIFIFD32 V1.6.8'}
    cmd = 'CMD_READ_FIRMWARE_VERSION'
    cmd_payload = '01 02 FF'
    cmd_packet = 'FF FF 50 06 01 02 FF 58'
    commands = {
        'CMD_WRITE_SSID': 'FF FF 11 03 14',
        'CMD_BROADCAST': 'FF FF 12 03 15',
        'CMD_READ_ECOWITT': 'FF FF 1E 03 21',
        'CMD_WRITE_ECOWITT': 'FF FF 1F 03 22',
        'CMD_READ_WUNDERGROUND': 'FF FF 20 03 23',
        'CMD_WRITE_WUNDERGROUND': 'FF FF 21 03 24',
        'CMD_READ_WOW': 'FF FF 22 03 25',
        'CMD_WRITE_WOW': 'FF FF 23 03 26',
        'CMD_READ_WEATHERCLOUD': 'FF FF 24 03 27',
        'CMD_WRITE_WEATHERCLOUD': 'FF FF 25 03 28',
        'CMD_READ_STATION_MAC': 'FF FF 26 03 29',
        'CMD_GW1000_LIVEDATA': 'FF FF 27 03 2A',
        'CMD_GET_SOILHUMIAD': 'FF FF 28 03 2B',
        'CMD_SET_SOILHUMIAD': 'FF FF 29 03 2C',
        'CMD_READ_CUSTOMIZED': 'FF FF 2A 03 2D',
        'CMD_WRITE_CUSTOMIZED': 'FF FF 2B 03 2E',
        'CMD_GET_MulCH_OFFSET': 'FF FF 2C 03 2F',
        'CMD_SET_MulCH_OFFSET': 'FF FF 2D 03 30',
        'CMD_GET_PM25_OFFSET': 'FF FF 2E 03 31',
        'CMD_SET_PM25_OFFSET': 'FF FF 2F 03 32',
        'CMD_READ_SSSS': 'FF FF 30 03 33',
        'CMD_WRITE_SSSS': 'FF FF 31 03 34',
        'CMD_READ_RAINDATA': 'FF FF 34 03 37',
        'CMD_WRITE_RAINDATA': 'FF FF 35 03 38',
        'CMD_READ_GAIN': 'FF FF 36 03 39',
        'CMD_WRITE_GAIN': 'FF FF 37 03 3A',
        'CMD_READ_CALIBRATION': 'FF FF 38 03 3B',
        'CMD_WRITE_CALIBRATION': 'FF FF 39 03 3C',
        'CMD_READ_SENSOR_ID': 'FF FF 3A 03 3D',
        'CMD_WRITE_SENSOR_ID': 'FF FF 3B 03 3E',
        'CMD_READ_SENSOR_ID_NEW': 'FF FF 3C 03 3F',
        'CMD_WRITE_REBOOT': 'FF FF 40 03 43',
        'CMD_WRITE_RESET': 'FF FF 41 03 44',
        'CMD_WRITE_UPDATE': 'FF FF 43 03 46',
        'CMD_READ_FIRMWARE_VERSION': 'FF FF 50 03 53',
        'CMD_READ_USR_PATH': 'FF FF 51 03 54',
        'CMD_WRITE_USR_PATH': 'FF FF 52 03 55',
        'CMD_GET_CO2_OFFSET': 'FF FF 53 03 56',
        'CMD_SET_CO2_OFFSET': 'FF FF 54 03 57'
    }
    # Station.discover() multiple device discovery response
    discover_multi_resp = [{'mac': b'\xe8h\xe7\x87\x1aO', #'E8:68:E7:87:1A:4F',
                            'ip_address': '192.168.50.3',
                            'port': 45001,
                            'ssid': 'GW1100C-WIFI1A4F V2.0.9',
                            'model': 'GW1100'},
                           {'mac': b'\xdcO"X\xa2E', #'DC:4F:22:58:A2:45'
                            'ip_address': '192.168.50.6',
                            'port': 45002,
                            'ssid': 'GW1000-WIFIA245 V1.6.7',
                            'model': 'GW1000'},
                           {'mac': b'P\x02\x91\xe3\xd3h', #'50:02:91:E3:D3:68',
                            'ip_address': '192.168.50.7',
                            'port': 45003,
                            'ssid': 'GW1000-WIFID368 V1.6.8',
                            'model': 'GW1000'}
                           ]
    # Station.discover() multiple device discovery response with different MAC
    discover_multi_diff_resp = [{'mac': b'\xe8h\xe7\x87\x1bO', #'E8:68:E7:87:1B:4F',
                                 'ip_address': '192.168.50.3',
                                 'port': 45001,
                                 'ssid': 'GW1100C-WIFI1A4F V2.0.9',
                                 'model': 'GW1100'},
                                {'mac': b'\xdcO"X\xa3E', #'DC:4F:22:58:A3:45'
                                 'ip_address': '192.168.50.6',
                                 'port': 45002,
                                 'ssid': 'GW1000-WIFIA245 V1.6.7',
                                 'model': 'GW1000'},
                                {'mac': b'P\x02\x91\xe3\xd2h', #'50:02:91:E3:D2:68',
                                 'ip_address': '192.168.50.7',
                                 'port': 45003,
                                 'ssid': 'GW1000-WIFID368 V1.6.8',
                                 'model': 'GW1000'}
                                ]

    @classmethod
    def setUpClass(cls):
        """Setup the StationTestCase to perform its tests.

        Determines the IP address and port to use for the Station tests. A
        GatewayCollector.Station object is required to perform some of the
        StationTestCase tests. If either or both of IP address and port are not
        specified when instantiating a Station object device discovery will be
        initiated which may result in delays or failure of the test case if no
        device is found. To avoid such situations an IP address and port number
        is always used when instantiating a Station object as part of this test
        case.

        the IP address and port number are determined as follows:
        - if --ip-address and --port were specifeid on the command line then
          the specified paramaters are used
        - if --ip-address is specifed on the command line but --port was not
          then port 45000 is used
        - if --port is specifeid on the command line but --ip-address was not
          then a fake IP address is used
        - if neither --ip-address or --port number is specified on the command
          line then a fake IP address and port number are used
        """

        # set the IP address we will use
        cls.test_ip = cls.ip_address if cls.ip_address is not None else StationTestCase.fake_ip
        # set the port number we will use
        cls.test_port = cls.port if cls.port is not None else StationTestCase.fake_port

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_cmd_vocab(self, mock_get_mac, mock_get_firmware):
        """Test command dictionaries for completeness.

        Tests:
        1. Station.commands contains all commands
        2. the command code for each Station.commands agrees with the test suite
        3. all Station.commands entries are in the test suite
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayCollector.Station(ip_address=self.test_ip,
                                                       port=self.test_port)
        # Check that the class Station command list is complete. This is a
        # simple check for (1) inclusion of the command and (2) the command
        # code (byte) is correct.
        for cmd, response in six.iteritems(self.commands):
            # check for inclusion of the command
            self.assertIn(cmd,
                          station.commands.keys(),
                          msg="Command '%s' not found in Station.commands" % cmd)
            # check the command code byte is correct
            self.assertEqual(hex_to_bytes(response)[2:3],
                             station.commands[cmd],
                             msg="Command code for command '%s' in "
                                 "Station.commands(0x%s) disagrees with "
                                 "command code in test suite (0x%s)" % (cmd,
                                                                        bytes_to_hex(station.commands[cmd]),
                                                                        bytes_to_hex(hex_to_bytes(response)[2:3])))

        # Check that we are testing everything in class Station command list.
        # This is a simple check that only needs to check for inclusion of the
        # command, the validity of the command code is checked in the earlier
        # iteration.
        for cmd, code in six.iteritems(station.commands):
            # check for inclusion of the command
            self.assertIn(cmd,
                          self.commands.keys(),
                          msg="Command '%s' is in Station.commands but it is not being tested" % cmd)

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_calc_checksum(self, mock_get_mac, mock_get_firmware):
        """Test checksum calculation.

        Tests:
        1. calculating the checksum of a bytestring
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayCollector.Station(ip_address=self.test_ip,
                                                       port=self.test_port)
        # test checksum calculation
        self.assertEqual(station.calc_checksum(b'00112233bbccddee'), 168)

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_build_cmd_packet(self, mock_get_mac, mock_get_firmware):
        """Test construction of an API command packet

        Tests:
        1. building a command packet for each command in Station.commands
        2. building a command packet with a payload
        3. building a command packet for an unknown command
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayCollector.Station(ip_address=self.test_ip,
                                                       port=self.test_port)
        # test the command packet built for each API command we know about
        for cmd, packet in six.iteritems(self.commands):
            self.assertEqual(station.build_cmd_packet(cmd), hex_to_bytes(packet))
        # test a command packet that has a payload
        self.assertEqual(station.build_cmd_packet(self.cmd, hex_to_bytes(self.cmd_payload)),
                         hex_to_bytes(self.cmd_packet))
        # test building a command packet for an unknown command, should be an UnknownCommand exception
        self.assertRaises(user.gw1000.UnknownCommand,
                          station.build_cmd_packet,
                          cmd='UNKNOWN_COMMAND')

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_decode_broadcast_response(self, mock_get_mac, mock_get_firmware):
        """Test decoding of a broadcast response

        Tests:
        1. decode a broadcast response
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayCollector.Station(ip_address=self.test_ip,
                                                       port=self.test_port)
        # get the broadcast response test data as a bytestring
        data = hex_to_bytes(self.broadcast_response_data)
        # test broadcast response decode
        self.assertEqual(station.decode_broadcast_response(data), self.decoded_broadcast_response)

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_api_response_validity_check(self, mock_get_mac, mock_get_firmware):
        """Test validity checking of an API response

        Tests:
        1. checks Station.check_response() with good data
        2. checks that Station.check_response() raises an InvalidChecksum
           exception for a response with an invalid checksum
        3. checks that Station.check_response() raises an InvalidApiResponse
           exception for a response with an command code
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayCollector.Station(ip_address=self.test_ip,
                                                       port=self.test_port)
        # test check_response() with good data, should be no exception
        try:
            station.check_response(self.read_fware_resp_bytes,
                                   self.cmd_read_fware_ver)
        except user.gw1000.InvalidChecksum:
            self.fail("check_response() raised an InvalidChecksum exception")
        except user.gw1000.InvalidApiResponse:
            self.fail("check_response() raised an InvalidApiResponse exception")
        # test check_response() with a bad checksum data, should be an InvalidChecksum exception
        self.assertRaises(user.gw1000.InvalidChecksum,
                          station.check_response,
                          response=self.read_fware_resp_bad_checksum_bytes,
                          cmd_code=self.cmd_read_fware_ver)
        # test check_response() with a bad response, should be an InvalidApiResponse exception
        self.assertRaises(user.gw1000.InvalidApiResponse,
                          station.check_response,
                          response=self.read_fware_resp_bad_cmd_bytes,
                          cmd_code=self.cmd_read_fware_ver)

    @patch.object(user.gw1000.GatewayCollector.Station, 'discover')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_discovery(self, mock_get_mac, mock_get_firmware, mock_discover):
        """Test discovery related methods.

        Tests:
        1.
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # discover() - list of discovered devices (list of dicts)
        mock_discover.return_value = StationTestCase.discover_multi_resp
        # get our mocked Station object
        station = user.gw1000.GatewayCollector.Station(ip_address=self.test_ip,
                                                       port=self.test_port)
        # to use discovery we need to fool the Station object into thinking it
        # used discovery to obtain the current devices IP address and port
        station.ip_discovered = True
        # to speed up testing we can reduce some of the retries and wait times
        station.max_tries = 1
        station.retry_wait = 3

        # test Station.rediscover() when the original device is found again
        # force rediscovery
        station.rediscover()
        # test that we retained the original MAC address after rediscovery
        self.assertEqual(station.mac, StationTestCase.discover_multi_resp[1]['mac'])
        # test that the new IP address was detected
        self.assertEqual(station.ip_address.decode(),
                         StationTestCase.discover_multi_resp[1]['ip_address'])
        # test that the new port number was detected
        self.assertEqual(station.port,
                         StationTestCase.discover_multi_resp[1]['port'])

        # test Station.rediscover() when devices are found but not the original
        # device
        mock_discover.return_value = StationTestCase.discover_multi_diff_resp
        # reset our Station object IP address and port
        station.ip_address = self.test_ip.encode()
        station.port = self.test_port
        # force rediscovery
        station.rediscover()
        # test that we retained the original MAC address after rediscovery
        self.assertEqual(station.mac, StationTestCase.discover_multi_resp[1]['mac'])
        # test that the new IP address was detected
        self.assertEqual(station.ip_address.decode(), self.test_ip)
        # test that the new port number was detected
        self.assertEqual(station.port, self.test_port)

        # now test Station.rediscover() when no devices are found
        mock_discover.return_value = []
        # reset our Station object IP address and port
        station.ip_address = self.test_ip.encode()
        station.port = self.test_port
        # force rediscovery
        station.rediscover()
        # test that we retained the original MAC address after rediscovery
        self.assertEqual(station.mac, StationTestCase.discover_multi_resp[1]['mac'])
        # test that the new IP address was detected
        self.assertEqual(station.ip_address.decode(), self.test_ip)
        # test that the new port number was detected
        self.assertEqual(station.port, self.test_port)

        # now test Station.rediscover() when Station.discover() raises an
        # exception
        mock_discover.side_effect = socket.error
        # reset our Station object IP address and port
        station.ip_address = self.test_ip.encode()
        station.port = self.test_port
        # force rediscovery
        station.rediscover()
        # test that we retained the original MAC address after rediscovery
        self.assertEqual(station.mac, StationTestCase.discover_multi_resp[1]['mac'])
        # test that the new IP address was detected
        self.assertEqual(station.ip_address.decode(), self.test_ip)
        # test that the new port number was detected
        self.assertEqual(station.port, self.test_port)


class Gw1000TestCase(unittest.TestCase):
    """Test the GW1000Service.

    Uses mock to simulate methods required to run a GW1000 service without a
    GW1x00. If for some reason the GW1000 service cannot be run the test is
    skipped.
    """

    fake_ip = '192.168.99.99'
    fake_port = 44444
    fake_mac = b'\xdcO"X\xa2E'
    # dummy GW1000 data used to exercise the GW1000 to WeeWX mapping
    gw1000_data = {'absbarometer': 1009.3,
                   'datetime': 1632109437,
                   'inHumidity': 56,
                   'inTemp': 27.3,
                   'lightningcount': 32,
                   'raintotals': 100.3,
                   'relbarometer': 1014.3,
                   'usUnits': 17
                   }
    # mapped dummy GW1000 data
    result_data = {'dateTime': 1632109437,
                   'inHumidity': 56,
                   'inTemp': 27.3,
                   'lightningcount': 32,
                   'pressure': 1009.3,
                   'relbarometer': 1014.3,
                   'totalRain': 100.3,
                   'usUnits': 17
                   }
    # amount to increment delta measurements
    increment = 5.6
    # mocked read_system_parameters() output
    mock_sys_params_resp = b'\xff\xff0\x0b\x00\x01b7\rj^\x02\xac'
    # mocked get_firmware() response
    mock_get_firm_resp = b'\xff\xffP\x11\rGW1000_V1.6.8}'

    @classmethod
    def setUpClass(cls):
        """Setup the Gw1000TestCase to perform its tests."""

        # Create a dummy config so we can stand up a dummy engine with a dummy
        # simulator emitting arbitrary loop packets. Only include the GW1000
        # service, we don't need the others. This will be a loop packets only
        # setup, no archive records, but that doesn't matter, we just need to
        # be able to exercise the GW1000 service.
        config = {
            'Station': {
                'station_type': 'Simulator',
                'altitude': [0, 'meter'],
                'latitude': 0,
                'longitude': 0},
            'Simulator': {
                'driver': 'weewx.drivers.simulator',
                'mode': 'simulator'},
            'GW1000': {},
            'Engine': {
                'Services': {
                    'archive_services': 'user.gw1000.GatewayService'}}}
        # set the IP address we will use, if we received an IP address via the
        # command line use it, otherwise use a fake address
        config['GW1000']['ip_address'] = cls.ip_address if cls.ip_address is not None else Gw1000TestCase.fake_ip
        # set the port number we will use, if we received a port number via the
        # command line use it, otherwise use a fake port number
        config['GW1000']['port'] = cls.port if cls.port is not None else Gw1000TestCase.fake_port
        # save the service config dict for use later
        cls.gw1000_svc_config = config

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_system_params')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_map(self, mock_get_mac, mock_get_firmware, mock_get_sys):
        """Test GW1000Service GW1000 to WeeWX mapping

        Tests:
        1. field dateTime is included in the GW1000 mapped data
        2. field usUnits is included in the GW1000 mapped data
        3. GW1000 obs data is correctly mapped to a WeeWX fields
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = Gw1000TestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = Gw1000TestCase.mock_get_firm_resp
        # get_system_params() - system parameters (bytestring)
        mock_get_sys.return_value = Gw1000TestCase.mock_sys_params_resp
        # obtain a GW1000 service
        gw1000_svc = self.get_gw1000_svc(caller='test_map')
        # get a mapped  version of our GW1000 test data
        mapped_gw1000_data = gw1000_svc.map_data(self.gw1000_data)
        # check that our mapped data has a field 'dateTime'
        self.assertIn('dateTime', mapped_gw1000_data)
        # check that our mapped data has a field 'usUnits'
        self.assertIn('usUnits', mapped_gw1000_data)
        # check that the usUnits field is set to weewx.METRICWX
        self.assertEqual(weewx.METRICWX, mapped_gw1000_data.get('usUnits'))

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_system_params')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_rain(self, mock_get_mac, mock_get_firmware, mock_get_sys):
        """Test GW1000Service correctly calculates WeeWX field rain

        Tests:
        1. field rain is included in the GW1000 data
        2. field rain is set to None if this is the first packet
        2. field rain is correctly calculated for a subsequent packet
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = Gw1000TestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = Gw1000TestCase.mock_get_firm_resp
        mock_get_sys.return_value = Gw1000TestCase.mock_sys_params_resp
        # obtain a GW1000 service
        gw1000_svc = self.get_gw1000_svc(caller='test_map')
        # set some GW1000 service parameters to enable rain related tests
        gw1000_svc.rain_total_field = 'raintotals'
        gw1000_svc.rain_mapping_confirmed = True
        # take a copy of our test data as we will be changing it
        _gw1000_data = dict(self.gw1000_data)
        # perform the rain calculation
        gw1000_svc.calculate_rain(_gw1000_data)
        # check that our data now has field 'rain'
        self.assertIn('rain', _gw1000_data)
        # check that the field rain is None as this is the first packet
        self.assertIsNone(_gw1000_data.get('rain', 1))
        # increment increase the rainfall in our GW1000 data
        _gw1000_data['raintotals'] += self.increment
        # perform the rain calculation
        gw1000_svc.calculate_rain(_gw1000_data)
        # Check that the field rain is now the increment we used. Use
        # AlmostEqual as unit conversion could cause assertEqual to fail.
        self.assertAlmostEqual(_gw1000_data.get('rain'), self.increment, places=3)
        # check delta_rain calculation
        # last_rain is None
        self.assertIsNone(gw1000_svc.delta_rain(rain=10.2, last_rain=None))
        # rain is None
        self.assertIsNone(gw1000_svc.delta_rain(rain=None, last_rain=5.2))
        # rain < last_rain
        self.assertEqual(gw1000_svc.delta_rain(rain=4.2, last_rain=5.8), 4.2)
        # rain and last_rain are not None
        self.assertAlmostEqual(gw1000_svc.delta_rain(rain=12.2, last_rain=5.8),
                               6.4,
                               places=3)

    @patch.object(user.gw1000.GatewayCollector.Station, 'get_system_params')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayCollector.Station, 'get_mac_address')
    def test_lightning(self, mock_get_mac, mock_get_firmware, mock_get_sys):
        """Test GW1000Service correctly calculates WeeWX field lightning_strike_count

        Tests:
        1. field lightning_strike_count is included in the GW1000 data
        2. field lightning_strike_count is set to None if this is the first
           packet
        2. field lightning_strike_count is correctly calculated for a
           subsequent packet
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = Gw1000TestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = Gw1000TestCase.mock_get_firm_resp
        mock_get_sys.return_value = Gw1000TestCase.mock_sys_params_resp
        # obtain a GW1000 service
        gw1000_svc = self.get_gw1000_svc(caller='test_map')
        # take a copy of our test data as we will be changing it
        _gw1000_data = dict(self.gw1000_data)
        # perform the lightning calculation
        gw1000_svc.calculate_lightning_count(_gw1000_data)
        # check that our data now has field 'lightning_strike_count'
        self.assertIn('lightning_strike_count', _gw1000_data)
        # check that the field lightning_strike_count is None as this is the
        # first packet
        self.assertIsNone(_gw1000_data.get('lightning_strike_count', 1))
        # increment increase the lightning count in our GW1000 data
        _gw1000_data['lightningcount'] += self.increment
        # perform the lightning calculation
        gw1000_svc.calculate_lightning_count(_gw1000_data)
        # check that the field lightning_strike_count is now the increment we
        # used
        self.assertAlmostEqual(_gw1000_data.get('lightning_strike_count'),
                               self.increment,
                               places=1)
        # check delta_lightning calculation
        # last_count is None
        self.assertIsNone(gw1000_svc.delta_lightning(count=10, last_count=None))
        # count is None
        self.assertIsNone(gw1000_svc.delta_lightning(count=None, last_count=5))
        # count < last_count
        self.assertEqual(gw1000_svc.delta_lightning(count=42, last_count=58), 42)
        # count and last_count are not None
        self.assertEqual(gw1000_svc.delta_lightning(count=122, last_count=58), 64)

    def get_gw1000_svc(self, caller):
        """Get a GW1000 service.

        Start a dummy engine with the GW1000 driver running as a service.
        Return a copy of the GW1000 service for use in unit tests.

        Returns a running GW1000 service or raises a unittest.SkipTest
        exception.
        """

        # create a dummy engine, wrap in a try..except in case there is an
        # error
        try:
            engine = weewx.engine.StdEngine(self.gw1000_svc_config)
        except user.gw1000.GWIOError as e:
            # could not communicate with the mocked or real GW1000 for some
            # reason, skip the test if we have an engine try to shut it down
            if engine:
                print("\nShutting down engine ... ", end='')
                engine.shutDown()
            # now raise unittest.SkipTest to skip this test class
            raise unittest.SkipTest("%s: Unable to connect to GW1000" % caller)
        else:
            # Our GW1000 service will have been instantiated by the engine
            # during its startup. Whilst access to the service is not normally
            # required we require access here so we can obtain info about the
            # station we are using for this test. The engine does not provide a
            # ready means to access that GW1000 service so we can do a bit of
            # guessing and iterate over all of the engine's services and select
            # the one that has a 'collector' property. Unlikely to cause a
            # problem since there are only two services in the dummy engine.
            gw1000_svc = None
            for svc in engine.service_obj:
                if hasattr(svc, 'collector'):
                    gw1000_svc = svc
            if gw1000_svc:
                # tell the user what device we are using
                if gw1000_svc.collector.station.ip_address.decode() == Gw1000TestCase.fake_ip:
                    _stem = "\nUsing mocked GW1x00 at %s:%d ... "
                else:
                    _stem = "\nUsing real GW1x00 at %s:%d ... "
                print(_stem % (gw1000_svc.collector.station.ip_address.decode(),
                               gw1000_svc.collector.station.port),
                      end='')
            else:
                # we could not get the GW1000 service for some reason, shutdown
                # the engine and skip this test
                if engine:
                    print("\nShutting down engine ... ", end='')
                    engine.shutDown()
                # now skip this test class
                raise unittest.SkipTest("%s: Could not obtain GW1000Service object" % caller)
            return gw1000_svc


def hex_to_bytes(hex_string):
    """Takes a string of hex character pairs and returns a string of bytes.

    Allows us to specify a byte string in a little more human readable format.
    Takes a space delimited string of hex pairs and converts to a string of
    bytes. hex_string pairs must be spaced delimited, eg 'AB 2E 3B'.

    If we only ran under python3 we could use bytes.fromhex(), but we need to
    cater for python2 as well so use struct.pack.
    """

    # first get our hex string as a list of integers
    dec_list = [int(a, 16) for a in hex_string.split()]
    # now pack them in a sequence of bytes
    return struct.pack('B' * len(dec_list), *dec_list)


def bytes_to_hex(iterable, separator=' ', caps=True):
    """Produce a hex string representation of a sequence of bytes."""

    # assume 'iterable' can be iterated by iterbytes and the individual
    # elements can be formatted with {:02X}
    format_str = "{:02X}" if caps else "{:02x}"
    try:
        return separator.join(format_str.format(c) for c in six.iterbytes(iterable))
    except ValueError:
        # most likely we are running python3 and iterable is not a bytestring,
        # try again coercing iterable to a bytestring
        return separator.join(format_str.format(c) for c in six.iterbytes(six.b(iterable)))
    except (TypeError, AttributeError):
        # TypeError - 'iterable' is not iterable
        # AttributeError - likely because separator is None
        # either way we can't represent as a string of hex bytes
        return "cannot represent '%s' as hexadecimal bytes" % (iterable,)


def xbytes(num, hex_string='00', separator=' '):
    """Construct a string of delimited repeated hex pairs.

    Resulting string contains num occurrences of hex_string separated by
    separator.
    """

    return separator.join([hex_string] * num)


def suite(test_cases):
    """Create a TestSuite object containing the tests we are to perform."""

    # get a test loader
    loader = unittest.TestLoader()
    # create an empty test suite
    suite = unittest.TestSuite()
    # iterate over the test cases we are to add
    for test_class in test_cases:
        # get the tests from the test case
        tests = loader.loadTestsFromTestCase(test_class)
        # add the tests to the test suite
        suite.addTests(tests)
    # finally return the populated test suite
    return suite


def main():
    import argparse

    # test cases that are production ready
    test_cases = (SensorsTestCase, ParseTestCase, UtilitiesTestCase,
                  ListsAndDictsTestCase, StationTestCase, Gw1000TestCase)

    usage = """python -m user.tests.test_gw1000 --help
           python -m user.tests.test_gw1000 --version
           python -m user.tests.test_gw1000 [-v|--verbose=VERBOSITY] [--ip-address=IP_ADDRESS] [--port=PORT]

        Arguments:

           VERBOSITY: Path and file name of the WeeWX configuration file to be used.
                        Default is weewx.conf.
           IP_ADDRESS: IP address to use to contact GW1000. If omitted discovery is used.
           PORT: Port to use to contact GW1000. If omitted discovery is used."""
    description = 'Test the GW1000 driver code.'
    epilog = """You must ensure the WeeWX modules are in your PYTHONPATH. For example:

    PYTHONPATH=/home/weewx/bin python -m user.tests.test_gw1000 --help
    """

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', dest='version', action='store_true',
                        help='display GW1000 driver test suite version number')
    parser.add_argument('--verbose', dest='verbosity', type=int, metavar="VERBOSITY",
                        default=2,
                        help='How much status to display, 0-2')
    parser.add_argument('--ip-address', dest='ip_address', metavar="IP_ADDRESS",
                        help='GW1000 IP address to use')
    parser.add_argument('--port', dest='port', type=int, metavar="PORT",
                        help='GW1000 port to use')
    # parse the arguments
    args = parser.parse_args()

    # display version number
    if args.version:
        print("%s test suite version: %s" % (TEST_SUITE_NAME, TEST_SUITE_VERSION))
        print("args=%s" % (args,))
        exit(0)
    # run the tests
    # first set the IP address and port to use in StationTestCase and
    # Gw1000TestCase
    StationTestCase.ip_address = args.ip_address
    StationTestCase.port = args.port
    Gw1000TestCase.ip_address = args.ip_address
    Gw1000TestCase.port = args.port
    # get a test runner with appropriate verbosity
    runner = unittest.TextTestRunner(verbosity=args.verbosity)
    # create a test suite and run the included tests
    runner.run(suite(test_cases))


if __name__ == '__main__':
    main()
