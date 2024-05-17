#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gw1000.py

A WeeWX driver for devices using Ecowitt LAN/Wi-Fi Gateway API.

The WeeWX Ecowitt Gateway driver (known historically as the 'WeeWX GW1000
driver') utilises the Ecowitt LAN/Wi-Fi Gateway API and device HTTP requests to
pull data from the gateway device. This is in contrast to the push methodology
used by drivers that obtain data from the gateway device via Ecowitt or
WeatherUnderground format uploads emitted by the device. The pull approach has
the advantage of giving the user more control over when the data is obtained
from the device plus also giving access to a greater range of metrics.

As of the time of release this driver supports the GW1000, GW1100 and GW2000
gateway devices as well as the WH2650, WH2680 and WN1900 Wi-Fi weather stations.
The Ecowitt Gateway driver can be operated as a traditional WeeWX driver where
it is the source of loop data or it can be operated as a WeeWX service where it
is used to augment loop data produced by another driver.

Copyright (C) 2020-2024 Gary Roderick                   gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see https://www.gnu.org/licenses/.

Version: 0.7.0a1                                   Date: X Xxxxxxxxx 202x

Revision History
    X Xxxxxxxxxx 202x       v0.7.0
        -
    21 February 2024        v0.6.1
        -   fix bug in construct_field_map() signature that resulted in field
            map and field map extensions being ignored
    7 February 2024         v0.6.0
        -   significant re-structuring of classes used to better delineate
            responsibilities and prepare for the implementation of the
            GatewayHttp class
        -   implement device HTTP requests to obtain additional device/sensor
            status data not available via API
        -   fixed issue that prevented use of the driver as both a driver and a
            service under a single WeeWX instance
        -   fixes error in multi-channel temperature calibration data decode
        -   updated IAW Gateway API documentation v1.6.9
        -   added support for free heap memory field
        -   rename a number of calibration/offset related command line options
            to better align with the labels/names now used in the WSView Plus
            app v2.0.32
        -   --firmware command line option now displays gateway device and
            (where available) sensor firmware versions along with a short
            message if a device firmware update is available
        -   implement gateway device firmware update check and logging
        -   gateway device temperature compensation setting can be displayed
            using the --system-params command line option (for firmware
            versions GW2000 all, GW1100 > v2.1.2 and GW1000 > v1.6.9)
        -   added wee_device/weectl device support
        -   rationalised driver direct and wee_device/weectl device actions
        -   the discarding of non-timestamped and stale packets is now logged
            by the GatewayService when debug_loop is set or debug >= 2
        -   unit groups are now assigned to all WeeWX fields in the default
            field map that are not included in the default WeeWX wview_extended
            schema
        -   'kilobyte' and 'megabyte' are added to unit group 'group_data' on
            driver/service startup
    13 June 2022            v0.5.0b5
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
        -   GatewayService now defaults to using a [GW1000Service] stanza but
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


This driver is based on the Ecowitt LAN/Wi-Fi Gateway API documentation v1.6.9.
However, the following deviations from the Ecowitt LAN/Wi-Fi Gateway API
documentation v1.6.9 have been made in this driver:

1.  CMD_READ_SSSS documentation states that 'UTC time' is part of the data
returned by the CMD_READ_SSSS API command. The UTC time field is described as
'UTC time' and is an unsigned long. No other details are provided in the API
documentation. Rather than being a Unix epoch timestamp, the UTC time data
appears to be a Unix epoch timestamp that is offset from UTC time by the
gateway device timezone. In other words, two gateway devices in different
timezones that have their system time correctly set will return different
values for UTC time via the CMD_READ_SSSS command. The Ecowitt Gateway driver
subtracts the system UTC offset in seconds from the UTC time returned by the
CMD_READ_SSSS command in order to obtain the correct UTC time.

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
calibration data. This API command is referred to as 'CMD_GET_MulCH_T_OFFSET'
within the driver and has been implemented as of v0.6.0. Calibration data is
provided in standardised Ecowitt gateway device API response packet format.
The API response uses two bytes for packet size. Header, command code and
checksum are standard values/formats. Data structure is two bytes per sensor,
first byte is sensor address (0x63 to 0x6A) and second byte is tenths C
calibration value (or calibration value x 10). Calibration value may be from
+10C to -10C. Data is included only for connected sensors. This support should
be considered experimental.

4.  API documentation v1.6.9 lists field 7B as 'Radiation compensation', though
in the WSView Plus app the field 7B data is displayed against a label
'Temperature Compensation' for devices WH65/WH69/WS80/WS90. Field 7B is more
correctly referred to as 'Temperature Compensation' as the setting controls
whether the outdoor temperature for the listed devices is compensated by an
Ecowitt formula based on the radiation level (perhaps other fields as well).
Field 7B is located amidst various rain related fields and bizarrely field 7B
data is only available through the recent CMD_READ_RAIN API command. As the
CMD_READ_RAIN command was only recently introduced, some gateway devices using
old firmware cannot use the CMD_READ_RAIN API command meaning field 7B cannot
be read from some gateway devices using the API. Field 7B can be read once the
gateway device firmware is updated to a version that supports the CMD_READ_RAIN
command. The field 7B data/'Temperature Compensation' setting can be displayed
via the --system-params command line option.


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
          'python' in the above api_commands may need to be changed to 'python2'
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
        super(BijectionError, self).__init__(msg.format(value))


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


class GatewayApiParser():
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
        b'\x01': ('decode_temp', 2, 'intemp', 'ITEM_INTEMP'),
        b'\x02': ('decode_temp', 2, 'outtemp', 'ITEM_OUTTEMP'),
        b'\x03': ('decode_temp', 2, 'dewpoint', 'ITEM_DEWPOINT'),
        b'\x04': ('decode_temp', 2, 'windchill', 'ITEM_WINDCHILL'),
        b'\x05': ('decode_temp', 2, 'heatindex', 'ITEM_HEATINDEX'),
        b'\x06': ('decode_humid', 1, 'inhumid', 'ITEM_INHUMI'),
        b'\x07': ('decode_humid', 1, 'outhumid', 'ITEM_OUTHUMI'),
        b'\x08': ('decode_press', 2, 'absbarometer', 'ITEM_ABSBARO'),
        b'\x09': ('decode_press', 2, 'relbarometer', 'ITEM_RELBARO'),
        b'\x0A': ('decode_dir', 2, 'winddir', 'ITEM_WINDDIRECTION'),
        b'\x0B': ('decode_speed', 2, 'windspeed', 'ITEM_WINDSPEED'),
        b'\x0C': ('decode_speed', 2, 'gustspeed', 'ITEM_GUSTSPEED'),
        b'\x0D': ('decode_rain', 2, 't_rainevent', 'ITEM_RAINEVENT'),
        b'\x0E': ('decode_rainrate', 2, 't_rainrate', 'ITEM_RAINRATE'),
        b'\x0F': ('decode_gain_100', 2, 't_raingain', 'ITEM_RAIN_Gain'),
        b'\x10': ('decode_rain', 2, 't_rainday', 'ITEM_RAINDAY'),
        b'\x11': ('decode_rain', 2, 't_rainweek', 'ITEM_RAINWEEK'),
        b'\x12': ('decode_big_rain', 4, 't_rainmonth', 'ITEM_RAINMONTH'),
        b'\x13': ('decode_big_rain', 4, 't_rainyear', 'ITEM_RAINYEAR'),
        b'\x14': ('decode_big_rain', 4, 't_raintotals', 'ITEM_TOTALS'),
        b'\x15': ('decode_light', 4, 'light', 'ITEM_LIGHT'),
        b'\x16': ('decode_uv', 2, 'uv', 'ITEM_UV'),
        b'\x17': ('decode_uvi', 1, 'uvi', 'ITEM_UVI'),
        b'\x18': ('decode_datetime', 6, 'datetime', 'ITEM_TIME'),
        b'\x19': ('decode_speed', 2, 'daymaxwind', 'ITEM_DAYLWINDMAX'),
        b'\x1A': ('decode_temp', 2, 'temp1', 'ITEM_TEMP1'),
        b'\x1B': ('decode_temp', 2, 'temp2', 'ITEM_TEMP2'),
        b'\x1C': ('decode_temp', 2, 'temp3', 'ITEM_TEMP3'),
        b'\x1D': ('decode_temp', 2, 'temp4', 'ITEM_TEMP4'),
        b'\x1E': ('decode_temp', 2, 'temp5', 'ITEM_TEMP5'),
        b'\x1F': ('decode_temp', 2, 'temp6', 'ITEM_TEMP6'),
        b'\x20': ('decode_temp', 2, 'temp7', 'ITEM_TEMP7'),
        b'\x21': ('decode_temp', 2, 'temp8', 'ITEM_TEMP8'),
        b'\x22': ('decode_humid', 1, 'humid1', 'ITEM_HUMI1'),
        b'\x23': ('decode_humid', 1, 'humid2', 'ITEM_HUMI2'),
        b'\x24': ('decode_humid', 1, 'humid3', 'ITEM_HUMI3'),
        b'\x25': ('decode_humid', 1, 'humid4', 'ITEM_HUMI4'),
        b'\x26': ('decode_humid', 1, 'humid5', 'ITEM_HUMI5'),
        b'\x27': ('decode_humid', 1, 'humid6', 'ITEM_HUMI6'),
        b'\x28': ('decode_humid', 1, 'humid7', 'ITEM_HUMI7'),
        b'\x29': ('decode_humid', 1, 'humid8', 'ITEM_HUMI8'),
        b'\x2A': ('decode_pm25', 2, 'pm251', 'ITEM_PM25_CH1'),
        b'\x2B': ('decode_temp', 2, 'soiltemp1', 'ITEM_SOILTEMP1'),
        b'\x2C': ('decode_moist', 1, 'soilmoist1', 'ITEM_SOILMOISTURE1'),
        b'\x2D': ('decode_temp', 2, 'soiltemp2', 'ITEM_SOILTEMP2'),
        b'\x2E': ('decode_moist', 1, 'soilmoist2', 'ITEM_SOILMOISTURE2'),
        b'\x2F': ('decode_temp', 2, 'soiltemp3', 'ITEM_SOILTEMP3'),
        b'\x30': ('decode_moist', 1, 'soilmoist3', 'ITEM_SOILMOISTURE3'),
        b'\x31': ('decode_temp', 2, 'soiltemp4', 'ITEM_SOILTEMP4'),
        b'\x32': ('decode_moist', 1, 'soilmoist4', 'ITEM_SOILMOISTURE4'),
        b'\x33': ('decode_temp', 2, 'soiltemp5', 'ITEM_SOILTEMP5'),
        b'\x34': ('decode_moist', 1, 'soilmoist5', 'ITEM_SOILMOISTURE5'),
        b'\x35': ('decode_temp', 2, 'soiltemp6', 'ITEM_SOILTEMP6'),
        b'\x36': ('decode_moist', 1, 'soilmoist6', 'ITEM_SOILMOISTURE6'),
        b'\x37': ('decode_temp', 2, 'soiltemp7', 'ITEM_SOILTEMP7'),
        b'\x38': ('decode_moist', 1, 'soilmoist7', 'ITEM_SOILMOISTURE7'),
        b'\x39': ('decode_temp', 2, 'soiltemp8', 'ITEM_SOILTEMP8'),
        b'\x3A': ('decode_moist', 1, 'soilmoist8', 'ITEM_SOILMOISTURE8'),
        b'\x3B': ('decode_temp', 2, 'soiltemp9', 'ITEM_SOILTEMP9'),
        b'\x3C': ('decode_moist', 1, 'soilmoist9', 'ITEM_SOILMOISTURE9'),
        b'\x3D': ('decode_temp', 2, 'soiltemp10', 'ITEM_SOILTEMP10'),
        b'\x3E': ('decode_moist', 1, 'soilmoist10', 'ITEM_SOILMOISTURE10'),
        b'\x3F': ('decode_temp', 2, 'soiltemp11', 'ITEM_SOILTEMP11'),
        b'\x40': ('decode_moist', 1, 'soilmoist11', 'ITEM_SOILMOISTURE11'),
        b'\x41': ('decode_temp', 2, 'soiltemp12', 'ITEM_SOILTEMP12'),
        b'\x42': ('decode_moist', 1, 'soilmoist12', 'ITEM_SOILMOISTURE12'),
        b'\x43': ('decode_temp', 2, 'soiltemp13', 'ITEM_SOILTEMP13'),
        b'\x44': ('decode_moist', 1, 'soilmoist13', 'ITEM_SOILMOISTURE13'),
        b'\x45': ('decode_temp', 2, 'soiltemp14', 'ITEM_SOILTEMP14'),
        b'\x46': ('decode_moist', 1, 'soilmoist14', 'ITEM_SOILMOISTURE14'),
        b'\x47': ('decode_temp', 2, 'soiltemp15', 'ITEM_SOILTEMP15'),
        b'\x48': ('decode_moist', 1, 'soilmoist15', 'ITEM_SOILMOISTURE15'),
        b'\x49': ('decode_temp', 2, 'soiltemp16', 'ITEM_SOILTEMP16'),
        b'\x4A': ('decode_moist', 1, 'soilmoist16', 'ITEM_SOILMOISTURE16'),
        b'\x4C': ('decode_batt', 16, 'lowbatt', 'ITEM_LOWBATT'),
        b'\x4D': ('decode_pm25', 2, 'pm251_24h_avg', 'ITEM_PM25_24HAVG1'),
        b'\x4E': ('decode_pm25', 2, 'pm252_24h_avg', 'ITEM_PM25_24HAVG2'),
        b'\x4F': ('decode_pm25', 2, 'pm253_24h_avg', 'ITEM_PM25_24HAVG3'),
        b'\x50': ('decode_pm25', 2, 'pm254_24h_avg', 'ITEM_PM25_24HAVG4'),
        b'\x51': ('decode_pm25', 2, 'pm252', 'ITEM_PM25_CH2'),
        b'\x52': ('decode_pm25', 2, 'pm253', 'ITEM_PM25_CH3'),
        b'\x53': ('decode_pm25', 2, 'pm254', 'ITEM_PM25_CH4'),
        b'\x58': ('decode_leak', 1, 'leak1', 'ITEM_LEAK_CH1'),
        b'\x59': ('decode_leak', 1, 'leak2', 'ITEM_LEAK_CH2'),
        b'\x5A': ('decode_leak', 1, 'leak3', 'ITEM_LEAK_CH3'),
        b'\x5B': ('decode_leak', 1, 'leak4', 'ITEM_LEAK_CH4'),
        b'\x60': ('decode_distance', 1, 'lightningdist', 'ITEM_LIGHTNING'),
        b'\x61': ('decode_utc', 4, 'lightningdettime', 'ITEM_LIGHTNING_TIME'),
        b'\x62': ('decode_count', 4, 'lightningcount', 'ITEM_LIGHTNING_POWER'),
        # WN34 battery data is not obtained from live data rather it is
        # obtained from sensor ID data
        b'\x63': ('decode_wn34', 3, 'temp9', 'ITEM_TF_USR1'),
        b'\x64': ('decode_wn34', 3, 'temp10', 'ITEM_TF_USR2'),
        b'\x65': ('decode_wn34', 3, 'temp11', 'ITEM_TF_USR3'),
        b'\x66': ('decode_wn34', 3, 'temp12', 'ITEM_TF_USR4'),
        b'\x67': ('decode_wn34', 3, 'temp13', 'ITEM_TF_USR5'),
        b'\x68': ('decode_wn34', 3, 'temp14', 'ITEM_TF_USR6'),
        b'\x69': ('decode_wn34', 3, 'temp15', 'ITEM_TF_USR7'),
        b'\x6A': ('decode_wn34', 3, 'temp16', 'ITEM_TF_USR8'),
        b'\x6C': ('decode_memory', 4, 'heap_free', 'ITEM_HEAP_FREE'),
        # WH45 battery data is not obtained from live data rather it is
        # obtained from sensor ID data
        b'\x70': ('decode_wh45', 16, ('temp17', 'humid17', 'pm10',
                                      'pm10_24h_avg', 'pm255', 'pm255_24h_avg',
                                      'co2', 'co2_24h_avg'), 'ITEM_SENSOR_CO2'),
        # placeholder for unknown field 0x71
        b'\x71': (None, None, None, 'ITEMPM25_AQI'),
        b'\x72': ('decode_wet', 1, 'leafwet1', 'ITEM_LEAF_WETNESS_CH1'),
        b'\x73': ('decode_wet', 1, 'leafwet2', 'ITEM_LEAF_WETNESS_CH2'),
        b'\x74': ('decode_wet', 1, 'leafwet3', 'ITEM_LEAF_WETNESS_CH3'),
        b'\x75': ('decode_wet', 1, 'leafwet4', 'ITEM_LEAF_WETNESS_CH4'),
        b'\x76': ('decode_wet', 1, 'leafwet5', 'ITEM_LEAF_WETNESS_CH5'),
        b'\x77': ('decode_wet', 1, 'leafwet6', 'ITEM_LEAF_WETNESS_CH6'),
        b'\x78': ('decode_wet', 1, 'leafwet7', 'ITEM_LEAF_WETNESS_CH7'),
        b'\x79': ('decode_wet', 1, 'leafwet8', 'ITEM_LEAF_WETNESS_CH8'),
        b'\x7A': ('decode_int', 1, 'rain_priority', 'ITEM_RAIN_Prority'),
        b'\x7B': ('decode_int', 1, 'temperature_comp', 'ITEM_radcompensation'),
        b'\x80': ('decode_rainrate', 2, 'p_rainrate', 'ITEM_Piezzo_Rain_Rate'),
        b'\x81': ('decode_rain', 2, 'p_rainevent', 'ITEM_Piezzo_Event_Rain'),
        b'\x82': ('decode_reserved', 2, 'p_rainhour', 'ITEM_Piezzo_Hourly_Rain'),
        b'\x83': ('decode_big_rain', 4, 'p_rainday', 'ITEM_Piezzo_Daily_Rain'),
        b'\x84': ('decode_big_rain', 4, 'p_rainweek', 'ITEM_Piezzo_Weekly_Rain'),
        b'\x85': ('decode_big_rain', 4, 'p_rainmonth', 'ITEM_Piezzo_Monthly_Rain'),
        b'\x86': ('decode_big_rain', 4, 'p_rainyear', 'ITEM_Piezzo_yearly_Rain'),
        # field 0x87 and 0x88 hold device parameter data that is not
        # included in the loop packets, hence the device field is not
        # used (None).
        b'\x87': ('decode_rain_gain', 20, None, 'ITEM_Piezo_Gain10'),
        b'\x88': ('decode_rain_reset', 3, None, 'ITEM_RST_RainTime')
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

    def __init__(self, log_unknown_fields=True):
        # do we log unknown fields at info or leave at debug
        self.log_unknown_fields = log_unknown_fields

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
                    decode_fn_str, field_size, field, item = structure[payload[index:index + 1]]
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
                                                               payload[index:index + 1])
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

    def parse_rain(self, response):
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

    def parse_raindata(self, response):
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
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our parsed data
        data_dict = {}
        data_dict['t_rainrate'] = self.decode_big_rain(data[0:4])
        data_dict['t_rainday'] = self.decode_big_rain(data[4:8])
        data_dict['t_rainweek'] = self.decode_big_rain(data[8:12])
        data_dict['t_rainmonth'] = self.decode_big_rain(data[12:16])
        data_dict['t_rainyear'] = self.decode_big_rain(data[16:20])
        return data_dict

    @staticmethod
    def parse_mulch_offset(response):
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
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a counter
        index = 0
        # initialise a dict to hold our parsed data
        offset_dict = {}
        # iterate over the data
        while index < len(data):
            channel = data[index]
            offset_dict[channel] = {}
            try:
                offset_dict[channel]['hum'] = struct.unpack("b", data[index + 1])[0]
            except TypeError:
                offset_dict[channel]['hum'] = struct.unpack("b", bytes([data[index + 1]]))[0]
            try:
                offset_dict[channel]['temp'] = struct.unpack("b", data[index + 2])[0] / 10.0
            except TypeError:
                offset_dict[channel]['temp'] = struct.unpack("b", bytes([data[index + 2]]))[0] / 10.0
            index += 3
        return offset_dict

    @staticmethod
    def parse_mulch_t_offset(response):
        """Parse data from a CMD_GET_MulCH_T_OFFSET API response.

        Response consists of a variable number of bytes determined by the
        connected sensors. Decode as follows:
        Byte(s)     Data            Format          Comments
        1-2         header          -               fixed header 0xFFFF
        3           command code    byte            0x59
        4-5         size            unsigned big
                                    endian short
        ....
        6-2nd last byte
            three bytes per connected WN34 sensor:
                    address         byte            sensor address, 0x63 to
                                                    0x6A incl
                    temp offset     signed big      -100 to +100 in tenths C
                                    endian short    (-10.0 to +10.0)
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
            channel = data[index]
            offset_dict[channel] = struct.unpack(">h", data[index + 1:index + 3])[0] / 10.0
            index += 3
        return offset_dict

    @staticmethod
    def parse_pm25_offset(response):
        """Parse data from a CMD_GET_PM25_OFFSET API response.

        Response consists of 17 bytes as follows:
        Byte(s) Data            Format          Comments
        1-2     header          -               fixed header 0xFFFF
        3       command code    byte            0x2E
        4       size            byte
        5       channel num     byte            fixed 00 (ch1)
        6-7     pm25 offset     signed short    -200 to +200 in tenths µg/m³
                                                (-20.0 to +20.0)
        ....
        14      channel num     byte            fixed 03 (ch4)
        15-16   pm25 offset     signed short    -200 to +200 in tenths µg/m³
                                                (-20.0 to +20.0)
        17      checksum        byte            LSB of the sum of the
                                                command, size and data
                                                bytes
        """

        # determine the size of the PM2.5 offset data
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a counter
        index = 0
        # initialise a dict to hold our parsed data
        offset_dict = {}
        # iterate over the data
        while index < len(data):
            channel = data[index]
            offset_dict[channel] = struct.unpack(">h", data[index + 1:index + 3])[0] / 10.0
            index += 3
        return offset_dict

    @staticmethod
    def parse_co2_offset(response):
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
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our parsed data
        offset_dict = {}
        # and decode/store the offset data
        # bytes 0 and 1 hold the CO2 offset
        offset_dict['co2'] = struct.unpack(">h", data[0:2])[0]
        # bytes 2 and 3 hold the PM2.5 offset
        offset_dict['pm25'] = struct.unpack(">h", data[2:4])[0] / 10.0
        # bytes 4 and 5 hold the PM10 offset
        offset_dict['pm10'] = struct.unpack(">h", data[4:6])[0] / 10.0
        return offset_dict

    @staticmethod
    def parse_gain(response):
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
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our parsed data
        gain_dict = {}
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
    def parse_calibration(response):
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
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our parsed data
        cal_dict = {}
        # and decode/store the offset calibration data
        cal_dict['intemp'] = struct.unpack(">h", data[0:2])[0] / 10.0
        try:
            cal_dict['inhum'] = struct.unpack("b", data[2])[0]
        except TypeError:
            cal_dict['inhum'] = struct.unpack("b", bytes([data[2]]))[0]
        cal_dict['abs'] = struct.unpack(">l", data[3:7])[0] / 10.0
        cal_dict['rel'] = struct.unpack(">l", data[7:11])[0] / 10.0
        cal_dict['outtemp'] = struct.unpack(">h", data[11:13])[0] / 10.0
        try:
            cal_dict['outhum'] = struct.unpack("b", data[13])[0]
        except TypeError:
            cal_dict['outhum'] = struct.unpack("b", bytes([data[13]]))[0]
        cal_dict['dir'] = struct.unpack(">h", data[14:16])[0]
        # return the parsed response
        return cal_dict

    @staticmethod
    def parse_soil_humiad(response):
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
        size = response[3]
        # extract the actual data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        cal_dict = {}
        # initialise a counter
        index = 0
        # iterate over the data
        while index < len(data):
            channel = data[index]
            cal_dict[channel] = {}
            try:
                humidity = data[index + 1]
            except TypeError:
                humidity = data[index + 1]
            cal_dict[channel]['humidity'] = humidity
            cal_dict[channel]['ad'] = struct.unpack(">h", data[index + 2:index + 4])[0]
            try:
                ad_select = data[index + 4]
            except TypeError:
                ad_select = data[index + 4]
            # get 'Customize' setting 1 = enable, 0 = customized
            cal_dict[channel]['ad_select'] = ad_select
            try:
                min_ad = data[index + 5]
            except TypeError:
                min_ad = data[index + 5]
            cal_dict[channel]['adj_min'] = min_ad
            cal_dict[channel]['adj_max'] = struct.unpack(">h", data[index + 6:index + 8])[0]
            index += 8
        # return the parsed response
        return cal_dict

    def parse_ssss(self, response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        data_dict['frequency'] = data[0]
        data_dict['sensor_type'] = data[1]
        data_dict['utc'] = self.decode_utc(data[2:6])
        data_dict['timezone_index'] = data[6]
        data_dict['dst_status'] = data[7] != 0
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_ecowitt(response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        data_dict['interval'] = data[0]
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_wunderground(response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        # obtain the required data from the response decoding any bytestrings
        id_size = data[0]
        data_dict['id'] = data[1:1 + id_size].decode()
        password_size = data[1 + id_size]
        data_dict['password'] = data[2 + id_size:2 + id_size + password_size].decode()
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_wow(response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        # obtain the required data from the response decoding any bytestrings
        id_size = data[0]
        data_dict['id'] = data[1:1 + id_size].decode()
        pw_size = data[1 + id_size]
        data_dict['password'] = data[2 + id_size:2 + id_size + pw_size].decode()
        stn_num_size = data[1 + id_size]
        data_dict['station_num'] = data[3 + id_size + pw_size:3 + id_size + pw_size + stn_num_size].decode()
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_weathercloud(response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        # obtain the required data from the response decoding any bytestrings
        id_size = data[0]
        data_dict['id'] = data[1:1 + id_size].decode()
        key_size = data[1 + id_size]
        data_dict['key'] = data[2 + id_size:2 + id_size + key_size].decode()
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_customized(response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        # obtain the required data from the response decoding any bytestrings
        index = 0
        id_size = data[index]
        index += 1
        data_dict['id'] = data[index:index + id_size].decode()
        index += id_size
        password_size = data[index]
        index += 1
        data_dict['password'] = data[index:index + password_size].decode()
        index += password_size
        server_size = data[index]
        index += 1
        data_dict['server'] = data[index:index + server_size].decode()
        index += server_size
        data_dict['port'] = struct.unpack(">h", data[index:index + 2])[0]
        index += 2
        data_dict['interval'] = struct.unpack(">h", data[index:index + 2])[0]
        index += 2
        data_dict['type'] = data[index]
        index += 1
        data_dict['active'] = data[index]
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_usr_path(response):
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
        size = response[3]
        # extract the actual system parameters data
        data = response[4:4 + size - 3]
        # initialise a dict to hold our final data
        data_dict = {}
        index = 0
        ecowitt_size = data[index]
        index += 1
        data_dict['ecowitt_path'] = data[index:index + ecowitt_size].decode()
        index += ecowitt_size
        wu_size = data[index]
        index += 1
        data_dict['wu_path'] = data[index:index + wu_size].decode()
        # return the parsed response
        return data_dict

    @staticmethod
    def parse_station_mac(response):
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

        # return the parsed response, in this case we convert the bytes to
        # hexadecimal digits and return a string of colon separated
        # hexadecimal digit pairs
        return bytes_to_hex(response[4:10], separator=":")

    @staticmethod
    def parse_firmware_version(response):
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

        Returns a unicode string
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
            results = {}
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
            results = {}
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
            results = {}
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

    def encode_ecowitt(self, interval):
        """Encode """

        interval_byte = struct.pack('B', interval)
        return interval_byte

    def encode_wu_wcloud_wow(self, station_id, station_key):
        """Encode """

        station_id_b = station_id.encode()
        station_key_b = station_key.encode()
        return b''.join([struct.pack('B', len(station_id_b)),
                         station_id_b,
                         struct.pack('B', len(station_key_b)),
                         station_key_b])

    def encode_custom(self, enabled, protocol, server, port, interval, key, ec_path, wu_path):
        """Encode """

        id_b = key.encode()
        password_b = key.encode()
        server_b = server.encode()
        port_b = struct.pack('H', port)
        interval_b = struct.pack('H', interval)
        type_b = struct.pack('B', protocol)
        active_b = struct.pack('B', enabled)
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

    def encode_custom_paths(self, enabled, protocol, server, port, interval, key, ec_path, wu_path):
        """Encode """

        ec_path_b = ec_path.encode()
        wu_path_b = wu_path.encode()
        return b''.join([struct.pack('B', len(ec_path_b)),
                         ec_path_b,
                         struct.pack('B', len(wu_path_b)),
                         wu_path_b])


class Sensors():
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
        'CMD_GET_MulCH_T_OFFSET': b'\x59'
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
                 debug=False, log_unknown_fields=False):

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
            # we don't have a known model so return None
            return None
        # we have no string so return None
        return None

    def get_livedata(self):
        """Get live data.

        Sends the API command to the device to obtain live data with retries.
        If the device cannot be contacted a GWIOError will have been raised by
        send_cmd_with_retries() which will be passed through by get_livedata().
        Any code calling get_livedata() should be prepared to handle this
        exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_GW1000_LIVEDATA')

    def get_raindata(self):
        """Get traditional gauge rain data.

        Sends the API command to obtain traditional gauge rain data from the
        device with retries. If the device cannot be contacted a GWIOError will
        be raised by send_cmd_with_retries() which will be passed through by
        get_raindata(). Any code calling get_raindata() should be prepared to
        handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_RAINDATA')

    def get_ssss(self):
        """Read system parameters.

        Sends the API command to obtain system parameters from the device
        with retries. If the device cannot be contacted a GWIOError will
        have been raised by send_cmd_with_retries() which will be passed
        through by get_system_params(). Any code calling
        get_system_params() should be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_SSSS')

    def get_ecowitt(self):
        """Get Ecowitt.net parameters.

        Sends the API command to obtain the device Ecowitt.net parameters
        with retries. If the device cannot be contacted a GWIOError will
        have been raised by send_cmd_with_retries() which will be passed
        through by get_ecowitt(). Any code calling
        get_ecowitt() should be prepared to handle this
        exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_ECOWITT')

    def get_wunderground(self):
        """Get Weather Underground parameters.

        Sends the API command to obtain the device Weather Underground
        parameters with retries. If the device cannot be contacted a
        GWIOError will have been raised by send_cmd_with_retries() which
        will be passed through by get_wunderground(). Any code
        calling get_wunderground() should be prepared to handle this
        exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_WUNDERGROUND')

    def get_weathercloud(self):
        """Get Weathercloud parameters.

        Sends the API command to obtain the device Weathercloud parameters
        with retries. If the device cannot be contacted a GWIOError will
        have been raised by send_cmd_with_retries() which will be passed
        through by get_weathercloud(). Any code calling
        get_weathercloud() should be prepared to handle this
        exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_WEATHERCLOUD')

    def get_wow(self):
        """Get Weather Observations Website parameters.

        Sends the API command to obtain the device Weather Observations
        Website parameters with retries. If the device cannot be contacted
        a GWIOError will have been raised by send_cmd_with_retries() which
        will be passed through by get_wow(). Any code calling
        get_wow() should be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_WOW')

    def get_customized(self):
        """Get custom server parameters.

        Sends the API command to obtain the device custom server parameters
        with retries. If the device cannot be contacted a GWIOError will
        have been raised by send_cmd_with_retries() which will be passed
        through by get_customized(). Any code calling
        get_customized() should be prepared to handle this exception.
        """

        # obtain the API response
        return self.send_cmd_with_retries('CMD_READ_CUSTOMIZED')

    def get_usr_path(self):
        """Get user defined custom path.

        Sends the API command to obtain the device user defined custom path
        with retries. If the device cannot be contacted a GWIOError will
        have been raised by send_cmd_with_retries() which will be passed
        through by get_usr_path(). Any code calling get_usr_path() should
        be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_USR_PATH')

    def get_station_mac(self):
        """Get device MAC address.

        Sends the API command to obtain the device MAC address with
        retries. If the device cannot be contacted a GWIOError will have
        been raised by send_cmd_with_retries() which will be passed through
        by get_station_mac(). Any code calling get_station_mac() should be
        prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_STATION_MAC')

    def get_firmware_version(self):
        """Get device firmware version.

        Sends the API command to obtain device firmware version with
        retries. If the device cannot be contacted a GWIOError will have
        been raised by send_cmd_with_retries() which will be passed through
        by get_firmware_version(). Any code calling get_firmware_version()
        should be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_FIRMWARE_VERSION')

    def get_sensor_id_new(self):
        """Get sensor ID data.

        Sends the API command to obtain sensor ID data from the device with
        retries. If the device cannot be contacted a GWIOError will have been
        raised by send_cmd_with_retries() which will be passed through by
        get_sensor_id_new(). Any code calling get_sensor_id_new() should be prepared to
        handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_SENSOR_ID_NEW')

    def get_mulch_offset(self):
        """Get multichannel temperature and humidity offset data.

        Sends the API command to obtain the multichannel temperature and
        humidity offset data with retries. If the device cannot be
        contacted a GWIOError will have been raised by
        send_cmd_with_retries() which will be passed through by
        display_mulch_offset(). Any code calling display_mulch_offset() should be
        prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_GET_MulCH_OFFSET')

    def get_mulch_t_offset(self):
        """Get multichannel temperature (WN34) offset data.

        Sends the API command to obtain the multichannel temperature (WN34)
        offset data with retries. If the device cannot be contacted a
        GWIOError will have been raised by send_cmd_with_retries() which
        will be passed through by display_mulch_t_offset(). Any code calling
        display_mulch_t_offset() should be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_GET_MulCH_T_OFFSET')

    def get_pm25_offset(self):
        """Get PM2.5 offset data.

        Sends the API command to obtain the PM2.5 sensor offset data with
        retries. If the device cannot be contacted a GWIOError will have
        been raised by send_cmd_with_retries() which will be passed through
        by display_pm25_offset(). Any code calling display_pm25_offset() should be
        prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_GET_PM25_OFFSET')

    def get_gain(self):
        """Get calibration coefficient data.

        Sends the API command to obtain the calibration coefficient data
        with retries. If the device cannot be contacted a GWIOError will
        have been raised by send_cmd_with_retries() which will be passed
        through by get_gain(). Any code calling
        get_gain() should be prepared to handle this
        exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_GAIN')

    def get_soil_humiad(self):
        """Get soil moisture sensor calibration data.

        Sends the API command to obtain the soil moisture sensor
        calibration data with retries. If the device cannot be contacted a
        GWIOError will have been raised by send_cmd_with_retries() which
        will be passed through by display_soil_calibration(). Any code calling
        display_soil_calibration() should be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_GET_SOILHUMIAD')

    def get_calibration(self):
        """Get offset calibration data.

        Sends the API command to obtain the offset calibration data with
        retries. If the device cannot be contacted a GWIOError will have
        been raised by send_cmd_with_retries() which will be passed through
        by get_offset_calibration(). Any code calling
        get_offset_calibration() should be prepared to handle this
        exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_CALIBRATION')

    def get_co2_offset(self):
        """Get WH45 CO2, PM10 and PM2.5 offset data.

        Sends the API command to obtain the WH45 CO2, PM10 and PM2.5 sensor
        offset data with retries. If the device cannot be contacted a
        GWIOError will have been raised by send_cmd_with_retries() which
        will be passed through by display_co2_offset(). Any code calling
        display_co2_offset() should be prepared to handle this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_GET_CO2_OFFSET')

    def get_rain(self):
        """Get traditional gauge and piezo gauge rain data.

        Sends the API command to obtain the traditional gauge and piezo gauge
        rain data with retries. If the device cannot be contacted a GWIOError
        will be raised by send_cmd_with_retries() which will be passed through
        by get_rain(). Any code calling get_rain() should be prepared to handle
        this exception.
        """

        # obtain the API response and return the validated API response
        return self.send_cmd_with_retries('CMD_READ_RAIN')

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
                           "to send command '{cmd}': {e}")
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
        _msg = ("Failed to obtain response to command '%s' "
                "after %d attempts" % (cmd, self.max_tries))
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
            # TODO. f string formatting
            _msg = "Unknown command code in API response. " \
                   "Expected '%s' (0x%s), received '%s' (0x%s)." % (exp_int,
                                                                    "{:02X}".format(exp_int),
                                                                    resp_int,
                                                                    "{:02X}".format(resp_int))
            raise UnknownApiCommand(_msg)
        # checksum check failed, raise an InvalidChecksum exception
        # TODO. f string formatting
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

        If the command completed sucessfully nothing is done, the function
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


class GatewayDevice():
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
                {'name': 'wunderground_params',
                 'long_name': 'Wunderground'
                 },
                {'name': 'weathercloud_params',
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
                 show_battery=False, log_unknown_fields=False,
                 debug=False):
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
                                      log_unknown_fields=log_unknown_fields,
                                      debug=debug)
        # if discover and (ip_address is None or port is None):
        #     self.ip_address, self.port = self.select_device_by_discovery()
        #     # log the device address being used
        #     print(f'     Using discovered address {self.ip_address}:{self.port}')

        # get a Gateway API parser
        self.gateway_api_parser = GatewayApiParser(log_unknown_fields=log_unknown_fields)

        # get a GatewayHttp object to handle any HTTP requests, a GatewayHttp
        # object requires an IP address
        self.http_api = HttpApi(ip_address=ip_address)

        # get a Sensors object for dealing with sensor state data
        self.sensors = Sensors()

#        # store our model, if we have non-None IP address and port then obtain
#        # the model from the Gateway API, otherwise set model to None
#        if i

        # start off logging failures
        self.log_failures = True

    # def select_device_by_discovery(self, mac=None):
    #     """Use discovery to select a device.
    #
    #     Returns a two-way tuple containing the selected (discovered) device
    #     IP address and port. If no device was selected (discovered) a two-way
    #     'None' tuple is returned.
    #     """
    #
    #     try:
    #         # discover devices on the local network, the result is a list
    #         # of dicts with each dict containing data for a unique
    #         # discovered device
    #         device_list = self.gateway_api.discover()
    #     except socket.error as e:
    #         print(f"An error occurred during discovery: {e} ({type(e)})")
    #         # we have a critical error so raise it
    #         raise
    #     # did we find any devices
    #     if len(device_list) > 0:
    #         # We have at least one, but which one to choose. If we were
    #         # provided a MAC search for that MAC, if we were not provided a
    #         # MAC or that MAC was not discovered just choose the first
    #         # device in the list.
    #         if mac is not None:
    #             for dev in device_list:
    #                 if dev['mac'] == mac.uppeer():
    #                     _ip = dev['ip_address']
    #                     _port = dev['port']
    #                     _model = dev['model']
    #                     # log what we chose
    #                     print(f"Selected {_model} at {_ip}:{_port}")
    #                     return _ip, _port
    #             print(f"Did not discover device with MAX {mac.upper()}")
    #         _ip = device_list[0]['ip_address']
    #         _port = device_list[0]['port']
    #         _model = device_list[0]['model']
    #         # log what we found
    #         devices_str = ', '.join([':'.join([f'{d["ip_address"]}:{int(d["port"]):d}']) for d in device_list])
    #         if len(device_list) == 1:
    #             stem = f"{_model} was"
    #         else:
    #             stem = "Multiple devices were"
    #         print(f"{stem} found at {devices_str}")
    #         print()
    #         # log what we chose
    #         print(f"Selected {_model} at {_ip}:{_port}")
    #         return _ip, _port
    #     # did not discover any device so log it
    #     print("Failed to discover any devices")
    #     return None, None

    @property
    def model(self):
        """Gateway device model."""

        return self.gateway_api.get_model_from_firmware(self.firmware_version)

    @property
    def livedata(self):
        """Gateway device live data."""

        _data = self.gateway_api.get_livedata()
        return self.gateway_api_parser.parse_livedata(_data)

    @property
    def raindata(self):
        """Gateway device traditional rain gauge data."""

        _data = self.gateway_api.get_raindata()
        return self.gateway_api_parser.parse_raindata(_data)

    @property
    def system_params(self):
        """Gateway device system parameters."""

        _data = self.gateway_api.get_ssss()
        return self.gateway_api_parser.parse_ssss(_data)

    @property
    def ecowitt_net_params(self):
        """Gateway device Ecowitt.net parameters.

        The WSView+ app displays the Ecowitt service parameters including the
        device MAC address. When queried for the Ecowitt service parameters the
        Gateway API returns all parameters except the device MAC address. To
        include the device MAC address we separately obtain the device MAC
        address and add it to the Ecowitt service parameter dict.
        """

        # obtain a dict containing the Ecowitt service parameters
        _data = self.gateway_api.get_ecowitt()
        # parse the Ecowitt service parameter data
        _parsed_data = self.gateway_api_parser.parse_ecowitt(_data)
        # now obtain the device MAC address and add it to the Ecowitt service
        # parameter dict
        _parsed_data['mac'] = self.mac_address
        # return the Ecowitt service data
        return _parsed_data

    @property
    def wunderground_params(self):
        """Gateway device Weather Underground parameters."""

        _data = self.gateway_api.get_wunderground()
        return self.gateway_api_parser.parse_wunderground(_data)

    @property
    def weathercloud_params(self):
        """Gateway device Weathercloud parameters."""

        _data = self.gateway_api.get_weathercloud()
        return self.gateway_api_parser.parse_weathercloud(_data)

    @property
    def wow_params(self):
        """Gateway device Weather Observations Website parameters."""

        _data = self.gateway_api.get_wow()
        return self.gateway_api_parser.parse_wow(_data)

    @property
    def custom_params(self):
        """Gateway device custom server parameters."""

        _data = self.gateway_api.get_customized()
        return self.gateway_api_parser.parse_customized(_data)

    @property
    def usr_path(self):
        """Gateway device user defined custom path parameters."""

        _data = self.gateway_api.get_usr_path()
        return self.gateway_api_parser.parse_usr_path(_data)

    @property
    def all_custom_params(self):
        """Gateway device custom server parameters."""
        # TODO. Needs comments

        custom_data = self.gateway_api.get_customized()
        parsed_custom_data = self.gateway_api_parser.parse_customized(custom_data)
        user_path_data = self.gateway_api.get_usr_path()
        parsed_user_path_data = self.gateway_api_parser.parse_usr_path(user_path_data)
        parsed_custom_data.update(parsed_user_path_data)
        return parsed_custom_data

    @property
    def mac_address(self):
        """Gateway device MAC address."""

        _data = self.gateway_api.get_station_mac()
        return self.gateway_api_parser.parse_station_mac(_data)

    @property
    def firmware_version(self):
        """Gateway device firmware version."""

        _data = self.gateway_api.get_firmware_version()
        return self.gateway_api_parser.parse_firmware_version(_data)

    @property
    def sensor_id(self):
        """Gateway device sensor ID data."""

        # TODO. What shoudl we do here?
        _data = self.gateway_api.get_sensor_id_new()
        return _data

    @property
    def mulch_offset(self):
        """Gateway device multichannel temperature and humidity offset data."""

        _data = self.gateway_api.get_mulch_offset()
        return self.gateway_api_parser.parse_mulch_offset(_data)

    @property
    def mulch_t_offset(self):
        """Gateway device multichannel temperature (WN34) offset data."""

        _data = self.gateway_api.get_mulch_t_offset()
        return self.gateway_api_parser.parse_mulch_t_offset(_data)

    @property
    def pm25_offset(self):
        """Gateway device PM2.5 offset data."""

        _data = self.gateway_api.get_pm25_offset()
        return self.gateway_api_parser.parse_pm25_offset(_data)

    @property
    def calibration_coefficient(self):
        """Gateway device calibration coefficient data."""

        _data = self.gateway_api.get_gain()
        return self.gateway_api_parser.parse_calibration(_data)

    @property
    def soil_calibration(self):
        """Gateway device soil calibration data."""

        _data = self.gateway_api.get_soil_humiad()
        return self.gateway_api_parser.parse_soil_humiad(_data)

    # TODO. Is this method appropriately named?
    @property
    def offset_calibration(self):
        """Gateway device offset calibration data."""

        _data = self.gateway_api.get_calibration()
        return self.gateway_api_parser.parse_calibration()

    @property
    def co2_offset(self):
        """Gateway device CO2 offset data."""

        _data = self.gateway_api.get_co2_offset()
        return self.gateway_api_parser.parse_co2_offset(_data)

    @property
    def rain(self):
        """Gateway device traditional gauge and piezo gauge rain data."""

        _data = self.gateway_api.get_rain()
        return self.gateway_api_parser.parse_rain(_data)

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
    def calibration(self):
        """Device device calibration data."""

        # obtain the calibration data via the API
        gain_data = self.gateway_api.get_gain()
        # parse the calibration data
        parsed_gain = self.gateway_api_parser.parse_gain(gain_data)
        # obtain the offset calibration data via the API
        calibration_data = self.gateway_api.get_calibration()
        # update our parsed gain data with the parsed calibration data
        parsed_gain.update(self.gateway_api_parser.parse_calibration(calibration_data))
        # return the parsed data
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

    def write_ecowitt(self, *ecowitt):
        """Write Ecowitt.net upload parameters.

        Write Ecowitt.net upload parameters to a gateway device. The only user
        configurable Ecowitt.net upload parameter is the upload interval which
        must be an integer number of minutes from 0 to 5 inclusive. 0
        indicates that uploads to Ecowitt.net are disabled.

        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # do we have a valid interval value
        if 0 <= ecowitt[0] <= 5:
            # we have a valid interval value, package as a dict and encode to
            # produce the data payload
            payload = self.gateway_api_parser.encode_ecowitt(*ecowitt)
            # update the gateway device
            self.gateway_api.set_ecowitt(payload)
        else:
            # we have an invalid interval setting, raise an InvalidSetting
            # exception with a suitable message
            raise InvalidSetting(f"Invalid interval value '{ecowitt[0]:d}'")

    def write_wu(self, *wu):
        """Write WeatherUnderground upload parameters.

        Write WeatherUnderground upload parameters to a gateway device. The
        WeatherUnderground parameters consist of station ID and station key
        (aka API key). The station ID and station key are both ASCII strings
        with a max length of 32 characters.

        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # do we have a valid interval value
        if 0 <= len(wu[0]) <= 32 and 0 <= len(wu[1]) <= 32:
            # we have valid data, encode to produce the data payload
            payload = self.gateway_api_parser.encode_wu_wcloud_wow(*wu)
            # update the gateway device
            self.gateway_api.set_wu(payload)
        else:
            # we have an invalid interval setting, raise an InvalidSetting
            # exception with a suitable message
            if len(wu[0]) > 32:
                raise InvalidSetting(f"Invalid Station ID '{wu[0]}'")
            else:
                raise InvalidSetting(f"Invalid Station key '{wu[1]}'")

    def write_wcloud(self, *wcloud):
        """Write Weathercloud upload parameters.

        Write Weathercloud upload parameters to a gateway device. The
        Weathercloud parameters consist of station ID and station key. The
        station ID and station key are both ASCII strings with a max length of
        32 characters.

        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # do we have a valid interval value
        if 0 <= len(wcloud[0]) <= 32 and 0 <= len(wcloud[1]) <= 32:
            # we have valid data, encode to produce the data payload
            payload = self.gateway_api_parser.encode_wu_wcloud_wow(*wcloud)
            # update the gateway device
            self.gateway_api.set_wcloud(payload)
        else:
            # we have an invalid interval setting, raise an InvalidSetting
            # exception with a suitable message
            if len(wcloud[0]) > 32:
                raise InvalidSetting(f"Invalid Station ID '{wcloud[0]}'")
            else:
                raise InvalidSetting(f"Invalid Station key '{wcloud[1]}'")

    def write_wow(self, *wow):
        """Write Weather Observations Website upload parameters.

        Write Weather Observations Website upload parameters to a gateway
        device. The Weather Observations Website parameters consist of station
        ID and station key. The station ID and station key are both ASCII
        strings with a max length of 39 and 32 characters respectively.

        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # do we have a valid interval value
        if 0 <= len(wow[0]) <= 39 and 0 <= len(wow[1]) <= 32:
            # we have valid data, encode to produce the data payload
            payload = self.gateway_api_parser.encode_wu_wcloud_wow(*wow)
            # update the gateway device
            self.gateway_api.set_wow(payload)
        else:
            # we have an invalid interval setting, raise an InvalidSetting
            # exception with a suitable message
            if len(wow[0]) > 39:
                raise InvalidSetting(f"Invalid Station ID '{wow[0]}'")
            else:
                raise InvalidSetting(f"Invalid Station key '{wow[1]}'")

    def write_custom(self, *custom):
        """Write 'Custom' upload parameters.

        Write 'Custom' upload parameters to a gateway device. The 'Custom'
        parameters consist of:
        enabled:
'ENABLED', 'PROTOCOL', 'SERVER', 'EC_PATH', 'WU_PATH', 'PORT',
                                       'INTERVAL', 'STATION_ID', 'STATION_KEY'

        The upload parameters are first encoded to produce the command data
        payload. The payload is then passed to a GatewayApi object for
        uploading to the gateway device.
        """

        # do we have a valid interval value
        if 0 <= len(custom[0]) <= 39 and 0 <= len(custom[1]) <= 32:
            # we have valid data, encode to produce the data payload
            payload_custom = self.gateway_api_parser.encode_custom(*custom)
            payload_paths = self.gateway_api_parser.encode_custom_paths(*custom)
            # update the gateway device
            self.gateway_api.set_custom(payload_custom)
            self.gateway_api.set_custom_paths(payload_paths)
        else:
            # we have an invalid interval setting, raise an InvalidSetting
            # exception with a suitable message
            if len(custom[0]) > 39:
                raise InvalidSetting(f"Invalid Station ID '{custom[0]}'")
            else:
                raise InvalidSetting(f"Invalid Station key '{custom[1]}'")

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

