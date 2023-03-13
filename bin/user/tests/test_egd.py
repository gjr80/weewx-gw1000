"""
Test suite for the WeeWX Ecowitt gateway driver.

Copyright (C) 2020-22 Gary Roderick                gjroderick<at>gmail.com

A python3 unittest based test suite for aspects of the Ecowitt gateway driver.
The test suite tests correct operation of:

-

Version: 0.5.0                                  Date: ?? April 2022

Revision History
    ?? April 2022       v0.5.0
        -   updated for Ecowitt gateway device driver release 0.5.0
    14 October 2021     v0.4.1
        -   no change, version increment only
    27 September 2021   v0.4.0
        -   updated to work with GW1000 driver v0.4.0
    20 March 2021       v0.3.0
        -   incomplete but works with release v0.3.0
        -   initial release

To run the test suite:

-   copy this file to the target machine, nominally to the $BIN/user/tests
    directory

-   run the test suite using:

    $ PYTHONPATH=$BIN python3 -m user.tests.test_egd [-v]
"""
# python imports
import socket
import struct
import unittest
from unittest.mock import patch

# TODO. Python3 only so remove six
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

TEST_SUITE_NAME = "Gateway driver"
TEST_SUITE_VERSION = "0.5.0"


class SensorsTestCase(unittest.TestCase):
    """Test the Sensors class."""

    # test sensor ID data
    sensor_id_data = 'FF FF 3C 01 54 00 FF FF FF FE FF 00 01 FF FF FF FE FF 00 '\
                     '06 00 00 00 5B 00 04 07 00 00 00 BE 00 04 08 00 00 00 D0 00 04 '\
                     '0F 00 00 CD 19 0D 04 10 00 00 CD 04 1F 00 11 FF FF FF FE 1F 00 '\
                     '15 FF FF FF FE 1F 00 16 00 00 C4 97 06 04 17 FF FF FF FE 0F 00 '\
                     '18 FF FF FF FE 0F 00 19 FF FF FF FE 0F 00 1A 00 00 D3 D3 05 03 '\
                     '1E FF FF FF FE 0F 00 1F 00 00 2A E7 3F 04 34'
    # processed sensor ID data
    sensor_data = {b'\x00': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x01': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x06': {'id': '0000005b', 'battery': 0, 'signal': 4},
                   b'\x07': {'id': '000000be', 'battery': 0, 'signal': 4},
                   b'\x08': {'id': '000000d0', 'battery': 0, 'signal': 4},
                   b'\x0f': {'id': '0000cd19', 'battery': 1.3, 'signal': 4},
                   b'\x10': {'id': '0000cd04', 'battery': None, 'signal': 0},
                   b'\x11': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x15': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x16': {'id': '0000c497', 'battery': 6, 'signal': 4},
                   b'\x17': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x18': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x19': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x1a': {'id': '0000d3d3', 'battery': 5, 'signal': 3},
                   b'\x1e': {'id': 'fffffffe', 'battery': None, 'signal': 0},
                   b'\x1f': {'id': '00002ae7', 'battery': 1.26, 'signal': 4}}
    connected_addresses = [b'\x06', b'\x07', b'\x08', b'\x0f',
                           b'\x10', b'\x16', b'\x1a', b'\x1f']
    batt_sig_data = {'wh31_ch1_batt': 0, 'wh31_ch1_sig': 4,
                     'wh31_ch2_batt': 0, 'wh31_ch2_sig': 4,
                     'wh31_ch3_batt': 0, 'wh31_ch3_sig': 4,
                     'wh41_ch1_batt': 6, 'wh41_ch1_sig': 4,
                     'wh51_ch2_batt': 1.3, 'wh51_ch2_sig': 4,
                     'wh51_ch3_batt': None, 'wh51_ch3_sig': 0,
                     'wh57_batt': 5, 'wh57_sig': 3,
                     'wn34_ch1_batt': 1.26, 'wn34_ch1_sig': 4}

    def setUp(self):

        # get a Sensors object
        self.sensors = user.gw1000.Sensors()

    def test_set_sensor_id_data(self):
        """Test the set_sensor_id_data() method."""

        # test when passed an empty dict
        self.sensors.set_sensor_id_data(None)
        self.assertDictEqual(self.sensors.sensor_data, {})

        # test when passed a zero length data bytestring
        self.sensors.set_sensor_id_data(b'')
        self.assertDictEqual(self.sensors.sensor_data, {})

        # test when passed a valid bytestring
        self.sensors.set_sensor_id_data(hex_to_bytes(self.sensor_id_data))
        self.assertDictEqual(self.sensors.sensor_data, self.sensor_data)

    def test_properties(self):
        """Test class Sensors.sensor_data related property methods."""

        # test when passed an empty dict
        self.sensors.set_sensor_id_data(None)
        # addresses property
        self.assertSequenceEqual(self.sensors.addresses, {}.keys())
        # connected_addresses property
        self.assertListEqual(list(self.sensors.connected_addresses), [])
        # data property
        self.assertDictEqual(self.sensors.data, {})
        # battery_and_signal_data property
        self.assertDictEqual(self.sensors.battery_and_signal_data, {})

        # test when passed a zero length data bytestring
        self.sensors.set_sensor_id_data(b'')
        # addresses property
        self.assertSequenceEqual(self.sensors.addresses, {}.keys())
        # connected_addresses property
        self.assertListEqual(list(self.sensors.connected_addresses), [])
        # data property
        self.assertDictEqual(self.sensors.data, {})
        # battery_and_signal_data property
        self.assertDictEqual(self.sensors.battery_and_signal_data, {})

        # test when passed a valid bytestring
        self.sensors.set_sensor_id_data(hex_to_bytes(self.sensor_id_data))
        # addresses property
        self.assertSequenceEqual(self.sensors.addresses,
                                 self.sensor_data.keys())
        # connected_addresses property
        self.assertListEqual(list(self.sensors.connected_addresses),
                             self.connected_addresses)
        # data property
        self.assertDictEqual(self.sensors.data, self.sensor_data)
        # battery_and_signal_data property
        self.assertDictEqual(self.sensors.battery_and_signal_data, self.batt_sig_data)

    def test_sensor_data_methods(self):
        """Test Sensors.sensor_data related methods."""

        # test when passed an empty dict
        self.sensors.set_sensor_id_data(None)
        # id method
        self.assertRaises(KeyError, self.sensors.id, b'\x00')
        # battery_state method
        self.assertRaises(KeyError, self.sensors.battery_state, b'\x00')
        # signal_level method
        self.assertRaises(KeyError, self.sensors.signal_level, b'\x00')

        # test when passed a zero length data bytestring
        self.sensors.set_sensor_id_data(b'')
        # id method
        self.assertRaises(KeyError, self.sensors.id, b'\x00')
        # battery_state method
        self.assertRaises(KeyError, self.sensors.battery_state, b'\x00')
        # signal_level method
        self.assertRaises(KeyError, self.sensors.signal_level, b'\x00')

        # test when passed a valid bytestring
        self.sensors.set_sensor_id_data(hex_to_bytes(self.sensor_id_data))
        # id method
        # for a non-existent sensor
        self.assertRaises(KeyError, self.sensors.id, b'\x34')
        # for an existing sensor
        self.assertEqual(self.sensors.id(b'\x11'), 'fffffffe')
        self.assertEqual(self.sensors.id(b'\x1a'), '0000d3d3')
        # battery_state method
        # for a non-existent sensor
        self.assertRaises(KeyError, self.sensors.battery_state, b'\x34')
        # for an existing sensor
        self.assertIsNone(self.sensors.battery_state(b'\x11'))
        self.assertEqual(self.sensors.battery_state(b'\x1a'), 5)
        # signal_level method
        # for a non-existent sensor
        self.assertRaises(KeyError, self.sensors.signal_level, b'\x34')
        # for an existing sensor
        self.assertEqual(self.sensors.signal_level(b'\x11'), 0)
        self.assertEqual(self.sensors.signal_level(b'\x1a'), 3)

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

        # voltage battery states (method wh40_batt_volt())
        # first check operation if ignore_legacy_wh40_battery is True
        self.sensors.ignore_wh40_batt = True
        # legacy WH40
        self.assertIsNone(self.sensors.wh40_batt_volt(0))
        self.assertIsNone(self.sensors.wh40_batt_volt(15))
        self.assertIsNone(self.sensors.wh40_batt_volt(19))
        # contemporary WH40
        self.assertEqual(self.sensors.wh40_batt_volt(20), 0.20)
        self.assertEqual(self.sensors.wh40_batt_volt(150), 1.50)
        self.assertEqual(self.sensors.wh40_batt_volt(255), 2.55)
        # now check operation if ignore_legacy_wh40_battery is False
        self.sensors.ignore_wh40_batt = False
        # legacy WH40
        self.assertEqual(self.sensors.wh40_batt_volt(0), 0.0)
        self.assertEqual(self.sensors.wh40_batt_volt(15), 1.5)
        self.assertEqual(self.sensors.wh40_batt_volt(19), 1.9)
        # contemporary WH40
        self.assertEqual(self.sensors.wh40_batt_volt(20), 0.20)
        self.assertEqual(self.sensors.wh40_batt_volt(150), 1.50)
        self.assertEqual(self.sensors.wh40_batt_volt(255), 2.55)

        # voltage battery states (method batt_volt_tenth())
        self.assertEqual(self.sensors.batt_volt_tenth(0), 0.00)
        self.assertEqual(self.sensors.batt_volt_tenth(15), 1.5)
        self.assertEqual(self.sensors.batt_volt_tenth(17), 1.7)
        self.assertEqual(self.sensors.batt_volt_tenth(255), 25.5)

        # binary description
        self.assertEqual(self.sensors.batt_state_desc(b'\x00', 0), 'OK')
        self.assertEqual(self.sensors.batt_state_desc(b'\x00', 1), 'low')
        self.assertEqual(self.sensors.batt_state_desc(b'\x00', 2), 'Unknown')
        self.assertEqual(self.sensors.batt_state_desc(b'\x00', None), 'Unknown')

        # int description
        self.assertEqual(self.sensors.batt_state_desc(b'\x16', 0), 'low')
        self.assertEqual(self.sensors.batt_state_desc(b'\x16', 1), 'low')
        self.assertEqual(self.sensors.batt_state_desc(b'\x16', 4), 'OK')
        self.assertEqual(self.sensors.batt_state_desc(b'\x16', 6), 'DC')
        self.assertEqual(self.sensors.batt_state_desc(b'\x16', 7), 'Unknown')
        self.assertEqual(self.sensors.batt_state_desc(b'\x16', None), 'Unknown')

        # voltage description
        self.assertEqual(self.sensors.batt_state_desc(b'\x20', 0), 'low')
        self.assertEqual(self.sensors.batt_state_desc(b'\x20', 1.2), 'low')
        self.assertEqual(self.sensors.batt_state_desc(b'\x20', 1.5), 'OK')
        self.assertEqual(self.sensors.batt_state_desc(b'\x20', None), 'Unknown')


