#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
backfill.py

Developmnmetn of a web API based backfill for the Ecowitt gateway driver.

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


class InvalidChecksum(Exception):
    """Exception raised when an API call response contains an invalid
    checksum."""


class GWIOError(Exception):
    """Exception raised when an input/output error with the device is
    encountered."""


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