class DirectGateway():
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
        self.ip_address = getattr(namespace, 'ip_address', None)
        self.port = getattr(namespace, 'port', None)
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
        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            temperature_comp = _rain_data.get('temperature_comp')
        # create a meaningful string for frequency representation
        freq_str = freq_decode.get(sys_params_dict['frequency'], 'Unknown')
        # if sensor_type is 0 there is a WH24 connected, if it's a 1 there
        # is a WH65
        _is_wh24 = sys_params_dict['sensor_type'] == 0
        # string to use in sensor type message
        _sensor_type_str = 'WH24' if _is_wh24 else 'WH65'
        # print the system parameters
        print()
        print(f'{"sensor type":>26}: {sys_params_dict["sensor_type"]} ({_sensor_type_str})')
        print(f'{"frequency":>26}: {sys_params_dict["frequency"]} ({freq_str})')
        if temperature_comp is not None:
            print(f'{"Temperature Compensation":>26}: {temperature_comp} '
                  f'({temperature_comp_decode.get(temperature_comp, "unknown")})')
        else:
            print(f'{"Temperature Compensation":>26}: unavailable')

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
        print(f'{"date-time":>26}: {date_time_str}')
        print(f'{"timezone index":>26}: {sys_params_dict["timezone_index"]}')
        print(f'{"DST status":>26}: {sys_params_dict["dst_status"]}')

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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
                print(f'{"Rainfall data priority":>26}: '
                      f'{source_lookup.get(rain_data["rain_priority"], "unknown selection")}')
                print()
            if any(field in rain_data for field in traditional):
                print(f'{"Traditional rain data":>26}:')
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
                print(f'{"Piezo rain data":>26}:')
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
                print(f'{"Rainfall reset time data:":>26}:')
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
                        channel_str = f'{"Channel":>11} {channel - 0x62:d}'
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
                    print(f'{"No PM2.5 sensors found":>26}')
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
            # identify the device being used
            print()
            print(f'Interrogating {Bcolors.BOLD}{device.model}{Bcolors.ENDC} '
                  f'at {Bcolors.BOLD}{device.ip_address}:{int(device.port):d}{Bcolors.ENDC}')
            # get the calibration data from the collector object's calibration
            # property
            calibration_data = device.calibration
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
                print(f'{"Irradiance gain":>26}: {calibration_data["solar"]:5.2f}')
                print(f'{"UV gain":>26}: {calibration_data["uv"]:4.1f}')
                print(f'{"Wind gain":>26}: {calibration_data["wind"]:4.1f}')
                print(f'{"Inside temperature offset":>26}: {calibration_data["intemp"]:4.1f} \xb0C')
                print(f'{"Inside humidity offset":>26}: {calibration_data["inhum"]:4.1f} %')
                print(f'{"Outside temperature offset":>26}: {calibration_data["outtemp"]:4.1f} \xb0C')
                print(f'{"Outside humidity offset":>26}: {calibration_data["outhum"]:4.1f} %')
                print(f'{"Absolute pressure offset":>26}: {calibration_data["abs"]:4.1f} hPa')
                print(f'{"Relative pressure offset":>26}: {calibration_data["rel"]:4.1f} hPa')
                print(f'{"Wind direction offset":>26}: {calibration_data["dir"]:4.1f} \xb0')
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
                key = data_dict['key'] if self.namespace.unmask else obfuscate(data_dict['key'])
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
                     'wunderground_params': print_wunderground,
                     'weathercloud_params': print_weathercloud,
                     'wow_params': print_wow,
                     'all_custom_params': print_custom}

        # wrap in a try..except in case there is an error
        try:
            # get a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port)
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
            for item_num in device.gateway_api_parser.live_data_struct.keys():
                if item_num in live_sensor_data_dict:
                    item_str = ''.join(['(', device.gateway_api_parser.live_data_struct[item_num][3], ')', ':'])
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
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
        try:
            device.write_ecowitt(self.namespace.ecowitt)
        except DeviceWriteFailed as e:
            print(f"Error: {e}")
        else:
            print("Device write completed successfully")

    def write_wu(self):
        """Write WeatherUnderground upload parameters to a gateway device."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
        try:
            device.write_wu(*self.namespace.wu)
        except DeviceWriteFailed as e:
            print(f"Error: {e}")
        else:
            print("Device write completed successfully")

    def write_wcloud(self):
        """Write Weathercloud upload parameters to a gateway device."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
        try:
            device.write_wcloud(*self.namespace.wcloud)
        except DeviceWriteFailed as e:
            print(f"Error: {e}")
        else:
            print("Device write completed successfully")

    def write_wow(self):
        """Write Weather Observations Website upload parameters to a gateway device."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
        try:
            device.write_wow(*self.namespace.wow)
        except DeviceWriteFailed as e:
            print(f"Error: {e}")
        else:
            print("Device write completed successfully")

    def write_custom(self):
        """Write 'Custom' upload parameters to a gateway device."""

        # wrap in a try..except in case there is an error
        try:
            # obtain a GatewayDevice object
            device = GatewayDevice(ip_address=self.ip_address, port=self.port, debug=self.debug)
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
        # do we have 9 (WU) or 7 (EC) parameters, if it's the latter read the current custom upload settings to obtain the current station ID and key
        if len(self.namespace.custom) == 7:
            _result = device.custom_params
            id = _result['id']
            password = _result['password']
            print(self.namespace.custom, id, password)
            # device.write_custom(*self.namespace.custom, id, password)
        elif len(self.namespace.custom) == 9:
            print(self.namespace.custom)
            # device.write_custom(*self.namespace.custom)
        else:
            # TODO.Need to fix this
            print("error")
            return
        try:
            device.write_custom(*self.namespace.custom)
        except DeviceWriteFailed as e:
            print(f"Error: {e}")
        else:
            print("Device write completed successfully")

def dispatch_get(namespace, parser):
    """Process 'get' subcommand."""

    # get a DirectGateway object
    direct_gw = DirectGateway(namespace)
    # process the command line arguments to determine what we should do
    if hasattr(namespace, 'sys_params') and namespace.sys_params:
        direct_gw.display_system_params()
    elif hasattr(namespace, 'rain_data') and namespace.rain_data:
        direct_gw.display_rain_data()
    elif hasattr(namespace, 'all_rain_data') and namespace.all_rain_data:
        direct_gw.display_all_rain_data()
    elif hasattr(namespace, 'mulch_calibration') and namespace.mulch_calibration:
        direct_gw.display_mulch_offset()
    elif hasattr(namespace, 'mulch_temp_calibration') and namespace.mulch_temp_calibration:
        direct_gw.display_mulch_t_offset()
    elif hasattr(namespace, 'pm25_calibration') and namespace.pm25_calibration:
        direct_gw.display_pm25_offset()
    elif hasattr(namespace, 'co2_calibration') and namespace.co2_calibration:
        direct_gw.display_co2_offset()
    elif hasattr(namespace, 'calibration') and namespace.calibration:
        direct_gw.display_calibration()
    elif hasattr(namespace, 'soil_calibration') and namespace.soil_calibration:
        direct_gw.display_soil_calibration()
    elif hasattr(namespace, 'services') and namespace.services:
        direct_gw.display_services()
    elif hasattr(namespace, 'mac') and namespace.mac:
        # TODO. Rename to remove 'station' ?
        direct_gw.display_station_mac()
    elif hasattr(namespace, 'firmware') and namespace.firmware:
        direct_gw.display_firmware()
    elif hasattr(namespace, 'sensors') and namespace.sensors:
        direct_gw.display_sensors()
    elif hasattr(namespace, 'live_data') and namespace.live_data:
        direct_gw.display_live_data()
    else:
        # we have no argument so display our subcommand help and return
        print()
        print("No option selected, nothing done")
        print()
        parser.print_help()

def dispatch_write(namespace, parser):
    """Process the 'write' subcommand."""

    # get a DirectGateway object
    direct_gw = DirectGateway(namespace)
    # process the command line arguments to determine what we should do
    if hasattr(namespace, 'ecowitt') and namespace.ecowitt is not None:
        direct_gw.write_ecowitt()
    elif hasattr(namespace, 'wu') and namespace.wu is not None:
        direct_gw.write_wu()
    elif hasattr(namespace, 'wcloud') and namespace.wcloud is not None:
        direct_gw.write_wcloud()
    elif hasattr(namespace, 'wow') and namespace.wow is not None:
        direct_gw.write_wow()
    elif hasattr(namespace, 'custom') and namespace.custom is not None:
        direct_gw.write_custom()
    else:
        # we have no argument so display our subcommand help and return
        print()
        print("No option selected, nothing done")
        print()
        parser.print_help()

def dispatch_ecowitt_write(namespace, parser):
    pass

def dispatch_wu_write(namespace, parser):
    pass

def dispatch_wow_write(namespace, parser):
    pass

def dispatch_wcloud_write(namespace, parser):
    pass

def dispatch_custom_write(namespace, parser):
    pass

def add_common_args(parser):
    """Add common arguments to an argument parser."""

    parser.add_argument('--ip-address',
                        dest='ip_address',
                        help='device IP address to use')
    parser.add_argument('--port',
                        dest='port',
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

def get_subparser(subparsers):
    """Add get subcommand."""

    get_usage = f"""{Bcolors.BOLD}ecowitt get --help
       ecowitt get --live-data | --sensors
                   [--ip-address=IP_ADDRESS] [--port=PORT]
                   [--show-all-batt] [--debug]
       ecowitt get --firmware | --mac-address |
                   --system-params | --rain-data | --all-rain-data
                   [--ip-address=IP_ADDRESS] [--port=PORT]
                   [--debug]
       ecowitt get --calibration | --mulch-th-cal | --mulch-soil-cal |
                   --pm25-cal | --co2-cal
                   [--ip-address=IP_ADDRESS] [--port=PORT]
                   [--debug]
       ecowitt get --services
                   [--ip-address=IP_ADDRESS] [--port=PORT]
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
    get_parser.add_argument('--ip-address',
                            dest='ip_address',
                            help='device IP address to use')
    get_parser.add_argument('--port',
                            dest='port',
                            type=int,
                            default=45000,
                            help='device port to use')
    get_parser.add_argument('--max-tries',
                            dest='max_tries',
                            type=int,
                            help='max number of attempts to contact the device')
    get_parser.add_argument('--retry-wait',
                            dest='retry_wait',
                            type=int,
                            help='how long to wait between attempts to contact the device')
    get_parser.add_argument('--show-all-batt',
                            dest='show_battery',
                            action='store_true',
                            help='show all available battery state data regardless of '
                                 'sensor state')
    get_parser.add_argument('--unmask',
                            dest='unmask',
                            action='store_true',
                            help='unmask sensitive settings')
    get_parser.add_argument('--debug',
                            dest='debug',
                            action='store_true',
                            help='display additional debug information')

    get_parser.set_defaults(func=dispatch_get)
    return get_parser

