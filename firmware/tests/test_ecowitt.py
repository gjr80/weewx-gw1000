"""
Test suite for the Ecowitt utility.

Copyright (C) 2024 Gary Roderick                   gjroderick<at>gmail.com

A python3 unittest based test suite for aspects of the Ecowitt utility.
The test suite tests correct operation of:

-

Version: 0.1.0a1                                  Date: ? ? 2024

Revision History
    ? ? 2024            v0.1.0
        -   incomplete but works with release v0.1.0a1
        -   initial release

To run the test suite:

-   copy this file to the target machine, nominally to the tests sub-directory
    under the directory containing ecowitt.py

-   run the test suite using:

    $ python3 /path/to/test_ecowitt.py --help
"""
# python imports
import socket
import struct
import unittest

from io import StringIO
from unittest.mock import patch

import ecowitt


TEST_SUITE_NAME = "Ecowitt utility"
TEST_SUITE_VERSION = "0.1.0a1"


class bcolors:
    """Colors used for terminals"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# class ParseTestCase(unittest.TestCase):
#     """Test the GatewayCollector Parser class."""
#
#     # decode structure for CMD_GW1000_LIVEDATA
#     live_data_struct = {
#         b'\x01': ('decode_temp', 2, 'intemp'),
#         b'\x02': ('decode_temp', 2, 'outtemp'),
#         b'\x03': ('decode_temp', 2, 'dewpoint'),
#         b'\x04': ('decode_temp', 2, 'windchill'),
#         b'\x05': ('decode_temp', 2, 'heatindex'),
#         b'\x06': ('decode_humid', 1, 'inhumid'),
#         b'\x07': ('decode_humid', 1, 'outhumid'),
#         b'\x08': ('decode_press', 2, 'absbarometer'),
#         b'\x09': ('decode_press', 2, 'relbarometer'),
#         b'\x0A': ('decode_dir', 2, 'winddir'),
#         b'\x0B': ('decode_speed', 2, 'windspeed'),
#         b'\x0C': ('decode_speed', 2, 'gustspeed'),
#         b'\x0D': ('decode_rain', 2, 't_rainevent'),
#         b'\x0E': ('decode_rainrate', 2, 't_rainrate'),
#         b'\x0F': ('decode_gain_100', 2, 't_raingain'),
#         b'\x10': ('decode_rain', 2, 't_rainday'),
#         b'\x11': ('decode_rain', 2, 't_rainweek'),
#         b'\x12': ('decode_big_rain', 4, 't_rainmonth'),
#         b'\x13': ('decode_big_rain', 4, 't_rainyear'),
#         b'\x14': ('decode_big_rain', 4, 't_raintotals'),
#         b'\x15': ('decode_light', 4, 'light'),
#         b'\x16': ('decode_uv', 2, 'uv'),
#         b'\x17': ('decode_uvi', 1, 'uvi'),
#         b'\x18': ('decode_datetime', 6, 'datetime'),
#         b'\x19': ('decode_speed', 2, 'daymaxwind'),
#         b'\x1A': ('decode_temp', 2, 'temp1'),
#         b'\x1B': ('decode_temp', 2, 'temp2'),
#         b'\x1C': ('decode_temp', 2, 'temp3'),
#         b'\x1D': ('decode_temp', 2, 'temp4'),
#         b'\x1E': ('decode_temp', 2, 'temp5'),
#         b'\x1F': ('decode_temp', 2, 'temp6'),
#         b'\x20': ('decode_temp', 2, 'temp7'),
#         b'\x21': ('decode_temp', 2, 'temp8'),
#         b'\x22': ('decode_humid', 1, 'humid1'),
#         b'\x23': ('decode_humid', 1, 'humid2'),
#         b'\x24': ('decode_humid', 1, 'humid3'),
#         b'\x25': ('decode_humid', 1, 'humid4'),
#         b'\x26': ('decode_humid', 1, 'humid5'),
#         b'\x27': ('decode_humid', 1, 'humid6'),
#         b'\x28': ('decode_humid', 1, 'humid7'),
#         b'\x29': ('decode_humid', 1, 'humid8'),
#         b'\x2A': ('decode_pm25', 2, 'pm251'),
#         b'\x2B': ('decode_temp', 2, 'soiltemp1'),
#         b'\x2C': ('decode_moist', 1, 'soilmoist1'),
#         b'\x2D': ('decode_temp', 2, 'soiltemp2'),
#         b'\x2E': ('decode_moist', 1, 'soilmoist2'),
#         b'\x2F': ('decode_temp', 2, 'soiltemp3'),
#         b'\x30': ('decode_moist', 1, 'soilmoist3'),
#         b'\x31': ('decode_temp', 2, 'soiltemp4'),
#         b'\x32': ('decode_moist', 1, 'soilmoist4'),
#         b'\x33': ('decode_temp', 2, 'soiltemp5'),
#         b'\x34': ('decode_moist', 1, 'soilmoist5'),
#         b'\x35': ('decode_temp', 2, 'soiltemp6'),
#         b'\x36': ('decode_moist', 1, 'soilmoist6'),
#         b'\x37': ('decode_temp', 2, 'soiltemp7'),
#         b'\x38': ('decode_moist', 1, 'soilmoist7'),
#         b'\x39': ('decode_temp', 2, 'soiltemp8'),
#         b'\x3A': ('decode_moist', 1, 'soilmoist8'),
#         b'\x3B': ('decode_temp', 2, 'soiltemp9'),
#         b'\x3C': ('decode_moist', 1, 'soilmoist9'),
#         b'\x3D': ('decode_temp', 2, 'soiltemp10'),
#         b'\x3E': ('decode_moist', 1, 'soilmoist10'),
#         b'\x3F': ('decode_temp', 2, 'soiltemp11'),
#         b'\x40': ('decode_moist', 1, 'soilmoist11'),
#         b'\x41': ('decode_temp', 2, 'soiltemp12'),
#         b'\x42': ('decode_moist', 1, 'soilmoist12'),
#         b'\x43': ('decode_temp', 2, 'soiltemp13'),
#         b'\x44': ('decode_moist', 1, 'soilmoist13'),
#         b'\x45': ('decode_temp', 2, 'soiltemp14'),
#         b'\x46': ('decode_moist', 1, 'soilmoist14'),
#         b'\x47': ('decode_temp', 2, 'soiltemp15'),
#         b'\x48': ('decode_moist', 1, 'soilmoist15'),
#         b'\x49': ('decode_temp', 2, 'soiltemp16'),
#         b'\x4A': ('decode_moist', 1, 'soilmoist16'),
#         b'\x4C': ('decode_batt', 16, 'lowbatt'),
#         b'\x4D': ('decode_pm25', 2, 'pm251_24h_avg'),
#         b'\x4E': ('decode_pm25', 2, 'pm252_24h_avg'),
#         b'\x4F': ('decode_pm25', 2, 'pm253_24h_avg'),
#         b'\x50': ('decode_pm25', 2, 'pm254_24h_avg'),
#         b'\x51': ('decode_pm25', 2, 'pm252'),
#         b'\x52': ('decode_pm25', 2, 'pm253'),
#         b'\x53': ('decode_pm25', 2, 'pm254'),
#         b'\x58': ('decode_leak', 1, 'leak1'),
#         b'\x59': ('decode_leak', 1, 'leak2'),
#         b'\x5A': ('decode_leak', 1, 'leak3'),
#         b'\x5B': ('decode_leak', 1, 'leak4'),
#         b'\x60': ('decode_distance', 1, 'lightningdist'),
#         b'\x61': ('decode_utc', 4, 'lightningdettime'),
#         b'\x62': ('decode_count', 4, 'lightningcount'),
#         b'\x63': ('decode_wn34', 3, 'temp9'),
#         b'\x64': ('decode_wn34', 3, 'temp10'),
#         b'\x65': ('decode_wn34', 3, 'temp11'),
#         b'\x66': ('decode_wn34', 3, 'temp12'),
#         b'\x67': ('decode_wn34', 3, 'temp13'),
#         b'\x68': ('decode_wn34', 3, 'temp14'),
#         b'\x69': ('decode_wn34', 3, 'temp15'),
#         b'\x6A': ('decode_wn34', 3, 'temp16'),
#         b'\x6C': ('decode_memory', 4, 'heap_free'),
#         b'\x70': ('decode_wh45', 16, ('temp17', 'humid17', 'pm10',
#                                       'pm10_24h_avg', 'pm255', 'pm255_24h_avg',
#                                       'co2', 'co2_24h_avg')),
#         # placeholder for unknown field 0x71
#         # b'\x71': (None, None, None),
#         b'\x72': ('decode_wet', 1, 'leafwet1'),
#         b'\x73': ('decode_wet', 1, 'leafwet2'),
#         b'\x74': ('decode_wet', 1, 'leafwet3'),
#         b'\x75': ('decode_wet', 1, 'leafwet4'),
#         b'\x76': ('decode_wet', 1, 'leafwet5'),
#         b'\x77': ('decode_wet', 1, 'leafwet6'),
#         b'\x78': ('decode_wet', 1, 'leafwet7'),
#         b'\x79': ('decode_wet', 1, 'leafwet8')
#     }
#     # decode structure for CMD_READ_RAIN
#     rain_data_struct = {
#         b'\x0D': ('decode_rain', 2, 't_rainevent'),
#         b'\x0E': ('decode_rainrate', 2, 't_rainrate'),
#         b'\x0F': ('decode_gain_100', 2, 't_raingain'),
#         b'\x10': ('decode_big_rain', 4, 't_rainday'),
#         b'\x11': ('decode_big_rain', 4, 't_rainweek'),
#         b'\x12': ('decode_big_rain', 4, 't_rainmonth'),
#         b'\x13': ('decode_big_rain', 4, 't_rainyear'),
#         b'\x7A': ('decode_int', 1, 'rain_priority'),
#         b'\x7B': ('decode_int', 1, 'temperature_comp'),
#         b'\x80': ('decode_rainrate', 2, 'p_rainrate'),
#         b'\x81': ('decode_rain', 2, 'p_rainevent'),
#         b'\x82': ('decode_reserved', 2, 'p_rainhour'),
#         b'\x83': ('decode_big_rain', 4, 'p_rainday'),
#         b'\x84': ('decode_big_rain', 4, 'p_rainweek'),
#         b'\x85': ('decode_big_rain', 4, 'p_rainmonth'),
#         b'\x86': ('decode_big_rain', 4, 'p_rainyear'),
#         b'\x87': ('decode_rain_gain', 20, None),
#         b'\x88': ('decode_rain_reset', 3, None)
#     }
#     rain_field_codes = (b'\x0D', b'\x0E', b'\x0F', b'\x10',
#                         b'\x11', b'\x12', b'\x13', b'\x14',
#                         b'\x80', b'\x81', b'\x83', b'\x84',
#                         b'\x85', b'\x86')
#     wind_field_codes = (b'\x0A', b'\x0B', b'\x0C', b'\x19')
#
#     response_data = 'FF FF 27 00 40 01 01 40 06 26 08 27 D2 09 27 D2 2A 00 5A ' \
#                     '4D 00 65 2C 27 2E 14 1A 00 ED 22 3A 1B 01 0B 23 3A 4C 06 ' \
#                     '00 00 00 05 FF FF 00 F6 FF FF FF FF FF FF FF 62 00 00 00 ' \
#                     '00 61 FF FF FF FF 60 FF EC'
#     parsed_response = {'intemp': 32.0,
#                        'inhumid': 38,
#                        'absbarometer': 1019.4,
#                        'relbarometer': 1019.4,
#                        'pm251': 9.0,
#                        'pm251_24h_avg': 10.1,
#                        'soilmoist1': 39,
#                        'soilmoist2': 20,
#                        'temp1': 23.7,
#                        'humid1': 58,
#                        'temp2': 26.7,
#                        'humid2': 58,
#                        'lightningcount': 0,
#                        'lightningdettime': None,
#                        'lightningdist': None}
#     temp_data = {'data': '00 EA', 'value': 23.4}
#     humid_data = {'data': '48', 'value': 72}
#     press_data = {'data': '27 4C', 'value': 1006.0,
#                   'long': '03 27 4C', 'long_value': 1006.0}
#     dir_data = {'data': '00 70', 'value': 112}
#     speed_data = {'data': '00 70', 'value': 11.2,
#                   'long': '03 00 70', 'long_value': 11.2}
#     rain_data = {'data': '01 70', 'value': 36.8,
#                  'long': '03 01 70', 'long_value': 36.8}
#     rainrate_data = {'data': '00 34', 'value': 5.2,
#                      'long': '03 00 34', 'long_value': 5.2}
#     big_rain_data = {'data': '01 70 37 21', 'value': 2413136.1}
#     light_data = {'data': '02 40 72 51', 'value': 3777800.1}
#     uv_data = {'data': '32 70', 'value': 1291.2,
#                'long': '03 32 70', 'long_value': 1291.2}
#     uvi_data = {'data': '0C', 'value': 12}
#     datetime_data = {'data': '0C AB 23 41 56 37', 'value': (12, 171, 35, 65, 86, 55)}
#     pm25_data = {'data': '00 39', 'value': 5.7,
#                  'long': '03 00 39', 'long_value': 5.7}
#     moist_data = {'data': '3A', 'value': 58}
#     leak_data = {'data': '3A', 'value': 58}
#     pm10_data = {'data': '1C 9D', 'value': 732.5,
#                  'long': '05 1C 9D', 'long_value': 732.5}
#     co2_data = {'data': '24 73', 'value': 9331}
#     wet_data = {'data': '53', 'value': 83}
#     rain_reset_data = {'data': '09 01 06',
#                        'value': {'day_reset': 9,
#                                  'week_reset': 1,
#                                  'annual_reset': 6}
#                        }
#     rain_gain_data = {'data': '00 0A 01 F4 00 64 00 E6 01 CC 01 EA 01 4A 00 '
#                               'DE 00 6E 00 14',
#                       'value': {'gain0': 0.1,
#                                 'gain1': 5.0,
#                                 'gain2': 1.0,
#                                 'gain3': 2.3,
#                                 'gain4': 4.6,
#                                 'gain5': 4.9,
#                                 'gain6': 3.3,
#                                 'gain7': 2.22,
#                                 'gain8': 1.1,
#                                 'gain9': 0.2
#                                 }
#                       }
#     distance_data = {'data': '1A', 'value': 26}
#     utc_data = {'data': '5F 40 72 51', 'value': 1598059089}
#     count_data = {'data': '00 40 72 51', 'value': 4223569}
#     gain_100_data = {'data': '01 F2', 'value': 4.98}
#     wn34_data = {'data': '00 EA 4D',
#                  'field': 't',
#                  'value': {'t': 23.4}
#                  }
#     wh45_data = {'data': '00 EA 4D 35 6D 28 78 34 3D 62 7E 8D 2A 39 9F 04',
#                  'field': ('t', 'h', 'p10', 'p10_24', 'p25', 'p25_24', 'c', 'c_24'),
#                  'value': {'t': 23.4, 'h': 77, 'p10': 1367.7, 'p10_24': 1036.0,
#                            'p25': 1337.3, 'p25_24': 2521.4, 'c': 36138, 'c_24': 14751}
#                  }
#     # CMD_READ_RAIN test response and decoded data - piezo gauge only
#     read_rain_piezo = {'response': 'FF FF 57 00 37 80 00 06 83 00 00 00 4B 84 00 00 '
#                                    '00 52 85 00 00 00 BB 86 00 00 00 BB 81 00 4B 87 '
#                                    '00 0A 01 F4 00 64 00 E6 01 CC 01 EA 01 4A 00 DE '
#                                    '00 6E 00 14 88 09 01 06 FC',
#                        'data': {'p_rainrate': 0.6,
#                                 'p_rainevent': 7.5,
#                                 'p_rainday': 7.5,
#                                 'p_rainweek': 8.2,
#                                 'p_rainmonth': 18.7,
#                                 'p_rainyear': 18.7,
#                                 'gain0': 0.1,
#                                 'gain1': 5.0,
#                                 'gain2': 1.0,
#                                 'gain3': 2.3,
#                                 'gain4': 4.6,
#                                 'gain5': 4.9,
#                                 'gain6': 3.3,
#                                 'gain7': 2.22,
#                                 'gain8': 1.1,
#                                 'gain9': 0.2,
#                                 'day_reset': 9,
#                                 'week_reset': 1,
#                                 'annual_reset': 6}
#                        }
#     # CMD_READ_RAIN test response and decoded data - traditional and piezo
#     # gauges
#     read_rain_both = {'response': 'FF FF 57 00 54 0E 00 00 10 00 00 00 00 11 '
#                                   '00 00 00 00 12 00 00 00 00 13 00 00 0C 11 '
#                                   '0D 00 00 0F 00 64 80 00 00 83 00 00 00 00 '
#                                   '84 00 00 00 00 85 00 00 00 00 86 00 00 0C '
#                                   '72 81 00 00 87 00 64 00 64 00 64 00 64 00 '
#                                   '64 00 64 00 64 00 64 00 64 00 64 88 00 00 '
#                                   '00 24',
#                       'data': {'t_rainrate': 0.0,
#                                't_rainevent': 0.0,
#                                't_raingain': 1.0,
#                                't_rainday': 0.0,
#                                't_rainweek': 0.0,
#                                't_rainmonth': 0.0,
#                                't_rainyear': 308.9,
#                                'p_rainrate': 0.0,
#                                'p_rainevent': 0.0,
#                                'p_rainday': 0.0,
#                                'p_rainweek': 0.0,
#                                'p_rainmonth': 0.0,
#                                'p_rainyear': 318.6,
#                                'gain0': 1.0,
#                                'gain1': 1.0,
#                                'gain2': 1.0,
#                                'gain3': 1.0,
#                                'gain4': 1.0,
#                                'gain5': 1.0,
#                                'gain6': 1.0,
#                                'gain7': 1.0,
#                                'gain8': 1.0,
#                                'gain9': 1.0,
#                                'day_reset': 0,
#                                'week_reset': 0,
#                                'annual_reset': 0}
#                       }
#     # CMD_READ_RAINDATA test response and decoded data
#     # TODO. Perhaps have a non-zero value for rainrate
#     read_raindata = {'response': 'FF FF 34 17 00 00 00 00 00 00 00 34 '
#                                  '00 00 00 34 00 00 01 7B 00 00 09 25 5D',
#                      'data': {'t_rainrate': 0.0,
#                               't_rainday': 5.2,
#                               't_rainweek': 5.2,
#                               't_rainmonth': 37.9,
#                               't_rainyear': 234.1}
#                      }
#     get_mulch_offset = {'response': 'FF FF 2C 1B 00 02 15 01 FB E5 02 0A '
#                                     '64 03 00 1A 04 06 00 05 F6 9C 06 05 '
#                                     '14 07 FB C4 52',
#                         'data': {0: {'temp': 2.1, 'hum': 2},
#                                  1: {'temp': -2.7, 'hum': -5},
#                                  2: {'temp': 10.0, 'hum': 10},
#                                  3: {'temp': 2.6, 'hum': 0},
#                                  4: {'temp': 0.0, 'hum': 6},
#                                  5: {'temp': -10.0, 'hum': -10},
#                                  6: {'temp': 2.0, 'hum': 5},
#                                  7: {'temp': -6.0, 'hum': -5}
#                                  }
#                         }
#     get_pm25_offset = {'response': 'FF FF 2E 0F 00 00 C8 01 FF 38 02 '
#                                    '00 00 03 FF C7 08',
#                        'data': {0: 20, 1: -20, 2: 0, 3: -5.7}
#                        }
#     get_co2_offset = {'response': 'FF FF 53 09 1D C7 00 7B FF CB 5C',
#                       'data': {'co2': 7623,
#                                'pm25': 12.3,
#                                'pm10': -5.3}
#                       }
#     read_gain = {'response': 'FF FF 36 0F 04 F3 00 35 00 0A 01 F4 01 '
#                              'AE 00 64 38',
#                  'data': {'uv': 0.53,
#                           'solar': 0.1,
#                           'wind': 5.0,
#                           'rain': 4.3}
#                  }
#     read_calibration = {'response': 'FF FF 38 13 FF C6 04 FF FF FF E5 '
#                                     '00 00 00 31 00 60 09 00 B4 44',
#                         'data': {'intemp': -5.8,
#                                  'inhum': 4,
#                                  'abs': -2.7,
#                                  'rel': 4.9,
#                                  'outtemp': 9.6,
#                                  'outhum': 9,
#                                  'dir': 180}
#                         }
#     get_soilhumiad = {'response': 'FF FF 28 13 00 29 00 EB 01 C8 03 '
#                                   'E8 01 35 01 17 01 23 00 C8 3D',
#                       'data': {0: {'humidity': 41, 'ad': 235, 'ad_select': 1, 'adj_min': 200, 'adj_max': 1000},
#                                1: {'humidity': 53, 'ad': 279, 'ad_select': 1, 'adj_min': 35, 'adj_max': 200}
#                                }
#                       }
#     read_ssss = {'response': 'FF FF 30 0B 00 01 62 66 8E 53 5E 03 46',
#                  'data': {'frequency': 0,
#                           'sensor_type': 1,
#                           'utc': 1650888275,
#                           'timezone_index': 94,
#                           'dst_status': True}
#                  }
#     read_ecowitt = {'response': 'FF FF 1E 04 03 23',
#                     'data': {'interval': 3}
#                     }
#     read_wunderground = {'response': 'FF FF 20 16 08 61 62 63 64 65 66 67 '
#                                      '68 08 31 32 33 34 35 36 37 38 01 0F',
#                          'data': {'id': 'abcdefgh',
#                                   'password': '12345678'}
#                          }
#     read_wow = {'response': 'FF FF 22 1E 07 77 6F 77 31 32 33 34 08 71 61 7A '
#                             '78 73 77 65 64 08 00 00 00 00 00 00 00 00 01 F6',
#                 'data': {'id': 'wow1234',
#                          'password': 'qazxswed',
#                          'station_num': '\x00\x00\x00\x00\x00\x00\x00\x00'}
#                 }
#     read_weathercloud = {'response': 'FF FF 24 16 08 71 77 65 72 74 79 75 69 '
#                                      '08 61 62 63 64 65 66 67 68 01 F9',
#                          'data': {'id': 'qwertyui',
#                                   'key': 'abcdefgh'}
#                          }
#     read_customized = {'response': 'FF FF 2A 27 06 31 32 33 34 35 36 08 61 62 '
#                                    '63 64 65 66 67 68 0D 31 39 32 2E 31 36 38 '
#                                    '2E 32 2E 32 32 30 1F 40 00 14 00 01 C4',
#                        'data': {'id': '123456',
#                                 'password': 'abcdefgh',
#                                 'server': '192.168.2.220',
#                                 'port': 8000,
#                                 'interval': 20,
#                                 'type': 0,
#                                 'active': 1}
#                        }
#     read_usr_path = {'response': 'FF FF 51 12 05 2F 70 61 74 68 08 2F 6D 79 2F '
#                                  '70 61 74 68 3D',
#                      'data': {'ecowitt_path': '/path',
#                               'wu_path': '/my/path'}
#                      }
#     read_station_mac = {'response': 'FF FF 26 09 E8 68 E7 12 9D D7 EC',
#                         'data': 'E8:68:E7:12:9D:D7'
#                         }
#     read_firmware_version = {'response': 'FF FF 50 12 0E 47 57 32 30 '
#                                          '30 30 43 5F 56 32 2E 31 2E 34 BB',
#                              'data': 'GW2000C_V2.1.4'
#                              }
#
#     def setUp(self):
#
#         # get a Parser object
#         self.parser = user.gw1000.ApiParser()
#         self.maxDiff = None
#
#     def tearDown(self):
#
#         pass
#
#     def test_constants(self):
#         """Test constants"""
#
#         # test live_data_struct
#         self.assertEqual(self.parser.live_data_struct, self.live_data_struct)
#
#         # test rain_data_struct
#         self.assertEqual(self.parser.rain_data_struct, self.rain_data_struct)
#
#         # test rain_field_codes
#         self.assertEqual(self.parser.rain_field_codes, self.rain_field_codes)
#
#         # wind_field_codes
#         self.assertEqual(self.parser.wind_field_codes, self.wind_field_codes)
#
#     def test_parse(self):
#         """Test methods used to parse API response data."""
#
#         # test parse_livedata()
#         self.assertDictEqual(self.parser.parse_livedata(response=hex_to_bytes(self.response_data)),
#                              self.parsed_response)
#
#         # test parse_read_rain() with piezo gauge only
#         self.assertDictEqual(self.parser.parse_read_rain(response=hex_to_bytes(self.read_rain_piezo['response'])),
#                              self.read_rain_piezo['data'])
#
#         # test parse_read_rain() with both traditional and piezo gauges
#         self.assertDictEqual(self.parser.parse_read_rain(response=hex_to_bytes(self.read_rain_both['response'])),
#                              self.read_rain_both['data'])
#
#         # test parse_read_raindata()
#         self.assertDictEqual(self.parser.parse_read_raindata(response=hex_to_bytes(self.read_raindata['response'])),
#                              self.read_raindata['data'])
#
#         # test parse_get_mulch_offset()
#         self.assertDictEqual(self.parser.parse_get_mulch_offset(response=hex_to_bytes(self.get_mulch_offset['response'])),
#                              self.get_mulch_offset['data'])
#
#         # test parse_get_pm25_offset()
#         self.assertDictEqual(self.parser.parse_get_pm25_offset(response=hex_to_bytes(self.get_pm25_offset['response'])),
#                              self.get_pm25_offset['data'])
#
#         # test parse_get_co2_offset()
#         self.assertDictEqual(self.parser.parse_get_co2_offset(response=hex_to_bytes(self.get_co2_offset['response'])),
#                              self.get_co2_offset['data'])
#
#         # test parse_read_gain()
#         self.assertDictEqual(self.parser.parse_read_gain(response=hex_to_bytes(self.read_gain['response'])),
#                              self.read_gain['data'])
#
#         # test parse_read_calibration()
#         self.assertDictEqual(self.parser.parse_read_calibration(response=hex_to_bytes(self.read_calibration['response'])),
#                              self.read_calibration['data'])
#
#         # test parse_get_soilhumiad()
#         self.assertDictEqual(self.parser.parse_get_soilhumiad(response=hex_to_bytes(self.get_soilhumiad['response'])),
#                              self.get_soilhumiad['data'])
#
#         # test read_ssss()
#         self.assertDictEqual(self.parser.parse_read_ssss(response=hex_to_bytes(self.read_ssss['response'])),
#                              self.read_ssss['data'])
#
#         # test parse_read_ecowitt()
#         self.assertDictEqual(self.parser.parse_read_ecowitt(response=hex_to_bytes(self.read_ecowitt['response'])),
#                              self.read_ecowitt['data'])
#
#         # test parse_read_wunderground()
#         self.assertDictEqual(self.parser.parse_read_wunderground(response=hex_to_bytes(self.read_wunderground['response'])),
#                              self.read_wunderground['data'])
#
#         # test parse_read_wow()
#         self.assertDictEqual(self.parser.parse_read_wow(response=hex_to_bytes(self.read_wow['response'])),
#                              self.read_wow['data'])
#
#         # test parse_read_weathercloud()
#         self.assertDictEqual(self.parser.parse_read_weathercloud(response=hex_to_bytes(self.read_weathercloud['response'])),
#                              self.read_weathercloud['data'])
#
#         # test parse_read_customized()
#         self.assertDictEqual(self.parser.parse_read_customized(response=hex_to_bytes(self.read_customized['response'])),
#                              self.read_customized['data'])
#
#         # test parse_read_usr_path()
#         self.assertDictEqual(self.parser.parse_read_usr_path(response=hex_to_bytes(self.read_usr_path['response'])),
#                              self.read_usr_path['data'])
#
#         # test parse_read_station_mac()
#         self.assertEqual(self.parser.parse_read_station_mac(response=hex_to_bytes(self.read_station_mac['response'])),
#                          self.read_station_mac['data'])
#
#         # test parse_read_firmware_version()
#         self.assertEqual(self.parser.parse_read_firmware_version(response=hex_to_bytes(self.read_firmware_version['response'])),
#                          self.read_firmware_version['data'])
#
#     def test_decode(self):
#         """Test methods used to decode observation byte data"""
#
#         # test temperature decode (method decode_temp())
#         self.assertEqual(self.parser.decode_temp(hex_to_bytes(self.temp_data['data'])),
#                          self.temp_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_temp(hex_to_bytes(self.temp_data['data']), field='test'),
#                              {'test': self.temp_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_temp(hex_to_bytes(xbytes(3))), None)
#
#         # test humidity decode (method decode_humid())
#         self.assertEqual(self.parser.decode_humid(hex_to_bytes(self.humid_data['data'])),
#                          self.humid_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_humid(hex_to_bytes(self.humid_data['data']), field='test'),
#                              {'test': self.humid_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_humid(hex_to_bytes(xbytes(2))), None)
#
#         # test pressure decode (method decode_press())
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.press_data['data'])),
#                          self.press_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_press(hex_to_bytes(self.press_data['data']), field='test'),
#                              {'test': self.press_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.press_data['long'])),
#                          self.press_data['long_value'])
#
#         # test direction decode (method decode_dir())
#         self.assertEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['data'])),
#                          self.dir_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['data']), field='test'),
#                              {'test': self.dir_data['value']})
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_dir(hex_to_bytes(self.dir_data['data']), field='test'),
#                              {'test': self.dir_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_dir(hex_to_bytes(xbytes(3))), None)
#
#         # test big rain decode (method decode_big_rain())
#         self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(self.big_rain_data['data'])),
#                          self.big_rain_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_big_rain(hex_to_bytes(self.big_rain_data['data']), field='test'),
#                              {'test': self.big_rain_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_big_rain(hex_to_bytes(xbytes(5))), None)
#
#         # test datetime decode (method decode_datetime())
#         self.assertEqual(self.parser.decode_datetime(hex_to_bytes(self.datetime_data['data'])),
#                          self.datetime_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_datetime(hex_to_bytes(self.datetime_data['data']), field='test'),
#                              {'test': self.datetime_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_datetime(hex_to_bytes(xbytes(7))), None)
#
#         # test distance decode (method decode_distance())
#         self.assertEqual(self.parser.decode_distance(hex_to_bytes(self.distance_data['data'])),
#                          self.distance_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_distance(hex_to_bytes(self.distance_data['data']), field='test'),
#                              {'test': self.distance_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_distance(hex_to_bytes(xbytes(2))), None)
#
#         # test utc decode (method decode_utc())
#         self.assertEqual(self.parser.decode_utc(hex_to_bytes(self.utc_data['data'])),
#                          self.utc_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_utc(hex_to_bytes(self.utc_data['data']), field='test'),
#                              {'test': self.utc_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_utc(hex_to_bytes(xbytes(5))), None)
#
#         # test count decode (method decode_count())
#         self.assertEqual(self.parser.decode_count(hex_to_bytes(self.count_data['data'])),
#                          self.count_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_count(hex_to_bytes(self.count_data['data']), field='test'),
#                              {'test': self.count_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_count(hex_to_bytes(xbytes(5))), None)
#
#         # test sensor gain decode (method decode_gain_100())
#         self.assertEqual(self.parser.decode_gain_100(hex_to_bytes(self.gain_100_data['data'])),
#                          self.gain_100_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_gain_100(hex_to_bytes(self.gain_100_data['data']), field='test'),
#                              {'test': self.gain_100_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_gain_100(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_gain_100(hex_to_bytes(xbytes(5))), None)
#
#         # test speed decode (method decode_speed())
#         self.assertEqual(self.parser.decode_speed(hex_to_bytes(self.speed_data['data'])),
#                          self.speed_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_speed(hex_to_bytes(self.speed_data['data']), field='test'),
#                              {'test': self.speed_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_speed(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.speed_data['long'])),
#                          self.speed_data['long_value'])
#
#         # test rain decode (method decode_rain())
#         self.assertEqual(self.parser.decode_rain(hex_to_bytes(self.rain_data['data'])),
#                          self.rain_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_rain(hex_to_bytes(self.rain_data['data']), field='test'),
#                              {'test': self.rain_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_rain(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.rain_data['long'])),
#                          self.rain_data['long_value'])
#
#         # test rain rate decode (method decode_rainrate())
#         self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(self.rainrate_data['data'])),
#                          self.rainrate_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_rainrate(hex_to_bytes(self.rainrate_data['data']), field='test'),
#                              {'test': self.rainrate_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_rainrate(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.rainrate_data['long'])),
#                          self.rainrate_data['long_value'])
#
#         # test light decode (method decode_light())
#         self.assertEqual(self.parser.decode_light(hex_to_bytes(self.light_data['data'])),
#                          self.light_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_light(hex_to_bytes(self.light_data['data']), field='test'),
#                              {'test': self.light_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_light(hex_to_bytes(xbytes(5))), None)
#
#         # test uv decode (method decode_uv())
#         self.assertEqual(self.parser.decode_uv(hex_to_bytes(self.uv_data['data'])),
#                          self.uv_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_uv(hex_to_bytes(self.uv_data['data']), field='test'),
#                              {'test': self.uv_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_uv(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.uv_data['long'])),
#                          self.uv_data['long_value'])
#
#         # test uvi decode (method decode_uvi())
#         self.assertEqual(self.parser.decode_uvi(hex_to_bytes(self.uvi_data['data'])),
#                          self.uvi_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_uvi(hex_to_bytes(self.uvi_data['data']), field='test'),
#                              {'test': self.uvi_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_uvi(hex_to_bytes(xbytes(2))), None)
#
#         # test moisture decode (method decode_moist())
#         self.assertEqual(self.parser.decode_moist(hex_to_bytes(self.moist_data['data'])),
#                          self.moist_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_moist(hex_to_bytes(self.moist_data['data']), field='test'),
#                              {'test': self.moist_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_moist(hex_to_bytes(xbytes(2))), None)
#
#         # test pm25 decode (method decode_pm25())
#         self.assertEqual(self.parser.decode_pm25(hex_to_bytes(self.pm25_data['data'])),
#                          self.pm25_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_pm25(hex_to_bytes(self.pm25_data['data']), field='test'),
#                              {'test': self.pm25_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_pm25(hex_to_bytes(xbytes(1))), None)
#         self.assertEqual(self.parser.decode_press(hex_to_bytes(self.pm25_data['long'])),
#                          self.pm25_data['long_value'])
#
#         # test leak decode (method decode_leak())
#         self.assertEqual(self.parser.decode_leak(hex_to_bytes(self.leak_data['data'])),
#                          self.leak_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_leak(hex_to_bytes(self.leak_data['data']), field='test'),
#                              {'test': self.leak_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_leak(hex_to_bytes(xbytes(2))), None)
#
#         # test pm10 decode (method decode_pm10())
#         self.assertEqual(self.parser.decode_pm10(hex_to_bytes(self.pm10_data['data'])),
#                          self.pm10_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_pm10(hex_to_bytes(self.pm10_data['data']), field='test'),
#                              {'test': self.pm10_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_pm10(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_pm10(hex_to_bytes(self.pm10_data['long'])),
#                          self.pm10_data['long_value'])
#
#         # test co2 decode (method decode_co2())
#         self.assertEqual(self.parser.decode_co2(hex_to_bytes(self.co2_data['data'])),
#                          self.co2_data['value'])
#         # test decode with field != None
#         self.assertDictEqual(self.parser.decode_co2(hex_to_bytes(self.co2_data['data']), field='test'),
#                              {'test': self.co2_data['value']})
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_co2(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_co2(hex_to_bytes(xbytes(3))), None)
#
#         # test wetness decode (method decode_wet())
#         self.assertEqual(self.parser.decode_wet(hex_to_bytes(self.wet_data['data'])),
#                          self.wet_data['value'])
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_wet(hex_to_bytes(xbytes(0))), None)
#         self.assertEqual(self.parser.decode_wet(hex_to_bytes(xbytes(2))), None)
#
#         # test wn34 decode (method decode_wn34())
#         self.assertEqual(self.parser.decode_wn34(hex_to_bytes(self.wn34_data['data']), field=self.wn34_data['field']),
#                          self.wn34_data['value'])
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_wn34(hex_to_bytes(xbytes(1)), field=self.wn34_data['field']), {})
#         self.assertEqual(self.parser.decode_wn34(hex_to_bytes(xbytes(4)), field=self.wn34_data['field']), {})
#
#         # test wh45 decode (method decode_wh45())
#         self.assertEqual(self.parser.decode_wh45(hex_to_bytes(self.wh45_data['data']), fields=self.wh45_data['field']),
#                          self.wh45_data['value'])
#         # test correct handling of too few and too many bytes
#         self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(1)), fields=self.wh45_data['field']),
#                          {})
#         self.assertEqual(self.parser.decode_wh45(hex_to_bytes(xbytes(17)), fields=self.wh45_data['field']),
#                          {})
#
#         # test rain gain decode (method decode_rain_gain())
#         self.assertDictEqual(self.parser.decode_rain_gain(hex_to_bytes(self.rain_gain_data['data'])),
#                              self.rain_gain_data['value'])
#         # test correct handling of too few and too many bytes
#         self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(xbytes(0))), {})
#         self.assertDictEqual(self.parser.decode_rain_gain(hex_to_bytes(xbytes(2))), {})
#
#         # test rain reset decode (method decode_rain_reset())
#         self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(self.rain_reset_data['data'])),
#                              self.rain_reset_data['value'])
#         # test correct handling of too few and too many bytes
#         self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(xbytes(0))), {})
#         self.assertDictEqual(self.parser.decode_rain_reset(hex_to_bytes(xbytes(2))), {})
#
#         # test battery status decode (method decode_batt())
#         # decode_batt() is obfuscated and should always return None
#         # irrespective of how it is called
#         self.assertIsNone(self.parser.decode_batt(''))
#
#
# class UtilitiesTestCase(unittest.TestCase):
#     """Unit tests for utility functions."""
#
#     unsorted_dict = {'leak2': 'leak2',
#                      'inHumidity': 'inhumid',
#                      'wh31_ch3_batt': 'wh31_ch3_batt',
#                      'leak1': 'leak1',
#                      'wh31_ch2_batt': 'wh31_ch2_batt',
#                      'windDir': 'winddir',
#                      'inTemp': 'intemp'}
#     sorted_dict_str = "{'inHumidity': 'inhumid', 'inTemp': 'intemp', " \
#                       "'leak1': 'leak1', 'leak2': 'leak2', " \
#                       "'wh31_ch2_batt': 'wh31_ch2_batt', " \
#                       "'wh31_ch3_batt': 'wh31_ch3_batt', " \
#                       "'windDir': 'winddir'}"
#     sorted_keys = ['inHumidity', 'inTemp', 'leak1', 'leak2',
#                    'wh31_ch2_batt', 'wh31_ch3_batt', 'windDir']
#     bytes_to_hex_fail_str = "cannot represent '%s' as hexadecimal bytes"
#
#     def test_utilities(self):
#         """Test utility functions
#
#         Tests:
#         1. natural_sort_keys()
#         2. natural_sort_dict()
#         3. bytes_to_hex()
#         """
#
#         # test natural_sort_keys()
#         self.assertEqual(user.gw1000.natural_sort_keys(self.unsorted_dict),
#                          self.sorted_keys)
#
#         # test natural_sort_dict()
#         self.assertEqual(user.gw1000.natural_sort_dict(self.unsorted_dict),
#                          self.sorted_dict_str)
#
#         # test bytes_to_hex()
#         # with defaults
#         self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2')),
#                          'FF 00 66 B2')
#         # with defaults and a separator
#         self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=':'),
#                          'FF:00:66:B2')
#         # with defaults using lower case
#         self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), caps=False),
#                          'ff 00 66 b2')
#         # with a separator and lower case
#         self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=':', caps=False),
#                          'ff:00:66:b2')
#         # and check exceptions raised
#         # TypeError
#         self.assertEqual(user.gw1000.bytes_to_hex(22), self.bytes_to_hex_fail_str % 22)
#         # AttributeError
#         self.assertEqual(user.gw1000.bytes_to_hex(hex_to_bytes('ff 00 66 b2'), separator=None),
#                          self.bytes_to_hex_fail_str % hex_to_bytes('ff 00 66 b2'))
#
#         # test obfuscate()
#         # > 8 character string, should see trailing 4 characters
#         self.assertEqual(user.gw1000.obfuscate('1234567890'), '******7890')
#         # 7 character string, should see trailing 3 characters
#         self.assertEqual(user.gw1000.obfuscate('1234567'), '****567')
#         # 5 character string, should see trailing 2 characters
#         self.assertEqual(user.gw1000.obfuscate('12345'), '***45')
#         # 3 character string, should see last character
#         self.assertEqual(user.gw1000.obfuscate('123'), '**3')
#         # 2 character string, should see no characters
#         self.assertEqual(user.gw1000.obfuscate('12'), '**')
#         # check obfuscation character
#         self.assertEqual(user.gw1000.obfuscate('1234567890', obf_char='#'),
#                          '######7890')


