#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
backfill.py

Development of a web API based backfill for the Ecowitt gateway driver.

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

Version: 0.1.0                                     Date: 2 August 2024

Revision History
    2 August 2024          `v0.1.0
        - started development


"""
# Python imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import calendar
from datetime import datetime

import configobj
import json
import re
import socket
import struct
import threading
import time
from operator import itemgetter

# Python 2/3 compatibility shims
import six
from six.moves import StringIO
from six.moves import urllib
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import urlencode


import sys

# WeeWX imports
import weecfg
import weeutil.weeutil
import weewx.drivers
import weewx.engine
import weewx.units
import weewx.wxformulas
from weeutil.weeutil import timestamp_to_string

# import/setup logging, WeeWX v3 is syslog based but WeeWX v4 is logging based,
# try v4 logging and if it fails use v3 logging
try:
    # WeeWX4 logging
    import logging
    from weeutil.logger import log_traceback

    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)

    # log_traceback() generates the same output but the signature and code is
    # different between v3 and v4. We only need log_traceback at the log.error
    # level so define a suitable wrapper function.
    def log_traceback_critical(prefix=''):
        log_traceback(log.critical, prefix=prefix)

    def log_traceback_error(prefix=''):
        log_traceback(log.error, prefix=prefix)

    def log_traceback_debug(prefix=''):
        log_traceback(log.debug, prefix=prefix)

except ImportError:
    # WeeWX legacy (v3) logging via syslog
    import syslog
    from weeutil.weeutil import log_traceback

    def logmsg(level, msg):
        syslog.syslog(level, 'gw1000: %s' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)

    # log_traceback() generates the same output but the signature and code is
    # different between v3 and v4. We only need log_traceback at the log.error
    # level so define a suitable wrapper function.
    def log_traceback_critical(prefix=''):
        log_traceback(prefix=prefix, loglevel=syslog.LOG_CRIT)

    def log_traceback_error(prefix=''):
        log_traceback(prefix=prefix, loglevel=syslog.LOG_ERR)

    def log_traceback_debug(prefix=''):
        log_traceback(prefix=prefix, loglevel=syslog.LOG_DEBUG)


# default socket timeout
default_socket_timeout = 2
# default retry/wait time
default_retry_wait = 10
# default max tries when polling the API
default_max_tries = 3
# default battery state filtering
default_show_battery = False
# For packet unit conversion to work correctly each possible WeeWX field needs
# to be assigned to a unit group. This is normally already taken care of for
# WeeWX fields that are part of the in-use database schema; however, an Ecowitt
# Gateway based system may include additional fields not included in the
# schema. We cannot know what unit group the user may intend for each WeeWX
# field in a custom field map, but we can take care of the default field map.

# define the default groups to use for WeeWX fields in the default field map
# but not in the (WeeWX default) wview_extended schema
default_groups = {
    'relbarometer': 'group_pressure',
    'luminosity': 'group_illuminance',
    'uvradiation': 'group_radiation',
    'extraHumid17': 'group_percent',
    'extraTemp9': 'group_temperature',
    'extraTemp10': 'group_temperature',
    'extraTemp11': 'group_temperature',
    'extraTemp12': 'group_temperature',
    'extraTemp13': 'group_temperature',
    'extraTemp14': 'group_temperature',
    'extraTemp15': 'group_temperature',
    'extraTemp16': 'group_temperature',
    'extraTemp17': 'group_temperature',
    'pm2_52': 'group_concentration',
    'pm2_53': 'group_concentration',
    'pm2_54': 'group_concentration',
    'pm2_55': 'group_concentration',
    'pm4_0': 'group_concentration',
    'soilTemp5': 'group_temperature',
    'soilMoist5': 'group_percent',
    'soilTemp6': 'group_temperature',
    'soilMoist6': 'group_percent',
    'soilTemp7': 'group_temperature',
    'soilMoist7': 'group_percent',
    'soilTemp8': 'group_temperature',
    'soilMoist8': 'group_percent',
    'soilTemp9': 'group_temperature',
    'soilMoist9': 'group_percent',
    'soilTemp10': 'group_temperature',
    'soilMoist10': 'group_percent',
    'soilTemp11': 'group_temperature',
    'soilMoist11': 'group_percent',
    'soilTemp12': 'group_temperature',
    'soilMoist12': 'group_percent',
    'soilTemp13': 'group_temperature',
    'soilMoist13': 'group_percent',
    'soilTemp14': 'group_temperature',
    'soilMoist14': 'group_percent',
    'soilTemp15': 'group_temperature',
    'soilMoist15': 'group_percent',
    'soilTemp16': 'group_temperature',
    'soilMoist16': 'group_percent',
    'pm1_0_24h_avg': 'group_concentration',
    'pm2_51_24h_avg': 'group_concentration',
    'pm2_52_24h_avg': 'group_concentration',
    'pm2_53_24h_avg': 'group_concentration',
    'pm2_54_24h_avg': 'group_concentration',
    'pm2_55_24h_avg': 'group_concentration',
    'pm4_0_24h_avg': 'group_concentration',
    'pm10_24h_avg': 'group_concentration',
    'co2_24h_avg': 'group_fraction',
    'leak1': 'group_count',
    'leak2': 'group_count',
    'leak3': 'group_count',
    'leak4': 'group_count',
    'lightning_last_det_time': 'group_time',
    'lightningcount': 'group_count',
    't_raingain': 'group_rain',
    'totalRain': 'group_rain',
    'weekRain': 'group_rain',
    'p_rain': 'group_rain',
    'p_rainRate': 'group_rainrate',
    'p_stormRain': 'group_rain',
    'p_dayRain': 'group_rain',
    'p_weekRain': 'group_rain',
    'p_monthRain': 'group_rain',
    'p_yearRain': 'group_rain',
    'daymaxwind': 'group_speed',
    'leafWet3': 'group_percent',
    'leafWet4': 'group_percent',
    'leafWet5': 'group_percent',
    'leafWet6': 'group_percent',
    'leafWet7': 'group_percent',
    'leafWet8': 'group_percent',
    'heap_free': 'group_data',
    'wh40_batt': 'group_volt',
    'wh26_batt': 'group_count',
    'wh25_batt': 'group_count',
    'wh24_batt': 'group_count',
    'wh65_batt': 'group_count',
    'wh32_batt': 'group_count',
    'wh31_ch1_batt': 'group_count',
    'wh31_ch2_batt': 'group_count',
    'wh31_ch3_batt': 'group_count',
    'wh31_ch4_batt': 'group_count',
    'wh31_ch5_batt': 'group_count',
    'wh31_ch6_batt': 'group_count',
    'wh31_ch7_batt': 'group_count',
    'wh31_ch8_batt': 'group_count',
    'wn34_ch1_batt': 'group_volt',
    'wn34_ch2_batt': 'group_volt',
    'wn34_ch3_batt': 'group_volt',
    'wn34_ch4_batt': 'group_volt',
    'wn34_ch5_batt': 'group_volt',
    'wn34_ch6_batt': 'group_volt',
    'wn34_ch7_batt': 'group_volt',
    'wn34_ch8_batt': 'group_volt',
    'wn35_ch1_batt': 'group_volt',
    'wn35_ch2_batt': 'group_volt',
    'wn35_ch3_batt': 'group_volt',
    'wn35_ch4_batt': 'group_volt',
    'wn35_ch5_batt': 'group_volt',
    'wn35_ch6_batt': 'group_volt',
    'wn35_ch7_batt': 'group_volt',
    'wn35_ch8_batt': 'group_volt',
    'wh41_ch1_batt': 'group_count',
    'wh41_ch2_batt': 'group_count',
    'wh41_ch3_batt': 'group_count',
    'wh41_ch4_batt': 'group_count',
    'wh45_batt': 'group_count',
    'wh46_batt': 'group_count',
    'wh51_ch1_batt': 'group_volt',
    'wh51_ch2_batt': 'group_volt',
    'wh51_ch3_batt': 'group_volt',
    'wh51_ch4_batt': 'group_volt',
    'wh51_ch5_batt': 'group_volt',
    'wh51_ch6_batt': 'group_volt',
    'wh51_ch7_batt': 'group_volt',
    'wh51_ch8_batt': 'group_volt',
    'wh51_ch9_batt': 'group_volt',
    'wh51_ch10_batt': 'group_volt',
    'wh51_ch11_batt': 'group_volt',
    'wh51_ch12_batt': 'group_volt',
    'wh51_ch13_batt': 'group_volt',
    'wh51_ch14_batt': 'group_volt',
    'wh51_ch15_batt': 'group_volt',
    'wh51_ch16_batt': 'group_volt',
    'wh55_ch1_batt': 'group_count',
    'wh55_ch2_batt': 'group_count',
    'wh55_ch3_batt': 'group_count',
    'wh55_ch4_batt': 'group_count',
    'wh57_batt': 'group_count',
    'wh68_batt': 'group_volt',
    'ws80_batt': 'group_volt',
    'ws85_batt': 'group_volt',
    'ws90_batt': 'group_volt',
    'wh40_sig': 'group_count',
    'wh26_sig': 'group_count',
    'wh25_sig': 'group_count',
    'wh24_sig': 'group_count',
    'wh65_sig': 'group_count',
    'wh32_sig': 'group_count',
    'wh31_ch1_sig': 'group_count',
    'wh31_ch2_sig': 'group_count',
    'wh31_ch3_sig': 'group_count',
    'wh31_ch4_sig': 'group_count',
    'wh31_ch5_sig': 'group_count',
    'wh31_ch6_sig': 'group_count',
    'wh31_ch7_sig': 'group_count',
    'wh31_ch8_sig': 'group_count',
    'wn34_ch1_sig': 'group_count',
    'wn34_ch2_sig': 'group_count',
    'wn34_ch3_sig': 'group_count',
    'wn34_ch4_sig': 'group_count',
    'wn34_ch5_sig': 'group_count',
    'wn34_ch6_sig': 'group_count',
    'wn34_ch7_sig': 'group_count',
    'wn34_ch8_sig': 'group_count',
    'wn35_ch1_sig': 'group_count',
    'wn35_ch2_sig': 'group_count',
    'wn35_ch3_sig': 'group_count',
    'wn35_ch4_sig': 'group_count',
    'wn35_ch5_sig': 'group_count',
    'wn35_ch6_sig': 'group_count',
    'wn35_ch7_sig': 'group_count',
    'wn35_ch8_sig': 'group_count',
    'wh41_ch1_sig': 'group_count',
    'wh41_ch2_sig': 'group_count',
    'wh41_ch3_sig': 'group_count',
    'wh41_ch4_sig': 'group_count',
    'wh45_sig': 'group_count',
    'wh46_sig': 'group_count',
    'wh51_ch1_sig': 'group_count',
    'wh51_ch2_sig': 'group_count',
    'wh51_ch3_sig': 'group_count',
    'wh51_ch4_sig': 'group_count',
    'wh51_ch5_sig': 'group_count',
    'wh51_ch6_sig': 'group_count',
    'wh51_ch7_sig': 'group_count',
    'wh51_ch8_sig': 'group_count',
    'wh51_ch9_sig': 'group_count',
    'wh51_ch10_sig': 'group_count',
    'wh51_ch11_sig': 'group_count',
    'wh51_ch12_sig': 'group_count',
    'wh51_ch13_sig': 'group_count',
    'wh51_ch14_sig': 'group_count',
    'wh51_ch15_sig': 'group_count',
    'wh51_ch16_sig': 'group_count',
    'wh55_ch1_sig': 'group_count',
    'wh55_ch2_sig': 'group_count',
    'wh55_ch3_sig': 'group_count',
    'wh55_ch4_sig': 'group_count',
    'wh57_sig': 'group_count',
    'wh68_sig': 'group_count',
    'ws80_sig': 'group_count',
    'ws85_sig': 'group_count',
    'ws90_sig': 'group_count'
}


# ============================================================================
#                         Gateway API error classes
# ============================================================================

class UnknownApiCommand(Exception):
    """Exception raised when an unknown API command was selected or an
    otherwise valid API response has an unexpected command code."""


class UnknownHttpCommand(Exception):
    """Exception raised when an unknown HTTP command was selected."""


class InvalidApiResponseError(Exception):
    """Exception raised when an API request response is invalid."""


class ApiResponseError(Exception):
    """Exception raised when a valid API response is received but the response
    contains a non-zero error code."""


class DebugOptions(object):
    """Class to simplify use and handling of device debug options."""

    debug_groups = ('rain', 'wind', 'loop', 'sensors')

    def __init__(self, gw_config_dict):
        # get any specific debug settings
        # rain
        self.debug_rain = weeutil.weeutil.tobool(gw_config_dict.get('debug_rain',
                                                                    False))
        # wind
        self.debug_wind = weeutil.weeutil.tobool(gw_config_dict.get('debug_wind',
                                                                    False))
        # loop data
        self.debug_loop = weeutil.weeutil.tobool(gw_config_dict.get('debug_loop',
                                                                    False))
        # sensors
        self.debug_sensors = weeutil.weeutil.tobool(gw_config_dict.get('debug_sensors',
                                                                       False))

    @property
    def rain(self):
        """Are we debugging rain data processing."""

        return self.debug_rain

    @property
    def wind(self):
        """Are we debugging wind data processing."""

        return self.debug_wind

    @property
    def loop(self):
        """Are we debugging loop data processing."""

        return self.debug_loop

    @property
    def sensors(self):
        """Are we debugging sensor processing."""

        return self.debug_sensors

    @property
    def any(self):
        """Are we performing any debugging."""

        for debug_group in self.debug_groups:
            if getattr(self, debug_group):
                return True
        else:
            return False


d = """{
    "code": 0,
    "msg": "success",
    "time": "1722787844",
    "data": {
        "outdoor": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "16.8",
                    "1722764700": "16.8",
                    "1722765000": "16.7",
                    "1722765300": "16.7",
                    "1722765600": "16.7",
                    "1722765900": "16.7",
                    "1722766200": "16.7",
                    "1722766500": "16.6",
                    "1722766800": "16.6",
                    "1722767100": "16.5",
                    "1722767400": "16.4",
                    "1722767700": "16.4",
                    "1722768000": "16.3",
                    "1722768300": "16.2",
                    "1722768600": "16.2",
                    "1722768900": "16.3",
                    "1722769200": "16.2",
                    "1722769500": "16.3",
                    "1722769800": "16.3",
                    "1722770100": "16.3",
                    "1722770400": "16.3",
                    "1722770700": "16.3",
                    "1722771000": "16.2",
                    "1722771300": "16.1",
                    "1722771600": "16.1",
                    "1722771900": "16.0",
                    "1722772200": "16.0",
                    "1722772500": "16.0",
                    "1722772800": "15.9",
                    "1722773100": "15.9",
                    "1722773400": "15.9",
                    "1722773700": "15.8",
                    "1722774000": "15.8",
                    "1722774300": "15.7",
                    "1722774600": "15.6",
                    "1722774900": "15.6",
                    "1722775200": "15.5",
                    "1722775500": "15.5",
                    "1722775800": "15.6",
                    "1722776100": "15.5",
                    "1722776400": "15.5",
                    "1722776700": "15.5",
                    "1722777000": "15.5",
                    "1722777300": "15.5",
                    "1722777600": "15.4",
                    "1722777900": "15.4",
                    "1722778200": "15.3",
                    "1722778500": "15.3",
                    "1722778800": "15.2",
                    "1722779100": "15.1",
                    "1722779400": "15.0",
                    "1722779700": "14.9",
                    "1722780000": "14.9",
                    "1722780300": "14.8",
                    "1722780600": "14.7",
                    "1722780900": "14.7",
                    "1722781200": "14.6",
                    "1722781500": "14.6",
                    "1722781800": "14.6",
                    "1722782100": "14.6",
                    "1722782400": "14.6",
                    "1722782700": "14.5",
                    "1722783000": "14.5",
                    "1722783300": "14.5",
                    "1722783600": "14.5",
                    "1722783900": "14.5",
                    "1722784200": "14.5",
                    "1722784500": "14.4",
                    "1722784800": "14.4",
                    "1722785100": "14.3",
                    "1722785400": "14.2",
                    "1722785700": "14.3",
                    "1722786000": "14.2",
                    "1722786300": "14.1",
                    "1722786600": "14.0",
                    "1722786900": "14.0",
                    "1722787200": "13.8"
                }
            },
            "feels_like": {
                "unit": "℃",
                "list": {
                    "1722764400": "16.8",
                    "1722764700": "16.8",
                    "1722765000": "16.7",
                    "1722765300": "16.7",
                    "1722765600": "16.7",
                    "1722765900": "16.7",
                    "1722766200": "16.7",
                    "1722766500": "16.7",
                    "1722766800": "16.6",
                    "1722767100": "16.5",
                    "1722767400": "16.4",
                    "1722767700": "16.4",
                    "1722768000": "16.3",
                    "1722768300": "16.2",
                    "1722768600": "16.2",
                    "1722768900": "16.3",
                    "1722769200": "16.2",
                    "1722769500": "16.3",
                    "1722769800": "16.3",
                    "1722770100": "16.3",
                    "1722770400": "16.3",
                    "1722770700": "16.3",
                    "1722771000": "16.2",
                    "1722771300": "16.1",
                    "1722771600": "16.1",
                    "1722771900": "16.0",
                    "1722772200": "16.0",
                    "1722772500": "16.0",
                    "1722772800": "15.9",
                    "1722773100": "15.9",
                    "1722773400": "15.9",
                    "1722773700": "15.8",
                    "1722774000": "15.8",
                    "1722774300": "15.7",
                    "1722774600": "15.6",
                    "1722774900": "15.6",
                    "1722775200": "15.5",
                    "1722775500": "15.5",
                    "1722775800": "15.6",
                    "1722776100": "15.5",
                    "1722776400": "15.5",
                    "1722776700": "15.5",
                    "1722777000": "15.5",
                    "1722777300": "15.5",
                    "1722777600": "15.4",
                    "1722777900": "15.4",
                    "1722778200": "15.3",
                    "1722778500": "15.3",
                    "1722778800": "15.2",
                    "1722779100": "15.1",
                    "1722779400": "15.0",
                    "1722779700": "14.9",
                    "1722780000": "14.9",
                    "1722780300": "14.8",
                    "1722780600": "14.7",
                    "1722780900": "14.7",
                    "1722781200": "14.7",
                    "1722781500": "14.6",
                    "1722781800": "14.6",
                    "1722782100": "14.6",
                    "1722782400": "14.6",
                    "1722782700": "14.5",
                    "1722783000": "14.5",
                    "1722783300": "14.5",
                    "1722783600": "14.5",
                    "1722783900": "14.5",
                    "1722784200": "14.5",
                    "1722784500": "14.4",
                    "1722784800": "14.3",
                    "1722785100": "14.3",
                    "1722785400": "14.2",
                    "1722785700": "14.3",
                    "1722786000": "14.2",
                    "1722786300": "14.1",
                    "1722786600": "14.0",
                    "1722786900": "14.0",
                    "1722787200": "13.8"
                }
            },
            "app_temp": {
                "unit": "℃",
                "list": {
                    "1722764400": "17.1",
                    "1722764700": "17.1",
                    "1722765000": "17.0",
                    "1722765300": "17.0",
                    "1722765600": "17.0",
                    "1722765900": "17.0",
                    "1722766200": "17.0",
                    "1722766500": "16.9",
                    "1722766800": "16.9",
                    "1722767100": "16.8",
                    "1722767400": "16.7",
                    "1722767700": "16.8",
                    "1722768000": "16.6",
                    "1722768300": "16.2",
                    "1722768600": "16.3",
                    "1722768900": "16.6",
                    "1722769200": "16.4",
                    "1722769500": "16.6",
                    "1722769800": "16.6",
                    "1722770100": "16.6",
                    "1722770400": "16.6",
                    "1722770700": "16.6",
                    "1722771000": "16.5",
                    "1722771300": "16.4",
                    "1722771600": "16.4",
                    "1722771900": "16.4",
                    "1722772200": "16.3",
                    "1722772500": "16.3",
                    "1722772800": "16.1",
                    "1722773100": "16.0",
                    "1722773400": "15.8",
                    "1722773700": "16.0",
                    "1722774000": "16.0",
                    "1722774300": "15.9",
                    "1722774600": "15.8",
                    "1722774900": "15.8",
                    "1722775200": "15.7",
                    "1722775500": "15.7",
                    "1722775800": "15.8",
                    "1722776100": "15.7",
                    "1722776400": "15.6",
                    "1722776700": "15.7",
                    "1722777000": "15.7",
                    "1722777300": "15.7",
                    "1722777600": "15.6",
                    "1722777900": "15.6",
                    "1722778200": "15.5",
                    "1722778500": "15.4",
                    "1722778800": "15.3",
                    "1722779100": "15.2",
                    "1722779400": "15.1",
                    "1722779700": "15.0",
                    "1722780000": "14.9",
                    "1722780300": "14.8",
                    "1722780600": "14.7",
                    "1722780900": "14.5",
                    "1722781200": "14.5",
                    "1722781500": "14.6",
                    "1722781800": "14.7",
                    "1722782100": "14.5",
                    "1722782400": "14.6",
                    "1722782700": "14.5",
                    "1722783000": "14.5",
                    "1722783300": "14.5",
                    "1722783600": "14.4",
                    "1722783900": "14.5",
                    "1722784200": "14.5",
                    "1722784500": "14.4",
                    "1722784800": "14.3",
                    "1722785100": "14.3",
                    "1722785400": "14.2",
                    "1722785700": "14.2",
                    "1722786000": "13.8",
                    "1722786300": "13.9",
                    "1722786600": "13.9",
                    "1722786900": "13.9",
                    "1722787200": "13.5"
                }
            },
            "dew_point": {
                "unit": "℃",
                "list": {
                    "1722764400": "10.9",
                    "1722764700": "10.9",
                    "1722765000": "11.0",
                    "1722765300": "11.0",
                    "1722765600": "11.0",
                    "1722765900": "11.0",
                    "1722766200": "11.0",
                    "1722766500": "10.9",
                    "1722766800": "10.9",
                    "1722767100": "11.0",
                    "1722767400": "10.9",
                    "1722767700": "11.0",
                    "1722768000": "10.9",
                    "1722768300": "10.9",
                    "1722768600": "10.9",
                    "1722768900": "11.1",
                    "1722769200": "10.9",
                    "1722769500": "11.0",
                    "1722769800": "11.1",
                    "1722770100": "11.1",
                    "1722770400": "11.1",
                    "1722770700": "11.0",
                    "1722771000": "10.9",
                    "1722771300": "10.9",
                    "1722771600": "11.1",
                    "1722771900": "11.0",
                    "1722772200": "10.9",
                    "1722772500": "10.9",
                    "1722772800": "10.9",
                    "1722773100": "10.9",
                    "1722773400": "10.9",
                    "1722773700": "10.8",
                    "1722774000": "10.8",
                    "1722774300": "10.6",
                    "1722774600": "10.7",
                    "1722774900": "10.8",
                    "1722775200": "10.7",
                    "1722775500": "10.7",
                    "1722775800": "10.8",
                    "1722776100": "10.7",
                    "1722776400": "10.7",
                    "1722776700": "10.7",
                    "1722777000": "10.7",
                    "1722777300": "10.6",
                    "1722777600": "10.6",
                    "1722777900": "10.6",
                    "1722778200": "10.5",
                    "1722778500": "10.4",
                    "1722778800": "10.3",
                    "1722779100": "10.3",
                    "1722779400": "10.2",
                    "1722779700": "10.1",
                    "1722780000": "10.1",
                    "1722780300": "10.0",
                    "1722780600": "9.9",
                    "1722780900": "9.9",
                    "1722781200": "9.9",
                    "1722781500": "10.0",
                    "1722781800": "10.0",
                    "1722782100": "10.0",
                    "1722782400": "10.0",
                    "1722782700": "10.0",
                    "1722783000": "9.9",
                    "1722783300": "9.9",
                    "1722783600": "9.9",
                    "1722783900": "9.9",
                    "1722784200": "9.9",
                    "1722784500": "9.9",
                    "1722784800": "9.8",
                    "1722785100": "9.9",
                    "1722785400": "9.8",
                    "1722785700": "9.9",
                    "1722786000": "9.9",
                    "1722786300": "9.7",
                    "1722786600": "9.7",
                    "1722786900": "9.7",
                    "1722787200": "9.6"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "68",
                    "1722764700": "68",
                    "1722765000": "69",
                    "1722765300": "69",
                    "1722765600": "69",
                    "1722765900": "69",
                    "1722766200": "69",
                    "1722766500": "69",
                    "1722766800": "69",
                    "1722767100": "70",
                    "1722767400": "70",
                    "1722767700": "70",
                    "1722768000": "70",
                    "1722768300": "71",
                    "1722768600": "71",
                    "1722768900": "71",
                    "1722769200": "71",
                    "1722769500": "71",
                    "1722769800": "71",
                    "1722770100": "71",
                    "1722770400": "71",
                    "1722770700": "71",
                    "1722771000": "71",
                    "1722771300": "71",
                    "1722771600": "72",
                    "1722771900": "72",
                    "1722772200": "72",
                    "1722772500": "72",
                    "1722772800": "72",
                    "1722773100": "72",
                    "1722773400": "72",
                    "1722773700": "72",
                    "1722774000": "72",
                    "1722774300": "72",
                    "1722774600": "73",
                    "1722774900": "73",
                    "1722775200": "73",
                    "1722775500": "73",
                    "1722775800": "73",
                    "1722776100": "73",
                    "1722776400": "73",
                    "1722776700": "73",
                    "1722777000": "73",
                    "1722777300": "73",
                    "1722777600": "73",
                    "1722777900": "73",
                    "1722778200": "73",
                    "1722778500": "73",
                    "1722778800": "73",
                    "1722779100": "73",
                    "1722779400": "73",
                    "1722779700": "73",
                    "1722780000": "73",
                    "1722780300": "73",
                    "1722780600": "73",
                    "1722780900": "73",
                    "1722781200": "73",
                    "1722781500": "74",
                    "1722781800": "74",
                    "1722782100": "74",
                    "1722782400": "74",
                    "1722782700": "74",
                    "1722783000": "74",
                    "1722783300": "74",
                    "1722783600": "74",
                    "1722783900": "74",
                    "1722784200": "74",
                    "1722784500": "74",
                    "1722784800": "74",
                    "1722785100": "75",
                    "1722785400": "75",
                    "1722785700": "75",
                    "1722786000": "75",
                    "1722786300": "75",
                    "1722786600": "75",
                    "1722786900": "75",
                    "1722787200": "75"
                }
            }
        },
        "indoor": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "21.1",
                    "1722764700": "21.1",
                    "1722765000": "21.1",
                    "1722765300": "21.1",
                    "1722765600": "21.1",
                    "1722765900": "21.1",
                    "1722766200": "21.1",
                    "1722766500": "21.1",
                    "1722766800": "21.1",
                    "1722767100": "21.1",
                    "1722767400": "21.1",
                    "1722767700": "21.1",
                    "1722768000": "21.0",
                    "1722768300": "21.0",
                    "1722768600": "21.0",
                    "1722768900": "21.0",
                    "1722769200": "20.9",
                    "1722769500": "21.0",
                    "1722769800": "21.0",
                    "1722770100": "20.9",
                    "1722770400": "20.9",
                    "1722770700": "20.9",
                    "1722771000": "20.9",
                    "1722771300": "20.9",
                    "1722771600": "20.9",
                    "1722771900": "20.7",
                    "1722772200": "20.8",
                    "1722772500": "20.8",
                    "1722772800": "20.7",
                    "1722773100": "20.7",
                    "1722773400": "20.7",
                    "1722773700": "20.7",
                    "1722774000": "20.7",
                    "1722774300": "20.6",
                    "1722774600": "20.6",
                    "1722774900": "20.5",
                    "1722775200": "20.5",
                    "1722775500": "20.5",
                    "1722775800": "20.5",
                    "1722776100": "20.4",
                    "1722776400": "20.4",
                    "1722776700": "20.4",
                    "1722777000": "20.4",
                    "1722777300": "20.4",
                    "1722777600": "20.4",
                    "1722777900": "20.4",
                    "1722778200": "20.3",
                    "1722778500": "20.3",
                    "1722778800": "20.3",
                    "1722779100": "20.3",
                    "1722779400": "20.2",
                    "1722779700": "20.2",
                    "1722780000": "20.2",
                    "1722780300": "20.1",
                    "1722780600": "20.1",
                    "1722780900": "20.1",
                    "1722781200": "20.1",
                    "1722781500": "20.0",
                    "1722781800": "20.0",
                    "1722782100": "20.0",
                    "1722782400": "20.0",
                    "1722782700": "20.0",
                    "1722783000": "20.0",
                    "1722783300": "19.9",
                    "1722783600": "19.9",
                    "1722783900": "19.9",
                    "1722784200": "19.9",
                    "1722784500": "19.8",
                    "1722784800": "19.9",
                    "1722785100": "19.8",
                    "1722785400": "19.8",
                    "1722785700": "19.8",
                    "1722786000": "19.8",
                    "1722786300": "19.7",
                    "1722786600": "19.7",
                    "1722786900": "19.7",
                    "1722787200": "19.7"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "57",
                    "1722764700": "57",
                    "1722765000": "57",
                    "1722765300": "57",
                    "1722765600": "57",
                    "1722765900": "57",
                    "1722766200": "57",
                    "1722766500": "57",
                    "1722766800": "57",
                    "1722767100": "57",
                    "1722767400": "57",
                    "1722767700": "57",
                    "1722768000": "57",
                    "1722768300": "57",
                    "1722768600": "57",
                    "1722768900": "57",
                    "1722769200": "57",
                    "1722769500": "57",
                    "1722769800": "57",
                    "1722770100": "57",
                    "1722770400": "57",
                    "1722770700": "57",
                    "1722771000": "57",
                    "1722771300": "57",
                    "1722771600": "58",
                    "1722771900": "58",
                    "1722772200": "58",
                    "1722772500": "58",
                    "1722772800": "58",
                    "1722773100": "58",
                    "1722773400": "58",
                    "1722773700": "58",
                    "1722774000": "58",
                    "1722774300": "58",
                    "1722774600": "58",
                    "1722774900": "58",
                    "1722775200": "58",
                    "1722775500": "58",
                    "1722775800": "58",
                    "1722776100": "58",
                    "1722776400": "58",
                    "1722776700": "58",
                    "1722777000": "57",
                    "1722777300": "57",
                    "1722777600": "57",
                    "1722777900": "57",
                    "1722778200": "57",
                    "1722778500": "57",
                    "1722778800": "57",
                    "1722779100": "57",
                    "1722779400": "57",
                    "1722779700": "57",
                    "1722780000": "57",
                    "1722780300": "57",
                    "1722780600": "57",
                    "1722780900": "57",
                    "1722781200": "57",
                    "1722781500": "58",
                    "1722781800": "58",
                    "1722782100": "58",
                    "1722782400": "58",
                    "1722782700": "58",
                    "1722783000": "58",
                    "1722783300": "58",
                    "1722783600": "58",
                    "1722783900": "58",
                    "1722784200": "58",
                    "1722784500": "58",
                    "1722784800": "58",
                    "1722785100": "58",
                    "1722785400": "58",
                    "1722785700": "58",
                    "1722786000": "58",
                    "1722786300": "58",
                    "1722786600": "58",
                    "1722786900": "58",
                    "1722787200": "58"
                }
            }
        },
        "solar_and_uvi": {
            "solar": {
                "unit": "W/m²",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "uvi": {
                "unit": "",
                "list": {
                    "1722764400": "0",
                    "1722764700": "0",
                    "1722765000": "0",
                    "1722765300": "0",
                    "1722765600": "0",
                    "1722765900": "0",
                    "1722766200": "0",
                    "1722766500": "0",
                    "1722766800": "0",
                    "1722767100": "0",
                    "1722767400": "0",
                    "1722767700": "0",
                    "1722768000": "0",
                    "1722768300": "0",
                    "1722768600": "0",
                    "1722768900": "0",
                    "1722769200": "0",
                    "1722769500": "0",
                    "1722769800": "0",
                    "1722770100": "0",
                    "1722770400": "0",
                    "1722770700": "0",
                    "1722771000": "0",
                    "1722771300": "0",
                    "1722771600": "0",
                    "1722771900": "0",
                    "1722772200": "0",
                    "1722772500": "0",
                    "1722772800": "0",
                    "1722773100": "0",
                    "1722773400": "0",
                    "1722773700": "0",
                    "1722774000": "0",
                    "1722774300": "0",
                    "1722774600": "0",
                    "1722774900": "0",
                    "1722775200": "0",
                    "1722775500": "0",
                    "1722775800": "0",
                    "1722776100": "0",
                    "1722776400": "0",
                    "1722776700": "0",
                    "1722777000": "0",
                    "1722777300": "0",
                    "1722777600": "0",
                    "1722777900": "0",
                    "1722778200": "0",
                    "1722778500": "0",
                    "1722778800": "0",
                    "1722779100": "0",
                    "1722779400": "0",
                    "1722779700": "0",
                    "1722780000": "0",
                    "1722780300": "0",
                    "1722780600": "0",
                    "1722780900": "0",
                    "1722781200": "0",
                    "1722781500": "0",
                    "1722781800": "0",
                    "1722782100": "0",
                    "1722782400": "0",
                    "1722782700": "0",
                    "1722783000": "0",
                    "1722783300": "0",
                    "1722783600": "0",
                    "1722783900": "0",
                    "1722784200": "0",
                    "1722784500": "0",
                    "1722784800": "0",
                    "1722785100": "0",
                    "1722785400": "0",
                    "1722785700": "0",
                    "1722786000": "0",
                    "1722786300": "0",
                    "1722786600": "0",
                    "1722786900": "0",
                    "1722787200": "0"
                }
            }
        },
        "rainfall_piezo": {
            "rain_rate": {
                "unit": "mm/hr",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "daily": {
                "unit": "mm",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "event": {
                "unit": "mm",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "hourly": {
                "unit": "mm",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "weekly": {
                "unit": "mm",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "monthly": {
                "unit": "mm",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.0",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.0",
                    "1722768600": "0.0",
                    "1722768900": "0.0",
                    "1722769200": "0.0",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.0",
                    "1722773100": "0.0",
                    "1722773400": "0.0",
                    "1722773700": "0.0",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.0",
                    "1722776400": "0.0",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.0",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.0",
                    "1722781200": "0.0",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.0",
                    "1722782400": "0.0",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.0",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.0",
                    "1722786000": "0.0",
                    "1722786300": "0.0",
                    "1722786600": "0.0",
                    "1722786900": "0.0",
                    "1722787200": "0.0"
                }
            },
            "yearly": {
                "unit": "mm",
                "list": {
                    "1722764400": "50.0",
                    "1722764700": "50.0",
                    "1722765000": "50.0",
                    "1722765300": "50.0",
                    "1722765600": "50.0",
                    "1722765900": "50.0",
                    "1722766200": "50.0",
                    "1722766500": "50.0",
                    "1722766800": "50.0",
                    "1722767100": "50.0",
                    "1722767400": "50.0",
                    "1722767700": "50.0",
                    "1722768000": "50.0",
                    "1722768300": "50.0",
                    "1722768600": "50.0",
                    "1722768900": "50.0",
                    "1722769200": "50.0",
                    "1722769500": "50.0",
                    "1722769800": "50.0",
                    "1722770100": "50.0",
                    "1722770400": "50.0",
                    "1722770700": "50.0",
                    "1722771000": "50.0",
                    "1722771300": "50.0",
                    "1722771600": "50.0",
                    "1722771900": "50.0",
                    "1722772200": "50.0",
                    "1722772500": "50.0",
                    "1722772800": "50.0",
                    "1722773100": "50.0",
                    "1722773400": "50.0",
                    "1722773700": "50.0",
                    "1722774000": "50.0",
                    "1722774300": "50.0",
                    "1722774600": "50.0",
                    "1722774900": "50.0",
                    "1722775200": "50.0",
                    "1722775500": "50.0",
                    "1722775800": "50.0",
                    "1722776100": "50.0",
                    "1722776400": "50.0",
                    "1722776700": "50.0",
                    "1722777000": "50.0",
                    "1722777300": "50.0",
                    "1722777600": "50.0",
                    "1722777900": "50.0",
                    "1722778200": "50.0",
                    "1722778500": "50.0",
                    "1722778800": "50.0",
                    "1722779100": "50.0",
                    "1722779400": "50.0",
                    "1722779700": "50.0",
                    "1722780000": "50.0",
                    "1722780300": "50.0",
                    "1722780600": "50.0",
                    "1722780900": "50.0",
                    "1722781200": "50.0",
                    "1722781500": "50.0",
                    "1722781800": "50.0",
                    "1722782100": "50.0",
                    "1722782400": "50.0",
                    "1722782700": "50.0",
                    "1722783000": "50.0",
                    "1722783300": "50.0",
                    "1722783600": "50.0",
                    "1722783900": "50.0",
                    "1722784200": "50.0",
                    "1722784500": "50.0",
                    "1722784800": "50.0",
                    "1722785100": "50.0",
                    "1722785400": "50.0",
                    "1722785700": "50.0",
                    "1722786000": "50.0",
                    "1722786300": "50.0",
                    "1722786600": "50.0",
                    "1722786900": "50.0",
                    "1722787200": "50.0"
                }
            }
        },
        "wind": {
            "wind_speed": {
                "unit": "m/s",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.1",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.0",
                    "1722767700": "0.0",
                    "1722768000": "0.0",
                    "1722768300": "0.5",
                    "1722768600": "0.2",
                    "1722768900": "0.0",
                    "1722769200": "0.1",
                    "1722769500": "0.0",
                    "1722769800": "0.0",
                    "1722770100": "0.0",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.0",
                    "1722771900": "0.0",
                    "1722772200": "0.0",
                    "1722772500": "0.0",
                    "1722772800": "0.1",
                    "1722773100": "0.2",
                    "1722773400": "0.5",
                    "1722773700": "0.1",
                    "1722774000": "0.0",
                    "1722774300": "0.0",
                    "1722774600": "0.0",
                    "1722774900": "0.0",
                    "1722775200": "0.0",
                    "1722775500": "0.0",
                    "1722775800": "0.0",
                    "1722776100": "0.1",
                    "1722776400": "0.2",
                    "1722776700": "0.0",
                    "1722777000": "0.0",
                    "1722777300": "0.0",
                    "1722777600": "0.0",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.0",
                    "1722779700": "0.0",
                    "1722780000": "0.1",
                    "1722780300": "0.0",
                    "1722780600": "0.0",
                    "1722780900": "0.3",
                    "1722781200": "0.2",
                    "1722781500": "0.0",
                    "1722781800": "0.0",
                    "1722782100": "0.2",
                    "1722782400": "0.1",
                    "1722782700": "0.0",
                    "1722783000": "0.0",
                    "1722783300": "0.0",
                    "1722783600": "0.1",
                    "1722783900": "0.0",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.0",
                    "1722785100": "0.0",
                    "1722785400": "0.0",
                    "1722785700": "0.1",
                    "1722786000": "0.7",
                    "1722786300": "0.3",
                    "1722786600": "0.1",
                    "1722786900": "0.0",
                    "1722787200": "0.3"
                }
            },
            "wind_gust": {
                "unit": "m/s",
                "list": {
                    "1722764400": "0.0",
                    "1722764700": "0.0",
                    "1722765000": "0.0",
                    "1722765300": "0.0",
                    "1722765600": "0.0",
                    "1722765900": "0.0",
                    "1722766200": "0.0",
                    "1722766500": "0.5",
                    "1722766800": "0.0",
                    "1722767100": "0.0",
                    "1722767400": "0.5",
                    "1722767700": "0.5",
                    "1722768000": "0.5",
                    "1722768300": "0.9",
                    "1722768600": "0.9",
                    "1722768900": "0.0",
                    "1722769200": "0.7",
                    "1722769500": "0.7",
                    "1722769800": "0.5",
                    "1722770100": "0.5",
                    "1722770400": "0.0",
                    "1722770700": "0.0",
                    "1722771000": "0.0",
                    "1722771300": "0.0",
                    "1722771600": "0.5",
                    "1722771900": "0.5",
                    "1722772200": "0.6",
                    "1722772500": "0.7",
                    "1722772800": "0.6",
                    "1722773100": "0.6",
                    "1722773400": "0.7",
                    "1722773700": "0.7",
                    "1722774000": "0.7",
                    "1722774300": "0.5",
                    "1722774600": "0.5",
                    "1722774900": "0.6",
                    "1722775200": "0.6",
                    "1722775500": "0.6",
                    "1722775800": "0.0",
                    "1722776100": "0.5",
                    "1722776400": "0.8",
                    "1722776700": "0.5",
                    "1722777000": "0.0",
                    "1722777300": "0.5",
                    "1722777600": "0.5",
                    "1722777900": "0.0",
                    "1722778200": "0.0",
                    "1722778500": "0.0",
                    "1722778800": "0.0",
                    "1722779100": "0.0",
                    "1722779400": "0.5",
                    "1722779700": "0.5",
                    "1722780000": "0.5",
                    "1722780300": "0.8",
                    "1722780600": "0.5",
                    "1722780900": "0.7",
                    "1722781200": "1.4",
                    "1722781500": "0.8",
                    "1722781800": "0.0",
                    "1722782100": "0.7",
                    "1722782400": "0.6",
                    "1722782700": "0.6",
                    "1722783000": "0.6",
                    "1722783300": "0.5",
                    "1722783600": "0.6",
                    "1722783900": "0.6",
                    "1722784200": "0.0",
                    "1722784500": "0.0",
                    "1722784800": "0.5",
                    "1722785100": "0.5",
                    "1722785400": "0.0",
                    "1722785700": "0.7",
                    "1722786000": "0.9",
                    "1722786300": "0.8",
                    "1722786600": "0.6",
                    "1722786900": "0.9",
                    "1722787200": "1.4"
                }
            },
            "wind_direction": {
                "unit": "º",
                "list": {
                    "1722764400": "326",
                    "1722764700": "322",
                    "1722765000": "316",
                    "1722765300": "231",
                    "1722765600": "229",
                    "1722765900": "240",
                    "1722766200": "291",
                    "1722766500": "222",
                    "1722766800": "239",
                    "1722767100": "332",
                    "1722767400": "231",
                    "1722767700": "256",
                    "1722768000": "138",
                    "1722768300": "253",
                    "1722768600": "321",
                    "1722768900": "309",
                    "1722769200": "221",
                    "1722769500": "262",
                    "1722769800": "307",
                    "1722770100": "301",
                    "1722770400": "297",
                    "1722770700": "219",
                    "1722771000": "195",
                    "1722771300": "300",
                    "1722771600": "312",
                    "1722771900": "302",
                    "1722772200": "296",
                    "1722772500": "46",
                    "1722772800": "301",
                    "1722773100": "328",
                    "1722773400": "278",
                    "1722773700": "222",
                    "1722774000": "192",
                    "1722774300": "224",
                    "1722774600": "211",
                    "1722774900": "25",
                    "1722775200": "254",
                    "1722775500": "232",
                    "1722775800": "259",
                    "1722776100": "235",
                    "1722776400": "212",
                    "1722776700": "195",
                    "1722777000": "335",
                    "1722777300": "303",
                    "1722777600": "283",
                    "1722777900": "281",
                    "1722778200": "230",
                    "1722778500": "230",
                    "1722778800": "160",
                    "1722779100": "224",
                    "1722779400": "269",
                    "1722779700": "249",
                    "1722780000": "221",
                    "1722780300": "234",
                    "1722780600": "294",
                    "1722780900": "204",
                    "1722781200": "118",
                    "1722781500": "147",
                    "1722781800": "322",
                    "1722782100": "222",
                    "1722782400": "235",
                    "1722782700": "220",
                    "1722783000": "229",
                    "1722783300": "235",
                    "1722783600": "264",
                    "1722783900": "297",
                    "1722784200": "233",
                    "1722784500": "246",
                    "1722784800": "333",
                    "1722785100": "316",
                    "1722785400": "319",
                    "1722785700": "181",
                    "1722786000": "187",
                    "1722786300": "210",
                    "1722786600": "236",
                    "1722786900": "184",
                    "1722787200": "160"
                }
            }
        },
        "pressure": {
            "relative": {
                "unit": "hPa",
                "list": {
                    "1722764400": "1023.9",
                    "1722764700": "1023.8",
                    "1722765000": "1023.7",
                    "1722765300": "1023.7",
                    "1722765600": "1023.7",
                    "1722765900": "1023.8",
                    "1722766200": "1023.9",
                    "1722766500": "1024.2",
                    "1722766800": "1024.2",
                    "1722767100": "1024.1",
                    "1722767400": "1024.2",
                    "1722767700": "1024.2",
                    "1722768000": "1023.9",
                    "1722768300": "1024.1",
                    "1722768600": "1024.3",
                    "1722768900": "1024.1",
                    "1722769200": "1024.1",
                    "1722769500": "1024.0",
                    "1722769800": "1024.2",
                    "1722770100": "1024.4",
                    "1722770400": "1024.3",
                    "1722770700": "1024.3",
                    "1722771000": "1024.2",
                    "1722771300": "1024.3",
                    "1722771600": "1024.3",
                    "1722771900": "1024.3",
                    "1722772200": "1024.5",
                    "1722772500": "1024.2",
                    "1722772800": "1024.4",
                    "1722773100": "1024.3",
                    "1722773400": "1024.4",
                    "1722773700": "1024.4",
                    "1722774000": "1024.4",
                    "1722774300": "1024.4",
                    "1722774600": "1024.4",
                    "1722774900": "1024.4",
                    "1722775200": "1024.5",
                    "1722775500": "1024.5",
                    "1722775800": "1024.4",
                    "1722776100": "1024.3",
                    "1722776400": "1024.3",
                    "1722776700": "1024.4",
                    "1722777000": "1024.3",
                    "1722777300": "1024.2",
                    "1722777600": "1024.2",
                    "1722777900": "1024.2",
                    "1722778200": "1024.2",
                    "1722778500": "1024.1",
                    "1722778800": "1024.1",
                    "1722779100": "1024.1",
                    "1722779400": "1023.9",
                    "1722779700": "1024.1",
                    "1722780000": "1024.0",
                    "1722780300": "1024.1",
                    "1722780600": "1024.0",
                    "1722780900": "1024.1",
                    "1722781200": "1023.9",
                    "1722781500": "1023.8",
                    "1722781800": "1023.7",
                    "1722782100": "1023.8",
                    "1722782400": "1023.6",
                    "1722782700": "1023.6",
                    "1722783000": "1023.7",
                    "1722783300": "1023.5",
                    "1722783600": "1023.6",
                    "1722783900": "1023.5",
                    "1722784200": "1023.5",
                    "1722784500": "1023.4",
                    "1722784800": "1023.2",
                    "1722785100": "1023.2",
                    "1722785400": "1023.2",
                    "1722785700": "1023.3",
                    "1722786000": "1023.0",
                    "1722786300": "1023.0",
                    "1722786600": "1023.1",
                    "1722786900": "1023.1",
                    "1722787200": "1023.2"
                }
            },
            "absolute": {
                "unit": "hPa",
                "list": {
                    "1722764400": "1023.9",
                    "1722764700": "1023.8",
                    "1722765000": "1023.7",
                    "1722765300": "1023.7",
                    "1722765600": "1023.7",
                    "1722765900": "1023.8",
                    "1722766200": "1023.9",
                    "1722766500": "1024.2",
                    "1722766800": "1024.2",
                    "1722767100": "1024.1",
                    "1722767400": "1024.2",
                    "1722767700": "1024.2",
                    "1722768000": "1023.9",
                    "1722768300": "1024.1",
                    "1722768600": "1024.3",
                    "1722768900": "1024.1",
                    "1722769200": "1024.1",
                    "1722769500": "1024.0",
                    "1722769800": "1024.2",
                    "1722770100": "1024.4",
                    "1722770400": "1024.3",
                    "1722770700": "1024.3",
                    "1722771000": "1024.2",
                    "1722771300": "1024.3",
                    "1722771600": "1024.3",
                    "1722771900": "1024.3",
                    "1722772200": "1024.5",
                    "1722772500": "1024.2",
                    "1722772800": "1024.4",
                    "1722773100": "1024.3",
                    "1722773400": "1024.4",
                    "1722773700": "1024.4",
                    "1722774000": "1024.4",
                    "1722774300": "1024.4",
                    "1722774600": "1024.4",
                    "1722774900": "1024.4",
                    "1722775200": "1024.5",
                    "1722775500": "1024.5",
                    "1722775800": "1024.4",
                    "1722776100": "1024.3",
                    "1722776400": "1024.3",
                    "1722776700": "1024.4",
                    "1722777000": "1024.3",
                    "1722777300": "1024.2",
                    "1722777600": "1024.2",
                    "1722777900": "1024.2",
                    "1722778200": "1024.2",
                    "1722778500": "1024.1",
                    "1722778800": "1024.1",
                    "1722779100": "1024.1",
                    "1722779400": "1023.9",
                    "1722779700": "1024.1",
                    "1722780000": "1024.0",
                    "1722780300": "1024.1",
                    "1722780600": "1024.0",
                    "1722780900": "1024.1",
                    "1722781200": "1023.9",
                    "1722781500": "1023.8",
                    "1722781800": "1023.7",
                    "1722782100": "1023.8",
                    "1722782400": "1023.6",
                    "1722782700": "1023.6",
                    "1722783000": "1023.7",
                    "1722783300": "1023.5",
                    "1722783600": "1023.6",
                    "1722783900": "1023.5",
                    "1722784200": "1023.5",
                    "1722784500": "1023.4",
                    "1722784800": "1023.2",
                    "1722785100": "1023.2",
                    "1722785400": "1023.2",
                    "1722785700": "1023.3",
                    "1722786000": "1023.0",
                    "1722786300": "1023.0",
                    "1722786600": "1023.1",
                    "1722786900": "1023.1",
                    "1722787200": "1023.2"
                }
            }
        },
        "lightning": {
            "distance": {
                "unit": "km",
                "list": {
                    "1722764400": "-",
                    "1722764700": "-",
                    "1722765000": "-",
                    "1722765300": "-",
                    "1722765600": "-",
                    "1722765900": "-",
                    "1722766200": "-",
                    "1722766500": "-",
                    "1722766800": "-",
                    "1722767100": "-",
                    "1722767400": "-",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "-",
                    "1722770100": "-",
                    "1722770400": "-",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "-",
                    "1722772500": "-",
                    "1722772800": "-",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "-",
                    "1722778500": "-",
                    "1722778800": "-",
                    "1722779100": "-",
                    "1722779400": "-",
                    "1722779700": "-",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "-",
                    "1722783300": "-",
                    "1722783600": "-",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "-",
                    "1722784800": "-",
                    "1722785100": "31",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            },
            "count": {
                "unit": "",
                "list": {
                    "1722764400": "1",
                    "1722764700": "1",
                    "1722765000": "1",
                    "1722765300": "1",
                    "1722765600": "1",
                    "1722765900": "1",
                    "1722766200": "1",
                    "1722766500": "1",
                    "1722766800": "1",
                    "1722767100": "1",
                    "1722767400": "1",
                    "1722767700": "1",
                    "1722768000": "1",
                    "1722768300": "1",
                    "1722768600": "1",
                    "1722768900": "1",
                    "1722769200": "1",
                    "1722769500": "1",
                    "1722769800": "1",
                    "1722770100": "1",
                    "1722770400": "1",
                    "1722770700": "1",
                    "1722771000": "1",
                    "1722771300": "1",
                    "1722771600": "1",
                    "1722771900": "1",
                    "1722772200": "1",
                    "1722772500": "1",
                    "1722772800": "1",
                    "1722773100": "1",
                    "1722773400": "1",
                    "1722773700": "1",
                    "1722774000": "1",
                    "1722774300": "1",
                    "1722774600": "1",
                    "1722774900": "1",
                    "1722775200": "1",
                    "1722775500": "1",
                    "1722775800": "1",
                    "1722776100": "1",
                    "1722776400": "1",
                    "1722776700": "1",
                    "1722777000": "1",
                    "1722777300": "1",
                    "1722777600": "1",
                    "1722777900": "1",
                    "1722778200": "1",
                    "1722778500": "1",
                    "1722778800": "1",
                    "1722779100": "1",
                    "1722779400": "1",
                    "1722779700": "1",
                    "1722780000": "0",
                    "1722780300": "0",
                    "1722780600": "0",
                    "1722780900": "0",
                    "1722781200": "0",
                    "1722781500": "0",
                    "1722781800": "0",
                    "1722782100": "0",
                    "1722782400": "0",
                    "1722782700": "0",
                    "1722783000": "0",
                    "1722783300": "0",
                    "1722783600": "0",
                    "1722783900": "0",
                    "1722784200": "0",
                    "1722784500": "0",
                    "1722784800": "0",
                    "1722785100": "1",
                    "1722785400": "1",
                    "1722785700": "1",
                    "1722786000": "1",
                    "1722786300": "1",
                    "1722786600": "1",
                    "1722786900": "1",
                    "1722787200": "1"
                }
            }
        },
        "pm25_ch1": {
            "pm25": {
                "unit": "µg/m³",
                "list": {
                    "1722764400": "9",
                    "1722764700": "8",
                    "1722765000": "9",
                    "1722765300": "7",
                    "1722765600": "8",
                    "1722765900": "8",
                    "1722766200": "8",
                    "1722766500": "8",
                    "1722766800": "8",
                    "1722767100": "8",
                    "1722767400": "8",
                    "1722767700": "8",
                    "1722768000": "9",
                    "1722768300": "9",
                    "1722768600": "9",
                    "1722768900": "8",
                    "1722769200": "9",
                    "1722769500": "8",
                    "1722769800": "9",
                    "1722770100": "9",
                    "1722770400": "10",
                    "1722770700": "9",
                    "1722771000": "9",
                    "1722771300": "9",
                    "1722771600": "9",
                    "1722771900": "9",
                    "1722772200": "9",
                    "1722772500": "9",
                    "1722772800": "10",
                    "1722773100": "8",
                    "1722773400": "8",
                    "1722773700": "9",
                    "1722774000": "8",
                    "1722774300": "9",
                    "1722774600": "9",
                    "1722774900": "10",
                    "1722775200": "10",
                    "1722775500": "9",
                    "1722775800": "9",
                    "1722776100": "9",
                    "1722776400": "9",
                    "1722776700": "8",
                    "1722777000": "10",
                    "1722777300": "9",
                    "1722777600": "9",
                    "1722777900": "9",
                    "1722778200": "9",
                    "1722778500": "9",
                    "1722778800": "8",
                    "1722779100": "9",
                    "1722779400": "9",
                    "1722779700": "8",
                    "1722780000": "8",
                    "1722780300": "9",
                    "1722780600": "9",
                    "1722780900": "10",
                    "1722781200": "9",
                    "1722781500": "9",
                    "1722781800": "8",
                    "1722782100": "9",
                    "1722782400": "9",
                    "1722782700": "9",
                    "1722783000": "9",
                    "1722783300": "9",
                    "1722783600": "9",
                    "1722783900": "9",
                    "1722784200": "10",
                    "1722784500": "8",
                    "1722784800": "8",
                    "1722785100": "9",
                    "1722785400": "8",
                    "1722785700": "9",
                    "1722786000": "8",
                    "1722786300": "9",
                    "1722786600": "8",
                    "1722786900": "9",
                    "1722787200": "9"
                }
            }
        },
        "temp_and_humidity_ch1": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "21.8",
                    "1722764700": "21.7",
                    "1722765000": "21.7",
                    "1722765300": "21.6",
                    "1722765600": "21.6",
                    "1722765900": "21.5",
                    "1722766200": "21.5",
                    "1722766500": "21.4",
                    "1722766800": "21.4",
                    "1722767100": "21.3",
                    "1722767400": "21.3",
                    "1722767700": "21.2",
                    "1722768000": "21.2",
                    "1722768300": "21.1",
                    "1722768600": "21.1",
                    "1722768900": "21.0",
                    "1722769200": "21.0",
                    "1722769500": "21.0",
                    "1722769800": "20.9",
                    "1722770100": "20.9",
                    "1722770400": "20.9",
                    "1722770700": "20.9",
                    "1722771000": "20.9",
                    "1722771300": "20.9",
                    "1722771600": "20.9",
                    "1722771900": "20.9",
                    "1722772200": "20.9",
                    "1722772500": "21.0",
                    "1722772800": "21.0",
                    "1722773100": "21.0",
                    "1722773400": "21.0",
                    "1722773700": "21.0",
                    "1722774000": "21.0",
                    "1722774300": "21.0",
                    "1722774600": "21.0",
                    "1722774900": "21.0",
                    "1722775200": "21.0",
                    "1722775500": "21.0",
                    "1722775800": "21.0",
                    "1722776100": "21.0",
                    "1722776400": "21.0",
                    "1722776700": "21.0",
                    "1722777000": "21.0",
                    "1722777300": "21.0",
                    "1722777600": "21.0",
                    "1722777900": "20.9",
                    "1722778200": "20.9",
                    "1722778500": "20.9",
                    "1722778800": "20.9",
                    "1722779100": "20.9",
                    "1722779400": "20.9",
                    "1722779700": "20.8",
                    "1722780000": "20.8",
                    "1722780300": "20.8",
                    "1722780600": "20.8",
                    "1722780900": "20.7",
                    "1722781200": "20.7",
                    "1722781500": "20.6",
                    "1722781800": "20.6",
                    "1722782100": "20.6",
                    "1722782400": "20.5",
                    "1722782700": "20.5",
                    "1722783000": "20.5",
                    "1722783300": "20.4",
                    "1722783600": "20.4",
                    "1722783900": "20.3",
                    "1722784200": "20.3",
                    "1722784500": "20.3",
                    "1722784800": "20.3",
                    "1722785100": "20.2",
                    "1722785400": "20.2",
                    "1722785700": "20.1",
                    "1722786000": "20.1",
                    "1722786300": "20.0",
                    "1722786600": "20.0",
                    "1722786900": "19.9",
                    "1722787200": "19.9"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "50",
                    "1722764700": "50",
                    "1722765000": "50",
                    "1722765300": "50",
                    "1722765600": "50",
                    "1722765900": "50",
                    "1722766200": "50",
                    "1722766500": "51",
                    "1722766800": "51",
                    "1722767100": "51",
                    "1722767400": "51",
                    "1722767700": "51",
                    "1722768000": "51",
                    "1722768300": "51",
                    "1722768600": "51",
                    "1722768900": "51",
                    "1722769200": "52",
                    "1722769500": "52",
                    "1722769800": "53",
                    "1722770100": "53",
                    "1722770400": "54",
                    "1722770700": "54",
                    "1722771000": "54",
                    "1722771300": "54",
                    "1722771600": "55",
                    "1722771900": "55",
                    "1722772200": "55",
                    "1722772500": "55",
                    "1722772800": "55",
                    "1722773100": "55",
                    "1722773400": "55",
                    "1722773700": "55",
                    "1722774000": "55",
                    "1722774300": "55",
                    "1722774600": "55",
                    "1722774900": "55",
                    "1722775200": "55",
                    "1722775500": "55",
                    "1722775800": "55",
                    "1722776100": "55",
                    "1722776400": "55",
                    "1722776700": "55",
                    "1722777000": "55",
                    "1722777300": "55",
                    "1722777600": "55",
                    "1722777900": "55",
                    "1722778200": "55",
                    "1722778500": "55",
                    "1722778800": "55",
                    "1722779100": "55",
                    "1722779400": "55",
                    "1722779700": "55",
                    "1722780000": "55",
                    "1722780300": "55",
                    "1722780600": "55",
                    "1722780900": "55",
                    "1722781200": "55",
                    "1722781500": "55",
                    "1722781800": "55",
                    "1722782100": "55",
                    "1722782400": "55",
                    "1722782700": "55",
                    "1722783000": "55",
                    "1722783300": "55",
                    "1722783600": "55",
                    "1722783900": "55",
                    "1722784200": "55",
                    "1722784500": "55",
                    "1722784800": "55",
                    "1722785100": "55",
                    "1722785400": "55",
                    "1722785700": "55",
                    "1722786000": "55",
                    "1722786300": "55",
                    "1722786600": "55",
                    "1722786900": "55",
                    "1722787200": "55"
                }
            }
        },
        "temp_and_humidity_ch2": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "15.7",
                    "1722764700": "15.7",
                    "1722765000": "15.4",
                    "1722765300": "15.4",
                    "1722765600": "-",
                    "1722765900": "15.3",
                    "1722766200": "15.3",
                    "1722766500": "15.3",
                    "1722766800": "15.3",
                    "1722767100": "15.2",
                    "1722767400": "15.2",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "15.1",
                    "1722770100": "15.1",
                    "1722770400": "15.1",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "14.8",
                    "1722772500": "14.8",
                    "1722772800": "14.8",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "13.6",
                    "1722778500": "13.6",
                    "1722778800": "13.6",
                    "1722779100": "13.2",
                    "1722779400": "13.2",
                    "1722779700": "13.2",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "12.8",
                    "1722783300": "12.8",
                    "1722783600": "12.8",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "12.7",
                    "1722784800": "12.7",
                    "1722785100": "12.7",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "62",
                    "1722764700": "62",
                    "1722765000": "63",
                    "1722765300": "63",
                    "1722765600": "-",
                    "1722765900": "63",
                    "1722766200": "64",
                    "1722766500": "63",
                    "1722766800": "64",
                    "1722767100": "64",
                    "1722767400": "64",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "65",
                    "1722770100": "65",
                    "1722770400": "65",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "66",
                    "1722772500": "66",
                    "1722772800": "66",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "68",
                    "1722778500": "68",
                    "1722778800": "68",
                    "1722779100": "69",
                    "1722779400": "69",
                    "1722779700": "69",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "71",
                    "1722783300": "71",
                    "1722783600": "71",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "71",
                    "1722784800": "71",
                    "1722785100": "71",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            }
        },
        "temp_and_humidity_ch3": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "21.2",
                    "1722764700": "21.2",
                    "1722765000": "21.1",
                    "1722765300": "21.1",
                    "1722765600": "21.1",
                    "1722765900": "21.0",
                    "1722766200": "21.0",
                    "1722766500": "20.9",
                    "1722766800": "20.9",
                    "1722767100": "20.9",
                    "1722767400": "20.8",
                    "1722767700": "20.8",
                    "1722768000": "20.8",
                    "1722768300": "20.7",
                    "1722768600": "20.7",
                    "1722768900": "20.6",
                    "1722769200": "20.6",
                    "1722769500": "20.6",
                    "1722769800": "20.6",
                    "1722770100": "20.5",
                    "1722770400": "20.5",
                    "1722770700": "20.5",
                    "1722771000": "20.4",
                    "1722771300": "20.4",
                    "1722771600": "20.4",
                    "1722771900": "20.4",
                    "1722772200": "20.3",
                    "1722772500": "20.3",
                    "1722772800": "20.3",
                    "1722773100": "20.3",
                    "1722773400": "20.3",
                    "1722773700": "20.2",
                    "1722774000": "20.2",
                    "1722774300": "20.2",
                    "1722774600": "20.2",
                    "1722774900": "20.2",
                    "1722775200": "20.2",
                    "1722775500": "20.1",
                    "1722775800": "20.1",
                    "1722776100": "20.1",
                    "1722776400": "20.1",
                    "1722776700": "20.0",
                    "1722777000": "20.0",
                    "1722777300": "20.0",
                    "1722777600": "20.0",
                    "1722777900": "19.9",
                    "1722778200": "19.9",
                    "1722778500": "19.9",
                    "1722778800": "19.9",
                    "1722779100": "19.8",
                    "1722779400": "19.8",
                    "1722779700": "19.8",
                    "1722780000": "19.7",
                    "1722780300": "19.7",
                    "1722780600": "19.7",
                    "1722780900": "19.7",
                    "1722781200": "19.7",
                    "1722781500": "19.6",
                    "1722781800": "19.6",
                    "1722782100": "19.6",
                    "1722782400": "19.6",
                    "1722782700": "19.6",
                    "1722783000": "19.6",
                    "1722783300": "19.5",
                    "1722783600": "19.5",
                    "1722783900": "19.5",
                    "1722784200": "19.5",
                    "1722784500": "19.5",
                    "1722784800": "19.5",
                    "1722785100": "19.4",
                    "1722785400": "19.3",
                    "1722785700": "19.3",
                    "1722786000": "19.3",
                    "1722786300": "19.2",
                    "1722786600": "19.2",
                    "1722786900": "19.2",
                    "1722787200": "19.1"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "56",
                    "1722764700": "56",
                    "1722765000": "56",
                    "1722765300": "56",
                    "1722765600": "56",
                    "1722765900": "56",
                    "1722766200": "56",
                    "1722766500": "56",
                    "1722766800": "56",
                    "1722767100": "56",
                    "1722767400": "57",
                    "1722767700": "57",
                    "1722768000": "57",
                    "1722768300": "57",
                    "1722768600": "57",
                    "1722768900": "57",
                    "1722769200": "57",
                    "1722769500": "57",
                    "1722769800": "57",
                    "1722770100": "57",
                    "1722770400": "57",
                    "1722770700": "57",
                    "1722771000": "57",
                    "1722771300": "57",
                    "1722771600": "58",
                    "1722771900": "58",
                    "1722772200": "58",
                    "1722772500": "58",
                    "1722772800": "58",
                    "1722773100": "58",
                    "1722773400": "58",
                    "1722773700": "58",
                    "1722774000": "59",
                    "1722774300": "59",
                    "1722774600": "59",
                    "1722774900": "59",
                    "1722775200": "59",
                    "1722775500": "59",
                    "1722775800": "59",
                    "1722776100": "59",
                    "1722776400": "59",
                    "1722776700": "59",
                    "1722777000": "59",
                    "1722777300": "60",
                    "1722777600": "60",
                    "1722777900": "60",
                    "1722778200": "60",
                    "1722778500": "60",
                    "1722778800": "60",
                    "1722779100": "60",
                    "1722779400": "60",
                    "1722779700": "60",
                    "1722780000": "60",
                    "1722780300": "60",
                    "1722780600": "60",
                    "1722780900": "60",
                    "1722781200": "60",
                    "1722781500": "60",
                    "1722781800": "60",
                    "1722782100": "60",
                    "1722782400": "60",
                    "1722782700": "60",
                    "1722783000": "60",
                    "1722783300": "60",
                    "1722783600": "60",
                    "1722783900": "60",
                    "1722784200": "60",
                    "1722784500": "60",
                    "1722784800": "60",
                    "1722785100": "60",
                    "1722785400": "60",
                    "1722785700": "60",
                    "1722786000": "60",
                    "1722786300": "60",
                    "1722786600": "60",
                    "1722786900": "60",
                    "1722787200": "60"
                }
            }
        },
        "temp_and_humidity_ch4": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "20.9",
                    "1722764700": "20.8",
                    "1722765000": "20.8",
                    "1722765300": "20.7",
                    "1722765600": "20.7",
                    "1722765900": "20.6",
                    "1722766200": "20.6",
                    "1722766500": "20.6",
                    "1722766800": "20.5",
                    "1722767100": "20.5",
                    "1722767400": "20.5",
                    "1722767700": "20.5",
                    "1722768000": "20.4",
                    "1722768300": "20.4",
                    "1722768600": "20.3",
                    "1722768900": "20.3",
                    "1722769200": "20.3",
                    "1722769500": "20.2",
                    "1722769800": "20.2",
                    "1722770100": "20.2",
                    "1722770400": "20.2",
                    "1722770700": "20.2",
                    "1722771000": "20.1",
                    "1722771300": "20.1",
                    "1722771600": "20.1",
                    "1722771900": "20.0",
                    "1722772200": "20.0",
                    "1722772500": "20.0",
                    "1722772800": "20.0",
                    "1722773100": "20.1",
                    "1722773400": "20.2",
                    "1722773700": "20.3",
                    "1722774000": "20.4",
                    "1722774300": "20.5",
                    "1722774600": "20.5",
                    "1722774900": "20.6",
                    "1722775200": "20.6",
                    "1722775500": "20.7",
                    "1722775800": "20.7",
                    "1722776100": "20.7",
                    "1722776400": "20.7",
                    "1722776700": "20.7",
                    "1722777000": "20.8",
                    "1722777300": "20.7",
                    "1722777600": "20.8",
                    "1722777900": "20.8",
                    "1722778200": "20.7",
                    "1722778500": "20.7",
                    "1722778800": "20.7",
                    "1722779100": "20.7",
                    "1722779400": "20.7",
                    "1722779700": "20.7",
                    "1722780000": "20.7",
                    "1722780300": "20.6",
                    "1722780600": "20.5",
                    "1722780900": "20.4",
                    "1722781200": "20.2",
                    "1722781500": "20.2",
                    "1722781800": "20.1",
                    "1722782100": "20.0",
                    "1722782400": "19.9",
                    "1722782700": "19.8",
                    "1722783000": "19.8",
                    "1722783300": "19.7",
                    "1722783600": "19.6",
                    "1722783900": "19.5",
                    "1722784200": "19.5",
                    "1722784500": "19.4",
                    "1722784800": "19.4",
                    "1722785100": "19.3",
                    "1722785400": "19.3",
                    "1722785700": "19.2",
                    "1722786000": "19.2",
                    "1722786300": "19.1",
                    "1722786600": "19.1",
                    "1722786900": "19.1",
                    "1722787200": "19.1"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "58",
                    "1722764700": "58",
                    "1722765000": "58",
                    "1722765300": "58",
                    "1722765600": "58",
                    "1722765900": "58",
                    "1722766200": "58",
                    "1722766500": "58",
                    "1722766800": "58",
                    "1722767100": "58",
                    "1722767400": "58",
                    "1722767700": "59",
                    "1722768000": "59",
                    "1722768300": "59",
                    "1722768600": "59",
                    "1722768900": "59",
                    "1722769200": "59",
                    "1722769500": "59",
                    "1722769800": "59",
                    "1722770100": "59",
                    "1722770400": "59",
                    "1722770700": "59",
                    "1722771000": "59",
                    "1722771300": "59",
                    "1722771600": "59",
                    "1722771900": "59",
                    "1722772200": "59",
                    "1722772500": "60",
                    "1722772800": "60",
                    "1722773100": "60",
                    "1722773400": "60",
                    "1722773700": "60",
                    "1722774000": "60",
                    "1722774300": "60",
                    "1722774600": "60",
                    "1722774900": "60",
                    "1722775200": "60",
                    "1722775500": "60",
                    "1722775800": "60",
                    "1722776100": "60",
                    "1722776400": "60",
                    "1722776700": "60",
                    "1722777000": "60",
                    "1722777300": "60",
                    "1722777600": "60",
                    "1722777900": "60",
                    "1722778200": "60",
                    "1722778500": "60",
                    "1722778800": "60",
                    "1722779100": "60",
                    "1722779400": "60",
                    "1722779700": "61",
                    "1722780000": "61",
                    "1722780300": "61",
                    "1722780600": "61",
                    "1722780900": "61",
                    "1722781200": "61",
                    "1722781500": "61",
                    "1722781800": "61",
                    "1722782100": "61",
                    "1722782400": "61",
                    "1722782700": "62",
                    "1722783000": "62",
                    "1722783300": "62",
                    "1722783600": "62",
                    "1722783900": "62",
                    "1722784200": "62",
                    "1722784500": "62",
                    "1722784800": "62",
                    "1722785100": "63",
                    "1722785400": "63",
                    "1722785700": "63",
                    "1722786000": "63",
                    "1722786300": "63",
                    "1722786600": "64",
                    "1722786900": "64",
                    "1722787200": "64"
                }
            }
        },
        "temp_and_humidity_ch5": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "19.1",
                    "1722764700": "19.1",
                    "1722765000": "19.0",
                    "1722765300": "19.0",
                    "1722765600": "18.9",
                    "1722765900": "18.8",
                    "1722766200": "18.8",
                    "1722766500": "18.7",
                    "1722766800": "18.7",
                    "1722767100": "18.6",
                    "1722767400": "18.6",
                    "1722767700": "18.6",
                    "1722768000": "18.6",
                    "1722768300": "18.5",
                    "1722768600": "18.5",
                    "1722768900": "18.5",
                    "1722769200": "18.4",
                    "1722769500": "18.4",
                    "1722769800": "18.4",
                    "1722770100": "18.4",
                    "1722770400": "18.4",
                    "1722770700": "18.5",
                    "1722771000": "18.5",
                    "1722771300": "18.4",
                    "1722771600": "18.4",
                    "1722771900": "18.5",
                    "1722772200": "18.6",
                    "1722772500": "18.7",
                    "1722772800": "18.8",
                    "1722773100": "18.9",
                    "1722773400": "18.9",
                    "1722773700": "19.0",
                    "1722774000": "19.0",
                    "1722774300": "19.0",
                    "1722774600": "19.0",
                    "1722774900": "19.1",
                    "1722775200": "19.1",
                    "1722775500": "19.1",
                    "1722775800": "19.1",
                    "1722776100": "19.1",
                    "1722776400": "19.0",
                    "1722776700": "19.0",
                    "1722777000": "19.0",
                    "1722777300": "19.0",
                    "1722777600": "19.0",
                    "1722777900": "19.0",
                    "1722778200": "19.0",
                    "1722778500": "19.0",
                    "1722778800": "19.0",
                    "1722779100": "19.0",
                    "1722779400": "19.0",
                    "1722779700": "19.0",
                    "1722780000": "19.0",
                    "1722780300": "18.9",
                    "1722780600": "18.9",
                    "1722780900": "18.9",
                    "1722781200": "18.9",
                    "1722781500": "18.9",
                    "1722781800": "18.8",
                    "1722782100": "18.8",
                    "1722782400": "18.8",
                    "1722782700": "18.8",
                    "1722783000": "18.8",
                    "1722783300": "18.8",
                    "1722783600": "18.8",
                    "1722783900": "18.8",
                    "1722784200": "18.8",
                    "1722784500": "18.8",
                    "1722784800": "18.7",
                    "1722785100": "18.7",
                    "1722785400": "18.7",
                    "1722785700": "18.7",
                    "1722786000": "18.7",
                    "1722786300": "18.7",
                    "1722786600": "18.7",
                    "1722786900": "18.6",
                    "1722787200": "18.6"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "63",
                    "1722764700": "62",
                    "1722765000": "63",
                    "1722765300": "63",
                    "1722765600": "63",
                    "1722765900": "63",
                    "1722766200": "63",
                    "1722766500": "63",
                    "1722766800": "63",
                    "1722767100": "63",
                    "1722767400": "64",
                    "1722767700": "64",
                    "1722768000": "64",
                    "1722768300": "64",
                    "1722768600": "64",
                    "1722768900": "64",
                    "1722769200": "64",
                    "1722769500": "64",
                    "1722769800": "64",
                    "1722770100": "64",
                    "1722770400": "64",
                    "1722770700": "64",
                    "1722771000": "65",
                    "1722771300": "65",
                    "1722771600": "65",
                    "1722771900": "65",
                    "1722772200": "65",
                    "1722772500": "65",
                    "1722772800": "65",
                    "1722773100": "65",
                    "1722773400": "65",
                    "1722773700": "65",
                    "1722774000": "65",
                    "1722774300": "65",
                    "1722774600": "65",
                    "1722774900": "65",
                    "1722775200": "65",
                    "1722775500": "65",
                    "1722775800": "65",
                    "1722776100": "65",
                    "1722776400": "65",
                    "1722776700": "65",
                    "1722777000": "65",
                    "1722777300": "65",
                    "1722777600": "65",
                    "1722777900": "65",
                    "1722778200": "65",
                    "1722778500": "65",
                    "1722778800": "65",
                    "1722779100": "65",
                    "1722779400": "65",
                    "1722779700": "65",
                    "1722780000": "65",
                    "1722780300": "65",
                    "1722780600": "65",
                    "1722780900": "65",
                    "1722781200": "65",
                    "1722781500": "65",
                    "1722781800": "65",
                    "1722782100": "65",
                    "1722782400": "65",
                    "1722782700": "65",
                    "1722783000": "65",
                    "1722783300": "65",
                    "1722783600": "66",
                    "1722783900": "66",
                    "1722784200": "66",
                    "1722784500": "66",
                    "1722784800": "66",
                    "1722785100": "66",
                    "1722785400": "66",
                    "1722785700": "66",
                    "1722786000": "66",
                    "1722786300": "66",
                    "1722786600": "66",
                    "1722786900": "66",
                    "1722787200": "66"
                }
            }
        },
        "temp_and_humidity_ch6": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "21.6",
                    "1722764700": "21.6",
                    "1722765000": "21.5",
                    "1722765300": "21.5",
                    "1722765600": "21.5",
                    "1722765900": "21.5",
                    "1722766200": "21.4",
                    "1722766500": "21.4",
                    "1722766800": "21.4",
                    "1722767100": "21.4",
                    "1722767400": "21.3",
                    "1722767700": "21.3",
                    "1722768000": "21.3",
                    "1722768300": "21.2",
                    "1722768600": "21.2",
                    "1722768900": "21.2",
                    "1722769200": "21.2",
                    "1722769500": "21.1",
                    "1722769800": "21.1",
                    "1722770100": "21.1",
                    "1722770400": "21.1",
                    "1722770700": "21.0",
                    "1722771000": "21.0",
                    "1722771300": "21.0",
                    "1722771600": "21.0",
                    "1722771900": "21.0",
                    "1722772200": "20.9",
                    "1722772500": "20.9",
                    "1722772800": "20.9",
                    "1722773100": "20.9",
                    "1722773400": "20.8",
                    "1722773700": "20.8",
                    "1722774000": "20.8",
                    "1722774300": "20.8",
                    "1722774600": "20.8",
                    "1722774900": "20.7",
                    "1722775200": "20.7",
                    "1722775500": "20.7",
                    "1722775800": "20.7",
                    "1722776100": "20.7",
                    "1722776400": "20.6",
                    "1722776700": "20.6",
                    "1722777000": "20.6",
                    "1722777300": "20.6",
                    "1722777600": "20.5",
                    "1722777900": "20.5",
                    "1722778200": "20.5",
                    "1722778500": "20.5",
                    "1722778800": "20.5",
                    "1722779100": "20.4",
                    "1722779400": "20.4",
                    "1722779700": "20.4",
                    "1722780000": "20.4",
                    "1722780300": "20.3",
                    "1722780600": "20.3",
                    "1722780900": "20.3",
                    "1722781200": "20.3",
                    "1722781500": "20.2",
                    "1722781800": "20.2",
                    "1722782100": "20.2",
                    "1722782400": "20.2",
                    "1722782700": "20.1",
                    "1722783000": "20.1",
                    "1722783300": "20.1",
                    "1722783600": "20.1",
                    "1722783900": "20.0",
                    "1722784200": "20.0",
                    "1722784500": "20.0",
                    "1722784800": "20.0",
                    "1722785100": "19.9",
                    "1722785400": "19.9",
                    "1722785700": "19.9",
                    "1722786000": "19.9",
                    "1722786300": "19.8",
                    "1722786600": "19.8",
                    "1722786900": "19.8",
                    "1722787200": "19.8"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "55",
                    "1722764700": "55",
                    "1722765000": "55",
                    "1722765300": "55",
                    "1722765600": "55",
                    "1722765900": "55",
                    "1722766200": "55",
                    "1722766500": "55",
                    "1722766800": "55",
                    "1722767100": "55",
                    "1722767400": "55",
                    "1722767700": "55",
                    "1722768000": "55",
                    "1722768300": "55",
                    "1722768600": "55",
                    "1722768900": "55",
                    "1722769200": "55",
                    "1722769500": "55",
                    "1722769800": "55",
                    "1722770100": "55",
                    "1722770400": "55",
                    "1722770700": "55",
                    "1722771000": "55",
                    "1722771300": "55",
                    "1722771600": "56",
                    "1722771900": "56",
                    "1722772200": "56",
                    "1722772500": "56",
                    "1722772800": "56",
                    "1722773100": "56",
                    "1722773400": "56",
                    "1722773700": "56",
                    "1722774000": "56",
                    "1722774300": "56",
                    "1722774600": "56",
                    "1722774900": "56",
                    "1722775200": "56",
                    "1722775500": "56",
                    "1722775800": "56",
                    "1722776100": "56",
                    "1722776400": "56",
                    "1722776700": "56",
                    "1722777000": "56",
                    "1722777300": "56",
                    "1722777600": "56",
                    "1722777900": "56",
                    "1722778200": "56",
                    "1722778500": "56",
                    "1722778800": "56",
                    "1722779100": "56",
                    "1722779400": "56",
                    "1722779700": "56",
                    "1722780000": "56",
                    "1722780300": "56",
                    "1722780600": "56",
                    "1722780900": "56",
                    "1722781200": "56",
                    "1722781500": "56",
                    "1722781800": "56",
                    "1722782100": "56",
                    "1722782400": "56",
                    "1722782700": "56",
                    "1722783000": "56",
                    "1722783300": "56",
                    "1722783600": "56",
                    "1722783900": "56",
                    "1722784200": "56",
                    "1722784500": "56",
                    "1722784800": "56",
                    "1722785100": "56",
                    "1722785400": "56",
                    "1722785700": "56",
                    "1722786000": "56",
                    "1722786300": "56",
                    "1722786600": "56",
                    "1722786900": "56",
                    "1722787200": "56"
                }
            }
        },
        "temp_and_humidity_ch7": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "21.7",
                    "1722764700": "21.6",
                    "1722765000": "21.6",
                    "1722765300": "21.5",
                    "1722765600": "21.5",
                    "1722765900": "21.5",
                    "1722766200": "21.5",
                    "1722766500": "21.4",
                    "1722766800": "21.4",
                    "1722767100": "21.3",
                    "1722767400": "21.3",
                    "1722767700": "21.3",
                    "1722768000": "21.2",
                    "1722768300": "21.2",
                    "1722768600": "21.2",
                    "1722768900": "21.2",
                    "1722769200": "21.1",
                    "1722769500": "21.1",
                    "1722769800": "21.0",
                    "1722770100": "21.0",
                    "1722770400": "21.0",
                    "1722770700": "21.0",
                    "1722771000": "20.9",
                    "1722771300": "20.9",
                    "1722771600": "20.9",
                    "1722771900": "20.9",
                    "1722772200": "20.8",
                    "1722772500": "20.8",
                    "1722772800": "20.8",
                    "1722773100": "20.8",
                    "1722773400": "20.7",
                    "1722773700": "20.7",
                    "1722774000": "20.7",
                    "1722774300": "20.6",
                    "1722774600": "20.6",
                    "1722774900": "20.6",
                    "1722775200": "20.5",
                    "1722775500": "20.5",
                    "1722775800": "20.5",
                    "1722776100": "20.4",
                    "1722776400": "20.4",
                    "1722776700": "20.4",
                    "1722777000": "20.3",
                    "1722777300": "20.3",
                    "1722777600": "20.2",
                    "1722777900": "20.2",
                    "1722778200": "20.2",
                    "1722778500": "20.1",
                    "1722778800": "20.1",
                    "1722779100": "20.1",
                    "1722779400": "20.0",
                    "1722779700": "20.0",
                    "1722780000": "20.0",
                    "1722780300": "19.9",
                    "1722780600": "19.9",
                    "1722780900": "19.9",
                    "1722781200": "19.8",
                    "1722781500": "19.8",
                    "1722781800": "19.7",
                    "1722782100": "19.7",
                    "1722782400": "19.7",
                    "1722782700": "19.7",
                    "1722783000": "19.6",
                    "1722783300": "19.6",
                    "1722783600": "19.6",
                    "1722783900": "19.5",
                    "1722784200": "19.5",
                    "1722784500": "19.5",
                    "1722784800": "19.4",
                    "1722785100": "19.4",
                    "1722785400": "19.4",
                    "1722785700": "19.4",
                    "1722786000": "19.4",
                    "1722786300": "19.3",
                    "1722786600": "19.3",
                    "1722786900": "19.3",
                    "1722787200": "19.3"
                }
            },
            "humidity": {
                "unit": "%",
                "list": {
                    "1722764400": "55",
                    "1722764700": "55",
                    "1722765000": "55",
                    "1722765300": "55",
                    "1722765600": "55",
                    "1722765900": "56",
                    "1722766200": "56",
                    "1722766500": "56",
                    "1722766800": "56",
                    "1722767100": "56",
                    "1722767400": "56",
                    "1722767700": "56",
                    "1722768000": "56",
                    "1722768300": "56",
                    "1722768600": "56",
                    "1722768900": "56",
                    "1722769200": "56",
                    "1722769500": "56",
                    "1722769800": "56",
                    "1722770100": "56",
                    "1722770400": "56",
                    "1722770700": "56",
                    "1722771000": "56",
                    "1722771300": "56",
                    "1722771600": "56",
                    "1722771900": "56",
                    "1722772200": "56",
                    "1722772500": "56",
                    "1722772800": "56",
                    "1722773100": "56",
                    "1722773400": "56",
                    "1722773700": "56",
                    "1722774000": "56",
                    "1722774300": "56",
                    "1722774600": "56",
                    "1722774900": "56",
                    "1722775200": "56",
                    "1722775500": "56",
                    "1722775800": "56",
                    "1722776100": "56",
                    "1722776400": "56",
                    "1722776700": "57",
                    "1722777000": "57",
                    "1722777300": "57",
                    "1722777600": "57",
                    "1722777900": "57",
                    "1722778200": "57",
                    "1722778500": "57",
                    "1722778800": "57",
                    "1722779100": "57",
                    "1722779400": "57",
                    "1722779700": "57",
                    "1722780000": "57",
                    "1722780300": "57",
                    "1722780600": "57",
                    "1722780900": "57",
                    "1722781200": "57",
                    "1722781500": "57",
                    "1722781800": "57",
                    "1722782100": "57",
                    "1722782400": "57",
                    "1722782700": "57",
                    "1722783000": "57",
                    "1722783300": "57",
                    "1722783600": "57",
                    "1722783900": "57",
                    "1722784200": "58",
                    "1722784500": "58",
                    "1722784800": "58",
                    "1722785100": "58",
                    "1722785400": "58",
                    "1722785700": "58",
                    "1722786000": "58",
                    "1722786300": "58",
                    "1722786600": "58",
                    "1722786900": "58",
                    "1722787200": "58"
                }
            }
        },
        "soil_ch1": {
            "soilmoisture": {
                "unit": "%",
                "list": {
                    "1722764400": "11",
                    "1722764700": "11",
                    "1722765000": "11",
                    "1722765300": "11",
                    "1722765600": "11",
                    "1722765900": "11",
                    "1722766200": "11",
                    "1722766500": "11",
                    "1722766800": "11",
                    "1722767100": "11",
                    "1722767400": "11",
                    "1722767700": "11",
                    "1722768000": "11",
                    "1722768300": "11",
                    "1722768600": "11",
                    "1722768900": "11",
                    "1722769200": "11",
                    "1722769500": "11",
                    "1722769800": "11",
                    "1722770100": "11",
                    "1722770400": "11",
                    "1722770700": "11",
                    "1722771000": "11",
                    "1722771300": "11",
                    "1722771600": "11",
                    "1722771900": "11",
                    "1722772200": "11",
                    "1722772500": "11",
                    "1722772800": "11",
                    "1722773100": "11",
                    "1722773400": "11",
                    "1722773700": "11",
                    "1722774000": "11",
                    "1722774300": "11",
                    "1722774600": "11",
                    "1722774900": "11",
                    "1722775200": "11",
                    "1722775500": "11",
                    "1722775800": "11",
                    "1722776100": "11",
                    "1722776400": "11",
                    "1722776700": "11",
                    "1722777000": "11",
                    "1722777300": "11",
                    "1722777600": "11",
                    "1722777900": "11",
                    "1722778200": "11",
                    "1722778500": "11",
                    "1722778800": "11",
                    "1722779100": "11",
                    "1722779400": "11",
                    "1722779700": "11",
                    "1722780000": "11",
                    "1722780300": "11",
                    "1722780600": "11",
                    "1722780900": "11",
                    "1722781200": "11",
                    "1722781500": "11",
                    "1722781800": "11",
                    "1722782100": "11",
                    "1722782400": "11",
                    "1722782700": "11",
                    "1722783000": "11",
                    "1722783300": "11",
                    "1722783600": "11",
                    "1722783900": "11",
                    "1722784200": "11",
                    "1722784500": "11",
                    "1722784800": "11",
                    "1722785100": "11",
                    "1722785400": "11",
                    "1722785700": "11",
                    "1722786000": "11",
                    "1722786300": "11",
                    "1722786600": "11",
                    "1722786900": "11",
                    "1722787200": "11"
                }
            },
            "ad": {
                "unit": "",
                "list": {
                    "1722764400": "117",
                    "1722764700": "116",
                    "1722765000": "117",
                    "1722765300": "117",
                    "1722765600": "117",
                    "1722765900": "117",
                    "1722766200": "117",
                    "1722766500": "117",
                    "1722766800": "117",
                    "1722767100": "117",
                    "1722767400": "116",
                    "1722767700": "117",
                    "1722768000": "117",
                    "1722768300": "117",
                    "1722768600": "117",
                    "1722768900": "117",
                    "1722769200": "116",
                    "1722769500": "117",
                    "1722769800": "117",
                    "1722770100": "117",
                    "1722770400": "117",
                    "1722770700": "117",
                    "1722771000": "116",
                    "1722771300": "117",
                    "1722771600": "117",
                    "1722771900": "117",
                    "1722772200": "117",
                    "1722772500": "116",
                    "1722772800": "116",
                    "1722773100": "117",
                    "1722773400": "117",
                    "1722773700": "117",
                    "1722774000": "117",
                    "1722774300": "116",
                    "1722774600": "117",
                    "1722774900": "116",
                    "1722775200": "117",
                    "1722775500": "117",
                    "1722775800": "117",
                    "1722776100": "117",
                    "1722776400": "117",
                    "1722776700": "117",
                    "1722777000": "117",
                    "1722777300": "117",
                    "1722777600": "117",
                    "1722777900": "116",
                    "1722778200": "117",
                    "1722778500": "117",
                    "1722778800": "117",
                    "1722779100": "117",
                    "1722779400": "117",
                    "1722779700": "117",
                    "1722780000": "117",
                    "1722780300": "117",
                    "1722780600": "117",
                    "1722780900": "117",
                    "1722781200": "117",
                    "1722781500": "117",
                    "1722781800": "116",
                    "1722782100": "117",
                    "1722782400": "117",
                    "1722782700": "117",
                    "1722783000": "117",
                    "1722783300": "117",
                    "1722783600": "117",
                    "1722783900": "117",
                    "1722784200": "117",
                    "1722784500": "117",
                    "1722784800": "117",
                    "1722785100": "116",
                    "1722785400": "117",
                    "1722785700": "117",
                    "1722786000": "117",
                    "1722786300": "117",
                    "1722786600": "116",
                    "1722786900": "117",
                    "1722787200": "117"
                }
            }
        },
        "soil_ch2": {
            "soilmoisture": {
                "unit": "%",
                "list": {
                    "1722764400": "-",
                    "1722764700": "-",
                    "1722765000": "-",
                    "1722765300": "-",
                    "1722765600": "-",
                    "1722765900": "-",
                    "1722766200": "-",
                    "1722766500": "-",
                    "1722766800": "-",
                    "1722767100": "-",
                    "1722767400": "-",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "-",
                    "1722770100": "-",
                    "1722770400": "-",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "-",
                    "1722772500": "-",
                    "1722772800": "-",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "-",
                    "1722778500": "-",
                    "1722778800": "-",
                    "1722779100": "-",
                    "1722779400": "-",
                    "1722779700": "-",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "-",
                    "1722783300": "-",
                    "1722783600": "-",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "-",
                    "1722784800": "-",
                    "1722785100": "-",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            }
        },
        "soil_ch3": {
            "soilmoisture": {
                "unit": "%",
                "list": {
                    "1722764400": "-",
                    "1722764700": "-",
                    "1722765000": "-",
                    "1722765300": "-",
                    "1722765600": "-",
                    "1722765900": "-",
                    "1722766200": "-",
                    "1722766500": "-",
                    "1722766800": "-",
                    "1722767100": "-",
                    "1722767400": "-",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "-",
                    "1722770100": "-",
                    "1722770400": "-",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "-",
                    "1722772500": "-",
                    "1722772800": "-",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "-",
                    "1722778500": "-",
                    "1722778800": "-",
                    "1722779100": "-",
                    "1722779400": "-",
                    "1722779700": "-",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "-",
                    "1722783300": "-",
                    "1722783600": "-",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "-",
                    "1722784800": "-",
                    "1722785100": "-",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            }
        },
        "temp_ch1": {
            "temperature": {
                "unit": "℃",
                "list": {
                    "1722764400": "18.9",
                    "1722764700": "18.8",
                    "1722765000": "18.7",
                    "1722765300": "18.7",
                    "1722765600": "18.7",
                    "1722765900": "18.8",
                    "1722766200": "18.7",
                    "1722766500": "18.8",
                    "1722766800": "18.8",
                    "1722767100": "18.7",
                    "1722767400": "18.7",
                    "1722767700": "18.8",
                    "1722768000": "18.7",
                    "1722768300": "18.7",
                    "1722768600": "18.7",
                    "1722768900": "18.7",
                    "1722769200": "18.6",
                    "1722769500": "18.6",
                    "1722769800": "18.6",
                    "1722770100": "18.6",
                    "1722770400": "18.6",
                    "1722770700": "18.6",
                    "1722771000": "18.6",
                    "1722771300": "18.4",
                    "1722771600": "18.6",
                    "1722771900": "18.5",
                    "1722772200": "18.4",
                    "1722772500": "18.4",
                    "1722772800": "18.3",
                    "1722773100": "18.4",
                    "1722773400": "18.3",
                    "1722773700": "18.3",
                    "1722774000": "18.4",
                    "1722774300": "18.4",
                    "1722774600": "18.4",
                    "1722774900": "18.4",
                    "1722775200": "18.3",
                    "1722775500": "18.2",
                    "1722775800": "18.3",
                    "1722776100": "18.2",
                    "1722776400": "18.1",
                    "1722776700": "18.2",
                    "1722777000": "18.2",
                    "1722777300": "18.1",
                    "1722777600": "18.1",
                    "1722777900": "18.0",
                    "1722778200": "18.1",
                    "1722778500": "18.0",
                    "1722778800": "18.1",
                    "1722779100": "18.0",
                    "1722779400": "18.0",
                    "1722779700": "18.0",
                    "1722780000": "17.9",
                    "1722780300": "17.9",
                    "1722780600": "17.9",
                    "1722780900": "17.8",
                    "1722781200": "17.9",
                    "1722781500": "17.8",
                    "1722781800": "17.8",
                    "1722782100": "17.7",
                    "1722782400": "17.6",
                    "1722782700": "17.6",
                    "1722783000": "17.6",
                    "1722783300": "17.6",
                    "1722783600": "17.6",
                    "1722783900": "17.6",
                    "1722784200": "17.6",
                    "1722784500": "17.6",
                    "1722784800": "17.5",
                    "1722785100": "17.5",
                    "1722785400": "17.5",
                    "1722785700": "17.5",
                    "1722786000": "17.5",
                    "1722786300": "17.5",
                    "1722786600": "17.5",
                    "1722786900": "17.4",
                    "1722787200": "17.5"
                }
            }
        },
        "battery": {
            "haptic_array_battery": {
                "unit": "V",
                "list": {
                    "1722764400": "3.28",
                    "1722764700": "3.28",
                    "1722765000": "3.28",
                    "1722765300": "3.28",
                    "1722765600": "3.28",
                    "1722765900": "3.28",
                    "1722766200": "3.28",
                    "1722766500": "3.28",
                    "1722766800": "3.28",
                    "1722767100": "3.28",
                    "1722767400": "3.28",
                    "1722767700": "3.28",
                    "1722768000": "3.28",
                    "1722768300": "3.28",
                    "1722768600": "3.28",
                    "1722768900": "3.28",
                    "1722769200": "3.28",
                    "1722769500": "3.28",
                    "1722769800": "3.28",
                    "1722770100": "3.28",
                    "1722770400": "3.28",
                    "1722770700": "3.28",
                    "1722771000": "3.28",
                    "1722771300": "3.28",
                    "1722771600": "3.28",
                    "1722771900": "3.28",
                    "1722772200": "3.28",
                    "1722772500": "3.28",
                    "1722772800": "3.28",
                    "1722773100": "3.28",
                    "1722773400": "3.28",
                    "1722773700": "3.28",
                    "1722774000": "3.28",
                    "1722774300": "3.28",
                    "1722774600": "3.28",
                    "1722774900": "3.28",
                    "1722775200": "3.28",
                    "1722775500": "3.28",
                    "1722775800": "3.28",
                    "1722776100": "3.28",
                    "1722776400": "3.28",
                    "1722776700": "3.28",
                    "1722777000": "3.28",
                    "1722777300": "3.28",
                    "1722777600": "3.28",
                    "1722777900": "3.28",
                    "1722778200": "3.28",
                    "1722778500": "3.28",
                    "1722778800": "3.28",
                    "1722779100": "3.28",
                    "1722779400": "3.28",
                    "1722779700": "3.28",
                    "1722780000": "3.28",
                    "1722780300": "3.28",
                    "1722780600": "3.28",
                    "1722780900": "3.28",
                    "1722781200": "3.28",
                    "1722781500": "3.28",
                    "1722781800": "3.28",
                    "1722782100": "3.28",
                    "1722782400": "3.28",
                    "1722782700": "3.28",
                    "1722783000": "3.28",
                    "1722783300": "3.28",
                    "1722783600": "3.28",
                    "1722783900": "3.28",
                    "1722784200": "3.28",
                    "1722784500": "3.28",
                    "1722784800": "3.28",
                    "1722785100": "3.28",
                    "1722785400": "3.28",
                    "1722785700": "3.28",
                    "1722786000": "3.28",
                    "1722786300": "3.28",
                    "1722786600": "3.28",
                    "1722786900": "3.28",
                    "1722787200": "3.28"
                }
            },
            "haptic_array_capacitor": {
                "unit": "V",
                "list": {
                    "1722764400": "5.2",
                    "1722764700": "5.2",
                    "1722765000": "5.2",
                    "1722765300": "5.2",
                    "1722765600": "5.2",
                    "1722765900": "5.2",
                    "1722766200": "5.2",
                    "1722766500": "5.2",
                    "1722766800": "5.2",
                    "1722767100": "5.1",
                    "1722767400": "5.1",
                    "1722767700": "5.1",
                    "1722768000": "5.1",
                    "1722768300": "5.1",
                    "1722768600": "5.1",
                    "1722768900": "5.1",
                    "1722769200": "5.1",
                    "1722769500": "5.1",
                    "1722769800": "5.1",
                    "1722770100": "5.1",
                    "1722770400": "5.1",
                    "1722770700": "5.1",
                    "1722771000": "5.1",
                    "1722771300": "5.1",
                    "1722771600": "5.1",
                    "1722771900": "5.1",
                    "1722772200": "5.1",
                    "1722772500": "5.0",
                    "1722772800": "5.0",
                    "1722773100": "5.0",
                    "1722773400": "5.0",
                    "1722773700": "5.0",
                    "1722774000": "5.0",
                    "1722774300": "5.0",
                    "1722774600": "5.0",
                    "1722774900": "5.0",
                    "1722775200": "5.0",
                    "1722775500": "5.0",
                    "1722775800": "5.0",
                    "1722776100": "5.0",
                    "1722776400": "5.0",
                    "1722776700": "5.0",
                    "1722777000": "5.0",
                    "1722777300": "5.0",
                    "1722777600": "5.0",
                    "1722777900": "5.0",
                    "1722778200": "5.0",
                    "1722778500": "4.9",
                    "1722778800": "4.9",
                    "1722779100": "4.9",
                    "1722779400": "4.9",
                    "1722779700": "4.9",
                    "1722780000": "4.9",
                    "1722780300": "4.9",
                    "1722780600": "4.9",
                    "1722780900": "4.9",
                    "1722781200": "4.9",
                    "1722781500": "4.9",
                    "1722781800": "4.9",
                    "1722782100": "4.9",
                    "1722782400": "4.9",
                    "1722782700": "4.9",
                    "1722783000": "4.9",
                    "1722783300": "4.9",
                    "1722783600": "4.9",
                    "1722783900": "4.8",
                    "1722784200": "4.8",
                    "1722784500": "4.8",
                    "1722784800": "4.8",
                    "1722785100": "4.8",
                    "1722785400": "4.8",
                    "1722785700": "4.8",
                    "1722786000": "4.8",
                    "1722786300": "4.8",
                    "1722786600": "4.8",
                    "1722786900": "4.8",
                    "1722787200": "4.8"
                }
            },
            "soilmoisture_sensor_ch1": {
                "unit": "V",
                "list": {
                    "1722764400": "1.7",
                    "1722764700": "1.7",
                    "1722765000": "1.7",
                    "1722765300": "1.7",
                    "1722765600": "1.7",
                    "1722765900": "1.7",
                    "1722766200": "1.7",
                    "1722766500": "1.7",
                    "1722766800": "1.7",
                    "1722767100": "1.7",
                    "1722767400": "1.7",
                    "1722767700": "1.7",
                    "1722768000": "1.7",
                    "1722768300": "1.7",
                    "1722768600": "1.7",
                    "1722768900": "1.7",
                    "1722769200": "1.7",
                    "1722769500": "1.7",
                    "1722769800": "1.7",
                    "1722770100": "1.7",
                    "1722770400": "1.7",
                    "1722770700": "1.7",
                    "1722771000": "1.7",
                    "1722771300": "1.7",
                    "1722771600": "1.7",
                    "1722771900": "1.7",
                    "1722772200": "1.7",
                    "1722772500": "1.7",
                    "1722772800": "1.7",
                    "1722773100": "1.7",
                    "1722773400": "1.7",
                    "1722773700": "1.7",
                    "1722774000": "1.7",
                    "1722774300": "1.7",
                    "1722774600": "1.7",
                    "1722774900": "1.7",
                    "1722775200": "1.7",
                    "1722775500": "1.7",
                    "1722775800": "1.7",
                    "1722776100": "1.7",
                    "1722776400": "1.7",
                    "1722776700": "1.7",
                    "1722777000": "1.7",
                    "1722777300": "1.7",
                    "1722777600": "1.7",
                    "1722777900": "1.7",
                    "1722778200": "1.7",
                    "1722778500": "1.7",
                    "1722778800": "1.7",
                    "1722779100": "1.7",
                    "1722779400": "1.7",
                    "1722779700": "1.7",
                    "1722780000": "1.7",
                    "1722780300": "1.7",
                    "1722780600": "1.7",
                    "1722780900": "1.7",
                    "1722781200": "1.7",
                    "1722781500": "1.7",
                    "1722781800": "1.7",
                    "1722782100": "1.7",
                    "1722782400": "1.7",
                    "1722782700": "1.7",
                    "1722783000": "1.7",
                    "1722783300": "1.7",
                    "1722783600": "1.7",
                    "1722783900": "1.7",
                    "1722784200": "1.7",
                    "1722784500": "1.7",
                    "1722784800": "1.7",
                    "1722785100": "1.7",
                    "1722785400": "1.7",
                    "1722785700": "1.7",
                    "1722786000": "1.7",
                    "1722786300": "1.7",
                    "1722786600": "1.7",
                    "1722786900": "1.7",
                    "1722787200": "1.7"
                }
            },
            "soilmoisture_sensor_ch2": {
                "unit": "V",
                "list": {
                    "1722764400": "-",
                    "1722764700": "-",
                    "1722765000": "-",
                    "1722765300": "-",
                    "1722765600": "-",
                    "1722765900": "-",
                    "1722766200": "-",
                    "1722766500": "-",
                    "1722766800": "-",
                    "1722767100": "-",
                    "1722767400": "-",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "-",
                    "1722770100": "-",
                    "1722770400": "-",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "-",
                    "1722772500": "-",
                    "1722772800": "-",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "-",
                    "1722778500": "-",
                    "1722778800": "-",
                    "1722779100": "-",
                    "1722779400": "-",
                    "1722779700": "-",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "-",
                    "1722783300": "-",
                    "1722783600": "-",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "-",
                    "1722784800": "-",
                    "1722785100": "-",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            },
            "soilmoisture_sensor_ch3": {
                "unit": "V",
                "list": {
                    "1722764400": "-",
                    "1722764700": "-",
                    "1722765000": "-",
                    "1722765300": "-",
                    "1722765600": "-",
                    "1722765900": "-",
                    "1722766200": "-",
                    "1722766500": "-",
                    "1722766800": "-",
                    "1722767100": "-",
                    "1722767400": "-",
                    "1722767700": "-",
                    "1722768000": "-",
                    "1722768300": "-",
                    "1722768600": "-",
                    "1722768900": "-",
                    "1722769200": "-",
                    "1722769500": "-",
                    "1722769800": "-",
                    "1722770100": "-",
                    "1722770400": "-",
                    "1722770700": "-",
                    "1722771000": "-",
                    "1722771300": "-",
                    "1722771600": "-",
                    "1722771900": "-",
                    "1722772200": "-",
                    "1722772500": "-",
                    "1722772800": "-",
                    "1722773100": "-",
                    "1722773400": "-",
                    "1722773700": "-",
                    "1722774000": "-",
                    "1722774300": "-",
                    "1722774600": "-",
                    "1722774900": "-",
                    "1722775200": "-",
                    "1722775500": "-",
                    "1722775800": "-",
                    "1722776100": "-",
                    "1722776400": "-",
                    "1722776700": "-",
                    "1722777000": "-",
                    "1722777300": "-",
                    "1722777600": "-",
                    "1722777900": "-",
                    "1722778200": "-",
                    "1722778500": "-",
                    "1722778800": "-",
                    "1722779100": "-",
                    "1722779400": "-",
                    "1722779700": "-",
                    "1722780000": "-",
                    "1722780300": "-",
                    "1722780600": "-",
                    "1722780900": "-",
                    "1722781200": "-",
                    "1722781500": "-",
                    "1722781800": "-",
                    "1722782100": "-",
                    "1722782400": "-",
                    "1722782700": "-",
                    "1722783000": "-",
                    "1722783300": "-",
                    "1722783600": "-",
                    "1722783900": "-",
                    "1722784200": "-",
                    "1722784500": "-",
                    "1722784800": "-",
                    "1722785100": "-",
                    "1722785400": "-",
                    "1722785700": "-",
                    "1722786000": "-",
                    "1722786300": "-",
                    "1722786600": "-",
                    "1722786900": "-",
                    "1722787200": "-"
                }
            },
            "temperature_sensor_ch1": {
                "unit": "V",
                "list": {
                    "1722764400": "1.56",
                    "1722764700": "1.56",
                    "1722765000": "1.56",
                    "1722765300": "1.56",
                    "1722765600": "1.56",
                    "1722765900": "1.56",
                    "1722766200": "1.56",
                    "1722766500": "1.56",
                    "1722766800": "1.56",
                    "1722767100": "1.56",
                    "1722767400": "1.56",
                    "1722767700": "1.56",
                    "1722768000": "1.56",
                    "1722768300": "1.56",
                    "1722768600": "1.56",
                    "1722768900": "1.56",
                    "1722769200": "1.56",
                    "1722769500": "1.56",
                    "1722769800": "1.56",
                    "1722770100": "1.56",
                    "1722770400": "1.54",
                    "1722770700": "1.54",
                    "1722771000": "1.55",
                    "1722771300": "1.56",
                    "1722771600": "1.56",
                    "1722771900": "1.56",
                    "1722772200": "1.56",
                    "1722772500": "1.56",
                    "1722772800": "1.56",
                    "1722773100": "1.56",
                    "1722773400": "1.56",
                    "1722773700": "1.56",
                    "1722774000": "1.56",
                    "1722774300": "1.56",
                    "1722774600": "1.56",
                    "1722774900": "1.56",
                    "1722775200": "1.56",
                    "1722775500": "1.56",
                    "1722775800": "1.56",
                    "1722776100": "1.56",
                    "1722776400": "1.56",
                    "1722776700": "1.56",
                    "1722777000": "1.56",
                    "1722777300": "1.56",
                    "1722777600": "1.56",
                    "1722777900": "1.56",
                    "1722778200": "1.56",
                    "1722778500": "1.56",
                    "1722778800": "1.56",
                    "1722779100": "1.56",
                    "1722779400": "1.56",
                    "1722779700": "1.56",
                    "1722780000": "1.56",
                    "1722780300": "1.56",
                    "1722780600": "1.56",
                    "1722780900": "1.56",
                    "1722781200": "1.56",
                    "1722781500": "1.56",
                    "1722781800": "1.56",
                    "1722782100": "1.56",
                    "1722782400": "1.56",
                    "1722782700": "1.56",
                    "1722783000": "1.56",
                    "1722783300": "1.56",
                    "1722783600": "1.56",
                    "1722783900": "1.56",
                    "1722784200": "1.56",
                    "1722784500": "1.56",
                    "1722784800": "1.56",
                    "1722785100": "1.56",
                    "1722785400": "1.56",
                    "1722785700": "1.56",
                    "1722786000": "1.56",
                    "1722786300": "1.56",
                    "1722786600": "1.56",
                    "1722786900": "1.56",
                    "1722787200": "1.56"
                }
            }
        }
    }
}"""


class EcowittBackfill:
    """Class to handle backfill via Ecowitt.net API.

    Ecowitt gateway devices do not include a hardware logger; however, they
    do have the ability to independently upload observation data to
    Ecowitt.net at various integer minute intervals from one to five
    minutes. Ecowitt provides an API to access this history data at
    Ecowitt.net. The Ecowitt.net history data provides a means for
    obtaining historical archive data, the data will likely differ slightly
    in values and times to the gateway generated archive data, but it may
    provide an effective 'virtual' logger capability to support backfill on
    startup.

    """

    # Ecowitt.net API endpoint
    endpoint = 'https://api.ecowitt.net/api/v3/device'
    # available Ecowitt.net API commands
    commands = ('real_time', 'history', 'list', 'info')
    # Ecowitt.net API result codes
    api_result_codes = {
        -1: 'System is busy',
        0: 'success result',
        40000: 'Illegal parameter',
        40010: 'Illegal Application_Key Parameter',
        40011: 'Illegal Api_Key Parameter',
        40012: 'Illegal MAC/IMEI Parameter',
        40013: 'Illegal start_date Parameter',
        40014: 'Illegal end_date Parameter',
        40015: 'Illegal cycle_type Parameter',
        40016: 'Illegal call_back Parameter',
        40017: 'Missing Application_Key Parameter',
        40018: 'Missing Api_Key Parameter',
        40019: 'Missing MAC Parameter',
        40020: 'Missing start_date Parameter',
        40021: 'Missing end_date Parameter',
        40022: 'Illegal Voucher type',
        43001: 'Needs other service support',
        44001: 'Media file or data packet is null',
        45001: 'Over the limit or other error',
        46001: 'No existing request',
        47001: 'Parse JSON/XML contents error',
        48001: 'Privilege Problem'
    }
    # default history call back
    default_call_back = ('outdoor', 'indoor', 'solar_and_uvi', 'rainfall',
                         'rainfall_piezo', 'wind', 'pressure', 'lightning',
                         'indoor_co2', 'pm25_ch1', 'pm25_ch2', 'pm25_ch3',
                         'pm25_ch4', 'co2_aqi_combo', 'pm25_aqi_combo',
                         'pm10_aqi_combo', 'pm1_aqi_combo', 't_rh_aqi_combo',
                         'temp_and_humidity_ch1', 'temp_and_humidity_ch2',
                         'temp_and_humidity_ch3', 'temp_and_humidity_ch4',
                         'temp_and_humidity_ch5', 'temp_and_humidity_ch6',
                         'temp_and_humidity_ch7', 'temp_and_humidity_ch8',
                         'soil_ch1', 'soil_ch2', 'soil_ch3', 'soil_ch4',
                         'soil_ch5', 'soil_ch6', 'soil_ch7', 'soil_ch8',
                         'temp_ch1', 'temp_ch2', 'temp_ch3', 'temp_ch4',
                         'temp_ch5', 'temp_ch6', 'temp_ch7', 'temp_ch8',
                         'leaf_ch1', 'leaf_ch2', 'leaf_ch3', 'leaf_ch4',
                         'leaf_ch5', 'leaf_ch6', 'leaf_ch7', 'leaf_ch8',
                         'battery')
    # Map from Ecowitt.net history fields to internal driver fields. Map is
    # keyed by Ecowitt.net history 'data set'. Individual key: value pairs are
    # Ecowitt.net field:driver field.
    net_to_driver_map = {
        'outdoor': {
            'temperature': 'outtemp',
            'humidity': 'outhumid'
        },
        'indoor': {
            'temperature': 'intemp',
            'humidity': 'inhumid'
        },
        'solar_and_uvi': {
            'solar': 'radiation',
            'uvi': 'uvi'
        },
        'rainfall': {
            'rain_rate': 't_rainrate',
            'event': 't_rainevent',
            'hourly': 't_rainday',
            'daily': 't_rainhour',
            'weekly': 't_rainweek',
            'monthly': 't_rainmonth',
            'yearly': 't_rainyear',
        },
        'rainfall_piezo': {
            'rain_rate': 'p_rainrate',
            'event': 'p_rainevent',
            'hourly': 'p_rainday',
            'daily': 'p_rainhour',
            'weekly': 'p_rainweek',
            'monthly': 'p_rainmonth',
            'yearly': 'p_rainyear',
        },
        'wind': {
            'wind_speed': 'windspeed',
            'wind_gust': 'gustspeed',
            'wind_direction': 'winddir'
        },
        'pressure': {
            'absolute': 'absbarometer',
            'relative': 'relbarometer'
        },
        'lightning': {
            'distance': 'lightningdist',
            'count': 'lightningcount'
        },
        # 'indoor_co2': {
        #     'co2': '',
        #     '24_hours_average': ''
        # },
        'pm25_ch1': {
            'pm25': 'pm251'
        },
        'pm25_ch2': {
            'pm25': 'pm252'
        },
        'pm25_ch3': {
            'pm25': 'pm253'
        },
        'pm25_ch4': {
            'pm25': 'pm254'
        },
        'co2_aqi_combo': {
            'co2': '',
            '24_hours_average': ''
        },
        'pm25_aqi_combo': {
            'pm25': 'pm255',
            'real_time_aqi': '',
            '24_hours_aqi': ''
        },
        'pm10_aqi_combo': {
            'pm10': 'pm10',
            'real_time_aqi': '',
            '24_hours_aqi': ''
        },
        'pm1_aqi_combo': {
            'pm1': 'pm1',
            'real_time_aqi': '',
            '24_hours_aqi': ''
        },
        'pm4_aqi_combo': {
            'pm4': 'pm4',
            'real_time_aqi': '',
            '24_hours_aqi': ''
        },
        't_rh_aqi_combo': {
            'temperature': '',
            'humidity': ''
        },
        'temp_and_humidity_ch1': {
            'temperature': 'temp1',
            'humidity': 'humid1'
        },
        'temp_and_humidity_ch2': {
            'temperature': 'temp2',
            'humidity': 'humid2'
        },
        'temp_and_humidity_ch3': {
            'temperature': 'temp3',
            'humidity': 'humid3'
        },
        'temp_and_humidity_ch4': {
            'temperature': 'temp4',
            'humidity': 'humid4'
        },
        'temp_and_humidity_ch5': {
            'temperature': 'temp5',
            'humidity': 'humid5'
        },
        'temp_and_humidity_ch6': {
            'temperature': 'temp6',
            'humidity': 'humid6'
        },
        'temp_and_humidity_ch7': {
            'temperature': 'temp7',
            'humidity': 'humid7'
        },
        'temp_and_humidity_ch8': {
            'temperature': 'temp8',
            'humidity': 'humid8'
        },
        'soil_ch1': {
            'soilmoisture': 'soilmoist1'
        },
        'soil_ch2': {
            'soilmoisture': 'soilmoist2'
        },
        'soil_ch3': {
            'soilmoisture': 'soilmoist3'
        },
        'soil_ch4': {
            'soilmoisture': 'soilmoist4'
        },
        'soil_ch5': {
            'soilmoisture': 'soilmoist5'
        },
        'soil_ch6': {
            'soilmoisture': 'soilmoist6'
        },
        'soil_ch7': {
            'soilmoisture': 'soilmoist7'
        },
        'soil_ch8': {
            'soilmoisture': 'soilmoist8'
        },
        'temp_ch1': {
            'temperature': 'temp9'
        },
        'temp_ch2': {
            'temperature': 'temp10'
        },
        'temp_ch3': {
            'temperature': 'temp11'
        },
        'temp_ch4': {
            'temperature': 'temp12'
        },
        'temp_ch5': {
            'temperature': 'temp13'
        },
        'temp_ch6': {
            'temperature': 'temp14'
        },
        'temp_ch7': {
            'temperature': 'temp15'
        },
        'temp_ch8': {
            'temperature': 'temp16'
        },
        'leaf_ch1': {
            'leaf_wetness': 'leafwet1'
        },
        'leaf_ch2': {
            'leaf_wetness': 'leafwet2'
        },
        'leaf_ch3': {
            'leaf_wetness': 'leafwet3'
        },
        'leaf_ch4': {
            'leaf_wetness': 'leafwet4'
        },
        'leaf_ch5': {
            'leaf_wetness': 'leafwet5'
        },
        'leaf_ch6': {
            'leaf_wetness': 'leafwet6'
        },
        'leaf_ch7': {
            'leaf_wetness': 'leafwet7'
        },
        'leaf_ch8': {
            'leaf_wetness': 'leafwet8'
        },
        'battery': {
            # 'ws1900_console': '',
            # 'ws1800_console': '',
            # 'ws6006_console': '',
            # 'console': '',
            # 'wind_sensor': '',
            # 'haptic_array_battery': '',
            # 'haptic_array_capacitor': '',
            # 'sonic_array': '',
            # 'rainfall_sensor': '',
            'soilmoisture_sensor_ch1': 'wh51_ch1_batt',
            'soilmoisture_sensor_ch2': 'wh51_ch2_batt',
            'soilmoisture_sensor_ch3': 'wh51_ch3_batt',
            'soilmoisture_sensor_ch4': 'wh51_ch4_batt',
            'soilmoisture_sensor_ch5': 'wh51_ch5_batt',
            'soilmoisture_sensor_ch6': 'wh51_ch6_batt',
            'soilmoisture_sensor_ch7': 'wh51_ch7_batt',
            'soilmoisture_sensor_ch8': 'wh51_ch8_batt',
            'temperature_sensor_ch1': 'wn34_ch1_batt',
            'temperature_sensor_ch2': 'wn34_ch2_batt',
            'temperature_sensor_ch3': 'wn34_ch3_batt',
            'temperature_sensor_ch4': 'wn34_ch4_batt',
            'temperature_sensor_ch5': 'wn34_ch5_batt',
            'temperature_sensor_ch6': 'wn34_ch6_batt',
            'temperature_sensor_ch7': 'wn34_ch7_batt',
            'temperature_sensor_ch8': 'wn34_ch8_batt',
            'leaf_wetness_sensor_ch1': 'wn35_ch1_batt',
            'leaf_wetness_sensor_ch2': 'wn35_ch2_batt',
            'leaf_wetness_sensor_ch3': 'wn35_ch3_batt',
            'leaf_wetness_sensor_ch4': 'wn35_ch4_batt',
            'leaf_wetness_sensor_ch5': 'wn35_ch5_batt',
            'leaf_wetness_sensor_ch6': 'wn35_ch6_batt',
            'leaf_wetness_sensor_ch7': 'wn35_ch7_batt',
            'leaf_wetness_sensor_ch8': 'wn35_ch8_batt'
        }
    }

    def __init__(self, api_key, app_key, mac):
        """Initialise an EcowittBackfill object."""

        # save the user Ecowitt.net API key
        self.api_key = api_key
        # save the user Ecowitt.net application key
        self.app_key = app_key
        # save the device MAC address
        self.mac = mac

    def gen_history_records(self, start_ts, stop_ts=None, **kwargs):
        """Generate archive-like records from Ecowitt.net API history data.

        Generator function that uses the Ecowitt.net API to obtain history data
        from Ecowitt.net and generate archive-like records suitable for
        backfill by the WeeWX Ecowitt gateway driver. Generated records are
        timestamped from start_ts to stop_ts inclusive. If stop_ts is not
        specified records are generated up to an including the current system
        time.

        start_ts: Earliest timestamp for which archive-like records are to be
                  emitted. Mandatory, integer.
        stop_ts:  Latest timestamp for which archive-like records are to be
                  emitted. If not specified or specified as None the current
                  system time is used instead. Optional, integer or None.

        Keyword Arguments. Supported keyword arguments include:
        call_back: Tuple containing the Ecowitt.net history data set names to
                   be sought in the API request. If not specified the default
                   call back data sets (EcowittBackfill.default_call_back) are
                   used. Optional, tuple of strings.
        """

        # use the current system time if stop_ts was not specified
        adj_stop_ts = int(time.time()) if stop_ts is None else stop_ts
        # construct the call_back, this specifies the data sets to be included
        # in the API history request
        # first check if we were given a call_back to use, if not use the
        # default
        _call_back = kwargs.get('call_back') if 'call_back' in kwargs else self.default_call_back
        # construct the call_back string; the call_back is specified in a tuple
        # but the API requires a comma separated string
        call_back = ','.join(_call_back)
        # we can only obtain a max of one days data at a time from Ecowitt.net
        # so split our interval into a series of 'day' spans
        for t_span in weeutil.weeutil.genDaySpans(start_ts, adj_stop_ts):
            # construct a dict containing the data elements to be included in
            # the API request
            data = {
                'application_key': self.app_key,
                'api_key': self.api_key,
                'mac': self.mac,
                'start_date': datetime.fromtimestamp(t_span.start).strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': datetime.fromtimestamp(t_span.stop).strftime('%Y-%m-%d %H:%M:%S'),
                'call_back': call_back,
                'cycle_type': '5min',
                'temp_unitid': 1,
                'pressure_unitid': 3,
                'wind_speed_unitid': 6,
                'rainfall_unitid': 12,
                'solar_irradiance_unitid': 16
            }
            # Obtain a day of history data via the Ecowitt.net API. We will
            # either receive data or encounter an exception if the request
            # failed or the data invalid. So wrap in a try .. except to catch
            # and handle any exceptions.
            try:
                day_data = self.request(command_str='history', data=data, headers=None)
            except (socket.timeout, urllib.error.URLError,
                    InvalidApiResponseError, ApiResponseError) as e:
                # A technical comms error was encountered or the response
                # received contains invalid data, either way we cannot
                # continue. Either way any logging has already occurred so just
                # raise the exception
                raise
            else:
                # parse the raw day data, this will give us an iterable we can
                # traverse to construct archive-like records for the day
                parsed_day_data = self.parse_history(day_data.get('data', dict()))
                # traverse the timestamped data for the day and construct and
                # yield records, we need the timestamps in ascending order
                for ts in sorted(parsed_day_data.keys()):
                    # ensure we are only yielding timestamps within our span of
                    # interest
                    if start_ts <= ts <= adj_stop_ts:
                        # construct an outline record, the timestamp is the
                        # current timestamp in our parsed data
                        rec = {'datetime': ts}
                        # add the rest of the parsed day dat for this timestamp
                        rec.update(parsed_day_data[ts])
                        # yield the archive-like record
                        yield rec

    def request(self, command_str, data=None, headers=None):
        """Send a HTTP request to the Ecowitt.net API and return the response.

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
        if command_str in EcowittBackfill.commands:
            # first convert any data to a percent-encoded ASCII text string
            data_enc = urllib.parse.urlencode(data_dict)
            # construct the endpoint and 'path' of the URL
            endpoint_path = '/'.join([EcowittBackfill.endpoint, command_str])
            # Finally add the encoded data. We need to add the data in this manner
            # rather than using the Request object's 'data' parameter so that the
            # request is sent as a GET request rather than a POST request.
            url = '?'.join([endpoint_path, data_enc])
            # create a Request object
            req = urllib.request.Request(url=url, headers=headers_dict)
            try:
                # submit the request and obtain the raw response
                with urllib.request.urlopen(req) as w:
                    # get charset used so we can decode the stream correctly
                    char_set = w.headers.get_content_charset()
                    # Now get the response and decode it using the headers
                    # character set. Be prepared for charset==None.
                    if char_set is not None:
                        response = w.read().decode(char_set)
                    else:
                        response = w.read().decode()
            except (socket.timeout, urllib.error.URLError) as e:
                # log the error and raise it
                log.error("Failed to obtain data from Ecowitt.net")
                log.error("   **** %s" % e)
                raise
            # we have a response, but first check it for validity
            try:
                return self.check_response(response)
            except (InvalidApiResponseError, ApiResponseError) as e:
                # the response was not valid, log it and attempt again
                # if we haven't had too many attempts already
#                if self.debug:
                log.error(f"Invalid Ecowitt.net API response: {e}")
            except Exception as e:
                # Some other error occurred in check_response(),
                # perhaps the response was malformed. Log the stack
                # trace but continue.
                raise

    def check_response(self, response):
        """Check the validity of an API response.

        Checks the validity of an API response. Three checks are performed:

        1.  the response has a length > 0
        2.  the response is valid JSON
        3.  the response contains a field 'code' with the value 0

        If any check fails an appropriate exception is raised, if all checks
        pass the decoded JSON response is returned.

        response: Raw, character set decoded response from a HTTP request the
        Ecowitt.net API.

        Returns a deserialized JSON object or raises an exception.
        """

        # do we have a response
        if response is not None and len(response) > 0:
            # we have some sort of response, but is it JSON and is the response
            # code 0
            try:
                # attempt to decode the response as JSON
                json_resp = json.loads(response)
            except json.JSONDecodeError as e:
                # the response could not be decoded as JSON, raise an
                # InvalidApiResponseError exception
                raise InvalidApiResponseError(e)
            # we have JSON format response, but does the response contain
            # 'code' == 0
            if json_resp.get('code') == 0:
                # we have valid JSO0 and a (sic) 'success result', return the
                # JSON format response
                return json_resp
            else:
                # we have a non-zero 'code', raise an ApiResponseError
                # exception with a suitable error message
                code = json_resp.get('code', 'no code')
                raise ApiResponseError(f"Received API response error code "
                                       f"'{code}': {self.api_result_codes.get(code)}")
        else:
            # response is None or zero length, raise an InvalidApiResponseError
            # exception
            raise InvalidApiResponseError(f"Invalid API response received")

    def parse_history(self, history_data):
        """Parse Ecowitt.net history data"""

#        history_data = json.loads(self.d).get('data', dict())
        # initialise a dict to hold the parsed data
        result = dict()
        # iterate over each set of data in history_data
        for set_name, set_data in history_data.items():
            # obtain the parsed set data
            parsed_set_data = self.parse_data_set(set_name, set_data)
            # the parsed set data is a dict of data keyed by timestamp, iterate
            # over each timestamp: data pair and add the data to the
            # corresponding timestamp in the parsed data accumulated so far
            for ts, ts_data in parsed_set_data.items():
                # if we have not previously seen this timestamp add an entry to
                # the parsed data results
                if ts not in result:
                    result[ts] = dict()
                # update the accumulated parsed data with the current parsed
                # data
                result[ts].update(ts_data)
        # return the accumulated parsed data
        return result

    def parse_data_set(self, set_name, data):
        """Parse a data set containing one or more observation types."""

        # initialise a dict to hold our accumulated results
        result = dict()
        # iterate over each observation type and its data in the data set
        for obs, obs_data in data.items():
            # obtain the field name to use, this is an internal
            field_name = self.get_field_name(set_name, obs)
            # if the field name is not None then add the current obs type data
            # to our results, if the field name is None then skip this obs type
            if field_name is not None:
                # obtain the parsed obs type data
                parsed_data = self.parse_float(obs_data)
                # iterate over the timestamp: data pairs and add them to our
                # accumulated results
                for ts, value in parsed_data.items():
                    # if we have not previously seen this timestamp add an
                    # entry to the parsed data results
                    if ts not in result:
                        result[ts] = dict()
                    # update the accumulated parsed data with the current
                    # parsed data
                    result[ts][field_name] = value
        # return the accumulated results
        return result

    @staticmethod
    def parse_float(data):
        """Parse an observation type consisting of floating point data.

        Each data set (eg 'outdoor', 'indoor', 'pressure' etc) equates to a
        JSON object (eg "outdoor", "indoor", "pressure" etc) and consists of
        one or more observation types (eg 'temperature', 'feels_like' etc)
        which also equate to JSON objects (eg "temperature", "feels_like" etc)
        containing timestamped observation values. Currently, this timestamped
        data exists in the JSON object "list" as a sequence of timestamp:value
        pairs where timestamp is a unix epoch timestamp enclosed in quotes and
        value is a numeric observation value again enclosed in quotes.

        The JSON "list" object is processed with each timestamp converted to an
        integer and the corresponding value converted to a floating point
        number. A dict of converted numeric timestamp:value pair is returned.
        The return dict may be in ascending timestamp order, but this is not
        guaranteed. If a timestamp string cannot be converted to an integer the
        timestamp:value pair is ignored. If a value cannot be converted to a
        floating point number the value is set to None.

        Example JSON data extract showing the 'outdoor' data set including the
        'temperature' and 'feels_like' observation types:

        ....
        "data": {
            "outdoor": {
                "temperature": {
                    "unit": "℃",
                    "list": {
                        "1722764400": "16.8",
                        "1722764700": "16.8",
                        "1722765000": "16.7",
                        "1722765300": "16.7"
                    }
                },
                "feels_like": {
                    "unit": "℃",
                    "list": {
                        "1722764400": "16.8",
                        "1722764700": "16.8",
                        "1722765000": "16.7",
                        "1722765300": "16.7"
                    }
                },
                ....
            },
            ....
        },
        ....
        """

        # initialise a dict to hold the result
        result = dict()
        # iterate over each ts, value pair in the 'list' entry in the source
        # data
        for ts_string, value_str in data['list'].items():
            # the ts is a string, try to convert to an int, if we cannot
            # skip the ts
            try:
                ts = int(ts_string)
            except ValueError:
                continue
            # Convert the value to a float and save to our result dict, if we
            # cannot convert to a float then save the value None
            try:
                result[ts] = float(value_str)
            except ValueError:
                result[ts] = None
        # return the result
        return result

    def get_field_name(self, set_name, obs):
        """Determine the destination field name to be used.

        The field names used in an Ecowitt.net API history response are
        different to those field names used internally within the Ecowitt
        gateway driver. To allow Ecowitt.net API history obs data to be used by
        the Ecowitt gateway driver each Ecowitt.net API obs data field must be
        mapped to an Ecowitt gateway driver internal field.

        Some Ecowitt.net API history fields are not used by the Ecowitt gateway
        driver and can be ignored. In these cases the value None is returned.

        Given an Ecowitt.net history set name and obs type a lookup table can
        be used to determine the applicable Ecowitt gateway driver internal
        field.
        """

        # wrap in a try .. except so we can catch those API fields we will
        # ignore (ie not in the lookup table)
        try:
            # Obtain the driver field name from the lookup table. If the
            # Ecowitt.net history field is to be ignored there will be no
            # lookup table entry resulting in a KeyError.
            return self.net_to_driver_map[set_name][obs]
        except KeyError:
            # we can ignore this API field so return None
            return None


def define_units():
    """Define formats and conversions used by the driver.

    This could be done in user/extensions.py or the driver. The
    user/extensions.py approach will make the conversions and formats available
    for all drivers and services, but requires manual editing of the file by
    the user. Inclusion in the driver removes the need for the user to edit
    user/extensions.py, but means the conversions and formats are only defined
    when the driver is being used. Given the specialised nature of the
    conversions and formats the latter is an acceptable approach. In any case,
    there is nothing preventing the user manually adding these entries to
    user/extensions.py.

    As of v5.0.0 WeeWX defines the unit group 'group_data' with member units
    'byte' and 'bit'. We will define additional group_data member units of
    'kilobyte' and 'megabyte'.

    All additions to the core conversion, label and format dicts are done in a
    way that do not overwrite and previous customisations the user may have
    made through another driver or user/extensions.py.
    """

    # add kilobyte and megabyte conversions
    if 'byte' not in weewx.units.conversionDict:
        # 'byte' is not a key in the conversion dict, so we add all conversions
        weewx.units.conversionDict['byte'] = {'bit': lambda x: x * 8,
                                              'kilobyte': lambda x: x / 1024.0,
                                              'megabyte': lambda x: x / 1024.0 ** 2}
    else:
        # byte already exists as a key in the conversion dict, so we add all
        # conversions individually if they do not already exist
        if 'bit' not in weewx.units.conversionDict['byte'].keys():
            weewx.units.conversionDict['byte']['bit'] = lambda x: x * 8
        if 'kilobyte' not in weewx.units.conversionDict['byte'].keys():
            weewx.units.conversionDict['byte']['kilobyte'] = lambda x: x / 1024.0
        if 'megabyte' not in weewx.units.conversionDict['byte'].keys():
            weewx.units.conversionDict['byte']['megabyte'] = lambda x: x / 1024.0 ** 2
    if 'kilobyte' not in weewx.units.conversionDict:
        weewx.units.conversionDict['kilobyte'] = {'bit': lambda x: x * 8192,
                                                  'byte': lambda x: x * 1024,
                                                  'megabyte': lambda x: x / 1024.0}
    else:
        # kilobyte already exists as a key in the conversion dict, so we add
        # all conversions individually if they do not already exist
        if 'bit' not in weewx.units.conversionDict['kilobyte'].keys():
            weewx.units.conversionDict['kilobyte']['bit'] = lambda x: x * 8192
        if 'byte' not in weewx.units.conversionDict['kilobyte'].keys():
            weewx.units.conversionDict['kilobyte']['byte'] = lambda x: x * 1024
        if 'megabyte' not in weewx.units.conversionDict['kilobyte'].keys():
            weewx.units.conversionDict['kilobyte']['megabyte'] = lambda x: x / 1024.0
    if 'megabyte' not in weewx.units.conversionDict:
        weewx.units.conversionDict['megabyte'] = {'bit': lambda x: x * 8 * 1024 ** 2,
                                                  'byte': lambda x: x * 1024 ** 2,
                                                  'kilobyte': lambda x: x * 1024}
    else:
        # megabyte already exists as a key in the conversion dict, so we add
        # all conversions individually if they do not already exist
        if 'bit' not in weewx.units.conversionDict['megabyte'].keys():
            weewx.units.conversionDict['megabyte']['bit'] = lambda x: x * 8 * 1024 ** 2
        if 'byte' not in weewx.units.conversionDict['megabyte'].keys():
            weewx.units.conversionDict['megabyte']['byte'] = lambda x: x * 1024 ** 2
        if 'kilobyte' not in weewx.units.conversionDict['megabyte'].keys():
            weewx.units.conversionDict['megabyte']['kilobyte'] = lambda x: x * 1024

    # set default formats and labels for byte, kilobyte and megabyte, but only
    # if they do not already exist
    weewx.units.default_unit_format_dict['byte'] = weewx.units.default_unit_format_dict.get('byte') or '%.d'
    weewx.units.default_unit_label_dict['byte'] = weewx.units.default_unit_label_dict.get('byte') or u' B'
    weewx.units.default_unit_format_dict['kilobyte'] = weewx.units.default_unit_format_dict.get('kilobyte') or '%.3f'
    weewx.units.default_unit_label_dict['kilobyte'] = weewx.units.default_unit_label_dict.get('kilobyte') or u' kB'
    weewx.units.default_unit_format_dict['megabyte'] = weewx.units.default_unit_format_dict.get('megabyte') or '%.3f'
    weewx.units.default_unit_label_dict['megabyte'] = weewx.units.default_unit_label_dict.get('megabyte') or u' MB'

    # merge the default unit groups into weewx.units.obs_group_dict, but so we
    # don't undo any user customisation elsewhere only merge those fields that do
    # not already exits in weewx.units.obs_group_dict
    for obs, group in six.iteritems(default_groups):
        if obs not in weewx.units.obs_group_dict.keys():
            weewx.units.obs_group_dict[obs] = group


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
    sorted_dict_fields = ["'%s': '%s'" % (k, source_dict[k]) for k in natural_sort_keys(source_dict)]
    # return as a string of comma separated key:value pairs in braces
    return "{%s}" % ", ".join(sorted_dict_fields)

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
    else:
        # if we received None or a zero length string then return it
        return plain


# To use this driver in standalone mode for testing or development, use one of
# the following commands (depending on your WeeWX install). For setup.py
# installs use:
#
#   $ PYTHONPATH=/home/weewx/bin python -m user.gw1000
#
# or for package installs use:
#
#   $ PYTHONPATH=/usr/share/weewx python -m user.gw1000
#
# The above api_commands will display details of available command line options.
#
# Note. Whilst the driver may be run independently of WeeWX the driver still
# requires WeeWX and it's dependencies be installed. Consequently, if
# WeeWX 4.0.0 or later is installed the driver must be run under the same
# Python version as WeeWX uses. This means that on some systems 'python' in the
# above api_commands may need to be changed to 'python2' or 'python3'.

def main():
    import optparse

    usage = """Usage: python -m user.gw1000 --help
       python -m user.gw1000 --version
       python -m user.gw1000 --test-driver|--test-service
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--poll-interval=INTERVAL]
            [--max-tries=MAX_TRIES]
            [--retry-wait=RETRY_WAIT]
            [--show-all-batt]
            [--debug=0|1|2|3]
       python -m user.gw1000 --live-data
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--units=us|metric|metricwx]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--show-all-batt]
            [--debug=0|1|2|3]
       python -m user.gw1000 --default-map|--driver-map|--service-map
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--debug=0|1|2|3]
       python -m user.gw1000 --discover
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--debug=0|1|2|3]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version number')
    parser.add_option('--discover', dest='discover', action='store_true',
                      help='discover devices and display device IP address '
                           'and port')
    parser.add_option('--live-data', dest='live', action='store_true',
                      help='display device live sensor data')
    parser.add_option('--test-driver', dest='test_driver', action='store_true',
                      metavar='TEST_DRIVER', help='exercise the gateway driver')
    parser.add_option('--test-service', dest='test_service',
                      action='store_true', metavar='TEST_SERVICE',
                      help='exercise the gateway service')
    parser.add_option('--default-map', dest='map', action='store_true',
                      help='display the default field map')
    parser.add_option('--driver-map', dest='driver_map', action='store_true',
                      help='display the field map that would be used by the gateway '
                           'driver')
    parser.add_option('--service-map', dest='service_map', action='store_true',
                      help='display the field map that would be used by the gateway '
                           'service')
    parser.add_option('--ip-address', dest='ip_address',
                      help='device IP address to use')
    parser.add_option('--port', dest='port', type=int,
                      help='device port to use')
    parser.add_option('--poll-interval', dest='poll_interval', type=int,
                      help='how often to poll the device API')
    parser.add_option('--max-tries', dest='max_tries', type=int,
                      help='max number of attempts to contact the device')
    parser.add_option('--retry-wait', dest='retry_wait', type=int,
                      help='how long to wait between attempts to contact the device')
    parser.add_option('--show-all-batt', dest='show_battery',
                      action='store_true',
                      help='show all available battery state data regardless of '
                           'sensor state')
    parser.add_option('--unmask', dest='unmask', action='store_true',
                      help='unmask sensitive settings')
    parser.add_option('--units', dest='units', metavar='UNITS', default='metric',
                      help='unit system to use when displaying live data')
    parser.add_option('--config', dest='config_path', metavar='CONFIG_FILE',
                      help="Use configuration file CONFIG_FILE.")
    parser.add_option('--debug', dest='debug', type=int,
                      help='How much status to display, 0-3')
    (opts, args) = parser.parse_args()

    # display driver version number
    if opts.version:
        print("%s driver version: %s" % (DRIVER_NAME, DRIVER_VERSION))
        exit(0)

    # get config_dict to use
    config_path, config_dict = weecfg.read_config(opts.config_path, args)
    print("Using configuration file %s" % config_path)
    stn_dict = config_dict.get('GW1000', {})

    # set weewx.debug as necessary
    if opts.debug is not None:
        _debug = weeutil.weeutil.to_int(opts.debug)
    else:
        _debug = weeutil.weeutil.to_int(config_dict.get('debug', 0))
    weewx.debug = _debug
    # inform the user if the debug level is 'higher' than 0
    if _debug > 0:
        print("debug level is '%d'" % _debug)

    # Now we can set up the user customized logging, but we need to handle both
    # v3 and v4 logging. V4 logging is very easy but v3 logging requires us to
    # set up syslog and raise our log level based on weewx.debug
    try:
        # assume v 4 logging
        weeutil.logger.setup('weewx', config_dict)
    except AttributeError:
        # must be v3 logging, so first set the defaults for the system logger
        syslog.openlog('weewx', syslog.LOG_PID | syslog.LOG_CONS)
        # now raise the log level if required
        if weewx.debug > 0:
            syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    # define custom unit settings used by the gateway driver
    define_units()

    # get a DirectGateway object
    direct_gw = DirectGateway(opts, parser, stn_dict)
    # now let the DirectGateway object process the options
    direct_gw.process_options()


if __name__ == '__main__':
    main()