def ecowitt_write_subparser(subparsers):
    """Define 'ecowitt write ecowitt' sub-subparser."""
    
    ecowitt_write_usage = f"""{Bcolors.BOLD}ecowitt write ecowitt --help
       ecowitt write ecowitt --interval INTERVAL
            --ip-address=IP_ADDRESS [--port=PORT]
            [--debug]{Bcolors.ENDC}
    """
    ecowitt_write_description = """Update Ecowitt.net upload parameters."""
    ecowitt_write_parser = subparsers.add_parser('ecowitt',
                                                 usage=ecowitt_write_usage,
                                                 description=ecowitt_write_description,
                                                 help="Update Ecowitt.net upload parameters.")
    ecowitt_write_parser.add_argument('--interval',
                                      dest='interval',
                                      type=int,
                                      choices=range(0, 6),
                                      default=0,
                                      metavar='INTERVAL',
                                      help='Ecowitt.net upload interval (0-5) in minutes. '
                                           '0 indicates upload is disabled. Default is 0.')
    add_common_args(ecowitt_write_parser)
    ecowitt_write_parser.set_defaults(func=dispatch_ecowitt_write)
    return ecowitt_write_parser


def wu_write_subparser(subparsers):
    """Define 'ecowitt write wu' sub-subparser."""

    wu_write_usage = f"""{Bcolors.BOLD}ecowitt write wu --help
       ecowitt write wu --station-id STATION_ID --station-key STATION_KEY
                        --ip-address=IP_ADDRESS [--port=PORT] [--debug]{Bcolors.ENDC}
    """
    wu_write_description = """Update WeatherUnderground upload parameters."""
    wu_write_parser = subparsers.add_parser('wu',
                                            usage=wu_write_usage,
                                            description=wu_write_description,
                                            help="Update various Ecowitt gateway device configuration settings.")
    wu_write_parser.add_argument('--station-id',
                                 dest='id',
                                 metavar='STATION_ID',
                                 help='WeatherUnderground station ID')
    wu_write_parser.add_argument('--station-key',
                                 dest='key',
                                 metavar='STATION_KEY',
                                 help='WeatherUnderground station key')
    add_common_args(wu_write_parser)
    wu_write_parser.set_defaults(func=dispatch_wu_write)
    return wu_write_parser

