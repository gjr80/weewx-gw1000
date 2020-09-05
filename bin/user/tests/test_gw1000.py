import unittest
import user.gw1000
import struct


class Gw1000TestCase(unittest.TestCase):

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
    one_byte = '00'
    two_byte = '00 00'
    three_byte = '00 00 00'

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

    def setUp(self):

        pass

    def test_station(self):

        # get a Gw1000Collector Station object, specify phony ip, port and mac
        # to prevent the GW1000 driver from actually looking for a GW1000
        station = user.gw1000.Gw1000Collector.Station(ip_address='1.1.1.1',
                                                      port=1234,
                                                      mac='1:2:3:4:5:6')

        # test checksum calculation
        self.assertEqual(station.calc_checksum(b'00112233bbccddee'), 168)
        # test check_response()
        self.assertEqual(station.check_response(b'00112233bbccddee'), 168)

    def test_decode(self):

        # get a Gw1000Collector Parser object
        parser = user.gw1000.Gw1000Collector.Parser()

        # test temperature decode correctly handles too few and too many bytes
        self.assertEqual(parser.decode_temp(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(parser.decode_temp(hex_to_bytes(xbytes(3))), None)
        # self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(2))), None)
        # test pressure decode correctly handles too few and too many bytes
        self.assertEqual(parser.decode_press(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(parser.decode_press(hex_to_bytes(xbytes(3))), None)
        self.assertEqual(parser.decode_dir(hex_to_bytes(self.dir_data)), 112)
        # test direction decode correctly handles too few and too many bytes
        self.assertEqual(parser.decode_dir(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(parser.decode_dir(hex_to_bytes(xbytes(3))), None)
        # test air quality decode correctly handles too few and too many bytes
        self.assertEqual(parser.decode_aq(hex_to_bytes(xbytes(1))), None)
        self.assertEqual(parser.decode_aq(hex_to_bytes(xbytes(3))), None)
        # self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(2))), None)
        # test parsing of all possible sensors
        self.assertDictEqual(parser.parse(raw_data=hex_to_bytes(self.response_data),timestamp=1599021263),
                             self.parsed_response)

        # test battery state methods
        # battery mask
        self.assertEqual(parser.battery_mask(255, 1 << 3), 1)
        self.assertEqual(parser.battery_mask(4, 1 << 3), 0)
        # battery value
        self.assertEqual(parser.battery_value(0x65, mask=0x0F, shift=4), 6)
        self.assertEqual(parser.battery_value(0x01020304, mask=0xFF, shift=8), 3)
        self.assertEqual(parser.battery_value(5), 5)
        # battery voltage
        self.assertEqual(parser.battery_voltage(100), 2)
        # binary description
        self.assertEqual(parser.binary_desc(0), 'OK')
        self.assertEqual(parser.binary_desc(1), 'low')
        self.assertEqual(parser.binary_desc(2), None)
        self.assertEqual(parser.binary_desc(None), None)
        # voltage description
        self.assertEqual(parser.voltage_desc(0), 'low')
        self.assertEqual(parser.voltage_desc(1.2), 'low')
        self.assertEqual(parser.voltage_desc(1.5), 'OK')
        self.assertEqual(parser.voltage_desc(None), None)
        # level description
        self.assertEqual(parser.level_desc(0), 'low')
        self.assertEqual(parser.level_desc(1), 'low')
        self.assertEqual(parser.level_desc(4), 'OK')
        self.assertEqual(parser.level_desc(6), 'DC')
        self.assertEqual(parser.level_desc(None), None)

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

def hex_to_bytes(hex_string):

    return bytes.fromhex(hex_string)

def xbytes(num):

    return ('00 ' * num).strip()

if __name__ == '__main__':
    unittest.main()
