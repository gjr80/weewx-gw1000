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
import struct
import unittest
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
    """Test the Gw1000Collector Parser class."""

    # batt = {
    #     'multi': (multi_batt, 'battery_mask'),
    #     'wh31': (wh31_batt, 'battery_mask'),
    #     'wh51': (wh51_batt, 'battery_mask'),
    #     'wh41': (wh41_batt, 'battery_value'),
    #     'wh57': (wh57_batt, 'battery_value'),
    #     'wh68': (wh68_batt, 'battery_voltage'),
    #     'ws80': (ws80_batt, 'battery_voltage'),
    #     'wh55': (wh55_batt, 'battery_value'),
    #     'unused': ({}, 'battery_mask')
    # }
    batt_fields = ('multi', 'wh31', 'wh51', 'wh57', 'wh68', 'ws80',
                   'unused', 'wh41', 'wh55')
    battery_state_desc = {'wh24': 'binary_desc',
                          'wh25': 'binary_desc',
                          'wh26': 'binary_desc',
                          'wh31': 'binary_desc',
                          'wh32': 'binary_desc',
                          'wh40': 'binary_desc',
                          'wh41': 'level_desc',
                          'wh51': 'binary_desc',
                          'wh55': 'level_desc',
                          'wh57': 'level_desc',
                          'wh65': 'binary_desc',
                          'wh68': 'voltage_desc',
                          'ws80': 'voltage_desc',
                          }
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
        b'\x63': ('decode_wh34', 3, ('temp9', 'wh34_ch1_batt')),
        b'\x64': ('decode_wh34', 3, ('temp10', 'wh34_ch2_batt')),
        b'\x65': ('decode_wh34', 3, ('temp11', 'wh34_ch3_batt')),
        b'\x66': ('decode_wh34', 3, ('temp12', 'wh34_ch4_batt')),
        b'\x67': ('decode_wh34', 3, ('temp13', 'wh34_ch5_batt')),
        b'\x68': ('decode_wh34', 3, ('temp14', 'wh34_ch6_batt')),
        b'\x69': ('decode_wh34', 3, ('temp15', 'wh34_ch7_batt')),
        b'\x6A': ('decode_wh34', 3, ('temp16', 'wh34_ch8_batt')),
        b'\x70': ('decode_wh45', 16, ('temp17', 'humid17', 'pm10',
                                      'pm10_24h_avg', 'pm255', 'pm255_24h_avg',
                                      'co2', 'co2_24h_avg', 'wh45_batt'))
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

    def test_constants(self):
        """Test constants used by class Parser()."""

        # test battery mask dicts

        # multi_batt
        self.assertEqual(self.parser.multi_batt['wh40']['mask'], 1 << 4)
        self.assertEqual(self.parser.multi_batt['wh26']['mask'], 1 << 5)
        self.assertEqual(self.parser.multi_batt['wh25']['mask'], 1 << 6)
        self.assertEqual(self.parser.multi_batt['wh65']['mask'], 1 << 7)

        # wh31_batt
        for bit in range(8):
            self.assertEqual(self.parser.wh31_batt[bit + 1]['mask'], 1 << bit)

        # wh41_batt
        for bit in range(4):
            self.assertEqual(self.parser.wh41_batt[bit + 1]['shift'], bit * 4)
            self.assertEqual(self.parser.wh41_batt[bit + 1]['mask'], 0x0F)

        # wh51_batt
        for bit in range(16):
            self.assertEqual(self.parser.wh51_batt[bit + 1]['mask'], 1 << bit)

        # wh55_batt
        for bit in range(4):
            self.assertEqual(self.parser.wh55_batt[bit + 1]['shift'], bit * 8)
            self.assertEqual(self.parser.wh55_batt[bit + 1]['mask'], 0xFF)

        # wh57_batt
        self.assertEqual(self.parser.wh57_batt['wh57'], {})

        # wh68_batt
        self.assertEqual(self.parser.wh68_batt['wh68'], {})

        # ws80_batt
        self.assertEqual(self.parser.ws80_batt['ws80'], {})

        # batt
#        self.assertEqual(self.parser.batt, self.batt)

        # batt_fields
        self.assertEqual(self.parser.batt_fields, self.batt_fields)
        
        # battery_state_format
        self.assertEqual(self.parser.battery_state_format, "<BBHBBBBHLBB")

        # battery_state_desc
        self.assertEqual(self.parser.battery_state_desc,
                         self.battery_state_desc)

        # response_struct
        self.assertEqual(self.parser.response_struct, self.response_struct)

        # rain_field_codes
        self.assertEqual(self.parser.rain_field_codes, self.rain_field_codes)

        # wind_field_codes
        self.assertEqual(self.parser.wind_field_codes, self.wind_field_codes)

    def test_decode(self):
        """Test class Parser() methods used to decode obs bytes."""

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
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(self.wh34_data['hex']), fields=self.wh34_data['field']),
                         self.wh34_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(xbytes(1)), fields=self.wh34_data['field']), {})
        self.assertEqual(self.parser.decode_wh34(hex_to_bytes(xbytes(4)), fields=self.wh34_data['field']), {})

        # test wh45 decode (method decode_wh45())
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(self.wh45_data['hex']), fields=self.wh45_data['field']),
                         self.wh45_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(1)), fields=self.wh45_data['field']), {})
        self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(17)), fields=self.wh45_data['field']), {})

        # test battery decode (method decode_batt())
        self.assertEqual(self.parser.decode_batt(hex_to_bytes(self.batt_data['hex'])),
                         self.batt_data['value'])
        # test correct handling of too few and too many bytes
        self.assertEqual(self.parser.decode_batt(hex_to_bytes(xbytes(1))), {})
        self.assertEqual(self.parser.decode_batt(hex_to_bytes(xbytes(17))), {})

        # test parsing of all possible sensors
        self.assertDictEqual(self.parser.parse(raw_data=hex_to_bytes(self.response_data), timestamp=1599021263),
                             self.parsed_response)

    def test_battery(self):
        """Test methods used to parse battery states."""

        # battery mask (method battery_mask())
        self.assertEqual(self.parser.battery_mask(255, 1 << 3), 1)
        self.assertEqual(self.parser.battery_mask(4, 1 << 3), 0)

        # battery value (method battery_value())
        self.assertEqual(self.parser.battery_value(0x65, mask=0x0F, shift=4), 6)
        self.assertEqual(self.parser.battery_value(0x01020304, mask=0xFF, shift=8), 3)
        self.assertEqual(self.parser.battery_value(5), 5)

        # battery voltage (method battery_voltage())
        self.assertEqual(self.parser.battery_voltage(100), 2)

        # binary description (method binary_desc())
        self.assertEqual(self.parser.binary_desc(0), 'OK')
        self.assertEqual(self.parser.binary_desc(1), 'low')
        self.assertEqual(self.parser.binary_desc(2), None)
        self.assertEqual(self.parser.binary_desc(None), None)

        # voltage description (method voltage_desc())
        self.assertEqual(self.parser.voltage_desc(0), 'low')
        self.assertEqual(self.parser.voltage_desc(1.2), 'low')
        self.assertEqual(self.parser.voltage_desc(1.5), 'OK')
        self.assertEqual(self.parser.voltage_desc(None), None)

        # level description (method level_desc())
        self.assertEqual(self.parser.level_desc(0), 'low')
        self.assertEqual(self.parser.level_desc(1), 'low')
        self.assertEqual(self.parser.level_desc(4), 'OK')
        self.assertEqual(self.parser.level_desc(6), 'DC')
        self.assertEqual(self.parser.level_desc(None), None)


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

        # test natural_sort_keys()
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