def wow_write_subparser(subparsers):
    """Define 'ecowitt write wow' sub-subparser."""

    wow_write_usage = f"""{Bcolors.BOLD}ecowitt write wow --help
       ecowitt write wow --station-id STATION_ID --station-key STATION_KEY
                         --ip-address=IP_ADDRESS [--port=PORT] [--debug]{Bcolors.ENDC}
    """
    wow_write_description = """Update Weather Observations Website upload parameters."""
    wow_write_parser = subparsers.add_parser('wow',
                                            usage=wow_write_usage,
                                            description=wow_write_description,
                                            help="Update various Ecowitt gateway device configuration settings.")
    wow_write_parser.add_argument('--station-id',
                                 dest='id',
                                 metavar='STATION_ID',
                                 help='Weather Observations Website station ID')
    wow_write_parser.add_argument('--station-key',
                                 dest='key',
                                 metavar='STATION_KEY',
                                 help='Weather Observations Website station key')
    add_common_args(wow_write_parser)
    wow_write_parser.set_defaults(func=dispatch_wow_write)
    return wow_write_parser

def wcloud_write_subparser(subparsers):
    """Define 'ecowitt write wcloud' sub-subparser."""

    wcloud_write_usage = f"""{Bcolors.BOLD}ecowitt write wcloud --help
       ecowitt write wcloud --station-id STATION_ID --station-key STATION_KEY
                            --ip-address=IP_ADDRESS [--port=PORT] [--debug]{Bcolors.ENDC}
    """
    wcloud_write_description = """Update Weathercloud upload parameters."""
    wcloud_write_parser = subparsers.add_parser('wcloud',
                                                usage=wcloud_write_usage,
                                                description=wcloud_write_description,
                                                help="Update various Ecowitt gateway device configuration settings.")
    wcloud_write_parser.add_argument('--station-id',
                                     dest='id',
                                     metavar='STATION_ID',
                                     help='Weathercloud station ID')
    wcloud_write_parser.add_argument('--station-key',
                                     dest='key',
                                     metavar='STATION_KEY',
                                     help='Weathercloud station key')
    add_common_args(wcloud_write_parser)
    wcloud_write_parser.set_defaults(func=dispatch_wcloud_write)
    return wcloud_write_parser

