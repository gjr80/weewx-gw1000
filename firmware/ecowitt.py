#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ecowitt.py

A utility for reading, displaying and updating devices using the Ecowitt
LAN/Wi-Fi Gateway API.

As of the time of release this utility supports the GW1000, GW1100, GW1200 and
GW2000 gateway devices as well as the WH2650, WH2680 and WN1900 Wi-Fi weather
stations.

Copyright (C) 2024 Gary Roderick                        gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see https://www.gnu.org/licenses/.

Version: 0.1.0a1                                   Date: X Xxxxxxxxx 2024

Revision History
        - initial release


"""

# Outstanding TODOs:
# TODO. Confirm WH26/WH32 sensor ID
# TODO. Confirm WH26/WH32 battery status
# TODO. Confirm WH68 battery status
# TODO. Confirm WS80 battery status
# TODO. Confirm WH24 battery status
# TODO. Confirm WH25 battery status
# TODO. Need to know date-time data format for decode date_time()
# TODO. Need to re-order sensor output for --display_sensors to better match app
# Refactor TODOS:
# TODO. self.sensor_ids vs Sensors.sensor_ids
# TODO. Where should IP address, port and MAC be properties

# Python imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import calendar
import json
import re
import socket
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from operator import itemgetter

NAME = 'Ecowitt Utility'
VERSION = '0.1.0a1'

# various defaults used throughout
# default port used by device
DEFAULT_PORT = 45000
# default network broadcast address - the address that network broadcasts are
# sent to
DEFAULT_BROADCAST_ADDRESS = '255.255.255.255'
# default network broadcast port - the port that network broadcasts are sent to
DEFAULT_BROADCAST_PORT = 46000
# default socket timeout
DEFAULT_SOCKET_TIMEOUT = 2
# default broadcast timeout
DEFAULT_BROADCAST_TIMEOUT = 5
# default retry/wait time
DEFAULT_RETRY_WAIT = 10
# default max tries when polling the API
DEFAULT_MAX_TRIES = 3
# When run as a service the default age in seconds after which API data is
# considered stale and will not be used to augment loop packets
DEFAULT_MAX_AGE = 60
# default device poll interval
DEFAULT_POLL_INTERVAL = 20
# default period between lost contact log entries during an extended period of
# lost contact when run as a Service
DEFAULT_LOST_CONTACT_LOG_PERIOD = 21600
# default battery state filtering
DEFAULT_SHOW_BATTERY = False
# default firmware update check interval
DEFAULT_FW_CHECK_INTERVAL = 86400


class Bcolors:
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


# ============================================================================
#                         Gateway API error classes
# ============================================================================

class InvertibleSetError(Exception):
    """Must set a unique value in a InvertibleMap."""

    def __init__(self, value):
        self.value = value
        msg = 'The value "{}" is already in the mapping.'
        super(InvertibleSetError, self).__init__(msg.format(value))


class InvertibleMap(dict):
    """Class implementing a basic invertible map."""

    def __init__(self, *args, inverse=None, **kwargs):
        super(InvertibleMap, self).__init__(*args, **kwargs)
        if inverse is None:
            _inv = dict()
            for key, value in self.items():
                _inv[value] = key
            inverse = self.__class__(_inv, inverse=self, **kwargs)
        self.inverse = inverse

    def __setitem__(self, key, value):
        if value in self.inverse:
            raise InvertibleSetError(value)

        self.inverse._set_item(value, key)
        self._set_item(key, value)

    def __delitem__(self, key):
        self.inverse._del_item(self[key])
        self._del_item(key)

    def _del_item(self, key):
        super(InvertibleMap, self).__delitem__(key)

    def _set_item(self, key, value):
        super(InvertibleMap, self).__setitem__(key, value)

    def pop(self, key):
        self.inverse._del_item(self[key])
        return super(InvertibleMap, self).pop(key)


# ============================================================================
#                         Gateway API error classes
# ============================================================================

class UnknownApiCommand(Exception):
    """Exception raised when an unknown API command was selected or an
    otherwise valid API response has an unexpected command code."""


class UnknownHttpCommand(Exception):
    """Exception raised when an unknown HTTP command was selected."""


class InvalidChecksum(Exception):
    """Exception raised when an API call response contains an invalid
    checksum."""


class GWIOError(Exception):
    """Exception raised when an input/output error with the device is
    encountered."""


class InvalidSetting(Exception):
    """Exception raised when an invalid setting or setting value is encountered."""


class DeviceWriteFailed(Exception):
    """Exception raised when a gateway device write failed."""


class GatewayApiParser:
    """Class to parse, decode and encode data to/from the gateway device API.

    The GatewayApiParser class is used to parse, decode and encode payload data
    received and sent via the Ecowitt LAN/Wi-Fi Gateway API (the 'gateway
    API'). The GatewayApiParser class understands the structure of the data
    payload in each gateway API command, but does not know how to communicate
    with the device in any way.
    """

    # Dictionary of common address based data received using various gateway
    # API commands. The dictionary is keyed by the device data field 'address'
    # and contains various parameters for each 'address'. Dictionary tuple
    # format is:
    #   (field name, decode fn, field size, common name)
    # where:
    #   field name:  the name of the device field as per the gateway API
    #                documentation.eg ITEM_INTEMP
    #   decode fn:   the name of the function used to decode the field data
    #   field size:  the size of field data in bytes
    #   common name: common use name for the field, eg intemp
    addressed_data_struct = {
        b'\x01': ('ITEM_INTEMP', 'decode_temp', 2, 'intemp'),
        b'\x02': ('ITEM_OUTTEMP', 'decode_temp', 2, 'outtemp'),
        b'\x03': ('ITEM_DEWPOINT', 'decode_temp', 2, 'dewpoint'),
        b'\x04': ('ITEM_WINDCHILL', 'decode_temp', 2, 'windchill'),
        b'\x05': ('ITEM_HEATINDEX', 'decode_temp', 2, 'heatindex'),
        b'\x06': ('ITEM_INHUMI', 'decode_humid', 1, 'inhumid'),
        b'\x07': ('ITEM_OUTHUMI', 'decode_humid', 1, 'outhumid'),
        b'\x08': ('ITEM_ABSBARO', 'decode_press', 2, 'absbarometer'),
        b'\x09': ('ITEM_RELBARO', 'decode_press', 2, 'relbarometer'),
        b'\x0A': ('ITEM_WINDDIRECTION', 'decode_dir', 2, 'winddir'),
        b'\x0B': ('ITEM_WINDSPEED', 'decode_speed', 2, 'windspeed'),
        b'\x0C': ('ITEM_GUSTSPEED', 'decode_speed', 2, 'gustspeed'),
        b'\x0D': ('ITEM_RAINEVENT', 'decode_rain', 2, 't_rainevent'),
        b'\x0E': ('ITEM_RAINRATE', 'decode_rainrate', 2, 't_rainrate'),
        b'\x0F': ('ITEM_RAIN_Gain', 'decode_gain_100', 2, 't_raingain'),
        b'\x10': ('ITEM_RAINDAY', 'decode_rain', 2, 't_rainday'),
        b'\x11': ('ITEM_RAINWEEK', 'decode_rain', 2, 't_rainweek'),
        b'\x12': ('ITEM_RAINMONTH', 'decode_big_rain', 4, 't_rainmonth'),
        b'\x13': ('ITEM_RAINYEAR', 'decode_big_rain', 4, 't_rainyear'),
        b'\x14': ('ITEM_TOTALS', 'decode_big_rain', 4, 't_raintotals'),
        b'\x15': ('ITEM_LIGHT', 'decode_light', 4, 'light'),
        b'\x16': ('ITEM_UV', 'decode_uv', 2, 'uv'),
        b'\x17': ('ITEM_UVI', 'decode_uvi', 1, 'uvi'),
        b'\x18': ('ITEM_TIME', 'decode_datetime', 6, 'datetime'),
        b'\x19': ('ITEM_DAYLWINDMAX', 'decode_speed', 2, 'daymaxwind'),
        b'\x1A': ('ITEM_TEMP1', 'decode_temp', 2, 'temp1'),
        b'\x1B': ('ITEM_TEMP2', 'decode_temp', 2, 'temp2'),
        b'\x1C': ('ITEM_TEMP3', 'decode_temp', 2, 'temp3'),
        b'\x1D': ('ITEM_TEMP4', 'decode_temp', 2, 'temp4'),
        b'\x1E': ('ITEM_TEMP5', 'decode_temp', 2, 'temp5'),
        b'\x1F': ('ITEM_TEMP6', 'decode_temp', 2, 'temp6'),
        b'\x20': ('ITEM_TEMP7', 'decode_temp', 2, 'temp7'),
        b'\x21': ('ITEM_TEMP8', 'decode_temp', 2, 'temp8'),
        b'\x22': ('ITEM_HUMI1', 'decode_humid', 1, 'humid1'),
        b'\x23': ('ITEM_HUMI2', 'decode_humid', 1, 'humid2'),
        b'\x24': ('ITEM_HUMI3', 'decode_humid', 1, 'humid3'),
        b'\x25': ('ITEM_HUMI4', 'decode_humid', 1, 'humid4'),
        b'\x26': ('ITEM_HUMI5', 'decode_humid', 1, 'humid5'),
        b'\x27': ('ITEM_HUMI6', 'decode_humid', 1, 'humid6'),
        b'\x28': ('ITEM_HUMI7', 'decode_humid', 1, 'humid7'),
        b'\x29': ('ITEM_HUMI8', 'decode_humid', 1, 'humid8'),
        b'\x2A': ('ITEM_PM25_CH1', 'decode_pm25', 2, 'pm251'),
        b'\x2B': ('ITEM_SOILTEMP1', 'decode_temp', 2, 'soiltemp1'),
        b'\x2C': ('ITEM_SOILMOISTURE1', 'decode_moist', 1, 'soilmoist1'),
        b'\x2D': ('ITEM_SOILTEMP2', 'decode_temp', 2, 'soiltemp2'),
        b'\x2E': ('ITEM_SOILMOISTURE2', 'decode_moist', 1, 'soilmoist2'),
        b'\x2F': ('ITEM_SOILTEMP3', 'decode_temp', 2, 'soiltemp3'),
        b'\x30': ('ITEM_SOILMOISTURE3', 'decode_moist', 1, 'soilmoist3'),
        b'\x31': ('ITEM_SOILTEMP4', 'decode_temp', 2, 'soiltemp4'),
        b'\x32': ('ITEM_SOILMOISTURE4', 'decode_moist', 1, 'soilmoist4'),
        b'\x33': ('ITEM_SOILTEMP5', 'decode_temp', 2, 'soiltemp5'),
        b'\x34': ('ITEM_SOILMOISTURE5', 'decode_moist', 1, 'soilmoist5'),
        b'\x35': ('ITEM_SOILTEMP6', 'decode_temp', 2, 'soiltemp6'),
        b'\x36': ('ITEM_SOILMOISTURE6', 'decode_moist', 1, 'soilmoist6'),
        b'\x37': ('ITEM_SOILTEMP7', 'decode_temp', 2, 'soiltemp7'),
        b'\x38': ('ITEM_SOILMOISTURE7', 'decode_moist', 1, 'soilmoist7'),
        b'\x39': ('ITEM_SOILTEMP8', 'decode_temp', 2, 'soiltemp8'),
        b'\x3A': ('ITEM_SOILMOISTURE8', 'decode_moist', 1, 'soilmoist8'),
        b'\x3B': ('ITEM_SOILTEMP9', 'decode_temp', 2, 'soiltemp9'),
        b'\x3C': ('ITEM_SOILMOISTURE9', 'decode_moist', 1, 'soilmoist9'),
        b'\x3D': ('ITEM_SOILTEMP10', 'decode_temp', 2, 'soiltemp10'),
        b'\x3E': ('ITEM_SOILMOISTURE10', 'decode_moist', 1, 'soilmoist10'),
        b'\x3F': ('ITEM_SOILTEMP11', 'decode_temp', 2, 'soiltemp11'),
        b'\x40': ('ITEM_SOILMOISTURE11', 'decode_moist', 1, 'soilmoist11'),
        b'\x41': ('ITEM_SOILTEMP12', 'decode_temp', 2, 'soiltemp12'),
        b'\x42': ('ITEM_SOILMOISTURE12', 'decode_moist', 1, 'soilmoist12'),
        b'\x43': ('ITEM_SOILTEMP13', 'decode_temp', 2, 'soiltemp13'),
        b'\x44': ('ITEM_SOILMOISTURE13', 'decode_moist', 1, 'soilmoist13'),
        b'\x45': ('ITEM_SOILTEMP14', 'decode_temp', 2, 'soiltemp14'),
        b'\x46': ('ITEM_SOILMOISTURE14', 'decode_moist', 1, 'soilmoist14'),
        b'\x47': ('ITEM_SOILTEMP15', 'decode_temp', 2, 'soiltemp15'),
        b'\x48': ('ITEM_SOILMOISTURE15', 'decode_moist', 1, 'soilmoist15'),
        b'\x49': ('ITEM_SOILTEMP16', 'decode_temp', 2, 'soiltemp16'),
        b'\x4A': ('ITEM_SOILMOISTURE16', 'decode_moist', 1, 'soilmoist16'),
        b'\x4C': ('ITEM_LOWBATT', 'decode_batt', 16, 'lowbatt'),
        b'\x4D': ('ITEM_PM25_24HAVG1', 'decode_pm25', 2, 'pm251_24h_avg'),
        b'\x4E': ('ITEM_PM25_24HAVG2', 'decode_pm25', 2, 'pm252_24h_avg'),
        b'\x4F': ('ITEM_PM25_24HAVG3', 'decode_pm25', 2, 'pm253_24h_avg'),
        b'\x50': ('ITEM_PM25_24HAVG4', 'decode_pm25', 2, 'pm254_24h_avg'),
        b'\x51': ('ITEM_PM25_CH2', 'decode_pm25', 2, 'pm252'),
        b'\x52': ('ITEM_PM25_CH3', 'decode_pm25', 2, 'pm253'),
        b'\x53': ('ITEM_PM25_CH4', 'decode_pm25', 2, 'pm254'),
        b'\x58': ('ITEM_LEAK_CH1', 'decode_leak', 1, 'leak1'),
        b'\x59': ('ITEM_LEAK_CH2', 'decode_leak', 1, 'leak2'),
        b'\x5A': ('ITEM_LEAK_CH3', 'decode_leak', 1, 'leak3'),
        b'\x5B': ('ITEM_LEAK_CH4', 'decode_leak', 1, 'leak4'),
        b'\x60': ('ITEM_LIGHTNING', 'decode_distance', 1, 'lightningdist'),
        b'\x61': ('ITEM_LIGHTNING_TIME', 'decode_utc', 4, 'lightningdettime'),
        b'\x62': ('ITEM_LIGHTNING_POWER', 'decode_count', 4, 'lightningcount'),
        # whilst WN34 battery data is available via live data the preference is
        # to obtain such data from sensor ID data (as with other sensors)
        b'\x63': ('ITEM_TF_USR1', 'decode_wn34', 3, 'temp9'),
        b'\x64': ('ITEM_TF_USR2', 'decode_wn34', 3, 'temp10'),
        b'\x65': ('ITEM_TF_USR3', 'decode_wn34', 3, 'temp11'),
        b'\x66': ('ITEM_TF_USR4', 'decode_wn34', 3, 'temp12'),
        b'\x67': ('ITEM_TF_USR5', 'decode_wn34', 3, 'temp13'),
        b'\x68': ('ITEM_TF_USR6', 'decode_wn34', 3, 'temp14'),
        b'\x69': ('ITEM_TF_USR7', 'decode_wn34', 3, 'temp15'),
        b'\x6A': ('ITEM_TF_USR8', 'decode_wn34', 3, 'temp16'),
        b'\x6C': ('ITEM_HEAP_FREE', 'decode_memory', 4, 'heap_free'),
        # whilst WH45 battery data is available via live data the preference is
        # to obtain such data from sensor ID data (as with other sensors)
        b'\x70': ('ITEM_SENSOR_CO2', 'decode_wh45', 16, ('temp17', 'humid17', 'pm10',
                                                         'pm10_24h_avg', 'pm255',
                                                         'pm255_24h_avg', 'co2',
                                                         'co2_24h_avg')),
        # placeholder for unknown field 0x71
        b'\x71': ('ITEM_PM25_AQI', None, None),
        b'\x72': ('ITEM_LEAF_WETNESS_CH1', 'decode_wet', 1, 'leafwet1'),
        b'\x73': ('ITEM_LEAF_WETNESS_CH2', 'decode_wet', 1, 'leafwet2'),
        b'\x74': ('ITEM_LEAF_WETNESS_CH3', 'decode_wet', 1, 'leafwet3'),
        b'\x75': ('ITEM_LEAF_WETNESS_CH4', 'decode_wet', 1, 'leafwet4'),
        b'\x76': ('ITEM_LEAF_WETNESS_CH5', 'decode_wet', 1, 'leafwet5'),
        b'\x77': ('ITEM_LEAF_WETNESS_CH6', 'decode_wet', 1, 'leafwet6'),
        b'\x78': ('ITEM_LEAF_WETNESS_CH7', 'decode_wet', 1, 'leafwet7'),
        b'\x79': ('ITEM_LEAF_WETNESS_CH8', 'decode_wet', 1, 'leafwet8'),
        b'\x7A': ('ITEM_RAIN_Priority', 'decode_int', 1, 'rain_priority'),
        b'\x7B': ('ITEM_radcompensation', 'decode_int', 1, 'temperature_comp'),
        b'\x80': ('ITEM_Piezo_Rain_Rate', 'decode_rainrate', 2, 'p_rainrate'),
        b'\x81': ('ITEM_Piezo_Event_Rain', 'decode_rain', 2, 'p_rainevent'),
        b'\x82': ('ITEM_Piezo_Hourly_Rain', 'decode_reserved', 2, 'p_rainhour'),
        b'\x83': ('ITEM_Piezo_Daily_Rain', 'decode_big_rain', 4, 'p_rainday'),
        b'\x84': ('ITEM_Piezo_Weekly_Rain', 'decode_big_rain', 4, 'p_rainweek'),
        b'\x85': ('ITEM_Piezo_Monthly_Rain', 'decode_big_rain', 4, 'p_rainmonth'),
        b'\x86': ('ITEM_Piezo_yearly_Rain', 'decode_big_rain', 4, 'p_rainyear'),
        # field 0x87 and 0x88 hold device parameter data that is not
        # included in the loop packets, hence the device field is not
        # used (None).
        b'\x87': ('ITEM_Piezo_Gain10', 'decode_rain_gain', 20, None),
        b'\x88': ('ITEM_RST_RainTime', 'decode_rain_reset', 3, None)
    }

    def __init__(self):
        """Initialise a GatewayApiParser object."""

        # Create an invertible API field name to field address dict. We could
        # define this statically but then any future changes to address based
        # data structure by ecowitt would require changes to the same
        # information in multiple locations within the code base. This way such
        # changes are limited to one location only.
        _field_idt = InvertibleMap()
        # iterate over the address based data structure
        for key, value in GatewayApiParser.addressed_data_struct.items():
            # for each address based data structure entry create an equivalent
            # API field name to field address in our invertible dict
            _field_idt[value[0]] = key
        # save our invertible dict for later use
        self.field_idt = _field_idt

    def parse_addressed_data(self, payload, structure):
        """Parse an address based API response data payload.

        Parses the data payload of an API response that uses an addressed
        based data structure, ie each data element is in the format

        <address byte> <data byte(s)>

        Data elements are assumed to be in any order and the data portion of
        each data element may consist of one or more bytes.

        payload:   API response payload to be parsed, bytestring
        structure: dict keyed by data element address and containing the field
                   name, decode function and field size to be used when
                   decoding the payload data

        Returns a dict of decoded data keyed by field name obtained from the
        structure parameter.
        """

        # initialise a dict to hold our parsed data
        data = {}
        # do we have any payload data to operate on
        if len(payload) > 0:
            # we have payload data
            # set a counter to keep track of where we are in the payload
            index = 0
            # work through the payload until we reach the end
            while index < len(payload) - 1:
                # obtain the decode function, field size and field name for
                # the current field, wrap in a try..except in case we
                # encounter a field address we do not know about
                try:
                    field_name, decode_fn_str, field_size, common_name = structure[payload[index:index + 1]]
                except KeyError:
                    # We struck a field 'address' we do not know how to
                    # process. We can't skip to the next field so all we
                    # can really do is accept the data we have so far,
                    # highlight the issue and ignore the remaining data.
                    # notify of the problem
                    print(f"Unknown field address '{bytes_to_hex(payload[index:index + 1])}' detected. "
                          f"Remaining data '{bytes_to_hex(payload[index + 1:])}' ignored.")
                    # and break, there is nothing more we can with this
                    # data
                    break
                else:
                    _field_data = getattr(self, decode_fn_str)(payload[index + 1:index + 1 + field_size],
                                                               field_name)
                    # do we have any decoded data?
                    if _field_data is not None:
                        # we have decoded data so add the decoded data to
                        # our data dict
                        data.update(_field_data)
                    else:
                        # we received None from the decode function, this
                        # usually indicates a field marked as 'reserved' in
                        # the API documentation
                        pass
                    # we are finished with this field, move onto the next
                    index += field_size + 1
        return data

    def parse_livedata(self, payload):
        """Parse the data payload from a CMD_GW1000_LIVEDATA API response.

        Payload consists of a bytestring of variable length dependent on the
        number of connected sensors.

        Returns a dict of live sensor data keyed by gateway API field name
        (eg ITEM_INTEMP etc).
        """

        # this is addressed data, so we can call parse_addressed_data() and
        # return the result
        return self.parse_addressed_data(payload, self.addressed_data_struct)

    def parse_rain(self, payload):
        """Parse the data payload from a CMD_READ_RAIN API response.


        Payload consists of a bytestring of variable length dependent on the
        number of connected sensors.

        Returns a dict of live rain data keyed by gateway API field name
        (eg ITEM_RAINRATE etc).
        """

        # this is addressed data, so we can call parse_addressed_data() and
        # return the result
        return self.parse_addressed_data(payload, self.addressed_data_struct)

    def parse_raindata(self, payload):
        """Parse the data payload from a CMD_READ_RAINDATA API response.

        Payload consists of a bytestring of length 20. Decode as
        follows:

        Parameter       Byte(s)     Data format     Comments
          Name
        ------------------------------------------------------------------------
        rain rate       0 to 3      unsigned long   0 to 60000 in tenths mm/hr
        day rain        4 to 7      unsigned long   0 to 99999 in tenths mm
        week rain       8 to 11     unsigned long   0 to 99999 in tenths mm
        month rain      12 to 15    unsigned long   0 to 99999 in tenths mm
        year rain       16 to 19    unsigned long   0 to 99999 in tenths mm

        Note CMD_READ_RAINDATA returns traditional rain gauge rain data only.
        It does not return piezo rain data.

        Returns a dict keyed as follows:

        't_rate'    rain rate (0 - 6000 mm/hr)
        't_day'     rain rate (0 - 9999.9 mm)
        't_week'    rain rate (0 - 9999.9 mm)
        't_month'   rain rate (0 - 9999.9 mm)
        't_year'    rain rate (0 - 9999.9 mm)
        """

        # create a dict holding our parsed data
        data_dict = {'t_rate': self.decode_big_rain(payload[0:4]),
                     't_day': self.decode_big_rain(payload[4:8]),
                     't_week': self.decode_big_rain(payload[8:12]),
                     't_month': self.decode_big_rain(payload[12:16]),
                     't_year': self.decode_big_rain(payload[16:20])}
        return data_dict

    @staticmethod
    def parse_mulch_offset(payload):
        """Parse the data payload from a CMD_GET_MulCH_OFFSET API response.

        Payload consists of a bytestring of length 24. Decode as follows:

        Parameter                Byte(s)  Data format    Comments
          Name
        ------------------------------------------------------------------------
        channel                  0        unsigned byte  fixed value 0 = channel 1
        ch 1 humidity offset     1        unsigned byte  -10 to 10 %
        ch 1 temperature offset  2        unsigned byte  -100 - +100 tenths °C
        channel                  3        unsigned byte  fixed value 1 = channel 2
        ch 2 humidity offset     4        unsigned byte  -10 to 10 %
        ch 2 temperature offset  5        unsigned byte  -100 - +100 tenths °C
        ..
        channel                  21       unsigned byte  fixed value 7 = channel 8
        ch n humidity offset     22       unsigned byte  -10 to 10 %
        ch n temperature offset  23       unsigned byte  -100 - +100 tenths °C

        Returns a nested dict keyed by channel (eg 0, 1, 2 .. 7) with each
        sub-dict keyed as follows:

        'hum'    channel n humidity offset (-10 - 10 %)
        'temp'   channel n temperature offset (-10.0 - 10.0 °C)
        """

        # initialise a counter
        index = 0
        # initialise a dict to hold our parsed data
        offset_dict = {}
        # iterate over the data
        while index < len(payload):
            channel = payload[index]
            offset_dict[channel] = {}
            try:
                offset_dict[channel]['hum'] = struct.unpack("b", payload[index + 1])[0]
            except TypeError:
                offset_dict[channel]['hum'] = struct.unpack("b", bytes([payload[index + 1]]))[0]
            try:
                offset_dict[channel]['temp'] = struct.unpack("b", payload[index + 2])[0] / 10.0
            except TypeError:
                offset_dict[channel]['temp'] = struct.unpack("b", bytes([payload[index + 2]]))[0] / 10.0
            index += 3
        return offset_dict

    def parse_mulch_t_offset(self, payload):
        """Parse the data payload from a CMD_GET_MulCH_T_OFFSET API response.

        Note: As of gateway API documentation v1.6.9 the CMD_GET_MulCH_T_OFFSET
        command is still not documented. The command code 0x59 has been
        supported in firmware for various devices for some time. The
        CMD_GET_MulCH_T_OFFSET command and response format has been deduced and
        the command appears stable. However, it has been noted that on GW1000
        devices the offset data is presented in a single signed byte whereas for
        other devices the offset data is presented as a signed short.

        The payload consists of addressed sensor offset data where each address
        matches one of the ITEM_TF_USRx field addresses.

        The payload consists of a bytestring of variable length depending on
        connected sensors. Each sensor address is decoded as follows:

        Parameter           Byte(s)  Data format    Comments
          Name
        ------------------------------------------------------------------------
        address             0        unsigned byte  0x63 - 0x6A
        temperature offset  1 or     signed byte    temperature offset for given
                            1 to 2   signed short   address, maybe a signed byte
                                                    or signed short depending on
                                                    device/firmware.
                                                    -100 - +100 tenths °C
        etc

        Returns a dict of temperature offset data keyed by address (eg 0x63 etc)
        """

        def parse_addressed(payload, st_format):
            """Parse simple address based data with user specified format."""

            # obtain a struct.Struct object using the specified format
            st = struct.Struct(st_format)
            # initialise a counter
            index = 0
            # initialise a dict to hold our parsed data
            _dict = {}
            # iterate over the data
            while index < len(payload):
                # obtain the address, this is the first byte of each address
                # based data chunk
                address = self.field_idt.inverse[payload[index:index + 1]]
                # obtain the data, in this case the data is in tenths so divide
                # by 10 to get the real value
                _dict[address] = st.unpack(payload[index + 1:index + 1 + st.size])[0] / 10.0
                # increment our index, the amount to increment is dependent on
                # the size of the data
                index += st.size + 1
            # return the parsed data
            return _dict

        # Try parsing the data as a signed short, if we have data that is a
        # signed byte we will likely encounter a KeyError or struct.error
        # exception. In that case we should try parsing the data as a signed
        # byte.
        try:
            # attempt to parse as a signed short
            offset_dict = parse_addressed(payload, '>h')
        except (KeyError, struct.error):
            # We encountered an error, try parsing as a signed byte. If this
            # does not work an exception will likely be raised which will halt
            # the program.
            offset_dict = parse_addressed(payload, 'b')
        # return the parsed data
        return offset_dict

    @staticmethod
    def parse_pm25_offset(payload):
        """Parse the data from a CMD_GET_PM25_OFFSET API response.

        Payload consists of a bytestring of length 12. Decode as follows:

        Parameter         Byte(s)    Data format      Comments
        ------------------------------------------------------------------------
        channel           0          unsigned byte   fixed value 0 = channel 1
        PM2.5 offset      1 to 2     signed short    -200 - +200 tenths μg/m³
        channel           3          unsigned byte   fixed value 1 = channel 2
        PM2.5 offset      4 to 5     signed short    -200 - +200 tenths μg/m³
        channel           6          unsigned byte   fixed value 2 = channel 3
        PM2.5 offset      7 to 8     signed short    -200 - +200 tenths μg/m³
        channel           9          unsigned byte   fixed value 3 = channel 4
        PM2.5 offset      10 to 11   signed short    -200 - +200 tenths μg/m³

        Returns a dict of PM2.5 offset values (-20.0 to +20.0 μg/m³) keyed by
        channel (eg 0, 1 .. 7).

        Response only includes channels with active sensors.
        """

        # initialise a counter
        index = 0
        # initialise a dict to hold our parsed data
        offset_dict = {}
        # iterate over the data
        while index < len(payload):
            # obtain the channel
            channel = payload[index]
            # obtian the offset value for the channel and add to the dict
            offset_dict[channel] = struct.unpack(">h", payload[index + 1:index + 3])[0] / 10.0
            # increment the index to the next channel
            index += 3
        # return the parsed data
        return offset_dict

    @staticmethod
    def parse_co2_offset(payload):
        """Parse the data from a CMD_GET_CO2_OFFSET API response.

        Payload consists of a bytestring of length 6. Decode as follows:

        Parameter         Byte(s)    Data format      Comments
        ------------------------------------------------------------------------
        CO2 offset        0 to 1     signed short     -600 - +10000 ppm
        PM2.5 offset      2 to 3     signed short     -200 - +200 tenths μg/m³
        PM10 offset       4 to 5     signed short     -200 - +200 tenths μg/m³

        Returns a dict of offset values keyed as follows:

        'co2'   CO2 offset (CO2 -600 - +10000 ppm)
        'pm25'  PM2.5 offset (PM2.5 -20.0 to +20.0 μg/m³)
        'pm10'  PM10 offset (PM2.5 -20.0 to +20.0 μg/m³)
        """

        # Create a dict holding our parsed data. bytes 0 and 1 hold the CO2
        # offset, bytes 2 and 3 hold the PM2.5 offset, bytes 4 and 5 hold the
        # PM10 offset
        offset_dict = {'co2': struct.unpack(">h", payload[0:2])[0],
                       'pm25': struct.unpack(">h", payload[2:4])[0] / 10.0,
                       'pm10': struct.unpack(">h", payload[4:6])[0] / 10.0}
        # return the parsed data
        return offset_dict

    @staticmethod
    def parse_gain(payload):
        """Parse the data from a CMD_READ_GAIN API response.

        Payload consists of a bytestring of length 12. Decode as follows:

        Parameter         Byte(s)    Data format      Comments
        ------------------------------------------------------------------------
        reserved          0 to 1      unsigned short      fixed value 1267 in tenths
        uvGain            2 to 3      unsigned short      10 to 500 in hundredths
        solarRadGain      4 to 5      unsigned short      10 to 500 in hundredths
        windGain          6 to 7      unsigned short      10 to 500 in hundredths
        rainGain          8 to 9      unsigned short      10 to 500 in hundredths
        reserved          10 to 11    unsigned short      reserved

        Returns a dict of gain values keyed as follows:

        'reserved1'     the value 126.7
        'uv'            UV gain (0.10 to 5.00)
        'solar'         solar radiation gain (0.10 to 5.00)
        'wind'          wind speed gain (0.10 to 5.00)
        'rain'          traditional rain gain (0.10 to 5.00)
        'reserved2'     reserved
        """

        # create a dict holding the parsed data
        gain_dict = {'reserved1': struct.unpack(">H", payload[0:2])[0] / 10.0,
                     'uv': struct.unpack(">H", payload[2:4])[0] / 100.0,
                     'solar': struct.unpack(">H", payload[4:6])[0] / 100.0,
                     'wind': struct.unpack(">H", payload[6:8])[0] / 100.0,
                     'rain': struct.unpack(">H", payload[8:10])[0] / 100.0,
                     'reserved2': struct.unpack(">H", payload[10:12])[0]}
        # return the parsed data
        return gain_dict

    @staticmethod
    def parse_calibration(payload):
        """Parse the data from a CMD_READ_CALIBRATION API response.

        Payload consists of a bytestring of length 16. Decode as follows:

        Parameter           Byte(s)     Data format     Comments
        ------------------------------------------------------------------------
        intemp offset       0 to 1      signed short    inside temperature offset,
                                                        -100 - +100 tenths °C
        inhum offset        2           signed byte     inside temperature offset,
                                                        -10 - +10 %
        abs offset          3 to 6      signed long     absolute pressure offset,
                                                        -800 - +800 tenths hPa
        rel offset          7 to 10     signed long     relative pressure offset,
                                                        -800 - +800 tenths hPa
        outtemp offset      10 to 12    signed short    outside temperature offset,
                                                        -100 - +100 tenths °C
        outhum offset       13          signed byte     outside temperature offset,
                                                        -10 - +10 %
        winddir offset      14 to 15    signed short    wind direction offset,
                                                        -180 - +180 °

        Returns a dict of gain values keyed as follows:

        'intemp'    inside temperature offset (-10.0 to +10.0 °C)
        'inhum'     inside humidity (-10 to +10 %)
        'abs'       absolute pressure offset (-80.0 to +80.0 hPa)
        'rel'       relative pressure offset (-80.0 to +80.0 hPa)
        'outtemp'   outside temperature offset (-10.0 to +10.0 °C)
        'outhum'    outside humidity (-10 to +10 %)
        'dir'       wind direction offset (-180 - +180 °)
        """

        # create a dict containing the decoded offset data
        cal_dict = {'intemp': struct.unpack(">h", payload[0:2])[0] / 10.0,
                    'inhum': struct.unpack("b", payload[2])[0],
                    'abs': struct.unpack(">l", payload[3:7])[0] / 10.0,
                    'rel': struct.unpack(">l", payload[7:11])[0] / 10.0,
                    'outtemp': struct.unpack(">h", payload[11:13])[0] / 10.0,
                    'outhum': struct.unpack("b", payload[13])[0],
                    'dir':  struct.unpack(">h", payload[14:16])[0]}
        # return the parsed response
        return cal_dict

    @staticmethod
    def parse_soil_humiad(payload):
        """Parse the data from a CMD_GET_SOILHUMIAD API response.

        Payload consists of a bytestring of variable length depending on the
        number of connected sensors (n * 8 bytes where n is the number of
        connected sensors). Decode as follows:

        Parameter         Byte(s)    Data format      Comments
        ------------------------------------------------------------------------
        channel number    0           unsigned byte       channel number (0 to 8)
        current hum       1           unsigned byte       current humidity (0 to 100 %)
        current ad        2 to 3      unsigned short      current AD (0 to 100 %)
        custom cal        4           unsigned byte       humidity ad select, 0 = sensor,
                                                          1 = enabled
        min ad            5           unsigned byte       0% ad setting (70 to 200)
        max ad            6 to 7      unsigned short      100% ad setting (80 to 1000)
        ...
        structure (bytes 0 to 7) repeats for remaining connected sensors

        Returns a nested dict keyed by channel (eg 0, 1, 2 .. 7) with each
        sub-dict keyed as follows:

        'humidity'      channel n humidity offset (-10 - 10 %)
        'ad'            channel n temperature offset (-10.0 - 10.0 °C)
        'ad_select'
        'adj_min'
        'adj_max'

        """

        # initialise a dict to hold our final data
        cal_dict = {}
        # initialise a counter
        index = 0
        # iterate over the data
        while index < len(payload):
            channel = payload[index]
            cal_dict[channel] = {}
            try:
                humidity = payload[index + 1]
            except TypeError:
                humidity = payload[index + 1]
            cal_dict[channel]['humidity'] = humidity
            cal_dict[channel]['ad'] = struct.unpack(">h", payload[index + 2:index + 4])[0]
            try:
                ad_select = payload[index + 4]
            except TypeError:
                ad_select = payload[index + 4]
            # get 'Customize' setting 1 = enable, 0 = customized
            cal_dict[channel]['ad_select'] = ad_select
            try:
                min_ad = payload[index + 5]
            except TypeError:
                min_ad = payload[index + 5]
            cal_dict[channel]['adj_min'] = min_ad
            cal_dict[channel]['adj_max'] = struct.unpack(">h", payload[index + 6:index + 8])[0]
            index += 8
        # return the parsed response
        return cal_dict

    def parse_ssss(self, payload):
        """Parse a CMD_READ_SSSS API response data payload.

        Payload consists of a bytestring of length 8. Decode as
        follows:

        Parameter       Byte(s)     Data format     Comments
          Name
        ------------------------------------------------------------------------
        frequency       0           unsigned byte   operating frequency
                                                    (0=433MHz, 1=868MHz,
                                                    2=915MHz, 3=920MHz)
        sensor type     1           unsigned byte   sensor type (0=WH25, 1=WH65)
        utc time        2 to 5      unsigned long   utc time
        timezone index  6           byte            timezone index
        dst status      7           bit 0           daylight saving status
                                                    (0=DST off, 1=DST on)
        auto timezone   7           bit 1           auto timezone selection
                                                    (0=auto selection,
                                                    1=manual selection)

        Returns a dict keyed as follows:

        'frequency'         operating frequency
        'sensor_type'       sensor type
        'utc':              local time
        'timezone_index':   timezone index
        'dst_status':       dst status
        'auto_timezone':    auto timezone selection
        """

        # create a dict holding our parsed data payload
        data_dict = {'frequency': payload[0],
                     'sensor_type': payload[1],
                     'utc': self.decode_utc(payload[2:6]),
                     'timezone_index': payload[6],
                     'dst_status': payload[7] >> 0 & 1,
                     'auto_timezone': payload[7] >> 1 & 1}
        # return the parsed response data payload
        return data_dict

    @staticmethod
    def parse_ecowitt(payload):
        """Parse a CMD_READ_ECOWITT API response data payload.

        The data payload consists of one byte as follows:

        Parameter Name  Byte(s)  Data  Format  Comments
        interval        0        byte  0-5     upload interval in minutes

        Returns a dict keyed by parameter name.
        """

        # We have only one parameter, create a dict holding our parsed data.
        # Use [x] form rather than [x:x+1] so the result is an integer rather
        # than a bytestring
        data_dict = {'interval': payload[0]}
        # return the parsed response
        return data_dict

    @staticmethod
    def encode_ecowitt(**ecowitt):
        """Encode data parameters used for CMD_WRITE_ECOWITT.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_ECOWITT. Required payload parameters are contained in the
        ecowitt dict keyed as follows:

        interval:   upload interval in minutes, integer 0-5 inclusive, 0 means
                    upload is disabled

        Returns a bytestring of length 1.
        """

        interval_byte = struct.pack('B', ecowitt['interval'])
        return interval_byte

    @staticmethod
    def parse_wunderground(payload):
        """Parse a CMD_READ_WUNDERGROUND API response data payload.

        Payload consists of a variable number of bytes. Number of
        bytes = 3 + i + p where i = length of the WU ID in ASCII characters and
        p is the length of the WU password/key in ASCII characters. Decode as
        follows:

        Parameter Name  Byte(s)     Data format    Comments
        ID size         0           unsigned byte  length of WU ID (i)
        ID              1 - 1+i     i ASCII char   WU ID
        password size   7+i         unsigned byte  length of WU password (p)
        password/key    8+i -       p ASCII char   WU password/key
                        8+i+p
        fixed           9+i+p       unsigned byte  fixed value 1 - unused

        Returns a dict keyed as follows:

        'id'        WeatherUnderground station ID
        'password'  WeatherUnderground password/key
        """

        # initialise a dict to hold our final data
        data_dict = {}
        # obtain ID size in bytes
        id_size = payload[0]
        # obtain the WU ID as a bytestring, convert to ASCII and save to dict
        data_dict['id'] = payload[1:1 + id_size].decode()
        # obtain the password/key size in bytes
        password_size = payload[1 + id_size]
        # obtain the WU password/key as a bytestring, convert to ASCII and save to
        # dict
        data_dict['password'] = payload[2 + id_size:2 + id_size + password_size].decode()
        # return the parsed payload data
        return data_dict

    @staticmethod
    def encode_wu(**wu):
        """Encode data parameters used for CMD_WRITE_WUNDERGROUND.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_WUNDERGROUND. Required payload parameters are contained in
        the wu dict keyed as follows:

        id:         WeatherUnderground station ID
        password:   WeatherUnderground password/key

        The encoded bytestring format is:

        Byte(s)       Format    Comments
        0             byte      length of station ID (i)
        1 to i        i bytes   station ID (i characters)
        1+i           byte      length of station password/key (p)
        2+i to 1+i+p  p bytes   station password (p characters)

        Returns a bytestring of length 2+i+p.
        """

        # convert the station ID to a bytestring
        station_id_b = wu['id'].encode()
        # convert the password to a bytestring
        station_key_b = wu['password'].encode()
        # assemble and return the bytestring data payload
        return b''.join([struct.pack('B', len(station_id_b)),
                         station_id_b,
                         struct.pack('B', len(station_key_b)),
                         station_key_b])

    # Weathercloud and Weather Observations Website both use a station ID and
    # password/key in a similar manner to WeatherUnderground. The
    # CMD_WRITE_WCLOUD and CMD_WRITE_WOW API commands use the same data payload
    # format as CMD_WRITE_WUNDERGROUND. Consequently, we can use the
    # WeatherUnderground encode function to encode the CMD_WRITE_WCLOUD and
    # CMD_WRITE_WOW data payloads.
    encode_wcloud = encode_wu
    encode_wow = encode_wu

    @staticmethod
    def parse_wow(payload):
        """Parse a CMD_READ_WOW API response data payload.

        Payload consists of a variable number of bytes. Number of
        bytes = 4 + i + p + s where i = length of the WOW ID in ASCII
        characters, p is the length of the WOW password/key in ASCII characters
        and s is the length of the WOW station number in characters. Decode as
        follows:

        Parameter Name  Byte(s)    Format          Comments
        ID size         0          unsigned byte   length of WOW ID in
                                                   characters
        station ID      1 to 1+i   i x bytes       ASCII, max 39 characters
        password size   2+i        unsigned byte   length of WOW password in
                                                   characters
        password/key    3+i to     p x bytes       ASCII, max 32 characters
                        3+i+p
        station num     4+i+p      unsigned byte   length of WOW station num
        size
        station num     5+i+p to   s x bytes       ASCII, max 32 characters
                        15+i+p+s                   (unused)
        fixed           6+i+p+s    unsigned byte   fixed value 1 (unused)

        Returns a dict keyed as follows:

        'id':           Weather Observations Website station ID
        'password':     Weather Observations Website password/key
        'station_num':  Weather Observations Website station number
        """

        # initialise a dict to hold our final data
        data_dict = {}
        # obtain ID size in bytes
        id_size = payload[0]
        # obtain the WOW station ID as a bytestring, convert to ASCII and save
        # to dict
        data_dict['id'] = payload[1:1 + id_size].decode()
        # obtain password size in bytes
        pw_size = payload[1 + id_size]
        # obtain the WOW password as a bytestring, convert to ASCII and save to
        # dict
        data_dict['password'] = payload[2 + id_size:2 + id_size + pw_size].decode()
        # obtain station number size in bytes
        stn_num_size = payload[1 + id_size]
        # obtain the WOW station number as a bytestring, convert to ASCII and
        # save to dict
        data_dict['station_num'] = payload[3 + id_size + pw_size:3 + id_size + pw_size + stn_num_size].decode()
        # return the parsed payload data
        return data_dict

    @staticmethod
    def parse_weathercloud(payload):
        """Parse a CMD_READ_WEATHERCLOUD API data payload.

        Payload consists of a variable number of bytes. Number of
        bytes = 3 + i + p where i = length of the Weathercloud ID in ASCII
        characters, p is the length of the Weathercloud password/key in ASCII
        characters. Decode as follows:

        Parameter Name  Byte(s)    Format          Comments
        Byte(s) Data               Format          Comments
        ID size         0          unsigned byte   length of Weathercloud ID
                                                                in characters
        station ID      1 to 1+i   i x bytes       ASCII, max 32 characters
        password size   2+i        unsigned byte   length of Weathercloud key
                                                   in characters
        password/key    3+i to     p x bytes       ASCII, max 32 characters
                        3+i+p
        fixed           4+i+p      unsigned byte   fixed value 1 (unused)
        """

        # initialise a dict to hold our final data
        data_dict = {}
        # obtain ID size in bytes
        id_size = payload[0]
        # obtain the Weathercloud station ID as a bytestring, convert to ASCII
        # and save to dict
        data_dict['id'] = payload[1:1 + id_size].decode()
        # obtain key/password size in bytes
        key_size = payload[1 + id_size]
        # obtain the Weathercloud key/password as a bytestring, convert to
        # ASCII and save to dict
        data_dict['password'] = payload[2 + id_size:2 + id_size + key_size].decode()
        # return the parsed payload data
        return data_dict

    @staticmethod
    def parse_customized(payload):
        """Parse a CMD_READ_CUSTOMIZED API response data payload.

        Response consists of a variable number of bytes. Number of
        bytes = 14 + i + p + s where i = length of the ID in characters,
        p is the length of the password in characters and s is the length
        of the server address in characters. Decode as follows:

        Parameter Name  Byte(s)     Format          Comments
        ID size         0           unsigned byte   length of ID in ASCII
                                                    characters
        station ID      1 to +i     i x bytes       ASCII, max 40 characters
        password size   1+i         unsigned byte   length of password in
                                                    ASCII characters
        password        2+i to      p x bytes       ASCII, max 40 characters
                        1+i+p
        server address  2+i+p       unsigned byte   length of server address in
        size                                        ASCII characters
        server address  3+i+p to    s x bytes       ASCII, max 64 characters
                        2+i+p+s
        port number     3+i+p+s to  unsigned short  0 to 65535
                        4+i+p+s
        interval        5+i+p+s to  unsigned short  16 to 600 seconds
                        6+i+p+s
        type            7+i+p+s     byte            0=Ecowitt, 1=WU
        active          8+i+p+s     byte            0=disable, 1=enable

        Returns a dict keyed as follows:

        'id':       station ID
        'password': station password/key
        'server':   server name/address
        'port':     server port
        'interval': upload interval (seconds)
        'type':     upload data format 0=Ecowitt, 1=WU
        'active':   whether upload is enabled/disabled, 1=enabled, 0=disabled
        """

        # initialise a dict to hold our final data
        data_dict = {}
        # initialise a byte index/placeholder, we will be stepping through the
        # data payload bytestring
        index = 0
        # obtain ID size in bytes
        id_size = payload[index]
        # move to the first byte of the next field
        index += 1
        # obtain the station ID as a bytestring, convert to ASCII and save to
        # dict
        data_dict['id'] = payload[index:index + id_size].decode()
        # move to the first byte of the next field
        index += id_size
        # obtain password/key size in bytes
        password_size = payload[index]
        # move to the first byte of the next field
        index += 1
        # obtain the password/key as a bytestring, convert to ASCII and save to
        # dict
        data_dict['password'] = payload[index:index + password_size].decode()
        # move to the first byte of the next field
        index += password_size
        # obtain server name size in bytes
        server_size = payload[index]
        # move to the first byte of the next field
        index += 1
        # obtain the server name as a bytestring, convert to ASCII and save to
        # dict
        data_dict['server'] = payload[index:index + server_size].decode()
        # move to the first byte of the next field
        index += server_size
        # obtain the port number and save to dict
        data_dict['port'] = struct.unpack(">h", payload[index:index + 2])[0]
        # move to the first byte of the next field
        index += 2
        # obtain the upload interval and save to dict
        data_dict['interval'] = struct.unpack(">h", payload[index:index + 2])[0]
        # move to the first byte of the next field
        index += 2
        # obtain the upload data format and save to dict
        data_dict['type'] = payload[index]
        # move to the first byte of the next field
        index += 1
        # determine whether the uplaod is active or not amd save to dict
        data_dict['active'] = payload[index]
        # return the parsed data payload
        return data_dict

    @staticmethod
    def encode_customized(**custom):
        """Encode data parameters used for CMD_WRITE_CUSTOMIZED.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_CUSTOMIZED. Required payload parameters are contained in the
        custom dict keyed as follows:

        active:     whether the custom upload is active, 0 = inactive,
                    1 = active
        type:       what protocol (Ecowitt or WeatherUnderground) to use for
                    upload, 0 = Ecowitt, 1 = WeatherUnderground
        server:     server IP address or host name, string
        port:       server port number, integer 0 to 65536
        interval:   upload interval in seconds
        id:         WeatherUnderground station ID
        password:   WeatherUnderground key

        The encoded bytestring format is:

        Byte(s)       Format            Comments
        0             byte              length of station ID (i)
        1 to i        i bytes           station ID (i characters)
        1+i           byte              length of station password/key (p)
        2+i to 1+i+p  p bytes           station password (p characters)
        2+i+p         byte              length of server address
        3+i+p to      s bytes           server address
        2+i+p+s
        3+i+p+s to    unsigned short    server port
        4+i+p+s
        5+i+p+s to    unsigned short    upload interval
        6+i+p+s
        7+i+p+s       byte              type
        8+i+p+s       byte              active/inactive

        Returns a bytestring of length 9+i+p+s.
        """

        id_b = custom['id'].encode()
        password_b = custom['password'].encode()
        server_b = custom['server'].encode()
        port_b = struct.pack('>h', custom['port'])
        interval_b = struct.pack('>h', custom['interval'])
        type_b = struct.pack('B', custom['type'])
        active_b = struct.pack('B', custom['active'])
        return b''.join([struct.pack('B', len(id_b)),
                         id_b,
                         struct.pack('B', len(password_b)),
                         password_b,
                         struct.pack('B', len(server_b)),
                         server_b,
                         port_b,
                         interval_b,
                         type_b,
                         active_b])

    @staticmethod
    def parse_usr_path(payload):
        """Parse a CMD_READ_USR_PATH API response data payload.

        Response data payload consists of 2+e+w bytes where e = length of the
        'Ecowitt path' in characters and w is the length of the
        'WeatherUnderground path'. Decode as follows:

        Parameter Name  Byte(s)     Format          Comments
        Ecowitt size    0           unsigned byte   length of Ecowitt path in
                                                    ASCII characters
        Ecowitt path    1 to +i     i x bytes       ASCII, max 40 characters
        WU size         1+i         unsigned byte   length of WU path in ASCII
                                                    characters
        WU path         2+i to      p x bytes       ASCII, max 40 characters
                        1+i+p

        Returns a dict keyed as follows:

        'ecowitt_path': Ecowitt.net path
        'wu_path':      WeatherUnderground path
        """

        # initialise a dict to hold our final data
        data_dict = {}
        # initialise a byte index/placeholder, we will be stepping through the
        # data payload bytestring
        index = 0
        # obtain Ecowitt path size in bytes
        ecowitt_size = payload[index]
        # move to the first byte of the next field
        index += 1
        # obtain the Ecowitt path as a bytestring, convert to ASCII and save to
        # dict
        data_dict['ecowitt_path'] = payload[index:index + ecowitt_size].decode()
        # move to the first byte of the next field
        index += ecowitt_size
        # obtain WU path size in bytes
        wu_size = payload[index]
        # move to the first byte of the next field
        index += 1
        # obtain the WU path as a bytestring, convert to ASCII and save to dict
        data_dict['wu_path'] = payload[index:index + wu_size].decode()
        # return the parsed data payload
        return data_dict

    @staticmethod
    def encode_usr_path(**usr_path):
        """Encode data parameters used for CMD_WRITE_USRPATH.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_USRPATH. Required payload parameters are contained in the
        custom dict keyed as follows:

        ecowit_path:    the Ecowitt.net path
        wu_path:        the WeatherUnderground path

        The encoded bytestring format is:

        Byte(s)       Format            Comments
        0             byte              length of Ecowitt path (i)
        1 to i        i bytes           Ecowitt path (i characters)
        1+i           byte              length of WU path (p)
        2+i to 1+i+p  p bytes           WU path (p characters)

        Returns a bytestring of length 2+i+p.
        """

        ec_path_b = usr_path['ecowitt_path'].encode()
        wu_path_b = usr_path['wu_path'].encode()
        return b''.join([struct.pack('B', len(ec_path_b)),
                         ec_path_b,
                         struct.pack('B', len(wu_path_b)),
                         wu_path_b])

    @staticmethod
    def parse_station_mac(response):
        """Parse a CMD_READ_STATION_MAC API response data payload.

        Response consists of a bytestring 6 bytes in length as follows:

        Parameter Name  Byte(s)     Format          Comments
        station MAC     0 - 5       6 x bytes       6 x ASCII characters

        Returns a dict containing a single field keyed 'mac' that contains a
        string of colon separated uppercase hexadecimal digit pairs.
        """

        # return the parsed response, in this case we convert the bytes to
        # hexadecimal digits and return a string of colon separated
        # hexadecimal digit pairs
        return bytes_to_hex(response[4:10], separator=":")

    @staticmethod
    def parse_firmware_version(payload):
        """Parse a CMD_READ_FIRMWARE_VERSION API response data payload.

        Response consists of a bytestring of length 1+f where f is the length
        of the firmware version string. Decode as follows:

        Parameter Name  Byte(s)     Format          Comments
        firmware        0           byte            length of firmware version
        version size                                string
        firmware        1 to f      f x bytes       firmware version string

        Returns a dict containing a single field keyed 'firmware' that contains
        a unicode firmware version string.
        """

        # get the length of the firmware version string
        fw_size = payload[0]
        # get the firmware version bytestring, decode to a unicode string and
        # return the resulting string
        return payload[1:1 + fw_size].decode()

    @staticmethod
    def decode_reserved(data, field='reserved'):
        """Decode data that is marked 'reserved'.

        Occasionally some fields are marked as 'reserved' in the API
        documentation. In such cases the decode routine should return the
        value None which will cause the data to be ignored.
        """

        return None

    @staticmethod
    def decode_temp(data, field=None):
        """Decode temperature data.

        Data is contained in a two byte big endian signed integer and
        represents tenths of a degree. If field is not None return the
        result as a dict in the format {field: decoded value} otherwise
        return just the decoded value.
        """

        if len(data) == 2:
            value = struct.unpack(">h", data)[0] / 10.0
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_humid(data, field=None):
        """Decode humidity data.

        Data is contained in a single unsigned byte and represents whole
        units. If field is not None return the result as a dict in the
        format {field: decoded value} otherwise return just the decoded
        value.
        """

        if len(data) == 1:
            value = struct.unpack("B", data)[0]
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_press(data, field=None):
        """Decode pressure data.

        Data is contained in a two byte big endian integer and represents
        tenths of a unit. If data contains more than two bytes take the
        last two bytes. If field is not None return the result as a dict in
        the format {field: decoded value} otherwise return just the decoded
        value.

        Also used to decode other two byte big endian integer fields.
        """

        if len(data) == 2:
            value = struct.unpack(">H", data)[0] / 10.0
        elif len(data) > 2:
            value = struct.unpack(">H", data[-2:])[0] / 10.0
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_dir(data, field=None):
        """Decode direction data.

        Data is contained in a two byte big endian integer and represents
        whole degrees. If field is not None return the result as a dict in
        the format {field: decoded value} otherwise return just the decoded
        value.
        """

        if len(data) == 2:
            value = struct.unpack(">H", data)[0]
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_big_rain(data, field=None):
        """Decode 4 byte rain data.

        Data is contained in a four byte big endian integer and represents
        tenths of a unit. If field is not None return the result as a dict
        in the format {field: decoded value} otherwise return just the
        decoded value.
        """

        if len(data) == 4:
            value = struct.unpack(">L", data)[0] / 10.0
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_datetime(data, field=None):
        """Decode date-time data.

        Unknown format but length is six bytes. If field is not None return
        the result as a dict in the format {field: decoded value} otherwise
        return just the decoded value.
        """

        if len(data) == 6:
            value = struct.unpack("BBBBBB", data)
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_distance(data, field=None):
        """Decode lightning distance.

        Data is contained in a single byte integer and represents a value
        from 0 to 40km. If field is not None return the result as a dict in
        the format {field: decoded value} otherwise return just the decoded
        value.
        """

        if len(data) == 1:
            value = struct.unpack("B", data)[0]
            value = value if value <= 40 else None
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_utc(data, field=None):
        """Decode UTC time.

        The API documentation claims to provide 'UTC time' as a 4 byte big
        endian integer. The 4 byte integer is a unix epoch timestamp;
        however, the timestamp is offset by the station's timezone. So for
        a station in the +10 hour timezone, the timestamp returned is the
        present epoch timestamp plus 10 * 3600 seconds.

        When decoded in localtime the decoded date-time is off by the
        station time zone, when decoded as GMT the date and time figures
        are correct but the timezone is incorrect.

        In any case decode the 4 byte big endian integer as is and any
        further use of this timestamp needs to take the above time zone
        offset into account when using the timestamp.

        If field is not None return the result as a dict in the format
        {field: decoded value} otherwise return just the decoded value.
        """

        if len(data) == 4:
            # unpack the 4 byte int
            value = struct.unpack(">L", data)[0]
            # when processing the last lightning strike time if the value
            # is 0xFFFFFFFF it means we have never seen a strike so return
            # None
            value = value if value != 0xFFFFFFFF else None
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_count(data, field=None):
        """Decode lightning count.

        Count is an integer stored in a four byte big endian integer. If
        field is not None return the result as a dict in the format
        {field: decoded value} otherwise return just the decoded value.
        """

        if len(data) == 4:
            value = struct.unpack(">L", data)[0]
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    @staticmethod
    def decode_gain_100(data, field=None):
        """Decode a sensor gain expressed in hundredths.

        Gain is stored in a four byte big endian integer and represents
        hundredths of a unit.
        """

        if len(data) == 2:
            value = struct.unpack(">H", data)[0] / 100.0
        else:
            value = None
        if field is not None:
            return {field: value}
        return value

    # alias' for other decodes
    decode_speed = decode_press
    decode_rain = decode_press
    decode_rainrate = decode_press
    decode_light = decode_big_rain
    decode_uv = decode_press
    decode_uvi = decode_humid
    decode_moist = decode_humid
    decode_pm25 = decode_press
    decode_leak = decode_humid
    decode_pm10 = decode_press
    decode_co2 = decode_dir
    decode_wet = decode_humid
    decode_int = decode_humid
    decode_memory = decode_count

    def decode_wn34(self, data, field=None):
        """Decode WN34 sensor data.

        Data consists of three bytes:

        Byte    Field               Comments
        1-2     temperature         standard Ecowitt temperature data, two
                                    byte big endian signed integer
                                    representing tenths of a degree
        3       battery voltage     0.02 * value Volts

        WN34 battery state data is included in the WN34 sensor data (along
        with temperature) as well as in the complete sensor ID data. In
        keeping with other sensors we do not use the sensor data battery
        state, rather we obtain it from the sensor ID data.

        If field is not None return the result as a dict in the format
        {field: decoded value} otherwise return just the decoded value.
        """

        if len(data) == 3 and field is not None:
            results = {field: self.decode_temp(data[0:2])}
            # we could decode the battery voltage, but we will be obtaining
            # battery voltage data from the sensor IDs in a later step, so
            # we can skip it here
            return results
        return {}

    def decode_wh45(self, data, fields=None):
        """Decode WH45 sensor data.

        WH45 sensor data includes TH sensor values, CO2/PM2.5/PM10 sensor
        values and 24 hour aggregates and battery state data in 16 bytes.

        The 16 bytes of WH45 sensor data is allocated as follows:
        Byte(s) #      Data               Format          Comments
        bytes   1-2    temperature        short           C x10
                3      humidity           unsigned byte   percent
                4-5    PM10               unsigned short  ug/m3 x10
                6-7    PM10 24-hour avg   unsigned short  ug/m3 x10
                8-9    PM2.5              unsigned short  ug/m3 x10
                10-11  PM2.5 24-hour avg  unsigned short  ug/m3 x10
                12-13  CO2                unsigned short  ppm
                14-15  CO2 24-hour avg    unsigned short  ppm
                16     battery state      unsigned byte   0-5 <=1 is low

        WH45 battery state data is included in the WH45 sensor data (along
        with temperature) as well as in the complete sensor ID data. In
        keeping with other sensors we do not use the sensor data battery
        state, rather we obtain it from the sensor ID data.
        """

        if len(data) == 16 and fields is not None:
            results = {fields[0]: self.decode_temp(data[0:2]),
                       fields[1]: self.decode_humid(data[2:3]),
                       fields[2]: self.decode_pm10(data[3:5]),
                       fields[3]: self.decode_pm10(data[5:7]),
                       fields[4]: self.decode_pm25(data[7:9]),
                       fields[5]: self.decode_pm25(data[9:11]),
                       fields[6]: self.decode_co2(data[11:13]),
                       fields[7]: self.decode_co2(data[13:15])}
            # we could decode the battery state, but we will be obtaining
            # battery state data from the sensor IDs in a later step, so
            # we can skip it here
            return results
        return {}

    def decode_rain_gain(self, data, fields=None):
        """Decode piezo rain gain data.

        Piezo rain gain data is 20 bytes of data comprising 10 two byte big
        endian fields with each field representing a value in hundredths of
        a unit.

        The 20 bytes of piezo rain gain data is allocated as follows:
        Byte(s) #      Data      Format            Comments
        bytes   1-2    gain1     unsigned short    gain x 100
                3-4    gain2     unsigned short    gain x 100
                5-6    gain3     unsigned short    gain x 100
                7-8    gain4     unsigned short    gain x 100
                9-10   gain5     unsigned short    gain x 100
                11-12  gain6     unsigned short    gain x 100, reserved
                13-14  gain7     unsigned short    gain x 100, reserved
                15-16  gain8     unsigned short    gain x 100, reserved
                17-18  gain9     unsigned short    gain x 100, reserved
                19-20  gain10    unsigned short    gain x 100, reserved

        As of device firmware v2.1.3 gain6-gain10 inclusive are unused and
        reserved for future use.
        """

        if len(data) == 20:
            results = {}
            for gain in range(10):
                results[f'gain{int(gain):d}'] = self.decode_gain_100(data[gain * 2:gain * 2 + 2])
            return results
        return {}

    @staticmethod
    def decode_rain_reset(data, fields=None):
        """Decode rain reset data.

        Rain reset data is three bytes of data comprising three unsigned
        byte fields with each field representing an integer.

        The three bytes of rain reset data is allocated as follows:
        Byte  #  Data               Format         Comments
        byte  1  day reset time     unsigned byte  hour of the day to reset day
                                                   rain, eg 7 = 07:00
              2  week reset time    unsigned byte  day of week to reset week rain,
                                                   allowed values are 0 or 1. 0=Sunday, 1=Monday
              3  annual reset time  unsigned byte  month of year to reset annual
                                                   rain, allowed values are 0-11, eg 2 = March
        """

        if len(data) == 3:
            results = {'day_reset': struct.unpack("B", data[0:1])[0],
                       'week_reset': struct.unpack("B", data[1:2])[0],
                       'annual_reset': struct.unpack("B", data[2:3])[0]}
            return results
        return {}

    @staticmethod
    def decode_batt(data, field=None):
        """Decode battery status data.

        GW1000 firmware version 1.6.4 and earlier supported 16 bytes of
        battery state data at response field x4C for the following sensors:
            WH24, WH25, WH26(WH32), WH31 ch1-8, WH40, WH41/WH43 ch1-4,
            WH51 ch1-8, WH55 ch1-4, WH57, WH68 and WS80

        As of GW1000 firmware version 1.6.5 the 16 bytes of battery state
        data is no longer returned at all (GW1100, GW2000 and later devices
        never provided this battery state data in this format).
        CMD_READ_SENSOR_ID_NEW or CMD_READ_SENSOR_ID must be used to obtain
        battery state information for connected sensors. The decode_batt()
        method has been retained to support devices using firmware
        version 1.6.4 and earlier.

        Since the gateway driver now obtains battery state information via
        CMD_READ_SENSOR_ID_NEW or CMD_READ_SENSOR_ID only the decode_batt()
        method now returns None so that firmware versions before 1.6.5
        continue to be supported.
        """

        return None

    @staticmethod
    def encode_gain(**gain):
        """Encode data parameters used for CMD_WRITE_GAIN.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_GAIN. Required payload parameters are contained in the gain
        dict keyed as follows:

        uv:     uv gain, integer 10-500                 --> unsigned short
        solar:  solar radiation gain, integer 10-500    --> unsigned short
        wind:   wind speed gain, integer 10-500         --> unsigned short
        rain:   rain gain, integer 10-500               --> unsigned short

        The CMD_WRITE_GAIN data payload includes two reserved integer values.
        The first two bytes contain the value 1267 and the last two bytes are
        only marked as 'reserved' with no value given (we will store the
        value 0).

        reserved1: reserved, fixed value of 1267        --> unsigned short
        reserved2: reserved, value not specified        --> unsigned short

        Returns a bytestring.
        """

        reserved1_b = struct.pack('>H', 1267)
        uv_b = struct.pack('>H', int(gain['uv'] * 100))
        solar_b = struct.pack('>H', int(gain['solar'] * 100))
        wind_b = struct.pack('>H', int(gain['wind'] * 100))
        rain_b = struct.pack('>H', int(gain['rain'] * 100))
        reserved2_b = struct.pack('>H', 0)
        return b''.join([reserved1_b,
                         uv_b,
                         solar_b,
                         wind_b,
                         rain_b,
                         reserved2_b])

    @staticmethod
    def encode_calibration(**calibration):
        """Encode data parameters used for CMD_WRITE_CALIBRATION.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_CALIBRATION. Required payload parameters are contained in the
        calibration dict keyed as follows:

        intemp:  inside temperature offset, float -100 - +100  --> signed short
        inhum:   inside humidity offset, float -10 - +10       --> signed byte
        abs:     absolute pressure offset, float -800 - +800   --> signed long
        rel:     relative pressure offset, float -800 - +800   --> signed long
        outtemp: outside temperature offset, float -100 - +100 --> signed short
        outhum:  outside humidity offset, float -10 - +10      --> signed byte
        winddir: wind direction offset, float -180 - +180      --> signed short

        Returns a bytestring.
        """

        intemp_b = struct.pack('>h', int(calibration['intemp'] * 100))
        inhum_b = struct.pack('>b', int(calibration['inhum']))
        abs_b = struct.pack('>l', int(calibration['abs'] * 100))
        rel_b = struct.pack('>l', int(calibration['rel'] * 100))
        outtemp_b = struct.pack('>h', int(calibration['outtemp'] * 100))
        outhum_b = struct.pack('>b', int(calibration['outhum']))
        winddir_b = struct.pack('>h', int(calibration['winddir']))
        return b''.join([intemp_b,
                         inhum_b,
                         abs_b,
                         rel_b,
                         outtemp_b,
                         outhum_b,
                         winddir_b])

    @staticmethod
    def encode_sensor_id(**ids):
        """Encode data parameters used for CMD_WRITE_SENSOR_ID.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_SENSOR_ID. The ids dict consists of sensor ID data keyed by
        sensor address. Payload consists of a sequence of sensor address
        followed by sensor ID for each sensor. The sensor address is
        represented as a single byte and sensor ID is represented as a long
        integer.

        Returns a bytestring.
        """

        # initialise a list to hold bytestring components of the result
        comp = []
        # iterate over the list of sensor addresses in address order
        for name, id_and_address in ids.items():
            # append the sensor address to our result list
            comp.append(struct.pack('b', id_and_address['address']))
            # append the sensor ID to our result list
            comp.append(struct.pack('>L', id_and_address['id']))
        # return a bytestring consisting of the concatenated list elements
        return b''.join(comp)

    @staticmethod
    def encode_pm25_offsets(**offsets):
        """Encode data parameters used for CMD_SET_PM25_OFFSET.

        Assemble a bytestring to be used as the data payload for
        CMD_SET_PM25_OFFSET. The ids dict consists of sensor ID data keyed by
        sensor address. Payload consists of a sequence of sensor address
        followed by sensor ID for each sensor. The sensor address is
        represented as a single byte and sensor ID is represented as a long
        integer.

        Returns a bytestring.
        """

        # initialise a list to hold bytestring components of the result
        comp = []
        # iterate over the list of sensor addresses in address order
        for channel, offset in offsets.items():
            # append the channel number to our result list
            comp.append(struct.pack('b', int(channel[-1])))
            # append the offset value to our result list
            comp.append(struct.pack('>h', offset * 10))
        # return a bytestring consisting of the concatenated list elements
        return b''.join(comp)

    @staticmethod
    def encode_co2_offsets(**offsets):
        """Encode data parameters used for CMD_SET_CO2_OFFSET.

        Assemble a bytestring to be used as the data payload for
        CMD_SET_CO2_OFFSET. Required payload parameters are contained in the
        calibration dict keyed as follows:

        co2:  CO2 offset, float -600 - +10 000  --> signed short
        pm25: PM2.5 offset, float -200 - +200   --> signed short
        pm10: PM10 offset, float -200 - +200    --> signed short

        Returns a bytestring.
        """

        co2_b = struct.pack('>h', int(offsets['co2']))
        pm25_b = struct.pack('>h', int(offsets['pm25'] * 10))
        pm10_b = struct.pack('>h', int(offsets['pm10'] * 10))
        return b''.join([co2_b, pm25_b, pm10_b])

    @staticmethod
    def encode_rain_params(**offsets):
        """Encode data parameters used for CMD_WRITE_RAIN.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_RAIN. Required payload parameters are contained in the
        calibration dict keyed as follows:

        rate:       rain rate, float -600 - +10 000  --> signed short
        day:        PM2.5 offset, float -200 - +200   --> signed short
        week:       PM10 offset, float -200 - +200    --> signed short
        month:
        year:
        event:
        gain:
        p_rate:
        p_event:
        p_day:
        p_week:
        p_month:
        p_year:
        priority:
        gain0:
        gain1:
        gain2:
        gain3:
        gain4:
        gain5:
        gain6:
        gain7:
        gain8:
        gain9:
        day_reset:
        week_reset:
        year_reset:

        Returns a bytestring.
        """

        co2_b = struct.pack('>h', int(offsets['co2']))
        pm25_b = struct.pack('>h', int(offsets['pm25'] * 10))
        pm10_b = struct.pack('>h', int(offsets['pm10'] * 10))
        return b''.join([co2_b, pm25_b, pm10_b])

    @staticmethod
    def encode_system_params(**params):
        """Encode data parameters used for CMD_WRITE_SSSS.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_SSSS. Required payload parameters are contained in the
        calibration dict keyed as follows:

        frequency:      operating frequency, integer        --> byte (read only)
                        0=433MHz, 1=868MHz, 2=915MHz, 3=920MHz
        sensor_type:    sensor type, integer 0=WH24, 1=WH65 --> byte
        utc:            system time, integer                --> unsigned long
                                                                (read only)
        timezone_index: timezone index, integer             --> byte
        dst_status:     DST status, integer                 --> byte (bit 0 only)
                        0=disabled, 1=enabled
        auto_timezone:  auto timezone detection and         --> byte (bit 1 only)
                        setting, integer 0=auto timezone,       (same byte as DST)
                        1=manual timezone

        Byte 0 (frequency) and bytes 2 to 5 (utc) are read only and cannot be
        set via CMD_WRITE_SSS; however, the CMD_WRITE_SSS data payload format
        includes both frequency and utc.

        Byte 7 (dst) is a combination of dst_status and auto_timezone as follows:
            bit 0 = 0 if DST disabled
            bit 0 = 1 if DST enabled
            bit 1 = 0 if auto timezone is enabled
            bit 1 = 1 if auto timezone is disabled

        Returns a bytestring.
        """

        freq_b = struct.pack('b', params['frequency'])
        sensor_type_b = struct.pack('b', params['sensor_type'])
        utc_b = struct.pack('>L', params['utc'])
        tz_b = struct.pack('b', params['timezone_index'])
        # The DST param is a combination of DST status (bit 0) and auto
        # timezone (bit 1)
        # start with nothing
        _dst = 0
        # set the DST bit if DST enabled
        if params['dst_status'] == 1:
            _dst = _dst | (1 << 0)
        # set the auto timezone bit if auto timezone is disabled
        if params['auto_timezone'] == 1:
            _dst = _dst | (1 << 1)
        # convert to a byte
        dst_b = struct.pack('b', _dst)
        return b''.join([freq_b, sensor_type_b, utc_b, tz_b, dst_b])

    @staticmethod
    def encode_rain_data(**params):
        """Encode data parameters used for CMD_WRITE_RAINDATA.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_SSSS. Required payload parameters are contained in the
        calibration dict keyed as follows:

        frequency:      operating frequency, integer        --> byte (read only)
                        0=433MHz, 1=868MHz, 2=915MHz, 3=920MHz
        sensor_type:    sensor type, integer 0=WH24, 1=WH65 --> byte
        utc:            system time, integer                --> unsigned long
                                                                (read only)
        timezone_index: timezone index, integer             --> byte
        dst_status:     DST status, integer                 --> byte (bit 0 only)
                        0=disabled, 1=enabled
        auto_timezone:  auto timezone detection and         --> byte (bit 1 only)
                        setting, integer 0=auto timezone,       (same byte as DST)
                        1=manual timezone

        Byte 0 (frequency) and bytes 2 to 5 (utc) are read only and cannot be
        set via CMD_WRITE_SSS; however, the CMD_WRITE_SSS data payload format
        includes both frequency and utc.

        Byte 7 (dst) is a combination of dst_status and auto_timezone as follows:
            bit 0 = 0 if DST disabled
            bit 0 = 1 if DST enabled
            bit 1 = 0 if auto timezone is enabled
            bit 1 = 1 if auto timezone is disabled

        Returns a bytestring.
        """

        day_b = struct.pack('>L', int(params['t_day'] * 10))
        week_b = struct.pack('>L', int(params['t_week'] * 10))
        month_b = struct.pack('>L', int(params['t_month'] * 10))
        year_b = struct.pack('>L', int(params['t_year'] * 10))
        return b''.join([day_b, week_b, month_b, year_b])

    @staticmethod
    def encode_mulch_th(**params):
        """Encode data parameters used for CMD_WRITE_RAINDATA.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_SSSS. Required payload parameters are contained in the
        calibration dict keyed as follows:

        frequency:      operating frequency, integer        --> byte (read only)
                        0=433MHz, 1=868MHz, 2=915MHz, 3=920MHz
        sensor_type:    sensor type, integer 0=WH24, 1=WH65 --> byte
        utc:            system time, integer                --> unsigned long
                                                                (read only)
        timezone_index: timezone index, integer             --> byte
        dst_status:     DST status, integer                 --> byte (bit 0 only)
                        0=disabled, 1=enabled
        auto_timezone:  auto timezone detection and         --> byte (bit 1 only)
                        setting, integer 0=auto timezone,       (same byte as DST)
                        1=manual timezone

        Byte 0 (frequency) and bytes 2 to 5 (utc) are read only and cannot be
        set via CMD_WRITE_SSS; however, the CMD_WRITE_SSS data payload format
        includes both frequency and utc.

        Byte 7 (dst) is a combination of dst_status and auto_timezone as follows:
            bit 0 = 0 if DST disabled
            bit 0 = 1 if DST enabled
            bit 1 = 0 if auto timezone is enabled
            bit 1 = 1 if auto timezone is disabled

        Returns a bytestring.
        """

        day_b = struct.pack('>L', int(params['t_day'] * 10))
        week_b = struct.pack('>L', int(params['t_week'] * 10))
        month_b = struct.pack('>L', int(params['t_month'] * 10))
        year_b = struct.pack('>L', int(params['t_year'] * 10))
        return b''.join([day_b, week_b, month_b, year_b])

    @staticmethod
    def encode_soil_moist(**params):
        """Encode data parameters used for CMD_WRITE_RAINDATA.

        Assemble a bytestring to be used as the data payload for
        CMD_WRITE_SSSS. Required payload parameters are contained in the
        calibration dict keyed as follows:

        frequency:      operating frequency, integer        --> byte (read only)
                        0=433MHz, 1=868MHz, 2=915MHz, 3=920MHz
        sensor_type:    sensor type, integer 0=WH24, 1=WH65 --> byte
        utc:            system time, integer                --> unsigned long
                                                                (read only)
        timezone_index: timezone index, integer             --> byte
        dst_status:     DST status, integer                 --> byte (bit 0 only)
                        0=disabled, 1=enabled
        auto_timezone:  auto timezone detection and         --> byte (bit 1 only)
                        setting, integer 0=auto timezone,       (same byte as DST)
                        1=manual timezone

        Byte 0 (frequency) and bytes 2 to 5 (utc) are read only and cannot be
        set via CMD_WRITE_SSS; however, the CMD_WRITE_SSS data payload format
        includes both frequency and utc.

        Byte 7 (dst) is a combination of dst_status and auto_timezone as follows:
            bit 0 = 0 if DST disabled
            bit 0 = 1 if DST enabled
            bit 1 = 0 if auto timezone is enabled
            bit 1 = 1 if auto timezone is disabled

        Returns a bytestring.
        """

        day_b = struct.pack('>L', int(params['t_day'] * 10))
        week_b = struct.pack('>L', int(params['t_week'] * 10))
        month_b = struct.pack('>L', int(params['t_month'] * 10))
        year_b = struct.pack('>L', int(params['t_year'] * 10))
        return b''.join([day_b, week_b, month_b, year_b])

    def encode_mulch_t(self, **offsets):
        """Encode data parameters used for CMD_SET_MulCH_T_OFFSET.

        Assemble a bytestring to be used as the data payload for
        CMD_SET_MulCH_T_OFFSET. Required payload parameters are contained in
        the calibration dict keyed as follows:

        frequency:      operating frequency, integer        --> byte (read only)
                        0=433MHz, 1=868MHz, 2=915MHz, 3=920MHz
        sensor_type:    sensor type, integer 0=WH24, 1=WH65 --> byte
        utc:            system time, integer                --> unsigned long
                                                                (read only)
        timezone_index: timezone index, integer             --> byte
        dst_status:     DST status, integer                 --> byte (bit 0 only)
                        0=disabled, 1=enabled
        auto_timezone:  auto timezone detection and         --> byte (bit 1 only)
                        setting, integer 0=auto timezone,       (same byte as DST)
                        1=manual timezone

        Byte 0 (frequency) and bytes 2 to 5 (utc) are read only and cannot be
        set via CMD_WRITE_SSS; however, the CMD_WRITE_SSS data payload format
        includes both frequency and utc.

        Byte 7 (dst) is a combination of dst_status and auto_timezone as follows:
            bit 0 = 0 if DST disabled
            bit 0 = 1 if DST enabled
            bit 1 = 0 if auto timezone is enabled
            bit 1 = 1 if auto timezone is disabled

        Returns a bytestring.
        """


        # initialise a list to hold bytestring components of the result
        comp = []
        # iterate over the list of sensor addresses in address order
        for channel, offset in offsets.items():
            # append the channel number to our result list
            comp.append(self.field_idt[channel])
            # append the offset value to our result list
            comp.append(struct.pack('b', int(offset * 10)))
        # return a bytestring consisting of the concatenated list elements
        print("comp=%s" % (comp,))
        return b''.join(comp)


class Sensors:
    """Class to manage device sensor ID data.

    Class Sensors allows access to various elements of sensor ID data via a
    number of properties and methods when the class is initialised with the
    device response to a CMD_READ_SENSOR_ID_NEW or CMD_READ_SENSOR_ID API
    command.

    A Sensors object can be initialised with sensor ID data on
    instantiation or an existing Sensors object can be updated by calling
    the set_sensor_id_data() method and passing the sensor ID data to be
    used as the only parameter.
    """

    # reversible sensor ident map
    sensor_idt = InvertibleMap({
        # 'eWH24_SENSOR': 00,
        'eWH65_SENSOR': 00,
        #  'eWH69_SENSOR': 1,
        'eWH68_SENSOR': 1,
        'eWH80_SENSOR': 2,
        'eWH40_SENSOR': 3,
        'eWH25_SENSOR': 4,
        'eWH26_SENSOR': 5,
        'eWH31_SENSORCH1': 6,
        'eWH31_SENSORCH2': 7,
        'eWH31_SENSORCH3': 8,
        'eWH31_SENSORCH4': 9,
        'eWH31_SENSORCH5': 10,
        'eWH31_SENSORCH6': 11,
        'eWH31_SENSORCH7': 12,
        'eWH31_SENSORCH8': 13,
        'eWH51_SENSORCH1': 14,
        'eWH51_SENSORCH2': 15,
        'eWH51_SENSORCH3': 16,
        'eWH51_SENSORCH4': 17,
        'eWH51_SENSORCH5': 18,
        'eWH51_SENSORCH6': 19,
        'eWH51_SENSORCH7': 20,
        'eWH51_SENSORCH8': 21,
        'eWH41_SENSORCH1': 22,
        'eWH41_SENSORCH2': 23,
        'eWH41_SENSORCH3': 24,
        'eWH41_SENSORCH4': 25,
        'eWH57_SENSOR': 26,
        'eWH55_SENSORCH1': 27,
        'eWH55_SENSORCH2': 28,
        'eWH55_SENSORCH3': 29,
        'eWH55_SENSORCH4': 30,
        'eWH34_SENSORCH1': 31,
        'eWH34_SENSORCH2': 32,
        'eWH34_SENSORCH3': 33,
        'eWH34_SENSORCH4': 34,
        'eWH34_SENSORCH5': 35,
        'eWH34_SENSORCH6': 36,
        'eWH34_SENSORCH7': 37,
        'eWH34_SENSORCH8': 38,
        'eWH45_SENSOR': 39,
        'eWH35_SENSORCH1': 40,
        'eWH35_SENSORCH2': 41,
        'eWH35_SENSORCH3': 42,
        'eWH35_SENSORCH4': 43,
        'eWH35_SENSORCH5': 44,
        'eWH35_SENSORCH6': 45,
        'eWH35_SENSORCH7': 46,
        'eWH35_SENSORCH8': 47,
        'eWH90_SENSOR': 48,
        'eMAX_SENSOR': 49
    })

    # map of sensor ids to short name, long name and battery byte decode
    # function
    sensor_ids = {
        b'\x00': {'name': 'wh65', 'long_name': 'WH65', 'batt_fn': 'batt_binary'},
        b'\x01': {'name': 'wh68', 'long_name': 'WH68', 'batt_fn': 'batt_volt'},
        b'\x02': {'name': 'ws80', 'long_name': 'WS80', 'batt_fn': 'batt_volt'},
        b'\x03': {'name': 'wh40', 'long_name': 'WH40', 'batt_fn': 'wh40_batt_volt'},
        b'\x04': {'name': 'wh25', 'long_name': 'WH25', 'batt_fn': 'batt_binary'},
        b'\x05': {'name': 'wh26', 'long_name': 'WH26', 'batt_fn': 'batt_binary'},
        b'\x06': {'name': 'wh31_ch1', 'long_name': 'WH31 ch1', 'batt_fn': 'batt_binary'},
        b'\x07': {'name': 'wh31_ch2', 'long_name': 'WH31 ch2', 'batt_fn': 'batt_binary'},
        b'\x08': {'name': 'wh31_ch3', 'long_name': 'WH31 ch3', 'batt_fn': 'batt_binary'},
        b'\x09': {'name': 'wh31_ch4', 'long_name': 'WH31 ch4', 'batt_fn': 'batt_binary'},
        b'\x0a': {'name': 'wh31_ch5', 'long_name': 'WH31 ch5', 'batt_fn': 'batt_binary'},
        b'\x0b': {'name': 'wh31_ch6', 'long_name': 'WH31 ch6', 'batt_fn': 'batt_binary'},
        b'\x0c': {'name': 'wh31_ch7', 'long_name': 'WH31 ch7', 'batt_fn': 'batt_binary'},
        b'\x0d': {'name': 'wh31_ch8', 'long_name': 'WH31 ch8', 'batt_fn': 'batt_binary'},
        b'\x0e': {'name': 'wh51_ch1', 'long_name': 'WH51 ch1', 'batt_fn': 'batt_volt_tenth'},
        b'\x0f': {'name': 'wh51_ch2', 'long_name': 'WH51 ch2', 'batt_fn': 'batt_volt_tenth'},
        b'\x10': {'name': 'wh51_ch3', 'long_name': 'WH51 ch3', 'batt_fn': 'batt_volt_tenth'},
        b'\x11': {'name': 'wh51_ch4', 'long_name': 'WH51 ch4', 'batt_fn': 'batt_volt_tenth'},
        b'\x12': {'name': 'wh51_ch5', 'long_name': 'WH51 ch5', 'batt_fn': 'batt_volt_tenth'},
        b'\x13': {'name': 'wh51_ch6', 'long_name': 'WH51 ch6', 'batt_fn': 'batt_volt_tenth'},
        b'\x14': {'name': 'wh51_ch7', 'long_name': 'WH51 ch7', 'batt_fn': 'batt_volt_tenth'},
        b'\x15': {'name': 'wh51_ch8', 'long_name': 'WH51 ch8', 'batt_fn': 'batt_volt_tenth'},
        b'\x16': {'name': 'wh41_ch1', 'long_name': 'WH41 ch1', 'batt_fn': 'batt_int'},
        b'\x17': {'name': 'wh41_ch2', 'long_name': 'WH41 ch2', 'batt_fn': 'batt_int'},
        b'\x18': {'name': 'wh41_ch3', 'long_name': 'WH41 ch3', 'batt_fn': 'batt_int'},
        b'\x19': {'name': 'wh41_ch4', 'long_name': 'WH41 ch4', 'batt_fn': 'batt_int'},
        b'\x1a': {'name': 'wh57', 'long_name': 'WH57', 'batt_fn': 'batt_int'},
        b'\x1b': {'name': 'wh55_ch1', 'long_name': 'WH55 ch1', 'batt_fn': 'batt_int'},
        b'\x1c': {'name': 'wh55_ch2', 'long_name': 'WH55 ch2', 'batt_fn': 'batt_int'},
        b'\x1d': {'name': 'wh55_ch3', 'long_name': 'WH55 ch3', 'batt_fn': 'batt_int'},
        b'\x1e': {'name': 'wh55_ch4', 'long_name': 'WH55 ch4', 'batt_fn': 'batt_int'},
        b'\x1f': {'name': 'wn34_ch1', 'long_name': 'WN34 ch1', 'batt_fn': 'batt_volt'},
        b'\x20': {'name': 'wn34_ch2', 'long_name': 'WN34 ch2', 'batt_fn': 'batt_volt'},
        b'\x21': {'name': 'wn34_ch3', 'long_name': 'WN34 ch3', 'batt_fn': 'batt_volt'},
        b'\x22': {'name': 'wn34_ch4', 'long_name': 'WN34 ch4', 'batt_fn': 'batt_volt'},
        b'\x23': {'name': 'wn34_ch5', 'long_name': 'WN34 ch5', 'batt_fn': 'batt_volt'},
        b'\x24': {'name': 'wn34_ch6', 'long_name': 'WN34 ch6', 'batt_fn': 'batt_volt'},
        b'\x25': {'name': 'wn34_ch7', 'long_name': 'WN34 ch7', 'batt_fn': 'batt_volt'},
        b'\x26': {'name': 'wn34_ch8', 'long_name': 'WN34 ch8', 'batt_fn': 'batt_volt'},
        b'\x27': {'name': 'wh45', 'long_name': 'WH45', 'batt_fn': 'batt_int'},
        b'\x28': {'name': 'wn35_ch1', 'long_name': 'WN35 ch1', 'batt_fn': 'batt_volt'},
        b'\x29': {'name': 'wn35_ch2', 'long_name': 'WN35 ch2', 'batt_fn': 'batt_volt'},
        b'\x2a': {'name': 'wn35_ch3', 'long_name': 'WN35 ch3', 'batt_fn': 'batt_volt'},
        b'\x2b': {'name': 'wn35_ch4', 'long_name': 'WN35 ch4', 'batt_fn': 'batt_volt'},
        b'\x2c': {'name': 'wn35_ch5', 'long_name': 'WN35 ch5', 'batt_fn': 'batt_volt'},
        b'\x2d': {'name': 'wn35_ch6', 'long_name': 'WN35 ch6', 'batt_fn': 'batt_volt'},
        b'\x2e': {'name': 'wn35_ch7', 'long_name': 'WN35 ch7', 'batt_fn': 'batt_volt'},
        b'\x2f': {'name': 'wn35_ch8', 'long_name': 'WN35 ch8', 'batt_fn': 'batt_volt'},
        b'\x30': {'name': 'ws90', 'long_name': 'WS90', 'batt_fn': 'batt_volt', 'low_batt': 3}
    }
    # sensors for which there is no low battery state
    no_low = ['ws80', 'ws90']
    # Tuple of sensor ID values for sensors that are not registered with
    # the device. 'fffffffe' means the sensor is disabled, 'ffffffff' means
    # the sensor is registering.
    not_registered = ('fffffffe', 'ffffffff')

    def __init__(self, sensor_id_data=None, ignore_wh40_batt=True,
                 show_battery=False, debug=0, use_wh32=True,
                 is_wh24=False):
        """Initialise myself"""

        # are we using a WH32 sensor, if so tell our sensor id decoding we have
        # a WH32, otherwise it will default to WH26.
        if use_wh32:
            # set the WH24 sensor id decode dict entry
            self.sensor_ids[b'\x05']['name'] = 'wh32'
            self.sensor_ids[b'\x05']['long_name'] = 'WH32'
        # Tell our sensor id decoding whether we have a WH24 or a WH65. By
        # default, we are coded to use a WH65. Is there a WH24 connected?
        if is_wh24:
            # set the WH24 sensor id decode dict entry
            self.sensor_ids[b'\x00']['name'] = 'wh24'
            self.sensor_ids[b'\x00']['long_name'] = 'WH24'

        # do we ignore battery state data from legacy WH40 sensors that do
        # not provide valid battery state data
        self.ignore_wh40_batt = ignore_wh40_batt
        # set the show_battery property
        self.show_battery = show_battery
        # initialise legacy WH40 flag
        self.legacy_wh40 = None
        # initialise a dict to hold the parsed sensor data
        self.sensor_data = {}
        # parse the raw sensor ID data and store the results in my parsed
        # sensor data dict
        self.set_sensor_id_data(sensor_id_data)
        # debug sensors
        self.debug = debug

    def parse_sensor_id_data(self, data):
        """Parse raw sensor ID data.

        Parse raw data obtained via the CMD_READ_SENSOR_ID_NEW API command.
        Sensor ID payload data consists of seven bytes of data for each
        reported sensor as follows:

        byte 1      sensor index    1 byte integer
        byte 2-5    sensor ID       4 byte unsigned long
        byte 6      battery state   1 byte integer (meaning dependent on sensor
                                                    type)
        byte 7      signal level    1 byte integer (0-6)

        Returns a dict keyed by sensor index with each dict value consisting of
        a dict keyed as follows:

        id:         Sensor ID as a four byte hexadecimal lowercase string.
                    String.
        battery:    Sensor battery state decoded by the applicable battery
                    decode function. May be None if battery levels for sensors
                    with no signal are ignored. Integer, real or None.
        signal:     Sensor signal level. Integer.
        """

        # initialise a dict to hold the parsed data
        sensor_data_dict = dict()
        # do we have any raw sensor ID data
        if data is not None and len(data) > 0:
            # Determine the packet size, it's a big endian short (two byte)
            # integer at bytes 4 and 5. The packet/packet size includes the
            # command code, size byte(s), data payload and checksum.
            packet_size = struct.unpack(">H", data[3:5])[0]
            # Extract the actual sensor id data payload. The payload starts at
            # byte 6 and is packet_size-4 bytes in length.
            payload = data[5:5 + packet_size - 4]
            # initialise a counter
            i = 0
            # iterate over the data payload
            while i < len(payload):
                # get the sensor data, each sensor has 7 bytes of data
                sensor_data = payload[i:i + 7]
                # get the sensor index, use x:y notation to ensure we get a
                # byte string not an integer
                sensor_index = sensor_data[0:1]
                # Is this a known or unknown sensor? If the sensor index is in
                # our sensors_id property it's known, otherwise it's unknown
                # and we don't know how to parse the data.
                if sensor_index in Sensors.sensor_ids:
                    # get the sensor ID as a lowercase hex string
                    sensor_id = bytes_to_hex(sensor_data[1:5],
                                             separator='',
                                             caps=False)
                    # get the sensor signal level, use x:y notation to ensure
                    # we get a byte string not an integer
                    sensor_signal = sensor_data[6]
                    # get the method to be used to decode the battery state
                    # data
                    batt_fn = getattr(self,
                                      Sensors.sensor_ids[sensor_index]['batt_fn'])
                    # if we are not showing all battery state data then the
                    # battery state for any sensor with signal == 0 must be set
                    # to None, otherwise parse the raw battery state data as
                    # applicable
                    if not self.show_battery and sensor_signal == 0:
                        sensor_batt_state = None
                    else:
                        # parse the raw battery state data, battery state is in
                        # byte 6
                        sensor_batt_state = batt_fn(sensor_data[5])
                    # construct a dict of data for this sensor and add this
                    # dict to our sensor data dict
                    sensor_data_dict[sensor_index] = {'id': sensor_id,
                                                      'battery': sensor_batt_state,
                                                      'signal': sensor_signal}
                else:
                    # advise the user we found an unknown sensor
                    print(f"Unknown sensor ID '{bytes_to_hex(sensor_index)}'")
                # increment our counter to the first byte of data for the next
                # sensor
                i += 7
        # return our dict of parsed sensor ID data
        return sensor_data_dict

    def set_sensor_id_data(self, id_data):
        """Parse the raw sensor ID data and store the results.

        id_data: bytestring of sensor ID data from the CMD_READ_SENSOR_ID_NEW
                 API command.

        Tested by SensorsTestCase.test_set_sensor_id_data
        """

        # parse the raw sensor ID data and update our sensor_data property with
        # the parsed data
        self.sensor_data = self.parse_sensor_id_data(id_data)

    @property
    def addresses(self):
        """Obtain a list of sensor addresses.

        This includes all sensor addresses reported by the device, this
        includes:
        - sensors that are actually connected to the device
        - sensors that are attempting to connect to the device
        - device sensor addresses that are searching for a sensor
        - device sensor addresses that are disabled

        Tested by SensorsTestCase.test_properties
        """

        # this is simply the list of keys to our sensor data dict
        return self.sensor_data.keys()

    @property
    def connected_addresses(self):
        """Obtain a list of sensor addresses for connected sensors only.

        Sometimes we only want a list of addresses for sensors that are
        actually connected to the gateway device. We can filter out those
        addresses that do not have connected sensors by looking at the
        sensor ID. If the sensor ID is 'fffffffe' either the sensor is
        connecting to the device or the device is searching for a sensor
        for that address. If the sensor ID is 'ffffffff' the device sensor
        address is disabled.

        Tested by SensorsTestCase.test_properties
        """

        # initialise a list to hold our connected sensor addresses
        connected_list = []
        # iterate over all sensors
        for address, data in self.sensor_data.items():
            # if the sensor ID is neither 'fffffffe' nor 'ffffffff' then it
            # must be connected
            if data['id'] not in self.not_registered:
                connected_list.append(address)
        return connected_list

    def ids_by_address(self, numeric_id=False):
        """Return a dict of sensor IDs keyed by address.

        Iterate over the address, data pairs in the sensor_data dict, extract
        the sensor ID and add to a new dict keyed by address. If numeric_id is
        True convert the sensor ID to a numeric value otherwise leave it as a
        hex string.

        Returns a dict of sensor IDs keyed by sensor address.
        """

        # initialise a dict to hold the sensor ID data
        ids = {}
        # iterate over the address, data pairs in the sensor_data dict
        for address, data in self.sensor_data.items():
            # add the sensor ID to our dict, if numeric_id is True convert the
            # sensor ID to a number, else leave as a string
            if numeric_id:
                ids[address] = int(data['id'], 16)
            else:
                ids[address] = data['id']
        # return the dict of sensor IDs
        return ids

    def ids_by_name(self, numeric_id=False):
        """Return a dict of sensor IDs keyed by sensor name.

        Iterate over the address, data pairs in the sensor_data dict, extract
        the sensor ID and add to a new dict keyed by sensor name,
        eg 'eWH90_SENSOR'. If numeric_id is True convert the sensor ID to a
        numeric value otherwise leave it as a hex string.

        Returns a dict of sensor IDs keyed by sensor name.
        """

        # initialise a dict to hold the sensor ID data
        ids = {}
        # iterate over the address, data pairs in the sensor_data dict
        for address, data in self.sensor_data.items():
            # obtain the sensor name
            name = self.sensor_idt.inverse.get(struct.unpack('b', address)[0])
            # add the sensor ID to our dict but use sensor name as the key, if
            # numeric_id is True convert the sensor ID to a number, else leave
            # as a string
            if numeric_id:
                ids[name] = int(data['id'], 16)
            else:
                ids[name] = data['id']
        # return the dict of sensor IDs
        return ids

    @property
    def data(self):
        """Obtain the data dict for all known sensors.

        Tested by SensorsTestCase.test_properties
        """

        return self.sensor_data

    def id(self, address):
        """Obtain the sensor ID for a given sensor address.

        Tested by SensorsTestCase.test_sensor_data_methods
        """

        return self.sensor_data[address]['id']

    def battery_state(self, address):
        """Obtain the sensor battery state for a given sensor address.

        Tested by SensorsTestCase.test_sensor_data_methods
        """

        return self.sensor_data[address]['battery']

    def signal_level(self, address):
        """Obtain the sensor signal level for a given sensor address.

        Tested by SensorsTestCase.test_sensor_data_methods
        """

        return self.sensor_data[address]['signal']

    @property
    def battery_and_signal_data(self):
        """Obtain a dict of sensor battery state and signal level data.

        Iterate over the list of connected sensors and obtain a dict of
        sensor battery state data for each connected sensor.

        Tested by SensorsTestCase.test_properties
        """

        # initialise a dict to hold the battery state data
        data = {}
        # iterate over our connected sensors
        for sensor in self.connected_addresses:
            # get the sensor name
            sensor_name = Sensors.sensor_ids[sensor]['name']
            # create the sensor battery state field for this sensor
            data[''.join([sensor_name, '_batt'])] = self.battery_state(sensor)
            # create the sensor signal level field for this sensor
            data[''.join([sensor_name, '_sig'])] = self.signal_level(sensor)
        # return our data
        return data

    @staticmethod
    def batt_state_desc(address, value):
        """Determine the battery state description for a given sensor.

        Given a sensor address and battery state value determine
        appropriate battery state descriptive text, eg 'low', 'OK' etc.
        Descriptive text is based on Ecowitt API documentation. None is
        returned for sensors for which the API documentation provides no
        suitable battery state data, or for which descriptive battery state
        text cannot be inferred.

        A battery state value of None should not occur but if received the
        descriptive text 'unknown' is returned.

        Tested by SensorsTestCase.test_battery_methods
        """

        if value is not None:
            if Sensors.sensor_ids[address].get('name') in Sensors.no_low:
                # we have a sensor for which no low battery cut-off
                # data exists
                return None
            batt_fn = Sensors.sensor_ids[address].get('batt_fn')
            if batt_fn == 'batt_binary':
                if value == 0:
                    return "OK"
                if value == 1:
                    return "low"
                return 'Unknown'
            if batt_fn == 'batt_int':
                if value <= 1:
                    return "low"
                if value == 6:
                    return "DC"
                if value <= 5:
                    return "OK"
                return 'Unknown'
            if batt_fn in ['batt_volt', 'batt_volt_tenth', 'wh40_batt_volt']:
                if value <= 1.2:
                    return "low"
                return "OK"
        else:
            return 'Unknown'
        return None

    @staticmethod
    def batt_binary(batt):
        """Decode a binary battery state.

        Battery state is stored in bit 0 as either 0 or 1. If 1 the battery
        is low, if 0 the battery is normal. We need to mask off bits 1 to 7 as
        they are not guaranteed to be set in any particular way.

        Tested by SensorsTestCase.test_battery_methods
        """

        return batt & 1

    @staticmethod
    def batt_int(batt):
        """Decode an integer battery state.

        According to the API documentation battery state is stored as an
        integer from 0 to 5 with <=1 being considered low. Experience with
        WH43 has shown that battery state 6 also exists when the device is
        run from DC. This does not appear to be documented in the API
        documentation.

        Tested by SensorsTestCase.test_battery_methods
        """

        return batt

    @staticmethod
    def batt_volt(batt):
        """Decode a voltage battery state in 2mV increments.

        Battery state is stored as integer values of battery voltage/0.02
        with <=1.2V considered low.

        Tested by SensorsTestCase.test_battery_methods
        """

        return round(0.02 * batt, 2)

    def wh40_batt_volt(self, batt):
        """Decode WH40 battery state.

        Initial WH40 devices did not provide battery state information. API
        versions up to and including v.1.6.4 reported WH40 battery state
        via a single bit. API v1.6.5 and later report WH40 battery state in
        a single byte in 100mV increments. It appears that API v1.6.5 and
        later return a fixed value of 0x10 (decodes to 1.6V) for WH40
        battery state for WH40 devices that do not report battery state.
        WH40 devices that do report battery state appear to return a value
        in a single byte in 10mV increments rather than 100mV increments as
        documented in the Ecowitt LAN/Wi-Fi Gateway API
        documentation v1.6.4. There is no known way to identify via the API
        whether a given WH40 reports battery state information or not.

        Consequently, decoding of WH40 battery state data is handled as
        follows:

        -   the WH40 battery state data is decoded as per the API
            documentation as a value in 100mV increments
        -   if the decoded value is <2.0V the device is assumed to be a
            non-battery state reporting WH40 and the value None is returned
        -   if the decoded value is >=2.0V the device is assumed to be a
            battery state reporting WH40 and the value returned is the WH40
            battery state data decoded in 10mV increments

        For WH40 that report battery state data a decoded value of <=1.2V
        is considered low.

        Tested by SensorsTestCase.test_battery_methods
        """

        if round(0.1 * batt, 1) < 2.0:
            # assume we have a non-battery state reporting WH40
            # first set the legacy_wh40 flag
            self.legacy_wh40 = True
            # then do we ignore the result or pass it on
            if self.ignore_wh40_batt:
                # we are ignoring the result so return None
                return None
            # we are not ignoring the result so return the result
            return round(0.1 * batt, 1)
        # assume we have a battery state reporting WH40
        # first reset the legacy_wh40 flag
        self.legacy_wh40 = False
        return round(0.01 * batt, 2)

    @staticmethod
    def batt_volt_tenth(batt):
        """Decode a voltage battery state in 100mV increments.

        Battery state is stored as integer values of battery voltage/0.1
        with <=1.2V considered low.

        Tested by SensorsTestCase.test_battery_methods
        """

        return round(0.1 * batt, 1)


class GatewayApi():
    """Class to interact with a gateway device via the Ecowitt LAN/Wi-Fi
    Gateway API.

    A GatewayApi object knows how to:
    1.  discover a device via UDP broadcast
    2.  send a command to the 'Gateway API'
    3.  receive a response from the 'Gateway API'
    4.  verify a 'Gateway API' response as valid

    A GatewayApi object may use a supplied IP address and port or the
    GatewayApi object may discover a device via UDP broadcast.
    """

    # Ecowitt LAN/Wi-Fi Gateway API commands
    api_commands = InvertibleMap({
        'CMD_WRITE_SSID': b'\x11',
        'CMD_BROADCAST': b'\x12',
        'CMD_READ_ECOWITT': b'\x1E',
        'CMD_WRITE_ECOWITT': b'\x1F',
        'CMD_READ_WUNDERGROUND': b'\x20',
        'CMD_WRITE_WUNDERGROUND': b'\x21',
        'CMD_READ_WOW': b'\x22',
        'CMD_WRITE_WOW': b'\x23',
        'CMD_READ_WEATHERCLOUD': b'\x24',
        'CMD_WRITE_WEATHERCLOUD': b'\x25',
        'CMD_READ_STATION_MAC': b'\x26',
        'CMD_GW1000_LIVEDATA': b'\x27',
        'CMD_GET_SOILHUMIAD': b'\x28',
        'CMD_SET_SOILHUMIAD': b'\x29',
        'CMD_READ_CUSTOMIZED': b'\x2A',
        'CMD_WRITE_CUSTOMIZED': b'\x2B',
        'CMD_GET_MulCH_OFFSET': b'\x2C',
        'CMD_SET_MulCH_OFFSET': b'\x2D',
        'CMD_GET_PM25_OFFSET': b'\x2E',
        'CMD_SET_PM25_OFFSET': b'\x2F',
        'CMD_READ_SSSS': b'\x30',
        'CMD_WRITE_SSSS': b'\x31',
        'CMD_READ_RAINDATA': b'\x34',
        'CMD_WRITE_RAINDATA': b'\x35',
        'CMD_READ_GAIN': b'\x36',
        'CMD_WRITE_GAIN': b'\x37',
        'CMD_READ_CALIBRATION': b'\x38',
        'CMD_WRITE_CALIBRATION': b'\x39',
        'CMD_READ_SENSOR_ID': b'\x3A',
        'CMD_WRITE_SENSOR_ID': b'\x3B',
        'CMD_READ_SENSOR_ID_NEW': b'\x3C',
        'CMD_WRITE_REBOOT': b'\x40',
        'CMD_WRITE_RESET': b'\x41',
        'CMD_WRITE_UPDATE': b'\x43',
        'CMD_READ_FIRMWARE_VERSION': b'\x50',
        'CMD_READ_USR_PATH': b'\x51',
        'CMD_WRITE_USR_PATH': b'\x52',
        'CMD_GET_CO2_OFFSET': b'\x53',
        'CMD_SET_CO2_OFFSET': b'\x54',
        'CMD_READ_RSTRAIN_TIME': b'\x55',
        'CMD_WRITE_RSTRAIN_TIME': b'\x56',
        'CMD_READ_RAIN': b'\x57',
        'CMD_WRITE_RAIN': b'\x58',
        'CMD_GET_MulCH_T_OFFSET': b'\x59',
        'CMD_SET_MulCH_T_OFFSET': b'\x5A'
    })
    destructive_cmd_codes = (b'\x11', b'\x1F', b'\x21', b'\x23', b'\x25',
                             b'\x29', b'\x2B', b'\x2D', b'\x2F', b'\x31',
                             b'\x35',b'\x37', b'\x39', b'\x3B', b'\x40',
                             b'\x41',b'\x43', b'\x52', b'\x54', b'\x56',
                             b'\x58')
    # header used in each API command and response packet
    header = b'\xff\xff'
    # known device models
    known_models = ('GW1000', 'GW1100', 'GW1200', 'GW2000',
                    'WH2650', 'WH2680', 'WN1900')

    def __init__(self, ip_address=None, port=None,
                 broadcast_address=None, broadcast_port=None,
                 socket_timeout=None, broadcast_timeout=None,
                 max_tries=DEFAULT_MAX_TRIES, retry_wait=DEFAULT_RETRY_WAIT,
                 debug=False):

        # save those parameters we will need later
        self.ip_address = ip_address
        self.port = port
        self.broadcast_address = broadcast_address if broadcast_address is not None else DEFAULT_BROADCAST_ADDRESS
        self.broadcast_port = broadcast_port if broadcast_port is not None else DEFAULT_BROADCAST_PORT
        self.socket_timeout = socket_timeout if socket_timeout is not None else DEFAULT_SOCKET_TIMEOUT
        self.broadcast_timeout = broadcast_timeout if broadcast_timeout is not None else DEFAULT_BROADCAST_TIMEOUT
        self.max_tries = max_tries
        self.retry_wait = retry_wait
        self.debug = debug

        # start off logging failures
        self.log_failures = True

    def discover(self):
        """Discover any devices on the local network.

        Send a UDP broadcast and check for replies. Decode each reply to obtain
        details of any devices on the local network. Create a dict of details
        for each device including a derived model name. Construct a list of
        dicts with details of each unique (ie each unique MAC address) device
        that responded. When complete return the list of devices found.
        """

        # create a socket object so we can broadcast to the network via
        # IPv4 UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # set socket datagram to broadcast
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # set timeout
        s.settimeout(self.broadcast_timeout)
        # set TTL to 1 to so messages do not go past the local network
        # segment
        ttl = struct.pack('b', 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        # construct the packet to broadcast
        packet = self.build_cmd_packet('CMD_BROADCAST')
        # if required display the packet we are sending
        if self.debug:
            print()
            print(f"sending broadcast packet '{pretty_bytes_as_hex(packet)['hex']}' "
                  f"to {self.broadcast_address}:{self.broadcast_port}")
        # initialise a list for the results as multiple devices may respond
        result_list = []
        # send the Broadcast command
        s.sendto(packet, (self.broadcast_address, self.broadcast_port))
        # obtain any responses
        while True:
            try:
                response = s.recv(1024)
                # if required display the response packet
                if self.debug:
                    _first_row = True
                    for row in gen_pretty_bytes_as_hex(response):
                        if _first_row:
                            print()
                            print(f"Received broadcast response: {row['hex']}")
                            _first_row = False
                        else:
                            print(f"                             {row['hex']}")
                        print(f"                             {row['printable']}")
            except socket.timeout:
                # if we time out then we are done with this attempt
                break
            except socket.error:
                # raise any other socket error
                raise
            # check the response is valid
            try:
                self.check_response(response, self.api_commands['CMD_BROADCAST'])
            except InvalidChecksum as e:
                # the response was not valid, log it and attempt again
                # if we haven't had too many attempts already
                if self.debug:
                    print(f"Invalid response to command 'CMD_BROADCAST': {e}")
            except UnknownApiCommand:
                # most likely we have encountered a device that does
                # not understand the command, possibly due to an old or
                # outdated firmware version, raise the exception for
                # our caller to deal with
                raise
            except Exception as e:
                # Some other error occurred in check_response(),
                # perhaps the response was malformed. Log the stack
                # trace but continue.
                raise
            else:
                # we have a valid response so decode the response
                # and obtain a dict of device data
                device = self.decode_broadcast_response(response)
                # if we haven't seen this MAC before attempt to obtain
                # and save the device model then add the device to our
                # results list
                if not any((d['mac'] == device['mac']) for d in result_list):
                    # determine the device model based on the device
                    # SSID and add the model to the device dict
                    device['model'] = self.get_model_from_ssid(device.get('ssid'))
                    # append the device to our list
                    result_list.append(device)
        # close our socket
        s.close()
        # now return our results
        return result_list

    @staticmethod
    def decode_broadcast_response(raw_data):
        """Decode a broadcast response and return the results as a dict.

        A device response to a CMD_BROADCAST API command consists of a
        number of control structures around a payload of a data. The API
        response is structured as follows:

        bytes 0-1 incl                  preamble, literal 0xFF 0xFF
        byte 2                          literal value 0x12
        bytes 3-4 incl                  payload size (big endian short integer)
        bytes 5-5+payload size incl     data payload (details below)
        byte 6+payload size             checksum

        The data payload is structured as follows:

        bytes 0-5 incl      device MAC address
        bytes 6-9 incl      device IP address
        bytes 10-11 incl    device port number
        bytes 11-           device AP SSID

        Note: The device AP SSID for a given device is fixed in size but
        this size can vary from device to device and across firmware
        versions.

        There also seems to be a peculiarity in the CMD_BROADCAST response
        data payload whereby the first character of the device AP SSID is a
        non-printable ASCII character. The WSView app appears to ignore or
        not display this character nor does it appear to be used elsewhere.
        Consequently, this character is ignored.

        raw_data:   a bytestring containing a validated (structure and
                    checksum verified) raw data response to the
                    CMD_BROADCAST API command

        Returns a dict with decoded data keyed as follows:
            'mac':          device MAC address (string)
            'ip_address':   device IP address (string)
            'port':         device port number (integer)
            'ssid':         device AP SSID (string)
        """

        # obtain the response size, it's a big endian short (two byte)
        # integer
        resp_size = struct.unpack('>H', raw_data[3:5])[0]
        # now extract the actual data payload
        data = raw_data[5:resp_size + 2]
        # initialise a dict to hold our result
        data_dict = {}
        # extract and decode the MAC address
        data_dict['mac'] = bytes_to_hex(data[0:6], separator=":")
        # extract and decode the IP address
        data_dict['ip_address'] = '%d.%d.%d.%d' % struct.unpack('>BBBB',
                                                                data[6:10])
        # extract and decode the port number
        data_dict['port'] = struct.unpack('>H', data[10: 12])[0]
        # get the SSID as a bytestring
        ssid_b = data[13:]
        # create a format string so the SSID string can be unpacked into its
        # bytes, remember the length can vary
        ssid_format = "B" * len(ssid_b)
        # unpack the SSID bytestring, we now have a tuple of integers
        # representing each of the bytes
        ssid_t = struct.unpack(ssid_format, ssid_b)
        # convert the sequence of bytes to unicode characters and assemble
        # as a string and return the result
        data_dict['ssid'] = "".join([chr(x) for x in ssid_t])
        # return the result dict
        return data_dict

    def get_model_from_firmware(self, firmware_string):
        """Determine the device model from the firmware version.

        To date device firmware versions have included the device model in
        the firmware version string returned via the device API. Whilst
        this is not guaranteed to be the case for future firmware releases,
        in the absence of any other direct means of obtaining the device
        model number it is a useful means for determining the device model.

        The check is a simple check to see if the model name is contained
        in the firmware version string returned by the device API.

        If a known model is found in the firmware version string the model
        is returned as a string. None is returned if (1) the firmware
        string is None or (2) a known model is not found in the firmware
        version string.
        """

        # do we have a firmware string
        if firmware_string is not None:
            # we have a firmware string so look for a known model in the
            # string and return the result
            return self.get_model_from_string(firmware_string)
        # for some reason we have no firmware string, so return None
        return None

    def get_model_from_ssid(self, ssid_string):
        """Determine the device model from the device SSID.

        To date the device SSID has included the device model in the SSID
        returned via the device API. Whilst this is not guaranteed to be
        the case for future firmware releases, in the absence of any other
        direct means of obtaining the device model number it is a useful
        means for determining the device model. This is particularly the
        case when using UDP broadcast to discover devices on the local
        network.

        Note that it may be possible to alter the SSID used by the device
        in which case this method may not provide an accurate result.
        However, as the device SSID is only used during initial device
        configuration and since altering the device SSID is not a normal
        part of the initial device configuration, this method of
        determining the device model is considered adequate for use during
        discovery by UDP broadcast.

        The check is a simple check to see if the model name is contained
        in the SSID returned by the device API.

        If a known model is found in the SSID the model is returned as a
        string. None is returned if (1) the SSID is None or (2) a known
        model is not found in the SSID.
        """

        return self.get_model_from_string(ssid_string)

    def get_model_from_string(self, t):
        """Determine the device model from a string.

        To date firmware versions have included the device model in the
        firmware version string or the device SSID. Both the firmware
        version string and device SSID are available via the device API so
        checking the firmware version string or SSID provides a de facto
        method of determining the device model.

        This method uses a simple check to see if a known model name is
        contained in the string concerned.

        Known model strings are contained in a tuple Station.known_models.

        If a known model is found in the string the model is returned as a
        string. None is returned if a known model is not found in the
        string.
        """

        # do we have a string to check
        if t is not None:
            # we have a string, now do we have a know model in the string,
            # if so return the model string
            for model in self.known_models:
                if model in t.upper():
                    return model
            # we don't have a known model so take an educated guess by
            # splitting the string on '-' or '_' and taking the first
            # sub-string
            if '_' in t:
                return ' '.join(['(possible)', t.split('_')[0]])
            if '-' in t:
                return ' '.join(['(possible)', t.split('-')[0]])
            # we are out of options, return 'unknown model'
            return '(unknown model)'
        # we have no string so return None
        return None

    def get_livedata(self):
        """Get live data.

        Sends the API command to the device to obtain live data. If the device
        cannot be contacted or the data is invalid the value None will be
        returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_GW1000_LIVEDATA')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned short in bytes 3 and 4
        packet_length = struct.unpack(">H", _response[3:5])[0]
        # return the data payload
        return _response[5:5 + packet_length - 4]

    def get_raindata(self):
        """Get traditional gauge rain data.

        Sends the API command to obtain traditional gauge rain data from the
        device. If the device cannot be contacted or the data is invalid the
        value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_RAINDATA')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_ssss(self):
        """Read system parameters.

        Sends the API command to obtain system parameters from the device. If
        the device cannot be contacted or the data is invalid the value None
        will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_SSSS')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_ecowitt(self):
        """Get Ecowitt.net parameters.

        Sends the API command to obtain the device Ecowitt.net parameters. If
        the device cannot be contacted or the data is invalid the value None
        will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_ECOWITT')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_wunderground(self):
        """Get Weather Underground parameters.

        Sends the API command to obtain the device Weather Underground
        parameters. If the device cannot be contacted or the data is invalid
        the value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_WUNDERGROUND')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_weathercloud(self):
        """Get Weathercloud parameters.

        Sends the API command to obtain the device Weathercloud parameters. If
        the device cannot be contacted or the data is invalid the value None
        will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_WEATHERCLOUD')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_wow(self):
        """Get Weather Observations Website parameters.

        Sends the API command to obtain the device Weather Observations
        Website parameters. If the device cannot be contacted or the data is
        invalid the value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_WOW')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_customized(self):
        """Get custom server parameters.

        Sends the API command to obtain the device custom server parameters.
        If the device cannot be contacted or the  data is invalid the value
        None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_CUSTOMIZED')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_usr_path(self):
        """Get user defined custom path.

        Sends the API command to obtain the device user defined custom path
        data. If the device cannot be contacted or the data is invalid the
        value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_USR_PATH')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_station_mac(self):
        """Get device MAC address.

        Sends the API command to obtain the device MAC address. If the device
        cannot be contacted or the data is invalid the value None will be
        returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_STATION_MAC')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_firmware_version(self):
        """Get device firmware version.

        Sends the API command to obtain device firmware version. If the device
        cannot be contacted or the data is invalid the value None will be
        returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_FIRMWARE_VERSION')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an integer in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_sensor_id_new(self):
        # TODO. Need to ensure consumer of this method know its now the data payload
        """Get sensor ID data.

        Sends the API command to obtain sensor ID data from the device. If the device cannot be contacted or the offset data is
        invalid the value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_SENSOR_ID_NEW')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned short in bytes 3 and 4
        packet_length = struct.unpack(">H", _response[3:5])[0]
        # return the data payload
        return _response[5:5 + packet_length - 4]

    def get_mulch_offset(self):
        """Get multichannel temperature and humidity offset data.

        Sends the API command to obtain the multichannel temperature and
        humidity offset data. If the device cannot be contacted or the data is
        invalid the value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_GET_MulCH_OFFSET')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned byte in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_mulch_t_offset(self):
        """Get multichannel temperature (WN34) offset data.

        Sends the API command to obtain the multichannel temperature (WN34)
        offset data. If the device cannot be contacted or the data is invalid
        the value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_GET_MulCH_T_OFFSET')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned short in bytes 3 and 4
        packet_length = struct.unpack(">H", _response[3:5])[0]
        # return the data payload
        return _response[5:5 + packet_length - 4]

    def get_pm25_offset(self):
        """Get PM2.5 offset data.

        Sends the API command to obtain the PM2.5 sensor offset data.
        If the device cannot be contacted or the data is invalid the value None
        will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_GET_PM25_OFFSET')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned byte in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_gain(self):
        """Get calibration coefficient data.

        Sends the API command to obtain the calibration coefficient data. If
        the device cannot be contacted or the data is invalid the value None
        will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_GAIN')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned byte in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_soil_humiad(self):
        """Get soil moisture sensor calibration data.

        Sends the API command to obtain the soil moisture sensor calibration
        data. If the device cannot be contacted or the data is invalid the
        value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_GET_SOILHUMIAD')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned byte in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_calibration(self):
        """Get offset calibration data.

        Sends the API command to obtain the offset calibration data. If the
        device cannot be contacted or the data is invalid the value None will
        be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_CALIBRATION')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned byte in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_co2_offset(self):
        """Get WH45 CO2, PM10 and PM2.5 offset data.

        Sends the API command to obtain the WH45 CO2, PM10 and PM2.5 sensor
        offset data. If the device cannot be contacted or the data is invalid
        the value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_GET_CO2_OFFSET')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned byte in byte 3
        packet_length = _response[3]
        # return the data payload
        return _response[4:packet_length + 1]

    def get_rain(self):
        """Get traditional gauge and piezo gauge rain data.

        Sends the API command to obtain the traditional gauge and piezo gauge
        rain data. If the device cannot be contacted or the data is invalid the
        value None will be returned.

        Returns the API response data payload as a bytestring or None if a
        valid response was not obtained.
        """

        # obtain the API response, if the response is non-None it has been
        # already been validated
        try:
            _response = self.send_cmd_with_retries('CMD_READ_RAIN')
        except (GWIOError, InvalidChecksum) as e:
            return None
        # get the packet length, it is an unsigned short in bytes 3 and 4
        packet_length = struct.unpack(">H", _response[3:5])[0]
        # return the data payload
        return _response[5:5 + packet_length - 4]

    def set_ecowitt(self, payload):
        """Set the Ecowitt.net upload parameters.

        Sends the API command to write the Ecowitt.net upload parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        set_ecowitt(). If the command failed a DeviceWriteFailed exception is
        raised. Any code calling set_ecowitt() should be prepared to handle
        these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_ECOWITT', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_wu(self, payload):
        """Set the WeatherUnderground upload parameters.

        Sends the API command to write the WeatherUnderground upload parameters
        to the gateway device. If the device cannot be contacted a GWIOError
        will be raised by send_cmd_with_retries() which will be passed through
        by set_wu(). If the command failed a DeviceWriteFailed exception is
        raised. Any code calling set_wu() should be prepared to handle these
        exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_WUNDERGROUND', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_wcloud(self, payload):
        """Set the Weathercloud upload parameters.

        Sends the API command to write the Weathercloud upload parameters to
        the gateway device. If the device cannot be contacted a GWIOError will
        be raised by send_cmd_with_retries() which will be passed through by
        set_wcloud(). If the command failed a DeviceWriteFailed exception is
        raised. Any code calling set_wcloud() should be prepared to handle these
        exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_WEATHERCLOUD', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_wow(self, payload):
        """Set the Weather Observations Website upload parameters.

        Sends the API command to write the Weather Observations Website upload
        parameters to the gateway device. If the device cannot be contacted a
        GWIOError will be raised by send_cmd_with_retries() which will be
        passed through by set_wow(). If the command failed a DeviceWriteFailed
        exception is raised. Any code calling set_wow() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_WOW', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_custom(self, payload):
        """Set the Weather Observations Website upload parameters.

        Sends the API command to write the Weather Observations Website upload
        parameters to the gateway device. If the device cannot be contacted a
        GWIOError will be raised by send_cmd_with_retries() which will be
        passed through by set_wow(). If the command failed a DeviceWriteFailed
        exception is raised. Any code calling set_wow() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_CUSTOMIZED', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_custom_paths(self, payload):
        """Set the 'Custom' upload path parameters.

        Sends the API command to write the Weather Observations Website upload
        parameters to the gateway device. If the device cannot be contacted a
        GWIOError will be raised by send_cmd_with_retries() which will be
        passed through by set_wow(). If the command failed a DeviceWriteFailed
        exception is raised. Any code calling set_wow() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_USR_PATH', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_gain(self, payload):
        """Set the gain parameters.

        Sends the API command to write the gain parameters to the gateway
        device. If the device cannot be contacted a GWIOError will be raised
        by send_cmd_with_retries() which will be passed through by set_gain().
        If the command failed a DeviceWriteFailed exception is raised. Any
        code calling set_gain() should be prepared to handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_GAIN', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_calibration(self, payload):
        """Set the calibration parameters.

        Sends the API command to write the calibration parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        set_calibration(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling set_calibration() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_CALIBRATION', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_sensor_id(self, payload):
        """Set the sensor ID parameters.

        Sends the API command to write the sensor ID parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        set_sensor_id(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling set_sensor_id() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_SENSOR_ID', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_pm25_offsets(self, payload):
        """Set the PM2.5 offsets.

        Sends the API command to write the sensor ID parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        set_sensor_id(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling set_sensor_id() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_SET_PM25_OFFSET', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def set_co2_offsets(self, payload):
        """Set the CO2 offsets.

        Sends the API command to write the sensor ID parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        set_sensor_id(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling set_sensor_id() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_SET_CO2_OFFSET', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def write_rain_params(self, payload):
        """Write the rain related parameters.

        Sends the API command to write the rain related parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        write_rain_params(). If the command failed a DeviceWriteFailed
        exception is raised. Any code calling write_rain_params() should be
        prepared to handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_RAIN', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def write_system_params(self, payload):
        """Write the system related parameters.

        Sends the API command to write the system related parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        write_system_params(). If the command failed a DeviceWriteFailed
        exception is raised. Any code calling write_system_params() should be
        prepared to handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_SSSS', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def write_rain_data(self, payload):
        """Write rain data parameters.

        Sends the API command to write the rain data parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        write_rain_data(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling write_rain_data() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_RAINDATA', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def write_mulch_th(self, payload):
        """Write rain data parameters.

        Sends the API command to write the rain data parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        write_rain_data(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling write_rain_data() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_RAINDATA', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def write_soil_moist(self, payload):
        """Write rain data parameters.

        Sends the API command to write the rain data parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        write_rain_data(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling write_rain_data() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_WRITE_RAINDATA', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def write_mulch_t(self, payload):
        """Write mulch-t parameters.

        Sends the API command to write the mulch-t offset parameters to the
        gateway device. If the device cannot be contacted a GWIOError will be
        raised by send_cmd_with_retries() which will be passed through by
        write_mulch_t(). If the command failed a DeviceWriteFailed exception
        is raised. Any code calling write_mulch_t() should be prepared to
        handle these exceptions.
        """

        # send the command and obtain the result
        result = self.send_cmd_with_retries('CMD_SET_MulCH_T_OFFSET', payload)
        # check the result to confirm the command executed successfully, if
        # unsuccessful a DeviceWriteFailed exception will be raised
        self.confirm_write_success(result)

    def send_cmd_with_retries(self, cmd, payload=b''):
        """Send an API command to the device with retries and return
        the response.

        Send a command to the device and obtain the response. If the
        response is valid return the response. If the response is invalid
        an appropriate exception is raised and the command resent up to
        self.max_tries times after which the value None is returned.

        cmd: A string containing a valid API command,
             eg: 'CMD_READ_FIRMWARE_VERSION'
        payload: The data to be sent with the API command, byte string.

        Returns the response as a byte string or the value None.
        """

        # construct the message packet
        packet = self.build_cmd_packet(cmd, payload)
        response = None
        # attempt to send up to 'self.max_tries' times
        for attempt in range(self.max_tries):
            # wrap in  try..except so we can catch any errors
            try:
                response = self.send_cmd(packet)
            except socket.timeout as e:
                # a socket timeout occurred, log it
                if self.log_failures:
                    print(f"Failed to obtain response to attempt {attempt + 1} "
                          f"to send command '{cmd}': {e}")
            except Exception as e:
                # an exception was encountered, log it
                if self.log_failures:
                    print(f"Failed attempt {attempt + 1} to send command '{cmd}': {e}")
            else:
                # check the response is valid
                try:
                    self.check_response(response, self.api_commands[cmd])
                except InvalidChecksum as e:
                    # the response was not valid, log it and attempt again
                    # if we haven't had too many attempts already
                    if self.debug:
                        print(f"Invalid response to attempt {attempt} "
                              f"to send command '{cmd}': {e}")
                except UnknownApiCommand:
                    # most likely we have encountered a device that does
                    # not understand the command, possibly due to an old or
                    # outdated firmware version, raise the exception for
                    # our caller to deal with
                    raise
                except Exception as e:
                    # Some other error occurred in check_response(),
                    # perhaps the response was malformed. Log the stack
                    # trace but continue.
                    print(f"Unexpected exception occurred while checking response "
                          f"to attempt {attempt} to send command '{cmd}': {e}")
                else:
                    # our response is valid, return it
                    return response
            # sleep before our next attempt, but skip the sleep if we
            # have just made our last attempt
            if attempt < self.max_tries - 1:
                time.sleep(self.retry_wait)
        # if we made it here we failed after self.max_tries attempts
        # first log it
        _msg = (f"Failed to obtain response to command '{cmd}' "
                f"after {self.max_tries:d} attempts")
        if response is not None or self.log_failures:
            print(_msg)
        # then finally, raise a GWIOError exception
        raise GWIOError(_msg)

    def build_cmd_packet(self, cmd, payload=b''):
        """Construct an API command packet.

        An API command packet looks like:

        fixed header, command, size, data 1, data 2...data n, checksum

        where:
            fixed header is 2 bytes = 0xFFFF
            command is a 1 byte API command code
            size is 1 byte being the number of bytes of command, size, data and
                checksum
            data 1, data 2 ... data n is the data being transmitted and is
                n bytes long, also known as the payload
            checksum is a byte checksum of command + size + data

        cmd:     A string containing a valid API command,
                   eg: 'CMD_READ_FIRMWARE_VERSION'
        payload: The data to be sent with the API command, byte string.

        Returns an API command packet as a bytestring.
        """

        # calculate size
        try:
            size = len(self.api_commands[cmd]) + 1 + len(payload) + 1
        except KeyError as e:
            raise UnknownApiCommand(f"Unknown API command '{cmd}'") from e
        # construct the portion of the message for which the checksum is calculated
        body = b''.join([self.api_commands[cmd], struct.pack('B', size), payload])
        # calculate the checksum
        checksum = self.calc_checksum(body)
        # return the constructed message packet
        return b''.join([self.header, body, struct.pack('B', checksum)])

    def send_cmd(self, packet):
        """Send a command to the API and return the response.

        Send a command to the API and return the response. Socket related
        errors are trapped and raised, code calling send_cmd should be
        prepared to handle such exceptions.

        cmd: A valid API command

        Returns the response as a byte string.
        """

        # create a socket object for sending api_commands and broadcasting to
        # the network
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # set the socket timeout
            s.settimeout(self.socket_timeout)
            # wrap our connect in a try..except, so we can catch any socket
            # related exceptions
            try:
                # connect to the device
                s.connect((self.ip_address, self.port))
                # if required display the packet we are sending
                if self.debug:
                    _first_row = True
                    for row in gen_pretty_bytes_as_hex(packet):
                        if _first_row:
                            print(f"sending packet '{row['hex']}' to {self.ip_address}:{self.port}")
                            _first_row = False
                        else:
                            print(f"               {row['hex']}")
                        print(f"               {row['printable']}")
                    print()
#                    print(f"sending packet '{pretty_bytes_as_hex(packet)['hex']}' to {self.ip_address}:{self.port}")
                # send the packet
                s.sendall(packet)
                # obtain the response, we assume here the response will be less
                # than 1024 characters
                response = s.recv(1024)
            except socket.error:
                # we received a socket error, raise it
                raise
            # if required display the response packet
            if self.debug:
                _first_row = True
                for row in gen_pretty_bytes_as_hex(response):
                    if _first_row:
                        print(f"response: {row['hex']}")
                        _first_row = False
                    else:
                        print(f"          {row['hex']}")
                    print(f"          {row['printable']}")
                print()
            # return the response
            return response

    def check_response(self, response, cmd_code):
        """Check the validity of an API response.

        Checks the validity of an API response. Two checks are performed:

        1.  the third byte of the response is the same as the command code
            used in the API call
        2.  the calculated checksum of the data in the response matches the
            checksum byte in the response

        The packet length byte (byte 3) could also be checked against the
        actual number of bytes in the packet but as the checksum is verified
        the former would be largely superfluous.

        If any check fails an appropriate exception is raised, if all checks
        pass the method exits without raising an exception.

        There are three likely scenarios:
        1. all checks pass, in which case the method returns with no value
        and no exception raised
        2. checksum check passes but command code check fails. This is most
        likely due to the device not understanding the command, possibly
        due to an old or outdated firmware version. An UnknownApiCommand
        exception is raised.
        3. checksum check fails. An InvalidChecksum exception is raised.

        response: Response received from the API call. Byte string.
        cmd_code: Command code sent to the API. Byte string of length one.
        """

        # first check the checksum is valid
        calc_checksum = self.calc_checksum(response[2:-1])
        resp_checksum = response[-1]
        if calc_checksum == resp_checksum:
            # checksum check passed, now check the response command code by
            # checkin the 3rd byte of the response matches the command code
            # that was issued
            if response[2] == cmd_code[0]:
                # we have a valid command code in the response so just return
                return
            # command code check failed, since we have a valid checksum
            # this is most likely due to the device not understanding
            # the command, possibly due to an old or outdated firmware
            # version. Raise an UnknownApiCommand exception.
            exp_int = cmd_code[0]
            resp_int = response[2]
            _msg = f"Unknown command code in API response. " \
                   f"Expected '{exp_int}' (0x{exp_int:02X}), " \
                   f"received '{resp_int}' (0x{resp_int:02X})."
            raise UnknownApiCommand(_msg)
        # checksum check failed, raise an InvalidChecksum exception
        _msg = f"Invalid checksum in API response. " \
               f"Expected '{calc_checksum}' (0x{calc_checksum:02X}), " \
               f"received '{resp_checksum}' (0x{resp_checksum:02X})."
        raise InvalidChecksum(_msg)

    @staticmethod
    def calc_checksum(data):
        """Calculate the checksum for an API call or response.

        The checksum used in an API response is simply the LSB of the sum
        of the command, size and data bytes. The fixed header and checksum
        bytes are excluded.

        data: The data on which the checksum is to be calculated. Byte
              string.

        Returns the checksum as an integer.
        """

        # initialise the checksum to 0
        checksum = 0
        # iterate over each byte in the response
        for b in data:
            # add the byte to the running total
            checksum += b
        # we are only interested in the least significant byte
        return checksum % 256

    def confirm_write_success(self, result):
        """Confirm a CMD_WRITE_xxxx command executed successfully.

        A 6 byte result is returned when a CMD_WRITE_xxxx command is executed.
        Byte 5 of this result indicates whether the command completed
        successfully or otherwise. If byte 5 == b'\x00' the command executed
        successfully, if byte 5 == b'\x01' the command failed. This function
        checks for byte 5 == b'\x00' for a successful command execution, any
        other value is taken as failure.

        If the command completed successfully nothing is done, the function
        exits/returns normally. If the command failed a DeviceWriteFailed
        exception is raised with an appropriate message.
        """

        # Check byte 5 of the response. If it is not 0x00 the command failed
        # and we should raise a DeviceWriteFailed exception with a suitable
        # message completed successfully. Use an x:y slice to ensure we obtain a
        # bytestring and not an integer.
        if result[4:5] != b'\x00':
            # the command failed, raise a DeviceWriteFailed exception with a
            # suitable message
            _msg = f"Command '{self.api_commands.inverse[result[2:3]]}' " \
                   f"({result[2:3]}) failed to write to gateway device"
            raise DeviceWriteFailed(_msg)


# ============================================================================
#                             GatewayHttp class
# ============================================================================

class HttpApi():
    """Class to interact with a gateway device via HTTP requests."""

    # HTTP request commands
    commands = ['get_version', 'get_livedata_info', 'get_ws_settings',
                'get_calibration_data', 'get_rain_totals', 'get_device_info',
                'get_sensors_info', 'get_network_info', 'get_units_info',
                'get_cli_soilad', 'get_cli_multiCh', 'get_cli_pm25',
                'get_cli_co2', 'get_piezo_rain']

    def __init__(self, ip_address, debug=0):
        """Initialise a HttpRequest object."""

        # the IP address to be used (stored as a string)
        self.ip_address = ip_address
        self.debug=debug

    def request(self, command_str, data=None, headers=None):
        """Send a HTTP request to the device and return the response.

        Create a HTTP request with optional data and headers. Send the HTTP
        request to the device as a GET request and obtain the response. The
        JSON deserialized response is returned. If the response cannot be
        deserialized the value None is returned. URL or timeout errors are
        logged and raised.

        command_str: a string containing the command to be sent,
                     eg: 'get_livedata_info'
        data: a dict containing key:value pairs representing the data to be
              sent
        headers: a dict containing headers to be included in the HTTP request

        Returns a deserialized JSON object or None
        """

        # check if we have a command that we know about
        data_dict = {} if data is None else data
        headers_dict = {} if headers is None else headers
        if command_str in HttpApi.commands:
            # first convert any data to a percent-encoded ASCII text string
            data_enc = urllib.parse.urlencode(data_dict)
            # construct the scheme and host portions of the URL
            stem = ''.join(['http://', self.ip_address])
            # now add the 'path'
            url = '/'.join([stem, command_str])
            # Finally add the encoded data. We need to add the data in this manner
            # rather than using the Request object's 'data' parameter so that the
            # request is sent as a GET request rather than a POST request.
            full_url = '?'.join([url, data_enc])
            # create a Request object
            req = urllib.request.Request(url=full_url, headers=headers_dict)
            try:
                # submit the request and obtain the raw response
                with urllib.request.urlopen(req) as w:
                    # Get charset used so we can decode the stream correctly.
                    # Unfortunately, the way to get the charset depends on whether we
                    # are running under python2 or python3. Assume python3, but be
                    # prepared to catch the error if python2.
                    try:
                        char_set = w.headers.get_content_charset()
                    except AttributeError:
                        # must be python2
                        char_set = w.headers.getparam('charset')
                    # Now get the response and decode it using the headers character
                    # set. Be prepared for charset==None.
                    if char_set is not None:
                        resp = w.read().decode(char_set)
                    else:
                        resp = w.read().decode()
                    # we are finished with the raw response so close it
            except (socket.timeout, urllib.error.URLError) as e:
                # log the error and raise it
                print("Failed to get device data")
                print("   **** %s" % e)
                raise
            # we have a response but can it be deserialized it to a python
            # object, wrap in a try..except in case it cannot be deserialized
            try:
                resp_json = json.loads(resp)
            except json.JSONDecodeError as e:
                # cannot deserialize the response, log it and return None
                print("Cannot deserialize device response")
                print("   **** %s" % e)
                return None
            # we have a deserialized response, log it as required
            if self.debug >= 3:
                print(f"Deserialized HTTP response: {json.dumps(resp_json)}")
            # now return the JSON object
            return resp_json
        # an invalid command
        raise UnknownHttpCommand(f"Unknown HTTP command '{command_str}'")

    def get_version(self):
        """Get the device firmware related information.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_version')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_livedata_info(self):
        """Get live sensor data from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_livedata_info')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_ws_settings(self):
        """Get weather services settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_ws_settings')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_calibration_data(self):
        """Get calibration settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_calibration_data')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_rain_totals(self):
        """Get rainfall totals and settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_rain_totals')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_device_info(self):
        """Get device settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_device_info')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_sensors_info(self):
        """Get sensor ID data from the device.

        Combines all pages of available data and returns a single dict or None
        if no valid data was returned by the device."""

        try:
            page_1 = self.request('get_sensors_info', data={'page': 1})
        except (urllib.error.URLError, socket.timeout):
            page_1 = None
        try:
            page_2 = self.request('get_sensors_info', data={'page': 2})
        except (urllib.error.URLError, socket.timeout):
            page_2 = None
        if page_1 is not None and page_2 is not None:
            return page_1 + page_2
        if page_1 is None:
            return page_2
        return page_1

    def get_network_info(self):
        """Get network related data/settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_network_info')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_units_info(self):
        """Get units settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_units_info')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_cli_soilad(self):
        """Get multichannel soil moisture sensor calibration data from the device.

        Returns a list of dicts or None if no valid data was returned by the
        device."""

        try:
            return self.request('get_cli_soilad')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_cli_multi_ch(self):
        """Get multichannel temperature/humidity sensor calibration data from
        the device.

        Returns a list of dicts or None if no valid data was returned by the
        device."""

        try:
            return self.request('get_cli_multiCh')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_cli_pm25(self):
        """Get PM2.5 sensor offset data from the device.

        Returns a list of dicts or None if no valid data was returned by the
        device."""

        try:
            return self.request('get_cli_pm25')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_cli_co2(self):
        """Get CO2 sensor offset data from the device.

        Returns a list of dicts or None if no valid data was returned by the
        device."""

        try:
            return self.request('get_cli_co2')
        except (urllib.error.URLError, socket.timeout):
            return None

    def get_piezo_rain(self):
        """Get piezo rain sensor data/settings from the device.

        Returns a dict or None if no valid data was returned by the device."""

        try:
            return self.request('get_piezo_rain')
        except (urllib.error.URLError, socket.timeout):
            return None


class GatewayDevice:
    """Class to interact with an Ecowitt gateway device.

    An Ecowitt gateway device can be interrogated directly in two ways:
    1. via the Ecowitt LAN/Wi-Fi Gateway API, aka the 'Gateway API'
    2. via a HTTP request, aka the 'HTTP API'

    The Gateway API uses a library of commands for read and/or set various
    gateway device parameters. Gateway API communications is socket based and
    involves exchange of data that must be encoded/decoded at the byte/bit
    level.

    The HTTP API provides the ability to read and/or set various gateway device
    parameters. HTTP API communications is via HTTP GET and involves the
    decoding/encoding of JSON format message data.

    A GatewayDevice object uses the following classes for interacting with the
    gateway device:

    - class GatewayApi.  Communicates directly with the gateway device via the
                         Gateway API and obtains and validates gateway device
                         responses.
    - class HttpApi.     Communicates directly with the gateway device via the
                         HTTP API to obtain and validate (as far as possible)
                         gateway device HTTP request responses.
    """

    # list of dicts of weather services that I know about
    services = [{'name': 'ecowitt_net_params',
                 'long_name': 'Ecowitt.net'
                 },
                {'name': 'wu_params',
                 'long_name': 'Wunderground'
                 },
                {'name': 'wcloud_params',
                 'long_name': 'Weathercloud'
                 },
                {'name': 'wow_params',
                 'long_name': 'Weather Observations Website'
                 },
                {'name': 'all_custom_params',
                 'long_name': 'Customized'
                 }
                ]

    def __init__(self, ip_address=None, port=None,
                 broadcast_address=None, broadcast_port=None,
                 socket_timeout=None, broadcast_timeout=None,
                 max_tries=DEFAULT_MAX_TRIES,
                 retry_wait=DEFAULT_RETRY_WAIT,
                 discover=False, mac=None,
                 use_wh32=True, ignore_wh40_batt=True,
                 show_battery=False, debug=False):
        """Initialise a GatewayDevice object."""

        # save our IP address and port
        self.ip_address = ip_address
        self.port = port
        # get a GatewayApi object to handle the interaction with the Gateway API
        self.gateway_api = GatewayApi(ip_address=ip_address,
                                      port=port,
                                      broadcast_address=broadcast_address,
                                      broadcast_port=broadcast_port,
                                      socket_timeout=socket_timeout,
                                      broadcast_timeout=broadcast_timeout,
                                      max_tries=max_tries,
                                      retry_wait=retry_wait,
                                      debug=debug)

        # get a Gateway API parser
        self.gateway_api_parser = GatewayApiParser()

        # get a GatewayHttp object to handle any HTTP requests, a GatewayHttp
        # object requires an IP address
        self.http_api = HttpApi(ip_address=ip_address)

        # get a Sensors object for dealing with sensor state data
        self.sensors = Sensors()

        # start off logging failures
        self.log_failures = True

    @property
    def model(self):
        """Gateway device model."""

        return self.gateway_api.get_model_from_firmware(self.firmware_version)

    @property
    def livedata(self):
        """Gateway device live data.

        Returns a dict keyed by field name and containing the device live data.
        """

        # obtain the device live data via the gateway API, the result will be a
        # bytestring or None
        payload = self.gateway_api.get_livedata()
        # return the parsed live data
        return self.gateway_api_parser.parse_livedata(payload)

    @property
    def raindata(self):
        """Gateway device traditional rain gauge data.

        Returns a dict keyed by field name and containing the device
        traditional rain gauge data.
        """

        # obtain the device traditional rain gauge data via the gateway API,
        # the result will be a bytestring or None
        payload = self.gateway_api.get_raindata()
        # return the parsed traditional rain gauge data
        return self.gateway_api_parser.parse_raindata(payload)

    @property
    def system_params(self):
        """Gateway device system parameters.

        Supports the following system parameters:

        Parameter     Description
        frequency:      sensor operating frequency
        sensor_type:    whether WH24 or WH65 is installed
        utc:            UTC time (incorrectly labelled as 'local time' in API
                        documentation)
        timezone_index: timezone index
        dst_status:     daylight saving status
        auto_timezone:  whether automatic timezone operation is in
                        enabled/disabled

        Returns a dict of system parameters.
        """

        # obtain the system parameters via the gateway API, the result will
        # be a bytestring or None
        payload = self.gateway_api.get_ssss()
        # return the parsed system parameters data
        return self.gateway_api_parser.parse_ssss(payload)

    @property
    def ecowitt_net_params(self):
        """Gateway device Ecowitt.net parameters.

        There is only one Ecowitt.net upload parameter:

        Parameter     Description
        interval      upload interval in minutes. Range 0-5, 0=off

        Returns a dict of Ecowitt.net upload parameters.
        """

        # obtain the Ecowitt.net upload parameters via the gateway API, the
        # result will be a bytestring or None
        payload = self.gateway_api.get_ecowitt()
        # parse the Ecowitt service parameter data
        _parsed_data = self.gateway_api_parser.parse_ecowitt(payload)
        # now obtain the device MAC address and add it to the Ecowitt service
        # parameter dict
        _parsed_data['mac'] = self.mac_address
        # return the Ecowitt service data
        return _parsed_data

    @property
    def wu_params(self):
        """Gateway device WeatherUnderground parameters.

        Supports the following WeatherUnderground upload parameters:

        Parameter     Description
        id            WeatherUnderground station ID
        password      WeatherUnderground password/key

        Returns a dict of WeatherUnderground upload parameters.
        """

        # obtain the WU upload parameters via the gateway API, the result will
        # be a bytestring or None
        payload = self.gateway_api.get_wunderground()
        # return the parsed WU upload data
        return self.gateway_api_parser.parse_wunderground(payload)

    @property
    def wcloud_params(self):
        """Gateway device Weathercloud parameters.

        Supports the following Weathercloud upload parameters:

        Parameter     Description
        id            Weathercloud station ID
        password      Weathercloud password/key

        Returns a dict of Weathercloud upload parameters.
        """

        # obtain the Weathercloud upload parameters via the gateway API, the
        # result will be a bytestring or None
        payload = self.gateway_api.get_weathercloud()
        # return the parsed Weathercloud upload data
        return self.gateway_api_parser.parse_weathercloud(payload)

    @property
    def wow_params(self):
        """Gateway device Weather Observations Website parameters.

        Supports the following Weathercloud upload parameters:

        Parameter     Description
        id            Weather Observations Website station ID
        password      Weather Observations Website password/key

        Returns a dict of Weather Observations Website upload parameters.
        """

        # obtain the Weather Observations Website upload parameters via the
        # gateway API, the result will be a bytestring or None
        payload = self.gateway_api.get_wow()
        # return the parsed Weather Observations Website upload data
        return self.gateway_api_parser.parse_wow(payload)

    @property
    def custom_params(self):
        """Gateway device custom server parameters.

        Returns a dict containing the following custom server upload
        parameters:

        Parameter       Description
        id:             station ID, string max 40 char
        password:       station password/key, string max 40 char
        server:         server address/name, string max 64 char
        port:           server port, integer 0-65535
        interval:       upload interval in seconds, integer 16-600
        type:           upload data format, integer 0=Ecowitt, 1=WU
        active:         whether upload is enabled/disabled, integer 0=disabled,
                        1=enabled
        """

        # obtain the customized upload parameters via the gateway API, the
        # result will be a bytestring or None
        payload = self.gateway_api.get_customized()
        # return the parsed customized upload data
        return self.gateway_api_parser.parse_customized(payload)

    @property
    def usr_path(self):
        """Gateway device user defined custom path parameters.

        Supports the following usr path parameters:

        Parameter       Description
        ecowitt_path:   Ecowitt.net path
        wu_path:        WeatherUnderground path

        Returns a dict of usr path parameters.
        """

        # obtain the usr path parameters via the gateway API, the result will
        # be a bytestring or None
        payload = self.gateway_api.get_usr_path()
        # return the parsed usr path data
        return self.gateway_api_parser.parse_usr_path(payload)

    @property
    def all_custom_params(self):
        """Gateway device custom server parameters.

        The gateway API provides access to custom server upload properties via
        two API commands; CMD_READ_CUSTOMIZED and CMD_READ_USR_PATH. The
        GatewayDevice.all_custom_params property provides the combined parsed
        data from these two API commands. This is useful when displaying the
        entire customs server upload parameters.

        The individual customized and user path parameters are available via
        the GatewayDevice.custom_params and GatewayDevice.usr_path properties
        respectively.
        """

        # obtain the parsed customized parameters
        parsed_custom_data = self.custom_params
        # return the parsed customized parameters updated with the parsed user
        # path parameters
        return parsed_custom_data.update(self.usr_path)

    @property
    def mac_address(self):
        """Gateway device MAC address."""

        payload = self.gateway_api.get_station_mac()
        # return the parsed data
        return self.gateway_api_parser.parse_station_mac(payload)

    @property
    def firmware_version(self):
        """Gateway device firmware version."""

        payload = self.gateway_api.get_firmware_version()
        # return the parsed data
        return self.gateway_api_parser.parse_firmware_version(payload)

    @property
    def sensor_id(self):
        """Gateway device sensor ID data."""

        # TODO. What should we do here?
        _data = self.gateway_api.get_sensor_id_new()
        return _data

    @property
    def mulch_offset(self):
        """Gateway device multichannel temperature and humidity offset data."""

        payload = self.gateway_api.get_mulch_offset()
        # return the parsed data
        return self.gateway_api_parser.parse_mulch_offset(payload)

    @property
    def mulch_t_offset(self):
        """Gateway device multichannel temperature (WN34) offset data."""

        payload = self.gateway_api.get_mulch_t_offset()
        # return the parsed data
        return self.gateway_api_parser.parse_mulch_t_offset(payload)

    @property
    def pm25_offset(self):
        """Gateway device PM2.5 offset data."""

        payload = self.gateway_api.get_pm25_offset()
        # return the parsed data
        return self.gateway_api_parser.parse_pm25_offset(payload)

    @property
    def calibration_coefficient(self):
        """Gateway device calibration coefficient data."""

        payload = self.gateway_api.get_gain()
        # return the parsed data
        return self.gateway_api_parser.parse_calibration(payload)

    @property
    def soil_calibration(self):
        """Gateway device soil calibration data."""

        payload = self.gateway_api.get_soil_humiad()
        # return the parsed data
        return self.gateway_api_parser.parse_soil_humiad(payload)

    # TODO. Is this method appropriately named?
    @property
    def calibration(self):
        """Gateway device calibration data.

        This is the offset calibration data from the main WSView+ calibration
        tab. It contains offset data for the major sensors. The
        GatewayDevice.gain property provides the gain calibration data for the
        major sensors on the WSView+ calibration tab. The
        GatewayDevice.offset_and_gain property provides combine offset and gain
        calibration data for the major sensors on the WSView+ calibration tab.
        """

        payload = self.gateway_api.get_calibration()
        # return the parsed data
        return self.gateway_api_parser.parse_calibration(payload)

    @property
    def co2_offset(self):
        """Gateway device CO2 offset data."""

        payload = self.gateway_api.get_co2_offset()
        # return the parsed data
        return self.gateway_api_parser.parse_co2_offset(payload)

    @property
    def rain(self):
        """Gateway device traditional gauge and piezo gauge rain data."""

        # obtain the traditional gauge and piezo gauge rain data via the
        # gateway API, the result will be a bytestring or None
        payload = self.gateway_api.get_rain()
        # return the parsed data
        return self.gateway_api_parser.parse_rain(payload)

    @property
    def sensor_state(self):
        """Sensor battery state and signal level data."""

        return self.gateway_api.get_current_sensor_state()

    @property
    def discovered_devices(self):
        """List of discovered gateway devices.

        Each list element is a dict keyed by 'ip_address', 'port', 'model',
        'mac' and 'ssid'."""

        return self.gateway_api.discover()

    @property
    def firmware_update_avail(self):
        """Whether a device firmware update is available or not.

        Return True if a device firmware update is available, False if there is
        no available firmware update or None if firmware update availability
        cannot be determined.
        """

        # get firmware version info
        version = self.http_api.get_version()
        # do we have current firmware version info and availability of a new
        # firmware version ?
        if version is not None and 'newVersion' in version:
            # we can now determine with certainty whether there is a new
            # firmware update or not
            return version['newVersion'] == '1'
        # We cannot determine the availability of a firmware update so return
        # None
        return None

    @property
    def firmware_update_message(self):
        """The device firmware update message.

        Returns the 'curr_msg' field in the 'get_device_info' response in the
        device HTTP API. This field is usually used for firmware update release
        notes.

        Returns a string containing the 'curr_msg' field contents of the
        'get_device_info' response. Return None if the 'get_device_info'
        response could not be obtained or the 'curr_msg' field was not included
        in the 'get_device_info' response.
        """

        # get device info
        device_info = self.http_api.get_device_info()
        # return the 'curr_msg' field contents or None
        return device_info.get('curr_msg') if device_info is not None else None

    @property
    def offset_and_gain(self):
        """Device combined offset and gain calibration data.

        This property mimics the data displayed on the WSView+ main calibration
        tab. It provides the offset and gain calibration data for the major
        sensors.
        """

        # obtain the calibration data via the API
        gain_data = self.gateway_api.get_gain()
        # parse the calibration data
        parsed_gain = self.gateway_api_parser.parse_gain(gain_data)
        # obtain the offset calibration data via the API
        calibration_data = self.gateway_api.get_calibration()
        # update our parsed gain data with the parsed calibration data
        parsed_gain.update(self.gateway_api_parser.parse_calibration(calibration_data))
        # return the combined parsed data
        return parsed_gain

    @property
    def ws90_firmware_version(self):
        """Provide the WH90 firmware version.

        Return the WS90 installed firmware version. If no WS90 is available the
        value None is returned.
        """

        sensors = self.http_api.get_sensors_info()
        if sensors is not None:
            for sensor in sensors:
                if sensor.get('img') == 'wh90':
                    return sensor.get('version', 'not available')
        return None

    def write_ecowitt(self, **ecowitt):
        """Write Ecowitt.net upload parameters.

        Write Ecowitt.net upload parameters to a gateway device. The only
        Ecowitt.net parameter is the upload interval. The upload parameter is
        first encoded to produce the command data payload. The payload is then
        passed to a GatewayApi object for uploading to the gateway device.
        """

        # encode the payload parameters to produce the data payload
        payload = self.gateway_api_parser.encode_ecowitt(**ecowitt)
        # update the gateway device
        self.gateway_api.set_ecowitt(payload)

    def write_wu(self, **wu):
        """Write WeatherUnderground upload parameters.

        Write WeatherUnderground upload parameters to a gateway device. The
        WeatherUnderground parameters consist of station ID and station key.
        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # encode the payload parameters to produce the data payload
        payload = self.gateway_api_parser.encode_wu(**wu)
        # update the gateway device
        self.gateway_api.set_wu(payload)

    def write_wcloud(self, **wcloud):
        """Write Weathercloud upload parameters.

        Write Weathercloud upload parameters to a gateway device. The
        Weathercloud parameters consist of station ID and station key. The
        upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # encode the payload parameters to produce the data payload
        payload = self.gateway_api_parser.encode_wcloud(**wcloud)
        # update the gateway device
        self.gateway_api.set_wcloud(payload)

    def write_wow(self, **wow):
        """Write Weather Observations Website upload parameters.

        Write Weather Observations Website upload parameters to a gateway
        device. The Weather Observations Website parameters consist of station
        ID and station key. The upload parameters are first encoded to produce
        the command data payload. The payload is then passed to a GatewayApi
        object for uploading to the gateway device.
        """

        # encode the payload parameters to produce the data payload
        payload = self.gateway_api_parser.encode_wow(**wow)
        # update the gateway device
        self.gateway_api.set_wow(payload)

    def write_custom(self, **custom):
        #TODO. Need comments here to expand on dual-update
        """Write 'Custom' upload parameters.

        Write 'Custom' upload parameters to a gateway device. The 'Custom'
        parameters consist of:

        active:     whether the custom upload is active, 0 = inactive,
                    1 = active
        type:       what protocol (Ecwoitt or WeatherUnderground) to use for
                    upload, 0 = Ecowitt, 1 = WeatherUnderground
        server:     server IP address or host name, string
        port:       server port number, integer 0 to 65536
        interval:   upload interval in seconds
        id:         WeatherUnderground station ID
        password:   WeatherUnderground key

        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payloads for each API command
        payload_custom = self.gateway_api_parser.encode_customized(**custom)
        payload_paths = self.gateway_api_parser.encode_usr_path(**custom)
        # update the gateway device
        self.gateway_api.set_custom(payload_custom)
        self.gateway_api.set_custom_paths(payload_paths)

    def write_gain(self, **gain):
        #TODO. Need to update these comments
        """Write gain parameters.

        Write gain parameters to a gateway device. The gain parameters consist
        of:

        active:     whether the custom upload is active, 0 = inactive,
                    1 = active
        type:       what protocol (Ecowitt or WeatherUnderground) to use for
                    upload, 0 = Ecowitt, 1 = WeatherUnderground
        server:     server IP address or host name, string
        port:       server port number, integer 0 to 65536
        interval:   upload interval in seconds
        id:         WeatherUnderground station ID
        password:   WeatherUnderground key

        The gain parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payloads for the API command
        payload = self.gateway_api_parser.encode_gain(**gain)
        # update the gateway device
        self.gateway_api.set_gain(payload)

    def write_calibration(self, **calibration):
        #TODO. Need to update these comments
        """Write calibration parameters.

        Write calibration parameters to a gateway device. The calibration
        parameters consist of:

        intemp: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The calibration parameters are first encoded to produce the command
        data payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payloads for the API command
        payload = self.gateway_api_parser.encode_calibration(**calibration)
        # update the gateway device
        self.gateway_api.set_calibration(payload)

    def write_sensor_id(self, **id):
        """Write sensor ID parameters.

        Write sensor ID parameters to a gateway device. The sensor ID
        parameters consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The sensor ID parameters are first encoded to produce the command
        data payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payloads for the API command
        payload = self.gateway_api_parser.encode_sensor_id(**id)
        # update the gateway device
        self.gateway_api.set_sensor_id(payload)

    def write_pm25_offsets(self, **offsets):
        """Write PM2.5 offsets.

        Write sensor ID parameters to a gateway device. The sensor ID
        parameters consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The sensor ID parameters are first encoded to produce the command
        data payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payloads for the API command
        payload = self.gateway_api_parser.encode_pm25_offsets(**offsets)
        # update the gateway device
        self.gateway_api.set_pm25_offsets(payload)

    def write_co2_offsets(self, **offsets):
        """Write CO2 offsets.

        Write sensor ID parameters to a gateway device. The sensor ID
        parameters consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The sensor ID parameters are first encoded to produce the command
        data payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payloads for the API command
        payload = self.gateway_api_parser.encode_co2_offsets(**offsets)
        # update the gateway device
        self.gateway_api.set_co2_offsets(payload)

    def write_rain(self, **params):
        """Write rain parameters.

        Write rain parameters to a gateway device. The rain parameters consist
        of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The rain parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # obtain encoded data payload for the API command
        payload = self.gateway_api_parser.encode_rain_params(**params)
        # update the gateway device
        self.gateway_api.write_rain_params(payload)

    def write_system_params(self, **params):
        """Write system parameters.

        Write system parameters to a gateway device. The system parameters
        consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The parameters are first encoded to produce the command data payload.
        The payload is then passed to a GatewayApi object for uploading to the
        gateway device.
        """

        # obtain encoded data payload for the API command
        payload = self.gateway_api_parser.encode_system_params(**params)
        # update the gateway device
        self.gateway_api.write_system_params(payload)

    def write_rain_data(self, **params):
        """Write rain data parameters.

        Write system parameters to a gateway device. The system parameters
        consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The parameters are first encoded to produce the command data payload.
        The payload is then passed to a GatewayApi object for uploading to the
        gateway device.
        """

        # obtain encoded data payload for the API command
        payload = self.gateway_api_parser.encode_rain_data(**params)
        # update the gateway device
        self.gateway_api.write_rain_data(payload)

    def write_mulch_th(self, **params):
        """Write rain data parameters.

        Write system parameters to a gateway device. The system parameters
        consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The parameters are first encoded to produce the command data payload.
        The payload is then passed to a GatewayApi object for uploading to the
        gateway device.
        """

        # obtain encoded data payload for the API command
        payload = self.gateway_api_parser.encode_rain_data(**params)
        # update the gateway device
        self.gateway_api.write_rain_data(payload)

    def write_soil_moist(self, **params):
        """Write rain data parameters.

        Write system parameters to a gateway device. The system parameters
        consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The parameters are first encoded to produce the command data payload.
        The payload is then passed to a GatewayApi object for uploading to the
        gateway device.
        """

        # obtain encoded data payload for the API command
        payload = self.gateway_api_parser.encode_rain_data(**params)
        # update the gateway device
        self.gateway_api.write_rain_data(payload)

    def write_mulch_t(self, **params):
        """Write mulch-t offset parameters.

        Write mulch-t offset parameters to a gateway device. The mulch-t offset
        parameters consist of:

        wh65: inside temperature offset, float -10.0 - +10.0 °C
        inhum:  inside humidity offset, integer -10 - +10 %
        abs:    absolute pressure offset, float -80.0 - +80.0 hPa
        rel:    relative pressure offset, float -80.0 - +80.0 hPa
        outemp: outside temperature offset, float -10.0 - +10.0 °C
        outhum: outside humidity offset, integer -10 - +10 %
        winddir: wind direction offset, integer -180 - +180 °

        The parameters are first encoded to produce the command data payload.
        The payload is then passed to a GatewayApi object for uploading to the
        gateway device.
        """

        # obtain encoded data payload for the API command
        payload = self.gateway_api_parser.encode_mulch_t(**params)
        # update the gateway device
        self.gateway_api.write_mulch_t(payload)

    def update_sensor_id_data(self):
        """Update the Sensors object with current sensor ID data."""

        # first get the current sensor ID data
        # TODO. This should return a value
        sensor_id_data = self.gateway_api.get_sensor_id_new()
        # now use the sensor ID data to re-initialise our sensors object
        self.sensors.set_sensor_id_data(sensor_id_data)


# ============================================================================
#                             Utility functions
# ============================================================================

def natural_sort_keys(source_dict):
    """Return a naturally sorted list of keys for a dict."""

    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        """Natural key sort.

        Allows use of key=natural_keys to sort a list in human order, eg:
            alist.sort(key=natural_keys)

        https://nedbatchelder.com/blog/200712/human_sorting.html (See
        Toothy's implementation in the comments)
        """

        return [atoi(c) for c in re.split(r'(\d+)', text.lower())]

    # create a list of keys in the dict
    keys_list = list(source_dict.keys())
    # naturally sort the list of keys where, for example, xxxxx16 appears in the
    # correct order
    keys_list.sort(key=natural_keys)
    # return the sorted list
    return keys_list


def natural_sort_dict(source_dict):
    """Return a string representation of a dict sorted naturally by key.

    When represented as a string a dict is displayed in the format:
        {key a:value a, key b: value b ... key z: value z}
    but the order of the key:value pairs is unlikely to be alphabetical.
    Displaying dicts of key:value pairs in logs or on the console in
    alphabetical order by key assists in the analysis of the dict data.
    Where keys are strings with leading digits a natural sort is useful.
    """

    # first obtain a list of key:value pairs as string sorted naturally by key
    sorted_dict_fields = [f"'{k}': '{source_dict[k]}'" for k in natural_sort_keys(source_dict)]
    # return as a string of comma separated key:value pairs in braces
    return f'{{{", ".join(sorted_dict_fields)}}}'


def bytes_to_hex(iterable, separator=' ', caps=True):
    """Produce a hex string representation of a sequence of bytes."""

    # assume 'iterable' can be iterated by iterbytes and the individual
    # elements can be formatted with {:02X}
    format_str = "{:02X}" if caps else "{:02x}"
    # TODO. Need to verify use of iterable and str.encode(iterable) do what we want
    try:
        return separator.join(format_str.format(c) for c in iterable)
    except ValueError:
        # most likely we are running python3 and iterable is not a bytestring,
        # try again coercing iterable to a bytestring
        return separator.join(format_str.format(c) for c in str.encode(iterable))
    except (TypeError, AttributeError):
        # TypeError - 'iterable' is not iterable
        # AttributeError - likely because separator is None
        # either way we can't represent as a string of hex bytes
        return f"cannot represent '{iterable}' as hexadecimal bytes"


def bytes_to_printable(raw_bytes):

    def byte_to_printable(b):
        s = chr(b)
        if s.isprintable() and s.isascii():
            return f"{s:>2}"
        return "  "

    return ' '.join(map(byte_to_printable, raw_bytes))


def pretty_bytes_as_hex(raw_bytes, columns=20, start_column=3):
    """Pretty print a byte string.

    Print a sequence of bytes as a sequence of space separated hexadecimal
    digit pairs with 'column' digit pairs per line. ASCII printable equivalents
    of each hexadecimal digit pair is printed under each hexadecimal digit
    pair. If there is no printable ASCII equivalent nothing is printed for that
    digit pair. Each line is indented with the first character printed in
    column 'start_column' (ie start_column - 1 spaces are printed at the start
    of each line). If 'label' is specified 'label' is printed without indent on
    the line preceding the hexadecimal data.
    """

    # do we have any bytes to print
    if len(raw_bytes) > 0:
        return {'hex': f"{bytes_to_hex(raw_bytes)}",
                'printable': f"{bytes_to_printable(raw_bytes)}"
                }
    else:
        return {'hex': '', 'printable': ''}


def gen_pretty_bytes_as_hex(raw_bytes, columns=20, start_column=3):
    """Pretty print a byte string.

    Print a sequence of bytes as a sequence of space separated hexadecimal
    digit pairs with 'column' digit pairs per line. ASCII printable equivalents
    of each hexadecimal digit pair is printed under each hexadecimal digit
    pair. If there is no printable ASCII equivalent nothing is printed for that
    digit pair. Each line is indented with the first character printed in
    column 'start_column' (ie start_column - 1 spaces are printed at the start
    of each line). If 'label' is specified 'label' is printed without indent on
    the line preceding the hexadecimal data.
    """

    # do we have any bytes to print
    if len(raw_bytes) > 0:
        # we have bytes to print
        # set an index to 0
        index = 0
        # iterate over the sequence of bytes
        while index < len(raw_bytes):
            # grab 'columns' bytes at a time
            if len(raw_bytes) >= index + columns:
                row_bytes = raw_bytes[index:index + columns]
            else:
                row_bytes = raw_bytes[index:]
            # print the grabbed bytes as a space separated sequence of
            # hexadecimal digit pairs
            yield {'hex': f"{' ' * (start_column - 1)}{bytes_to_hex(row_bytes)}",
                  'printable': f"{' ' * (start_column - 1)}{bytes_to_printable(row_bytes)}"}
            # increment our index to grab the next group of bytes
            index += columns


def obfuscate(plain, obf_char='*'):
    """Obfuscate all but the last x characters in a string.

    Obfuscate all but (at most) the last four characters of a string. Always
    reveal no more than 50% of the characters. The obfuscation character
    defaults to '*' but can be set when the function is called.
    """

    if plain is not None and len(plain) > 0:
        # obtain the number of the characters to be retained
        stem = 4
        stem = 3 if len(plain) < 8 else stem
        stem = 2 if len(plain) < 6 else stem
        stem = 1 if len(plain) < 4 else stem
        stem = 0 if len(plain) < 3 else stem
        if stem > 0:
            # we are retaining some characters so do a little string
            # manipulation
            obfuscated = obf_char * (len(plain) - stem) + plain[-stem:]
        else:
            # we are obfuscating everything
            obfuscated = obf_char * len(plain)
        return obfuscated
    # if we received None or a zero length string then return it
    return plain


# ============================================================================
#                             class DirectGateway
# ============================================================================

class DirectGateway:
    """Class to interact with gateway driver when run directly.

    Would normally run a driver directly by calling from main() only, but when
    run directly the gateway driver has many options so pushing the detail into
    its own class/object makes sense. Also simplifies some test suite
    routines/calls.

    A DirectGateway object is created with just an optparse options dict and a
    standard WeeWX station dict. Once created the DirectGateway()
    process_options() method is called to process the respective command line
    options.
    """

    # list of sensors to be displayed in the sensor ID output
    sensors_list = []

    def __init__(self, namespace):
        """Initialise a DirectGateway object."""

        # save the optparse options and station dict
        self.namespace = namespace
        # save the IP address and port number to use
        self.ip_address = getattr(namespace, 'device_ip_address', None)
        self.port = getattr(namespace, 'device_port', None)
        # do we filter battery state data
        self.show_battery = getattr(namespace, 'show_battery', None)
        # set our debug level
        self.debug = namespace.debug

    def display_system_params(self):
        """Display system parameters.

        Obtain and display the gateway device system parameters.
        """

        # dict for decoding system parameters frequency byte
        freq_decode = {
            0: '433MHz',
            1: '868Mhz',
            2: '915MHz',
            3: '920MHz'
        }
        temperature_comp_decode = {
            0: 'off',
            1: 'on'
        }
        auto_tz_decode = {
            0: 'enabled (auto)',
            1: 'disabled (manual)'
        }
        dst_decode = {
            0: 'disabled (manual update)',
            1: 'enabled (automatic update)'
        }
        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f"Unable to connect to device at {self.ip_address}: {e}")
            return
        except socket.timeout:
            print()
            print(f"Timeout. Device at {self.ip_address} did not respond.")
            return
        # identify the device being used
        print()
        print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        # get the device display_system_params property
        sys_params_dict = device.system_params
        # we need the radiation compensation setting which, according to
        # the v1.6.9 API documentation, resides in field 7B. But bizarrely
        # this is only available via the CMD_READ_RAIN API command.
        # CMD_READ_RAIN is a relatively new command so wrap in a
        # try..except just in case.
        try:
            _rain_data = device.rain
        except GWIOError:
            temperature_comp = None
        else:
            temperature_comp = _rain_data.get('ITEM_radcompensation')
        # create a meaningful string for frequency representation
        freq_str = freq_decode.get(sys_params_dict['frequency'], 'Unknown')
        # if sensor_type is 0 there is a WH24 connected, if it's a 1 there
        # is a WH65
        _is_wh24 = sys_params_dict['sensor_type'] == 0
        # string to use in sensor type message
        _sensor_type_str = 'WH24' if _is_wh24 else 'WH65'
        # print the system parameters
        print()
        print(f'{"sensor type":>28}: {sys_params_dict["sensor_type"]} ({_sensor_type_str})')
        print(f'{"frequency":>28}: {sys_params_dict["frequency"]} ({freq_str})')
        if temperature_comp is not None:
            print(f'{"Temperature Compensation":>28}: {temperature_comp} '
                  f'({temperature_comp_decode.get(temperature_comp, "unknown")})')
        else:
            print(f'{"Temperature Compensation":>28}: unavailable')
        print(f'{"Auto Timezone":>28}: {auto_tz_decode[sys_params_dict["auto_timezone"]]}')
        print(f'{"timezone index":>28}: {sys_params_dict["timezone_index"]}')
        # The gateway API returns what is labelled "UTC" but is in fact the
        # current epoch timestamp adjusted by the station timezone offset.
        # So when the timestamp is converted to a human-readable GMT
        # date-time string it in fact shows the local date-time. We can
        # work around this by formatting this offset UTC time stamp as a
        # UTC date-time but then calling it local time. ideally we would
        # re-adjust to remove the timezone offset to get the real
        # (unadjusted) epoch timestamp but since the timezone index is
        # stored as an arbitrary number rather than an offset in seconds
        # this is not possible. We can only do what we can.
        date_time_str = time.strftime("%-d %B %Y %H:%M:%S",
                                      time.gmtime(sys_params_dict['utc']))
        print(f'{"date-time":>28}: {date_time_str}')
        print(f'{"Automatically adjust for DST":>28}: '
              f'{dst_decode.get(sys_params_dict["dst_status"], "unknown")}')

    def display_rain_data(self):
        """Display the device rain data.

        Obtain and display the device rain data. The device IP address and port
        are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the device objects raindata property
            rain_data = device.raindata
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            print()
            print(f'{"Rain rate":>10}: {rain_data["t_rainrate"]:.1f} mm/{rain_data["t_rainrate"] / 25.4:.1f} in')
            print(f'{"Day rain":>10}: {rain_data["t_rainday"]:.1f} mm/{rain_data["t_rainday"] / 25.4:.1f} in')
            print(f'{"Week rain":>10}: {rain_data["t_rainweek"]:.1f} mm/{rain_data["t_rainweek"] / 25.4:.1f} in')
            print(f'{"Month rain":>10}: {rain_data["t_rainmonth"]:.1f} mm/{rain_data["t_rainmonth"] / 25.4:.1f} in')
            print(f'{"Year rain":>10}: {rain_data["t_rainyear"]:.1f} mm/{rain_data["t_rainyear"] / 25.4:.1f} in')

    def display_all_rain_data(self):
        """Display the device rain data including piezo data.

        Obtain and display the device rain data including piezo data. The
        CMD_READ_RAIN API command is used to obtain the device data, this
        command returns rain data from the device for both traditional and
        piezo rain gauges.

        The device address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery

        Note. Early testing showed the CMD_READ_RAIN command returned data for
        the piezo gauge only. This may be due to the system under test (it only
        had a piezo rain gauge) or it may be an issue with the v2.1.3 device
        firmware.
        """

        traditional = ['t_rainrate', 't_rainevent', 't_rainday',
                       't_rainweek', 't_rainmonth', 't_rainyear']
        piezo = ['p_rainrate', 'p_event', 'p_day', 'p_week', 'p_month', 'p_year',
                 'gain1', 'gain2', 'gain3', 'gain4', 'gain5']
        reset = ['day_reset', 'week_reset', 'annual_reset']
        source_lookup = {0: 'No selection',
                         1: 'Traditional rain gauge',
                         2: 'Piezoelectric rain gauge'
                         }
        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the rain data from the device object. First try to get
            # all_rain_data but be prepared to catch the exception if our
            # device does not support CMD_READ_RAIN. In that case fall back to
            # the rain_data property instead.
            try:
                rain_data = device.rain
            except UnknownApiCommand:
                # use the rain_data property
                rain_data = device.raindata
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            print()
            if 'rain_priority' in rain_data:
                print(f'{"Rainfall data priority":>28}: '
                      f'{source_lookup.get(rain_data["rain_priority"], "unknown selection")}')
                print()
            if any(field in rain_data for field in traditional):
                print(f'{"Traditional rain data":>28}:')
                _data = rain_data.get('t_rainrate')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Rain rate":>30}: {_data_str})')
                _data = rain_data.get('t_rainevent')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Event rain":>30}: {_data_str})')
                _data = rain_data.get('t_rainday')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Daily rain":>30}: {_data_str})')
                _data = rain_data.get('t_rainweek')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Weekly rain":>30}: {_data_str})')
                _data = rain_data.get('t_rainmonth')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Monthly rain":>30}: {_data_str})')
                _data = rain_data.get('t_rainyear')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Yearly rain":>30}: {_data_str})')
                _data = rain_data.get('t_raingain')
                _data_str = "%.2f" % _data / 100.0 if _data is not None else "---"
                print("%30s: %s" % ('Rain gain', _data_str))
            else:
                print(f'{"No traditional rain data available":>38}')
            print()
            if any(field in rain_data for field in piezo):
                print(f'{"Piezo rain data":>28}:')
                _data = rain_data.get('p_rainrate')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Rain rate":>30}: {_data_str})')
                _data = rain_data.get('p_rainevent')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Event rain":>30}: {_data_str})')
                _data = rain_data.get('p_rainday')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Daily rain":>30}: {_data_str})')
                _data = rain_data.get('p_rainweek')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Weekly rain":>30}: {_data_str})')
                _data = rain_data.get('p_rainmonth')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Monthly rain":>30}: {_data_str})')
                _data = rain_data.get('p_rainyear')
                _data_str = f'{_data:.1f}mm/hr ({_data / 25.4:.1f}in/hr)' if _data is not None else "---mm/hr (---in/hr)"
                print(f'{"Yearly rain":>30}: {_data_str})')
                _data = rain_data.get('gain1')
                _data_str = f'{_data:.2f} (< 4mm/h)' if _data is not None else '-- (< 4mm/h)'
                print(f'{"Rain1 gain":>30}: {_data_str})')
                _data = rain_data.get('gain2')
                _data_str = f'{_data:.2f} (< 4mm/h)' if _data is not None else '-- (< 10mm/h)'
                print(f'{"Rain1 gain":>30}: {_data_str})')
                _data = rain_data.get('gain3')
                _data_str = f'{_data:.2f} (< 4mm/h)' if _data is not None else '-- (< 30mm/h)'
                print(f'{"Rain1 gain":>30}: {_data_str})')
                _data = rain_data.get('gain4')
                _data_str = f'{_data:.2f} (< 4mm/h)' if _data is not None else '-- (< 60mm/h)'
                print(f'{"Rain1 gain":>30}: {_data_str})')
                _data = rain_data.get('gain5')
                _data_str = f'{_data:.2f} (< 4mm/h)' if _data is not None else '-- (> 60mm/h)'
                print(f'{"Rain1 gain":>30}: {_data_str})')
            else:
                print(f'{"No piezo rain data available":>32}')
            print()
            if any(field in rain_data for field in reset):
                print(f'{"Rainfall reset time data:":>28}:')
                _data = rain_data.get('day_reset')
                _data_str = f'{_data:02d}:00' if _data is not None else '-----'
                print(f'{"Daily rainfall reset time":>30}: {_data_str}')
                _data = rain_data.get('week_reset')
                _data_str = f'{calendar.day_name[(_data + 6) % 7]}' if _data is not None else '-----'
                print(f'{"Weekly rainfall reset time":>30}: {_data_str}')
                _data = rain_data.get('annual_reset')
                _data_str = f'{calendar.month_name[_data + 1]}' if _data is not None else '-----'
                print(f'{"Annual rainfall reset time":>30}: {_data_str}')
            else:
                print(f'{"No rainfall reset time data available":>41}')

    def display_mulch_offset(self):
        """Display device multichannel temperature and humidity offset data.

        Obtain and display the multichannel temperature and humidity offset
        data from the selected device. The device IP address and port are
        derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the mulch offset data from the API
            mulch_offset_data = device.mulch_offset
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any mulch offset data
            if mulch_offset_data is not None:
                # now format and display the data
                print()
                print("Multi-channel Temperature and Humidity Calibration")
                # do we have any results to display?
                if len(mulch_offset_data) > 0:
                    # iterate over each channel for which we have data
                    for channel in mulch_offset_data:
                        # Print the channel and offset data. The API returns
                        # channels starting at 0, but the WS View app displays
                        # channels starting at 1, so add 1 to our channel number
                        channel_str = f'{"Channel":>11} {channel + 1:d}'
                        temp_offset_str = f'{mulch_offset_data[channel]["temp"]:2.1f}'
                        hum_offset_str = f'{mulch_offset_data[channel]["hum"]:d}'
                        print(f'{channel_str:>13}: Temperature offset: {temp_offset_str:5} '
                              f'Humidity offset: {hum_offset_str:5}')
                else:
                    # we have no results, so display a suitable message
                    print(f'{"No Multi-channel temperature and humidity sensors found":>59}')
            else:
                print()
                print(f'Device at {self.ip_address} did not respond.')

    def display_mulch_t_offset(self):
        """Display device multichannel temperature (WN34) offset data.

        Obtain and display the multichannel temperature (WN34) offset data from
        the selected device. The device IP address and port are derived (in
        order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the mulch temp offset data via the API
            mulch_t_offset_data = device.mulch_t_offset
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any mulch temp offset data
            if mulch_t_offset_data is not None:
                print()
                print("Multi-channel Temperature Calibration")
                # do we have any results to display?
                if len(mulch_t_offset_data) > 0:
                    # we have results, now format and display the data
                    # iterate over each channel for which we have data
                    for channel in mulch_t_offset_data:
                        # Print the channel and offset data. The API returns
                        # channels starting at 0x63, but the WSView Plus app
                        # displays channels starting at 1, so subtract 0x62
                        # (or 98) from our channel number
                        # channel_str = f'{"Channel":>11} {channel - 0x62:d}'
                        channel_str = f'{"Channel":>11} {channel[-1]}'
                        temp_offset_str = f'{mulch_t_offset_data[channel]:2.1f}'
                        print(f'{channel_str:>13}: Temperature offset: {temp_offset_str:5}')

                else:
                    # we have no results, so display a suitable message
                    print(f'{"No Multi-channel temperature sensors found":>46}')
            else:
                print()
                print(f'Device at {self.ip_address} did not respond.')

    def display_pm25_offset(self):
        """Display the device PM2.5 offset data.

        Obtain and display the PM2.5 offset data from the selected device.The
        device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the PM2.5 offset data from the API
            pm25_offset_data = device.pm25_offset
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any PM2.5 offset data
            if pm25_offset_data is not None:
                # do we have any results to display?
                if len(pm25_offset_data) > 0:
                    # now format and display the data
                    print()
                    print("PM2.5 Calibration")
                    # iterate over each channel for which we have data
                    for channel in pm25_offset_data:
                        # print the channel and offset data
                        channel_str = f'{"Channel":>11} {channel:d}'
                        offset_str = f'{pm25_offset_data[channel]:2.1f}'
                        print(f'{channel_str:>13}: PM2.5 offset: {offset_str:5}')
                else:
                    # we have no results, so display a suitable message
                    print(f'{"No PM2.5 sensors found":>28}')
            else:
                print()
                print(f'Device at {self.ip_address} did not respond.')

    def display_co2_offset(self):
        """Display the device WH45 CO2, PM10 and PM2.5 offset data.

        Obtain and display the WH45 CO2, PM10 and PM2.5 offset data from the
        selected device. The device IP address and port are derived (in order)
        as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the offset data from the API
            co2_offset_data = device.co2_offset
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any offset data
            if co2_offset_data is not None:
                # now format and display the data
                print()
                print("CO2 Calibration")
                print(f'{"CO2 offset":>16}: {co2_offset_data["co2"]:2.1f}')
                print(f'{"PM10 offset":>16}: {co2_offset_data["pm10"]:2.1f}')
                print(f'{"PM2.5 offset":>16}: {co2_offset_data["pm25"]:2.1f}')
            else:
                print()
                print(f'Device at {self.ip_address} did not respond.')

    def display_calibration(self):
        """Display the device calibration data.

        Obtain and display the calibration data from the selected device. The
        device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the main offset and gain calibration data from the device
            calibration_data = device.offset_and_gain
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any calibration data
            if calibration_data is not None:
                # now format and display the data
                print()
                print("Calibration")
                print(f'{"Irradiance gain":>28}: {calibration_data["solar"]:5.2f}')
                print(f'{"UV gain":>28}: {calibration_data["uv"]:4.1f}')
                print(f'{"Wind gain":>28}: {calibration_data["wind"]:4.1f}')
                print(f'{"Inside temperature offset":>28}: {calibration_data["intemp"]:4.1f} \xb0C')
                print(f'{"Inside humidity offset":>28}: {calibration_data["inhum"]:4.1f} %')
                print(f'{"Outside temperature offset":>28}: {calibration_data["outtemp"]:4.1f} \xb0C')
                print(f'{"Outside humidity offset":>28}: {calibration_data["outhum"]:4.1f} %')
                print(f'{"Absolute pressure offset":>28}: {calibration_data["abs"]:4.1f} hPa')
                print(f'{"Relative pressure offset":>28}: {calibration_data["rel"]:4.1f} hPa')
                print(f'{"Wind direction offset":>28}: {calibration_data["dir"]:4.1f} \xb0')
            else:
                print()
                print(f'Device at {self.ip_address} did not respond.')

    def display_soil_calibration(self):
        """Display the device soil moisture sensor calibration data.

        Obtain and display the soil moisture sensor calibration data from the
        selected device. The device IP address and port are derived (in order)
        as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the device soil_calibration property
            calibration_data = device.soil_calibration
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any calibration data
            if calibration_data is not None:
                # now format and display the data
                # first get a list of channels for which we have data, since
                # this is the keys to a dict we need to sort them
                channels = sorted(calibration_data.keys())
                print()
                print("Soil Calibration")
                # iterate over each channel printing the channel data
                for channel in channels:
                    channel_dict = calibration_data[channel]
                    # the API returns channels starting at 0, but the
                    # WSView/WSView Plus apps display channels starting at 1,
                    # so add 1 to our channel number
                    print("    Channel %d (%d%%)" % (channel + 1, channel_dict['humidity']))
                    print("%16s: %d" % ("Now AD", channel_dict['ad']))
                    print("%16s: %d" % ("0% AD", channel_dict['adj_min']))
                    print("%16s: %d" % ("100% AD", channel_dict['adj_max']))
            else:
                print()
                print(f'Device at {self.ip_address} did not respond.')

    def display_services(self):
        """Display the device Weather Services settings.

        Obtain and display the settings for the various weather services
        supported by the device. the device IP address and port are
        derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # each weather service uses different parameters so define individual
        # functions to print each services settings

        def print_ecowitt_net(data_dict=None):
            """Print Ecowitt.net settings."""

            # do we have any settings?
            if data_dict is not None:
                # upload interval, 0 means disabled
                if data_dict['interval'] == 0:
                    print("%22s: %s" % ("Upload Interval",
                                        "Upload to Ecowitt.net is disabled"))
                elif data_dict['interval'] > 1:
                    print("%22s: %d minutes" % ("Upload Interval",
                                                data_dict['interval']))
                else:
                    print("%22s: %d minute" % ("Upload Interval",
                                               data_dict['interval']))
                # device MAC
                print("%22s: %s" % ("MAC", data_dict['mac']))

        def print_wunderground(data_dict=None):
            """Print Weather Underground settings."""

            # do we have any settings?
            if data_dict is not None:
                # Station ID
                wu_id = data_dict['id'] if self.namespace.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Station ID", wu_id))
                # Station key
                key = data_dict['password'] if self.namespace.unmask else obfuscate(data_dict['password'])
                print("%22s: %s" % ("Station Key", key))

        def print_weathercloud(data_dict=None):
            """Print Weathercloud settings."""

            # do we have any settings?
            if data_dict is not None:
                # Weathercloud ID
                wc_id = data_dict['id'] if self.namespace.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Weathercloud ID", wc_id))
                # Weathercloud key
                key = data_dict['password'] if self.namespace.unmask else obfuscate(data_dict['password'])
                print("%22s: %s" % ("Weathercloud Key", key))

        def print_wow(data_dict=None):
            """Print Weather Observations Website settings."""

            # do we have any settings?
            if data_dict is not None:
                # Station ID
                wow_id = data_dict['id'] if self.namespace.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Station ID", wow_id))
                # Station key
                key = data_dict['password'] if self.namespace.unmask else obfuscate(data_dict['password'])
                print("%22s: %s" % ("Station Key", key))

        def print_custom(data_dict=None):
            """Print Custom server settings."""

            # do we have any settings?
            if data_dict is not None:
                # Is upload enabled, API specifies 1=enabled and 0=disabled, if
                # we have anything else use 'Unknown'
                if data_dict['active'] == 1:
                    print("%22s: %s" % ("Upload", "Enabled"))
                elif data_dict['active'] == 0:
                    print("%22s: %s" % ("Upload", "Disabled"))
                else:
                    print("%22s: %s" % ("Upload", "Unknown"))
                # upload protocol, API specifies 1=wundeground and 0=ecowitt,
                # if we have anything else use 'Unknown'
                if data_dict['type'] == 0:
                    print("%22s: %s" % ("Upload Protocol", "Ecowitt"))
                elif data_dict['type'] == 1:
                    print("%22s: %s" % ("Upload Protocol", "Wunderground"))
                else:
                    print("%22s: %s" % ("Upload Protocol", "Unknown"))
                # remote server IP address
                print("%22s: %s" % ("Server IP/Hostname", data_dict['server']))
                # remote server path, if using wunderground protocol we have
                # Station ID and Station key as well
                if data_dict['type'] == 0:
                    print("%22s: %s" % ("Path", data_dict['ecowitt_path']))
                elif data_dict['type'] == 1:
                    print("%22s: %s" % ("Path", data_dict['wu_path']))
                    custom_id = data_dict['id'] if self.namespace.unmask else obfuscate(data_dict['id'])
                    print("%22s: %s" % ("Station ID", custom_id))
                    key = data_dict['password'] if self.namespace.unmask else obfuscate(data_dict['password'])
                    print("%22s: %s" % ("Station Key", key))
                # port
                print("%22s: %d" % ("Port", data_dict['port']))
                # upload interval in seconds
                print("%22s: %d seconds" % ("Upload Interval", data_dict['interval']))

        # look table of functions to use to print weather service settings
        print_fns = {'ecowitt_net_params': print_ecowitt_net,
                     'wu_params': print_wunderground,
                     'wcloud_params': print_weathercloud,
                     'wow_params': print_wow,
                     'all_custom_params': print_custom}

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            print()
            # get the settings for each service know to the device, store them
            # in a dict keyed by the service name
            services_data = {}
            for service in device.services:
                services_data[service['name']] = getattr(device, service['name'])
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
        else:
            # did we get any service data
            if len(services_data) > 0:
                # now format and display the data
                print("Weather Services")
                print()
                # iterate over the weather services we know about and call the
                # relevant function to print the services settings
                for service in device.services:
                    print("  %s" % (service['long_name'],))
                    print_fns[service['name']](services_data[service['name']])
                    print()

            else:
                print()
                print("Device at %s did not respond." % (self.ip_address,))

    def display_station_mac(self):
        """Display the device hardware MAC address.

        Obtain and display the hardware MAC address of the selected device.
        """

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # get the device MAC address
        print("    MAC address: %s" % device.mac_address)

    def display_firmware(self):
        """Display device firmware details.

        Obtain and display the firmware version string from the selected
        gateway device. User is advised whether a firmware update is available
        or not.
        """

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # obtain the device model
        model = device.model
        # identify the device being used
        print()
        print(f'Interrogating {Bcolors.BOLD}{model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # get the firmware version via the API
        print("    installed %s firmware version is %s" % (model, device.firmware_version))
        ws90_fw = device.ws90_firmware_version
        if ws90_fw is not None:
            print("    installed WS90 firmware version is %s" % ws90_fw)
        print()
        fw_update_avail = device.firmware_update_avail
        if fw_update_avail:
            # we have an available firmware update
            # obtain the 'curr_msg' from the device HTTP API
            # 'get_device_info' command, this field usually contains the
            # firmware change details
            curr_msg = device.firmware_update_message
            # now print the firmware update details
            print("    a firmware update is available for this %s," % model)
            print("    update at http://%s or via the WSView Plus app" % (self.ip_address,))
            # if we have firmware update details print them
            if curr_msg is not None:
                print()
                # Ecowitt have not documented the HTTP API calls so we are
                # not exactly sure what the 'curr_msg' field is used for,
                # it might be for other things as well
                print("    likely firmware update message:")
                # multi-line messages seem to have \r\n at the end of each
                # line, split the string so we can format it a little better
                if '\r\n' in curr_msg:
                    for line in curr_msg.split('\r\n'):
                        # print each line
                        print("      %s" % line)
                else:
                    # print as a single line
                    print("      %s" % curr_msg)
            else:
                # we had no 'curr_msg' for one reason or another
                print("    no firmware update message found")
        elif fw_update_avail is None:
            # we don't know if we have an available firmware update
            print("    could not determine if a firmware update is available for this %s" % model)
        else:
            # there must be no available firmware update
            print("    the firmware is up to date for this %s" % model)

    def display_sensors(self):
        """Display the device sensor ID information.

        Obtain and display the sensor ID information from the selected gateway
        device.
        """

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # obtain the device model
        model = device.model
        # identify the device being used
        print()
        print(f'Interrogating {Bcolors.BOLD}{model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        # first update the GatewayDevice object sensor ID data
        device.update_sensor_id_data()
        # now get the sensors property from the GatewayDevice object
        sensors = device.sensors
        # the sensor ID data is in the sensors data property, did
        # we get any sensor ID data
        if sensors.data is not None and len(sensors.data) > 0:
            # now format and display the data
            print()
            print(f"{'Sensor':<10} {'Status'}")
            # iterate over each sensor for which we have data
            for address, sensor_data in sensors.data.items():
                # the sensor id indicates whether it is disabled, attempting to
                # register a sensor or already registered
                if sensor_data['id'] == 'fffffffe':
                    state = 'sensor is disabled'
                elif sensor_data['id'] == 'ffffffff':
                    state = 'sensor is registering...'
                else:
                    # the sensor is registered, so we should have signal and
                    # battery data as well
                    battery_desc = sensors.batt_state_desc(address, sensor_data.get('battery'))
                    battery_desc_text = f" ({battery_desc})" if battery_desc is not None else f""
                    battery_str = f"{sensor_data.get('battery')}{battery_desc_text}"
                    state = f"sensor ID: {sensor_data.get('id').lstrip('0'):<6}  "\
                            f"signal: {sensor_data.get('signal'):1}  battery: {battery_str:<14}"
                    # print the formatted data
                print(f"{Sensors.sensor_ids[address].get('long_name'):<10} {state}")
        elif len(sensors.data) == 0:
            print()
            print(f"Device at {self.ip_address} did not return any sensor data.")
        else:
            print()
            print("Device at {self.ip_address} did not respond.")

    def display_live_data(self):
        """Display the device live sensor data.

        Obtain and display live sensor data from the selected device.
        """

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        # get the live sensor data
        live_sensor_data_dict = device.livedata
        # display the live sensor data if we have any
        if len(live_sensor_data_dict) > 0:
            print()
            for item_num in device.gateway_api_parser.addressed_data_struct.keys():
                if item_num in live_sensor_data_dict:
                    item_str = ''.join(['(', device.gateway_api_parser.addressed_data_struct[item_num][3], ')', ':'])
                    value_str = re.sub(r'\.?0+$',lambda match: ' '*(match.end()-match.start()),'{:>12.1f}'.format(live_sensor_data_dict[item_num]))
                    print(f"0x{bytes_to_hex(item_num):<3}{item_str:<23} {value_str}")
        print(f"live sensor data={live_sensor_data_dict}")

    def display_discovered_devices(self):
        """Display details of gateway devices on the local network."""

        # this could take a few seconds so warn the user
        print()
        print("Discovering devices on the local network. Please wait...")
        # obtain a GatewayDevice object
        device = GatewayDevice(debug=self.namespace.debug)
        # Obtain a list of discovered devices. Would consider wrapping in a
        # try..except so we can catch any socket timeout exceptions, but the
        # GatewayApi.discover() method should catch any such exceptions for us.
        device_list = device.discovered_devices
        print()
        if len(device_list) > 0:
            # we have at least one result
            # first sort our list by IP address
            sorted_list = sorted(device_list, key=itemgetter('ip_address'))
            # initialise a counter to count the number of valid devices found
            num_gw_found = 0
            # iterate over the unique devices that were found
            for device in sorted_list:
                if device['ip_address'] is not None and device['port'] is not None:
                    print("%s discovered at IP address %s on port %d" % (device['model'],
                                                                         device['ip_address'],
                                                                         device['port']))
                    num_gw_found += 1
            if num_gw_found == 0:
                print("No devices were discovered.")
        else:
            # we have no results
            print("No devices were discovered.")

    def write_ecowitt(self):
        """Write Ecowitt.net upload parameters to a gateway device."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current custom params and usr path settings from the
        # device
        ecowitt_params = device.ecowitt_net_params
        # make a copy of the current ecowitt params, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_ecowitt_params = dict(ecowitt_params)
        # iterate over each ecowitt param (param, value) pair
        for param, value in ecowitt_params.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our ecowitt param dict copy if the namespace argument is
            # not None, otherwise keep the current custom param value
            arg_ecowitt_params[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_ecowitt_params != ecowitt_params:
            # something has changed, so write the updated params to the device
            try:
                device.write_custom(**arg_ecowitt_params)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print()
            print("No changes to current device settings")

    def write_wu_wow_wcloud(self):
        """Process wu, wow and wcloud write sub-subcommands."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current WU/WOW/Weathercloud upload params from the device
        current_params = getattr(device, '_'.join([self.namespace.write_subcommand, 'params']))
        # make a copy of the current params, this copy will be updated with
        # the subcommand arguments and then used to update the device
        arg_service_params = dict(current_params)
        # iterate over each current param (param, value) pair
        for param, value in current_params.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our param dict copy if the namespace argument is not None,
            # otherwise keep the current param value
            arg_service_params[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_service_params != current_params:
            # something has changed, so write the updated params to the device
            try:
                getattr(device, '_'.join(['write', self.namespace.write_subcommand]))(**arg_service_params)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print()
            print("No changes to current device settings")

    def write_custom(self):
        """Process custom write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current custom params and usr path settings from the
        # device
        custom_params = device.custom_params
        usr_path = device.usr_path
        # make a copy of the current custom params, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_custom_params = dict(custom_params)
        # iterate over each custom param (param, value) pair
        for param, value in custom_params.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our custom param dict copy if the namespace argument is
            # not None, otherwise keep the current custom param value
            arg_custom_params[param] = _arg if _arg is not None else value
        # make a copy of the current usr path params, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_usr_path = dict(usr_path)
        # iterate over each usr path param (param, value) pair
        for param, value in usr_path.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our usr path param dict copy if the namespace argument is
            # not None, otherwise keep the current usr path param value
            arg_usr_path[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_custom_params != custom_params or arg_usr_path != usr_path:
            # something has changed, so combine our updated dicts and write the
            # updated params to the device
            arg_custom_params.update(arg_usr_path)
            # write the updated settings to the device
            try:
                device.write_custom(**arg_custom_params)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")

            else:
                print("Device write completed successfully")
        else:
            print()
            print("No changes to current device settings")

    def write_calibration(self):
        """Process calibration write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current ofsset and gain params from the device
        cal_params = device.offset_and_gain
        # make a copy of the current cal params, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_cal_params = dict(cal_params)
        # iterate over each cal param (param, value) pair
        for param, value in cal_params.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our cal param dict copy if the namespace argument is
            # not None, otherwise keep the current cal param value
            arg_cal_params[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_cal_params != cal_params:
            # something has changed, so write the updated params to the device
            try:
                device.write_gain(**arg_cal_params)
                device.write_calibration(**arg_cal_params)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print()
            print("No changes to current device settings")

    def write_sensor_id(self):
        """Process sensor-id write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current sensor ID params from the device
        # first update the GatewayDevice object sensor ID data
        device.update_sensor_id_data()
        # now obtain a dict of current sensors IDs in numeric format
        id_params = device.sensors.ids_by_name(numeric_id=True)
        # make a copy of the current sensor ID params, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_id_params = dict(id_params)
        # iterate over each sensor ID param (param, value) pair
        for sensor_name, sensor_id in id_params.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, sensor_name, None)
            # update our cal param dict copy if the namespace argument is
            # not None, otherwise keep the current cal param value
            arg_id_params[sensor_name] = _arg if _arg is not None else sensor_id
        # do we have any changes from our existing settings
        if arg_id_params != id_params:
            # something has changed, so
            id_and_address = dict()
            for name, id in arg_id_params.items():
                id_and_address[name] = {'id': id,
                                        'address': device.sensors.sensor_idt[name]
                                        }
            # write the updated params to the device
            try:
                device.write_sensor_id(**id_and_address)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_pm25_offset(self):
        """Process pm25-offset write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current pm2.5 sensor offsets from the device
        offsets = device.pm25_offset
        # make a copy of the current offsets, this copy will be updated with
        # the subcommand arguments and then used to update the device
        arg_offsets = dict(offsets)
        # iterate over each offset (param, value) pair
        for channel, offset in offsets.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, channel, None)
            # update our offset dict copy if the namespace argument is not
            # None, otherwise keep the current offset
            arg_offsets[channel] = _arg if _arg is not None else offset
        # do we have any changes from our existing settings
        if arg_offsets != offsets:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_pm25_offsets(**arg_offsets)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_co2_offset(self):
        """Process c02-offset write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current co2 sensor offsets from the device
        offsets = device.co2_offset
        # make a copy of the current sensor offsets, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_offsets = dict(offsets)
        # iterate over each offset (param, value) pair
        for type, offset in offsets.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, type, None)
            # update our offset dict copy if the namespace argument is not
            # None, otherwise keep the current offsets
            arg_offsets[type] = _arg if _arg is not None else offset
        # do we have any changes from our existing settings
        if arg_offsets != offsets:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_co2_offsets(**arg_offsets)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_rain(self):
        """Process rain write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current rain related parameters from the device
        parameters = device.rain
        # make a copy of the current parameters, this copy will be updated with
        # the subcommand arguments and then used to update the device
        arg_parameters = dict(parameters)
        # iterate over each parameter (param, value) pair
        for param, value in parameters.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our dict copy if the namespace argument is not None,
            # otherwise keep the current parameter value
            arg_parameters[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_parameters != parameters:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_rain(**arg_parameters)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_system(self):
        """Process system write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current system params from the device
        _params = device.system_params
        # make a copy of the current system params, this copy will be updated
        # with the subcommand arguments and then used to update the device
        arg_params = dict(_params)
        # iterate over each system param (param, value) pair
        for param, value in _params.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our dict copy if the namespace argument is not None,
            # otherwise keep the current param value
            arg_params[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_params != _params:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_system_params(**arg_params)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_rain_data(self):
        """Process rain-data write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current rain data from the device
        rain_data = device.raindata
        # make a copy of the current rain data, this copy will be updated with
        # the subcommand arguments and then used to update the device
        arg_rain_data = dict(rain_data)
        # iterate over each rain data (param, value) pair
        for param, value in rain_data.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our dict copy if the namespace argument is not None,
            # otherwise keep the current pm25 offsets
            arg_rain_data[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_rain_data != rain_data:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_rain_data(**arg_rain_data)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_mulch_th(self):
        """Process rain-data write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current rain data from the device
        rain_data = device.raindata
        # make a copy of the current rain data, this copy will be updated with
        # the subcommand arguments and then used to update the device
        arg_rain_data = dict(rain_data)
        # iterate over each rain data (param, value) pair
        for param, value in rain_data.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our dict copy if the namespace argument is not None,
            # otherwise keep the current pm25 offsets
            arg_rain_data[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_rain_data != rain_data:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_rain_data(**arg_rain_data)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_soil_moist(self):
        """Process rain-data write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current rain data from the device
        rain_data = device.raindata
        # make a copy of the current rain data, this copy will be updated with
        # the subcommand arguments and then used to update the device
        arg_rain_data = dict(rain_data)
        # iterate over each rain data (param, value) pair
        for param, value in rain_data.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, param, None)
            # update our dict copy if the namespace argument is not None,
            # otherwise keep the current pm25 offsets
            arg_rain_data[param] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_rain_data != rain_data:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_rain_data(**arg_rain_data)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")

    def write_mulch_t(self):
        """Process mulch-t-cal write sub-subcommand."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address,
                                   port=self.port,
                                   debug=self.debug)
        except GWIOError as e:
            print()
            print(f'Unable to connect to device at {self.ip_address}: {e}')
            return
        except socket.timeout:
            print()
            print(f'Timeout. Device at {self.ip_address} did not respond.')
            return
        # identify the device being used
        print()
        print(f'Updating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
              f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
        print()
        # obtain the current mulch temperature offset data from the device
        offset_data = device.mulch_t_offset
        # make a copy of the current mulch temperature offset data, this copy
        # will be updated with the subcommand arguments and then used to update
        # the device
        arg_offset_data = dict(offset_data)
        # iterate over each offset (param, value) pair
        for offset, value in offset_data.items():
            # obtain the corresponding argument from the namespace, if the
            # argument does not exist or is not set it will be None
            _arg = getattr(self.namespace, offset, None)
            # update our dict copy if the namespace argument is not None,
            # otherwise keep the current pm25 offsets
            arg_offset_data[offset] = _arg if _arg is not None else value
        # do we have any changes from our existing settings
        if arg_offset_data != offset_data:
            # something has changed, so write the updated offsets to the device
            try:
                device.write_mulch_t(**arg_offset_data)
            except DeviceWriteFailed as e:
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: {e}")
            else:
                print("Device write completed successfully")
        else:
            print("No changes to current device settings")


# ============================================================================
#                             Argparse utility functions
# ============================================================================

def maxlen(max_length):
    """Function supporting length limited ArgumentParser arguments.

    Returns a handle to a function that checks the length of an argument is
    less than or equal to specified value. If the argument is longer than the
    specified length an ArgumentTypeError exception is raised with a suitable
    error message.

    If the argument meets the type and range checks a string is returned.
    """

    # define a function to perform the necessary checks, we will return a
    # handle to this function
    def check(arg):
        """Check an argument is no longer than a given value."""

        if len(arg) > max_length:
            raise argparse.ArgumentTypeError(f"argument length must be {max_length:d} characters or less ({arg})")
        return arg

    # return a handle to the check function
    return check


def ranged_type(type, min_value, max_value):
    """Function supporting range limited ArgumentParser numeric arguments.

    Returns a handle to a function that checks an argument is a specified type
    and falls within a specified range. If the argument cannot be converted to
    the specified type or the argument < min_value or > max_value an
    ArgumentTypeError exception is raised with a suitable error message.

    If the argument meets the type and range checks a number of the specified
    type is returned.
    """

    # define a function to perform the necessary checks, we will return a
    # handle to this function
    def check(arg):
        """Check an argument type and its value is within a given range."""

        try:
            _arg = type(arg)
        except ValueError:
            raise argparse.ArgumentTypeError(f"argument must be a valid {type} ({arg})")
        if _arg < min_value or _arg > max_value:
            raise argparse.ArgumentTypeError(f"argument must be in range [{min_value} .. {max_value}] ({arg})")
        return _arg

    # return a handle to the check function
    return check


def sensor_id_type(digits):
    """Argparse type support for Ecowitt sensor ID hexadecimal arguments.

    Returns a handle to a function that checks an argument is a valid Ecowitt
    sensor ID hexadecimal number with no more than a given number of digits.
    If the argument cannot be converted to a hexadecimal number or the argument
    has more than the specified number of digits an ArgumentTypeError exception
    is raised with a suitable error message.

    The function also supports the shorthand 'disable'. If the argument is
    'disable' the Ecowitt disabled sensor ID value 0xfffffffe is returned.

    If the argument meets the type and number of digits checks the decimal
    equivalent of the argument is returned.
    """

    # define a function to perform the necessary checks, we will return a
    # handle to this function
    def check(arg):
        """Check an argument type and its value is within a given range."""

        # first check to see if the shorthand 'disable' has been used
        if arg.lower() == 'disable':
            return int('0xfffffffe', 0)
        else:
            # try to convert the argument to an integer using base 16
            try:
                _arg = int(arg, 16)
            except ValueError:
                # Could not convert to an integer, ergo the argument is not a valid
                # hexadecimal string. Raise a suitable argparse.ArgumentTypeError
                # exception
                raise argparse.ArgumentTypeError(f"argument must be a valid hexadecimal number ({arg})")
            # check the argument does not exceed the max number of digits
            if _arg > 16 ** digits - 1:
                # too many digits, raise a suitable argparse.ArgumentTypeError
                # exception
                raise argparse.ArgumentTypeError(f"argument must be 0x{(16 ** digits - 1):02x} or less ({arg})")
            # the argument meets all checks, return the converted argument
            return _arg

    # return a handle to the check function
    return check

def sensor_type(sensor_types):
    """Argparse type support for Ecowitt sensor type selection.

    Returns a handle to a function that checks an argument is a member of a
    given list of possible choices. If the argument is not in the list of
    choices an ArgumentTypeError exception is raised with a suitable error
    message.

    If the argument is in the list of choices the index number of the argument
    in the choices list is returned.
    """

    # define a function to perform the necessary checks, we will return a
    # handle to this function
    def check(arg):
        """Check an argument is a member of a given list."""

        # check if the argument is in the choices list
        if arg.upper() in sensor_types:
            # we have a valid argument, return its index
            return sensor_types.index(arg.upper())
        else:
            # we have an invalid argument, raise an ArgumentTypeError exception
            option_list_str = ", ".join(["'{}'".format(o) for o in sensor_types])
            raise argparse.ArgumentTypeError(f"invalid choice: {arg} (choose from {option_list_str})")

    # return a handle to the check function
    return check


def enable_disable_type(opts=('disable', 'enable')):
    """Argparse type support for Ecowitt sensor type selection.

    Returns a handle to a function that checks an argument is a member of a
    given list of possible choices. If the argument is not in the list of
    choices an ArgumentTypeError exception is raised with a suitable error
    message.

    If the argument is in the list of choices the index number of the argument
    in the choices list is returned.
    """

    # define a function to perform the necessary checks, we will return a
    # handle to this function
    def check(arg):
        """Check an argument is a member of a given list."""

        # check if the argument is in the choices list
        if arg.lower() in opts:
            # we have a valid argument, return its index
            return opts.index(arg.lower())
        else:
            # we have an invalid argument, raise an ArgumentTypeError exception
            option_list_str = ", ".join(["'{}'".format(o) for o in opts])
            raise argparse.ArgumentTypeError(f"invalid choice: {arg} (choose from {option_list_str})")

    # return a handle to the check function
    return check


def dispatch_get(namespace):
    """Process 'get' subcommand."""

    # get a DirectGateway object
    direct_gw = DirectGateway(namespace)
    # process the command line arguments to determine what we should do
    if getattr(namespace, 'sys_params', False):
        direct_gw.display_system_params()
    elif getattr(namespace, 'rain_data', False):
        direct_gw.display_rain_data()
    elif getattr(namespace, 'all_rain_data', False):
        direct_gw.display_all_rain_data()
    elif getattr(namespace, 'mulch_calibration', False):
        direct_gw.display_mulch_offset()
    elif getattr(namespace, 'mulch_temp_calibration', False):
        direct_gw.display_mulch_t_offset()
    elif getattr(namespace, 'pm25_calibration', False):
        direct_gw.display_pm25_offset()
    elif getattr(namespace, 'co2_calibration', False):
        direct_gw.display_co2_offset()
    elif getattr(namespace, 'calibration', False):
        direct_gw.display_calibration()
    elif getattr(namespace, 'soil_calibration', False):
        direct_gw.display_soil_calibration()
    elif getattr(namespace, 'services', False):
        direct_gw.display_services()
    elif getattr(namespace, 'mac', False):
        # TODO. Rename to remove 'station' ?
        direct_gw.display_station_mac()
    elif getattr(namespace, 'firmware', False):
        direct_gw.display_firmware()
    elif getattr(namespace, 'sensors', False):
        direct_gw.display_sensors()
    elif getattr(namespace, 'live_data', False):
        direct_gw.display_live_data()


def dispatch_write(namespace):
    """Process 'write' subcommand."""

    # get a DirectGateway object
    direct_gw = DirectGateway(namespace)
    # process the command line arguments to determine what we should do
    # first look for sub-subcommands
    if getattr(namespace, 'write_subcommand', False)  == 'ecowitt':
        direct_gw.write_ecowitt()
    if getattr(namespace, 'write_subcommand', False)  in ('wu', 'wow', 'wcloud'):
        direct_gw.write_wu_wow_wcloud()
    if getattr(namespace, 'write_subcommand', False)  == 'custom':
        direct_gw.write_custom()
    if getattr(namespace, 'write_subcommand', False)  == 'calibration':
        direct_gw.write_calibration()
    if getattr(namespace, 'write_subcommand', False)  == 'sensor-id':
        direct_gw.write_sensor_id()
    if getattr(namespace, 'write_subcommand', False)  == 'pm25-offset':
        direct_gw.write_pm25_offset()
    if getattr(namespace, 'write_subcommand', False)  == 'co2-offset':
        direct_gw.write_co2_offset()
    if getattr(namespace, 'write_subcommand', False)  == 'rain':
        direct_gw.write_rain()
    if getattr(namespace, 'write_subcommand', False)  == 'system':
        direct_gw.write_system()
    if getattr(namespace, 'write_subcommand', False)  == 'rain-data':
        direct_gw.write_rain_data()
    if getattr(namespace, 'write_subcommand', False)  == 'mulch-th-offset':
        direct_gw.write_mulch_th()
    if getattr(namespace, 'write_subcommand', False)  == 'soil-moist':
        direct_gw.write_soil_moist()
    if getattr(namespace, 'write_subcommand', False)  == 'mulch-t-offset':
        direct_gw.write_mulch_t()


def add_common_args(parser):
    """Add common arguments to an argument parser."""

    parser.add_argument('--ip-address',
                        dest='device_ip_address',
                        help='device IP address to use')
    parser.add_argument('--port',
                        dest='device_port',
                        type=int,
                        choices=range(0, 65537),
                        default=45000,
                        metavar='PORT',
                        help='device port to use')
    parser.add_argument('--max-tries',
                        dest='max_tries',
                        type=int,
                        help='max number of attempts to contact the device')
    parser.add_argument('--retry-wait',
                        dest='retry_wait',
                        type=int,
                        help='how long to wait between attempts to contact the device')
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='display additional debug information')


def get_action_exists(ns):
    """Does a given namespace contain at least one get action."""
    
    get_actions = ['live-data', 'sensors firmware', 'mac-address',
                   'system-params', 'rain-data', 'all-rain-data calibration',
                   'mulch-th-cal', 'mulch-soil-cal', 'pm25-cal', 'co2-cal',
                   'services']

    for action in get_actions:
        if getattr(ns, action, None) is not None:
            return True
    return False


def write_action_exists(ns):
    """Does a given namespace contain at least one write action."""

    return False if getattr(ns, 'write_subcommand', None) is None else True


def get_subparser(subparsers):
    """Add get subcommand."""

    get_usage = f"""{Bcolors.BOLD}ecowitt get --help
       ecowitt get --live-data | --sensors
                   --ip-address=IP_ADDRESS [--port=PORT]
                   [--show-all-batt] [--debug]
       ecowitt get --firmware | --mac-address |
                   --system-params | --rain-data | --all-rain-data
                   --ip-address=IP_ADDRESS [--port=PORT]
                   [--debug]
       ecowitt get --calibration | --mulch-th-cal | --mulch-soil-cal |
                   --pm25-cal | --co2-cal
                   --ip-address=IP_ADDRESS [--port=PORT]
                   [--debug]
       ecowitt get --services
                   --ip-address=IP_ADDRESS [--port=PORT]
                   [--unmask] [--debug]{Bcolors.ENDC}
    """
    get_description = """Obtain and display various sensor and device configuration data from an 
    Ecowitt gateway device."""

    get_parser = subparsers.add_parser('get',
                                       usage=get_usage,
                                       description=get_description,
                                       help="Obtain and display data from an Ecowitt gateway device.")

    get_parser.add_argument('--live-data',
                            dest='live_data',
                            action='store_true',
                            help='display device live sensor data')
    get_parser.add_argument('--sensors',
                            dest='sensors',
                            action='store_true',
                            help='display device sensor information')
    get_parser.add_argument('--firmware',
                            dest='firmware',
                            action='store_true',
                            help='display device firmware information')
    get_parser.add_argument('--mac-address',
                            dest='mac',
                            action='store_true',
                            help='display device station MAC address')
    get_parser.add_argument('--system-params',
                            dest='sys_params',
                            action='store_true',
                            help='display device system parameters')
    get_parser.add_argument('--rain-data',
                            dest='rain_data',
                            action='store_true',
                            help='display device traditional rain data only')
    get_parser.add_argument('--all-rain-data',
                            dest='all_rain_data',
                            action='store_true',
                            help='display device traditional, piezo and rain reset '
                                 'time data')
    get_parser.add_argument('--calibration',
                            dest='calibration',
                            action='store_true',
                            help='display device calibration data')
    get_parser.add_argument('--mulch-th-cal',
                            dest='mulch_calibration',
                            action='store_true',
                            help='display device multi-channel temperature and '
                                 'humidity calibration data')
    get_parser.add_argument('--mulch-soil-cal',
                            dest='soil_calibration',
                            action='store_true',
                            help='display device soil moisture calibration data')
    get_parser.add_argument('--mulch-t-cal',
                            dest='mulch_temp_calibration',
                            action='store_true',
                            help='display device temperature (WN34) calibration data')
    get_parser.add_argument('--pm25-cal',
                            dest='pm25_calibration',
                            action='store_true',
                            help='display device PM2.5 calibration data')
    get_parser.add_argument('--co2-cal',
                            dest='co2_calibration',
                            action='store_true',
                            help='display device CO2 (WH45) calibration data')
    get_parser.add_argument('--services',
                            dest='services',
                            action='store_true',
                            help='display device weather services configuration data')
    get_parser.add_argument('--show-all-batt',
                            dest='show_battery',
                            action='store_true',
                            help='show all available battery state data regardless of '
                                 'sensor state')
    get_parser.add_argument('--unmask',
                            dest='unmask',
                            action='store_true',
                            help='unmask sensitive settings')
    add_common_args(get_parser)
    get_parser.set_defaults(func=dispatch_get)
    return get_parser


def ecowitt_write_subparser(subparsers):
    """Define 'ecowitt write ecowitt' sub-subparser."""
    
    ecowitt_write_usage = f"""{Bcolors.BOLD}ecowitt write ecowitt --help
       ecowitt write ecowitt --interval INTERVAL
            --ip-address=IP_ADDRESS [--port=PORT]
            [--debug]{Bcolors.ENDC}
    """
    ecowitt_write_description = """Set Ecowitt.net upload parameters."""
    ecowitt_write_parser = subparsers.add_parser('ecowitt',
                                                 usage=ecowitt_write_usage,
                                                 description=ecowitt_write_description,
                                                 help="Set Ecowitt.net upload parameters.")
    ecowitt_write_parser.add_argument('--interval',
                                      dest='interval',
                                      type=int,
                                      choices=range(0, 6),
                                      default=0,
                                      metavar='INTERVAL',
                                      help='Ecowitt.net upload interval (0-5) in minutes. '
                                           '0 indicates upload is disabled. Default is 0.')
    add_common_args(ecowitt_write_parser)
    ecowitt_write_parser.set_defaults(func=dispatch_write)
    return ecowitt_write_parser


def wu_write_subparser(subparsers):
    """Define 'ecowitt write wu' sub-subparser."""

    wu_write_usage = f"""{Bcolors.BOLD}ecowitt write wu --help
       ecowitt write wu --station-id STATION_ID --station-key STATION_KEY
                        --ip-address=IP_ADDRESS [--port=PORT] [--debug]{Bcolors.ENDC}
    """
    wu_write_description = """Set WeatherUnderground upload parameters."""
    wu_write_parser = subparsers.add_parser('wu',
                                            usage=wu_write_usage,
                                            description=wu_write_description,
                                            help="Set WeatherUnderground upload parameters.")
    wu_write_parser.add_argument('--station-id',
                                 dest='id',
                                 metavar='STATION_ID',
                                 help='WeatherUnderground station ID')
    wu_write_parser.add_argument('--station-key',
                                 dest='key',
                                 metavar='STATION_KEY',
                                 help='WeatherUnderground station key')
    add_common_args(wu_write_parser)
    wu_write_parser.set_defaults(func=dispatch_write)
    return wu_write_parser


def wow_write_subparser(subparsers):
    """Define 'ecowitt write wow' sub-subparser."""

    wow_write_usage = f"""{Bcolors.BOLD}ecowitt write wow --help
       ecowitt write wow --station-id STATION_ID --station-key STATION_KEY
                         --ip-address=IP_ADDRESS [--port=PORT] [--debug]{Bcolors.ENDC}
    """
    wow_write_description = """Set Weather Observations Website upload parameters."""
    wow_write_parser = subparsers.add_parser('wow',
                                             usage=wow_write_usage,
                                             description=wow_write_description,
                                             help="Set Weather Observations Website upload parameters.")
    wow_write_parser.add_argument('--station-id',
                                  dest='id',
                                  metavar='STATION_ID',
                                  help='Weather Observations Website station ID')
    wow_write_parser.add_argument('--station-key',
                                  dest='key',
                                  metavar='STATION_KEY',
                                  help='Weather Observations Website station key')
    add_common_args(wow_write_parser)
    wow_write_parser.set_defaults(func=dispatch_write)
    return wow_write_parser


def wcloud_write_subparser(subparsers):
    """Define 'ecowitt write wcloud' sub-subparser."""

    wcloud_write_usage = f"""{Bcolors.BOLD}ecowitt write wcloud --help
       ecowitt write wcloud --station-id STATION_ID --station-key STATION_KEY
                            --ip-address=IP_ADDRESS [--port=PORT] [--debug]{Bcolors.ENDC}
    """
    wcloud_write_description = """Set Weathercloud upload parameters."""
    wcloud_write_parser = subparsers.add_parser('wcloud',
                                                usage=wcloud_write_usage,
                                                description=wcloud_write_description,
                                                help="Set Weathercloud upload parameters.")
    wcloud_write_parser.add_argument('--station-id',
                                     dest='id',
                                     metavar='STATION_ID',
                                     help='Weathercloud station ID')
    wcloud_write_parser.add_argument('--station-key',
                                     dest='key',
                                     metavar='STATION_KEY',
                                     help='Weathercloud station key')
    add_common_args(wcloud_write_parser)
    wcloud_write_parser.set_defaults(func=dispatch_write)
    return wcloud_write_parser


def custom_write_subparser(subparsers):
    """Define 'ecowitt write custom' sub-subparser."""

    custom_write_usage = f"""{Bcolors.BOLD}ecowitt write custom --help
       ecowitt write custom --ip-address=IP_ADDRESS [--port=PORT]
                            [--enabled | --disabled] [--protocol EC | WU] [--server IP_ADDRESS | NAME] 
                            [--upload-port UPLOAD_PORT] [--interval INTERVAL] 
                            [--ec-path EC_PATH] [--wu-path WU_PATH] 
                            [--station-id STATION_ID] [--station-key STATION_KEY]
                            [--debug]
{Bcolors.ENDC}"""
    custom_write_description = """Set Customized upload parameters. If a 
    parameter is omitted the corresponding current gateway device parameter is 
    left unchanged."""
    custom_write_parser = subparsers.add_parser('custom',
                                                usage=custom_write_usage,
                                                description=custom_write_description,
                                                help="Set Customized upload parameters.")
    custom_write_parser.add_argument('--enabled',
                                     dest='active',
                                     action='store_const',
                                     const=1,
                                     help='enable customized uploads')
    custom_write_parser.add_argument('--disabled',
                                     dest='active',
                                     action='store_const',
                                     const=0,
                                     help='disable customized uploads')
    custom_write_parser.add_argument('--protocol',
                                     dest='type',
                                     choices=('EC', 'WU'),
                                     type=lambda p: 0 if p.upper() == 'EC' else 1,
                                     metavar='PROTOCOL',
                                     help='upload protocol EC = Ecowitt WU = WeatherUnderground '
                                          '(WU requires --station-id and --station-key be populated)')
    custom_write_parser.add_argument('--server',
                                     dest='server',
                                     type=maxlen(64),
                                     metavar='IP_ADDRESS | NAME',
                                     help='destination server IP address or host name, max length 64 characters')
    custom_write_parser.add_argument('--upload-port',
                                     dest='port',
                                     type=ranged_type(int, 0, 65536),
                                     metavar='UPLOAD_PORT',
                                     help='destination server port number')
    custom_write_parser.add_argument('--ec-path',
                                     dest='ecowitt_path',
                                     type=maxlen(64),
                                     metavar='EC_PATH',
                                     help='Ecowitt protocol upload path')
    custom_write_parser.add_argument('--wu-path',
                                     dest='wu_path',
                                     type=maxlen(64),
                                     metavar='WU_PATH',
                                     help='WeatherUnderground protocol upload path')
    custom_write_parser.add_argument('--station-id',
                                     dest='id',
                                     type=maxlen(40),
                                     metavar='STATION_ID',
                                     help='WeatherUnderground protocol station ID')
    custom_write_parser.add_argument('--station-key',
                                     dest='password',
                                     type=maxlen(40),
                                     metavar='STATION_KEY',
                                     help='WeatherUnderground protocol station key')
    custom_write_parser.add_argument('--interval',
                                     dest='interval',
                                     type=ranged_type(int, 16, 600),
                                     metavar='UPLOAD_PORT',
                                     help='destination server port number')
    add_common_args(custom_write_parser)
    custom_write_parser.set_defaults(active=0, func=dispatch_write)
    return custom_write_parser


def cal_write_subparser(subparsers):
    """Define 'ecowitt write calibration' sub-subparser."""

    cal_write_usage = f"""{Bcolors.BOLD}ecowitt write calibration --help
       ecowitt write calibration --ip-address=IP_ADDRESS [--port=PORT]
                                 [--uv UV_GAIN] [--solar SOLAR_GAIN]
                                 [---wind-speed WIND_GAIN] [--rain RAIN_GAIN]
                                 [--debug]
{Bcolors.ENDC}"""
    cal_write_description = """Set calibration coefficients. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    cal_write_parser = subparsers.add_parser('calibration',
                                             usage=cal_write_usage,
                                             description=cal_write_description,
                                             help="Set calibration coefficients.")
    cal_write_parser.add_argument('--uv',
                                  dest='uv',
                                  type=ranged_type(float, 0.1, 5.0),
                                  help='UV calibration gain')
    cal_write_parser.add_argument('--solar',
                                  dest='solar',
                                  type=ranged_type(float, 0.1, 5.0),
                                  help='solar radiation calibration gain')
    cal_write_parser.add_argument('--wind-speed',
                                  dest='wind',
                                  type=ranged_type(float, 0.1, 5.0),
                                  help='wind speed calibration gain')
    cal_write_parser.add_argument('--intemp',
                                  dest='intemp',
                                  type=ranged_type(float, -10.0, 10.0),
                                  help='Inside temperature offset')
    cal_write_parser.add_argument('--inhum',
                                  dest='inhum',
                                  type=ranged_type(float, -10.0, 10.0),
                                  help='Inside humidity offset')
    cal_write_parser.add_argument('--outtemp',
                                  dest='outtemp',
                                  type=ranged_type(float, -10.0, 10.0),
                                  help='Outside temperature offset')
    cal_write_parser.add_argument('--outhum',
                                  dest='outhum',
                                  type=ranged_type(float, -10.0, 10.0),
                                  help='Outside humidity offset')
    cal_write_parser.add_argument('--abs',
                                  dest='abs',
                                  type=ranged_type(float, -80.0, 80.0),
                                  help='Absolute pressure offset')
    cal_write_parser.add_argument('--rel',
                                  dest='rel',
                                  type=ranged_type(float, -80.0, 80.0),
                                  help='Relative pressure offset')
    cal_write_parser.add_argument('--winddir',
                                  dest='winddir',
                                  type=ranged_type(float, -180, 180),
                                  help='Wind direction offset')
    add_common_args(cal_write_parser)
    cal_write_parser.set_defaults(func=dispatch_write)
    return cal_write_parser

def sensor_id_write_subparser(subparsers):
    """Define 'ecowitt write sensor-id' sub-subparser."""

    id_write_usage = f"""{Bcolors.BOLD}ecowitt write sensor-id --help
       ecowitt write sensor-id --ip-address=IP_ADDRESS [--port=PORT]
                                 [--wh65 ID] [--wh68 ID] [--wh80 ID] [--wh40 ID]
                                 [--wh25 ID] [--wh26 ID]
                                 [--wh31-1 ID] [--wh31-2 ID] [--wh31-3 ID] [--wh31-4 ID]
                                 [--wh31-5 ID] [--wh31-6 ID] [--wh31-7 ID] [--wh31-8 ID]
                                 [--wh51-1 ID] [--wh51-2 ID] [--wh51-3 ID] [--wh51-4 ID]
                                 [--wh51-5 ID] [--wh51-6 ID] [--wh51-7 ID] [--wh51-8 ID]
                                 [--wh41-1 ID] [--wh41-2 ID] [--wh41-3 ID] [--wh41-4 ID]
                                 [--wh57 ID]
                                 [--wh55-1 ID] [--wh55-2 ID] [--wh55-3 ID] [--wh55-4 ID]
                                 [--wh34-1 ID] [--wh34-2 ID] [--wh34-3 ID] [--wh34-4 ID]
                                 [--wh34-5 ID] [--wh34-6 ID] [--wh34-7 ID] [--wh34-8 ID]
                                 [--wh45 ID]
                                 [--wh35-1 ID] [--wh35-2 ID] [--wh35-3 ID] [--wh35-4 ID]
                                 [--wh35-5 ID] [--wh35-6 ID] [--wh35-7 ID] [--wh35-8 ID]
                                 [--wh90 ID]
                                 [--debug]
{Bcolors.ENDC}"""
    id_write_description = """Set sensor identification values. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    id_write_parser = subparsers.add_parser('sensor-id',
                                             usage=id_write_usage,
                                             description=id_write_description,
                                             help="Set sensor identification values.")
    id_write_parser.add_argument('--wh65',
                                 dest='eWH65_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH65 sensor identification value')
    id_write_parser.add_argument('--wh68',
                                 dest='eWH68_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH68 sensor identification value')
    id_write_parser.add_argument('--wh80',
                                 dest='eWH80_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH80 sensor identification value')
    id_write_parser.add_argument('--wh40',
                                 dest='eWH40_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH40 sensor identification value')
    id_write_parser.add_argument('--wh25',
                                 dest='eWH25_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH25 sensor identification value')
    id_write_parser.add_argument('--wh26',
                                 dest='eWH26_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH26 sensor identification value')
    id_write_parser.add_argument('--wh31-1',
                                 dest='eWH31_SENSORCH1',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 1 sensor identification value')
    id_write_parser.add_argument('--wh31-2',
                                 dest='eWH31_SENSORCH2',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 2 sensor identification value')
    id_write_parser.add_argument('--wh31-3',
                                 dest='eWH31_SENSORCH3',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 3 sensor identification value')
    id_write_parser.add_argument('--wh31-4',
                                 dest='eWH31_SENSORCH4',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 4 sensor identification value')
    id_write_parser.add_argument('--wh31-5',
                                 dest='eWH31_SENSORCH5',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 5 sensor identification value')
    id_write_parser.add_argument('--wh31-6',
                                 dest='eWH31_SENSORCH6',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 6 sensor identification value')
    id_write_parser.add_argument('--wh31-7',
                                 dest='eWH31_SENSORCH7',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 7 sensor identification value')
    id_write_parser.add_argument('--wh31-8',
                                 dest='eWH31_SENSORCH8',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH31 channel 8 sensor identification value')
    id_write_parser.add_argument('--wh51-1',
                                 dest='eWH51_SENSORCH1',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 1 sensor identification value')
    id_write_parser.add_argument('--wh51-2',
                                 dest='eWH51_SENSORCH2',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 2 sensor identification value')
    id_write_parser.add_argument('--wh51-3',
                                 dest='eWH51_SENSORCH3',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 3 sensor identification value')
    id_write_parser.add_argument('--wh51-4',
                                 dest='eWH51_SENSORCH4',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 4 sensor identification value')
    id_write_parser.add_argument('--wh51-5',
                                 dest='eWH51_SENSORCH5',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 5 sensor identification value')
    id_write_parser.add_argument('--wh51-6',
                                 dest='eWH51_SENSORCH6',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 6 sensor identification value')
    id_write_parser.add_argument('--wh51-7',
                                 dest='eWH51_SENSORCH7',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 7 sensor identification value')
    id_write_parser.add_argument('--wh51-8',
                                 dest='eWH51_SENSORCH8',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH51 channel 8 sensor identification value')
    id_write_parser.add_argument('--wh41-1',
                                 dest='eWH41_SENSORCH1',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH41 channel 1 sensor identification value')
    id_write_parser.add_argument('--wh41-2',
                                 dest='eWH41_SENSORCH2',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH41 channel 2 sensor identification value')
    id_write_parser.add_argument('--wh41-3',
                                 dest='eWH41_SENSORCH3',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH41 channel 3 sensor identification value')
    id_write_parser.add_argument('--wh41-4',
                                 dest='eWH41_SENSORCH4',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH41 channel 4 sensor identification value')
    id_write_parser.add_argument('--wh57',
                                 dest='eWH57_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH57 sensor identification value')
    id_write_parser.add_argument('--wh55-1',
                                 dest='eWH55_SENSORCH1',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH55 channel 1 sensor identification value')
    id_write_parser.add_argument('--wh55-2',
                                 dest='eWH55_SENSORCH2',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH55 channel 2 sensor identification value')
    id_write_parser.add_argument('--wh55-3',
                                 dest='eWH55_SENSORCH3',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH55 channel 3 sensor identification value')
    id_write_parser.add_argument('--wh55-4',
                                 dest='eWH55_SENSORCH4',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH55 channel 4 sensor identification value')
    id_write_parser.add_argument('--wh34-1',
                                 dest='eWH34_SENSORCH1',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 1 sensor identification value')
    id_write_parser.add_argument('--wh34-2',
                                 dest='eWH34_SENSORCH2',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 2 sensor identification value')
    id_write_parser.add_argument('--wh34-3',
                                 dest='eWH34_SENSORCH3',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 3 sensor identification value')
    id_write_parser.add_argument('--wh34-4',
                                 dest='eWH34_SENSORCH4',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 4 sensor identification value')
    id_write_parser.add_argument('--wh34-5',
                                 dest='eWH34_SENSORCH5',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 5 sensor identification value')
    id_write_parser.add_argument('--wh34-6',
                                 dest='eWH34_SENSORCH6',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 6 sensor identification value')
    id_write_parser.add_argument('--wh34-7',
                                 dest='eWH34_SENSORCH7',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 7 sensor identification value')
    id_write_parser.add_argument('--wh34-8',
                                 dest='eWH34_SENSORCH8',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH34 channel 8 sensor identification value')
    id_write_parser.add_argument('--wh45',
                                 dest='eWH45_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH45 sensor identification value')
    id_write_parser.add_argument('--wh35-1',
                                 dest='eWH35_SENSORCH1',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 1 sensor identification value')
    id_write_parser.add_argument('--wh35-2',
                                 dest='eWH35_SENSORCH2',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 2 sensor identification value')
    id_write_parser.add_argument('--wh35-3',
                                 dest='eWH35_SENSORCH3',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 3 sensor identification value')
    id_write_parser.add_argument('--wh35-4',
                                 dest='eWH35_SENSORCH4',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 4 sensor identification value')
    id_write_parser.add_argument('--wh35-5',
                                 dest='eWH35_SENSORCH5',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 5 sensor identification value')
    id_write_parser.add_argument('--wh35-6',
                                 dest='eWH35_SENSORCH6',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 6 sensor identification value')
    id_write_parser.add_argument('--wh35-7',
                                 dest='eWH35_SENSORCH7',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 7 sensor identification value')
    id_write_parser.add_argument('--wh35-8',
                                 dest='eWH35_SENSORCH8',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH35 channel 8 sensor identification value')
    id_write_parser.add_argument('--wh90',
                                 dest='eWH90_SENSOR',
                                 type=sensor_id_type(digits=8),
                                 metavar='ID',
                                 help='WH90 sensor identification value')
    add_common_args(id_write_parser)
    id_write_parser.set_defaults(func=dispatch_write)
    return id_write_parser


def pm25_offset_write_subparser(subparsers):
    """Define 'ecowitt write pm25-offset' sub-subparser."""

    pm25_write_usage = f"""{Bcolors.BOLD}ecowitt write pm25-offset --help
       ecowitt write pm25-offset --ip-address=IP_ADDRESS [--port=PORT]
                                 [--ch1 OFFSET] [--ch2 OFFSET] [--ch3 OFFSET] [--ch4 OFFSET]
                                 [--debug]
{Bcolors.ENDC}"""
    pm25_write_description = """Set PM2.5 sensor offset values. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    pm25_write_parser = subparsers.add_parser('pm25-offset',
                                              usage=pm25_write_usage,
                                              description=pm25_write_description,
                                              help="Set PM2.5 sensor offset values.")
    pm25_write_parser.add_argument('--ch1',
                                   dest='ch1',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 1 offset')
    pm25_write_parser.add_argument('--ch2',
                                   dest='ch2',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 2 offset')
    pm25_write_parser.add_argument('--ch3',
                                   dest='ch3',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 3 offset')
    pm25_write_parser.add_argument('--ch4',
                                   dest='ch4',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 4 offset')
    add_common_args(pm25_write_parser)
    pm25_write_parser.set_defaults(func=dispatch_write)
    return pm25_write_parser


def co2_offset_write_subparser(subparsers):
    """Define 'ecowitt write co2-offset' sub-subparser."""

    co2_write_usage = f"""{Bcolors.BOLD}ecowitt write co2-offset --help
       ecowitt write co2-offset --ip-address=IP_ADDRESS [--port=PORT]
                                [--co2 OFFSET] [--pm25 OFFSET] [--pm10 OFFSET]
                                [--debug]
{Bcolors.ENDC}"""
    co2_write_description = """Set WH45 sensor offset values. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    co2_write_parser = subparsers.add_parser('co2-offset',
                                             usage=co2_write_usage,
                                             description=co2_write_description,
                                             help="Set CO2 sensor offset values.")
    co2_write_parser.add_argument('--co2',
                                  dest='co2',
                                  type=ranged_type(float, -600, 10000),
                                  metavar='OFFSET',
                                  help='CO2 offset')
    co2_write_parser.add_argument('--pm25',
                                  dest='pm25',
                                  type=ranged_type(float, -20, 20),
                                  metavar='OFFSET',
                                  help='PM2.5 offset')
    co2_write_parser.add_argument('--pm10',
                                  dest='pm10',
                                  type=ranged_type(float, -20, 20),
                                  metavar='OFFSET',
                                  help='PM10 offset')
    add_common_args(co2_write_parser)
    co2_write_parser.set_defaults(func=dispatch_write)
    return co2_write_parser


def rain_write_subparser(subparsers):
    """Define 'ecowitt write rain' sub-subparser."""

    rain_write_usage = f"""{Bcolors.BOLD}ecowitt write rain --help
       ecowitt write rain --ip-address IP_ADDRESS [--port PORT]
                          [--day TOTAL] [--week TOTAL] [--month TOTAL] [--year TOTAL]
                          [--event TOTAL] [--rate RATE] [--gain GAIN]
                          [--p-day TOTAL] [--p-week TOTAL] [--p-month TOTAL] [--p-year TOTAL]
                          [--p-event TOTAL] [--p-rate RATE] [--p-gain0 GAIN] [--p-gain1 GAIN]
                          [--p-gain2 GAIN] [--p-gain3 GAIN] [--p-gain4 GAIN] [--p-gain5 GAIN]
                          [--p-gain6 GAIN] [--p-gain7 GAIN] [--p-gain8 GAIN] [--p-gain9 GAIN]
                          [--priority traditional | piezo] 
                          [--day-reset HOUR] [--week-reset DAY] [--year-reset MONTH]
                          [--debug]
{Bcolors.ENDC}"""
    rain_write_description = """Set rain related parameters. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    rain_write_parser = subparsers.add_parser('rain',
                                              usage=rain_write_usage,
                                              description=rain_write_description,
                                              help="Set rain related parameters.")
    rain_write_parser.add_argument('--day',
                                   dest='day',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='day rain total')
    rain_write_parser.add_argument('--week',
                                   dest='week',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='week rain total')
    rain_write_parser.add_argument('--month',
                                   dest='month',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='month rain total')
    rain_write_parser.add_argument('--year',
                                   dest='year',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='year rain total')
    rain_write_parser.add_argument('--event',
                                   dest='event',
                                   # TODO. Event is 2 bytes only so not 9999.9
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='rain event total')
    rain_write_parser.add_argument('--rate',
                                   dest='rate',
                                   type=ranged_type(float, 0, 6000.0),
                                   metavar='RATE',
                                   help='rain rate')
    rain_write_parser.add_argument('--gain',
                                   dest='gain',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='rain gain')
    rain_write_parser.add_argument('--p-day',
                                   dest='p_day',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='day piezo rain total')
    rain_write_parser.add_argument('--p-week',
                                   dest='p_week',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='week piezo rain total')
    rain_write_parser.add_argument('--p-month',
                                   dest='p_month',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='month piezo rain total')
    rain_write_parser.add_argument('--p-year',
                                   dest='p_year',
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='year rain total')
    rain_write_parser.add_argument('--p-event',
                                   dest='p_event',
                                   # TODO. Event is 2 bytes only so not 9999.9
                                   type=ranged_type(float, 0, 9999.9),
                                   metavar='TOTAL',
                                   help='piezo rain event total')
    rain_write_parser.add_argument('--p-rate',
                                   dest='p_rate',
                                   type=ranged_type(float, 0, 6000.0),
                                   metavar='RATE',
                                   help='piezo rain rate')
    rain_write_parser.add_argument('--gain0',
                                   dest='gain0',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain0')
    rain_write_parser.add_argument('--gain1',
                                   dest='gain1',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain1')
    rain_write_parser.add_argument('--gain2',
                                   dest='gain2',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain2')
    rain_write_parser.add_argument('--gain3',
                                   dest='gain3',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain3')
    rain_write_parser.add_argument('--gain4',
                                   dest='gain4',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain4')
    rain_write_parser.add_argument('--gain5',
                                   dest='gain5',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain5')
    rain_write_parser.add_argument('--gain6',
                                   dest='gain6',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain6')
    rain_write_parser.add_argument('--gain7',
                                   dest='gain7',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain7')
    rain_write_parser.add_argument('--gain8',
                                   dest='gain8',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain8')
    rain_write_parser.add_argument('--gain9',
                                   dest='gain9',
                                   type=ranged_type(float, 0.1, 5.0),
                                   metavar='GAIN',
                                   help='piezo rain gain9')
    rain_write_parser.add_argument('--priority',
                                   dest='priority',
                                   choices=('traditional', 'piezo'),
                                   type=lambda p: 1 if p.lower() == 'traditional' else 2,
                                   metavar='PRIORITY',
                                   help='rain priority, traditional = traditional tipping rain gauge, '
                                        'piezo = piezo rain gauge')
    rain_write_parser.add_argument('--day-reset',
                                   dest='day_reset',
                                   type=ranged_type(int, 0, 23),
                                   metavar='HOUR',
                                   help='daily rain reset time (hour)')
    rain_write_parser.add_argument('--week-reset',
                                   dest='week_reset',
                                   choices=('Sunday', 'Monday'),
                                   type=lambda p: 1 if p.lower() == 'monday' else 1,
                                   metavar='DAY',
                                   help='weekly rain reset time (day)')
    rain_write_parser.add_argument('--year-reset',
                                   dest='year_reset',
                                   type=ranged_type(int, 0, 11),
                                   metavar='MONTH',
                                   help='yearly rain reset time (month)')
    add_common_args(rain_write_parser)
    rain_write_parser.set_defaults(func=dispatch_write)
    return rain_write_parser


def system_write_subparser(subparsers):
    """Define 'ecowitt write system' sub-subparser."""

    conv_table = {'WH24': 0,
                  'WH65': 1}

    sys_write_usage = f"""{Bcolors.BOLD}ecowitt write system --help
       ecowitt write system --ip-address=IP_ADDRESS [--port=PORT]
                            [--sensor-type OFFSET] [--tz INDEX] [--dst enable | disable]
                            [--auto-tz enable | disable] [--debug]
{Bcolors.ENDC}"""
    sys_write_description = """Set system parameters. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    sys_write_parser = subparsers.add_parser('system',
                                              usage=sys_write_usage,
                                              description=sys_write_description,
                                              help="Set system parameters.")
    sys_write_parser.add_argument('--sensor-type',
                                  dest='sensor_type',
                                  type=sensor_type(['WH24', 'WH65']),
                                  metavar='SENSOR',
                                  help='sensor type, WH24 or WH65')
    sys_write_parser.add_argument('--tz',
                                   dest='timezone_index',
                                   type=ranged_type(int, 0, 255),
                                   metavar='INDEX',
                                   help='timezone index')
    sys_write_parser.add_argument('--dst',
                                  dest='dst_status',
                                  type=enable_disable_type(),
                                  metavar='disable | enable',
                                  help='DST status, enable or disable')
    sys_write_parser.add_argument('--auto-tz',
                                   dest='auto_timezone',
                                   type=enable_disable_type(('enable', 'disable')),
                                   metavar='disable | enable',
                                   help='automatically detect and set timezone')
    add_common_args(sys_write_parser)
    sys_write_parser.set_defaults(func=dispatch_write)
    return sys_write_parser


def rain_data_write_subparser(subparsers):
    """Define 'ecowitt write pm25-offset' sub-subparser."""

    rain_data_write_usage = f"""{Bcolors.BOLD}ecowitt write rain-data --help
       ecowitt write rain-data --ip-address=IP_ADDRESS [--port=PORT]
                               [--day TOTAL] [--week TOTAL] [--month TOTAL] [--year TOTAL]
                               [--debug]
{Bcolors.ENDC}"""
    rain_data_write_description = """Set rain data relted parameters. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    rain_data_write_parser = subparsers.add_parser('rain-data',
                                              usage=rain_data_write_usage,
                                              description=rain_data_write_description,
                                              help="Set rain data related paramters.")
    rain_data_write_parser.add_argument('--day',
                                        dest='t_day',
                                        type=ranged_type(float, 0, 9999.9),
                                        metavar='TOTAL',
                                        help='day rain total')
    rain_data_write_parser.add_argument('--week',
                                        dest='t_week',
                                        type=ranged_type(float, 0, 9999.9),
                                        metavar='TOTAL',
                                        help='week rain total')
    rain_data_write_parser.add_argument('--month',
                                        dest='t_month',
                                        type=ranged_type(float, 0, 9999.9),
                                        metavar='TOTAL',
                                        help='month rain total')
    rain_data_write_parser.add_argument('--year',
                                        dest='t_year',
                                        type=ranged_type(float, 0, 9999.9),
                                        metavar='TOTAL',
                                        help='year rain total')
    add_common_args(rain_data_write_parser)
    rain_data_write_parser.set_defaults(func=dispatch_write)
    return rain_data_write_parser

def soil_write_subparser(subparsers):
    """Define 'ecowitt write pm25-offset' sub-subparser."""

    pm25_write_usage = f"""{Bcolors.BOLD}ecowitt write pm25-offset --help
       ecowitt write pm25-offset --ip-address=IP_ADDRESS [--port=PORT]
                                 [--ch1 OFFSET] [--ch2 OFFSET] [--ch3 OFFSET] [--ch4 OFFSET]
                                 [--debug]
{Bcolors.ENDC}"""
    pm25_write_description = """Set PM2.5 sensor offset values. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    pm25_write_parser = subparsers.add_parser('pm25-offset',
                                              usage=pm25_write_usage,
                                              description=pm25_write_description,
                                              help="Set PM2.5 sensor offset values.")
    pm25_write_parser.add_argument('--ch1',
                                   dest='ch1',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 1 offset')
    pm25_write_parser.add_argument('--ch2',
                                   dest='ch2',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 2 offset')
    pm25_write_parser.add_argument('--ch3',
                                   dest='ch3',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 3 offset')
    pm25_write_parser.add_argument('--ch4',
                                   dest='ch4',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 4 offset')
    add_common_args(pm25_write_parser)
    pm25_write_parser.set_defaults(func=dispatch_write)
    return pm25_write_parser

def mulch_th_write_subparser(subparsers):
    """Define 'ecowitt write pm25-offset' sub-subparser."""

    pm25_write_usage = f"""{Bcolors.BOLD}ecowitt write pm25-offset --help
       ecowitt write pm25-offset --ip-address=IP_ADDRESS [--port=PORT]
                                 [--ch1 OFFSET] [--ch2 OFFSET] [--ch3 OFFSET] [--ch4 OFFSET]
                                 [--debug]
{Bcolors.ENDC}"""
    pm25_write_description = """Set PM2.5 sensor offset values. If a parameter
    is omitted the corresponding current gateway device parameter is left
    unchanged."""
    pm25_write_parser = subparsers.add_parser('pm25-offset',
                                              usage=pm25_write_usage,
                                              description=pm25_write_description,
                                              help="Set PM2.5 sensor offset values.")
    pm25_write_parser.add_argument('--ch1',
                                   dest='ch1',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 1 offset')
    pm25_write_parser.add_argument('--ch2',
                                   dest='ch2',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 2 offset')
    pm25_write_parser.add_argument('--ch3',
                                   dest='ch3',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 3 offset')
    pm25_write_parser.add_argument('--ch4',
                                   dest='ch4',
                                   type=ranged_type(float, -20, 20),
                                   metavar='OFFSET',
                                   help='PM2.5 channel 4 offset')
    add_common_args(pm25_write_parser)
    pm25_write_parser.set_defaults(func=dispatch_write)
    return pm25_write_parser

def mulch_t_write_subparser(subparsers):
    """Define 'ecowitt write mulch-t' sub-subparser."""

    mulch_t_write_usage = f"""{Bcolors.BOLD}ecowitt write mulch-t-offset --help
       ecowitt write pm25-offset --ip-address=IP_ADDRESS [--port=PORT]
                                 [--ch1 OFFSET] [--ch2 OFFSET] [--ch3 OFFSET] [--ch4 OFFSET]
                                 [--ch5 OFFSET] [--ch6 OFFSET] [--ch7 OFFSET] [--ch8 OFFSET]
                                 [--debug]
{Bcolors.ENDC}"""
    mulch_t_write_description = """Set multi-channel temperature sensor offset 
    values. If a parameter is omitted the corresponding current gateway device 
    parameter is left unchanged."""
    mulch_t_write_parser = subparsers.add_parser('mulch-t-offset',
                                                 usage=mulch_t_write_usage,
                                                 description=mulch_t_write_description,
                                                 help="Set Multi-channel temperature sensor offset values.")
    mulch_t_write_parser.add_argument('--ch1',
                                      dest='ITEM_TF_USR1',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 1 offset')
    mulch_t_write_parser.add_argument('--ch2',
                                      dest='ITEM_TF_USR2',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 2 offset')
    mulch_t_write_parser.add_argument('--ch3',
                                      dest='ITEM_TF_USR3',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 3 offset')
    mulch_t_write_parser.add_argument('--ch4',
                                      dest='ITEM_TF_USR4',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 4 offset')
    mulch_t_write_parser.add_argument('--ch5',
                                      dest='ITEM_TF_USR5',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 5 offset')
    mulch_t_write_parser.add_argument('--ch6',
                                      dest='ITEM_TF_USR6',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 6 offset')
    mulch_t_write_parser.add_argument('--ch7',
                                      dest='ITEM_TF_USR7',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 7 offset')
    mulch_t_write_parser.add_argument('--ch8',
                                      dest='ITEM_TF_USR8',
                                      type=ranged_type(float, -10, 10),
                                      metavar='OFFSET',
                                      help='Multi-channel temperature channel 8 offset')
    add_common_args(mulch_t_write_parser)
    mulch_t_write_parser.set_defaults(func=dispatch_write)
    return mulch_t_write_parser


def write_subparser(subparsers):
    """Define the 'ecowitt write' subcommand."""

    write_usage = f"""{Bcolors.BOLD}ecowitt write --help
       ecowitt write ecowitt --help
       ecowitt write wu --help
       ecowitt write wow --help
       ecowitt write wcloud --help
       ecowitt write custom --help
       ecowitt write calibration --help
       ecowitt write sensor-id --help
       ecowitt write pm25-offset --help
       ecowitt write co2-offset --help
       ecowitt write rain --help
       ecowitt write system --help
       ecowitt write rain-data --help
       ecowitt write soil-offset --help
       ecowitt write mulch-th-cal --help
       ecowitt write mulch-t-cal --help
{Bcolors.ENDC}"""
    write_description = """Set various Ecowitt gateway device configuration parameters."""
    write_parser = subparsers.add_parser('write',
                                         usage=write_usage,
                                         description=write_description,
                                         help="Set various Ecowitt gateway device configuration parameters.")
    # add a subparser to handle the various subcommands.
    write_subparsers = write_parser.add_subparsers(dest='write_subcommand',
                                                   title="Available subcommands")
    ecowitt_write_subparser(write_subparsers)
    wu_write_subparser(write_subparsers)
    wow_write_subparser(write_subparsers)
    wcloud_write_subparser(write_subparsers)
    custom_write_subparser(write_subparsers)
    cal_write_subparser(write_subparsers)
    sensor_id_write_subparser(write_subparsers)
    pm25_offset_write_subparser(write_subparsers)
    co2_offset_write_subparser(write_subparsers)
    rain_write_subparser(write_subparsers)
    system_write_subparser(write_subparsers)
    rain_data_write_subparser(write_subparsers)
    soil_write_subparser(write_subparsers)
    mulch_th_write_subparser(write_subparsers)
    mulch_t_write_subparser(write_subparsers)
    return write_parser


# To use this utility use the following command:
#
#   $ python3 /path/to/ecowitt.py --help
#
# The above command will display available command line options.

def main():

    # create a lookup table of functions used to determine if an action or
    # sub-subcommand was specified byt the user for a given subcommand
    exists_fns = {'get': get_action_exists,
                  'write': write_action_exists}
    # top level usage instructions
    usage = f"""{Bcolors.BOLD}%(prog)s --help
       %(prog)s --version
       %(prog)s --discover
                  [--debug] [--max-tries]
       %(prog)s get --help
       %(prog)s write --help{Bcolors.ENDC}
    """
    # top level description
    description = """Interact with an Ecowitt gateway device."""
    # obtain an ArgumentParser object
    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    # add argument definitions
    parser.add_argument('--version',
                        dest='version',
                        action='store_true',
                        help='display the Ecowitt utility version number')
    parser.add_argument('--discover',
                        dest='discover',
                        action='store_true',
                        help='discover devices and display device IP address '
                             'and listening port')
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='display additional debug information')
    # add a subparser to handle the various subcommands.
    subparsers = parser.add_subparsers(dest='subcommand',
                                       title="Available subcommands")
    # maintain a dict of our subparsers so we can easily display the subparser
    # help/usage
    parsers = dict()
    # create each subparser and add to our parser dict
    parsers['get'] = get_subparser(subparsers)
    parsers['write'] = write_subparser(subparsers)
    # parse the arguments
    namespace = parser.parse_args()
    print("namespace=%s" % (namespace,))
#    exit(1)
    # inform the user if debug is set
    if int(namespace.debug):
        print(f"debug is set")
    # process any top level non-subcommand options
    if namespace.version:
        # display the utility version and exit
        print(f"{NAME} version {VERSION}")
        sys.exit(0)
    if namespace.discover:
        # discover gateway devices and display the results
        # first, make sure we have a device IP address
        if namespace.device_ip_address is not None:
            # get a DirectGateway object
            direct_gw = DirectGateway(namespace)
            # discover any gateway devices and display the results
            direct_gw.display_discovered_devices()
            exit(0)
        else:
            print()
            print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: device IP address not specified")
            print()
            parser.print_help()
            exit(1)
    # if we made it here we must have a subcommand
    # do we have a subcommand function we can call
    if hasattr(namespace, 'subcommand'):
        # we have a subcommand, subcommands require either an action or a
        # sub-subcommand
        if exists_fns[namespace.subcommand](namespace):
            # the current subcommand has at least one action or sub-subcommand,
            # actions and sub-subcommands require a device IP address, so make
            # sure we have one
            if namespace.device_ip_address is not None:
                # now act on the subcommand
                namespace.func(namespace)
            else:
                # we do not have an IP address, advise the user, display our
                # help and exit
                print()
                print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: device IP address not specified")
                print()
                parsers[namespace.subcommand].print_help()
                exit(1)
        else:
            # we do not have an action or sub-subcommand, advise the user,
            # display our help and exit
            print()
            print(f"{Bcolors.BOLD}Error{Bcolors.ENDC}: no action or subcommand specified")
            print()
            parsers[namespace.subcommand].print_help()
            exit(1)

    else:
        # Only non-subcommands do not have a subcommand function, but we have
        # already processed all non-subcommands. So display our help and exit.
        print()
        parser.print_help()
        exit(0)


if __name__ == '__main__':
    main()