class ParseTestCase(unittest.TestCase):
    """Test the GatewayCollector Parser class."""

    # decode structure for CMD_GW1000_LIVEDATA
    live_data_struct = {
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
        b'\x0D': ('decode_rain', 2, 't_rainevent'),
        b'\x0E': ('decode_rainrate', 2, 't_rainrate'),
        b'\x0F': ('decode_gain_100', 2, 't_raingain'),
        b'\x10': ('decode_rain', 2, 't_rainday'),
        b'\x11': ('decode_rain', 2, 't_rainweek'),
        b'\x12': ('decode_big_rain', 4, 't_rainmonth'),
        b'\x13': ('decode_big_rain', 4, 't_rainyear'),
        b'\x14': ('decode_big_rain', 4, 't_raintotals'),
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
        b'\x63': ('decode_wn34', 3, 'temp9'),
        b'\x64': ('decode_wn34', 3, 'temp10'),
        b'\x65': ('decode_wn34', 3, 'temp11'),
        b'\x66': ('decode_wn34', 3, 'temp12'),
        b'\x67': ('decode_wn34', 3, 'temp13'),
        b'\x68': ('decode_wn34', 3, 'temp14'),
        b'\x69': ('decode_wn34', 3, 'temp15'),
        b'\x6A': ('decode_wn34', 3, 'temp16'),
        b'\x70': ('decode_wh45', 16, ('temp17', 'humid17', 'pm10',
                                      'pm10_24h_avg', 'pm255', 'pm255_24h_avg',
                                      'co2', 'co2_24h_avg')),
        # placeholder for unknown field 0x71
        # b'\x71': (None, None, None),
        b'\x72': ('decode_wet', 1, 'leafwet1'),
        b'\x73': ('decode_wet', 1, 'leafwet2'),
        b'\x74': ('decode_wet', 1, 'leafwet3'),
        b'\x75': ('decode_wet', 1, 'leafwet4'),
        b'\x76': ('decode_wet', 1, 'leafwet5'),
        b'\x77': ('decode_wet', 1, 'leafwet6'),
        b'\x78': ('decode_wet', 1, 'leafwet7'),
        b'\x79': ('decode_wet', 1, 'leafwet8')
    }
    # decode structure for CMD_READ_RAIN
    rain_data_struct = {
        b'\x0D': ('decode_rain', 2, 't_rainevent'),
        b'\x0E': ('decode_rainrate', 2, 't_rainrate'),
        b'\x0F': ('decode_gain_100', 2, 't_raingain'),
        b'\x10': ('decode_big_rain', 4, 't_rainday'),
        b'\x11': ('decode_big_rain', 4, 't_rainweek'),
        b'\x12': ('decode_big_rain', 4, 't_rainmonth'),
        b'\x13': ('decode_big_rain', 4, 't_rainyear'),
        b'\x7A': ('decode_int', 1, 'rain_priority'),
        b'\x7B': ('decode_int', 1, 'rad_comp'),
        b'\x80': ('decode_rainrate', 2, 'p_rainrate'),
        b'\x81': ('decode_rain', 2, 'p_rainevent'),
        b'\x82': ('decode_reserved', 2, 'p_rainhour'),
        b'\x83': ('decode_big_rain', 4, 'p_rainday'),
        b'\x84': ('decode_big_rain', 4, 'p_rainweek'),
        b'\x85': ('decode_big_rain', 4, 'p_rainmonth'),
        b'\x86': ('decode_big_rain', 4, 'p_rainyear'),
        b'\x87': ('decode_rain_gain', 20, None),
        b'\x88': ('decode_rain_reset', 3, None)
    }
    rain_field_codes = (b'\x0D', b'\x0E', b'\x0F', b'\x10',
                        b'\x11', b'\x12', b'\x13', b'\x14',
                        b'\x80', b'\x81', b'\x83', b'\x84',
                        b'\x85', b'\x86')
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
                       'lightningdist': None}
    temp_data = {'data': '00 EA', 'value': 23.4}
    humid_data = {'data': '48', 'value': 72}
    press_data = {'data': '27 4C', 'value': 1006.0,
                  'long': '03 27 4C', 'long_value': 1006.0}
    dir_data = {'data': '00 70', 'value': 112}
    speed_data = {'data': '00 70', 'value': 11.2,
                  'long': '03 00 70', 'long_value': 11.2}
    rain_data = {'data': '01 70', 'value': 36.8,
                 'long': '03 01 70', 'long_value': 36.8}
    rainrate_data = {'data': '00 34', 'value': 5.2,
                     'long': '03 00 34', 'long_value': 5.2}
    big_rain_data = {'data': '01 70 37 21', 'value': 2413136.1}
    light_data = {'data': '02 40 72 51', 'value': 3777800.1}
    uv_data = {'data': '32 70', 'value': 1291.2,
               'long': '03 32 70', 'long_value': 1291.2}
    uvi_data = {'data': '0C', 'value': 12}
    datetime_data = {'data': '0C AB 23 41 56 37', 'value': (12, 171, 35, 65, 86, 55)}
    pm25_data = {'data': '00 39', 'value': 5.7,
                 'long': '03 00 39', 'long_value': 5.7}
    moist_data = {'data': '3A', 'value': 58}
    leak_data = {'data': '3A', 'value': 58}
    pm10_data = {'data': '1C 9D', 'value': 732.5,
                 'long': '05 1C 9D', 'long_value': 732.5}
    co2_data = {'data': '24 73', 'value': 9331}
    wet_data = {'data': '53', 'value': 83}
    rain_reset_data = {'data': '09 01 06',
                       'value': {'day_reset': 9,
                                 'week_reset': 1,
                                 'annual_reset': 6}
                       }
    rain_gain_data = {'data': '00 0A 01 F4 00 64 00 E6 01 CC 01 EA 01 4A 00 '
                              'DE 00 6E 00 14',
                      'value': {'gain0': 0.1,
                                'gain1': 5.0,
                                'gain2': 1.0,
                                'gain3': 2.3,
                                'gain4': 4.6,
                                'gain5': 4.9,
                                'gain6': 3.3,
                                'gain7': 2.22,
                                'gain8': 1.1,
                                'gain9': 0.2
                                }
                      }
    distance_data = {'data': '1A', 'value': 26}
    utc_data = {'data': '5F 40 72 51', 'value': 1598059089}
    count_data = {'data': '00 40 72 51', 'value': 4223569}
    gain_100_data = {'data': '01 F2', 'value': 4.98}
    wn34_data = {'data': '00 EA 4D',
                 'field': 't',
                 'value': {'t': 23.4}
                 }
    wh45_data = {'data': '00 EA 4D 35 6D 28 78 34 3D 62 7E 8D 2A 39 9F 04',
                 'field': ('t', 'h', 'p10', 'p10_24', 'p25', 'p25_24', 'c', 'c_24'),
                 'value': {'t': 23.4, 'h': 77, 'p10': 1367.7, 'p10_24': 1036.0,
                           'p25': 1337.3, 'p25_24': 2521.4, 'c': 36138, 'c_24': 14751}
                 }
    # CMD_READ_RAIN test response and decoded data - piezo gauge only
    read_rain_piezo = {'response': 'FF FF 57 00 37 80 00 06 83 00 00 00 4B 84 00 00 '
                                   '00 52 85 00 00 00 BB 86 00 00 00 BB 81 00 4B 87 '
                                   '00 0A 01 F4 00 64 00 E6 01 CC 01 EA 01 4A 00 DE '
                                   '00 6E 00 14 88 09 01 06 FC',
                       'data': {'p_rainrate': 0.6,
                                'p_rainevent': 7.5,
                                'p_rainday': 7.5,
                                'p_rainweek': 8.2,
                                'p_rainmonth': 18.7,
                                'p_rainyear': 18.7,
                                'gain0': 0.1,
                                'gain1': 5.0,
                                'gain2': 1.0,
                                'gain3': 2.3,
                                'gain4': 4.6,
                                'gain5': 4.9,
                                'gain6': 3.3,
                                'gain7': 2.22,
                                'gain8': 1.1,
                                'gain9': 0.2,
                                'day_reset': 9,
                                'week_reset': 1,
                                'annual_reset': 6}
                       }
    # CMD_READ_RAIN test response and decoded data - traditional and piezo
    # gauges
    read_rain_both = {'response': 'FF FF 57 00 54 0E 00 00 10 00 00 00 00 11 '
                                  '00 00 00 00 12 00 00 00 00 13 00 00 0C 11 '
                                  '0D 00 00 0F 00 64 80 00 00 83 00 00 00 00 '
                                  '84 00 00 00 00 85 00 00 00 00 86 00 00 0C '
                                  '72 81 00 00 87 00 64 00 64 00 64 00 64 00 '
                                  '64 00 64 00 64 00 64 00 64 00 64 88 00 00 '
                                  '00 24',
                      'data': {'t_rainrate': 0.0,
                               't_rainevent': 0.0,
                               't_raingain': 10.0,
                               't_rainday': 0.0,
                               't_rainweek': 0.0,
                               't_rainmonth': 0.0,
                               't_rainyear': 308.9,
                               'p_rainrate': 0.0,
                               'p_rainevent': 0.0,
                               'p_rainday': 0.0,
                               'p_rainweek': 0.0,
                               'p_rainmonth': 0.0,
                               'p_rainyear': 318.6,
                               'gain0': 1.0,
                               'gain1': 1.0,
                               'gain2': 1.0,
                               'gain3': 1.0,
                               'gain4': 1.0,
                               'gain5': 1.0,
                               'gain6': 1.0,
                               'gain7': 1.0,
                               'gain8': 1.0,
                               'gain9': 1.0,
                               'day_reset': 0,
                               'week_reset': 0,
                               'annual_reset': 0}
                      }
    # CMD_READ_RAINDATA test response and decoded data
    # TODO. Perhaps have a non-zero value for rainrate
    read_raindata = {'response': 'FF FF 34 17 00 00 00 00 00 00 00 34 '
                                 '00 00 00 34 00 00 01 7B 00 00 09 25 5D',
                     'data': {'t_rainrate': 0.0,
                              't_rainday': 5.2,
                              't_rainweek': 5.2,
                              't_rainmonth': 37.9,
                              't_rainyear': 234.1}
                     }
    get_mulch_offset = {'response': 'FF FF 2C 1B 00 02 15 01 FB E5 02 0A '
                                    '64 03 00 1A 04 06 00 05 F6 9C 06 05 '
                                    '14 07 FB C4 52',
                        'data': {0: {'temp': 2.1, 'hum': 2},
                                 1: {'temp': -2.7, 'hum': -5},
                                 2: {'temp': 10.0, 'hum': 10},
                                 3: {'temp': 2.6, 'hum': 0},
                                 4: {'temp': 0.0, 'hum': 6},
                                 5: {'temp': -10.0, 'hum': -10},
                                 6: {'temp': 2.0, 'hum': 5},
                                 7: {'temp': -6.0, 'hum': -5}
                                 }
                        }
    get_pm25_offset = {'response': 'FF FF 2E 0F 00 00 C8 01 FF 38 02 '
                                   '00 00 03 FF C7 08',
                       'data': {0: 20, 1: -20, 2: 0, 3: -5.7}
                       }
    get_co2_offset = {'response': 'FF FF 53 09 1D C7 00 7B FF CB 5C',
                      'data': {'co2': 7623,
                               'pm25': 12.3,
                               'pm10': -5.3}
                      }
    read_gain = {'response': 'FF FF 36 0F 04 F3 00 35 00 0A 01 F4 01 '
                             'AE 00 64 38',
                 'data': {'uv': 0.53,
                          'solar': 0.1,
                          'wind': 5.0,
                          'rain': 4.3}
                 }
    read_calibration = {'response': 'FF FF 38 13 FF C6 04 FF FF FF E5 '
                                    '00 00 00 31 00 60 09 00 B4 44',
                        'data': {'intemp': -5.8,
                                 'inhum': 4,
                                 'abs': -2.7,
                                 'rel': 4.9,
                                 'outtemp': 9.6,
                                 'outhum': 9,
                                 'dir': 180}
                        }
    get_soilhumiad = {'response': 'FF FF 28 13 00 29 00 EB 01 C8 03 '
                                  'E8 01 35 01 17 01 23 00 C8 3D',
                      'data': {0: {'humidity': 41, 'ad': 235, 'ad_select': 1, 'adj_min': 200, 'adj_max': 1000},
                               1: {'humidity': 53, 'ad': 279, 'ad_select': 1, 'adj_min': 35, 'adj_max': 200}
                               }
                      }
    read_ssss = {'response': 'FF FF 30 0B 00 01 62 66 8E 53 5E 03 46',
                 'data': {'frequency': 0,
                          'sensor_type': 1,
                          'utc': 1650888275,
                          'timezone_index': 94,
                          'dst_status': True}
                 }
    read_ecowitt = {'response': 'FF FF 1E 04 03 23',
                    'data': {'interval': 3}
                    }
    read_wunderground = {'response': 'FF FF 20 16 08 61 62 63 64 65 66 67 '
                                     '68 08 31 32 33 34 35 36 37 38 01 0F',
                         'data': {'id': 'abcdefgh',
                                  'password': '12345678'}
                         }
    read_wow = {'response': 'FF FF 22 1E 07 77 6F 77 31 32 33 34 08 71 61 7A '
                            '78 73 77 65 64 08 00 00 00 00 00 00 00 00 01 F6',
                'data': {'id': 'wow1234',
                         'password': 'qazxswed',
                         'station_num': '\x00\x00\x00\x00\x00\x00\x00\x00'}
                }
    read_weathercloud = {'response': 'FF FF 24 16 08 71 77 65 72 74 79 75 69 '
                                     '08 61 62 63 64 65 66 67 68 01 F9',
                         'data': {'id': 'qwertyui',
                                  'key': 'abcdefgh'}
                         }
    read_customized = {'response': 'FF FF 2A 27 06 31 32 33 34 35 36 08 61 62 '
                                   '63 64 65 66 67 68 0D 31 39 32 2E 31 36 38 '
                                   '2E 32 2E 32 32 30 1F 40 00 14 00 01 C4',
                       'data': {'id': '123456',
                                'password': 'abcdefgh',
                                'server': '192.168.2.220',
                                'port': 8000,
                                'interval': 20,
                                'type': 0,
                                'active': 1}
                       }
    read_usr_path = {'response': 'FF FF 51 12 05 2F 70 61 74 68 08 2F 6D 79 2F '
                                 '70 61 74 68 3D',
                     'data': {'ecowitt_path': '/path',
                              'wu_path': '/my/path'}
                     }
    read_station_mac = {'response': 'FF FF 26 09 E8 68 E7 12 9D D7 EC',
                        'data': 'E8:68:E7:12:9D:D7'
                        }
    read_firmware_version = {'response': 'FF FF 50 12 0E 47 57 32 30 '
                                         '30 30 43 5F 56 32 2E 31 2E 34 BB',
                             'data': 'GW2000C_V2.1.4'
                             }

    def setUp(self):

        # get a Parser object
        self.parser = user.gw1000.ApiParser()
        self.maxDiff = None

    def tearDown(self):

        pass

    def test_constants(self):
        """Test constants"""

        # test live_data_struct
        self.assertEqual(self.parser.live_data_struct, self.live_data_struct)

        # test rain_data_struct
        self.assertEqual(self.parser.rain_data_struct, self.rain_data_struct)

        # test rain_field_codes
        self.assertEqual(self.parser.rain_field_codes, self.rain_field_codes)

        # wind_field_codes
        self.assertEqual(self.parser.wind_field_codes, self.wind_field_codes)

    def test_parse(self):
        """Test methods used to parse API response data."""

        # test parse_livedata()
        self.assertDictEqual(self.parser.parse_livedata(response=hex_to_bytes(self.response_data)),
                             self.parsed_response)

        # test parse_read_rain() with piezo gauge only
        self.assertDictEqual(self.parser.parse_read_rain(response=hex_to_bytes(self.read_rain_piezo['response'])),
                             self.read_rain_piezo['data'])

        # test parse_read_rain() with both traditional and piezo gauges
        self.assertDictEqual(self.parser.parse_read_rain(response=hex_to_bytes(self.read_rain_both['response'])),
                             self.read_rain_both['data'])

        # test parse_read_raindata()
        self.assertDictEqual(self.parser.parse_read_raindata(response=hex_to_bytes(self.read_raindata['response'])),
                             self.read_raindata['data'])

        # test parse_get_mulch_offset()
        self.assertDictEqual(self.parser.parse_get_mulch_offset(response=hex_to_bytes(self.get_mulch_offset['response'])),
                             self.get_mulch_offset['data'])

        # test parse_get_pm25_offset()
        self.assertDictEqual(self.parser.parse_get_pm25_offset(response=hex_to_bytes(self.get_pm25_offset['response'])),
                             self.get_pm25_offset['data'])

        # test parse_get_co2_offset()
        self.assertDictEqual(self.parser.parse_get_co2_offset(response=hex_to_bytes(self.get_co2_offset['response'])),
                             self.get_co2_offset['data'])

        # test parse_read_gain()
        self.assertDictEqual(self.parser.parse_read_gain(response=hex_to_bytes(self.read_gain['response'])),
                             self.read_gain['data'])

        # test parse_read_calibration()
        self.assertDictEqual(self.parser.parse_read_calibration(response=hex_to_bytes(self.read_calibration['response'])),
                             self.read_calibration['data'])

        # test parse_get_soilhumiad()
        self.assertDictEqual(self.parser.parse_get_soilhumiad(response=hex_to_bytes(self.get_soilhumiad['response'])),
                             self.get_soilhumiad['data'])

        # test read_ssss()
        self.assertDictEqual(self.parser.parse_read_ssss(response=hex_to_bytes(self.read_ssss['response'])),
                             self.read_ssss['data'])

        # test parse_read_ecowitt()
        self.assertDictEqual(self.parser.parse_read_ecowitt(response=hex_to_bytes(self.read_ecowitt['response'])),
                             self.read_ecowitt['data'])

        # test parse_read_wunderground()
        self.assertDictEqual(self.parser.parse_read_wunderground(response=hex_to_bytes(self.read_wunderground['response'])),
                             self.read_wunderground['data'])

        # test parse_read_wow()
        self.assertDictEqual(self.parser.parse_read_wow(response=hex_to_bytes(self.read_wow['response'])),
                             self.read_wow['data'])

        # test parse_read_weathercloud()
        self.assertDictEqual(self.parser.parse_read_weathercloud(response=hex_to_bytes(self.read_weathercloud['response'])),
                             self.read_weathercloud['data'])

        # test parse_read_customized()
        self.assertDictEqual(self.parser.parse_read_customized(response=hex_to_bytes(self.read_customized['response'])),
                             self.read_customized['data'])

        # test parse_read_usr_path()
        self.assertDictEqual(self.parser.parse_read_usr_path(response=hex_to_bytes(self.read_usr_path['response'])),
                             self.read_usr_path['data'])

        # test parse_read_station_mac()
        self.assertEqual(self.parser.parse_read_station_mac(response=hex_to_bytes(self.read_station_mac['response'])),
                         self.read_station_mac['data'])

        # test parse_read_firmware_version()
        self.assertEqual(self.parser.parse_read_firmware_version(response=hex_to_bytes(self.read_firmware_version['response'])),
                         self.read_firmware_version['data'])

    def test_decode(self):
        """Test methods used to decode observation byte data"""

        # test temperature decode (method decode_temp())
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(self.temp_data['data'])),
                         self.temp_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_temp(hex_to_bytes(self.temp_data['data']), field='test'),
                             {'test': self.temp_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(3))), None)

        # test humidity decode (method decode_humid())
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(self.humid_data['data'])),
                         self.humid_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_humid(hex_to_bytes(self.humid_data['data']), field='test'),
                             {'test': self.humid_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(2))), None)

        # test pressure decode (method decode_press())
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.press_data['data'])),
                         self.press_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_press(hex_to_bytes(self.press_data['data']), field='test'),
                             {'test': self.press_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.press_data['long'])),
                         self.press_data['long_value'])

        # test direction decode (method decode_dir())
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['data'])),
                         self.dir_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['data']), field='test'),
                             {'test': self.dir_data['value']})
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['data']), field='test'),
                             {'test': self.dir_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(3))), None)

        # test big rain decode (method decode_big_rain())
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(self.big_rain_data['data'])),
                         self.big_rain_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_big_rain(hex_to_bytes(self.big_rain_data['data']), field='test'),
                             {'test': self.big_rain_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(5))), None)

        # test datetime decode (method decode_datetime())
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(self.datetime_data['data'])),
                         self.datetime_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_datetime(hex_to_bytes(self.datetime_data['data']), field='test'),
                             {'test': self.datetime_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(7))), None)

        # test distance decode (method decode_distance())
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(self.distance_data['data'])),
                         self.distance_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_distance(hex_to_bytes(self.distance_data['data']), field='test'),
                             {'test': self.distance_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(2))), None)

        # test utc decode (method decode_utc())
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(self.utc_data['data'])),
                         self.utc_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_utc(hex_to_bytes(self.utc_data['data']), field='test'),
                             {'test': self.utc_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(5))), None)

        # test count decode (method decode_count())
        self.assertEqual(self.parser.decode_count(hex_to_bytes(self.count_data['data'])),
                         self.count_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_count(hex_to_bytes(self.count_data['data']), field='test'),
                             {'test': self.count_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(5))), None)

        # test sensor gain decode (method decode_gain_100())
        self.assertEqual(self.parser.decode_gain_100(hex_to_bytes(self.gain_100_data['data'])),
                         self.gain_100_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_gain_100(hex_to_bytes(self.gain_100_data['data']), field='test'),
                             {'test': self.gain_100_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_gain_100(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_gain_100(hex_to_bytes(xbytes(5))), None)

        # test speed decode (method decode_speed())
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(self.speed_data['data'])),
                         self.speed_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_speed(hex_to_bytes(self.speed_data['data']), field='test'),
                             {'test': self.speed_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.speed_data['long'])),
                         self.speed_data['long_value'])

        # test rain decode (method decode_rain())
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(self.rain_data['data'])),
                         self.rain_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_rain(hex_to_bytes(self.rain_data['data']), field='test'),
                             {'test': self.rain_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.rain_data['long'])),
                         self.rain_data['long_value'])

        # test rain rate decode (method decode_rainrate())
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(self.rainrate_data['data'])),
                         self.rainrate_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_rainrate(hex_to_bytes(self.rainrate_data['data']), field='test'),
                             {'test': self.rainrate_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.rainrate_data['long'])),
                         self.rainrate_data['long_value'])

        # test light decode (method decode_light())
        self.assertEqual(self.parser.decode_light(hex_to_bytes(self.light_data['data'])),
                         self.light_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_light(hex_to_bytes(self.light_data['data']), field='test'),
                             {'test': self.light_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(5))), None)

        # test uv decode (method decode_uv())
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(self.uv_data['data'])),
                         self.uv_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_uv(hex_to_bytes(self.uv_data['data']), field='test'),
                             {'test': self.uv_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.uv_data['long'])),
                         self.uv_data['long_value'])

        # test uvi decode (method decode_uvi())
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(self.uvi_data['data'])),
                         self.uvi_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_uvi(hex_to_bytes(self.uvi_data['data']), field='test'),
                             {'test': self.uvi_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(2))), None)

        # test moisture decode (method decode_moist())
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(self.moist_data['data'])),
                         self.moist_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_moist(hex_to_bytes(self.moist_data['data']), field='test'),
                             {'test': self.moist_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(2))), None)

        # test pm25 decode (method decode_pm25())
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(self.pm25_data['data'])),
                         self.pm25_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_pm25(hex_to_bytes(self.pm25_data['data']), field='test'),
                             {'test': self.pm25_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.pm25_data['long'])),
                         self.pm25_data['long_value'])

        # test leak decode (method decode_leak())
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(self.leak_data['data'])),
                         self.leak_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_leak(hex_to_bytes(self.leak_data['data']), field='test'),
                             {'test': self.leak_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(2))), None)

        # test pm10 decode (method decode_pm10())
        self.assertEqual(self.parser.decode_pm10(hex_to_bytes(self.pm10_data['data'])),
                         self.pm10_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_pm10(hex_to_bytes(self.pm10_data['data']), field='test'),
                             {'test': self.pm10_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_pm10(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_pm10(hex_to_bytes(self.pm10_data['long'])),
                         self.pm10_data['long_value'])

        # test co2 decode (method decode_co2())
        self.assertEqual(self.parser.decode_co2(hex_to_bytes(self.co2_data['data'])),
                         self.co2_data['value'])
        # test decode with field != None
        self.assertDictEqual(self.parser.decode_co2(hex_to_bytes(self.co2_data['data']), field='test'),
                             {'test': self.co2_data['value']})
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_co2(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_co2(hex_to_bytes(xbytes(3))), None)

        # test wetness decode (method decode_wet())
        self.assertEqual(self.parser.decode_wet(hex_to_bytes(self.wet_data['data'])),
                         self.wet_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wet(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_wet(hex_to_bytes(xbytes(2))), None)

        # test wn34 decode (method decode_wn34())
        self.assertEqual(self.parser.decode_wn34(hex_to_bytes(self.wn34_data['data']), field=self.wn34_data['field']),
                         self.wn34_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wn34(hex_to_bytes(xbytes(1)), field=self.wn34_data['field']), {})
        self.assertEqual(self.parser.decode_wn34(hex_to_bytes(xbytes(4)), field=self.wn34_data['field']), {})

        # test wh45 decode (method decode_wh45())
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(self.wh45_data['data']), fields=self.wh45_data['field']),
                         self.wh45_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(1)), fields=self.wh45_data['field']),
                         {})
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(17)), fields=self.wh45_data['field']),
                         {})

        # test rain gain decode (method decode_rain_gain())
        self.assertDictEqual(self.parser.decode_rain_gain(hex_to_bytes(self.rain_gain_data['data'])),
                             self.rain_gain_data['value'])
        # test correct handling of too few and too many bytes
        self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(xbytes(0))), {})
        self.assertDictEqual(self.parser.decode_rain_gain(hex_to_bytes(xbytes(2))), {})

        # test rain reset decode (method decode_rain_reset())
        self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(self.rain_reset_data['data'])),
                             self.rain_reset_data['value'])
        # test correct handling of too few and too many bytes
        self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(xbytes(0))), {})
        self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(xbytes(2))), {})

        # test battery status decode (method decode_batt())
        # decode_batt() is obfuscated and should always return None
        # irrespective of how it is called
        self.assertIsNone(self.parser.decode_batt(''))


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
        for w_field, g_field in self.default_field_map.items():
            self.assertIn(g_field,
                          user.gw1000.DirectGateway.gateway_obs_group_dict.keys(),
                          msg="A field from the GW1000 default field map is "
                              "missing from the observation group dictionary")