def maxlen_40(arg):
    if len(arg) <= 40:
        return arg
    else:
        raise argparse.ArgumentTypeError("Argument length must be 64 characters or less")

def maxlen_64(arg):
    if len(arg) <= 64:
        return arg
    else:
        raise argparse.ArgumentTypeError("Argument length must be 64 characters or less")

def custom_write_subparser(subparsers):
    """Define 'ecowitt write custom' sub-subparser."""

    custom_write_usage = f"""{Bcolors.BOLD}ecowitt write custom --help
       ecowitt write custom --ip-address=IP_ADDRESS [--port=PORT]
                            [--enabled] [--protocol EC | WU] [--server IP_ADDRESS | NAME] 
                            [--upload-port UPLOAD_PORT] [--interval INTERVAL] 
                            [--ec-path EC_PATH] [--wu-path WU_PATH] 
                            [--station-id STATION_ID] [--station-key STATION_KEY]
                            [--debug]{Bcolors.ENDC}
    """
    custom_write_description = """Update Customized upload parameters. If a 
    parameter is omitted the corresponding current gateway device parameter is 
    left unchanged."""
    custom_write_parser = subparsers.add_parser('custom',
                                                usage=custom_write_usage,
                                                description=custom_write_description)
    custom_write_parser.add_argument('--enabled',
                                     action='store_true',
                                     help='enable customized uploads')
    custom_write_parser.add_argument('--disabled',
                                     dest='enabled',
                                     action='store_false',
                                     help='disable customized uploads')
    custom_write_parser.add_argument('--protocol',
                                     dest='protocol',
                                     choices=('EC', 'WU'),
                                     metavar='PROTOCOL',
                                     help='upload protocol EC = Ecowitt WU = WeatherUnderground '
                                          '(WU requires --station-id and --station-key be populated)')
    custom_write_parser.add_argument('--server',
                                     dest='server',
                                     type=maxlen_64,
                                     metavar='IP_ADDRESS | NAME',
                                     help='destination server IP address or host name, max length 64 characters')
    custom_write_parser.add_argument('--upload-port',
                                     dest='up_port',
                                     type=int,
                                     choices=range(0, 65537),
                                     metavar='UPLOAD_PORT',
                                     help='destination server port number')
    custom_write_parser.add_argument('--ec-path',
                                     dest='ec_path',
                                     type=maxlen_64,
                                     metavar='EC_PATH',
                                     help='Ecowitt protocol upload path')
    custom_write_parser.add_argument('--wu-path',
                                     dest='wu_path',
                                     type=maxlen_64,
                                     metavar='WU_PATH',
                                     help='WeatherUnderground protocol upload path')
    custom_write_parser.add_argument('--station-id',
                                     dest='id',
                                     type=maxlen_40,
                                     metavar='STATION_ID',
                                     help='WeatherUnderground protocol station ID')
    custom_write_parser.add_argument('--station-key',
                                     dest='key',
                                     type=maxlen_40,
                                     metavar='STATION_KEY',
                                     help='WeatherUnderground protocol station key')
    custom_write_parser.add_argument('--interval',
                                     dest='interval',
                                     type=int,
                                     choices=range(16, 601),
                                     metavar='UPLOAD_PORT',
                                     help='destination server port number')
    add_common_args(custom_write_parser)
    custom_write_parser.set_defaults(enabled=False, func=dispatch_custom_write)
    return custom_write_parser


