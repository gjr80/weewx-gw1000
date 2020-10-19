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
import unittest
import user.gw1000


class ParseTestCase(unittest.TestCase):

    response_data = 'FF FF 27 00 40 01 01 40 06 26 08 27 D2 09 27 D2 2A 00 5A ' \
                    '4D 00 65 2C 27 2E 14 1A 00 ED 22 3A 1B 01 0B 23 3A 4C 06 ' \
                    '00 00 00 05 FF FF 00 F6 FF FF FF FF FF FF FF 62 00 00 00 ' \
                    '00 61 FF FF FF FF 60 FF EC'
    parsed_response= {'intemp': 32.0,
                      'inhumid': 38,
                      'absbarometer': 1019.4,
                      'relbarometer': 1019.4,
                      'pm251': 9.0,
                      'pm251_24hav': 10.1,
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
    dir_data = '00 70'      # 112
    # speed_data = ''
    # rain_data =''
    # rainrate_data = ''
    # big_rain_data = ''
    # light_data = ''
    # uv_data = ''
    # uvi_data = ''
    # datetime_data = ''
    # leak_data = ''
    # distance_data = ''
    # utc_data = ''
    # count_data = ''
    # temp_batt_data = ''

    def setUp(self):

        # get a Parser object
        self. parser = user.gw1000.Gw1000Collector.Parser()

    def tearDown(self):

        pass

    def test_decode(self):

        # test temperature decode correctly handles too few and too many bytes
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(3))), None)
        # self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(2))), None)
        # test pressure decode correctly handles too few and too many bytes
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(3))), None)
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data)), 112)
        # test direction decode correctly handles too few and too many bytes
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(3))), None)
        # test air quality decode correctly handles too few and too many bytes
        self.assertEqual(self.parser.decode_aq(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(self.parser.decode_aq(hex_to_bytes(xbytes(3))), None)
        # self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(2))), None)
        # test parsing of all possible sensors
        self.assertDictEqual(self.parser.parse(raw_data=hex_to_bytes(self.response_data),timestamp=1599021263),
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
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff0066b2')),
                         'FF 00 66 B2')
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff0066b2'), separator=':'),
                         'FF:00:66:B2')
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff0066b2'), caps=False),
                         'ff 00 66 b2')
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff0066b2'), separator=':', caps=False),
                         'ff:00:66:b2')
        # and check exceptions raised
        # ValueError
        self.assertEqual(user.gw1000.bytes_to_hex('gh'),
                         self.bytes_to_hex_fail_str % 'gh')
        # TypeError
        self.assertEqual(user.gw1000.bytes_to_hex(22),
                         self.bytes_to_hex_fail_str % 22)
        # AttributeError
        self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff0066b2'), separator=None),
                         self.bytes_to_hex_fail_str % hex_to_bytes('ff0066b2'))

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

    return bytes.fromhex(hex_string)


def xbytes(num):

    return ('00 ' * num).strip()


if __name__ == '__main__':
    unittest.main(verbosity=2)