#        # test that each entry in the observation group dictionary is included
#        # in the GW1000 default field map
#        for g_field, group in user.gw1000.DirectGateway.gateway_obs_group_dict.items():
#            self.assertIn(g_field,
#                          self.default_field_map.values(),
#                          msg="A key from the observation group dictionary is "
#                              "missing from the GW1000 default field map")


class StationTestCase(unittest.TestCase):

    fake_ip = '192.168.99.99'
    fake_port = 44444
    mock_mac = 'A1:B2:C3:D4:E5:F6'
    mock_firmware = ''.join([chr(x) for x in b'\xff\xffP\x11\rGW1000_V1.6.8}'])
    mock_sys_params = {
        'frequency': 0,
        'sensor_type': 1,
        'utc': 1674801882,
        'timezone_index': 94,
        'dst_status': False
    }
    # test sensor ID data
    fake_sensor_id_data = 'FF FF 3C 01 54 00 FF FF FF FE FF 00 01 FF FF FF FE FF 00 '\
                          '06 00 00 00 5B 00 04 07 00 00 00 BE 00 04 08 00 00 00 D0 00 04 '\
                          '0F 00 00 CD 19 0D 04 10 00 00 CD 04 1F 00 11 FF FF FF FE 1F 00 '\
                          '15 FF FF FF FE 1F 00 16 00 00 C4 97 06 04 17 FF FF FF FE 0F 00 '\
                          '18 FF FF FF FE 0F 00 19 FF FF FF FE 0F 00 1A 00 00 D3 D3 05 03 '\
                          '1E FF FF FF FE 0F 00 1F 00 00 2A E7 3F 04 34'

    cmd_read_fware_ver = b'\x50'
    read_fware_cmd_bytes = b'\xff\xffP\x03S'
    read_fware_resp_bytes = b'\xff\xffP\x11\rGW1000_V1.6.1v'
    read_fware_resp_bad_checksum_bytes = b'\xff\xffP\x11\rGW1000_V1.6.1z'
    read_fware_resp_unex_cmd_bytes = b'\xff\xffQ\x11\rGW1000_V1.6.1w'
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
        'CMD_SET_CO2_OFFSET': 'FF FF 54 03 57',
        'CMD_READ_RSTRAIN_TIME': 'FF FF 55 03 58',
        'CMD_WRITE_RSTRAIN_TIME': 'FF FF 56 03 59',
        'CMD_READ_RAIN': 'FF FF 57 03 5A',
        'CMD_WRITE_RAIN': 'FF FF 58 03 5B',
        'CMD_GET_MulCH_T_OFFSET': 'FF FF 59 03 5C'
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
        GatewayCollector.Station object is required to perform some
        StationTestCase tests. If either or both of IP address and port are not
        specified when instantiating a Station object device discovery will be
        initiated which may result in delays or failure of the test case if no
        device is found. To avoid such situations an IP address and port number
        is always used when instantiating a Station object as part of this test
        case.

        The IP address and port number are determined as follows:
        - if --ip-address and --port were specified on the command line then
          the specified parameters are used
        - if --ip-address is specified on the command line but --port was not
          then port 45000 is used
        - if --port is specified on the command line but --ip-address was not
          then a fake IP address is used
        - if neither --ip-address or --port number is specified on the command
          line then a fake IP address and port number are used
        """

        # set the IP address we will use
        cls.test_ip = cls.ip_address if cls.ip_address is not None else StationTestCase.fake_ip
        # set the port number we will use
        cls.test_port = cls.port if cls.port is not None else StationTestCase.fake_port

#    @patch.object(user.gw1000.GatewayApi, 'get_sensor_id')
    @patch.object(user.gw1000.GatewayApi, 'get_system_params')
    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_cmd_vocab(self, mock_get_mac, mock_get_firmware, mock_get_sys):#, mock_get_sensor_id):
#    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
#    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
#    def test_cmd_vocab(self, mock_get_mac, mock_get_firmware):
        """Test command dictionaries for completeness.

        Tests:
        1. Station.api_commands contains all api_commands
        2. the command code for each Station.api_commands agrees with the test suite
        3. all Station.api_commands entries are in the test suite
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (string)
        mock_get_mac.return_value = StationTestCase.mock_mac
        # get_firmware_version - firmware version (string)
        mock_get_firmware.return_value = StationTestCase.mock_firmware
        # get_system_params - system parameters (dict)
        mock_get_sys.return_value = StationTestCase.mock_sys_params