def write_subparser(subparsers):
    """Add 'write' subcommand."""

    write_usage = f"""{Bcolors.BOLD}ecowitt write --help
       ecowitt write --custom ENABLED PROTOCOL SERVER PATH
            PORT KEY ECOWITT_PATH WU_PATH
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug]{Bcolors.ENDC}
    """
    write_description = """Update various Ecowitt gateway device configuration settings."""

    write_parser = subparsers.add_parser('write',
                                         usage=write_usage,
                                         description=write_description,
                                         help="Update various Ecowitt gateway device configuration settings.")
    # add a subparser to handle the various subcommands.
    write_subparsers = write_parser.add_subparsers(dest='write_subcommand',
                                                   title="Available subcommands")
    ecowitt_write_subparser(write_subparsers)
    wu_write_subparser(write_subparsers)
    wow_write_subparser(write_subparsers)
    wcloud_write_subparser(write_subparsers)
    custom_write_subparser(write_subparsers)
    write_parser.set_defaults(func=dispatch_write)
    return write_parser


# To use this utility use the following command:
#
#   $ python3 /path/to/ecowitt.py --help
#
# The above command will display available command line options.

def main():

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
    # inform the user if debug is set
    if int(namespace.debug):
        print(f"debug is set")
    # do we have a subcommand function we can call
    if hasattr(namespace, 'func'):
        # we have a subcommand function, so call it
        namespace.func(namespace, parsers[namespace.subcommand])
    else:
        # process any top level namespace arguments/actions
        if namespace.version:
            # display the utility version
            print(f"{NAME} version {VERSION}")
            sys.exit(0)
        # a subcommand has not been specified, did we get any arguments?
        elif namespace.discover:
            # discover gateway devices and display the results
            # firs, get a DirectGateway object
            direct_gw = DirectGateway(namespace)
            # discover any gateway devices and display the results
            direct_gw.display_discovered_devices()
        else:
            # we have no action arguments, display the top level help text and
            # exit
            parser.print_help()
            sys.exit(0)


if __name__ == '__main__':
    main()