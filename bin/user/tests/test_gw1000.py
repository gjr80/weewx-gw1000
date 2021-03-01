"""
Test suite for the GW1000 driver.

Copyright (C) 2020 Gary Roderick                   gjroderick<at>gmail.com

A python unittest based test suite for aspects of the GW1000 driver. The test
suite tests correct operation of:

-

Version: 0.1.0b13                                 Date: 1 September 2020

Revision History
    ?? ????? 2020      v0.1.0
        - initial release

To run the test suite:

-   copy this file to the target machine, nominally to the $BIN/user/tests
    directory

-   run the test suite using:

    $ PYTHONPATH=$BIN python3 -m user.tests.test_gw1000
"""
# python imports
import struct
import unittest

# Python 2/3 compatibility shims
import six

# WeeWX imports
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


class ParseTestCase(unittest.TestCase):

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
                       'wh40_batt': 0,
                       'wh26_batt': 0,
                       'wh25_batt': 0,
                       'wh65_batt': 0,
                       'wh31_ch1_batt': 0,
                       'wh31_ch2_batt': 0,
                       'wh31_ch3_batt': 0,
                       'wh31_ch4_batt': 0,
                       'wh31_ch5_batt': 0,
                       'wh31_ch6_batt': 0,
                       'wh31_ch7_batt': 0,
                       'wh31_ch8_batt': 0,
                       'wh51_ch1_batt': 0,
                       'wh51_ch2_batt': 0,
                       'wh51_ch3_batt': 0,
                       'wh51_ch4_batt': 0,
                       'wh51_ch5_batt': 0,
                       'wh51_ch6_batt': 0,
                       'wh51_ch7_batt': 0,
                       'wh51_ch8_batt': 0,
                       'wh51_ch9_batt': 0,
                       'wh51_ch10_batt': 0,
                       'wh51_ch11_batt': 0,
                       'wh51_ch12_batt': 0,
                       'wh51_ch13_batt': 0,
                       'wh51_ch14_batt': 0,
                       'wh51_ch15_batt': 0,
                       'wh51_ch16_batt': 0,
                       'wh57_batt': 5,
                       'wh68_batt': 5.1000000000000005,
                       'ws80_batt': 5.1000000000000005,
                       'wh41_ch1_batt': 6,
                       'wh41_ch2_batt': None,
                       'wh41_ch3_batt': None,
                       'wh41_ch4_batt': None,
                       'wh55_ch1_batt': None,
                       'wh55_ch2_batt': None,
                       'wh55_ch3_batt': None,
                       'wh55_ch4_batt': None,
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
    batt_data = {'hex': '06 00 00 00 04 FF FF FF F6 FF FF FF FF FF FF FF',
                 'value': {'wh40_batt': 0, 'wh26_batt': 0, 'wh25_batt': 0, 'wh65_batt': 0,
                           'wh31_ch1_batt': 0, 'wh31_ch2_batt': 0, 'wh31_ch3_batt': 0,
                           'wh31_ch4_batt': 0, 'wh31_ch5_batt': 0, 'wh31_ch6_batt': 0,
                           'wh31_ch7_batt': 0, 'wh31_ch8_batt': 0, 'wh51_ch1_batt': 0,
                           'wh51_ch2_batt': 0, 'wh51_ch3_batt': 0, 'wh51_ch4_batt': 0,
                           'wh51_ch5_batt': 0, 'wh51_ch6_batt': 0, 'wh51_ch7_batt': 0,
                           'wh51_ch8_batt': 0, 'wh51_ch9_batt': 0, 'wh51_ch10_batt': 0,
                           'wh51_ch11_batt': 0, 'wh51_ch12_batt': 0, 'wh51_ch13_batt': 0,
                           'wh51_ch14_batt': 0, 'wh51_ch15_batt': 0, 'wh51_ch16_batt': 0,
                           'wh57_batt': 4, 'wh68_batt': 5.1000000000000005,
                           'ws80_batt': 5.1000000000000005, 'wh41_ch1_batt': 6,
                           'wh41_ch2_batt': None, 'wh41_ch3_batt': None, 'wh41_ch4_batt': None,
                           'wh55_ch1_batt': None, 'wh55_ch2_batt': None, 'wh55_ch3_batt': None,
                           'wh55_ch4_batt': None}}
    leak_data = {'hex': '3A', 'value': 58}
    distance_data = {'hex': '1A', 'value': 26}
    utc_data = {'hex': '5F 40 72 51', 'value': 1598059089}
    count_data = {'hex': '00 40 72 51', 'value': 4223569}
    wh34_data = {'hex': '00 EA 4D',
                 'field': ('t', 'b'),
                 'value': {'t': 23.4, 'b': 1.54}
                 }
    wh45_data = {'hex': '00 EA 4D 35 6D 28 78 34 3D 62 7E 8D 2A 39 9F 04',
                 'field': ('t', 'h', 'p10', 'p10_24', 'p25', 'p25_24', 'c', 'c_24', 'b'),
                 'value': {'t': 23.4, 'h': 77, 'p10': 1367.7, 'p10_24': 1036.0,
                           'p25': 1337.3, 'p25_24': 2521.4, 'c': 36138, 'c_24': 14751, 'b': 4}
                 }

    def setUp(self):

        # get a Parser object
        self.parser = user.gw1000.Gw1000Collector.Parser()
        self.maxDiff = None

    def tearDown(self):

        pass

    def test_decode(self):

        # test temperature decode
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(self.temp_data['hex'])),
                         self.temp_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(3))), None)

        # test humidity decode
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(self.humid_data['hex'])),
                         self.humid_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(2))), None)

        # test pressure decode
        self.assertEqual(self.parser.decode_press(hex_to_bytes(self.press_data['hex'])),
                         self.press_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(3))), None)

        # test direction decode
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['hex'])),
                         self.dir_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(3))), None)

        # test speed decode
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(self.speed_data['hex'])),
                         self.speed_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_speed(hex_to_bytes(xbytes(3))), None)

        # test rain decode
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(self.rain_data['hex'])),
                         self.rain_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_rain(hex_to_bytes(xbytes(3))), None)

        # test rain rate decode
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(self.rainrate_data['hex'])),
                         self.rainrate_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(xbytes(3))), None)

        # test big rain decode
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(self.big_rain_data['hex'])),
                         self.big_rain_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(5))), None)

        # test light decode
        self.assertEqual(self.parser.decode_light(hex_to_bytes(self.light_data['hex'])),
                         self.light_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(5))), None)

        # test uv decode
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(self.uv_data['hex'])),
                         self.uv_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_uv(hex_to_bytes(xbytes(3))), None)

        # test uvi decode
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(self.uvi_data['hex'])),
                         self.uvi_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(2))), None)

        # test datetime decode
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(self.datetime_data['hex'])),
                         self.datetime_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(7))), None)

        # test pm25 decode
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(self.pm25_data['hex'])),
                         self.pm25_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_pm25(hex_to_bytes(xbytes(3))), None)

        # test moisture decode
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(self.moist_data['hex'])),
                         self.moist_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(2))), None)

        # test battery decode
        self.assertEqual(self.parser.decode_batt(hex_to_bytes(self.batt_data['hex'])),
                         self.batt_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_batt(hex_to_bytes(xbytes(1))), {})
        self.assertEqual(self.parser.decode_batt(hex_to_bytes(xbytes(17))), {})

        # test leak decode
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(self.leak_data['hex'])),
                         self.leak_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(2))), None)

        # test distance decode
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(self.distance_data['hex'])),
                         self.distance_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(0))), None)
        self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(2))), None)

        # test utc decode
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(self.utc_data['hex'])),
                         self.utc_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(5))), None)

        # test count decode
        self.assertEqual(self.parser.decode_count(hex_to_bytes(self.count_data['hex'])),
                         self.count_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(5))), None)

        # test wh34 decode
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(self.wh34_data['hex']), fields=self.wh34_data['field']),
                         self.wh34_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(xbytes(1)), fields=self.wh34_data['field']), {})
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(xbytes(4)), fields=self.wh34_data['field']), {})

        # test wh45 decode
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(self.wh45_data['hex']), fields=self.wh45_data['field']),
                         self.wh45_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(1)), fields=self.wh45_data['field']), {})
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(17)), fields=self.wh45_data['field']), {})

        # test parsing of all possible sensors
        self.assertDictEqual(self.parser.parse(raw_data=hex_to_bytes(self.response_data), timestamp=1599021263),
                             self.parsed_response)

    def test_battery(self):

        # test battery state methods
        # battery mask
        self.assertEqual(self.parser.battery_mask(255, 1 << 3), 1)
        self.assertEqual(self.parser.battery_mask(4, 1 << 3), 0)
        # battery value
        self.assertEqual(self.parser.battery_value(0x65, mask=0x0F, shift=4), 6)
        self.assertEqual(self.parser.battery_value(0x01020304, mask=0xFF, shift=8), 3)
        self.assertEqual(self.parser.battery_value(5), 5)
        # battery voltage
        self.assertEqual(self.parser.battery_voltage(100), 2)
        # binary description
        self.assertEqual(self.parser.binary_desc(0), 'OK')
        self.assertEqual(self.parser.binary_desc(1), 'low')
        self.assertEqual(self.parser.binary_desc(2), None)
        self.assertEqual(self.parser.binary_desc(None), None)
        # voltage description
        self.assertEqual(self.parser.voltage_desc(0), 'low')
        self.assertEqual(self.parser.voltage_desc(1.2), 'low')
        self.assertEqual(self.parser.voltage_desc(1.5), 'OK')
        self.assertEqual(self.parser.voltage_desc(None), None)
        # level description
        self.assertEqual(self.parser.level_desc(0), 'low')
        self.assertEqual(self.parser.level_desc(1), 'low')
        self.assertEqual(self.parser.level_desc(4), 'OK')
        self.assertEqual(self.parser.level_desc(6), 'DC')
        self.assertEqual(self.parser.level_desc(None), None)