#        # get_sensor_id - get sensor IDs (bytestring)
#        mock_get_sensor_id.return_value = hex_to_bytes(StationTestCase.fake_sensor_id_data)

        # get our mocked Station object
        # TODO. Should not use 'station'
        station = user.gw1000.GatewayApi(ip_address=self.test_ip,
                                         port=self.test_port)
        # Check that the class Station command list is complete. This is a
        # simple check for (1) inclusion of the command and (2) the command
        # code (byte) is correct.
        for cmd, response in self.commands.items():
            # check for inclusion of the command
            self.assertIn(cmd,
                          station.api_commands.keys(),
                          msg="Command '%s' not found in Station.api_commands" % cmd)
            # check the command code byte is correct
            self.assertEqual(hex_to_bytes(response)[2:3],
                             station.api_commands[cmd],
                             msg="Command code for command '%s' in "
                                 "Station.api_commands(0x%s) disagrees with "
                                 "command code in test suite (0x%s)" % (cmd,
                                                                        bytes_to_hex(station.api_commands[cmd]),
                                                                        bytes_to_hex(hex_to_bytes(response)[2:3])))

        # Check that we are testing everything in class Station command list.
        # This is a simple check that only needs to check for inclusion of the
        # command, the validity of the command code is checked in the earlier
        # iteration.
        for cmd, code in station.api_commands.items():
            # check for inclusion of the command
            self.assertIn(cmd,
                          self.commands.keys(),
                          msg="Command '%s' is in Station.api_commands but it is not being tested" % cmd)

    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_calc_checksum(self, mock_get_mac, mock_get_firmware):
        """Test checksum calculation.

        Tests:
        1. calculating the checksum of a bytestring
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.mock_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayApi(ip_address=self.test_ip,
                                         port=self.test_port)
        # test checksum calculation
        self.assertEqual(station.calc_checksum(b'00112233bbccddee'), 168)

    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_build_cmd_packet(self, mock_get_mac, mock_get_firmware):
        """Test construction of an API command packet

        Tests:
        1. building a command packet for each command in Station.api_commands
        2. building a command packet with a payload
        3. building a command packet for an unknown command
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.mock_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayApi(ip_address=self.test_ip,
                                         port=self.test_port)
        # test the command packet built for each API command we know about
        for cmd, packet in self.commands.items():
            self.assertEqual(station.build_cmd_packet(cmd), hex_to_bytes(packet))
        # test a command packet that has a payload
        self.assertEqual(station.build_cmd_packet(self.cmd, hex_to_bytes(self.cmd_payload)),
                         hex_to_bytes(self.cmd_packet))
        # test building a command packet for an unknown command, should be an UnknownCommand exception
        self.assertRaises(user.gw1000.UnknownApiCommand,
                          station.build_cmd_packet,
                          cmd='UNKNOWN_COMMAND')

    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_decode_broadcast_response(self, mock_get_mac, mock_get_firmware):
        """Test decoding of a broadcast response

        Tests:
        1. decode a broadcast response
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.mock_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # get our mocked Station object
        station = user.gw1000.GatewayApi(ip_address=self.test_ip,
                                         port=self.test_port)
        # get the broadcast response test data as a bytestring
        data = hex_to_bytes(self.broadcast_response_data)
        # test broadcast response decode
        self.assertEqual(station.decode_broadcast_response(data), self.decoded_broadcast_response)

    @patch.object(user.gw1000.GatewayApi, 'get_sensor_id')
    @patch.object(user.gw1000.GatewayApi, 'get_system_params')
    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_api_response_validity_check(self, mock_get_mac, mock_get_firmware, mock_get_sys, mock_get_sensor_id):
        """Test validity checking of an API response

        Tests:
        1. checks Station.check_response() with good data
        2. checks that Station.check_response() raises an InvalidChecksum
           exception for a response with an invalid checksum
        3. checks that Station.check_response() raises an UnknownApiCommand
           exception for a response with a valid check sum but an unexpected
           command code
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.mock_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = ''.join([chr(x) for x in b'\xff\xffP\x11\rGW1000_V1.6.8}'])
        # get_system_params() - system parameters (bytestring)
        mock_get_sys.return_value = StationTestCase.mock_sys_params
        # get_sensor_id - get sensor IDs (bytestring)
        mock_get_sensor_id.return_value = hex_to_bytes(StationTestCase.fake_sensor_id_data)

        # get our mocked Station object
        station = user.gw1000.GatewayApi(ip_address=self.test_ip,
                                         port=self.test_port)
        # test check_response() with good data, should be no exception
        try:
            station.check_response(self.read_fware_resp_bytes,
                                   self.cmd_read_fware_ver)
        except user.gw1000.InvalidChecksum:
            self.fail("check_response() raised an InvalidChecksum exception")
        except user.gw1000.UnknownApiCommand:
            self.fail("check_response() raised an UnknownApiCommand exception")
        # test check_response() with a bad checksum data, should be an InvalidChecksum exception
        self.assertRaises(user.gw1000.InvalidChecksum,
                          station.check_response,
                          response=self.read_fware_resp_bad_checksum_bytes,
                          cmd_code=self.cmd_read_fware_ver)
        # test check_response() with a valid checksum but unexpected command
        # code, should be an UnknownApiCommand exception
        self.assertRaises(user.gw1000.UnknownApiCommand,
                          station.check_response,
                          response=self.read_fware_resp_unex_cmd_bytes,
                          cmd_code=self.cmd_read_fware_ver)

    @patch.object(user.gw1000.GatewayApi, 'discover')
    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_discovery(self, mock_get_mac, mock_get_firmware, mock_discover):
        """Test discovery related methods.

        Tests:
        1.
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = StationTestCase.mock_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = b'\xff\xffP\x11\rGW1000_V1.6.8}'
        # discover() - list of discovered devices (list of dicts)
        mock_discover.return_value = StationTestCase.discover_multi_resp
        # get our mocked Station object
        station = user.gw1000.GatewayApi(ip_address=self.test_ip,
                                         port=self.test_port)
        # to use discovery we need to fool the Station object into thinking it
        # used discovery to obtain the current devices IP address and port
        station.ip_discovered = True
        # to speed up testing we can reduce some retries and wait times
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


class GatewayTestCase(unittest.TestCase):
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
                   't_raintotals': 100.3,
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
    # mocked get_sensor_id() response
    mock_sensor_id_resp = 'FF FF 3C 01 54 00 FF FF FF FE FF 00 01 FF FF FF ' \
                          'FE FF 00 02 FF FF FF FE FF 00 03 FF FF FF FE 1F ' \
                          '00 05 00 00 00 E4 00 04 06 00 00 00 5B 00 04 07 ' \
                          '00 00 00 BE 00 04 08 00 00 00 D0 00 04 09 00 00 ' \
                          '00 52 00 04 0A 00 00 00 6C 00 04 0B 00 00 00 C8 ' \
                          '00 04 0C 00 00 00 EE 00 04 0D FF FF FF FE 00 00 ' \
                          '0E 00 00 CD 19 0D 04 0F 00 00 CB D1 0D 04 10 FF ' \
                          'FF FF FE 1F 00 11 00 00 CD 04 1F 00 12 FF FF FF ' \
                          'FE 1F 00 13 FF FF FF FE 1F 00 14 FF FF FF FE 1F ' \
                          '00 15 FF FF FF FE 1F 00 16 00 00 C4 97 06 04 17 ' \
                          'FF FF FF FE 0F 00 18 FF FF FF FE 0F 00 19 FF FF ' \
                          'FF FE 0F 00 1A 00 00 D3 D3 05 00 1B FF FF FF FE ' \
                          '0F 00 1C FF FF FF FE 0F 00 1D FF FF FF FE 0F 00 ' \
                          '1E FF FF FF FE 0F 00 1F 00 00 2A E7 40 04 20 FF ' \
                          'FF FF FE FF 00 21 FF FF FF FE FF 00 22 FF FF FF ' \
                          'FE FF 00 23 FF FF FF FE FF 00 24 FF FF FF FE FF ' \
                          '00 25 FF FF FF FE FF 00 26 FF FF FF FE FF 00 27 ' \
                          'FF FF FF FE 0F 00 28 FF FF FF FE FF 00 29 FF FF ' \
                          'FF FE FF 00 2A FF FF FF FE FF 00 2B FF FF FF FE ' \
                          'FF 00 2C FF FF FF FE FF 00 2D FF FF FF FE FF 00 ' \
                          '2E FF FF FF FE FF 00 2F FF FF FF FE FF 00 30 FF ' \
                          'FF FF FE FF 00 F4'

    @classmethod
    def setUpClass(cls):
        """Setup the GatewayTestCase to perform its tests."""

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
        config['GW1000']['ip_address'] = cls.ip_address if cls.ip_address is not None else GatewayTestCase.fake_ip
        # set the port number we will use, if we received a port number via the
        # command line use it, otherwise use a fake port number
        config['GW1000']['port'] = cls.port if cls.port is not None else GatewayTestCase.fake_port
        # save the service config dict for use later
        cls.gw1000_svc_config = config

    @patch.object(user.gw1000.GatewayApi, 'get_sensor_id')
    @patch.object(user.gw1000.GatewayApi, 'get_system_params')
    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_map(self, mock_get_mac, mock_get_firmware, mock_get_sys, mock_get_sensor_id):
        """Test GW1000Service GW1000 to WeeWX mapping

        Tests:
        1. field dateTime is included in the GW1000 mapped data
        2. field usUnits is included in the GW1000 mapped data
        3. GW1000 obs data is correctly mapped to a WeeWX fields
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = GatewayTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = GatewayTestCase.mock_get_firm_resp
        # get_system_params() - system parameters (bytestring)
        mock_get_sys.return_value = GatewayTestCase.mock_sys_params_resp
        # get_sensor_id - get sensor IDs (bytestring)
        mock_get_sensor_id.return_value = hex_to_bytes(GatewayTestCase.mock_sensor_id_resp)
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

    @patch.object(user.gw1000.GatewayApi, 'get_sensor_id')
    @patch.object(user.gw1000.GatewayApi, 'get_system_params')
    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_rain(self, mock_get_mac, mock_get_firmware, mock_get_sys, mock_get_sensor_id):
        """Test GW1000Service correctly calculates WeeWX field rain

        Tests:
        1. field rain is included in the GW1000 data
        2. field rain is set to None if this is the first packet
        2. field rain is correctly calculated for a subsequent packet
        """

        # set return values for mocked methods
        # get_mac_address - MAC address (bytestring)
        mock_get_mac.return_value = GatewayTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = GatewayTestCase.mock_get_firm_resp
        # get_system_params - system parameters (bytestring)
        mock_get_sys.return_value = GatewayTestCase.mock_sys_params_resp
        # get_sensor_id - get sensor IDs (bytestring)
        mock_get_sensor_id.return_value = hex_to_bytes(GatewayTestCase.mock_sensor_id_resp)
        # obtain a GW1000 service
        gw1000_svc = self.get_gw1000_svc(caller='test_map')
        # set some GW1000 service parameters to enable rain related tests
        gw1000_svc.rain_total_field = 't_raintotals'
        gw1000_svc.rain_mapping_confirmed = True
        # take a copy of our test data as we will be changing it
        _gw1000_data = dict(self.gw1000_data)
        # perform the rain calculation
        gw1000_svc.calculate_rain(_gw1000_data)
        # check that our data now has field 'rain'
        self.assertIn('t_rain', _gw1000_data)
        # check that the field rain is None as this is the first packet
        self.assertIsNone(_gw1000_data['t_rain'])
        # increment increase the rainfall in our GW1000 data
        _gw1000_data['t_raintotals'] += self.increment
        # perform the rain calculation
        gw1000_svc.calculate_rain(_gw1000_data)
        # Check that the field rain is now the increment we used. Use
        # AlmostEqual as unit conversion could cause assertEqual to fail.
        self.assertAlmostEqual(_gw1000_data.get('t_rain'), self.increment, places=3)
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

    @patch.object(user.gw1000.GatewayApi, 'get_sensor_id')
    @patch.object(user.gw1000.GatewayApi, 'get_system_params')
    @patch.object(user.gw1000.GatewayApi, 'get_firmware_version')
    @patch.object(user.gw1000.GatewayApi, 'get_mac_address')
    def test_lightning(self, mock_get_mac, mock_get_firmware, mock_get_sys, mock_get_sensor_id):
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
        mock_get_mac.return_value = GatewayTestCase.fake_mac
        # get_firmware_version - firmware version (bytestring)
        mock_get_firmware.return_value = GatewayTestCase.mock_get_firm_resp
        # get_system_params - system parameters (bytestring)
        mock_get_sys.return_value = GatewayTestCase.mock_sys_params_resp
        # get_sensor_id - get sensor IDs (bytestring)
        mock_get_sensor_id.return_value = hex_to_bytes(GatewayTestCase.mock_sensor_id_resp)
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
                if gw1000_svc.collector.station.ip_address.decode() == GatewayTestCase.fake_ip:
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

    Allows us to specify a byte string in a little more human-readable format.
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
                  ListsAndDictsTestCase, StationTestCase, GatewayTestCase)

    usage = """python3 -m user.tests.test_eg --help
           python3 -m user.tests.test_eg --version
           python3 -m user.tests.test_eg [-v|--verbose=VERBOSITY] [--ip-address=IP_ADDRESS] [--port=PORT]

        Arguments:

           VERBOSITY: Path and file name of the WeeWX configuration file to be used.
                      Default is weewx.conf.
           IP_ADDRESS: IP address to use to contact the gateway device. If omitted 
                       discovery is used.
           PORT: Port to use to contact the gateway device. If omitted discovery is 
                 used."""
    description = 'Test the Ecowitt gateway driver code.'
    epilog = """You must ensure the WeeWX modules are in your PYTHONPATH. For example:

    PYTHONPATH=/home/weewx/bin python3 -m user.tests.test_eg --help
    """

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', dest='version', action='store_true',
                        help='display Ecowitt gateway driver test suite version number')
    parser.add_argument('--verbose', dest='verbosity', type=int, metavar="VERBOSITY",
                        default=2,
                        help='How much status to display, 0-2')
    parser.add_argument('--ip-address', dest='ip_address', metavar="IP_ADDRESS",
                        help='Gateway device IP address to use')
    parser.add_argument('--port', dest='port', type=int, metavar="PORT",
                        help='Gateway device port to use')
    # parse the arguments
    args = parser.parse_args()

    # display version number
    if args.version:
        print("%s test suite version: %s" % (TEST_SUITE_NAME, TEST_SUITE_VERSION))
        print("args=%s" % (args,))
        exit(0)
    # run the tests
    # first set the IP address and port to use in StationTestCase and
    # GatewayTestCase
    StationTestCase.ip_address = args.ip_address
    StationTestCase.port = args.port
    GatewayTestCase.ip_address = args.ip_address
    GatewayTestCase.port = args.port
    # get a test runner with appropriate verbosity
    runner = unittest.TextTestRunner(verbosity=args.verbosity)
    # create a test suite and run the included tests
    runner.run(suite(test_cases))


if __name__ == '__main__':
    main()
