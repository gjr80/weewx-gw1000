#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gw1000.py

A WeeWX driver for devices using Ecowitt LAN/Wi-Fi Gateway API.

The WeeWX Ecowitt Gateway driver (known historically as the 'WeeWX GW1000
driver') utilises the Ecowitt LAN/Wi-Fi Gateway API thus using a pull
methodology in obtaining data from the gateway device rather than the push
methodology used by drivers that obtain data from the gateway device via
Ecowitt or WeatherUnderground format uploads emitted by the device. The API
approach has the advantage of giving the user more control over when the data
is obtained from the device plus also giving access to a greater range of
metrics.

As of the time of release this driver supports the GW1000, GW1100 and GW2000
gateway devices as well as the WH2650, WH2680 and WN1900 Wi-Fi weather stations.
The Ecowitt Gateway driver can be operated as a traditional WeeWX driver where
it is the source of loop data or it can be operated as a WeeWX service where it
is used to augment loop data produced by another driver.

Copyright (C) 2020-2022 Gary Roderick                   gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see https://www.gnu.org/licenses/.

Version: 0.5.0b6                                    Date: ?? August 2022

Revision History
    ?? June 2022           v0.5.0
        -   renamed as the Ecowitt Gateway driver/service rather than the
            former GW1000 or GW1000/GW1100 driver/service
        -   added support for GW2000
        -   added support for WS90 sensor platform
        -   WH40 and WH51 battery state now decoded as tenths of a Volt rather
            than as binary
        -   redesignated WH35 as WN35 and WH34 as WN34, these changes are
            essentially sensor name change only and do not change any
            decoding/calculations
        -   added mappings for WN34 battery and signal state to the default
            mapping meaning this data will now appear in WeeWX loop packets
        -   refactored GatewayDriver, GatewayService and Gateway class
            initialisations to facilitate running the GatewayDriver and
            GatewayService simultaneously
        -   GatewayService now defaults to using a [GatewayService] stanza but
            if not found will drop back to the legacy [GW1000] stanza
        -   the source of GatewayDriver and GatewayService log output is now
            clearly identified
        -   moved all parsing and decoding of API responses to class Parser
        -   assigned WeeWX fields extraTemp9 to extraTemp17 inclusive to
            group_temperature
        -   implemented --driver-map and --service-map command line options to
            display the actual field map that would be used when running as a
            driver and service respectively
        -   default field map is now only logged at startup when debug>=1
        -   internal non-piezo rainfall related fields renamed with a 't_'
            prefix, eg: 't_rainrate', 't_rainday'
        -   default field map now maps 't_' rainfall fields to the standard
            WeeWX rainfall related fields
        -   added config option log_unknown_fields to log unknown fields found
            in a CMD_GW1000_LIVEDATA or CMD_READ_RAIN API response at the
            info (True) or the default debug (False) level
        -   added support for (likely) rain source selection field (0x7A)
            appearing in CMD_READ_RAIN response
        -   fix issue where day rain and week rain use a different format in
            CMD_READ_RAIN to that in CMD_GW1000_LIVEDATA
        -   fix issue where sensor ID is incorrectly displayed for sensors with
            an ID ending in one or more zeros (issue 48)
        -   device field 't_rainhour' removed from the default field map IAW
            API v1.6.6 change of 0x0F rain hour (ITEM_RAINHOUR) to rain gain
            (ITEM_RAIN_Gain)
        -   --live-data output now indicates the unit group being used
        -   battery state data received from WH40 devices that do not emit
            battery state is now ignored by default and the value None returned
        -   rename a number of calibration/offset related command line options
            to better align with the labels/names now used in the WSView Plus
            app v2.0.32
        -   implement --get-mulch-t-cal command line option to display WN34
            temperature calibration data
    20 March 2022           v0.4.2
        -   fix bug in Station.rediscover()
    14 October 2021         v0.4.1
        -   no change, version increment only
    27 September 2021       v0.4.0
        -   the device model is now identified via the API so many former
            references to 'GW1000' in console and log output should now be
            replaced with the correct device model
        -   when used as a driver the driver hardware_name property now returns
            the device model instead of the driver name (GW1000)
        -   reworked processing of queued data by class GatewayService() to fix
            a bug resulting is intermittent missing GW1000 data
        -   implemented debug_wind reporting
        -   re-factored debug_rain reporting to report both 'WeeWX' and
            'GW1000' rain related fields
        -   battery state data is now set to None for sensors with signal
            level == 0, can be disabled by setting option
            show_all_batt = True under [GW1000] in weewx.conf or by use of
            the --show-all-batt command line option
        -   implemented the --units command line option to control the units
            used when displaying --live-data output, available options are US
            customary (--units=us), Metric (--units=metric) and MetricWx
            (--units=metricwx)
        -   --live-data now formatted and labelled using WeeWX default formats
            and labels
        -   fixed some incorrect command line option descriptions
        -   simplified binary battery state calculation
        -   socket objects are now managed via the 'with' context manager
        -   fixed bug when operated with GW1100 using firmware v2.0.4
        -   implemented limited debug_sensors reporting
        -   implemented a separate broadcast_timeout config option to allow an
            increased socket timeout when broadcasting for gateway devices,
            default value is five seconds
        -   a device is now considered unique if it has a unique MAC address
            (was formerly unique if IP address and port combination were
            unique)
        -   minor reformatting of --discover console output
        -   WH24 battery and signal state fields are now included in the
            default field map
    28 March 2021           v0.3.1
        -   fixed error when broadcast port or socket timeout is specified in
            weewx.conf
        -   fixed bug when decoding firmware version string that gives a
            truncated result
    20 March 2021           v0.3.0
        -   added the --units command line option to allow the output of
            --live-data to be displayed in specified units (US customary or
            Metric)
        -   added support for WH35 sensor
        -   when run directly the driver now distinguishes between no sensor ID
            response and an empty sensor ID response
        -   reworked battery state, signal level and sensor ID processing to
            cater for changes to battery state reporting introduced in GW1000
            API v1.6.0 (GW1000 v1.6.5 firmware)
        -   The GW1000 cumulative daily lightning count field is now included
            in driver loop packets as field 'lightningcount' (the default field
            name). Previously this field was used to derive the WeeWX extended
            schema field 'lightning_strike_count' and was not included in loop
            packets.
        -   fixed incomplete --default-map output
        -   fixes loss of battery state data for some sensors that occurred
            under GW1000 firmware release v1.6.5 and later
    9 January 2021          v0.2.0
        -   added support for WH45 sensor
        -   improved comments in installer/wee_config inserted config
            stanzas/entries
        -   added basic test suite
        -   sensor signal levels added to loop packet
        -   added --get-services command line option to display GW1000
            supported weather services settings
        -   added --get-pm25-offset command line option to display GW1000 PM2.5
            sensor offset settings
        -   added --get-mulch-offset command line option to display GW1000
            multi-channel TH sensor calibration settings
        -   added --get-soil-calibration command line option to display GW1000
            soil moisture sensor calibration settings
        -   added --get-calibration command line option to display GW1000
            sensor calibration settings
        -   renamed --rain-data command line option to --get-rain-data
        -   renamed various 24 hour average particulate concentration fields
        -   added a check for unknown field addresses when processing sensor
            data
    1 September 2020        v0.1.0 (b1-b12)
        - initial release


The Ecowitt LAN/Wi-Fi Gateway API documentation

This driver has been based on the Ecowitt LAN/Wi-Fi Gateway API documentation
v1.6.6. However, the following deviations from the Ecowitt LAN/Wi-Fi Gateway
API documentation v1.6.6 have been made in this driver:

1.  CMD_READ_SSSS documentation states that 'UTC time' is part of the data
returned by the CMD_READ_SSSS API command. The UTC time field is described as
'UTC time' and is an unsigned long. No other details are provided in the API
documentation. Rather than being a Unix epoch timestamp the UTC time data
appears to be a Unix epoch timestamp that is offset from UTC time by the
gateway device timezone. In other words, two gateway devices in different
timezones that have their system time correctly set will return different
values for UTC time. The Ecowitt Gateway driver subtracts the system UTC
offset in seconds from the UTC time returned by the CMD_READ_SSSS command in
order to obtain the correct UTC time.

2.  WH40 battery state data contained in the CMD_READ_SENSOR_ID_NEW response is
documented as a single byte representing 10x the battery voltage. However,
Ecowitt has confirmed that early WH40 hardware does not send any battery state
data. Whilst no battery state data is transmitted by early WH40 hardware, the
API reports a value of 0x10 (decodes to 1.6V) for these devices. Ecowitt has
also confirmed that later revisions of the WH40 do in fact report battery state
data. However, anecdotal evidence shows that the battery state is reported as
100x the battery voltage not 10x as stated in the API documentation.
Consequently, the Ecowitt Gateway driver now discards the bogus 0x10 battery
data (1.6V) reported by early WH40 hardware and WH40 battery voltage is
reported as None for these devices. Battery state data for later WH40 hardware
that does report battery voltage is decoded and passed through to WeeWX.

3.  Yet to released/named API command code 0x59 provides WN34 temperature
calibration data. Calibration data is provided in standardised Ecowitt gateway
device API response packet. Packet uses two bytes for packet size. Header,
command code and checksum are standard values/formats. Data structure is two
bytes per sensor, first byte is sensor address (0x63 to 0x6A) and second byte
is tenths C calibration value. Calibration value may be from +10C to -10C. Data
is included only for connected sensors. This support should be considered
experimental.


Before using this driver:

Before running WeeWX with the Ecowitt Gateway driver you may wish to run the
driver directly from the command line to ensure correct operation/assist in
configuration. Running the driver directly will not interrupt a running WeeWX
instance other than perhaps placing a few extra lines in the WeeWX log. To run
the driver directly from the command line:

1.  Install WeeWX (https://weewx.com/docs/usersguide.htm#installing) and make
sure WeeWX is operating correctly (perhaps with the simulator driver). Whilst
the Ecowitt Gateway driver may be run independently of WeeWX the driver still
requires WeeWX and it's dependencies be installed.

2.  Run the driver directly and display the driver help:

    for a WeeWX setup.py install:

        $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --help

    or for a WeeWX package install use:

        $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --help

    Note: Depending on your system/installation the above command may need to be
          prefixed with sudo.

    Note: The driver must be run under the same Python version as WeeWX uses.
          For WeeWX 3.x this is Python 2. If WeeWX 4.0.0 or later is installed
          this may be Python 2 or Python 3. This means that on some systems
          'python' in the above commands may need to be changed to 'python2'
          or 'python3'.

3.  The --discover command line option is useful for discovering any gateway
devices on the local network. The IP address and port details returned by
--discover can be useful for configuring the driver IP address and port config
options in weewx.conf.

    Note: The recommended approach when using the Ecowitt Gateway driver in a
          live environment is to specify the IP address and port number to be
          used for each gateway device. Discovery has been unreliable at time
          and to date has not worked on a WiFi only connected GW2000 (ethernet
          connected GW200 discover fine).

4.  The --live-data command line option is useful for seeing what data is
available from a particular gateway device. Note the fields available will
depend on the sensors connected to the device. As the field names returned by
--live-data are internal gateway device field names before they have been
mapped to WeeWX fields names, the --live-data output is useful for configuring
the field map to be used by the Ecowitt Gateway driver.

5.  Once you believe the Ecowitt Gateway driver is configured the --test-driver
or --test-service command line options can be used to confirm correct operation
of the Ecowitt Gateway driver as a driver or as a service respectively.


Installing and Configuring the Ecowitt Gateway Driver

Refer to the included readme.txt for basic installation instructions. Refer to
the Ecowitt Gateway driver wiki (https://github.com/gjr80/weewx-gw1000/wiki)
for more in-depth installation and configuration information.
"""

# Standing TODOs:
# TODO. Review against latest
# Outstanding TODOs:
# TODO. Confirm WH26/WH32 sensor ID
# TODO. Confirm WH26/WH32 battery status
# TODO. Confirm WH68 battery status
# TODO. Confirm WS80 battery status
# TODO. Confirm WH24 battery status
# TODO. Confirm WH25 battery status
# TODO. Need to know date-time data format for decode date_time()
# TODO. Review queue dwell times
# TODO. Should service aspects of running the driver directly use [GatewayService] then [GW1000]
# TODO. Need to re-order sensor output for --sensors to better match app
# TODO. windSpeed, windGust, lightning_distance have an excessive number of decimal places in --test-service
# TODO. Revisit debug_wind and debug_rain to see what more debugging output is required

# Python imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import calendar
import configobj
import re
import socket
import struct
import threading
import time
from operator import itemgetter

# Python 2/3 compatibility shims
import six
from six.moves import StringIO

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

DRIVER_NAME = 'GW1000'
DRIVER_VERSION = '0.5.0b6'

# various defaults used throughout
# default port used by device
default_port = 45000
# default network broadcast address - the address that network broadcasts are
# sent to
default_broadcast_address = '255.255.255.255'
# default network broadcast port - the port that network broadcasts are sent to
default_broadcast_port = 46000
# default socket timeout
default_socket_timeout = 2
# default broadcast timeout
default_broadcast_timeout = 5
# default retry/wait time
default_retry_wait = 10
# default max tries when polling the API
default_max_tries = 3
# When run as a service the default age in seconds after which API data is
# considered stale and will not be used to augment loop packets
default_max_age = 60
# default device poll interval
default_poll_interval = 20
# default period between lost contact log entries during an extended period of
# lost contact when run as a Service
default_lost_contact_log_period = 21600
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
default_groups = {'extraTemp9': 'group_temperature',
                  'extraTemp10': 'group_temperature',
                  'extraTemp11': 'group_temperature',
                  'extraTemp12': 'group_temperature',
                  'extraTemp13': 'group_temperature',
                  'extraTemp14': 'group_temperature',
                  'extraTemp15': 'group_temperature',
                  'extraTemp16': 'group_temperature',
                  'extraTemp17': 'group_temperature',
                  'p_rain': 'group_rain',
                  'p_stormRain': 'group_rain',
                  'p_dayRain': 'group_rain',
                  'p_weekRain': 'group_rain',
                  'p_monthRain': 'group_rain',
                  'p_yearRain': 'group_rain'}

# merge the default unit groups into weewx.units.obs_group_dict, but so we
# don't undo any user customisation elsewhere only merge those fields that do
# not already exits in weewx.units.obs_group_dict
for obs, group in six.iteritems(default_groups):
    if obs not in weewx.units.obs_group_dict.keys():
        weewx.units.obs_group_dict[obs] = group


# ============================================================================
#                         Gateway API error classes
# ============================================================================

class UnknownApiCommand(Exception):
    """Exception raised when an unknown API command was selected or an
    otherwise valid API response has an unexpected command code."""


class InvalidChecksum(Exception):
    """Exception raised when an API call response contains an invalid
    checksum."""


class GWIOError(Exception):
    """Exception raised when an input/output error with the device is
    encountered."""


# ============================================================================
#                               class Gateway
# ============================================================================

class Gateway(object):
    """Base class for interacting with an Ecowitt Gateway device.

    There are a number of common properties and methods (eg IP address, field
    map, rain calculation etc) when dealing with a gateway device either as a
    driver or service. This class captures those common features.
    """

    # Default field map to map device sensor data to WeeWX fields. Field names
    # in the WeeWX wview_extended schema are used where there is a direct
    # correlation to the WeeWX wview_extended schema or
    # weewx.units.obs_group_dict. If there is a related but different field in
    # the wview_extended schema then a WeeWX field name with a similar format
    # is used. Otherwise fields are passed through as is.
    # Field map format is:
    #   WeeWX field name: Gateway device field name
    default_field_map = {
        'inTemp': 'intemp',
        'outTemp': 'outtemp',
        'dewpoint': 'dewpoint',
        'windchill': 'windchill',
        'heatindex': 'heatindex',
        'inHumidity': 'inhumid',
        'outHumidity': 'outhumid',
        'pressure': 'absbarometer',
        'relbarometer': 'relbarometer',
        'luminosity': 'light',
        # we can't pass through 'uv'; it's too much like 'UV', so use the
        # Ecowitt term 'uvradiation'
        'uvradiation': 'uv',
        'UV': 'uvi',
        'dateTime': 'datetime',
        'extraTemp1': 'temp1',
        'extraTemp2': 'temp2',
        'extraTemp3': 'temp3',
        'extraTemp4': 'temp4',
        'extraTemp5': 'temp5',
        'extraTemp6': 'temp6',
        'extraTemp7': 'temp7',
        'extraTemp8': 'temp8',
        'extraTemp9': 'temp9',
        'extraTemp10': 'temp10',
        'extraTemp11': 'temp11',
        'extraTemp12': 'temp12',
        'extraTemp13': 'temp13',
        'extraTemp14': 'temp14',
        'extraTemp15': 'temp15',
        'extraTemp16': 'temp16',
        'extraTemp17': 'temp17',
        'extraHumid1': 'humid1',
        'extraHumid2': 'humid2',
        'extraHumid3': 'humid3',
        'extraHumid4': 'humid4',
        'extraHumid5': 'humid5',
        'extraHumid6': 'humid6',
        'extraHumid7': 'humid7',
        'extraHumid8': 'humid8',
        'extraHumid17': 'humid17',
        'leafWet1': 'leafwet1',
        'leafWet2': 'leafwet2',
        'leafWet3': 'leafwet3',
        'leafWet4': 'leafwet4',
        'leafWet5': 'leafwet5',
        'leafWet6': 'leafwet6',
        'leafWet7': 'leafwet7',
        'leafWet8': 'leafwet8',
        'pm2_5': 'pm251',
        'pm2_52': 'pm252',
        'pm2_53': 'pm253',
        'pm2_54': 'pm254',
        'pm2_55': 'pm255',
        'pm10': 'pm10',
        'co2': 'co2',
        'soilTemp1': 'soiltemp1',
        'soilMoist1': 'soilmoist1',
        'soilTemp2': 'soiltemp2',
        'soilMoist2': 'soilmoist2',
        'soilTemp3': 'soiltemp3',
        'soilMoist3': 'soilmoist3',
        'soilTemp4': 'soiltemp4',
        'soilMoist4': 'soilmoist4',
        'soilTemp5': 'soiltemp5',
        'soilMoist5': 'soilmoist5',
        'soilTemp6': 'soiltemp6',
        'soilMoist6': 'soilmoist6',
        'soilTemp7': 'soiltemp7',
        'soilMoist7': 'soilmoist7',
        'soilTemp8': 'soiltemp8',
        'soilMoist8': 'soilmoist8',
        'soilTemp9': 'soiltemp9',
        'soilMoist9': 'soilmoist9',
        'soilTemp10': 'soiltemp10',
        'soilMoist10': 'soilmoist10',
        'soilTemp11': 'soiltemp11',
        'soilMoist11': 'soilmoist11',
        'soilTemp12': 'soiltemp12',
        'soilMoist12': 'soilmoist12',
        'soilTemp13': 'soiltemp13',
        'soilMoist13': 'soilmoist13',
        'soilTemp14': 'soiltemp14',
        'soilMoist14': 'soilmoist14',
        'soilTemp15': 'soiltemp15',
        'soilMoist15': 'soilmoist15',
        'soilTemp16': 'soiltemp16',
        'soilMoist16': 'soilmoist16',
        'pm2_51_24h_avg': 'pm251_24h_avg',
        'pm2_52_24h_avg': 'pm252_24h_avg',
        'pm2_53_24h_avg': 'pm253_24h_avg',
        'pm2_54_24h_avg': 'pm254_24h_avg',
        'pm2_55_24h_avg': 'pm255_24h_avg',
        'pm10_24h_avg': 'pm10_24h_avg',
        'co2_24h_avg': 'co2_24h_avg',
        'leak1': 'leak1',
        'leak2': 'leak2',
        'leak3': 'leak3',
        'leak4': 'leak4',
        'lightning_distance': 'lightningdist',
        'lightning_last_det_time': 'lightningdettime',
        # 'lightningcount' is the device lightning count field obtained via the
        # API. It is safe for the user to change this mapping as
        # 'lightning_strike_count' is derived before the user mapping is
        # applied.
        'lightningcount': 'lightningcount',
        # 'lightning_strike_count' is the WeeWX extended schema per period
        # lightning count field that is derived from the device cumulative
        # 'lightningcount' field
        'lightning_strike_count': 'lightning_strike_count'
    }
    # Rain related fields default field map, merged into default_field_map to
    # give the overall default field map. Kept separate to make it easier to
    # iterate over only rain related fields.
    rain_field_map = {
        'rain': 't_rain',
        'stormRain': 't_rainevent',
        'rainRate': 't_rainrate',
        'dayRain': 't_rainday',
        'weekRain': 't_rainweek',
        'monthRain': 't_rainmonth',
        'yearRain': 't_rainyear',
        'totalRain': 't_raintotals',
        'p_rain': 'p_rain',
        'p_stormRain': 'p_rainevent',
        'p_rainRate': 'p_rainrate',
        'p_dayRain': 'p_rainday',
        'p_weekRain': 'p_rainweek',
        'p_monthRain': 'p_rainmonth',
        'p_yearRain': 'p_rainyear'
    }
    # wind related fields default field map, merged into default_field_map to
    # give the overall default field map. Kept separate to make it easier to
    # iterate over only wind related fields.
    wind_field_map = {
        'windDir': 'winddir',
        'windSpeed': 'windspeed',
        'windGust': 'gustspeed',
        'daymaxwind': 'daymaxwind',
    }
    # battery state default field map, merged into default_field_map to give
    # the overall default field map
    battery_field_map = {
        'wh40_batt': 'wh40_batt',
        'wh26_batt': 'wh26_batt',
        'wh25_batt': 'wh25_batt',
        'wh24_batt': 'wh24_batt',
        'wh65_batt': 'wh65_batt',
        'wh32_batt': 'wh32_batt',
        'wh31_ch1_batt': 'wh31_ch1_batt',
        'wh31_ch2_batt': 'wh31_ch2_batt',
        'wh31_ch3_batt': 'wh31_ch3_batt',
        'wh31_ch4_batt': 'wh31_ch4_batt',
        'wh31_ch5_batt': 'wh31_ch5_batt',
        'wh31_ch6_batt': 'wh31_ch6_batt',
        'wh31_ch7_batt': 'wh31_ch7_batt',
        'wh31_ch8_batt': 'wh31_ch8_batt',
        'wn34_ch1_batt': 'wn34_ch1_batt',
        'wn34_ch2_batt': 'wn34_ch2_batt',
        'wn34_ch3_batt': 'wn34_ch3_batt',
        'wn34_ch4_batt': 'wn34_ch4_batt',
        'wn34_ch5_batt': 'wn34_ch5_batt',
        'wn34_ch6_batt': 'wn34_ch6_batt',
        'wn34_ch7_batt': 'wn34_ch7_batt',
        'wn34_ch8_batt': 'wn34_ch8_batt',
        'wn35_ch1_batt': 'wn35_ch1_batt',
        'wn35_ch2_batt': 'wn35_ch2_batt',
        'wn35_ch3_batt': 'wn35_ch3_batt',
        'wn35_ch4_batt': 'wn35_ch4_batt',
        'wn35_ch5_batt': 'wn35_ch5_batt',
        'wn35_ch6_batt': 'wn35_ch6_batt',
        'wn35_ch7_batt': 'wn35_ch7_batt',
        'wn35_ch8_batt': 'wn35_ch8_batt',
        'wh41_ch1_batt': 'wh41_ch1_batt',
        'wh41_ch2_batt': 'wh41_ch2_batt',
        'wh41_ch3_batt': 'wh41_ch3_batt',
        'wh41_ch4_batt': 'wh41_ch4_batt',
        'wh45_batt': 'wh45_batt',
        'wh51_ch1_batt': 'wh51_ch1_batt',
        'wh51_ch2_batt': 'wh51_ch2_batt',
        'wh51_ch3_batt': 'wh51_ch3_batt',
        'wh51_ch4_batt': 'wh51_ch4_batt',
        'wh51_ch5_batt': 'wh51_ch5_batt',
        'wh51_ch6_batt': 'wh51_ch6_batt',
        'wh51_ch7_batt': 'wh51_ch7_batt',
        'wh51_ch8_batt': 'wh51_ch8_batt',
        'wh51_ch9_batt': 'wh51_ch9_batt',
        'wh51_ch10_batt': 'wh51_ch10_batt',
        'wh51_ch11_batt': 'wh51_ch11_batt',
        'wh51_ch12_batt': 'wh51_ch12_batt',
        'wh51_ch13_batt': 'wh51_ch13_batt',
        'wh51_ch14_batt': 'wh51_ch14_batt',
        'wh51_ch15_batt': 'wh51_ch15_batt',
        'wh51_ch16_batt': 'wh51_ch16_batt',
        'wh55_ch1_batt': 'wh55_ch1_batt',
        'wh55_ch2_batt': 'wh55_ch2_batt',
        'wh55_ch3_batt': 'wh55_ch3_batt',
        'wh55_ch4_batt': 'wh55_ch4_batt',
        'wh57_batt': 'wh57_batt',
        'wh68_batt': 'wh68_batt',
        'ws80_batt': 'ws80_batt',
        'ws90_batt': 'ws90_batt'
    }
    # sensor signal level default field map, merged into default_field_map to
    # give the overall default field map
    sensor_signal_field_map = {
        'wh40_sig': 'wh40_sig',
        'wh26_sig': 'wh26_sig',
        'wh25_sig': 'wh25_sig',
        'wh24_sig': 'wh24_sig',
        'wh65_sig': 'wh65_sig',
        'wh32_sig': 'wh32_sig',
        'wh31_ch1_sig': 'wh31_ch1_sig',
        'wh31_ch2_sig': 'wh31_ch2_sig',
        'wh31_ch3_sig': 'wh31_ch3_sig',
        'wh31_ch4_sig': 'wh31_ch4_sig',
        'wh31_ch5_sig': 'wh31_ch5_sig',
        'wh31_ch6_sig': 'wh31_ch6_sig',
        'wh31_ch7_sig': 'wh31_ch7_sig',
        'wh31_ch8_sig': 'wh31_ch8_sig',
        'wn34_ch1_sig': 'wn34_ch1_sig',
        'wn34_ch2_sig': 'wn34_ch2_sig',
        'wn34_ch3_sig': 'wn34_ch3_sig',
        'wn34_ch4_sig': 'wn34_ch4_sig',
        'wn34_ch5_sig': 'wn34_ch5_sig',
        'wn34_ch6_sig': 'wn34_ch6_sig',
        'wn34_ch7_sig': 'wn34_ch7_sig',
        'wn34_ch8_sig': 'wn34_ch8_sig',
        'wn35_ch1_sig': 'wn35_ch1_sig',
        'wn35_ch2_sig': 'wn35_ch2_sig',
        'wn35_ch3_sig': 'wn35_ch3_sig',
        'wn35_ch4_sig': 'wn35_ch4_sig',
        'wn35_ch5_sig': 'wn35_ch5_sig',
        'wn35_ch6_sig': 'wn35_ch6_sig',
        'wn35_ch7_sig': 'wn35_ch7_sig',
        'wn35_ch8_sig': 'wn35_ch8_sig',
        'wh41_ch1_sig': 'wh41_ch1_sig',
        'wh41_ch2_sig': 'wh41_ch2_sig',
        'wh41_ch3_sig': 'wh41_ch3_sig',
        'wh41_ch4_sig': 'wh41_ch4_sig',
        'wh45_sig': 'wh45_sig',
        'wh51_ch1_sig': 'wh51_ch1_sig',
        'wh51_ch2_sig': 'wh51_ch2_sig',
        'wh51_ch3_sig': 'wh51_ch3_sig',
        'wh51_ch4_sig': 'wh51_ch4_sig',
        'wh51_ch5_sig': 'wh51_ch5_sig',
        'wh51_ch6_sig': 'wh51_ch6_sig',
        'wh51_ch7_sig': 'wh51_ch7_sig',
        'wh51_ch8_sig': 'wh51_ch8_sig',
        'wh51_ch9_sig': 'wh51_ch9_sig',
        'wh51_ch10_sig': 'wh51_ch10_sig',
        'wh51_ch11_sig': 'wh51_ch11_sig',
        'wh51_ch12_sig': 'wh51_ch12_sig',
        'wh51_ch13_sig': 'wh51_ch13_sig',
        'wh51_ch14_sig': 'wh51_ch14_sig',
        'wh51_ch15_sig': 'wh51_ch15_sig',
        'wh51_ch16_sig': 'wh51_ch16_sig',
        'wh55_ch1_sig': 'wh55_ch1_sig',
        'wh55_ch2_sig': 'wh55_ch2_sig',
        'wh55_ch3_sig': 'wh55_ch3_sig',
        'wh55_ch4_sig': 'wh55_ch4_sig',
        'wh57_sig': 'wh57_sig',
        'wh68_sig': 'wh68_sig',
        'ws80_sig': 'ws80_sig',
        'ws90_sig': 'ws90_sig'
    }

    def __init__(self, **gw_config):
        """Initialise a Gateway object."""

        # construct the field map, first obtain the field map from our config
        field_map = gw_config.get('field_map')
        # obtain any field map extensions from our config
        extensions = gw_config.get('field_map_extensions', {})
        # if we have no field map then use the default
        if field_map is None:
            # obtain the default field map
            field_map = dict(Gateway.default_field_map)
            # now add in the rain field map
            field_map.update(Gateway.rain_field_map)
            # now add in the wind field map
            field_map.update(Gateway.wind_field_map)
            # now add in the battery state field map
            field_map.update(Gateway.battery_field_map)
            # now add in the sensor signal field map
            field_map.update(Gateway.sensor_signal_field_map)
        # If a user wishes to map a device field differently to that in the
        # default map they can include an entry in field_map_extensions, but if
        # we just update the field map dict with the field map extensions that
        # will leave two entries for that device field in the field map; the
        # original field map entry as well as the entry from the extended map.
        # So if we have field_map_extensions we need to first go through the
        # field map and delete any entries that map device fields that are
        # included in the field_map_extensions.
        # we only need process the field_map_extensions if we have any
        if len(extensions) > 0:
            # first make a copy of the field map because we will be iterating
            # over it and changing it
            field_map_copy = dict(field_map)
            # iterate over each key, value pair in the copy of the field map
            for k, v in six.iteritems(field_map_copy):
                # if the 'value' (ie the device field) is in the field map
                # extensions we will be mapping that device field elsewhere so
                # pop that field map entry out of the field map so we don't end
                # up with multiple mappings for a device field
                if v in extensions.values():
                    # pop the field map entry
                    _dummy = field_map.pop(k)
            # now we can update the field map with the extensions
            field_map.update(extensions)
        # we now have our final field map
        self.field_map = field_map
        # network broadcast address and port
        self.broadcast_address = str.encode(gw_config.get('broadcast_address',
                                                          default_broadcast_address))
        self.broadcast_port = weeutil.weeutil.to_int(gw_config.get('broadcast_port',
                                                                   default_broadcast_port))
        self.socket_timeout = weeutil.weeutil.to_int(gw_config.get('socket_timeout',
                                                                   default_socket_timeout))
        self.broadcast_timeout = weeutil.weeutil.to_int(gw_config.get('broadcast_timeout',
                                                                      default_broadcast_timeout))
        # obtain the device IP address
        _ip_address = gw_config.get('ip_address')
        # if the user has specified some variation of 'auto' then we are to
        # automatically detect the device IP address, to do that we set the
        # ip_address property to None
        if _ip_address is not None and _ip_address.lower() == 'auto':
            # we need to autodetect IP address so set to None
            _ip_address = None
        # set the IP address property
        self.ip_address = _ip_address
        # obtain the device port from the config dict
        # for port number we have a default value we can use, so if port is not
        # specified use the default
        _port = gw_config.get('port', default_port)
        # if a port number was specified it needs to be an integer not a string
        # so try to do the conversion
        try:
            _port = int(_port)
        except TypeError:
            # most likely port somehow ended up being None, in any case force
            # auto-detection by setting port to None
            _port = None
        except ValueError:
            # We couldn't convert the port number to an integer. Maybe it was
            # because it was 'auto' (or some variation) or perhaps it was
            # invalid. Either way we need to set port to None to force
            # auto-detection. If there was an invalid port specified then log
            # it.
            if _port.lower() != 'auto':
                loginf("Invalid device port '%s' specified, "
                       "port will be auto detected" % (_port,))
            _port = None
        # set the port property
        self.port = _port
        # how many times to poll the API before giving up, default is
        # default_max_tries
        self.max_tries = int(gw_config.get('max_tries', default_max_tries))
        # wait time in seconds between retries, default is default_retry_wait
        # seconds
        self.retry_wait = int(gw_config.get('retry_wait',
                                            default_retry_wait))
        # how often (in seconds) we should poll the API, use a default
        self.poll_interval = int(gw_config.get('poll_interval',
                                               default_poll_interval))
        # Is a WH32 in use. WH32 TH sensor can override/provide outdoor TH data
        # to the gateway device. In terms of TH data the process is transparent
        # and we do not need to know if a WH32 or other sensor is providing
        # outdoor TH data but in terms of battery state we need to know so the
        # battery state data can be reported against the correct sensor.
        use_wh32 = weeutil.weeutil.tobool(gw_config.get('wh32', True))
        # do we ignore battery state data from legacy WH40 sensors that do not
        # provide valid battery state data
        ignore_wh40_batt = weeutil.weeutil.tobool(gw_config.get('ignore_legacy_wh40_battery',
                                                                True))
        # do we show all battery state data including nonsense data or do we
        # filter those sensors with signal state == 0
        self.show_battery = weeutil.weeutil.tobool(gw_config.get('show_all_batt',
                                                                 False))
        # whether to log unknown API fields, unknown fields are logged at the
        # debug level, this will log them at the info level
        log_unknown_fields = weeutil.weeutil.tobool(gw_config.get('log_unknown_fields',
                                                                  False))
        # get any specific debug settings
        # rain
        self.debug_rain = weeutil.weeutil.tobool(gw_config.get('debug_rain',
                                                               False))
        # wind
        self.debug_wind = weeutil.weeutil.tobool(gw_config.get('debug_wind',
                                                               False))
        # loop data
        self.debug_loop = weeutil.weeutil.tobool(gw_config.get('debug_loop',
                                                               False))
        # sensors
        self.debug_sensors = weeutil.weeutil.tobool(gw_config.get('debug_sensors',
                                                                  False))
        # create an GatewayCollector object to interact with the gateway device
        # API
        self.collector = GatewayCollector(ip_address=self.ip_address,
                                          port=self.port,
                                          broadcast_address=self.broadcast_address,
                                          broadcast_port=self.broadcast_port,
                                          socket_timeout=self.socket_timeout,
                                          broadcast_timeout=self.broadcast_timeout,
                                          poll_interval=self.poll_interval,
                                          max_tries=self.max_tries,
                                          retry_wait=self.retry_wait,
                                          use_wh32=use_wh32,
                                          ignore_wh40_batt=ignore_wh40_batt,
                                          show_battery=self.show_battery,
                                          log_unknown_fields=log_unknown_fields,
                                          debug_rain=self.debug_rain,
                                          debug_wind=self.debug_wind,
                                          debug_sensors=self.debug_sensors)
        # initialise last lightning count and last rain properties
        self.last_lightning = None
        self.last_rain = None
        self.piezo_last_rain = None
        self.rain_mapping_confirmed = False
        self.rain_total_field = None
        self.piezo_rain_mapping_confirmed = False
        self.piezo_rain_total_field = None
        # Finally, log any config that is not being pushed any further down.
        # Log specific debug output but only if set ie. True
        debug_list = []
        if self.debug_rain:
            debug_list.append("debug_rain is %s" % (self.debug_rain,))
        if self.debug_wind:
            debug_list.append("debug_wind is %s" % (self.debug_wind,))
        if self.debug_loop:
            debug_list.append("debug_loop is %s" % (self.debug_loop,))
        if len(debug_list) > 0:
            loginf(" ".join(debug_list))

    @property
    def model(self):
        """What model device am I using."""

        return self.collector.station.model

    def map_data(self, data):
        """Map parsed device data to a WeeWX loop packet.

        Maps parsed device data to WeeWX loop packet fields using the field
        map. Result includes usUnits field set to METRICWX.

        data: Dict of parsed device API data
        """

        # parsed device API data uses the METRICWX unit system
        _result = {'usUnits': weewx.METRICWX}
        # iterate over each of the key, value pairs in the field map
        for weewx_field, data_field in six.iteritems(self.field_map):
            # if the field to be mapped exists in the data obtain it's
            # value and map it to the packet
            if data_field in data:
                _result[weewx_field] = data.get(data_field)
        return _result

    @staticmethod
    def log_rain_data(data, preamble=None):
        """Log rain related data from the collector.

        General routine to obtain and log rain related data from a packet. The
        packet could be unmapped device data using 'device' field names, or it
        may be mapped data or a WeeWX loop packet that uses 'WeeWX' field
        names. So we iterate over the keys ('WeeWX' field names) and values
        ('device' field names) of the rain field map.
        """

        msg_list = []
        # iterate over our rain_field_map keys (the 'WeeWX' fields) and values
        # (the 'device' fields) we are interested in
        for weewx_field, gw_field in six.iteritems(Gateway.rain_field_map):
            # do we have a 'WeeWX' field of interest
            if weewx_field in data:
                # we do so add some formatted output to our list
                msg_list.append("%s=%s" % (weewx_field,
                                           data[weewx_field]))
            # do we have a 'device' field of interest
            if gw_field in data and weewx_field != gw_field:
                # we do so add some formatted output to our list
                msg_list.append("%s=%s" % (gw_field,
                                           data[gw_field]))
        # pre-format the log line label
        label = "%s: " % preamble if preamble is not None else ""
        # if we have some entries log them otherwise provide suitable text
        if len(msg_list) > 0:
            loginf("%s%s" % (label, " ".join(msg_list)))
        else:
            loginf("%sno rain data found" % (label,))

    @staticmethod
    def log_wind_data(data, preamble=None):
        """Log wind related data from the collector.

        General routine to obtain and log wind related data from a packet. The
        packet could be unmapped device data using 'device' field names, or it
        may be mapped data or a WeeWX loop packet that uses 'WeeWX' field
        names. So we iterate over the keys ('WeeWX' field names) and values
        ('device' field names) of the rain field map.
        """

        msg_list = []
        # iterate over our wind_field_map keys (the 'WeeWX' fields) and values
        # (the 'device' fields) we are interested in
        for weewx_field, gw_field in six.iteritems(Gateway.wind_field_map):
            # do we have a 'WeeWX' field of interest
            if weewx_field in data:
                # we do so add some formatted output to our list
                msg_list.append("%s=%s" % (weewx_field,
                                           data[weewx_field]))
            # do we have a 'device' field of interest
            if gw_field in data:
                # we do so add some formatted output to our list
                msg_list.append("%s=%s" % (gw_field,
                                           data[gw_field]))
        # pre-format the log line label
        label = "%s: " % preamble if preamble is not None else ""
        # if we have some entries log them otherwise provide suitable text
        if len(msg_list) > 0:
            loginf("%s%s" % (label, " ".join(msg_list)))
        else:
            loginf("%sno wind data found" % (label,))

    def get_cumulative_rain_field(self, data):
        """Determine the cumulative rain field used to derive field 'rain'.

        Ecowitt gateway devices emit various rain totals but WeeWX needs a per
        period value for field rain. Try the 'big' (four byte) counters
        starting at the longest period and working our way down. This should
        only need be done once.

        This is further complicated by the introduction of 'piezo' rain with
        the WS90. Do a second round of checks on the piezo rain equivalents and
        create piezo equivalent properties.

        data: dic of parsed device API data
        """

        # Do we have a confirmed field to use for calculating rain? If we do we
        # can skip this otherwise we need to look for one.
        if not self.rain_mapping_confirmed:
            # We have no field for calculating rain so look for one, if device
            # field 't_raintotals' is present used that as our first choice.
            # Otherwise, work down the list in order of descending period.
            if 't_raintotals' in data:
                self.rain_total_field = 't_raintotals'
                self.rain_mapping_confirmed = True
            # t_raintotals is not present so now try rainyear
            elif 't_rainyear' in data:
                self.rain_total_field = 't_rainyear'
                self.rain_mapping_confirmed = True
            # t_rainyear is not present so now try rainmonth
            elif 't_rainmonth' in data:
                self.rain_total_field = 't_rainmonth'
                self.rain_mapping_confirmed = True
            # do nothing, we can try again next packet
            else:
                self.rain_total_field = None
            # if we found a field log what we are using
            if self.rain_mapping_confirmed:
                loginf("Using '%s' for rain total" % self.rain_total_field)
            elif self.debug_rain:
                # if debug_rain is set log that we had nothing
                loginf("No suitable field found for rain")

        # now do the same for piezo rain

        # Do we have a confirmed field to use for calculating piezo rain? If we
        # do we can skip this otherwise we need to look for one.
        if not self.piezo_rain_mapping_confirmed:
            # We have no field for calculating piezo rain so look for one, if
            # device field 'p_rainyear' is present used that as our first
            # choice. Otherwise, work down the list in order of descending
            # period.
            if 'p_rainyear' in data:
                self.piezo_rain_total_field = 'p_rainyear'
                self.piezo_rain_mapping_confirmed = True
            # rainyear is not present so now try rainmonth
            elif 'p_rainmonth' in data:
                self.piezo_rain_total_field = 'p_rainmonth'
                self.piezo_rain_mapping_confirmed = True
            # do nothing, we can try again next packet
            else:
                self.piezo_rain_total_field = None
            # if we found a field log what we are using
            if self.piezo_rain_mapping_confirmed:
                loginf("Using '%s' for piezo rain total" % self.piezo_rain_total_field)
            elif self.debug_rain:
                # if debug_rain is set log that we had nothing
                loginf("No suitable field found for piezo rain")

    def calculate_rain(self, data):
        """Calculate total rainfall for a period.

        'rain' is calculated as the change in a user designated cumulative rain
        field between successive periods. 'rain' is only calculated if the
        field to be used has been selected and the designated field exists.

        This is further complicated by the introduction of 'piezo' rain with
        the WS90. Do a second round of calculations on the piezo rain
        equivalents and calculate the piezo rain field.

        data: dict of parsed device API data
        """

        # have we decided on a field to use and is the field present
        if self.rain_mapping_confirmed and self.rain_total_field in data:
            # yes on both counts, so get the new total
            new_total = data[self.rain_total_field]
            # now calculate field rain as the difference between the new and
            # old totals
            data['t_rain'] = self.delta_rain(new_total, self.last_rain)
            # if debug_rain is set log some pertinent values
            if self.debug_rain:
                loginf("calculate_rain: last_rain=%s new_total=%s calculated rain=%s" % (self.last_rain,
                                                                                         new_total,
                                                                                         data['t_rain']))
            # save the new total as the old total for next time
            self.last_rain = new_total

        # now do the same for piezo rain

        # have we decided on a field to use for piezo rain and is the field
        # present
        if self.piezo_rain_mapping_confirmed and self.piezo_rain_total_field in data:
            # yes on both counts, so get the new total
            piezo_new_total = data[self.piezo_rain_total_field]
            # now calculate field p_rain as the difference between the new and
            # old totals
            data['p_rain'] = self.delta_rain(piezo_new_total,
                                             self.piezo_last_rain,
                                             descriptor='piezo rain')
            # if debug_rain is set log some pertinent values
            if self.debug_rain:
                loginf("calculate_rain: piezo_last_rain=%s piezo_new_total=%s "
                       "calculated p_rain=%s" % (self.piezo_last_rain,
                                                 piezo_new_total,
                                                 data['p_rain']))
            # save the new total as the old total for next time
            self.piezo_last_rain = piezo_new_total

    def calculate_lightning_count(self, data):
        """Calculate total lightning strike count for a period.

        'lightning_strike_count' is calculated as the change in field
        'lightningcount' between successive periods. 'lightning_strike_count'
        is only calculated if 'lightningcount' exists.

        data: dict of parsed device API data
        """

        # is the lightningcount field present
        if 'lightningcount' in data:
            # yes, so get the new total
            new_total = data['lightningcount']
            # now calculate field lightning_strike_count as the difference
            # between the new and old totals
            data['lightning_strike_count'] = self.delta_lightning(new_total,
                                                                  self.last_lightning)
            # save the new total as the old total for next time
            self.last_lightning = new_total

    @staticmethod
    def delta_rain(rain, last_rain, descriptor='rain'):
        """Calculate rainfall from successive cumulative values.

        Rainfall is calculated as the difference between two cumulative values.
        If either value is None the value None is returned. If the previous
        value is greater than the latest value a counter wrap around is assumed
        and the latest value is returned.

        rain:       current cumulative rain value
        last_rain:  last cumulative rain value
        descriptor: string to indicate what rain data we are working with
        """

        # do we have a last rain value
        if last_rain is None:
            # no, log it and return None
            loginf("skipping %s measurement of %s: no last rain" % (descriptor, rain))
            return None
        # do we have a non-None current rain value
        if rain is None:
            # no, log it and return None
            loginf("skipping %s measurement: no current rain data" % descriptor)
            return None
        # is the last rain value greater than the current rain value
        if rain < last_rain:
            # it is, assume a counter wrap around/reset, log it and return the
            # latest rain value
            loginf("%s counter wraparound detected: new=%s last=%s" % (descriptor, rain, last_rain))
            return rain
        # return the difference between the counts
        return rain - last_rain

    @staticmethod
    def delta_lightning(count, last_count):
        """Calculate lightning strike count from successive cumulative values.

        Lightning strike count is calculated as the difference between two
        cumulative values. If either value is None the value None is returned.
        If the previous value is greater than the latest value a counter wrap
        around is assumed and the latest value is returned.

        count:      current cumulative lightning count
        last_count: last cumulative lightning count
        """

        # do we have a last count
        if last_count is None:
            # no, log it and return None
            loginf("Skipping lightning count of %s: no last count" % count)
            return None
        # do we have a non-None current count
        if count is None:
            # no, log it and return None
            loginf("Skipping lightning count: no current count")
            return None
        # is the last count greater than the current count
        if count < last_count:
            # it is, assume a counter wrap around/reset, log it and return the
            # latest count
            loginf("Lightning counter wraparound detected: new=%s last=%s" % (count, last_count))
            return count
        # otherwise return the difference between the counts
        return count - last_count


# ============================================================================
#                            GW1000 Service class
# ============================================================================

class GatewayService(weewx.engine.StdService, Gateway):
    """Gateway device service class.

    A WeeWX service to augment loop packets with observational data obtained
    from a gateway device via the Ecowitt LAN/Wi-Fi Gateway API. The
    GatewayService is useful when data is required from more than one source;
    for example, WeeWX is using another driver and the GatewayDriver cannot be
    used.

    Data is obtained via the Ecowitt LAN/Wi-Fi Gateway API. The data is parsed
    and mapped to WeeWX fields and if the device data is not stale the loop
    packet is augmented with the mapped device data.

    Class GatewayCollector collects and parses data from the API. The
    GatewayCollector runs in a separate thread, so it does not block the main
    WeeWX processing loop. The GatewayCollector is turn uses child classes
    Station and Parser to interact directly with the API and parse the API
    responses respectively.
    """

    def __init__(self, engine, config_dict):
        """Initialise a GatewayService object."""

        # extract the gateway service config dictionary
        # first look for [Gw1000Service]
        if 'GW1000Service' in config_dict:
            # we have a [GW1000Service] config stanza so use it
            gw_config_dict = config_dict['GW1000Service']
        else:
            # we don't have a [GW1000Service] stana so use [GW1000] if it
            # exists otherwise use an empty config
            gw_config_dict = config_dict.get('GW1000', {})
        # initialize my superclasses
        super(GatewayService, self).__init__(engine, config_dict)
        super(weewx.engine.StdService, self).__init__(**gw_config_dict)

        # age (in seconds) before API data is considered too old to use, use a
        # default
        self.max_age = int(gw_config_dict.get('max_age', default_max_age))
        # minimum period in seconds between 'lost contact' log entries during
        # an extended lost contact period
        self.lost_contact_log_period = int(gw_config_dict.get('lost_contact_log_period',
                                                              default_lost_contact_log_period))
        # set failure logging on
        self.log_failures = True
        # reset the lost contact timestamp
        self.lost_con_ts = None
        # create a placeholder for our most recent, non-stale queued device
        # sensor data packet
        self.cached_sensor_data = None
        # log our version number
        loginf('GatewayService: version is %s' % DRIVER_VERSION)
        # log the relevant settings/parameters we are using
        if self.ip_address is None and self.port is None:
            loginf('GatewayService: %s IP address and port not specified, '
                   'attempting to discover %s...' % (self.collector.station.model,
                                                     self.collector.station.model))
        elif self.ip_address is None:
            loginf('GatewayService: %s IP address not specified, attempting '
                   'to discover %s...' % (self.collector.station.model,
                                          self.collector.station.model))
        elif self.port is None:
            loginf('Gw1000Service: %s port not specified, attempting '
                   'to discover %s...' % (self.collector.station.model,
                                          self.collector.station.model))
        loginf('GatewayService: %s address is %s:%d' % (self.collector.station.model,
                                                        self.collector.station.ip_address.decode(),
                                                        self.collector.station.port))
        loginf('GatewayService: poll interval is %d seconds' % self.poll_interval)
        logdbg('GatewayService: max tries is %d, retry wait time is %d seconds' % (self.max_tries,
                                                                                   self.retry_wait))
        logdbg('GatewayService: broadcast address %s:%d, '
               'broadcast timeout is %d seconds' % (self.broadcast_address,
                                                    self.broadcast_port,
                                                    self.broadcast_timeout))
        logdbg('GatewayService: socket timeout is %d seconds' % self.socket_timeout)
        loginf("GatewayService: max age of API data to be used is %d seconds" % self.max_age)
        # The field map. Field map dict output will be in unsorted key order.
        # It is easier to read if sorted alphanumerically but we have keys such
        # as xxxxx16 that do not sort well. Use a custom natural sort of the
        # keys in a manually produced formatted dict representation.
        logdbg('Gw1000Service: field map is %s' % natural_sort_dict(self.field_map))
        loginf('Gw1000Service: lost contact will be logged every %d seconds' % self.lost_contact_log_period)
        # log specific debug but only if set ie. True
        debug_list = []
        if self.debug_rain:
            debug_list.append('debug_rain is %s' % (self.debug_rain,))
        if self.debug_wind:
            debug_list.append('debug_wind is %s' % (self.debug_wind,))
        if self.debug_loop:
            debug_list.append('debug_loop is %s' % (self.debug_loop,))
        if len(debug_list) > 0:
            loginf('%s: %s' % ('Gw1000Service', ' '.join(debug_list)))

        # start the Gw1000Collector in its own thread
        self.collector.startup()
        # bind our self to the relevant WeeWX events
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)

    def new_loop_packet(self, event):
        """Augment a loop packet with device data.

        When a new loop packet arrives process the queue looking for any device
        sensor data packets. If there are sensor data packets keep the most
        recent, non-stale packet and use it to augment the loop packet. If
        there are no sensor data packets, or they are all stale, then the loop
        packet is not augmented.

        The queue may also contain other control data, eg exception reporting
        from the GatewayCollector thread. This control data needs to be
        processed as well.
        """

        # log the loop packet received if necessary, there are several debug
        # settings that may require this
        if self.debug_loop or self.debug_rain or self.debug_wind:
            loginf('GatewayService: Processing loop packet: %s %s' % (timestamp_to_string(event.packet['dateTime']),
                                                                      natural_sort_dict(event.packet)))
        # we are about to process the queue so reset our cached sensor data
        # packet property
        self.cached_sensor_data = None
        # now process the queue until it is empty
        while True:
            # Get the next item from the queue. Wrap in a try to catch any
            # instances where the queue is empty as that is our signal to break
            # out of the while loop.
            try:
                # get the next item from the collector queue, but don't dwell
                # very long
                queue_data = self.collector.queue.get(True, 0.5)
            except six.moves.queue.Empty:
                # there was nothing in the queue so if required log this and
                # then break out of the while loop
                if self.debug_loop or self.debug_rain or self.debug_wind:
                    loginf('GatewayService: No queued items to process')
                if self.lost_con_ts is not None and time.time() > self.lost_con_ts + self.lost_contact_log_period:
                    self.lost_con_ts = time.time()
                    self.set_failure_logging(True)
                # now break out of the while loop
                break
            else:
                # We received something in the queue, it will be one of three
                # things:
                # 1. a dict containing sensor data
                # 2. an exception
                # 3. the value None signalling a serious error that means the
                #    Collector needs to shut down

                # if the data has a 'keys' attribute it is a dict so must be
                # data
                if hasattr(queue_data, 'keys'):
                    # we have a dict so assume it is data
                    self.lost_con_ts = None
                    self.set_failure_logging(True)
                    # log the received data if necessary, there are several
                    # debug settings that may require this, start from the
                    # highest (most encompassing) and work to the lowest (least
                    # encompassing)
                    if self.debug_loop:
                        if 'datetime' in queue_data:
                            # if we have a 'datetime' field it is almost
                            # certainly a sensor data packet
                            loginf('GatewayService: Received queued sensor '
                                   'data: %s %s' % (timestamp_to_string(queue_data['datetime']),
                                                    natural_sort_dict(queue_data)))
                        else:
                            # There is no 'datetime' field, this should not
                            # happen. Log it in any case.
                            loginf('GatewayService: Received queued data: %s' % (natural_sort_dict(queue_data),))
                    else:
                        # perhaps we have individual debugs such as rain or wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # mapped data, if it does not exist say so
                            self.log_rain_data(queue_data,
                                               'GatewayService: Received %s data' % self.collector.station.model)
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # received data, if they do not exist say so
                            self.log_wind_data(queue_data,
                                               'GatewayService: Received %s data' % self.collector.station.model)
                    # now process the just received sensor data packet
                    self.process_queued_sensor_data(queue_data, event.packet['dateTime'])

                # if it's a tuple then it's a tuple with an exception and
                # exception text
                elif isinstance(queue_data, BaseException):
                    # We have an exception. The collector did not deem it
                    # serious enough to want to shut down, or it would have
                    # sent None instead. The action we take depends on the type
                    # of exception it is. If it's a GWIOError we can ignore it
                    # as appropriate action will have been taken by the
                    # GatewayCollector. If it is anything else we log it.
                    # process the exception
                    self.process_queued_exception(queue_data)

                # if it's None then it's a signal the Collector needs to shutdown
                elif queue_data is None:
                    # if debug_loop log what we received
                    if self.debug_loop:
                        loginf('GatewayService: Received collector shutdown signal')
                    # we received the signal that the GatewayCollector needs to
                    # shut down, that means we cannot continue so call our shutdown
                    # method which will also shut down the GatewayCollector thread
                    self.shutDown()
                    # the GatewayCollector has been shut down, so we will not see
                    # anything more in the queue. We are still bound to
                    # NEW_LOOP_PACKET but since the queue is always empty we
                    # will just wait for the empty queue timeout before exiting

                # if it's none of the above (which it should never be) we don't
                # know what to do with it so pass and wait for the next item in
                # the queue
                else:
                    pass

        # we have now finished processing the queue, do we have a sensor data
        # packet to add to the loo packet
        if self.cached_sensor_data is not None:
            # we have a sensor data packet
            # if not already done so determine which cumulative rain field will
            # be used to determine the per period rain field
            if not self.rain_mapping_confirmed or not self.piezo_rain_mapping_confirmed:
                self.get_cumulative_rain_field(self.cached_sensor_data)
            # get the rainfall this period from total
            self.calculate_rain(self.cached_sensor_data)
            # get the lightning strike count this period from total
            self.calculate_lightning_count(self.cached_sensor_data)
            # map the raw data to WeeWX loop packet fields
            mapped_data = self.map_data(self.cached_sensor_data)
            # log the mapped data if necessary
            if self.debug_loop:
                loginf('GatewayService: Mapped %s data: %s' % (self.collector.station.model,
                                                               natural_sort_dict(mapped_data)))
            else:
                # perhaps we have individual debugs such as rain or wind
                if self.debug_rain:
                    # debug_rain is set so log the 'rain' field in the
                    # mapped data, if it does not exist say so
                    self.log_rain_data(mapped_data,
                                       'GatewayService: Mapped %s data' % self.collector.station.model)
                if self.debug_wind:
                    # debug_wind is set so log the 'wind' fields in the
                    # mapped data, if they do not exist say so
                    self.log_wind_data(mapped_data,
                                       'GatewayService: Mapped %s data' % self.collector.station.model)
            # and finally augment the loop packet with the mapped data
            self.augment_packet(event.packet, mapped_data)
            # log the augmented packet if necessary, there are several debug
            # settings that may require this, start from the highest (most
            # encompassing) and work to the lowest (least encompassing)
            if self.debug_loop or weewx.debug >= 2:
                loginf('GatewayService: Augmented packet: %s %s' % (timestamp_to_string(event.packet['dateTime']),
                                                                    natural_sort_dict(event.packet)))
            else:
                # perhaps we have individual debugs such as rain or wind
                if self.debug_rain:
                    # debug_rain is set so log the 'rain' field in the
                    # augmented loop packet, if it does not exist say
                    # so
                    self.log_rain_data(event.packet, 'GatewayService: Augmented packet')
                if self.debug_wind:
                    # debug_wind is set so log the 'wind' fields in the
                    # loop packet being emitted, if they do not exist
                    # say so
                    self.log_wind_data(event.packet, 'GatewayService: Augmented packet')

    def process_queued_sensor_data(self, sensor_data, date_time):
        """Process a sensor data packet received in the collector queue.

        When the queue is processed there may be multiple sensor data packets
        in the queue but we only want the most recent, non-stale packet. Check
        the received sensor packet is timestamped and not stale, if it is not
        stale and is newer than the previously cached sensor data packet then
        replace the cached packet with this packet.

        Non-timestamped sensor data packets are discarded.

        sensor_data: the sensor data packet obtained from the queue
        date_time:   the timestamp of the current loop packet
        """

        # first up check we have a field 'datetime' and that it is not None
        if 'datetime' in sensor_data and sensor_data['datetime'] is not None:
            # now check it is not stale
            if sensor_data['datetime'] > date_time - self.max_age:
                # the sensor data is not stale, but is it more recent than our
                # current cached packet
                if self.cached_sensor_data is None or sensor_data['datetime'] > self.cached_sensor_data['dateTime']:
                    # this packet is newer, so keep it
                    self.cached_sensor_data = dict(sensor_data)
                    # the cached packet will have the timestamp in the field
                    # 'datetime', WeeWX requires 'dateTime'. Do the change here
                    # rather than later.
                    self.cached_sensor_data['dateTime'] = self.cached_sensor_data.pop('datetime')

    def process_queued_exception(self, e):
        """Process an exception received in the collector queue."""

        # is it a GWIOError
        if isinstance(e, GWIOError):
            # set our failure logging appropriately
            if self.lost_con_ts is None:
                # we have previously been in contact with the device so set our
                # lost contact timestamp
                self.lost_con_ts = time.time()
                # any failure logging for this failure will already have
                # occurred in our GatewayCollector object and its Station, so
                # turn off failure logging
                self.set_failure_logging(False)
            elif self.log_failures:
                # we are already in a lost contact state, but failure logging
                # may have been turned on for a 'once in a while' log entry so
                # we need to turn it off again
                self.set_failure_logging(False)
        else:
            # it's not so log it
            logerr('GatewayService: Caught unexpected exception %s: %s' % (e.__class__.__name__,
                                                                           e))

    def augment_packet(self, packet, data):
        """Augment a loop packet with data from another packet.

        The data to be used for augmentation (the new data) may not be in the
        same unit system as the loop data being augmented so the new data is
        converted to the same unit system as used in the loop packet before
        augmentation occurs. Only fields that exist in the new data but not in
        the loop packet are added to the loop packet.

        packet: dict containing the loop packet
        data:   dict containing the data to be used to augment the loop packet
        """

        if self.debug_loop:
            _stem = 'GatewayService: Mapped data will be used to augment loop packet(%s)'
            loginf(_stem % timestamp_to_string(packet['dateTime']))
        # But the mapped data must be converted to the same unit system as
        # the packet being augmented. First get a converter.
        converter = weewx.units.StdUnitConverters[packet['usUnits']]
        # convert the mapped data to the same unit system as the packet to
        # be augmented
        converted_data = converter.convertDict(data)
        # if required log the converted data
        if self.debug_loop:
            loginf("GatewayService: Converted %s data: %s" % (self.collector.station.model,
                                                              natural_sort_dict(converted_data)))
        # now we can freely augment the packet with any of our mapped obs
        for field, data in six.iteritems(converted_data):
            # Any existing packet fields, whether they contain data or are
            # None, are respected and left alone. Only fields from the
            # converted data that do not already exist in the packet are
            # used to augment the packet.
            if field not in packet:
                packet[field] = data

    def set_failure_logging(self, log_failures):
        """Turn failure logging on or off.

        When operating as a service lost contact or other non-fatal errors
        should only be logged every so often so as not to flood the logs.
        Failure logging occurs at three levels:
        1. in myself (the service)
        2. in the GatewayCollector object
        3. in the GatewayCollector object's Station object

        Failure logging is turned on or off by setting the log_failures
        property True or False for each of the above 3 objects.
        """

        self.log_failures = log_failures
        self.collector.log_failures = log_failures
        self.collector.station.log_failures = log_failures

    def shutDown(self):
        """Shut down the service."""

        # the collector will likely be running in a thread so call its
        # shutdown() method so that any thread shut down/tidy up can occur
        self.collector.shutdown()


# for backwards compatibility
Gw1000Service = GatewayService


# ============================================================================
#                 GW1000 Loader/Configurator/Editor methods
# ============================================================================

def loader(config_dict, engine):
    return GatewayDriver(**config_dict[DRIVER_NAME])


def configurator_loader(config_dict):  # @UnusedVariable

    pass
    # return Gw1000Configurator()


def confeditor_loader():
    return Gw1000ConfEditor()


# ============================================================================
#                          class Gw1000ConfEditor
# ============================================================================

class Gw1000ConfEditor(weewx.drivers.AbstractConfEditor):
    # define our config as a multiline string so we can preserve comments
    accum_config = """
    [Accumulator]
        # Start GW1000 driver extractors
        [[daymaxwind]]
            extractor = last
        [[lightning_distance]]
            extractor = last
        [[lightning_strike_count]]
            extractor = sum
        [[lightning_last_det_time]]
            extractor = last
        [[stormRain]]
            extractor = last
        [[dayRain]]
            extractor = last
        [[weekRain]]
            extractor = last
        [[monthRain]]
            extractor = last
        [[yearRain]]
            extractor = last
        [[totalRain]]
            extractor = last
        [[t_rain]]
            extractor = sum
        [[t_stormRain]]
            extractor = last
        [[t_dayRain]]
            extractor = last
        [[t_weekRain]]
            extractor = last
        [[t_monthRain]]
            extractor = last
        [[t_yearRain]]
            extractor = last
        [[p_rain]]
            extractor = sum
        [[p_stormRain]]
            extractor = last
        [[p_dayRain]]
            extractor = last
        [[p_weekRain]]
            extractor = last
        [[p_monthRain]]
            extractor = last
        [[p_yearRain]]
            extractor = last
        [[pm2_51_24h_avg]]
            extractor = last
        [[pm2_52_24h_avg]]
            extractor = last
        [[pm2_53_24h_avg]]
            extractor = last
        [[pm2_54_24h_avg]]
            extractor = last
        [[pm2_55_24h_avg]]
            extractor = last
        [[pm10_24h_avg]]
            extractor = last
        [[co2_24h_avg]]
            extractor = last
        [[wh40_batt]]
            extractor = last
        [[wh26_batt]]
            extractor = last
        [[wh25_batt]]
            extractor = last
        [[wh65_batt]]
            extractor = last
        [[wh32_batt]]
            extractor = last
        [[wh31_ch1_batt]]
            extractor = last
        [[wh31_ch2_batt]]
            extractor = last
        [[wh31_ch3_batt]]
            extractor = last
        [[wh31_ch4_batt]]
            extractor = last
        [[wh31_ch5_batt]]
            extractor = last
        [[wh31_ch6_batt]]
            extractor = last
        [[wh31_ch7_batt]]
            extractor = last
        [[wh31_ch8_batt]]
            extractor = last
        [[wn34_ch1_batt]]
            extractor = last
        [[wn34_ch2_batt]]
            extractor = last
        [[wn34_ch3_batt]]
            extractor = last
        [[wn34_ch4_batt]]
            extractor = last
        [[wn34_ch5_batt]]
            extractor = last
        [[wn34_ch6_batt]]
            extractor = last
        [[wn34_ch7_batt]]
            extractor = last
        [[wn34_ch8_batt]]
            extractor = last
        [[wn35_ch1_batt]]
            extractor = last
        [[wn35_ch2_batt]]
            extractor = last
        [[wn35_ch3_batt]]
            extractor = last
        [[wn35_ch4_batt]]
            extractor = last
        [[wn35_ch5_batt]]
            extractor = last
        [[wn35_ch6_batt]]
            extractor = last
        [[wn35_ch7_batt]]
            extractor = last
        [[wn35_ch8_batt]]
            extractor = last
        [[wh41_ch1_batt]]
            extractor = last
        [[wh41_ch2_batt]]
            extractor = last
        [[wh41_ch3_batt]]
            extractor = last
        [[wh41_ch4_batt]]
            extractor = last
        [[wh45_batt]]
            extractor = last
        [[wh51_ch1_batt]]
            extractor = last
        [[wh51_ch2_batt]]
            extractor = last
        [[wh51_ch3_batt]]
            extractor = last
        [[wh51_ch4_batt]]
            extractor = last
        [[wh51_ch5_batt]]
            extractor = last
        [[wh51_ch6_batt]]
            extractor = last
        [[wh51_ch7_batt]]
            extractor = last
        [[wh51_ch8_batt]]
            extractor = last
        [[wh51_ch9_batt]]
            extractor = last
        [[wh51_ch10_batt]]
            extractor = last
        [[wh51_ch11_batt]]
            extractor = last
        [[wh51_ch12_batt]]
            extractor = last
        [[wh51_ch13_batt]]
            extractor = last
        [[wh51_ch14_batt]]
            extractor = last
        [[wh51_ch15_batt]]
            extractor = last
        [[wh51_ch16_batt]]
            extractor = last
        [[wh55_ch1_batt]]
            extractor = last
        [[wh55_ch2_batt]]
            extractor = last
        [[wh55_ch3_batt]]
            extractor = last
        [[wh55_ch4_batt]]
            extractor = last
        [[wh57_batt]]
            extractor = last
        [[wh68_batt]]
            extractor = last
        [[ws80_batt]]
            extractor = last
        [[wh40_sig]]
            extractor = last
        [[wh26_sig]]
            extractor = last
        [[wh25_sig]]
            extractor = last
        [[wh65_sig]]
            extractor = last
        [[wh32_sig]]
            extractor = last
        [[wh31_ch1_sig]]
            extractor = last
        [[wh31_ch2_sig]]
            extractor = last
        [[wh31_ch3_sig]]
            extractor = last
        [[wh31_ch4_sig]]
            extractor = last
        [[wh31_ch5_sig]]
            extractor = last
        [[wh31_ch6_sig]]
            extractor = last
        [[wh31_ch7_sig]]
            extractor = last
        [[wh31_ch8_sig]]
            extractor = last
        [[wn34_ch1_sig]]
            extractor = last
        [[wn34_ch2_sig]]
            extractor = last
        [[wn34_ch3_sig]]
            extractor = last
        [[wn34_ch4_sig]]
            extractor = last
        [[wn34_ch5_sig]]
            extractor = last
        [[wn34_ch6_sig]]
            extractor = last
        [[wn34_ch7_sig]]
            extractor = last
        [[wn34_ch8_sig]]
            extractor = last
        [[wn35_ch1_sig]]
            extractor = last
        [[wn35_ch2_sig]]
            extractor = last
        [[wn35_ch3_sig]]
            extractor = last
        [[wn35_ch4_sig]]
            extractor = last
        [[wn35_ch5_sig]]
            extractor = last
        [[wn35_ch6_sig]]
            extractor = last
        [[wn35_ch7_sig]]
            extractor = last
        [[wn35_ch8_sig]]
            extractor = last
        [[wh41_ch1_sig]]
            extractor = last
        [[wh41_ch2_sig]]
            extractor = last
        [[wh41_ch3_sig]]
            extractor = last
        [[wh41_ch4_sig]]
            extractor = last
        [[wh45_sig]]
            extractor = last
        [[wh51_ch1_sig]]
            extractor = last
        [[wh51_ch2_sig]]
            extractor = last
        [[wh51_ch3_sig]]
            extractor = last
        [[wh51_ch4_sig]]
            extractor = last
        [[wh51_ch5_sig]]
            extractor = last
        [[wh51_ch6_sig]]
            extractor = last
        [[wh51_ch7_sig]]
            extractor = last
        [[wh51_ch8_sig]]
            extractor = last
        [[wh51_ch9_sig]]
            extractor = last
        [[wh51_ch10_sig]]
            extractor = last
        [[wh51_ch11_sig]]
            extractor = last
        [[wh51_ch12_sig]]
            extractor = last
        [[wh51_ch13_sig]]
            extractor = last
        [[wh51_ch14_sig]]
            extractor = last
        [[wh51_ch15_sig]]
            extractor = last
        [[wh51_ch16_sig]]
            extractor = last
        [[wh55_ch1_sig]]
            extractor = last
        [[wh55_ch2_sig]]
            extractor = last
        [[wh55_ch3_sig]]
            extractor = last
        [[wh55_ch4_sig]]
            extractor = last
        [[wh57_sig]]
            extractor = last
        [[wh68_sig]]
            extractor = last
        [[ws80_sig]]
            extractor = last
        # End GW1000 driver extractors
    """

    @property
    def default_stanza(self):
        return """
    [GW1000]
        # This section is for the GW1000 API driver.

        # The driver to use:
        driver = user.gw1000

        # How often to poll the GW1000 API:
        poll_interval = %d
    """ % (default_poll_interval,)

    def get_conf(self, orig_stanza=None):
        """Given a configuration stanza, return a possibly modified copy
        that will work with the current version of the device driver.

        The default behavior is to return the original stanza, unmodified.

        Derived classes should override this if they need to modify previous
        configuration options or warn about deprecated or harmful options.

        The return value should be a long string. See default_stanza above
        for an example string stanza.
        """

        return self.default_stanza if orig_stanza is None else orig_stanza

    def prompt_for_settings(self):
        """Prompt for settings required for proper operation of this driver.

        Returns a dict of setting, value key pairs for settings to be included
        in the driver stanza. The _prompt() method may be used to prompt the
        user for input with a default.
        """

        # obtain IP address
        print()
        print("Specify the gateway device IP address, for example: 192.168.1.100")
        print("Set to 'auto' to autodiscover the gateway device IP address (not")
        print("recommended for systems with more than one gateway device)")
        ip_address = self._prompt('IP address',
                                  dflt=self.existing_options.get('ip_address'))
        # obtain port number
        print()
        print("Specify gateway device network port, for example: 45000")
        port = self._prompt('port', dflt=self.existing_options.get('port', default_port))
        # obtain poll interval
        print()
        print("Specify how often to poll the gateway API in seconds")
        poll_interval = self._prompt('Poll interval',
                                     dflt=self.existing_options.get('poll_interval',
                                                                    default_poll_interval))
        return {'ip_address': ip_address,
                'port': port,
                'poll_interval': poll_interval
                }

    @staticmethod
    def modify_config(config_dict):
        import weecfg

        # set loop_on_init
        loop_on_init_config = """loop_on_init = %d"""
        dflt = config_dict.get('loop_on_init', '1')
        label = """The GW1000 driver requires a network connection to the 
gateway device. Consequently, the absence of a network connection 
when WeeWX starts will cause WeeWX to exit and such a situation 
can occur on system startup. The 'loop_on_init' setting can be
used to mitigate such problems by having WeeWX retry startup 
indefinitely. Set to '0' to attempt startup once only or '1' to 
attempt startup indefinitely."""
        print()
        loop_on_init = int(weecfg.prompt_with_options(label, dflt, ['0', '1']))
        loop_on_init_dict = configobj.ConfigObj(StringIO(loop_on_init_config % (loop_on_init,)))
        config_dict.merge(loop_on_init_dict)
        if len(config_dict.comments['loop_on_init']) == 0:
            config_dict.comments['loop_on_init'] = ['',
                                                    '# Whether to try indefinitely to load the driver']
        print()

        # set record generation to software
        print("""Setting record_generation to software.""")
        config_dict['StdArchive']['record_generation'] = 'software'
        print()

        # set the accumulator extractor functions
        print("""Setting accumulator extractor functions.""")
        # construct our default accumulator config dict
        accum_config_dict = configobj.ConfigObj(StringIO(Gw1000ConfEditor.accum_config))
        # merge the existing config dict into our default accumulator config
        # dict so that we keep any changes made to [Accumulator] by the user
        accum_config_dict.merge(config_dict)
        # now make our updated accumulator config the config dict
        config_dict = configobj.ConfigObj(accum_config_dict)

        # we don't need weecfg any more so remove it from memory
        del weecfg
        print()


# ============================================================================
#                            GatewayDriver class
# ============================================================================

class GatewayDriver(weewx.drivers.AbstractDevice, Gateway):
    """Ecowitt gateway device driver class.

    A WeeWX driver to emit loop packets based on observational data obtained
    from the Ecowitt LAN/Wi-Fi Gateway API. The GatewayDriver should be used
    when there is no other data source or other sources data can be ingested
    via one or more WeeWX services.

    Data is obtained from the Ecowitt LAN/Wi-Fi Gateway API. The data is parsed
    and mapped to WeeWX fields and emitted as a WeeWX loop packet.

    Class GatewayCollector collects and parses data from the API. The
    GatewayCollector runs in a separate thread, so it does not block the main
    WeeWX processing loop. The GatewayCollector is turn uses child classes
    Station and Parser to interact directly with the API and parse the API
    responses respectively."""

    def __init__(self, **stn_dict):
        """Initialise a gateway device driver object."""

        # now initialize my superclasses
        super(GatewayDriver, self).__init__(**stn_dict)

        # log our version number
        loginf('GatewayDriver: version is %s' % DRIVER_VERSION)
        # log the relevant settings/parameters we are using
        if self.ip_address is None and self.port is None:
            loginf('GatewayDriver: %s IP address and port not specified, '
                   'attempting to discover %s...' % (self.collector.station.model,
                                                     self.collector.station.model))
        elif self.ip_address is None:
            loginf('GatewayDriver: %s IP address not specified, attempting '
                   'to discover %s...' % (self.collector.station.model,
                                          self.collector.station.model))
        elif self.port is None:
            loginf('GatewayDriver: %s port not specified, attempting '
                   'to discover %s...' % (self.collector.station.model,
                                          self.collector.station.model))
        loginf('GatewayDriver: %s address is %s:%d' % (self.collector.station.model,
                                                       self.collector.station.ip_address.decode(),
                                                       self.collector.station.port))
        loginf('GatewayDriver: poll interval is %d seconds' % self.poll_interval)
        logdbg('GatewayDriver: max tries is %d, retry wait time '
               'is %d seconds' % (self.max_tries,
                                  self.retry_wait))
        logdbg('GatewayDriver: broadcast address is %s:%d, broadcast '
               'timeout is %d seconds' % (self.broadcast_address.decode(),
                                          self.broadcast_port,
                                          self.broadcast_timeout))
        logdbg('GatewayDriver: socket timeout is %d seconds' % self.socket_timeout)
        # The field map. Field map dict output will be in unsorted key order.
        # It is easier to read if sorted alphanumerically, but we have keys
        # such as xxxxx16 that do not sort well. Use a custom natural sort of
        # the keys in a manually produced formatted dict representation.
        logdbg('GatewayDriver: field map is %s' % natural_sort_dict(self.field_map))
        # log specific debug but only if set ie. True
        debug_list = []
        if self.debug_rain:
            debug_list.append('debug_rain is %s' % (self.debug_rain,))
        if self.debug_wind:
            debug_list.append('debug_wind is %s' % (self.debug_wind,))
        if self.debug_loop:
            debug_list.append('debug_loop is %s' % (self.debug_loop,))
        if len(debug_list) > 0:
            loginf('%s: %s' % ('GatewayDriver', ' '.join(debug_list)))

        # start the Gw1000Collector in its own thread
        self.collector.startup()

    def genLoopPackets(self):
        """Generator function that returns loop packets.

        Run a continuous loop checking the GatewayCollector queue for data.
        When data arrives map the raw data to a WeeWX loop packet and yield the
        packet.
        """

        # generate loop packets forever
        while True:
            # wrap in a try to catch any instances where the queue is empty
            try:
                # get any data from the collector queue
                queue_data = self.collector.queue.get(True, 10)
            except six.moves.queue.Empty:
                # there was nothing in the queue so continue
                pass
            else:
                # We received something in the queue, it will be one of three
                # things:
                # 1. a dict containing sensor data
                # 2. an exception
                # 3. the value None signalling a serious error that means the
                #    Collector needs to shut down

                # if the data has a 'keys' attribute it is a dict so must be
                # data
                if hasattr(queue_data, 'keys'):
                    # we have a dict so assume it is data
                    # log the received data if necessary
                    if self.debug_loop:
                        if 'datetime' in queue_data:
                            loginf('GatewayDriver: Received %s data: %s %s' % (self.collector.station.model,
                                                                               timestamp_to_string(
                                                                                   queue_data['datetime']),
                                                                               natural_sort_dict(queue_data)))
                        else:
                            loginf('GatewayDriver: Received %s data: %s' % (self.collector.station.model,
                                                                            natural_sort_dict(queue_data)))
                    else:
                        # perhaps we have individual debugs such as rain or
                        # wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # received data, if it does not exist say so
                            self.log_rain_data(queue_data,
                                               'GatewayDriver: Received %s data' % self.collector.station.model)
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # received data, if they do not exist say so
                            self.log_wind_data(queue_data,
                                               'GatewayDriver: Received %s data' % self.collector.station.model)
                    # Now start to create a loop packet. A loop packet must
                    # have a timestamp, if we have one (key 'datetime') in the
                    # received data use it otherwise allocate one.
                    if 'datetime' in queue_data:
                        packet = {'dateTime': queue_data['datetime']}
                    else:
                        # we don't have a timestamp so create one
                        packet = {'dateTime': int(time.time() + 0.5)}
                    # if not already determined, determine which cumulative rain
                    # field will be used to determine the per period rain field
                    if not self.rain_mapping_confirmed or not self.piezo_rain_mapping_confirmed:
                        self.get_cumulative_rain_field(queue_data)
                    # get the rainfall this period from total
                    self.calculate_rain(queue_data)
                    # get the lightning strike count this period from total
                    self.calculate_lightning_count(queue_data)
                    # map the raw data to WeeWX loop packet fields
                    mapped_data = self.map_data(queue_data)
                    # log the mapped data if necessary
                    if self.debug_loop:
                        if 'datetime' in mapped_data:
                            loginf('GatewayDriver: Mapped %s data: %s %s' % (self.collector.station.model,
                                                                             timestamp_to_string(
                                                                                 mapped_data['datetime']),
                                                                             natural_sort_dict(mapped_data)))
                        else:
                            loginf('GatewayDriver: Mapped %s data: %s' % (self.collector.station.model,
                                                                          natural_sort_dict(mapped_data)))
                    else:
                        # perhaps we have individual debugs such as rain or wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # mapped data, if it does not exist say so
                            self.log_rain_data(mapped_data,
                                               'GatewayDriver: Mapped %s data' % self.collector.station.model)
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # mapped data, if they do not exist say so
                            self.log_wind_data(mapped_data,
                                               'GatewayDriver: Mapped %s data' % self.collector.station.model)
                    # add the mapped data to the empty packet
                    packet.update(mapped_data)
                    # log the packet if necessary, there are several debug
                    # settings that may require this, start from the highest
                    # (most encompassing) and work to the lowest (least
                    # encompassing)
                    if self.debug_loop or weewx.debug >= 2:
                        loginf('GatewayDriver: Packet %s: %s' % (timestamp_to_string(packet['dateTime']),
                                                                 natural_sort_dict(packet)))
                    else:
                        # perhaps we have individual debugs such as rain or wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # loop packet being emitted, if it does not exist
                            # say so
                            self.log_rain_data(mapped_data,
                                               'GatewayDriver: Packet %s' % timestamp_to_string(packet['dateTime']))
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # loop packet being emitted, if they do not exist
                            # say so
                            self.log_wind_data(mapped_data,
                                               'GatewayDriver: Packets %s' % timestamp_to_string(packet['dateTime']))
                    # yield the loop packet
                    yield packet
                # if it's a tuple then it's a tuple with an exception and
                # exception text
                elif isinstance(queue_data, BaseException):
                    # We have an exception. The collector did not deem it
                    # serious enough to want to shut down or it would have sent
                    # None instead. The action we take depends on the type of
                    # exception it is. If it's a GWIOError we need to force
                    # the WeeWX engine to restart by raining a WeewxIOError. If
                    # it is anything else we log it and then raise it.
                    # first extract our exception
                    e = queue_data
                    # and process it if we have something
                    if e:
                        # is it a GWIOError
                        if isinstance(e, GWIOError):
                            # it is so we raise a WeewxIOError, ideally would
                            # use raise .. from .. but raise.. from .. is not
                            # available under Python 2
                            raise weewx.WeeWxIOError(e)
                        else:
                            # it's not so log it
                            logerr('GatewayDriver: Caught unexpected exception %s: %s' % (e.__class__.__name__,
                                                                                          e))
                            # then raise it, WeeWX will decide what to do
                            raise e
                # if it's None then its a signal the Collector needs to shutdown
                elif queue_data is None:
                    # if debug_loop log what we received
                    if self.debug_loop:
                        loginf('GatewayDriver: Received shutdown signal')
                    # we received the signal to shut down, so call closePort()
                    self.closePort()
                    # and raise an exception to cause the engine to shut down
                    raise GWIOError("GatewayCollector needs to shutdown")
                # if it's none of the above (which it should never be) we don't
                # know what to do with it so pass and wait for the next item in
                # the queue
                else:
                    pass

    @property
    def hardware_name(self):
        """Return the hardware name.

        Use the device model from our Collector's Station object, but if this
        is None use the driver name.
        """

        if self.collector.station.model is not None:
            return self.collector.station.model
        else:
            return DRIVER_NAME

    @property
    def mac_address(self):
        """Return the device MAC address."""

        return self.collector.mac_address

    @property
    def firmware_version(self):
        """Return the device firmware version string."""

        return self.collector.firmware_version

    @property
    def sensor_id_data(self):
        """Return the device sensor identification data.

        The sensor ID data is available via the data property of the Collector
        objects' sensors property.
        """

        return self.collector.sensors.data

    def closePort(self):
        """Close down the driver port."""

        # in this case there is no port to close, just shutdown the collector
        self.collector.shutdown()


# for backwards compatibility
Gw1000Driver = GatewayDriver


# ============================================================================
#                              class Collector
# ============================================================================

class Collector(object):
    """Base class for a client that polls an API."""

    # a queue object for passing data back to the driver
    queue = six.moves.queue.Queue()

    def __init__(self):
        pass

    def startup(self):
        pass

    def shutdown(self):
        pass


# ============================================================================
#                              class GatewayCollector
# ============================================================================

class GatewayCollector(Collector):
    """Class to collect and return data from an Ecowitt LAN/Wi-Fi Gateway
    device.

    A GatewayCollector object is responsible for obtaining data from an Ecowitt
    LAN/Wi-Fi Gateway device using the Ecowitt LAN/Wi-Fi Gateway device API. A
    GatewayCollector object also decodes this data and makes it available to
    WeeWX drivers, services and other components as required. A
    GatewayCollector object uses the following subordinate classes as
    indicated:
    - class Station. Communicates directly with the gateway device via the API
                     and obtains and validates gateway device responses.
    - class Parser.  Parses and decodes the validated gateway response data
                     returning observational and parametric data
    - class Sensors. Allows easy access sensor data from coded API sensor data
    """

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
    # list of dicts of weather services that I know about
    services = [{'name': 'ecowitt_net',
                 'long_name': 'Ecowitt.net'
                 },
                {'name': 'wunderground',
                 'long_name': 'Wunderground'
                 },
                {'name': 'weathercloud',
                 'long_name': 'Weathercloud'
                 },
                {'name': 'wow',
                 'long_name': 'Weather Observations Website'
                 },
                {'name': 'custom',
                 'long_name': 'Customized'
                 }
                ]

    def __init__(self, ip_address=None, port=None, broadcast_address=None,
                 broadcast_port=None, socket_timeout=None, broadcast_timeout=None,
                 poll_interval=default_poll_interval,
                 max_tries=default_max_tries, retry_wait=default_retry_wait,
                 use_wh32=True, ignore_wh40_batt=True, show_battery=False,
                 log_unknown_fields=False, debug_rain=False, debug_wind=False,
                 debug_sensors=False):
        """Initialise our class."""

        # initialize my base class:
        super(GatewayCollector, self).__init__()

        # interval between polls of the API, use a default
        self.poll_interval = poll_interval
        # how many times to poll the API before giving up, default is
        # default_max_tries
        self.max_tries = max_tries
        # period in seconds to wait before polling again, default is
        # default_retry_wait seconds
        self.retry_wait = retry_wait
        # are we using a WH32 sensor, if so tell our sensor id decoding we have
        # a WH32, otherwise it will default to WH26.
        if use_wh32:
            # set the WH24 sensor id decode dict entry
            self.sensor_ids[b'\x05']['name'] = 'wh32'
            self.sensor_ids[b'\x05']['long_name'] = 'WH32'
        # get a station object to do the handle the interaction with the API
        self.station = GatewayCollector.Station(ip_address=ip_address,
                                                port=port,
                                                broadcast_address=broadcast_address,
                                                broadcast_port=broadcast_port,
                                                socket_timeout=socket_timeout,
                                                broadcast_timeout=broadcast_timeout,
                                                max_tries=max_tries,
                                                retry_wait=retry_wait)
        # Do we have a WH24 attached? First obtain our system parameters.
        _sys_params = self.station.get_system_params()
        # WH24 is indicated by the 6th byte being 0
        is_wh24 = six.indexbytes(_sys_params, 5) == 0
        # Tell our sensor id decoding whether we have a WH24 or a WH65. By
        # default, we are coded to use a WH65. Is there a WH24 connected?
        if is_wh24:
            # set the WH24 sensor id decode dict entry
            self.sensor_ids[b'\x00']['name'] = 'wh24'
            self.sensor_ids[b'\x00']['long_name'] = 'WH24'
        # start off logging failures
        self.log_failures = True
        # get a parser object to parse any data from the station
        self.parser = GatewayCollector.Parser(log_unknown_fields=log_unknown_fields,
                                              debug_rain=debug_rain,
                                              debug_wind=debug_wind)
        # get a sensors object to handle sensor ID data
        self.sensors_obj = GatewayCollector.Sensors(ignore_wh40_batt=ignore_wh40_batt,
                                                    show_battery=show_battery,
                                                    debug_sensors=debug_sensors)
        # update the sensors object
        self.update_sensor_id_data()
        # do we have a legacy WH40 and how are we handling its battery state
        # data
        if b'\x03' in self.sensors_obj.connected_addresses and self.sensors_obj.legacy_wh40:
            # we have a connected legacy WH40
            if ignore_wh40_batt:
                _msg = 'Legacy WH40 detected, WH40 battery state data will be ignored'
            else:
                _msg = 'Legacy WH40 detected, WH40 battery state data will be reported'
            loginf(_msg)
        # create a thread property
        self.thread = None
        # we start off not collecting data, it will be turned on later when we
        # are threaded
        self.collect_data = False

    def collect(self):
        """Collect and queue sensor data by polling the API.

        Loop forever waking periodically to see if it is time to quit or
        collect more data. A dictionary of data is placed in the queue on each
        successful poll of the device. If an exception is raised when
        interacting with the device the exception is placed in the queue as a
        signal to our parent that there is a problem.
        """

        # initialise ts of last time API was polled
        last_poll = 0
        # collect data continuously while we are told to collect data
        while self.collect_data:
            # store the current time
            now = time.time()
            # is it time to poll?
            if now - last_poll > self.poll_interval:
                # it is time to poll, wrap in a try..except in case we get a
                # GWIOError exception
                try:
                    queue_data = self.get_current_data()
                except GWIOError as e:
                    # a GWIOError occurred, most likely because the Station
                    # object could not contact the device
                    # first up log the event, but only if we are logging
                    # failures
                    if self.log_failures:
                        logerr('Unable to obtain live sensor data')
                    # assign the GWIOError exception, so it will be sent in
                    # the queue to our controlling object
                    queue_data = e
                # put the queue data in the queue
                self.queue.put(queue_data)
                # debug log when we will next poll the API
                logdbg('Next update in %d seconds' % self.poll_interval)
                # reset the last poll ts
                last_poll = now
            # sleep for a second and then see if its time to poll again
            time.sleep(1)

    def get_current_data(self):
        """Get all current sensor data.

        Return current sensor data, battery state data and signal state data
        for each sensor. The current sensor data consists of sensor data
        available through multiple API commands. Each API command response is
        parsed and the results accumulated in a dictionary. Battery and signal
        state for each sensor is added to this dictionary. The dictionary is
        timestamped and the timestamped accumulated data is returned. If the
        API does not return any data a suitable exception will have been
        raised.
        """

        # first obtain the bulk of the current raw sensor data via the API, if
        # the data cannot be obtained we will see a GWIOError exception, if we
        # do let it bubble up
        livedata_response = self.station.get_livedata()
        # Now get the raw rain data via the API. If the data cannot be obtained
        # we may see an GWIOError exception or an UnknownApiCommand exception.
        # If we get the UnknownApiCommand exception it is likely due to an old
        # device that cannot handle CMD_READ_RAIN in which case our only
        # available rain data will already be in our livedata response so just
        # set the raindata response to None. If we get the GWIOError then let
        # it bubble up.
        try:
            raindata_response = self.station.read_rain()
        except UnknownApiCommand:
            raindata_response = None
        except GWIOError:
            raise
        # if we made it here our raw data was validated by checksum, now
        # get a timestamp to use in case our data does not come with one
        _timestamp = int(time.time())
        # parse the raw livedata (the parsed data is a dict keyed by internal
        # device field names and containing the decoded raw sensor data)
        parsed_data = self.parser.parse_livedata(livedata_response)
        # now parse the raw rain data if we have any and update our parsed data
        # dict
        if raindata_response is not None:
            parsed_data.update(self.parser.parse_read_rain(raindata_response))
        # add the timestamp to the data dict
        parsed_data['datetime'] = _timestamp
        # log the parsed data but only if debug>=3
        if weewx.debug >= 3:
            logdbg("Parsed data: %s" % parsed_data)
        # The parsed data does not currently contain any sensor battery state
        # or signal level data. The battery state and signal level data for
        # each sensor can be obtained from the API via our Sensors object.
        # First we need to update our Sensors object with current sensor ID data
        self.update_sensor_id_data()
        # now add any sensor battery state and signal level data to the parsed
        # data
        parsed_data.update(self.sensors_obj.battery_and_signal_data)
        # log the processed parsed data but only if debug>=3
        if weewx.debug >= 3:
            logdbg("Processed parsed data: %s" % parsed_data)
        return parsed_data

    def update_sensor_id_data(self):
        """Update the Sensors object with current sensor ID data."""

        # first get the current sensor ID data
        sensor_id_data = self.station.get_sensor_id()
        # now use the sensor ID data to re-initialise our sensors object
        self.sensors_obj.set_sensor_id_data(sensor_id_data)

    @property
    def rain_data(self):
        """Obtain device rain data.

        Uses the API command CMD_READ_RAINDATA to obtain 'traditional' rain
        gauge data only. To obtain 'traditional' and 'piezo' rain data use the
        GatewayCollector.all_rain_data property instead.
        """

        # obtain the rain data via the API
        response = self.station.read_raindata()
        # return the parsed response
        return self.parser.parse_read_raindata(response)

    @property
    def all_rain_data(self):
        """Obtain all device rain data.

        Uses the API command CMD_READ_RAIN to obtain 'traditional' and 'piezo'
        gauge rain data.
        """

        # obtain the rain data via the API
        response = self.station.read_rain()
        # return the parsed response
        return self.parser.parse_read_rain(response)

    @property
    def mulch_offset(self):
        """Obtain device multi-channel temperature and humidity offset data."""

        # obtain the mulch offset data via the API
        response = self.station.get_mulch_offset()
        # return the parsed response
        return self.parser.parse_get_mulch_offset(response)

    @property
    def mulch_t_offset(self):
        """Obtain device multi-channel temperature (WN34) offset data."""

        # obtain the mulch offset data via the API
        response = self.station.get_mulch_t_offset()
        # return the parsed response
        return self.parser.parse_get_mulch_t_offset(response)

    @property
    def pm25_offset(self):
        """Obtain device PM2.5 offset data."""

        # obtain the PM2.5 offset data via the API
        response = self.station.get_pm25_offset()
        # return the parsed response
        return self.parser.parse_get_pm25_offset(response)

    @property
    def co2_offset(self):
        """Obtain device WH45 CO2, PM10 and PM2.5 offset data."""

        # obtain the WH45 offset data via the API
        response = self.station.get_co2_offset()
        # return the parsed response
        return self.parser.parse_get_co2_offset(response)

    @property
    def calibration(self):
        """Obtain device calibration data."""

        # obtain the calibration data via the API
        response = self.station.get_calibration_coefficient()
        # parse the response
        parsed_gain = self.parser.parse_read_gain(response)
        # obtain the offset calibration data via the API
        response = self.station.get_offset_calibration()
        # update our parsed gain data with the parsed offset calibration data
        parsed_gain.update(self.parser.parse_read_calibration(response))
        # return the parsed data
        return parsed_gain

    @property
    def soil_calibration(self):
        """Obtain device soil moisture sensor calibration data."""

        # obtain the soil moisture calibration data via the API
        response = self.station.get_soil_calibration()
        # return the parsed response
        return self.parser.parse_get_soilhumiad(response)

    @property
    def system_parameters(self):
        """Obtain device system parameters."""

        # obtain the system parameters data via the API
        response = self.station.get_system_params()
        # return the parsed response
        return self.parser.parse_read_ssss(response)

    @property
    def ecowitt_net(self):
        """Obtain device Ecowitt.net service parameters.

        Also includes the device MAC address.
        """

        # obtain the system parameters data via the API
        response = self.station.get_ecowitt_net_params()
        # parse the response
        ecowitt = self.parser.parse_read_ecowitt(response)
        # add the device MAC address to the parsed data
        ecowitt['mac'] = self.mac_address
        # return the parsed response
        return ecowitt

    @property
    def wunderground(self):
        """Obtain device Weather Underground service parameters."""

        # obtain the system parameters data via the API
        response = self.station.get_wunderground_params()
        # return the parsed response
        return self.parser.parse_read_wunderground(response)

    @property
    def wow(self):
        """Obtain device Weather Observations Website service parameters."""

        # obtain the system parameters data via the API
        response = self.station.get_wow_params()
        # return the parsed response
        return self.parser.parse_read_wow(response)

    @property
    def weathercloud(self):
        """Obtain device Weathercloud service parameters."""

        # obtain the system parameters data via the API
        response = self.station.get_weathercloud_params()
        # return the parsed response
        return self.parser.parse_read_weathercloud(response)

    @property
    def custom(self):
        """Obtain device custom server parameters."""

        # obtain the system parameters data via the API
        response = self.station.get_custom_params()
        # obtain the parsed response
        data_dict = self.parser.parse_read_customized(response)
        # the user path is obtained separately, get the user path and add it to
        # our response
        data_dict.update(self.usr_path)
        # return the resulting parsed data
        return data_dict

    @property
    def usr_path(self):
        """Obtain the device user defined custom paths."""

        # return the device user defined custom path
        response = self.station.get_usr_path()
        # return the parsed response
        return self.parser.parse_read_usr_path(response)

    @property
    def mac_address(self):
        """Obtain the device MAC address."""

        # obtain the device MAC address bytes
        response = self.station.get_mac_address()
        # return the parsed response
        return self.parser.parse_read_station_mac(response)

    @property
    def firmware_version(self):
        """Obtain the device firmware version string."""

        # get the firmware bytestring via the API
        response = self.station.get_firmware_version()
        # return the parsed response
        return self.parser.parse_read_firmware_version(response)

    @property
    def sensors(self):
        """Get the current Sensors object.

        A Sensors object holds the address, id, battery state and signal level
        data sensors known to the device. The sensor id value can be used to
        discriminate between connected sensors, connecting sensors and disabled
        sensor addresses.

        Before using the GatewayCollector's Sensors object it should be updated
        with recent sensor ID data via the API
        """

        # obtain current sensor id data via the API, we may get a GWIOError
        # exception, if we do let it bubble up
        response = self.station.get_sensor_id()
        # if we made it here our response was validated by checksum
        # re-initialise our sensors object with the sensor ID data we just
        # obtained
        self.sensors_obj.set_sensor_id_data(response)
        # return our Sensors object
        return self.sensors_obj

    def startup(self):
        """Start a thread that collects data from the API."""

        try:
            self.thread = GatewayCollector.CollectorThread(self)
            self.collect_data = True
            self.thread.setDaemon(True)
            self.thread.setName('GatewayCollectorThread')
            self.thread.start()
        except threading.ThreadError:
            logerr("Unable to launch GatewayCollector thread")
            self.thread = None

    def shutdown(self):
        """Shut down the thread that collects data from the API.

        Tell the thread to stop, then wait for it to finish.
        """

        # we only need do something if a thread exists
        if self.thread:
            # tell the thread to stop collecting data
            self.collect_data = False
            # terminate the thread
            self.thread.join(10.0)
            # log the outcome
            if self.thread.is_alive():
                logerr("Unable to shut down GatewayCollector thread")
            else:
                loginf("GatewayCollector thread has been terminated")
        self.thread = None

    class CollectorThread(threading.Thread):
        """Class using a thread to collect data via the Ecowitt LAN/Wi-Fi
        Gateway API."""

        def __init__(self, client):
            # initialise our parent
            threading.Thread.__init__(self)
            # keep reference to the client we are supporting
            self.client = client
            self.name = 'gateway-collector'

        def run(self):
            # rather than letting the thread silently fail if an exception
            # occurs within the thread, wrap in a try..except so the exception
            # can be caught and available exception information displayed
            try:
                # kick the collection off
                self.client.collect()
            except:
                # we have an exception so log what we can
                log_traceback_critical('    ****  ')

    class Station(object):
        """Class to interact directly with the Ecowitt LAN/Wi-Fi Gateway API.

        A Station object knows how to:
        1.  discover a device via UDP broadcast
        2.  send a command to the API
        3.  receive a response from the API
        4.  verify the response as valid

        A Station object needs an IP address and port as well as a network
        broadcast address and port.
        """

        # Ecowitt LAN/Wi-Fi Gateway API commands
        commands = {
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
            'CMD_GET_MulCH_T_OFFSET': b'\x59'
        }
        # header used in each API command and response packet
        header = b'\xff\xff'
        # known device models
        known_models = ('GW1000', 'GW1100', 'GW2000',
                        'WH2650', 'WH2680', 'WN1900')

        def __init__(self, ip_address=None, port=None,
                     broadcast_address=None, broadcast_port=None,
                     socket_timeout=None, broadcast_timeout=None,
                     max_tries=default_max_tries,
                     retry_wait=default_retry_wait, mac=None):

            # network broadcast address
            self.broadcast_address = broadcast_address if broadcast_address is not None else default_broadcast_address
            # network broadcast port
            self.broadcast_port = broadcast_port if broadcast_port is not None else default_broadcast_port
            self.socket_timeout = socket_timeout if socket_timeout is not None else default_socket_timeout
            self.broadcast_timeout = broadcast_timeout if broadcast_timeout is not None else default_broadcast_timeout

            # initialise flags to indicate if IP address or port were discovered
            self.ip_discovered = ip_address is None
            self.port_discovered = port is None
            # if IP address or port was not specified (None) then attempt to
            # discover the device with a UDP broadcast
            if ip_address is None or port is None:
                for attempt in range(max_tries):
                    try:
                        # discover devices on the local network, the result is
                        # a list of dicts in IP address order with each dict
                        # containing data for a unique discovered device
                        device_list = self.discover()
                    except socket.error as e:
                        _msg = "Unable to detect device IP address and port: %s (%s)" % (e, type(e))
                        logerr(_msg)
                        # signal that we have a critical error
                        raise
                    else:
                        # did we find any devices
                        if len(device_list) > 0:
                            # we have at least one, arbitrarily choose the first one
                            # found as the one to use
                            disc_ip = device_list[0]['ip_address']
                            disc_port = device_list[0]['port']
                            # log the fact as well as what we found
                            gw1000_str = ', '.join([':'.join(['%s:%d' % (d['ip_address'],
                                                                         d['port'])]) for d in device_list])
                            if len(device_list) == 1:
                                stem = "%s was" % device_list[0]['model']
                            else:
                                stem = "Multiple devices were"
                            loginf("%s found at %s" % (stem, gw1000_str))
                            ip_address = disc_ip if ip_address is None else ip_address
                            port = disc_port if port is None else port
                            break
                        else:
                            # did not discover any device so log it
                            logdbg("Failed attempt %d to detect device IP address and/or port" % (attempt + 1,))
                            # do we try again or raise an exception
                            if attempt < max_tries - 1:
                                # we still have at least one more try left so sleep
                                # and try again
                                time.sleep(retry_wait)
                            else:
                                # we've used all our tries, log it and raise an exception
                                _msg = "Failed to detect device IP address and/or " \
                                       "port after %d attempts" % (attempt + 1,)
                                logerr(_msg)
                                raise GWIOError(_msg)
            # set our ip_address property but encode it first, it saves doing
            # it repeatedly later
            self.ip_address = ip_address.encode()
            self.port = port
            self.max_tries = max_tries
            self.retry_wait = retry_wait
            # start off logging failures
            self.log_failures = True
            # Get my MAC address to use later if we have to rediscover. Within
            # class Station the MAC address is stored as a bytestring.
            if mac is None:
                self.mac = self.get_mac_address()
            else:
                self.mac = mac
            # get my device model
            try:
                _firmware_b = self.get_firmware_version()
            except GWIOError:
                self.model = None
            else:
                _firmware_t = struct.unpack("B" * len(_firmware_b), _firmware_b)
                _firmware_str = "".join([chr(x) for x in _firmware_t[5:5 + _firmware_t[4]]])
                self.model = self.get_model_from_firmware(_firmware_str)

        def discover(self):
            """Discover any devices on the local network.

            Send a UDP broadcast and check for replies. Decode each reply to
            obtain details of any devices on the local network. Create a dict
            of details for each device including a derived model name.
            Construct a list of dicts with details of unique (MAC address)
            devices that responded. When complete return the list of devices
            found.
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
            if weewx.debug >= 3:
                logdbg("Sending broadcast packet '%s' to '%s:%d'" % (bytes_to_hex(packet),
                                                                     self.broadcast_address,
                                                                     self.broadcast_port))
            # initialise a list for the results as multiple devices may respond
            result_list = []
            # send the Broadcast command
            s.sendto(packet, (self.broadcast_address, self.broadcast_port))
            # obtain any responses
            while True:
                try:
                    response = s.recv(1024)
                    # log the response if debug is high enough
                    if weewx.debug >= 3:
                        logdbg("Received broadcast response '%s'" % (bytes_to_hex(response),))
                except socket.timeout:
                    # if we time out then we are done
                    break
                except socket.error:
                    # raise any other socket error
                    raise
                else:
                    # check the response is valid
                    try:
                        self.check_response(response, self.commands['CMD_BROADCAST'])
                    except InvalidChecksum as e:
                        # the response was not valid, log it and attempt again
                        # if we haven't had too many attempts already
                        logdbg("Invalid response to command '%s': %s" % ('CMD_BROADCAST', e))
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
                        logerr("Unexpected exception occurred while checking response "
                               "to command '%s': %s" % ('CMD_BROADCAST', e))
                        log_traceback_error('    ****  ')
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
            data_dict = dict()
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
                return self.get_model(firmware_string)
            else:
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

            return self.get_model(ssid_string)

        def get_model(self, t):
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
                # we don't have a known model so return None
                return None
            else:
                # we have no string so return None
                return None

        def get_livedata(self):
            """Get live data.

            Sends the API command to the device to obtain live data with
            retries. If the device cannot be contacted re-discovery is
            attempted. If rediscovery is successful the command is sent again
            otherwise the lost contact timestamp is set and a GWIOError
            exception raised. Any code that calls this method should be
            prepared to handle this exception.
            """

            # send the API command to obtain live data from the device, be
            # prepared to catch the exception raised if the device cannot be
            # contacted
            try:
                # return the validated API response
                return self.send_cmd_with_retries('CMD_GW1000_LIVEDATA')
            except GWIOError:
                # there was a problem contacting the device, it could be it has
                # changed IP address so attempt to rediscover
                if not self.rediscover():
                    # we could not re-discover so raise the exception
                    raise
                else:
                    # we did rediscover successfully so try again, if it fails
                    # we get another GWIOError exception which will be raised
                    return self.send_cmd_with_retries('CMD_GW1000_LIVEDATA')

        def read_raindata(self):
            """Get traditional gauge rain data.

            Sends the API command to obtain traditional gauge rain data from
            the device with retries. If the device cannot be contacted a
            GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by read_raindata(). Any code calling
            read_raindata() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_RAINDATA')

        def get_system_params(self):
            """Read system parameters.

            Sends the API command to obtain system parameters from the device
            with retries. If the device cannot be contacted a GWIOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_system_params(). Any code calling
            get_system_params() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_SSSS')

        def get_ecowitt_net_params(self):
            """Get Ecowitt.net parameters.

            Sends the API command to obtain the device Ecowitt.net parameters
            with retries. If the device cannot be contacted a GWIOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_ecowitt_net_params(). Any code calling
            get_ecowitt_net_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_ECOWITT')

        def get_wunderground_params(self):
            """Get Weather Underground parameters.

            Sends the API command to obtain the device Weather Underground
            parameters with retries. If the device cannot be contacted a
            GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by get_wunderground_params(). Any code
            calling get_wunderground_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_WUNDERGROUND')

        def get_weathercloud_params(self):
            """Get Weathercloud parameters.

            Sends the API command to obtain the device Weathercloud parameters
            with retries. If the device cannot be contacted a GWIOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_weathercloud_params(). Any code calling
            get_weathercloud_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_WEATHERCLOUD')

        def get_wow_params(self):
            """Get Weather Observations Website parameters.

            Sends the API command to obtain the device Weather Observations
            Website parameters with retries. If the device cannot be contacted
            a GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by get_wow_params(). Any code calling
            get_wow_params() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_WOW')

        def get_custom_params(self):
            """Get custom server parameters.

            Sends the API command to obtain the device custom server parameters
            with retries. If the device cannot be contacted a GWIOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_custom_params(). Any code calling
            get_custom_params() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_CUSTOMIZED')

        def get_usr_path(self):
            """Get user defined custom path.

            Sends the API command to obtain the device user defined custom path
            with retries. If the device cannot be contacted a GWIOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_usr_path(). Any code calling get_usr_path() should
            be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_USR_PATH')

        def get_mac_address(self):
            """Get device MAC address.

            Sends the API command to obtain the device MAC address with
            retries. If the device cannot be contacted a GWIOError will have
            been raised by send_cmd_with_retries() which will be passed through
            by get_mac_address(). Any code calling get_mac_address() should be
            prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_STATION_MAC')

        def get_firmware_version(self):
            """Get device firmware version.

            Sends the API command to obtain device firmware version with
            retries. If the device cannot be contacted a GWIOError will have
            been raised by send_cmd_with_retries() which will be passed through
            by get_firmware_version(). Any code calling get_firmware_version()
            should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_FIRMWARE_VERSION')

        def get_sensor_id(self):
            """Get sensor ID data.

            Sends the API command to obtain sensor ID data from the device with
            retries. If the device cannot be contacted re-discovery is
            attempted. If rediscovery is successful the command is tried again
            otherwise the lost contact timestamp is set and the exception
            raised. Any code that calls this method should be prepared to
            handle a GWIOError exception.
            """

            # send the API command to obtain sensor ID data from the device, be
            # prepared to catch the exception raised if the device cannot be
            # contacted
            try:
                return self.send_cmd_with_retries('CMD_READ_SENSOR_ID_NEW')
            except GWIOError:
                # there was a problem contacting the device, it could be it has
                # changed IP address so attempt to rediscover
                if not self.rediscover():
                    # we could not re-discover so raise the exception
                    raise
                else:
                    # we did rediscover successfully so try again, if it fails
                    # we get another GWIOError exception which will be
                    # raised
                    return self.send_cmd_with_retries('CMD_READ_SENSOR_ID_NEW')

        def get_mulch_offset(self):
            """Get multichannel temperature and humidity offset data.

            Sends the API command to obtain the multichannel temperature and
            humidity offset data with retries. If the device cannot be
            contacted a GWIOError will have been raised by
            send_cmd_with_retries() which will be passed through by
            get_mulch_offset(). Any code calling get_mulch_offset() should be
            prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_MulCH_OFFSET')

        def get_mulch_t_offset(self):
            """Get multichannel temperature (WN34) offset data.

            Sends the API command to obtain the multichannel temperature (WN34)
            offset data with retries. If the device cannot be contacted a
            GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by get_mulch_t_offset(). Any code calling
            get_mulch_t_offset() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_MulCH_T_OFFSET')

        def get_pm25_offset(self):
            """Get PM2.5 offset data.

            Sends the API command to obtain the PM2.5 sensor offset data with
            retries. If the device cannot be contacted a GWIOError will have
            been raised by send_cmd_with_retries() which will be passed through
            by get_pm25_offset(). Any code calling get_pm25_offset() should be
            prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_PM25_OFFSET')

        def get_calibration_coefficient(self):
            """Get calibration coefficient data.

            Sends the API command to obtain the calibration coefficient data
            with retries. If the device cannot be contacted a GWIOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_calibration_coefficient(). Any code calling
            get_calibration_coefficient() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_GAIN')

        def get_soil_calibration(self):
            """Get soil moisture sensor calibration data.

            Sends the API command to obtain the soil moisture sensor
            calibration data with retries. If the device cannot be contacted a
            GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by get_soil_calibration(). Any code calling
            get_soil_calibration() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_SOILHUMIAD')

        def get_offset_calibration(self):
            """Get offset calibration data.

            Sends the API command to obtain the offset calibration data with
            retries. If the device cannot be contacted a GWIOError will have
            been raised by send_cmd_with_retries() which will be passed through
            by get_offset_calibration(). Any code calling
            get_offset_calibration() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_CALIBRATION')

        def get_co2_offset(self):
            """Get WH45 CO2, PM10 and PM2.5 offset data.

            Sends the API command to obtain the WH45 CO2, PM10 and PM2.5 sensor
            offset data with retries. If the device cannot be contacted a
            GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by get_co2_offset(). Any code calling
            get_co2_offset() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_CO2_OFFSET')

        def read_rain(self):
            """Get traditional gauge and piezo gauge rain data.

            Sends the API command to obtain the traditional gauge and piezo
            gauge rain data with retries. If the device cannot be contacted a
            GWIOError will have been raised by send_cmd_with_retries() which
            will be passed through by get_piezo_rain_(). Any code calling
            get_piezo_rain_() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_RAIN')

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
            # attempt to send up to 'self.max_tries' times
            for attempt in range(self.max_tries):
                response = None
                # wrap in  try..except so we can catch any errors
                try:
                    response = self.send_cmd(packet)
                except socket.timeout as e:
                    # a socket timeout occurred, log it
                    if self.log_failures:
                        logdbg("Failed to obtain response to attempt %d "
                               "to send command '%s': %s" % (attempt + 1, cmd, e))
                except Exception as e:
                    # an exception was encountered, log it
                    if self.log_failures:
                        logdbg("Failed attempt %d to send command '%s': %s" % (attempt + 1, cmd, e))
                else:
                    # check the response is valid
                    try:
                        self.check_response(response, self.commands[cmd])
                    except InvalidChecksum as e:
                        # the response was not valid, log it and attempt again
                        # if we haven't had too many attempts already
                        logdbg("Invalid response to attempt %d "
                               "to send command '%s': %s" % (attempt + 1, cmd, e))
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
                        logerr("Unexpected exception occurred while checking response "
                               "to attempt %d to send command '%s': %s" % (attempt + 1, cmd, e))
                        log_traceback_error('    ****  ')
                    else:
                        # our response is valid so return it
                        return response
                # sleep before our next attempt, but skip the sleep if we
                # have just made our last attempt
                if attempt < self.max_tries - 1:
                    time.sleep(self.retry_wait)
            # if we made it here we failed after self.max_tries attempts
            # first log it
            _msg = ("Failed to obtain response to command '%s' "
                    "after %d attempts" % (cmd, attempt + 1))
            if response is not None or self.log_failures:
                logerr(_msg)
            # then finally, raise a GWIOError exception
            raise GWIOError(_msg)

        def build_cmd_packet(self, cmd, payload=b''):
            """Construct an API command packet.

            An API command packet looks like:

            fixed header, command, size, data 1, data 2...data n, checksum

            where:
                fixed header is 2 bytes = 0xFFFF
                command is a 1 byte API command code
                size is 1 byte being the number of bytes of command to checksum
                data 1, data 2 ... data n is the data being transmitted and is
                    n bytes long
                checksum is a byte checksum of command + size + data 1 +
                    data 2 ... + data n

            cmd:     A string containing a valid API command,
                       eg: 'CMD_READ_FIRMWARE_VERSION'
            payload: The data to be sent with the API command, byte string.

            Returns an API command packet as a bytestring.
            """

            # calculate size
            try:
                size = len(self.commands[cmd]) + 1 + len(payload) + 1
            except KeyError:
                raise UnknownApiCommand("Unknown API command '%s'" % (cmd,))
            # construct the portion of the message for which the checksum is calculated
            body = b''.join([self.commands[cmd], struct.pack('B', size), payload])
            # calculate the checksum
            checksum = self.calc_checksum(body)
            # return the constructed message packet
            return b''.join([self.header, body, struct.pack('B', checksum)])

        def send_cmd(self, packet):
            """Send a command to the API and return the response.

            Send a command to the and return the response. Socket related
            errors are trapped and raised, code calling send_cmd should be
            prepared to handle such exceptions.

            cmd: A valid API command

            Returns the response as a byte string.
            """

            # create a socket object for sending commands and broadcasting to
            # the network, would normally do this using a with statement but
            # with statement support for socket.socket did not appear until
            # python 3.
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # set the socket timeout
            s.settimeout(self.socket_timeout)
            # wrap our connect in a try..except, so we can catch any socket
            # related exceptions
            try:
                # connect to the device
                s.connect((self.ip_address, self.port))
                # if required log the packet we are sending
                if weewx.debug >= 3:
                    logdbg("Sending packet '%s' to %s:%d" % (bytes_to_hex(packet),
                                                             self.ip_address.decode(),
                                                             self.port))
                # send the packet
                s.sendall(packet)
                # obtain the response, we assume here the response will be less
                # than 1024 characters
                response = s.recv(1024)
                # if required log the response
                if weewx.debug >= 3:
                    logdbg("Received response '%s'" % (bytes_to_hex(response),))
                # return the response
                return response
            except socket.error:
                # we received a socket error, raise it
                raise
            finally:
                # make sure we close our socket
                s.close()

        def check_response(self, response, cmd_code):
            """Check the validity of an API response.

            Checks the validity of an API response. Two checks are performed:

            1.  the third byte of the response is the same as the command code
                used in the API call
            2.  the calculated checksum of the data in the response matches the
                checksum byte in the response

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
            resp_checksum = six.indexbytes(response, -1)
            if calc_checksum == resp_checksum:
                # checksum check passed, now check the response command code by
                # checkin the 3rd byte of the response matches the command code
                # that was issued
                if six.indexbytes(response, 2) == six.byte2int(cmd_code):
                    # we have a valid command code in the response, so the
                    # response is valid and all we need do is return
                    return
                else:
                    # command code check failed, since we have a valid checksum
                    # this is most likely due to the device not understanding
                    # the command, possibly due to an old or outdated firmware
                    # version. Raise an UnknownApiCommand exception.
                    exp_int = six.byte2int(cmd_code)
                    resp_int = six.indexbytes(response, 2)
                    _msg = "Unknown command code in API response. " \
                           "Expected '%s' (0x%s), received '%s' (0x%s)." % (exp_int,
                                                                            "{:02X}".format(exp_int),
                                                                            resp_int,
                                                                            "{:02X}".format(resp_int))
                    raise UnknownApiCommand(_msg)
            else:
                # checksum check failed, raise an InvalidChecksum exception
                _msg = "Invalid checksum in API response. " \
                       "Expected '%s' (0x%s), received '%s' (0x%s)." % (calc_checksum,
                                                                        "{:02X}".format(calc_checksum),
                                                                        resp_checksum,
                                                                        "{:02X}".format(resp_checksum))
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
            for b in six.iterbytes(data):
                # add the byte to the running total
                checksum += b
            # we are only interested in the least significant byte
            return checksum % 256

        def rediscover(self):
            """Attempt to rediscover a lost device.

            Use UDP broadcast to discover a device that may have changed to a
            new IP or contact has otherwise been lost. We should not be
            re-discovering a device for which the user specified an IP, only
            for those for which we discovered the IP address on startup. If a
            device is discovered then change my ip_address and port properties
            as necessary to use the device in the future. If the rediscovery
            was successful return True otherwise return False.
            """

            # we will only rediscover if we first discovered
            if self.ip_discovered:
                # log that we are attempting re-discovery
                if self.log_failures:
                    loginf("Attempting to re-discover %s..." % self.model)
                # attempt to discover up to self.max_tries times
                for attempt in range(self.max_tries):
                    # sleep before our attempt, but not if it's the first one
                    if attempt > 0:
                        time.sleep(self.retry_wait)
                    try:
                        # discover devices on the local network, the result is
                        # a list of dicts in IP address order with each dict
                        # containing data for a unique discovered device
                        device_list = self.discover()
                    except socket.error as e:
                        # log the error
                        logdbg("Failed attempt %d to detect any devices: %s (%s)" % (attempt + 1,
                                                                                     e,
                                                                                     type(e)))
                    else:
                        # did we find any devices
                        if len(device_list) > 0:
                            # we have at least one, log the fact as well as what we found
                            gw1000_str = ', '.join([':'.join(['%s:%d' % (d['ip_address'],
                                                                         d['port'])]) for d in device_list])
                            if len(device_list) == 1:
                                stem = "%s was" % device_list[0]['model']
                            else:
                                stem = "Multiple devices were"
                            loginf("%s found at %s" % (stem, gw1000_str))
                            # iterate over each candidate checking their MAC
                            # address against my mac property. This way we know
                            # we will be connecting to the device we were
                            # previously using.
                            for device in device_list:
                                # do the MACs match, if so we have our old
                                # device and we can exit the loop
                                if self.mac == device['mac']:
                                    self.ip_address = device['ip_address'].encode()
                                    self.port = device['port']
                                    break
                            else:
                                # we have exhausted the device list without a
                                # match so continue the outer loop if we have
                                # any attempts left
                                continue
                            # log the new IP address and port
                            loginf("%s at address %s:%d will be used" % (self.model,
                                                                         self.ip_address.decode(),
                                                                         self.port))
                            # return True indicating the re-discovery was
                            # successful
                            return True
                        else:
                            # did not discover any devices so log it
                            if self.log_failures:
                                logdbg("Failed attempt %d to detect any devices" % (attempt + 1,))
                else:
                    # we exhausted our attempts at re-discovery so log it
                    if self.log_failures:
                        loginf("Failed to detect original %s after %d attempts" % (self.model,
                                                                                   attempt + 1))
            else:
                # an IP address was specified so we cannot go searching, log it
                if self.log_failures:
                    logdbg("IP address specified in 'weewx.conf', "
                           "re-discovery was not attempted")
            # if we made it here re-discovery was unsuccessful so return False
            return False

    class Parser(object):
        """Class to parse and decode device API response payload data.

        The main function of class Parser is to parse and decode the payloads
        of the device response to the following API calls:

        - CMD_GW1000_LIVEDATA
        - CMD_READ_RAIN

        By virtue of its ability to decode fields in the above API responses
        the decode methods of class Parser are also used individually
        elsewhere in the driver to decode simple responses received from the
        device, eg when reading device configuration settings.
        """

        # Dictionary of 'address' based data. Dictionary is keyed by device
        # data field 'address' containing various parameters for each
        # 'address'. Dictionary tuple format is:
        #   (decode fn, size, field name)
        # where:
        #   decode fn:  the decode function name to be used for the field
        #   size:       the size of field data in bytes
        #   field name: the name of the device field to be used for the decoded
        #               data
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
            # WN34 battery data is not obtained from live data rather it is
            # obtained from sensor ID data
            b'\x63': ('decode_wn34', 3, 'temp9'),
            b'\x64': ('decode_wn34', 3, 'temp10'),
            b'\x65': ('decode_wn34', 3, 'temp11'),
            b'\x66': ('decode_wn34', 3, 'temp12'),
            b'\x67': ('decode_wn34', 3, 'temp13'),
            b'\x68': ('decode_wn34', 3, 'temp14'),
            b'\x69': ('decode_wn34', 3, 'temp15'),
            b'\x6A': ('decode_wn34', 3, 'temp16'),
            # WH45 battery data is not obtained from live data rather it is
            # obtained from sensor ID data
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
        rain_data_struct = {
            b'\x0D': ('decode_rain', 2, 't_rainevent'),
            b'\x0E': ('decode_rainrate', 2, 't_rainrate'),
            b'\x0F': ('decode_rain', 2, 't_raingain'),
            b'\x10': ('decode_big_rain', 4, 't_rainday'),
            b'\x11': ('decode_big_rain', 4, 't_rainweek'),
            b'\x12': ('decode_big_rain', 4, 't_rainmonth'),
            b'\x13': ('decode_big_rain', 4, 't_rainyear'),
            # undocumented field 0x7A, believed to be rain source selection
            b'\x7A': ('decode_int', 1, 'rain_priority'),
            b'\x80': ('decode_rainrate', 2, 'p_rainrate'),
            b'\x81': ('decode_rain', 2, 'p_rainevent'),
            b'\x82': ('decode_reserved', 2, 'p_rainhour'),
            b'\x83': ('decode_big_rain', 4, 'p_rainday'),
            b'\x84': ('decode_big_rain', 4, 'p_rainweek'),
            b'\x85': ('decode_big_rain', 4, 'p_rainmonth'),
            b'\x86': ('decode_big_rain', 4, 'p_rainyear'),
            # field 0x87 and 0x88 hold device parameter data that is not
            # included in the loop packets, hence the device field is not
            # used (None).
            b'\x87': ('decode_rain_gain', 20, None),
            b'\x88': ('decode_rain_reset', 3, None)
        }
        # tuple of field codes for device rain related fields in the live data
        # so we can isolate these fields
        rain_field_codes = (b'\x0D', b'\x0E', b'\x0F', b'\x10',
                            b'\x11', b'\x12', b'\x13', b'\x14',
                            b'\x80', b'\x81', b'\x83', b'\x84',
                            b'\x85', b'\x86')
        # tuple of field codes for wind related fields in the device live data
        # so we can isolate these fields
        wind_field_codes = (b'\x0A', b'\x0B', b'\x0C', b'\x19')

        def __init__(self, log_unknown_fields=True, debug_rain=False, debug_wind=False):
            # do we log unknown fields at info or leave at debug
            self.log_unknown_fields = log_unknown_fields
            # get debug_rain and debug_wind
            self.debug_rain = debug_rain
            self.debug_wind = debug_wind

        def parse_addressed_data(self, payload, structure):
            """Parse an address structure API response payload.

            Parses the data payload of an API response that uses an addressed
            data structure, ie each data element is in the format

            <address byte> <data byte(s)>

            Data elements may be in any order and the data portion of each data
            element may consist of one or mor bytes.

            payload:   API response payload to be parsed, bytestring
            structure: dict keyed by data element address and containing the
                       decode function, field size and the field name to be
                       used as the key against which the decoded data is to be
                       stored in the result dict

            Returns a dict of decoded data keyed by destination field name
            """

            # initialise a dict to hold our parsed data
            data = dict()
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
                        decode_fn_str, field_size, field = structure[payload[index:index + 1]]
                    except KeyError:
                        # We struck a field 'address' we do not know how to
                        # process. We can't skip to the next field so all we
                        # can really do is accept the data we have so far, log
                        # the issue and ignore the remaining data.
                        # are we logging as info or debug, get an appropriate log function
                        if self.log_unknown_fields:
                            log_fn = loginf
                        else:
                            log_fn = logdbg
                        # now call it
                        log_fn("Unknown field address '%s' detected. "
                               "Remaining data '%s' ignored." % (bytes_to_hex(payload[index:index + 1]),
                                                                 bytes_to_hex(payload[index + 1:])))
                        # and break, there is nothing more we can with this
                        # data
                        break
                    else:
                        _field_data = getattr(self, decode_fn_str)(payload[index + 1:index + 1 + field_size],
                                                                   field)
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

        def parse_livedata(self, response):
            """Parse data from a CMD_GW1000_LIVEDATA API response.

            Parse the raw sensor data obtained from the CMD_GW1000_LIVEDATA API
            command and create a dict of sensor observations/status data.

            Returns a dict of observations/status data.

            Response consists of a variable number of bytes determined by the
            number of connected sensors. Decode as follows:
            Byte(s)     Data            Format          Comments
            1-2         header          -               fixed header 0xFFFF
            3           command code    byte            0x27
            4-5         size            unsigned short
            ....
            6-2nd last byte
                    data structure follows the structure of
                    Parser.live_data_struct in the format:
                        address (byte)
                        data    length: as per second element of tuple
                                decode: Parser method as per first element of
                                        tuple
            ....
            last byte   checksum        byte            LSB of the sum of the
                                                        command, size and data
                                                        bytes
            """

            # obtain the payload size, it's a big endian short (two byte) integer
            payload_size = struct.unpack(">H", response[3:5])[0]
            # obtain the payload
            payload = response[5:5 + payload_size - 4]
            # this is addressed data, so we can call parse_addressed_data() and
            # return the result
            return self.parse_addressed_data(payload, self.live_data_struct)

        def parse_read_rain(self, response):
            """Parse data from a CMD_READ_RAIN API response.

            Parse the raw sensor data obtained from the CMD_READ_RAIN API
            command and create a dict of sensor observations/status data.

            Returns a dict of observations/status data.

            Response consists of a variable number of bytes determined by the
            connected sensors. Decode as follows:
            Byte(s)     Data            Format          Comments
            1-2         header          -               fixed header 0xFFFF
            3           command code    byte            0x57
            4-5         size            unsigned short
            ....
            6-2nd last byte
                    data structure follows the structure of
                    Parser.rain_data_struct in the format:
                        address (byte)
                        data    length: as per second element of tuple
                                decode: Parser method as per first element of
                                        tuple
            ....
            last byte   checksum        byte            LSB of the sum of the
                                                        command, size and data
                                                        bytes
            """

            # obtain the payload size, it's a big endian short (two byte) integer
            payload_size = struct.unpack(">H", response[3:5])[0]
            # obtain the payload
            payload = response[5:5 + payload_size - 4]
            # this is addressed data, so we can call parse_addressed_data() and
            # return the result
            return self.parse_addressed_data(payload, self.rain_data_struct)

        def parse_read_raindata(self, response):
            """Parse data from a CMD_READ_RAINDATA API response.

            Response consists of 25 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x2C
            4       size            byte
            5-8     rainrate        unsigned long   0 to 60000 in tenths mm/hr
                                                    0 to 6000.0
            9-12    rainday         unsigned long   0 to 99999 in tenths mm
                                                    0 to 9999.9
            13-16   rainweek        unsigned long   0 to 99999 in tenths mm
                                                    0 to 9999.9
            17-20   rainmonth       unsigned long   0 to 99999 in tenths mm
                                                    0 to 9999.9
            21-24   rainyear        unsigned long   0 to 99999 in tenths mm
                                                    0 to 9999.9
            25      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the rain data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our parsed data
            data_dict = dict()
            data_dict['t_rainrate'] = self.decode_big_rain(data[0:4])
            data_dict['t_rainday'] = self.decode_big_rain(data[4:8])
            data_dict['t_rainweek'] = self.decode_big_rain(data[8:12])
            data_dict['t_rainmonth'] = self.decode_big_rain(data[12:16])
            data_dict['t_rainyear'] = self.decode_big_rain(data[16:20])
            return data_dict

        @staticmethod
        def parse_get_mulch_offset(response):
            """Parse data from a CMD_GET_MulCH_OFFSET API response.

            Response consists of 29 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x2C
            4       size            byte
            5       channel 1       byte            fixed 00
            6       hum offset      signed byte     -10 to +10
            7       temp offset     signed byte     -100 to +100 in tenths C
                                                    (-10.0 to +10.0)
            8       channel 2       byte            fixed 01
            9       hum offset      signed byte     -10 to +10
            10      temp offset     signed byte     -100 to +100 in tenths C
                                                    (-10.0 to +10.0)
            ....
            26      channel 8       byte            fixed 07
            27      hum offset      signed byte     -10 to +10
            28      temp offset     signed byte     -100 to +100 in tenths C
                                                    (-10.0 to +10.0)
            29      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the mulch offset data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a counter
            index = 0
            # initialise a dict to hold our parsed data
            offset_dict = {}
            # iterate over the data
            while index < len(data):
                try:
                    channel = six.byte2int(data[index])
                except TypeError:
                    channel = data[index]
                offset_dict[channel] = {}
                try:
                    offset_dict[channel]['hum'] = struct.unpack("b", data[index + 1])[0]
                except TypeError:
                    offset_dict[channel]['hum'] = struct.unpack("b", six.int2byte(data[index + 1]))[0]
                try:
                    offset_dict[channel]['temp'] = struct.unpack("b", data[index + 2])[0] / 10.0
                except TypeError:
                    offset_dict[channel]['temp'] = struct.unpack("b", six.int2byte(data[index + 2]))[0] / 10.0
                index += 3
            return offset_dict

        @staticmethod
        def parse_get_mulch_t_offset(response):
            """Parse data from a CMD_GET_MulCH_T_OFFSET API response.

            Response consists of a variable number of bytes determined by the
            connected sensors. Decode as follows:
            Byte(s)     Data            Format          Comments
            1-2         header          -               fixed header 0xFFFF
            3           command code    byte            0x59
            4-5         size            unsigned short
            ....
            6-2nd last byte
                two bytes per connected WN34 sensor:
                        address         byte            sensor address, 0x63 to
                                                        0x6A incl
                        temp offset     signed byte     -100 to +100 in tenths C
                                                        (-10.0 to +10.0)
            ....
            last byte   checksum        byte            LSB of the sum of the
                                                        command, size and data
                                                        bytes
            """

            # obtain the payload size, it's a big endian short (two byte) integer
            size = struct.unpack(">H", response[3:5])[0]
            # extract the actual data
            data = response[5:5 + size - 4]
            # initialise a counter
            index = 0
            # initialise a dict to hold our parsed data
            offset_dict = {}
            # iterate over the data
            while index < len(data):
                try:
                    channel = six.byte2int(data[index])
                except TypeError:
                    channel = data[index]
                try:
                    offset_dict[channel] = struct.unpack("b", data[index + 1])[0] / 10.0
                except TypeError:
                    offset_dict[channel] = struct.unpack("b", six.int2byte(data[index + 1]))[0] / 10.0
                index += 2
            return offset_dict

        @staticmethod
        def parse_get_pm25_offset(response):
            """Parse data from a CMD_GET_PM25_OFFSET API response.

            Response consists of 17 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x2E
            4       size            byte
            5       channel 1       byte            fixed 00
            6-7     pm25 offset     signed short    -200 to +200 in tenths µg/m³
                                                    (-20.0 to +20.0)
            ....
            14      channel 1       byte            fixed 00
            15-16   pm25 offset     signed short    -200 to +200 in tenths µg/m³
                                                   (-20.0 to +20.0)
            17      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the PM2.5 offset data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a counter
            index = 0
            # initialise a dict to hold our parsed data
            offset_dict = {}
            # iterate over the data
            while index < len(data):
                try:
                    channel = six.byte2int(data[index])
                except TypeError:
                    channel = data[index]
                offset_dict[channel] = struct.unpack(">h", data[index + 1:index + 3])[0] / 10.0
                index += 3
            return offset_dict

        @staticmethod
        def parse_get_co2_offset(response):
            """Parse data from a CMD_GET_CO2_OFFSET API response.

            Response consists of 11 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x53
            4       size            byte
            5-6     co2 offset      signed short    -600 to +10000 in tenths µg/m³
            7-8     pm25 offset     signed short    -200 to +200 in tenths µg/m³
                                                   (-20.0 to +20.0)
            9-10    pm10 offset     signed short    -200 to +200 in tenths µg/m³
                                                   (-20.0 to +20.0)
            17      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the WH45 offset data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our parsed data
            offset_dict = dict()
            # and decode/store the offset data
            # bytes 0 and 1 hold the CO2 offset
            offset_dict['co2'] = struct.unpack(">h", data[0:2])[0]
            # bytes 2 and 3 hold the PM2.5 offset
            offset_dict['pm25'] = struct.unpack(">h", data[2:4])[0] / 10.0
            # bytes 4 and 5 hold the PM10 offset
            offset_dict['pm10'] = struct.unpack(">h", data[4:6])[0] / 10.0
            return offset_dict

        @staticmethod
        def parse_read_gain(response):
            """Parse a CMD_READ_GAIN API response.

            Response consists of 17 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x36
            4       size            byte
            5-6     fixed           short           fixed value 1267
            7-8     uvGain          unsigned short  10 to 500 in hundredths
                                                    (0.10 to 5.00)
            9-10    solarRadGain    unsigned short  10 to 500 in hundredths
                                                    (0.10 to 5.00)
            11-12   windGain        unsigned short  10 to 500 in hundredths
                                                    (0.10 to 5.00)
            13-14   rainGain        unsigned short  10 to 500 in hundredths
                                                    (0.10 to 5.00)
            15-16   reserved                        reserved
            17      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the calibration data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our parsed data
            gain_dict = dict()
            # and decode/store the calibration data
            # bytes 0 and 1 are reserved (lux to solar radiation conversion
            # gain (126.7))
            gain_dict['uv'] = struct.unpack(">H", data[2:4])[0] / 100.0
            gain_dict['solar'] = struct.unpack(">H", data[4:6])[0] / 100.0
            gain_dict['wind'] = struct.unpack(">H", data[6:8])[0] / 100.0
            gain_dict['rain'] = struct.unpack(">H", data[8:10])[0] / 100.0
            # return the parsed response
            return gain_dict

        @staticmethod
        def parse_read_calibration(response):
            """Parse a CMD_READ_CALIBRATION API response.

            Response consists of 21 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x38
            4       size            byte
            5-6     intemp offset   signed short    -100 to +100 in tenths C
                                                    (-10.0 to +10.0)
            7       inhum offset    signed byte     -10 to +10 %
            8-11    abs offset      signed long     -800 to +800 in tenths hPa
                                                    (-80.0 to +80.0)
            12-15   rel offset      signed long     -800 to +800 in tenths hPa
                                                    (-80.0 to +80.0)
            16-17   outtemp offset  signed short    -100 to +100 in tenths C
                                                    (-10.0 to +10.0)
            18      outhum offset   signed byte     -10 to +10 %
            19-20   wind dir offset signed short    -180 to +180 degrees
            21      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the calibration data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our parsed data
            cal_dict = dict()
            # and decode/store the offset calibration data
            cal_dict['intemp'] = struct.unpack(">h", data[0:2])[0] / 10.0
            try:
                cal_dict['inhum'] = struct.unpack("b", data[2])[0]
            except TypeError:
                cal_dict['inhum'] = struct.unpack("b", six.int2byte(data[2]))[0]
            cal_dict['abs'] = struct.unpack(">l", data[3:7])[0] / 10.0
            cal_dict['rel'] = struct.unpack(">l", data[7:11])[0] / 10.0
            cal_dict['outtemp'] = struct.unpack(">h", data[11:13])[0] / 10.0
            try:
                cal_dict['outhum'] = struct.unpack("b", data[13])[0]
            except TypeError:
                cal_dict['outhum'] = struct.unpack("b", six.int2byte(data[13]))[0]
            cal_dict['dir'] = struct.unpack(">h", data[14:16])[0]
            # return the parsed response
            return cal_dict

        @staticmethod
        def parse_get_soilhumiad(response):
            """Parse a CMD_GET_SOILHUMIAD API response.

            Response consists of a variable number of bytes determined by the
            number of WH51 soil moisture sensors. Number of bytes = 5 + (n x 9)
            where n is the number of connected WH51 sensors. Decode as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x29
            4       size            byte
            5       channel         byte            channel number (0 to 8)
            6       current hum     byte            from sensor
            7-8     current ad      unsigned short  from sensor
            9       custom cal      byte            0 = sensor, 1 = enabled
            10      min ad          unsigned byte   0% ad setting (70 to 200)
            11-12   max ad          unsigned short  100% ad setting (80 to 1000)
            ....
            structure of bytes 5 to 12 incl repeated for each WH51 sensor
            ....
            21      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the calibration data
            size = six.indexbytes(response, 3)
            # extract the actual data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            cal_dict = {}
            # initialise a counter
            index = 0
            # iterate over the data
            while index < len(data):
                try:
                    channel = six.byte2int(data[index])
                except TypeError:
                    channel = data[index]
                cal_dict[channel] = {}
                try:
                    humidity = six.byte2int(data[index + 1])
                except TypeError:
                    humidity = data[index + 1]
                cal_dict[channel]['humidity'] = humidity
                cal_dict[channel]['ad'] = struct.unpack(">h", data[index + 2:index + 4])[0]
                try:
                    ad_select = six.byte2int(data[index + 4])
                except TypeError:
                    ad_select = data[index + 4]
                # get 'Customize' setting 1 = enable, 0 = customised
                cal_dict[channel]['ad_select'] = ad_select
                try:
                    min_ad = six.byte2int(data[index + 5])
                except TypeError:
                    min_ad = data[index + 5]
                cal_dict[channel]['adj_min'] = min_ad
                cal_dict[channel]['adj_max'] = struct.unpack(">h", data[index + 6:index + 8])[0]
                index += 8
            # return the parsed response
            return cal_dict

        def parse_read_ssss(self, response):
            """Parse a CMD_READ_SSSS API response.

            Response consists of 13 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x30
            4       size            byte
            5       frequency       byte            0=433, 1=868, 2=915, 3=920
            6       sensor type     byte            0=WH24, 1=WH65
            7-10    utc time        unsigned long
            11      timezone index  byte
            12      dst status      byte            0=False, 1=True
            13      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the system parameters data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            data_dict['frequency'] = six.indexbytes(data, 0)
            data_dict['sensor_type'] = six.indexbytes(data, 1)
            data_dict['utc'] = self.decode_utc(data[2:6])
            data_dict['timezone_index'] = six.indexbytes(data, 6)
            data_dict['dst_status'] = six.indexbytes(data, 7) != 0
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_ecowitt(response):
            """Parse a CMD_READ_ECOWITT API response.

            Response consists of six bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x1E
            4       size            byte
            5       upload interval byte            1-5 minutes, 0=off
            6       checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the system parameters data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            data_dict['interval'] = six.indexbytes(data, 0)
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_wunderground(response):
            """Parse a CMD_READ_WUNDERGROUND API response.

            Response consists of a variable number of bytes. Number of
            bytes = 8 + i + p where i = length of the Wunderground ID in
            characters and p is the length of the Wunderground password in
            characters. Decode as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x20
            4       size            byte
            5       ID size         unsigned byte   length of Wunderground ID
                                                    in characters
            6-6+i   ID              i x bytes       ASCII, max 32 characters
            7+i     password size   unsigned byte   length of Wunderground
                                                    password in characters
            8+i-    password        p x bytes       ASCII, max 32 characters
            8+i+p
            9+i+p   fixed           1               fixed value 1
            10+i+p  checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the system parameters data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            # obtain the required data from the response decoding any bytestrings
            id_size = six.indexbytes(data, 0)
            data_dict['id'] = data[1:1 + id_size].decode()
            password_size = six.indexbytes(data, 1 + id_size)
            data_dict['password'] = data[2 + id_size:2 + id_size + password_size].decode()
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_wow(response):
            """Parse a CMD_READ_WOW API response.

            Response consists of a variable number of bytes. Number of
            bytes = 9 + i + p + s where i = length of the WOW ID in characters,
            p is the length of the WOW password in characters and s is the
            length of the WOW station number in characters. Decode as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x22
            4       size            byte
            5       ID size         unsigned byte   length of WOW ID in
                                                    characters
            6-6+i   ID              i x bytes       ASCII, max 39 characters
            7+i     password size   unsigned byte   length of WOW password in
                                                    characters
            8+i-    password        p x bytes       ASCII, max 32 characters
            8+i+p
            9+i+p   station num     unsigned byte   length of WOW station num
                    size                            (unused)
            10+i+p- station num     s x bytes       ASCII, max 32 characters
            10+i+p+s                                (unused)
            11+i+p+s fixed          1               fixed value 1
            12+i+p+s checksum       byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the system parameters data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            # obtain the required data from the response decoding any bytestrings
            id_size = six.indexbytes(data, 0)
            data_dict['id'] = data[1:1 + id_size].decode()
            pw_size = six.indexbytes(data, 1 + id_size)
            data_dict['password'] = data[2 + id_size:2 + id_size + pw_size].decode()
            stn_num_size = six.indexbytes(data, 1 + id_size)
            data_dict['station_num'] = data[3 + id_size + pw_size:3 + id_size + pw_size + stn_num_size].decode()
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_weathercloud(response):
            """Parse a CMD_READ_WEATHERCLOUD API response.

            Response consists of a variable number of bytes. Number of
            bytes = 8 + i + k where i = length of the Weathercloud ID in
            characters and p is the length of the Weathercloud key in
            characters. Decode as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x24
            4       size            byte
            5       ID size         unsigned byte   length of Weathercloud ID
                                                    in characters
            6-6+i   ID              i x bytes       ASCII, max 32 characters
            7+i     key size        unsigned byte   length of Weathercloud key
                                                    in characters
            8+i-    key             k x bytes       ASCII, max 32 characters
            8+i+k
            9+i+k   fixed           1               fixed value 1
            10+i+k  checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # determine the size of the system parameters data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            # obtain the required data from the response decoding any bytestrings
            id_size = six.indexbytes(data, 0)
            data_dict['id'] = data[1:1 + id_size].decode()
            key_size = six.indexbytes(data, 1 + id_size)
            data_dict['key'] = data[2 + id_size:2 + id_size + key_size].decode()
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_customized(response):
            """Parse a CMD_READ_CUSTOMIZED API response.

            Response consists of a variable number of bytes. Number of
            bytes = 14 + i + p + s where i = length of the ID in characters,
            p is the length of the password in characters and s is the length
            of the server address in characters. Decode as follows:
            Byte(s)   Data            Format          Comments
            1-2       header          -               fixed header 0xFFFF
            3         command code    byte            0x2A
            4         size            byte
            5         ID size         unsigned byte   length of ID in characters
            6-5+i     ID              i x bytes       ASCII, max 40 characters
            6+i       password size   unsigned byte   length of password in
                                                      characters
            7+i-      password        p x bytes       ASCII, max 40 characters
            6+i+p
            7+i+p     server address  unsigned byte   length of server address in
                      size                            characters
            8+i+p-    server address  s x bytes       ASCII, max 64 characters
            7+i+p+s
            8+i+p+s-  port number     unsigned short  0 to 65535
            9+i+p+s
            10+i+p+s- interval        unsigned short  16 to 600 seconds
            11+i+p+s
            12+i+p+s  type            byte            0 = Ecowitt, 1 = WU
            13+i+p+s  active          byte            0 = disable, 1 = enable
            14+i+p+s  checksum        byte            LSB of the sum of the
                                                      command, size and data
                                                      bytes
            """

            # determine the size of the system parameters data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            # obtain the required data from the response decoding any bytestrings
            index = 0
            id_size = six.indexbytes(data, index)
            index += 1
            data_dict['id'] = data[index:index + id_size].decode()
            index += id_size
            password_size = six.indexbytes(data, index)
            index += 1
            data_dict['password'] = data[index:index + password_size].decode()
            index += password_size
            server_size = six.indexbytes(data, index)
            index += 1
            data_dict['server'] = data[index:index + server_size].decode()
            index += server_size
            data_dict['port'] = struct.unpack(">h", data[index:index + 2])[0]
            index += 2
            data_dict['interval'] = struct.unpack(">h", data[index:index + 2])[0]
            index += 2
            data_dict['type'] = six.indexbytes(data, index)
            index += 1
            data_dict['active'] = six.indexbytes(data, index)
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_usr_path(response):
            """Parse a CMD_READ_USR_PATH API response.

            Response consists of a variable number of bytes. Number of
            bytes = 7 + e + w where e = length of the 'Ecowitt path' in
            characters and w is the length of the 'Weather Underground path'.
            Decode as follows:
            Byte(s)     Data            Format          Comments
            1-2         header          -               fixed header 0xFFFF
            3           command code    byte            0x51
            4           size            byte
            5           Ecowitt size    unsigned byte   length of Ecowitt path
                                                        in characters
            6-5+e       Ecowitt path    e x bytes       ASCII, max 64 characters
            6+e         WU size         unsigned byte   length of WU path in
                                                        characters
            7+e-6+e+w   WU path         w x bytes       ASCII, max 64 characters
            7+e+w       checksum        byte            LSB of the sum of the
                                                        command, size and data
                                                        bytes
            """

            # determine the size of the user path data
            size = six.indexbytes(response, 3)
            # extract the actual system parameters data
            data = response[4:4 + size - 3]
            # initialise a dict to hold our final data
            data_dict = dict()
            index = 0
            ecowitt_size = six.indexbytes(data, index)
            index += 1
            data_dict['ecowitt_path'] = data[index:index + ecowitt_size].decode()
            index += ecowitt_size
            wu_size = six.indexbytes(data, index)
            index += 1
            data_dict['wu_path'] = data[index:index + wu_size].decode()
            # return the parsed response
            return data_dict

        @staticmethod
        def parse_read_station_mac(response):
            """Parse a CMD_READ_STATION_MAC API response.

            Response consists of 11 bytes as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x26
            4       size            byte
            5-12    station MAC     6 x byte
            13      checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # return the parsed response, in this case we simply return the
            # bytes as a semicolon separated hex string
            return bytes_to_hex(response[4:10], separator=":")

        @staticmethod
        def parse_read_firmware_version(response):
            """Parse a CMD_READ_FIRMWARE_VERSION API response.

            Response consists of a variable number of bytes. Number of
            bytes = 6 + f where f = length of the firmware version string in
            characters. Decode as follows:
            Byte(s) Data            Format          Comments
            1-2     header          -               fixed header 0xFFFF
            3       command code    byte            0x50
            4       size            byte
            5       fw size         byte            length of firmware version
                                                    string in characters
            6-5+f   fw string       f x byte        firmware version string
                                                    (ASCII ?)
            6+f     checksum        byte            LSB of the sum of the
                                                    command, size and data
                                                    bytes
            """

            # create a format string so the firmware string can be unpacked into
            # its bytes
            firmware_format = "B" * len(response)
            # unpack the firmware response bytestring, we now have a tuple of
            # integers representing each of the bytes
            firmware_t = struct.unpack(firmware_format, response)
            # get the length of the firmware string, it is in byte 4
            str_length = firmware_t[4]
            # the firmware string starts at byte 5 and is str_length bytes long,
            # convert the sequence of bytes to unicode characters and assemble as a
            # string and return the result
            return ''.join([chr(x) for x in firmware_t[5:5 + str_length]])

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
            else:
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
            else:
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
            else:
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
            else:
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
            else:
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
            else:
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
            else:
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
            else:
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
            else:
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
            else:
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
                results = dict()
                results[field] = self.decode_temp(data[0:2])
                # we could decode the battery voltage but we will be obtaining
                # battery voltage data from the sensor IDs in a later step so
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
                    6-7    PM10 24hour avg    unsigned short  ug/m3 x10
                    8-9    PM2.5              unsigned short  ug/m3 x10
                    10-11  PM2.5 24 hour avg  unsigned short  ug/m3 x10
                    12-13  CO2                unsigned short  ppm
                    14-15  CO2 24 our avg     unsigned short  ppm
                    16     battery state      unsigned byte   0-5 <=1 is low

            WH45 battery state data is included in the WH45 sensor data (along
            with temperature) as well as in the complete sensor ID data. In
            keeping with other sensors we do not use the sensor data battery
            state, rather we obtain it from the sensor ID data.
            """

            if len(data) == 16 and fields is not None:
                results = dict()
                results[fields[0]] = self.decode_temp(data[0:2])
                results[fields[1]] = self.decode_humid(data[2:3])
                results[fields[2]] = self.decode_pm10(data[3:5])
                results[fields[3]] = self.decode_pm10(data[5:7])
                results[fields[4]] = self.decode_pm25(data[7:9])
                results[fields[5]] = self.decode_pm25(data[9:11])
                results[fields[6]] = self.decode_co2(data[11:13])
                results[fields[7]] = self.decode_co2(data[13:15])
                # we could decode the battery state but we will be obtaining
                # battery state data from the sensor IDs in a later step so
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
                results = dict()
                for gain in range(10):
                    results['gain%d' % gain] = self.decode_gain_100(data[gain * 2:gain * 2 + 2])
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
                results = dict()
                results['day_reset'] = struct.unpack("B", data[0:1])[0]
                results['week_reset'] = struct.unpack("B", data[1:2])[0]
                results['annual_reset'] = struct.unpack("B", data[2:3])[0]
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

    class Sensors(object):
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

        # Tuple of sensor ID values for sensors that are not registered with
        # the device. 'fffffffe' means the sensor is disabled, 'ffffffff' means
        # the sensor is registering.
        not_registered = ('fffffffe', 'ffffffff')

        def __init__(self, sensor_id_data=None, ignore_wh40_batt=True,
                     show_battery=False, debug_sensors=False):
            """Initialise myself"""

            # do we ignore battery state data from legacy WH40 sensors that do
            # not provide valid battery state data
            self.ignore_wh40_batt = ignore_wh40_batt
            # set the show_battery property
            self.show_battery = show_battery
            # initialise legacy WH40 flag
            self.legacy_wh40 = None
            # initialise a dict to hold the parsed sensor data
            self.sensor_data = dict()
            # parse the raw sensor ID data and store the results in my parsed
            # sensor data dict
            self.set_sensor_id_data(sensor_id_data)
            # debug sensors
            self.debug_sensors = debug_sensors

        def set_sensor_id_data(self, id_data):
            """Parse the raw sensor ID data and store the results.

            id_data: bytestring of sensor ID data

            Tested by SensorsTestCase.test_set_sensor_id_data
            """

            # initialise our parsed sensor ID data dict
            self.sensor_data = {}
            # do we have any raw sensor ID data
            if id_data is not None and len(id_data) > 0:
                # determine the size of the sensor id data, it's a big endian
                # short (two byte) integer at bytes 4 and 5
                data_size = struct.unpack(">H", id_data[3:5])[0]
                # extract the actual sensor id data
                data = id_data[5:5 + data_size - 4]
                # initialise a counter
                index = 0
                # iterate over the data
                while index < len(data):
                    # get the sensor address
                    address = data[index:index + 1]
                    # do we know how to decode this address
                    if address in GatewayCollector.sensor_ids.keys():
                        # get the sensor ID
                        sensor_id = bytes_to_hex(data[index + 1: index + 5],
                                                 separator='',
                                                 caps=False)
                        # get the method to be used to decode the battery state
                        # data
                        batt_fn = GatewayCollector.sensor_ids[data[index:index + 1]]['batt_fn']
                        # get the raw battery state data
                        batt = six.indexbytes(data, index + 5)
                        # if we are not showing all battery state data then the
                        # battery state for any sensor with signal == 0 must be set
                        # to None, otherwise parse the raw battery state data as
                        # applicable
                        if not self.show_battery and six.indexbytes(data, index + 6) == 0:
                            batt_state = None
                        else:
                            # parse the raw battery state data
                            batt_state = getattr(self, batt_fn)(batt)
                        # now add the sensor to our sensor data dict
                        self.sensor_data[address] = {'id': sensor_id,
                                                     'battery': batt_state,
                                                     'signal': six.indexbytes(data, index + 6)
                                                     }
                    else:
                        if self.debug_sensors:
                            loginf("Unknown sensor ID '%s'" % bytes_to_hex(address))
                    # each sensor entry is seven bytes in length so skip to the
                    # start of the next sensor
                    index += 7

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
            connected_list = list()
            # iterate over all sensors
            for address, data in six.iteritems(self.sensor_data):
                # if the sensor ID is neither 'fffffffe' or 'ffffffff' then it
                # must be connected
                if data['id'] not in self.not_registered:
                    connected_list.append(address)
            return connected_list

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
                sensor_name = GatewayCollector.sensor_ids[sensor]['name']
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
                if GatewayCollector.sensor_ids[address].get('name') in GatewayCollector.no_low:
                    # we have a sensor for which no low battery cut-off
                    # data exists
                    return None
                else:
                    batt_fn = GatewayCollector.sensor_ids[address].get('batt_fn')
                    if batt_fn == 'batt_binary':
                        if value == 0:
                            return "OK"
                        elif value == 1:
                            return "low"
                        else:
                            return 'Unknown'
                    elif batt_fn == 'batt_int':
                        if value <= 1:
                            return "low"
                        elif value == 6:
                            return "DC"
                        elif value <= 5:
                            return "OK"
                        else:
                            return 'Unknown'
                    elif batt_fn in ['batt_volt', 'batt_volt_tenth', 'wh40_batt_volt']:
                        if value <= 1.2:
                            return "low"
                        else:
                            return "OK"
            else:
                return 'Unknown'

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
            """Decode a integer battery state.

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
                else:
                    # we are not ignoring the result so return the result
                    return round(0.1 * batt, 1)
            else:
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
    sorted_dict_fields = ["'%s': '%s'" % (k, source_dict[k]) for k in natural_sort_keys(source_dict)]
    # return as a string of comma separated key:value pairs in braces
    return "{%s}" % ", ".join(sorted_dict_fields)


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


# ============================================================================
#                             class DirectGateway
# ============================================================================

class DirectGateway(object):
    """Class to interact with gateway driver when run directly.

    Would normally run a driver directly by calling from main() only, but when
    run directly the gateway driver has many options so pushing the detail into
    its own class/object makes sense. Also simplifies some of the test suite
    routines/calls.

    A DirectGateway object is created with just an optparse options dict and a
    standard WeeWX station dict. Once created the DirectGateway()
    process_options() method is called to process the respective command line
    options.
    """

    # gateway observation group dict, this maps all device 'fields' to a WeeWX
    # unit group
    gateway_obs_group_dict = {
        'intemp': 'group_temperature',
        'outtemp': 'group_temperature',
        'dewpoint': 'group_temperature',
        'windchill': 'group_temperature',
        'heatindex': 'group_temperature',
        'inhumid': 'group_percent',
        'outhumid': 'group_percent',
        'absbarometer': 'group_pressure',
        'relbarometer': 'group_pressure',
        'light': 'group_illuminance',
        'uv': 'group_radiation',
        'uvi': 'group_uv',
        'datetime': 'group_time',
        'temp1': 'group_temperature',
        'temp2': 'group_temperature',
        'temp3': 'group_temperature',
        'temp4': 'group_temperature',
        'temp5': 'group_temperature',
        'temp6': 'group_temperature',
        'temp7': 'group_temperature',
        'temp8': 'group_temperature',
        'temp9': 'group_temperature',
        'temp10': 'group_temperature',
        'temp11': 'group_temperature',
        'temp12': 'group_temperature',
        'temp13': 'group_temperature',
        'temp14': 'group_temperature',
        'temp15': 'group_temperature',
        'temp16': 'group_temperature',
        'temp17': 'group_temperature',
        'humid1': 'group_percent',
        'humid2': 'group_percent',
        'humid3': 'group_percent',
        'humid4': 'group_percent',
        'humid5': 'group_percent',
        'humid6': 'group_percent',
        'humid7': 'group_percent',
        'humid8': 'group_percent',
        'humid17': 'group_percent',
        'pm251': 'group_concentration',
        'pm252': 'group_concentration',
        'pm253': 'group_concentration',
        'pm254': 'group_concentration',
        'pm255': 'group_concentration',
        'pm10': 'group_concentration',
        'co2': 'group_fraction',
        'soiltemp1': 'group_temperature',
        'soilmoist1': 'group_percent',
        'soiltemp2': 'group_temperature',
        'soilmoist2': 'group_percent',
        'soiltemp3': 'group_temperature',
        'soilmoist3': 'group_percent',
        'soiltemp4': 'group_temperature',
        'soilmoist4': 'group_percent',
        'soiltemp5': 'group_temperature',
        'soilmoist5': 'group_percent',
        'soiltemp6': 'group_temperature',
        'soilmoist6': 'group_percent',
        'soiltemp7': 'group_temperature',
        'soilmoist7': 'group_percent',
        'soiltemp8': 'group_temperature',
        'soilmoist8': 'group_percent',
        'soiltemp9': 'group_temperature',
        'soilmoist9': 'group_percent',
        'soiltemp10': 'group_temperature',
        'soilmoist10': 'group_percent',
        'soiltemp11': 'group_temperature',
        'soilmoist11': 'group_percent',
        'soiltemp12': 'group_temperature',
        'soilmoist12': 'group_percent',
        'soiltemp13': 'group_temperature',
        'soilmoist13': 'group_percent',
        'soiltemp14': 'group_temperature',
        'soilmoist14': 'group_percent',
        'soiltemp15': 'group_temperature',
        'soilmoist15': 'group_percent',
        'soiltemp16': 'group_temperature',
        'soilmoist16': 'group_percent',
        'pm251_24h_avg': 'group_concentration',
        'pm252_24h_avg': 'group_concentration',
        'pm253_24h_avg': 'group_concentration',
        'pm254_24h_avg': 'group_concentration',
        'pm255_24h_avg': 'group_concentration',
        'pm10_24h_avg': 'group_concentration',
        'co2_24h_avg': 'group_fraction',
        'leak1': 'group_count',
        'leak2': 'group_count',
        'leak3': 'group_count',
        'leak4': 'group_count',
        'lightningdist': 'group_distance',
        'lightningdettime': 'group_time',
        'lightning_strike_count': 'group_count',
        'lightningcount': 'group_count',
        't_rain': 'group_rain',
        't_rainevent': 'group_rain',
        't_rainrate': 'group_rainrate',
        't_raingain': 'group_rain',
        't_rainday': 'group_rain',
        't_rainweek': 'group_rain',
        't_rainmonth': 'group_rain',
        't_rainyear': 'group_rain',
        't_raintotals': 'group_rain',
        'p_rain': 'group_rain',
        'p_rainevent': 'group_rain',
        'p_rainrate': 'group_rainrate',
        'p_rainday': 'group_rain',
        'p_rainweek': 'group_rain',
        'p_rainmonth': 'group_rain',
        'p_rainyear': 'group_rain',
        'winddir': 'group_direction',
        'windspeed': 'group_speed',
        'gustspeed': 'group_speed',
        'daymaxwind': 'group_speed',
        'leafwet1': 'group_percent',
        'leafwet2': 'group_percent',
        'leafwet3': 'group_percent',
        'leafwet4': 'group_percent',
        'leafwet5': 'group_percent',
        'leafwet6': 'group_percent',
        'leafwet7': 'group_percent',
        'leafwet8': 'group_percent',
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
        'ws90_sig': 'group_count'
    }
    # list of sensors to be displayed in the sensor ID output
    sensors_list = []

    def __init__(self, opts, stn_dict):
        """Initialise a DirectGateway object."""

        # save the optparse options and station dict
        self.opts = opts
        self.stn_dict = stn_dict
        # obtain the IP address and port number to use
        self.ip_address = self.ip_from_config_opts()
        self.port = self.port_from_config_opts()
        # do we filter battery state data
        self.show_battery = self.show_battery_from_config_opts()

    def ip_from_config_opts(self):
        """Obtain the IP address from station config or command line options.

        Determine the IP address to use given a station config dict and command
        line options. The IP address is chosen as follows:
        - if specified use the IP address from the command line
        - if an IP address was not specified on the command line obtain the IP
          address from the station config dict
        - if the station config dict does not specify an IP address, or if it
          is set to 'auto', return None to force device discovery
        """

        # obtain an IP address from the command line options
        ip_address = self.opts.ip_address if self.opts.ip_address else None
        # if we didn't get an IP address check the station config dict
        if ip_address is None:
            # obtain the IP address from the station config dict
            ip_address = self.stn_dict.get('ip_address')
            # if the station config dict specifies some variation of 'auto'
            # then we need to return None to force device discovery
            if ip_address is not None:
                # do we have a variation of 'auto'
                if ip_address.lower() == 'auto':
                    # we need to autodetect IP address so set to None
                    ip_address = None
                    if weewx.debug >= 1:
                        print()
                        print("IP address to be obtained by discovery")
                else:
                    if weewx.debug >= 1:
                        print()
                        print("IP address obtained from station config")
            else:
                if weewx.debug >= 1:
                    print()
                    print("IP address to be obtained by discovery")
        else:
            if weewx.debug >= 1:
                print()
                print("IP address obtained from command line options")
        return ip_address

    def port_from_config_opts(self):
        """Obtain the port from station config or command line options.

        Determine the port to use given a station config dict and command
        line options. The port is chosen as follows:
        - if specified use the port from the command line
        - if a port was not specified on the command line obtain the port from
          the station config dict
        - if the station config dict does not specify a port use the default
          45000
        """

        # obtain a port number from the command line options
        port = self.opts.port if self.opts.port else None
        # if we didn't get a port number check the station config dict
        if port is None:
            # obtain the port number from the station config dict
            port = self.stn_dict.get('port')
            # if a port number was specified it needs to be an integer not a
            # string so try to do the conversion
            try:
                port = int(port)
            except (TypeError, ValueError):
                # If a TypeError then most likely port somehow ended up being
                # None. If a ValueError then we couldn't convert the port
                # number to an integer, maybe it was because it was 'auto'
                # (or some variation) or perhaps it was invalid. Regardless of
                # the error we need to set port to None to force discovery.
                port = default_port
                if weewx.debug >= 1:
                    print("Port number set to default port number")
            else:
                if weewx.debug >= 1:
                    print("Port number obtained from station config")
        else:
            if weewx.debug >= 1:
                print("Port number obtained from command line options")
        return port

    def show_battery_from_config_opts(self):
        """Determine whether to filter nonsense battery state data.

        Determine the whether to filter nonsense battery state data given a
        station config dict and command line options. The decision to filter is
        made as follows:
        - if specified use the show_battery option from the command line
        - if show_battery was not specified on the command line obtain the
          show_battery option from the station config dict
        - if the station config dict does not specify show_battery use the
          default value False
        """

        # obtain the show_battery value from the command line options if it
        # exists
        show_battery = self.opts.show_battery if self.opts.show_battery else None
        # if we didn't get a show_battery value check the station config dict
        if show_battery is None:
            # obtain the show_battery value from the station config dict, try
            # to convert it to a Boolean, if it fails be prepared to catch the
            # ValueError from tobool() and use the default
            try:
                show_battery = weeutil.weeutil.tobool(self.stn_dict.get('show_battery'))
            except ValueError:
                # we could not get show_battery from the stn_dict so use the default
                show_battery = default_show_battery
                if weewx.debug >= 1:
                    print("Battery state filtering ('%s') using the default" % show_battery)
            else:
                if weewx.debug >= 1:
                    print("Port number obtained from station config")
                    print("Battery state filtering ('%s') obtained from station config" % show_battery)
        else:
            if weewx.debug >= 1:
                print("Battery state filtering ('%s') obtained from command line options" % show_battery)
        return show_battery

    def process_options(self):
        """Call the appropriate method based on the optparse options."""

        # run the driver
        if self.opts.test_driver:
            self.test_driver()
        # run the service with simulator
        elif self.opts.test_service:
            self.test_service()
        elif self.opts.sys_params:
            self.system_params()
        elif self.opts.get_rain:
            self.get_rain_data()
        elif self.opts.get_all_rain:
            self.get_all_rain_data()
        elif self.opts.get_mulch_offset:
            self.get_mulch_offset()
        elif self.opts.get_temp_calibration:
            self.get_mulch_t_offset()
        elif self.opts.get_pm25_offset:
            self.get_pm25_offset()
        elif self.opts.get_co2_offset:
            self.get_co2_offset()
        elif self.opts.get_calibration:
            self.get_calibration()
        elif self.opts.get_soil_calibration:
            self.get_soil_calibration()
        elif self.opts.get_services:
            self.get_services()
        elif self.opts.mac:
            self.station_mac()
        elif self.opts.firmware:
            self.firmware()
        elif self.opts.sensors:
            self.sensors()
        elif self.opts.live:
            self.live_data()
        elif self.opts.discover:
            self.discover()
        elif self.opts.map:
            self.field_map()
        elif self.opts.driver_map:
            self.driver_field_map()
        elif self.opts.service_map:
            self.service_field_map()
        else:
            return
        exit(0)

    def system_params(self):
        """Display system parameters.

        Obtain and display the gateway device system parameters. Device IP
        address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # dict for decoding system parameters frequency byte, at present all we
        # know is 0 = 433MHz
        freq_decode = {
            0: '433MHz',
            1: '868Mhz',
            2: '915MHz',
            3: '920MHz'
        }
        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the collector objects system_parameters property
            sys_params_dict = collector.system_parameters
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            # socket timeout so inform the user
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # create a meaningful string for frequency representation
            freq_str = freq_decode.get(sys_params_dict['frequency'], 'Unknown')
            # if sensor_type is 0 there is a WH24 connected, if it's a 1 there
            # is a WH65
            _is_wh24 = sys_params_dict['sensor_type'] == 0
            # string to use in sensor type message
            _sensor_type_str = 'WH24' if _is_wh24 else 'WH65'
            # print the system parameters
            print()
            print("%18s: %s (%s)" % ('frequency',
                                     sys_params_dict['frequency'],
                                     freq_str))
            print("%18s: %s (%s)" % ('sensor type',
                                     sys_params_dict['sensor_type'],
                                     _sensor_type_str))
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
            print("%18s: %s" % ('date-time', date_time_str))
            print("%18s: %s" % ('timezone index', sys_params_dict['timezone_index']))
            print("%18s: %s" % ('DST status', sys_params_dict['dst_status']))

    def get_rain_data(self):
        """Display the device rain data.

        Obtain and display the device rain data. The device IP address and port
        are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the collector objects get_rain_data property
            rain_data = collector.rain_data
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            print()
            print("%10s: %.1f mm/%.1f in" % ('Rain rate', rain_data['t_rainrate'], rain_data['t_rainrate'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Day rain', rain_data['t_rainday'], rain_data['t_rainday'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Week rain', rain_data['t_rainweek'], rain_data['t_rainweek'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Month rain', rain_data['t_rainmonth'], rain_data['t_rainmonth'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Year rain', rain_data['t_rainyear'], rain_data['t_rainyear'] / 25.4))

    def get_all_rain_data(self):
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
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the rain data from the collector object. First try to get
            # all_rain_data but be prepared to catch the exception if our
            # device does not support CMD_READ_RAIN. In that case fall back to
            # the rain_data property instead.
            try:
                rain_data = collector.all_rain_data
            except UnknownApiCommand:
                # use the rain_data property
                rain_data = collector.rain_data
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            print()
            if 'rain_priority' in rain_data:
                print("    Rainfall data priority: %s" % source_lookup.get(rain_data['rain_priority'],
                                                                           "unknown selection"))
                print()
            if any(field in rain_data for field in traditional):
                print("    Traditional rain data:")
                _data = rain_data.get('t_rainrate')
                _data_str = "%.1fmm/hr (%.1fin/hr)" % (_data, _data / 25.4) if _data is not None else "---mm/hr (---in/hr)"
                print("%30s: %s)" % ('Rain rate', _data_str))
                _data = rain_data.get('t_rainevent')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Event rain', _data_str))
                _data = rain_data.get('t_rainday')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Daily rain', _data_str))
                _data = rain_data.get('t_rainweek')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Weekly rain', _data_str))
                _data = rain_data.get('t_rainmonth')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Monthly rain', _data_str))
                _data = rain_data.get('t_rainyear')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Yearly rain', _data_str))
                _data = rain_data.get('t_raingain')
                _data_str = "%.2f" % _data / 100.0 if _data is not None else "---"
                print("%30s: %s" % ('Rain gain', _data_str))
            else:
                print("    No traditional rain data available")
            print()
            if any(field in rain_data for field in piezo):
                print("    Piezo rain data:")
                _data = rain_data.get('p_rainrate')
                _data_str = "%.1fmm/hr (%.1fin/hr)" % (_data, _data / 25.4) if _data is not None else "---mm/hr (---in/hr)"
                print("%30s: %s)" % ('Rain rate', _data_str))
                _data = rain_data.get('p_rainevent')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Event rain', _data_str))
                _data = rain_data.get('p_rainday')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Daily rain', _data_str))
                _data = rain_data.get('p_rainweek')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Weekly rain', _data_str))
                _data = rain_data.get('p_rainmonth')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Monthly rain', _data_str))
                _data = rain_data.get('p_rainyear')
                _data_str = "%.1fmm (%.1fin)" % (_data, _data / 25.4) if _data is not None else "---mm (---in)"
                print("%30s: %s" % ('Yearly rain', _data_str))
                print("%30s: %.2f (%s)" % ('Rain1 gain', rain_data.get('gain1', '--'), '< 4mm/h'))
                print("%30s: %.2f (%s)" % ('Rain2 gain', rain_data.get('gain2', '--'), '< 10mm/h'))
                print("%30s: %.2f (%s)" % ('Rain3 gain', rain_data.get('gain3', '--'), '< 30mm/h'))
                print("%30s: %.2f (%s)" % ('Rain4 gain', rain_data.get('gain4', '--'), '< 60mm/h'))
                print("%30s: %.2f (%s)" % ('Rain5 gain', rain_data.get('gain5', '--'), '> 60mm/h'))
            else:
                print("    No piezo rain data available")
            print()
            if any(field in rain_data for field in reset):
                print("    Rainfall reset time data:")
                print("%30s: 0%d:00" % ('Daily rainfall reset time', rain_data.get('day_reset', '-----')))
                _data = rain_data.get('week_reset')
                _data_str = "%s" % calendar.day_name[(_data + 6) % 7] if _data is not None else "-----"
                print("%30s: %s" % ('Weekly rainfall reset time', _data_str))
                _data = rain_data.get('annual_reset')
                _data_str = "%s" % calendar.month_name[_data + 1] if _data is not None else "-----"
                print("%30s: %s" % ('Annual rainfall reset time', calendar.month_name[rain_data['annual_reset'] + 1]))
            else:
                print("    No rainfall reset time data available")

    def get_mulch_offset(self):
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
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the mulch offset data from the collector object's mulch_offset
            # property
            mulch_offset_data = collector.mulch_offset
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # did we get any mulch offset data
            if mulch_offset_data is not None:
                # now format and display the data
                print()
                print("Multi-channel Temperature and Humidity Calibration")
                # iterate over each channel for which we have data
                for channel in mulch_offset_data:
                    # print the channel and offset data
                    mulch_str = "    Channel %d: Temperature offset: %5s Humidity offset: %3s"
                    # the API returns channels starting at 0, but the WS View
                    # app displays channels starting at 1, so add 1 to our
                    # channel number
                    print(mulch_str % (channel + 1,
                                       "%2.1f" % mulch_offset_data[channel]['temp'],
                                       "%d" % mulch_offset_data[channel]['hum']))
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def get_mulch_t_offset(self):
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
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the mulch temp offset data from the collector object's
            # mulch_offset property
            mulch_t_offset_data = collector.mulch_t_offset
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
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
                        # print the channel and offset data
                        mulch_str = "    Channel %d: Temperature offset: %5s"
                        # the API returns channels starting at 0x63, but the WSView
                        # Plus app displays channels starting at 1, so subtract
                        # 0x62 (or 98) from our channel number
                        print(mulch_str % (channel - 98,
                                           "%2.1f" % mulch_t_offset_data[channel]))
                else:
                    # we have no results, so display a suitable message
                    print("    No Multi-channel temperature sensors found")
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def get_pm25_offset(self):
        """Display the device PM2.5 offset data.

        Obtain and display the PM2.5 offset data from the selected device.The
        device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the PM2.5 offset data from the collector object's pm25_offset
            # property
            pm25_offset_data = collector.pm25_offset
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # did we get any PM2.5 offset data
            if pm25_offset_data is not None:
                # now format and display the data
                print()
                print("PM2.5 Calibration")
                # iterate over each channel for which we have data
                for channel in pm25_offset_data:
                    # print the channel and offset data
                    print("    Channel %d PM2.5 offset: %5s" % (channel, "%2.1f" % pm25_offset_data[channel]))
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def get_co2_offset(self):
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
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the offset data from the collector object's co2_offset
            # property
            co2_offset_data = collector.co2_offset
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # did we get any offset data
            if co2_offset_data is not None:
                # now format and display the data
                print()
                print("CO2 Calibration")
                print("%16s: %5s" % ("CO2 offset", "%2.1f" % co2_offset_data['co2']))
                print("%16s: %5s" % ("PM10 offset", "%2.1f" % co2_offset_data['pm10']))
                print("%16s: %5s" % ("PM2.5 offset", "%2.1f" % co2_offset_data['pm25']))
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def get_calibration(self):
        """Display the device calibration data.

        Obtain and display the calibration data from the selected device. The
        device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the calibration data from the collector object's calibration
            # property
            calibration_data = collector.calibration
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # did we get any calibration data
            if calibration_data is not None:
                # now format and display the data
                print()
                print("Calibration")
                print("%26s: %5.2f" % ("Irradiance gain", calibration_data['solar']))
                print("%26s: %4.1f" % ("UV gain", calibration_data['uv']))
                print("%26s: %4.1f" % ("Wind gain", calibration_data['wind']))
                print("%26s: %4.1f %sC" % ("Inside temperature offset", calibration_data['intemp'], u'\xb0'))
                print("%26s: %4.1f %%" % ("Inside humidity offset", calibration_data['inhum']))
                print("%26s: %4.1f %sC" % ("Outside temperature offset", calibration_data['outtemp'], u'\xb0'))
                print("%26s: %4.1f %%" % ("Outside humidity offset", calibration_data['outhum']))
                print("%26s: %4.1f hPa" % ("Absolute pressure offset", calibration_data['abs']))
                print("%26s: %4.1f hPa" % ("Relative pressure offset", calibration_data['rel']))
                print("%26s: %4.1f %s" % ("Wind direction offset", calibration_data['dir'], u'\xb0'))
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def get_soil_calibration(self):
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
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the calibration data from the collector object's
            # soil_calibration property
            calibration_data = collector.soil_calibration
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
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
                print("%s did not respond." % collector.station.model)

    def get_services(self):
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
                wu_id = data_dict['id'] if self.opts.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Station ID", wu_id))
                # Station key
                key = data_dict['password'] if self.opts.unmask else obfuscate(data_dict['password'])
                print("%22s: %s" % ("Station Key", key))

        def print_weathercloud(data_dict=None):
            """Print Weathercloud settings."""

            # do we have any settings?
            if data_dict is not None:
                # Weathercloud ID
                wc_id = data_dict['id'] if self.opts.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Weathercloud ID", wc_id))
                # Weathercloud key
                key = data_dict['key'] if self.opts.unmask else obfuscate(data_dict['key'])
                print("%22s: %s" % ("Weathercloud Key", key))

        def print_wow(data_dict=None):
            """Print Weather Observations Website settings."""

            # do we have any settings?
            if data_dict is not None:
                # Station ID
                wow_id = data_dict['id'] if self.opts.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Station ID", wow_id))
                # Station key
                key = data_dict['password'] if self.opts.unmask else obfuscate(data_dict['password'])
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
                    custom_id = data_dict['id'] if self.opts.unmask else obfuscate(data_dict['id'])
                    print("%22s: %s" % ("Station ID", custom_id))
                    key = data_dict['password'] if self.opts.unmask else obfuscate(data_dict['password'])
                    print("%22s: %s" % ("Station Key", key))
                # port
                print("%22s: %d" % ("Port", data_dict['port']))
                # upload interval in seconds
                print("%22s: %d seconds" % ("Upload Interval", data_dict['interval']))

        # look table of functions to use to print weather service settings
        print_fns = {'ecowitt_net': print_ecowitt_net,
                     'wunderground': print_wunderground,
                     'weathercloud': print_weathercloud,
                     'wow': print_wow,
                     'custom': print_custom}

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # get the settings for each service know to the device, store them
            # in a dict keyed by the service name
            services_data = dict()
            for service in collector.services:
                services_data[service['name']] = getattr(collector, service['name'])
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # did we get any service data
            if len(services_data) > 0:
                # now format and display the data
                print()
                print("Weather Services")
                # iterate over the weather services we know about and call the
                # relevant function to print the services settings
                for service in collector.services:
                    print()
                    print("  %s" % (service['long_name'],))
                    print_fns[service['name']](services_data[service['name']])
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def station_mac(self):
        """Display the device hardware MAC address.

        Obtain and display the hardware MAC address of the selected device. The
        device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # call the driver objects mac_address() method
            print()
            print("    MAC address: %s" % collector.mac_address)
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)

    def firmware(self):
        """Display the device firmware version string.

        Obtain and display the firmware version string from the selected device.
        The device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # call the driver objects firmware_version() method
            print()
            print("    firmware version string: %s" % collector.firmware_version)
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)

    def sensors(self):
        """Display the device sensor ID information.

        Obtain and display the sensor ID information from the selected device.
        The device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port,
                                         show_battery=self.show_battery)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # first update the collector's sensor ID data
            collector.update_sensor_id_data()
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # now get the sensors property from the collector
            sensors = collector.sensors
            # the sensor ID data is in the sensors data property, did
            # we get any sensor ID data
            if sensors.data is not None and len(sensors.data) > 0:
                # now format and display the data
                print()
                print("%-10s %s" % ("Sensor", "Status"))
                # iterate over each sensor for which we have data
                for address, sensor_data in six.iteritems(sensors.data):
                    # the sensor id indicates whether it is disabled, attempting to
                    # register a sensor or already registered
                    if sensor_data['id'] == 'fffffffe':
                        state = 'sensor is disabled'
                    elif sensor_data['id'] == 'ffffffff':
                        state = 'sensor is registering...'
                    else:
                        # the sensor is registered so we should have signal and battery
                        # data as well
                        battery_desc = sensors.batt_state_desc(address, sensor_data.get('battery'))
                        battery_desc_text = " (%s)" % battery_desc if battery_desc is not None else ""
                        battery_str = "%s%s" % (sensor_data.get('battery'), battery_desc_text)
                        state = "sensor ID: %s  signal: %s  battery: %s" % (sensor_data.get('id').lstrip('0'),
                                                                            sensor_data.get('signal'),
                                                                            battery_str)
                        # print the formatted data
                    print("%-10s %s" % (GatewayCollector.sensor_ids[address].get('long_name'), state))
            elif len(sensors.data) == 0:
                print()
                print("%s did not return any sensor data." % collector.station.model)
            else:
                print()
                print("%s did not respond." % collector.station.model)

    def live_data(self):
        """Display the device live sensor data.

        Obtain and display live sensor data from the selected device. Data is
        presented as read from the device except for conversion to US customary
        or Metric units. Unit labels are included.

        The device IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayCollector object
            collector = GatewayCollector(ip_address=self.ip_address,
                                         port=self.port,
                                         show_battery=self.show_battery)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (collector.station.model,
                                                 collector.station.ip_address.decode(),
                                                 collector.station.port))
            # call the driver objects get_current_data() method to obtain
            # the live sensor data
            live_sensor_data_dict = collector.get_current_data()
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. %s did not respond." % collector.station.model)
        else:
            # we have a data dict to work with, but we need to format the
            # values and may need to convert units

            # the live sensor data dict is a dict of sensor values and a
            # timestamp only, whilst all sensor values are in MetricWX units
            # there is no usUnits field present. We need usUnits to do our unit
            # conversion so add in the usUnits field.
            live_sensor_data_dict['usUnits'] = weewx.METRICWX
            # we will use the timestamp separately so pop it from the dict and
            # save for later
            datetime = live_sensor_data_dict.pop('datetime')
            # extend the WeeWX obs_group_dict with our gateway
            # obs_group_dict, because weewx.units.obs_group_dict.extend is a
            # ListOfDicts we need to use .prepend since the synthetic python2
            # ListOfDicts does not support .update and we want to use the
            # device entry should there already be an entry of the same name in
            # weewx.units.obs_group_dict (eg 'rain')
            weewx.units.obs_group_dict.prepend(DirectGateway.gateway_obs_group_dict)
            # the live data is in MetricWX units, get a suitable converter
            # based on our output units
            if self.opts.units.lower() == 'us':
                _unit_system = weewx.US
            elif self.opts.units.lower() == 'metricwx':
                _unit_system = weewx.METRICWX
            else:
                _unit_system = weewx.METRIC
            c = weewx.units.StdUnitConverters[_unit_system]
            # Now get a formatter, we could use the
            # weewx.units.default_unit_format_dict but we need voltages
            # formatted to two decimal places. So take a copy of the default
            # unit format dict, change the 'volt' format to suit and use that.
            gw_unit_format_dict = dict(weewx.units.default_unit_format_dict)
            gw_unit_format_dict['volt'] = '%.2f'
            f = weewx.units.Formatter(unit_format_dict=gw_unit_format_dict,
                                      unit_label_dict=weewx.units.default_unit_label_dict)
            # now build a new data dict with our converted and formatted data
            result = {}
            # iterate over the fields in our original data dict
            for key, value in six.iteritems(live_sensor_data_dict):
                # we don't need usUnits in the result so skip it
                if key == 'usUnits':
                    continue
                # get our key as a ValueTuple
                key_vt = weewx.units.as_value_tuple(live_sensor_data_dict, key)
                # now get a ValueHelper which will do the conversion and
                # formatting
                key_vh = weewx.units.ValueHelper(key_vt, formatter=f, converter=c)
                # and add the converted and formatted value to our dict
                result[key] = key_vh.toString(None_string='None')
            # finally, sort our dict by key and print the data
            print()
            print("Displaying data using the WeeWX %s unit group." % weewx.units.unit_nicknames.get(_unit_system))
            print()
            print("%s live sensor data (%s): %s" % (collector.station.model,
                                                    weeutil.weeutil.timestamp_to_string(datetime),
                                                    weeutil.weeutil.to_sorted_string(result)))

    @staticmethod
    def discover():
        """Display details of gateway devices on the local network."""

        # this could take a few seconds so warn the user
        print()
        print("Discovering devices on the local network. Please wait...")
        # get an GatewayCollector object
        collector = GatewayCollector()
        # Call the GatewayCollector object discover() method to obtain a list of
        # unique devices discovered. Would consider wrapping in a try..except
        # so we can catch any socket timeout exceptions but the
        # Station.discover() method should catch any such exceptions for us.
        device_list = collector.station.discover()
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
            else:
                if num_gw_found > 1:
                    print()
                    print("Multiple devices were found.")
                    print("If using the gateway driver consider explicitly specifying the ")
                    print("IP address and port of the device to be used under [GW1000] in weewx.conf.")
                elif num_gw_found == 0:
                    print("No devices were discovered.")
        else:
            # we have no results
            print("No devices were discovered.")

    @staticmethod
    def field_map():
        """Display the default field map."""

        # obtain a copy of the default field map, we need a copy so we can
        # augment it with the battery state map
        field_map = dict(Gateway.default_field_map)
        # now add in the rain field map
        field_map.update(Gateway.rain_field_map)
        # now add in the wind field map
        field_map.update(Gateway.wind_field_map)
        # now add in the battery state field map
        field_map.update(Gateway.battery_field_map)
        # now add in the sensor signal field map
        field_map.update(Gateway.sensor_signal_field_map)
        print()
        print("Gateway driver/service default field map:")
        print("(format is WeeWX field name: gateway field name)")
        print()
        # obtain a list of naturally sorted dict keys so that, for example,
        # xxxxx16 appears in the correct order
        keys_list = natural_sort_keys(field_map)
        # iterate over the sorted keys and print the key and item
        for key in keys_list:
            print("    %23s: %s" % (key, field_map[key]))

    def driver_field_map(self):
        """Display the driver field map that would be used.

        By default, the default field map is used by the driver; however, the
        user may alter the field map used by the driver via the [GW1000]
        stanza. This method displays the actual field map that would be used by
        the driver.
        """

        # this may take a moment to set up so inform the user
        print()
        print("This may take a moment...")
        # place an entry in the log so that if we encounter errors that are
        # logged we can tell they were not caused by a live WeeWX instance
        loginf("Obtaining a gateway driver...")
        # wrap in a try..except in case there is an error obtaining and
        # interacting with the driver
        try:
            # get a GatewayDriver object
            driver = GatewayDriver(**self.stn_dict)
            # now display the field map defined in the driver's field_map
            # property
            print()
            print("Gateway driver actual field map:")
            print("(format is WeeWX field name: gateway field name)")
            print()
            # obtain a list of naturally sorted dict keys so that, for example,
            # xxxxx16 appears in the correct order
            keys_list = natural_sort_keys(driver.field_map)
            # iterate over the sorted keys and print the key and item
            for key in keys_list:
                print("    %23s: %s" % (key, driver.field_map[key]))
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
            print()
            print("Unable to display actual driver field map")
        except KeyboardInterrupt:
            # we have a keyboard interrupt so shut down
            if driver:
                driver.closePort()
        loginf("Finished using gateway driver")

    def service_field_map(self):
        """Display the service field map that would be used.

        By default, the default field map is used by the service; however, the
        user may alter the field map used by the service via the [GW1000]
        stanza. This method displays the actual field map that would be used by
        the service.
        """

        # this may take a moment to set up so inform the user
        print()
        print("This may take a moment...")
        # place an entry in the log so that if we encounter errors that are
        # logged we can tell they were not caused by a live WeeWX instance
        loginf("Obtaining a gateway service...")
        # Create a dummy config so we can stand up a dummy engine with a dummy
        # simulator emitting arbitrary loop packets. Include the gateway
        # service and StdPrint. StdPrint will take care of printing our loop
        # packets (no StdArchive so loop packets only, no archive records)
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
                    'archive_services': 'user.gw1000.GatewayService',
                    'report_services': 'weewx.engine.StdPrint'}}}
        # set the IP address and port in the dummy config
        config['GW1000']['ip_address'] = self.ip_address
        config['GW1000']['port'] = self.port
        # wrap in a try..except in case there is an error
        try:
            # create a dummy engine
            engine = weewx.engine.StdEngine(config)
            # Our gateway service will have been instantiated by the engine
            # during its startup. Whilst access to the service is not normally
            # required we require access here, so we can obtain some info about
            # the station we are using for this test. The engine does not
            # provide a ready means to access that gateway service, so we can
            # do a bit of guessing and iterate over all the engine's services
            # and select the one that has a 'collector' property. Unlikely to
            # cause a problem since there are only two services in the dummy
            # engine.
            gw_svc = None
            for svc in engine.service_obj:
                if hasattr(svc, 'collector'):
                    gw_svc = svc
            if gw_svc is not None:
                # we have a gateway service, it's not much use, but it has the
                # field map we need so go ahead and display its field map
                print()
                print("Gateway service actual field map:")
                print("(format is WeeWX field name: gateway field name)")
                print()
                # obtain a list of naturally sorted dict keys so that, for example,
                # xxxxx16 appears in the correct order
                keys_list = natural_sort_keys(gw_svc.field_map)
                # iterate over the sorted keys and print the key and item
                for key in keys_list:
                    print("    %23s: %s" % (key, gw_svc.field_map[key]))
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
            print()
            print("Unable to display actual driver field map")
        except KeyboardInterrupt:
            if engine:
                engine.shutDown()
        loginf("Finished using gateway service")

    def test_driver(self):
        """Exercise the gateway driver as a driver.

        Exercises the gateway driver only. Loop packets, but no archive
        records, are emitted to the console continuously until a keyboard
        interrupt is received. A station config dict is coalesced from any
        relevant command line parameters and the config file in use with
        command line parameters overriding those in the config file.
        """

        loginf("Testing gateway driver...")
        # set the IP address and port in the station config dict
        self.stn_dict['ip_address'] = self.ip_address
        self.stn_dict['port'] = self.port
        if self.opts.poll_interval:
            self.stn_dict['poll_interval'] = self.opts.poll_interval
        if self.opts.max_tries:
            self.stn_dict['max_tries'] = self.opts.max_tries
        if self.opts.retry_wait:
            self.stn_dict['retry_wait'] = self.opts.retry_wait
        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDriver object
            driver = GatewayDriver(**self.stn_dict)
            # identify the device being used
            print()
            print("Interrogating %s at %s:%d" % (driver.collector.station.model,
                                                 driver.collector.station.ip_address.decode(),
                                                 driver.collector.station.port))
            print()
            # continuously get loop packets and print them to screen
            for pkt in driver.genLoopPackets():
                print(": ".join([weeutil.weeutil.timestamp_to_string(pkt['dateTime']),
                                 weeutil.weeutil.to_sorted_string(pkt)]))
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except KeyboardInterrupt:
            # we have a keyboard interrupt so shut down
            driver.closePort()
        loginf("Gateway driver testing complete")

    def test_service(self):
        """Exercise the gateway driver as a service.

        Uses a dummy engine/simulator to generate arbitrary loop packets for
        augmenting. Use a 10-second loop interval so we don't get too many bare
        packets.
        """

        loginf("Testing gateway service...")
        # Create a dummy config, so we can stand up a dummy engine with a dummy
        # simulator emitting arbitrary loop packets. Include the gateway
        # service and StdPrint. StdPrint will take care of printing our loop
        # packets (no StdArchive so loop packets only, no archive records)
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
                    'archive_services': 'user.gw1000.GatewayService',
                    'report_services': 'weewx.engine.StdPrint'}}}
        # set the IP address and port in the dummy config
        config['GW1000']['ip_address'] = self.ip_address
        config['GW1000']['port'] = self.port
        # these command line options should only be added if they exist
        if self.opts.poll_interval:
            config['GW1000']['poll_interval'] = self.opts.poll_interval
        if self.opts.max_tries:
            config['GW1000']['max_tries'] = self.opts.max_tries
        if self.opts.retry_wait:
            config['GW1000']['retry_wait'] = self.opts.retry_wait
        # assign our dummyTemp field to a unit group so unit conversion works
        # properly
        weewx.units.obs_group_dict['dummyTemp'] = 'group_temperature'
        # wrap in a try..except in case there is an error
        try:
            # create a dummy engine
            engine = weewx.engine.StdEngine(config)
            # Our gateway service will have been instantiated by the engine
            # during its startup. Whilst access to the service is not normally
            # required we require access here, so we can obtain some info about
            # the station we are using for this test. The engine does not
            # provide a ready means to access that gateway service, so we can
            # do a bit of guessing and iterate over all the engine's services
            # and select the one that has a 'collector' property. Unlikely to
            # cause a problem since there are only two services in the dummy
            # engine.
            gw_svc = None
            for svc in engine.service_obj:
                if hasattr(svc, 'collector'):
                    gw_svc = svc
            if gw_svc is not None:
                # identify the device being used
                print()
                print("Interrogating %s at %s:%d" % (gw_svc.collector.station.model,
                                                     gw_svc.collector.station.ip_address.decode(),
                                                     gw_svc.collector.station.port))
            print()
            while True:
                # create an arbitrary loop packet, all it needs is a timestamp, a
                # defined unit system and a token obs
                packet = {'dateTime': int(time.time()),
                          'usUnits': weewx.US,
                          'dummyTemp': 96.3
                          }
                # send out a NEW_LOOP_PACKET event with the dummy loop packet
                # to trigger the gateway service to augment the loop packet
                engine.dispatchEvent(weewx.Event(weewx.NEW_LOOP_PACKET,
                                                 packet=packet,
                                                 origin='software'))
                # sleep for a bit to emulate the simulator
                time.sleep(10)
        except GWIOError as e:
            print()
            print("Unable to connect to device: %s" % e)
        except KeyboardInterrupt:
            engine.shutDown()
        loginf("Gateway service testing complete")


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
# The above commands will display details of available command line options.
#
# Note. Whilst the driver may be run independently of WeeWX the driver still
# requires WeeWX and it's dependencies be installed. Consequently, if
# WeeWX 4.0.0 or later is installed the driver must be run under the same
# Python version as WeeWX uses. This means that on some systems 'python' in the
# above commands may need to be changed to 'python2' or 'python3'.

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
       python -m user.gw1000 --sensors
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--show-all-batt]
            [--debug=0|1|2|3]
       python -m user.gw1000 --live-data
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--units=us|metric|metricwx]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--show-all-batt]
            [--debug=0|1|2|3]
       python -m user.gw1000 --firmware-version|--mac-address|
            --system-params|--get-rain-data|--get-all-rain_data
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]
       python -m user.gw1000 --get-calibration|--get-mulch-th-cal|
            --get-mulch-soil-cal|--get-mulch-t-cal|
            --get-pm25-cal|--get-co2-cal
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]
       python -m user.gw1000 --get-services
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--unmask] [--debug=0|1|2|3]
       python -m user.gw1000 --default-map|--driver-map|--service-map
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--debug=0|1|2|3]
       python -m user.gw1000 --discover
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--debug=0|1|2|3]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version number')
    parser.add_option('--config', dest='config_path', metavar='CONFIG_FILE',
                      help="Use configuration file CONFIG_FILE.")
    parser.add_option('--debug', dest='debug', type=int,
                      help='How much status to display, 0-3')
    parser.add_option('--discover', dest='discover', action='store_true',
                      help='discover devices and display device IP address '
                           'and port')
    parser.add_option('--firmware-version', dest='firmware',
                      action='store_true',
                      help='display device firmware version')
    parser.add_option('--mac-address', dest='mac', action='store_true',
                      help='display device station MAC address')
    parser.add_option('--system-params', dest='sys_params', action='store_true',
                      help='display device system parameters')
    parser.add_option('--sensors', dest='sensors', action='store_true',
                      help='display device sensor information')
    parser.add_option('--live-data', dest='live', action='store_true',
                      help='display device live sensor data')
    parser.add_option('--get-rain-data', dest='get_rain', action='store_true',
                      help='display device traditional rain data only')
    parser.add_option('--get-all-rain-data', dest='get_all_rain', action='store_true',
                      help='display device traditional, piezo and rain reset '
                           'time data')
    parser.add_option('--get-calibration', dest='get_calibration',
                      action='store_true',
                      help='display device calibration data')
    parser.add_option('--get-mulch-th-cal', dest='get_mulch_offset',
                      action='store_true',
                      help='display device multi-channel temperature and '
                           'humidity calibration data')
    parser.add_option('--get-mulch-soil-cal', dest='get_soil_calibration',
                      action='store_true',
                      help='display device soil moisture calibration data')
    parser.add_option('--get-mulch-t-cal', dest='get_temp_calibration',
                      action='store_true',
                      help='display device temperature (WN34) calibration data')
    parser.add_option('--get-pm25-cal', dest='get_pm25_offset',
                      action='store_true',
                      help='display device PM2.5 calibration data')
    parser.add_option('--get-co2-cal', dest='get_co2_offset',
                      action='store_true',
                      help='display device CO2 (WH45) calibration data')
    parser.add_option('--get-services', dest='get_services',
                      action='store_true',
                      help='display device weather services configuration data')
    parser.add_option('--default-map', dest='map', action='store_true',
                      help='display the default field map')
    parser.add_option('--driver-map', dest='driver_map', action='store_true',
                      help='display the field map that would be used by the gateway '
                           'driver')
    parser.add_option('--service-map', dest='service_map', action='store_true',
                      help='display the field map that would be used by the gateway '
                           'service')
    parser.add_option('--test-driver', dest='test_driver', action='store_true',
                      metavar='TEST_DRIVER', help='exercise the gateway driver')
    parser.add_option('--test-service', dest='test_service',
                      action='store_true', metavar='TEST_SERVICE',
                      help='exercise the gateway service')
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

    # get a DirectGateway object
    direct_gw = DirectGateway(opts, stn_dict)
    # now let the DirectGateway object process the options
    direct_gw.process_options()
    # if we made it here no option was selected so display our help
    parser.print_help()


if __name__ == '__main__':
    main()