class UtilitiesTestCase(unittest.TestCase):

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

        # test natural_sort_keys
        self.assertEqual(user.gw1000.natural_sort_keys(self.unsorted_dict),
                         self.sorted_keys)

        # test natural_sort_dict()
        self.assertEqual(user.gw1000.natural_sort_dict(self.unsorted_dict),
                         self.sorted_dict_str)

        # test bytes_to_hex()
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2')),
                         'FF 00 66 B2')
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=':'),
                         'FF:00:66:B2')
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), caps=False),
                         'ff 00 66 b2')
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=':', caps=False),
                         'ff:00:66:b2')
        # and check exceptions raised
        # TypeError
        self.assertEqual(user.gw1000.bytes_to_hex(22), self.bytes_to_hex_fail_str % 22)
        # AttributeError
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=None),
                         self.bytes_to_hex_fail_str % hex_to_bytes('ff 00 66 b2'))

        # test obfuscate
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

    def test_dicts(self):
        """Test dicts for consistency."""

        for w_field, g_field in six.iteritems(user.gw1000.Gw1000.default_field_map):
            self.assertIn(g_field,
                          user.gw1000.DirectGw1000.gw1000_obs_group_dict.keys(),
                          msg="A field from the GW1000 default field map is missing from the observation group dictionary")
        for g_field, group in six.iteritems(user.gw1000.DirectGw1000.gw1000_obs_group_dict):
            self.assertIn(g_field,
                          user.gw1000.Gw1000.default_field_map.values(),
                          msg="A key from the observation group dictionary is missing from the GW1000 default field map")