class ListsAndDictsTestCase(unittest.TestCase):
    """Test case to test list and dict consistency."""

    def setUp(self):

        pass

    def test_dicts(self):
        """Test dicts for consistency"""

        # set longMessage to False, our custom error messages in this test
        # method are standalone
        self.longMessage = False
        # test addressed_data_struct dict entries
        for address, field_dict in ecowitt.TelnetApiParser.addressed_data_struct.items():
            # test that each field in the addressed_data_struct dict has an
            # entry in the field_to_text dict
            self.assertIn(field_dict[0],
                          ecowitt.EcowittDeviceConfigurator.field_to_text.keys(),
                          msg=f"Addressed data field '{field_dict[0]}'is missing "
                              f"from the field-to-text map")
            # test that each field decode function in addressed_data_struct
            # dict exists in class GatewayApiParser
            self.assertTrue(hasattr(ecowitt.TelnetApiParser, field_dict[1]),
                            msg=f"Decode function '{field_dict[1]}' does not exist "
                                f"in class GatewayApiParser")
            # test that each value in the addressed_data_struct dict is of length 3
            self.assertTrue(len(field_dict) == 3,
                            msg=f"Addressed data field {address} has an incorrect "
                                f"number of parameters")

        # test wh45_sub_fields dict entries
        for field, field_dict in ecowitt.TelnetApiParser.wh45_sub_fields.items():
            # test that each field decode function in wh45_sub_fields
            # dict exists in class GatewayApiParser
            self.assertTrue(hasattr(ecowitt.TelnetApiParser, field_dict[0]),
                            msg=f"Decode function '{field_dict[0]}' does not exist "
                                f"in class GatewayApiParser")
            # test that each value in the wh45_sub_fields dict is of length 2
            self.assertTrue(len(field_dict) == 2,
                            msg=f"Addressed data field {address} has an incorrect "
                                f"number of parameters")

        # test Sensors.sensor_ids dict entries
        for field, field_dict in ecowitt.Sensors.sensor_ids.items():
            # test that each field dict has a name, a long_name and batt_fn fields
            self.assertIn('name',
                          field_dict.keys(),
                          msg=f"Sensors.sensor_ids '{ord(field):#04x}' entry is missing "
                              f"a 'name' entry")
            self.assertIn('long_name',
                          field_dict.keys(),
                          msg=f"Sensors.sensor_ids '{ord(field):#04x}' entry is missing "
                              f"a 'long_name' entry")
            self.assertIn('batt_fn',
                          field_dict.keys(),
                          msg=f"Sensors.sensor_ids '{ord(field):#04x}' entry is missing "
                              f"a 'batt_fn' entry")
            # test that each field_dict battery decode function in sensors_id
            # dict exists in class Sensors
            self.assertTrue(hasattr(ecowitt.Sensors, field_dict['batt_fn']),
                            msg=f"Battery decode function '{field_dict['batt_fn']}' "
                                f"does not exist in class Sensors")
            # test that each value in the addressed_data_struct dict is of length 3
            self.assertTrue(len(field_dict) == 3,
                            msg=f"Sensors.sensor_ids '{ord(field):#04x}' entry has an incorrect "
                                f"number of parameters")

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
        return separator.join(format_str.format(c) for c in iterable)
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
    test_cases = (ListsAndDictsTestCase,)

    usage = """PYTHONPATH=/path/to/ecowitt.py python3 /path/to/test_ecowitt.py 
           --help
           --version
           [--ip-address IP_ADDRESS] [--port PORT] [-v|--verbose VERBOSITY]

        Arguments:

           IP_ADDRESS: IP address to use to contact the gateway device. If omitted 
                       discovery is used.
           PORT: Port to use to contact the gateway device. If omitted discovery is 
                 used.
           VERBOSITY: How much status to display, 0-2. Default is 2."""
    description = 'Test the Ecowitt utility code.'
    epilog = """You must ensure the directory containing ecowitt.py is are in 
    your PYTHONPATH. For example:

    PYTHONPATH=/home/username python3 /home/username/tests/test_ecowitt.py --help
    """

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', dest='version', action='store_true',
                        help='display test suite version number')
    parser.add_argument('--ip-address', dest='ip_address', metavar="IP_ADDRESS",
                        help='Device IP address to use')
    parser.add_argument('--port', dest='port', type=int, metavar="PORT",
                        help='Device port to use')
#    parser.add_argument('--no-device', dest='no_device', action='store_true',
#                        help='skip tests that require a physical device')
    parser.add_argument('--verbose', dest='verbosity', type=int, metavar="VERBOSITY",
                        default=2,
                        help='How much status to display, 0-2')
    # parse the arguments
    args = parser.parse_args()

    # display version number
    if args.version:
        print("%s test suite version: %s" % (TEST_SUITE_NAME, TEST_SUITE_VERSION))
        exit(0)
    # run the tests
#     # first set the IP address and port to use in StationTestCase and
#     # GatewayServiceTestCase
#     StationTestCase.ip_address = args.ip_address
#     StationTestCase.port = args.port
# #    StationTestCase.no_device = args.no_device
#     GatewayDriverTestCase.ip_address = args.ip_address
#     GatewayDriverTestCase.port = args.port
#     GatewayServiceTestCase.ip_address = args.ip_address
#     GatewayServiceTestCase.port = args.port
    # get a test runner with appropriate verbosity
    runner = unittest.TextTestRunner(verbosity=args.verbosity)
    # create a test suite and run the included tests
    runner.run(suite(test_cases))


if __name__ == '__main__':
    main()