class StationTestCase(unittest.TestCase):

    cmd_read_fware_ver = b'\x50'
    read_fware_cmd_bytes = b'\xff\xffP\x03S'
    read_fware_resp_bytes = b'\xff\xffP\x11\rGW1000_V1.6.1v'
    read_fware_resp_bad_checksum_bytes = b'\xff\xffP\x11\rGW1000_V1.6.1w'
    read_fware_resp_bad_cmd_bytes = b'\xff\xffQ\x11\rGW1000_V1.6.1v'

    def setUp(self):

        # get a Gw1000Collector Station object, specify phony ip, port and mac
        # to prevent the GW1000 driver from actually looking for a GW1000
        self.station = user.gw1000.Gw1000Collector.Station(ip_address='1.1.1.1',
                                                           port=1234,
                                                           mac='1:2:3:4:5:6')

    def test_response(self):

        # test checksum calculation
        self.assertEqual(self.station.calc_checksum(b'00112233bbccddee'), 168)
        # test check_response() with good data, should be no exception
        try:
            self.station.check_response(self.read_fware_resp_bytes,
                                        self.cmd_read_fware_ver)
        except user.gw1000.InvalidChecksum:
            self.fail("check_reponse() raised an InvalidChecksum exception")
        except user.gw1000.InvalidApiResponse:
            self.fail("check_reponse() raised an InvalidApiResponse exception")
        # test check_response() with a bad checksum data, should be an InvalidChecksum exception
        self.assertRaises(user.gw1000.InvalidChecksum,
                          self.station.check_response,
                          response=self.read_fware_resp_bad_checksum_bytes,
                          cmd_code=self.cmd_read_fware_ver)
        # test check_response() with a bad response, should be an InvalidApiResponse exception
        self.assertRaises(user.gw1000.InvalidApiResponse,
                          self.station.check_response,
                          response=self.read_fware_resp_bad_cmd_bytes,
                          cmd_code=self.cmd_read_fware_ver)


class Gw1000TestCase(unittest.TestCase):

    def setUp(self):

        pass

    def test_map(self):
        pass

    def test_rain(self):
        pass

    def test_lightning(self):
        pass


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


def xbytes(num, hex_string='00', separator=' '):
    """Construct a string of delimited repeated hex pairs.

    Resulting string contains num occurrences of hex_string separated by
    separator.
    """

    return separator.join([hex_string] * num)


if __name__ == '__main__':
    unittest.main(verbosity=2)
