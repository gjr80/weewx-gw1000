#!/usr/bin/env python
"""
gw1000.py

A WeeWX driver for the Ecowitt GW1000 Wi-Fi Gateway API.

The WeeWX GW1000 driver utilise the GW1000 API thus using a pull methodology for
obtaining data from the GW1000 rather than the push methodology used by current
drivers. This has the advantage of giving the user more control over when the
data is obtained from the GW1000 plus also giving access to a greater range of
metrics.

The GW1000 driver can be operated as a traditional WeeWX driver where it is the
source of loop data or it can be operated as a WeeWX service where it is used
to augment loop data produced by another driver.

Copyright (C) 2020 Gary Roderick                   gjroderick<at>gmail.com

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see http://www.gnu.org/licenses/.

Version: 0.2.0                                    Date: 9 January 2021

Revision History
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


Before using this driver:

Before running WeeWX with the GW1000 driver you may wish to run the driver
directly from the command line to ensure correct operation/assist in
configuration. To run the driver directly from the command line enter one of
the following commands depending on your WeeWX installation type:

    for a setup.py install:

        $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --help

    or for package installs use:

        $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --help

Note: Depending on your system/installation the above command may need to be
      prefixed with sudo.

Note: Whilst the driver may be run independently of WeeWX the driver still
      requires WeeWX and it's dependencies be installed. Consequently, if
      WeeWX 4.0.0 or later is installed the driver must be run under the same
      Python version as WeeWX uses. This means that on some systems 'python' in
      the above commands may need to be changed to 'python2' or 'python3'.

Note: The nature of the GW1000 API and the GW1000 driver mean that the GW1000
      driver can be run directly from the command line while the GW1000
      continues to serve data to any existing drivers/services. This makes it
      possible to configure and test the GW1000 driver without taking an
      existing GW1000 based system off-line.

The --discover command line option is useful for discovering any GW1000 on the
local network. The IP address and port details returned by --discover can be
useful for configuring the driver IP address and port config options in
weewx.conf.

The --live-data command line option is useful for seeing what data is available
from a particular GW1000. Note the fields available will depend on the sensors
connected to the GW1000. As the field names returned by --live-data are GW1000
field names before they have been mapped to WeeWX fields names, the --live-data
output is useful for configuring the field map to be used by the GW1000 driver.

Once you believe the GW1000 driver is configured the --test-driver or
--test-service command line options can be used to confirm correct operation of
the GW1000 driver as a driver or as a service respectively.


To use the GW1000 driver as a WeeWX driver:

1.  If installing on a fresh WeeWX installation install WeeWX and configure it
to use the 'simulator'. Refer to http://weewx.com/docs/usersguide.htm#installing

2.  If installing the driver using the wee_extension utility (the recommended
method):

    -   download the GW1000 driver extension package:

        $ wget -P /var/tmp https://github.com/gjr80/weewx-gw1000/releases/download/v0.1.0/gw1000-0.1.0.tar.gz

    -   install the GW1000 driver extension:

        $ wee_extension --install=/var/tmp/gw1000-0.1.0.tar.gz

        Note: Depending on your system/installation the above command may need
              to be prefixed with sudo.

        Note: Depending on your WeeWX installation wee_extension may need to be
              prefixed with the path to wee_extension.

    -   skip to step 4

3.  If installing manually:

    -   put this file in $BIN_ROOT/user.

    -   add the following stanza to weewx.conf:

        [GW1000]
            # This section is for the GW1000

            # The driver itself
            driver = user.gw1000

    -   add the following stanza to weewx.conf:

        Note: If an [Accumulator] stanza already exists in weewx.conf just add
              the child settings.

        [Accumulator]
            [[lightning_strike_count]]
                extractor = sum
            [[lightning_last_det_time]]
                extractor = last
            [[daymaxwind]]
                extractor = last
            [[lightning_distance]]
                extractor = last
            [[stormRain]]
                extractor = last
            [[hourRain]]
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

4.  Confirm that WeeWX is set to use software record generation
(refer http://weewx.com/docs/usersguide.htm#record_generation). In weewx.conf
under [StdArchive] ensure the record_generation setting is set to software:

        [StdArchive]
            ....
            record_generation = software

    If record_generation is set to hardware change it to software.

5.  Test the GW1000 driver by running the driver file directly using the
--test-driver command line option:

    $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --test-driver

    for setup.py installs or for package installs use:

    $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --test-driver

    Note: Depending on your system/installation the above command may need to be
          prefixed with sudo.

    Note: Whilst the driver may be run independently of WeeWX the driver still
          requires WeeWX and it's dependencies be installed. Consequently, if
          WeeWX 4.0.0 or later is installed the driver must be run under the
          same Python version as WeeWX uses. This means that on some systems
          'python' in the above commands may need to be changed to 'python2' or
          'python3'.

    Note: If necessary you can specify the GW1000 IP address and port using the
          --ip-address and --port command line options. Refer to the GW1000
          driver help using --help for further information.

    You should observe loop packets being emitted on a regular basis. Once
    finished press ctrl-c to exit.

    Note: You will only see loop packets and not archive records when running
          the driver directly. This is because you are seeing output directly
          from the driver and not WeeWX.

6.  Configure the driver:

    $ wee_config --reconfigure --driver=user.gw1000

    Note: Depending on your system/installation the above command may need to
          be prefixed with sudo.

    Note: Depending on your WeeWX installation wee_config may need to be
          prefixed with the path to wee_config.

7.  You may chose to run WeeWX directly (refer http://weewx.com/docs/usersguide.htm#Running_directly)
to observe the loop packets and archive records being generated by WeeWX.

8.  Once satisfied that the GW1000 driver is operating correctly you can start
the WeeWX daemon:

    $ sudo /etc/init.d/weewx start

    or

    $ sudo service weewx start

    or

    $ sudo systemctl start weewx


To use the GW1000 driver as a WeeWX service:

1.  Install WeeWX and configure it to use either the 'simulator' or another
driver of your choice. Refer to http://weewx.com/docs/usersguide.htm#installing.

2.  Install the GW1000 driver using the wee_extension utility (preferred) as
per 'To use the GW1000 driver as a WeeWX driver' step 2 above. If installing
manually copy this file to the $BIN_ROOT/user directory and then add the
[Accumulator] entries to weewx.conf as per 'To use the GW1000 driver as a WeeWX
driver' step 3 above.

3.  Under the [Engine] [[Services]] stanza in weewx.conf add an entry
'user.gw1000.Gw1000Service' to the data_services option. It should look
something like:

[Engine]

    [[Services]]
        ....
        data_services = user.gw1000.Gw1000Service

5.  Test the now configured GW1000 service using the --test-service command
line option. You should observe loop packets being emitted on a regular basis
that include GW1000 data. Note that depending on the frequency of the loop
packets emitted by the in-use driver and the polling interval of the GW1000
service it is likely that not all loop packets will include GW1000 data.

7.  You may chose to run WeeWX directly to observe the loop packets and archive
records being generated by WeeWX. Refer to
http://weewx.com/docs/usersguide.htm#Running_directly. Note that depending on
the frequency of the loop packets emitted by the in-use driver and the polling
interval of the GW1000 service it is likely that not all loop packets will
include GW1000 data.

8.  Once satisfied that the GW1000 service is operating correctly you can start
the WeeWX daemon:

    $ sudo /etc/init.d/weewx restart

    or

    $ sudo service weewx restart

    or

    $ sudo systemctl restart weewx
"""

# Standing TODOs:
# TODO. Review against latest
# TODO. Confirm WH26/WH32 sensor ID
# TODO. Confirm sensor ID signal value meaning
# TODO. Confirm sensor ID battery meaning
# TODO. Confirm WH26/WH32 battery status
# TODO. Confirm WH68 battery status
# TODO. Confirm WS80 battery status
# TODO. Confirm WH55 battery status
# TODO. Confirm WH24 battery status
# TODO. Confirm WH25 battery status
# TODO. Confirm WH40 battery status
# TODO. Need to know date-time data format for decode date_time()
# TODO. Need to implement debug_wind reporting
# TODO. Review queue dwell times
# TODO. Move decoding of any response from GW1000 API to class Parser()

# Python imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

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
DRIVER_VERSION = '0.2.0'

# various defaults used throughout
# default port used by GW1000
default_port = 45000
# default network broadcast address - the address that network broadcasts are
# sent to
default_broadcast_address = '255.255.255.255'
# default network broadcast port - the port that network broadcasts are sent to
default_broadcast_port = 46000
# default socket timeout
default_socket_timeout = 2
# default retry/wait time
default_retry_wait = 10
# default max tries when polling the API
default_max_tries = 3
# When run as a service the default age in seconds after which GW1000 API data
# is considered stale and will not be used to augment loop packets
default_max_age = 60
# default GW1000 poll interval
default_poll_interval = 20
# default period between lost contact log entries during an extended period of
# lost contact when run as a Service
default_lost_contact_log_period = 21600


# ============================================================================
#                          GW1000 API error classes
# ============================================================================


class InvalidApiResponse(Exception):
    """Exception raised when an API call response is invalid."""


class InvalidChecksum(Exception):
    """Exception raised when an API call response contains an invalid
    checksum."""


class GW1000IOError(Exception):
    """Exception raised when an input/output error with the GW1000 is
    encountered."""


class UnknownCommand(Exception):
    """Exception raised when an unknown API command is used."""


# ============================================================================
#                               class Gw1000
# ============================================================================


class Gw1000(object):
    """Base class for interacting with a GW1000.

    There are a number of common properties and methods (eg IP address,
    field map, rain calculation etc) when dealing with a GW1000 either as a
    driver or service. This class captures those common features.
    """

    # Default field map to map GW1000 sensor data to WeeWX fields. WeeWX field
    # names are used where there is a direct correlation to the WeeWX
    # wview_extended schema or weewx.units.obs_group_dict otherwise fields are
    # passed passed through as is.
    # Format is:
    #   WeeWX field name: GW1000 field name
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
        'lightning_strike_count': 'lightning_strike_count'
    }
    # Rain related fields default field map, merged into default_field_map to
    # give the overall default field map. Kept separate to make it easier to
    # iterate over rain related fields.
    rain_field_map = {
        'rain': 'rain',
        'stormRain': 'rainevent',
        'rainRate': 'rainrate',
        'hourRain': 'rainhour',
        'dayRain': 'rainday',
        'weekRain': 'rainweek',
        'monthRain': 'rainmonth',
        'yearRain': 'rainyear',
        'totalRain': 'raintotals',
    }
    # wind related fields default field map, merged into default_field_map to
    # give the overall default field map. Kept separate to make it easier to
    # iterate over wind related fields.
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
        'wh65_batt': 'wh65_batt',
        'wh31_ch1_batt': 'wh31_ch1_batt',
        'wh31_ch2_batt': 'wh31_ch2_batt',
        'wh31_ch3_batt': 'wh31_ch3_batt',
        'wh31_ch4_batt': 'wh31_ch4_batt',
        'wh31_ch5_batt': 'wh31_ch5_batt',
        'wh31_ch6_batt': 'wh31_ch6_batt',
        'wh31_ch7_batt': 'wh31_ch7_batt',
        'wh31_ch8_batt': 'wh31_ch8_batt',
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
        'ws80_batt': 'ws80_batt'
    }
    # sensor signal level default field map, merged into default_field_map to
    # give the overall default field map
    sensor_signal_field_map = {
        'wh40_sig': 'wh40_sig',
        'wh26_sig': 'wh26_sig',
        'wh25_sig': 'wh25_sig',
        'wh65_sig': 'wh65_sig',
        'wh31_ch1_sig': 'wh31_ch1_sig',
        'wh31_ch2_sig': 'wh31_ch2_sig',
        'wh31_ch3_sig': 'wh31_ch3_sig',
        'wh31_ch4_sig': 'wh31_ch4_sig',
        'wh31_ch5_sig': 'wh31_ch5_sig',
        'wh31_ch6_sig': 'wh31_ch6_sig',
        'wh31_ch7_sig': 'wh31_ch7_sig',
        'wh31_ch8_sig': 'wh31_ch8_sig',
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
        'ws80_sig': 'ws80_sig'
    }

    def __init__(self, **gw1000_config):
        """Initialise a GW1000 object."""

        # construct the field map, first obtain the field map from our config
        field_map = gw1000_config.get('field_map')
        # obtain any field map extensions from our config
        extensions = gw1000_config.get('field_map_extensions', {})
        # if we have no field map then use the default
        if field_map is None:
            # obtain the default field map
            field_map = dict(Gw1000.default_field_map)
            # now add in the rain field map
            field_map.update(Gw1000.rain_field_map)
            # now add in the wind field map
            field_map.update(Gw1000.wind_field_map)
            # now add in the battery state field map
            field_map.update(Gw1000.battery_field_map)
            # now add in the sensor signal field map
            field_map.update(Gw1000.sensor_signal_field_map)
        # If a user wishes to map a GW1000 field differently to that in the
        # default map they can include an entry in field_map_extensions, but if
        # we just update the field map dict with the field map extensions that
        # leaves two entries for that GW1000 field in the field map; the
        # original field map entry as well as the entry from the extended map.
        # So if we have field_map_extensions we need to first go through the
        # field map and delete any entries that map GW1000 fields that are
        # included in the field_map_extensions.
        # we only need process the field_map_extensions if we have any
        if len(extensions) > 0:
            # first make a copy of the field map because we will be iterating
            # over it and changing it
            field_map_copy = dict(field_map)
            # iterate over each key, value pair in the copy of the field map
            for k, v in six.iteritems(field_map_copy):
                # if the 'value' (ie the GW1000 field) is in the field map
                # extensions we will be mapping that GW1000 field elsewhere so
                # pop that field map entry out of the field map so we don't end
                # up with multiple mappings for a GW1000 field
                if v in extensions.values():
                    # pop the field map entry
                    _dummy = field_map.pop(k)
            # now we can update the field map with the extensions
            field_map.update(extensions)
        # we now have our final field map
        self.field_map = field_map
        # network broadcast address and port
        self.broadcast_address = str.encode(gw1000_config.get('broadcast_address',
                                                              default_broadcast_address))
        self.broadcast_port = gw1000_config.get('broadcast_port',
                                                default_broadcast_port)
        self.socket_timeout = gw1000_config.get('socket_timeout',
                                                default_socket_timeout)
        # obtain the GW1000 ip address
        _ip_address = gw1000_config.get('ip_address')
        # if the user has specified some variation of 'auto' then we are to
        # automatically detect the GW1000 IP address, to do that we set the
        # ip_address property to None
        if _ip_address is not None and _ip_address.lower() == 'auto':
            # we need to autodetect ip address so set to None
            _ip_address = None
        # set the ip address property
        self.ip_address = _ip_address
        # obtain the GW1000 port from the config dict
        # for port number we have a default value we can use, so if port is not
        # specified use the default
        _port = gw1000_config.get('port', default_port)
        # if a port number was specified it needs to be an integer not a string
        # so try to do the conversion
        try:
            _port = int(_port)
        except TypeError:
            # most likely port somehow ended up being None, in any case force
            # autodetection by setting port to None
            _port = None
        except ValueError:
            # We couldn't convert the port number to an integer. Maybe it was
            # because it was 'auto' (or some variation) or perhaps it was
            # invalid. Either way we need to set port to None to force
            # autodetection. If there was an invalid port specified then log it.
            if _port.lower() != 'auto':
                loginf("Invalid GW1000 port '%s' specified, port will be autodetected" % (_port,))
            _port = None
        # set the port property
        self.port = _port
        # how many times to poll the API before giving up, default is
        # default_max_tries
        self.max_tries = int(gw1000_config.get('max_tries', default_max_tries))
        # wait time in seconds between retries, default is default_retry_wait
        # seconds
        self.retry_wait = int(gw1000_config.get('retry_wait',
                                                default_retry_wait))
        # how often (in seconds) we should poll the API, use a default
        self.poll_interval = int(gw1000_config.get('poll_interval',
                                                   default_poll_interval))
        # Is a WH32 in use. WH32 TH sensor can override/provide outdoor TH data
        # to the GW1000. In tems of TH data the process is transparent and we
        # do not need to know if a WH32 or other sensor is providing outdoor TH
        # data but in terms of battery state we need to know so the battery
        # state data can be reported against the correct sensor.
        use_th32 = weeutil.weeutil.tobool(gw1000_config.get('th32', False))
        # get any GW1000 specific debug settings
        # rain
        self.debug_rain = weeutil.weeutil.tobool(gw1000_config.get('debug_rain',
                                                                   False))
        # wind
        self.debug_wind = weeutil.weeutil.tobool(gw1000_config.get('debug_wind',
                                                                   False))
        # loop data
        self.debug_loop = weeutil.weeutil.tobool(gw1000_config.get('debug_loop',
                                                                   False))
        # create an Gw1000Collector object to interact with the GW1000 API
        self.collector = Gw1000Collector(ip_address=self.ip_address,
                                         port=self.port,
                                         broadcast_address=self.broadcast_address,
                                         broadcast_port=self.broadcast_port,
                                         socket_timeout=self.socket_timeout,
                                         poll_interval=self.poll_interval,
                                         max_tries=self.max_tries,
                                         retry_wait=self.retry_wait,
                                         use_th32=use_th32,
                                         debug_rain=self.debug_rain,
                                         debug_wind=self.debug_wind)
        # initialise last lightning count and last rain properties
        self.last_lightning = None
        self.last_rain = None
        self.rain_mapping_confirmed = False
        self.rain_total_field = None
        # Finally, log any config that is not being pushed any further down.
        # GW1000 specific debug but only if set ie. True
        debug_list = []
        if self.debug_rain:
            debug_list.append("debug_rain is %s" % (self.debug_rain,))
        if self.debug_wind:
            debug_list.append("debug_wind is %s" % (self.debug_wind,))
        if self.debug_loop:
            debug_list.append("debug_loop is %s" % (self.debug_loop,))
        if len(debug_list) > 0:
            loginf(" ".join(debug_list))
        # The field map. Field map dict output will be in unsorted key order.
        # It is easier to read if sorted alphanumerically but we have keys such
        # as xxxxx16 that do not sort well. Use a custom natural sort of the
        # keys in a manually produced formatted dict representation.
        loginf('field map is %s' % natural_sort_dict(self.field_map))

    def map_data(self, data):
        """Map parsed GW1000 data to a WeeWX loop packet.

        Maps parsed GW1000 data to WeeWX loop packet fields using the field map.
        Result includes usUnits field set to METRICWX.

        data: Dict of parsed GW1000 API data
        """

        # parsed GW1000 API data uses the METRICWX unit system
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
        """Log rain related data from the collector."""

        msg_list = []
        # iterate over our rain_field_map values, these are the GW1000 'fields'
        # we are interested in
        for gw1000_rain_field in Gw1000.rain_field_map.values():
            # do we have a field of interest
            if gw1000_rain_field in data:
                # we do so add some formatted output to our list
                msg_list.append("%s=%s" % (gw1000_rain_field,
                                           data[gw1000_rain_field]))
        # pre-format the log line label
        label = "%s: " % preamble if preamble is not None else ""
        # if we have some entries log them otherwise provide suitable text
        if len(msg_list) > 0:
            loginf("%s%s" % (label, " ".join(msg_list)))
        else:
            loginf("%sno rain data found" % (label,))

    def get_cumulative_rain_field(self, data):
        """Determine the cumulative rain field used to derive field 'rain'.

        Ecowitt rain gauges/GW1000 emit various rain totals but WeeWX needs a
        per period value for field rain. Try the 'big' (4 byte) counters
        starting at the longest period and working our way down. This should
        only need be done once.

        data: dic of parsed GW1000 API data
        """

        # if raintotals is present used that as our first choice
        if 'raintotals' in data:
            self.rain_total_field = 'raintotals'
            self.rain_mapping_confirmed = True
        # raintotals is not present so now try rainyear
        elif 'rainyear' in data:
            self.rain_total_field = 'rainyear'
            self.rain_mapping_confirmed = True
        # rainyear is not present so now try rainmonth
        elif 'rainmonth' in data:
            self.rain_total_field = 'rainmonth'
            self.rain_mapping_confirmed = True
        # otherwise do nothing, we can try again next packet
        else:
            self.rain_total_field = None
        # if we found a field log what we are using
        if self.rain_mapping_confirmed:
            loginf("Using '%s' for rain total" % self.rain_total_field)
        elif self.debug_rain:
            # if debug_rain is set log that we had nothing
            loginf("No suitable field found for rain total")

    def calculate_rain(self, data):
        """Calculate total rainfall for a period.

        'rain' is calculated as the change in a user designated cumulative rain
        field between successive periods. 'rain' is only calculated if the
        field to be used has been selected and the designated field exists.

        data: dict of parsed GW1000 API data
        """

        # have we decided on a field to use and is the field present
        if self.rain_mapping_confirmed and self.rain_total_field in data:
            # yes on both counts, so get the new total
            new_total = data[self.rain_total_field]
            # now calculate field rain as the difference between the new and
            # old totals
            data['rain'] = self.delta_rain(new_total, self.last_rain)
            # if debug_rain is set log some pertinent values
            if self.debug_rain:
                loginf("calculate_rain: last_rain=%s new_total=%s calculated rain=%s" % (self.last_rain,
                                                                                         new_total,
                                                                                         data['rain']))
            # save the new total as the old total for next time
            self.last_rain = new_total

    def calculate_lightning_count(self, data):
        """Calculate total lightning strike count for a period.

        'lightning_strike_count' is calculated as the change in field
        'lightningcount' between successive periods. 'lightning_strike_count'
        is only calculated if 'lightningcount' exists.

        data: dict of parsed GW1000 API data
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
    def delta_rain(rain, last_rain):
        """Calculate rainfall from successive cumulative values.

        Rainfall is calculated as the difference between two cumulative values.
        If either value is None the value None is returned. If the previous
        value is greater than the latest value a counter wrap around is assumed
        and the latest value is returned.

        rain:      current cumulative rain value
        last_rain: last cumulative rain value
        """

        # do we have a last rain value
        if last_rain is None:
            # no, log it and return None
            loginf("skipping rain measurement of %s: no last rain" % rain)
            return None
        # do we have a non-None current rain value
        if rain is None:
            # no, log it and return None
            loginf("skipping rain measurement: no current rain")
            return None
        # is the last rain value greater than the current rain value
        if rain < last_rain:
            # it is, assume a counter wrap around/reset, log it and return the
            # latest rain value
            loginf("rain counter wraparound detected: new=%s last=%s" % (rain, last_rain))
            return rain
        # otherwise return the difference between the counts
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


class Gw1000Service(weewx.engine.StdService, Gw1000):
    """GW1000 service class.

    A WeeWX service to augment loop packets with observational data obtained
    from the GW1000 API. Using the Gw1000Service is useful when data is
    required from more than one source, for example, WeeWX is using another
    driver and the Gw1000Driver cannot be used.

    Data is obtained from the GW1000 API. The data is parsed and mapped to
    WeeWX fields and if the GW1000 data is not stale the loop packets is
    augmented with the GW1000 mapped data.

    Class Gw1000Collector collects and parses data from the GW1000 API. The
    Gw1000Collector runs in a separate thread so as to not block the main WeeWX
    processing loop. The Gw1000Collector is turn uses child classes Station and
    Parser to interact directly with the GW1000 API and parse the API responses
    respectively.
    """

    def __init__(self, engine, config_dict):
        """Initialise a Gw1000Service object."""

        # extract the GW1000 service config dictionary
        gw1000_config_dict = config_dict.get('GW1000', {})
        # initialize my superclasses
        super(Gw1000Service, self).__init__(engine, config_dict)
        super(weewx.engine.StdService, self).__init__(**gw1000_config_dict)

        # age (in seconds) before API data is considered too old to use,
        # use a default
        self.max_age = int(gw1000_config_dict.get('max_age', default_max_age))
        # minimum period in seconds between 'lost contact' log entries during
        # an extended lost contact period
        self.lost_contact_log_period = int(gw1000_config_dict.get('lost_contact_log_period',
                                                                  default_lost_contact_log_period))
        # set failure logging on
        self.log_failures = True
        # reset the lost contact timestamp
        self.lost_con_ts = None
        # log our version number
        loginf('version is %s' % DRIVER_VERSION)
        # log the relevant settings/parameters we are using
        if self.ip_address is None and self.port is None:
            loginf("GW1000 IP address and port not specified, attempting to discover GW1000...")
        elif self.ip_address is None:
            loginf("GW1000 IP address not specified, attempting to discover GW1000...")
        elif self.port is None:
            loginf("GW1000 port not specified, attempting to discover GW1000...")
        loginf("GW1000 address is %s:%d" % (self.collector.station.ip_address.decode(),
                                            self.collector.station.port))
        loginf("poll interval is %d seconds" % self.poll_interval)
        logdbg('max tries is %d, retry wait time is %d seconds' % (self.max_tries,
                                                                   self.retry_wait))
        logdbg('broadcast address %s:%d, socket timeout is %d seconds' % (self.broadcast_address,
                                                                          self.broadcast_port,
                                                                          self.socket_timeout))
        loginf("max age of API data to be used is %d seconds" % self.max_age)
        loginf("lost contact will be logged every %d seconds" % self.lost_contact_log_period)
        # start the Gw1000Collector in its own thread
        self.collector.startup()
        # bind our self to the relevant weeWX events
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)

    def new_loop_packet(self, event):
        """Augment a loop packet with GW1000 data.

        When a new loop packet arrives check for any GW1000 data in the queue
        and if available and not stale map the data to WeeWX fields and use the
        mapped data to augment the loop packet.
        """

        # log the loop packet received if necessary, there are several debug
        # settings that may require this
        if self.debug_loop or self.debug_rain or self.debug_wind:
            loginf("Processing loop packet: %s %s" % (timestamp_to_string(event.packet['dateTime']),
                                                      natural_sort_dict(event.packet)))
        # Check the queue to get the latest GW1000 sensor data. Wrap in a try
        # to catch any instances where the queue is empty but also be prepared
        # to pop off any old records to get the most recent.
        try:
            # get any data from the collector queue, but don't dwell very long
            queue_data = self.collector.queue.get(True, 0.5)
        except six.moves.queue.Empty:
            # there was nothing in the queue so log it if required else continue
            if self.debug_loop or self.debug_rain or self.debug_wind:
                loginf("No queued GW1000 data to process")
            if self.lost_con_ts is not None and time.time() > self.lost_con_ts + self.lost_contact_log_period:
                self.lost_con_ts = time.time()
                self.set_failure_logging(True)
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

                # log the mapped data if necessary, there are several debug
                # settings that may require this, start from the highest (most
                # encompassing) and work to the lowest (least encompassing)
                if self.debug_loop:
                    if 'datetime' in queue_data:
                        loginf("Received GW1000 data: %s %s" % (timestamp_to_string(queue_data['datetime']),
                                                                natural_sort_dict(queue_data)))
                    else:
                        loginf("Received GW1000 data: %s" % (natural_sort_dict(queue_data),))
                else:
                    # perhaps we have individual debugs such as rain or wind
                    if self.debug_rain:
                        # debug_rain is set so log the 'rain' field in the
                        # mapped data, if it does not exist say so
                        self.log_rain_data(queue_data, "Received GW1000 data")
                    if self.debug_wind:
                        # debug_wind is set so log the 'wind' fields in the
                        # received data, if they do not exist say so
                        pass
                # if not already determined determine which cumulative rain
                # field will be used to determine the per period rain field
                if not self.rain_mapping_confirmed:
                    self.get_cumulative_rain_field(queue_data)
                # get the rainfall this period from total
                self.calculate_rain(queue_data)
                # get the lightning strike count this period from total
                self.calculate_lightning_count(queue_data)

                # Now start to create a loop packet. A loop packet must
                # have a timestamp, if we have one (key 'datetime') in the
                # received data use it otherwise allocate one.
                if 'datetime' in queue_data:
                    mapped_packet = {'dateTime': queue_data['datetime']}
                else:
                    # we don't have a timestamp so create one
                    mapped_packet = {'dateTime': int(time.time() + 0.5)}
                # map the raw data to WeeWX loop packet fields
                mapped_data = self.map_data(queue_data)
                # add the mapped data to the timestamped bare mapped packet
                mapped_packet.update(mapped_data)
                # log the mapped data if necessary
                if self.debug_loop:
                    loginf("Mapped GW1000 data: %s %s" % (timestamp_to_string(mapped_packet['dateTime']),
                                                          natural_sort_dict(mapped_packet)))
                else:
                    # perhaps we have individual debugs such as rain or wind
                    if self.debug_rain:
                        # debug_rain is set so log the 'rain' field in the
                        # mapped data, if it does not exist say so
                        self.log_rain_data(mapped_packet, "Mapped GW1000 data")
                    if self.debug_wind:
                        # debug_wind is set so log the 'wind' fields in the
                        # mapped data, if they do not exist say so
                        pass
                # and finally augment the loop packet with the mapped data
                self.augment_packet(event.packet, mapped_packet)
                # log the augmented packet if necessary, there are several debug
                # settings that may require this, start from the highest (most
                # encompassing) and work to the lowest (least encompassing)
                if self.debug_loop:
                    loginf('Augmented packet: %s %s' % (timestamp_to_string(event.packet['dateTime']),
                                                        natural_sort_dict(event.packet)))
                elif weewx.debug >= 2:
                    logdbg('Augmented packet: %s %s' % (timestamp_to_string(event.packet['dateTime']),
                                                        natural_sort_dict(event.packet)))
                else:
                    # perhaps we have individual debugs such as rain or wind
                    if self.debug_rain:
                        # debug_rain is set so log the 'rain' field in the
                        # augmented loop packet, if it does not exist say
                        # so
                        self.log_rain_data(event.packet, "Augmented packet")
                    if self.debug_wind:
                        # debug_wind is set so log the 'wind' fields in the
                        # loop packet being emitted, if they do not exist
                        # say so
                        pass
            # if it's a tuple then it's a tuple with an exception and
            # exception text
            elif isinstance(queue_data, BaseException):
                # We have an exception. The collector did not deem it serious
                # enough to want to shutdown or it would have sent None
                # instead. The action we take depends on the type of exception
                # it is. If its a GW1000IOError we can ignore it as appropriate
                # action will have been taken by the GW1000Collector. If it is
                # anything else we log it.
                # first extract our exception
                e = queue_data
                # and process it if we have something
                if e:
                    # is it a GW1000Error
                    if isinstance(e, GW1000IOError):
                        # set our failure logging appropriately
                        if self.lost_con_ts is None:
                            # we have previously been in contact with the
                            # GW1000 so set our lost contact timestamp
                            self.lost_con_ts = time.time()
                            # any failure logging for this failure will already
                            # have occurred in our GW1000Collector object and
                            # its Station, so turn off failure logging
                            self.set_failure_logging(False)
                        elif self.log_failures:
                            # we are already in a lost contact state, but
                            # failure logging may have been turned on for a
                            # 'once in a while' log entry so we need to trun it
                            # off again
                            self.set_failure_logging(False)
                    else:
                        # it's not so log it
                        logerr("Caught unexpected exception %s: %s" % (e.__class__.__name__,
                                                                       e))
            # if it's None then its a signal the Collector needs to shutdown
            elif queue_data is None:
                # if debug_loop log what we received
                if self.debug_loop:
                    loginf("Received collector shutdown signal 'None'")
                # we received the signal that the Gw1000Collector needs to
                # shutdown, that means we cannot continue so call our shutdown
                # method which will also shutdown the GW1000Collector thread
                self.shutDown()
                # the Gw1000Collector has been shutdown so we will not see
                # anything more in the queue, we are still bound to
                # NEW_LOOP_PACKET but since the queue is always empty we will
                # just wait for the empty queue timeout before exiting
            # if it's none of the above (which it should never be) we don't
            # know what to do with it so pass and wait for the next item in
            # the queue
            else:
                pass

    def augment_packet(self, packet, data):
        """Augment a loop packet with data from another packet.

        If the data to be used to augment the loop packet is not stale then
        augment the loop packet with the data concerned. The data to be
        used to augment the lop packet is assumed to contain a field 'usUnits'
        designating the unit system of the data to be used for augmentation.
        The data to be used for augmentation is converted to the same unit
        system as used in the loop packet before augmentation occurs. Only
        fields that exist in the data used for augmentation but not in the loop
        packet are added to the loop packet.

        packet: dict containing the loop packet
        data: dict containing the data to be used to augment the loop packet
        """

        if 'dateTime' in data and data['dateTime'] > packet['dateTime'] - self.max_age:
            # the GW1000 data is not stale so augmentation will occur, log if required
            if self.debug_loop:
                _stem = "Mapped data(%s) will be used to augment loop packet(%s)"
                loginf(_stem % (timestamp_to_string(data['dateTime']),
                                timestamp_to_string(packet['dateTime'])))
            # But the mapped data must be converted to the same unit system as
            # the packet being augmented. First get a converter.
            converter = weewx.units.StdUnitConverters[packet['usUnits']]
            # convert the mapped data to the same unit system as the packet to
            # be augmented
            converted_data = converter.convertDict(data)
            # if required log the converted data
            if self.debug_loop:
                loginf("Converted GW1000 data: %s %s" % (timestamp_to_string(converted_data['dateTime']),
                                                         natural_sort_dict(converted_data)))
            # now we can freely augment the packet with any of our mapped obs
            for field, data in six.iteritems(converted_data):
                # Any existing packet fields, whether they contain data or are
                # None, are respected and left alone. Only fields from the
                # converted data that do not already exist in the packet are
                # used to augment the packet.
                if field not in packet:
                    packet[field] = data
        else:
            # the GW1000 data is either stale or not timestamped (this should
            # never happen) and we can't use it to augment, log if required
            if self.debug_loop:
                _stem = "Mapped data (%s) is too old to augment loop packet(%s)"
                loginf(_stem % (timestamp_to_string(data.get('dateTime')),
                                timestamp_to_string(packet['dateTime'])))

    def set_failure_logging(self, log_failures):
        """Turn failure logging on or off.

        When operating as a service lost contact or other non-fatal errors
        should only be logged every so often so as not to flood the logs.
        Failure logging occurs at three levels:
        1. in myself (the service)
        2. in the GW1000Collector object
        3. in the GW1000Collector object's Station object

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


# ============================================================================
#                 GW1000 Loader/Configurator/Editor methods
# ============================================================================


def loader(config_dict, engine):
    return Gw1000Driver(**config_dict[DRIVER_NAME])


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
        [[hourRain]]
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
        for an example string stanza."""
        return self.default_stanza if orig_stanza is None else orig_stanza

    def prompt_for_settings(self):
        """Prompt for settings required for proper operation of this driver.

        Returns a dict of setting, value key pairs for settings to be included
        in the driver stanza. The _prompt() method may be used to prompt the
        user for input with a default.
        """

        # obtain IP address
        print()
        print("Specify GW1000 IP address, for example: 192.168.1.100")
        print("Set to 'auto' to autodiscover GW1000 IP address (not")
        print("recommended for systems with more than one GW1000)")
        ip_address = self._prompt('IP address',
                                  dflt=self.existing_options.get('ip_address'))
        # obtain port number
        print()
        print("Specify GW1000 network port, for example: 45000")
        port = self._prompt('port', dflt=self.existing_options.get('port', default_port))
        # obtain poll interval
        print()
        print("Specify how often to poll the GW1000 API in seconds")
        poll_interval = self._prompt('Poll interval',
                                     dflt=self.existing_options.get('poll_interval',
                                                                    default_poll_interval))
        return {'ip_address': ip_address,
                'port': port,
                'poll_interval': poll_interval
                }

    def modify_config(self, config_dict):

        import weecfg

        # set loop_on_init
        loop_on_init_config = """loop_on_init = %d"""
        dflt = config_dict.get('loop_on_init', '1')
        label = """The GW1000 driver requires a network connection to the 
GW1000. Consequently, the absence of a network connection 
when WeeWX starts will cause WeeWX to exit and such a situation 
can occur on system startup. The 'loop_on_init' setting 
can be used to mitigate such problems by having WeeWX 
retry startup indefinitely. Set to '0' to attempt startup 
once only or '1' to attempt startup indefinitely."""
        print()
        loop_on_init = int(weecfg.prompt_with_options(label, dflt, ['0', '1']))
        loop_on_init_dict = configobj.ConfigObj(StringIO(loop_on_init_config % (loop_on_init, )))
        config_dict.merge(loop_on_init_dict)
        if len(config_dict.comments['loop_on_init']) == 0:
            config_dict.comments['loop_on_init'] = ['', '# Whether to try indefinitely to load the driver']
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
#                            GW1000 Driver class
# ============================================================================


class Gw1000Driver(weewx.drivers.AbstractDevice, Gw1000):
    """GW1000 driver class.

    A WeeWX driver to emit loop packets based on observational data obtained
    from the GW1000 API. The Gw1000Driver should be used when there is no other
    data source or other sources data can be ingested via one or more WeeWX
    services.

    Data is obtained from the GW1000 API. The data is parsed and mapped to
    WeeWX fields and emitted as a WeeWX loop packet.

    Class Gw1000Collector collects and parses data from the GW1000 API. The
    Gw1000Collector runs in a separate thread so as to not block the main WeeWX
    processing loop. The Gw1000Collector is turn uses child classes Station and
    Parser to interact directly with the GW1000 API and parse the API responses
    respectively."""

    def __init__(self, **stn_dict):
        """Initialise a GW1000 driver object."""

        # now initialize my superclasses
        super(Gw1000Driver, self).__init__(**stn_dict)

        # log our version number
        loginf('driver version is %s' % DRIVER_VERSION)
        # log the relevant settings/parameters we are using
        if self.ip_address is None and self.port is None:
            loginf("GW1000 IP address and port not specified, attempting to discover GW1000...")
        elif self.ip_address is None:
            loginf("GW1000 IP address not specified, attempting to discover GW1000...")
        elif self.port is None:
            loginf("GW1000 port not specified, attempting to discover GW1000...")
        loginf("GW1000 address is %s:%d" % (self.collector.station.ip_address.decode(),
                                            self.collector.station.port))
        loginf("poll interval is %d seconds" % self.poll_interval)
        logdbg('max tries is %d, retry wait time is %d seconds' % (self.max_tries,
                                                                   self.retry_wait))
        logdbg('broadcast address is %s:%d, socket timeout is %d seconds' % (self.broadcast_address,
                                                                             self.broadcast_port,
                                                                             self.socket_timeout))
        # start the Gw1000Collector in its own thread
        self.collector.startup()

    def genLoopPackets(self):
        """Generator function that returns loop packets.

        Run a continuous loop checking the Gw1000Collector queue for data. When
        data arrives map the raw data to a WeeWX loop packet and yield the
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
                            loginf("Received GW1000 data: %s %s" % (timestamp_to_string(queue_data['datetime']),
                                                                    natural_sort_dict(queue_data)))
                        else:
                            loginf("Received GW1000 data: %s" % (natural_sort_dict(queue_data),))
                    else:
                        # perhaps we have individual debugs such as rain or wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # received data, if it does not exist say so
                            self.log_rain_data(queue_data, "Received GW1000 data")
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # received data, if they do not exist say so
                            pass
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
                    if not self.rain_mapping_confirmed:
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
                            loginf("Mapped GW1000 data: %s %s" % (timestamp_to_string(mapped_data['datetime']),
                                                                  natural_sort_dict(mapped_data)))
                        else:
                            loginf("Mapped GW1000 data: %s" % (natural_sort_dict(mapped_data),))
                    else:
                        # perhaps we have individual debugs such as rain or wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # mapped data, if it does not exist say so
                            self.log_rain_data(mapped_data, "Mapped GW1000 data")
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # mapped data, if they do not exist say so
                            pass
                    # add the mapped data to the empty packet
                    packet.update(mapped_data)
                    # log the packet if necessary, there are several debug
                    # settings that may require this, start from the highest
                    # (most encompassing) and work to the lowest (least
                    # encompassing)
                    if self.debug_loop:
                        loginf('Packet%s: %s' % (timestamp_to_string(packet['dateTime']),
                                                 natural_sort_dict(packet)))
                    elif weewx.debug >= 2:
                        logdbg('Packet%s: %s' % (timestamp_to_string(packet['dateTime']),
                                                 natural_sort_dict(packet)))
                    else:
                        # perhaps we have individual debugs such as rain or wind
                        if self.debug_rain:
                            # debug_rain is set so log the 'rain' field in the
                            # loop packet being emitted, if it does not exist
                            # say so
                            self.log_rain_data(mapped_data,
                                               "Packet%s" % timestamp_to_string(packet['dateTime']))
                        if self.debug_wind:
                            # debug_wind is set so log the 'wind' fields in the
                            # loop packet being emitted, if they do not exist
                            # say so
                            pass
                    # yield the loop packet
                    yield packet
                # if it's a tuple then it's a tuple with an exception and
                # exception text
                elif isinstance(queue_data, BaseException):
                    # We have an exception. The collector did not deem it
                    # serious enough to want to shutdown or it would have sent
                    # None instead. The action we take depends on the type of
                    # exception it is. If its a GW1000IOError we need to force
                    # the WeeWX engine to restart by raining a WeewxIOError. If
                    # it is anything else we log it and then raise it.
                    # first extract our exception
                    e = queue_data
                    # and process it if we have something
                    if e:
                        # is it a GW1000Error
                        if isinstance(e, GW1000IOError):
                            # it is so we raise a WeewxIOError, ideally would
                            # use raise .. from .. but raise.. from .. is not
                            # available under Python 2
                            raise weewx.WeeWxIOError(e)
                        else:
                            # it's not so log it
                            logerr("Caught unexpected exception %s: %s" % (e.__class__.__name__,
                                                                           e))
                            # then raise it, WeeWX will decide what to do
                            raise e
                # if it's None then its a signal the Collector needs to shutdown
                elif queue_data is None:
                    # if debug_loop log what we received
                    if self.debug_loop:
                        loginf("Received 'None'")
                    # we received the signal to shutdown, so call closePort()
                    self.closePort()
                    # and raise an exception to cause the engine to shutdown
                    raise GW1000IOError("Gw1000Collector needs to shutdown")
                # if it's none of the above (which it should never be) we don't
                # know what to do with it so pass and wait for the next item in
                # the queue
                else:
                    pass

    @property
    def hardware_name(self):
        """Return the hardware name."""

        return DRIVER_NAME

    @property
    def mac_address(self):
        """Return the GW1000 MAC address."""

        return self.collector.mac_address

    @property
    def firmware_version(self):
        """Return the GW1000 firmware version string."""

        return self.collector.firmware_version

    @property
    def sensor_id_data(self):
        """Return the GW1000 sensor identification data."""

        return self.collector.sensor_id_data

    def closePort(self):
        """Close down the driver port."""

        # in this case there is no port to close, just shutdown the collector
        self.collector.shutdown()


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
#                              class Gw1000Collector
# ============================================================================


class Gw1000Collector(Collector):
    """Class to poll the GW1000 API then decode and return data to the driver."""

    # map of sensor ids to short and long names
    sensor_ids = {
        b'\x00': {'name': 'wh65', 'long_name': 'WH65'},
        b'\x01': {'name': 'wh68', 'long_name': 'WH68'},
        b'\x02': {'name': 'ws80', 'long_name': 'WS80'},
        b'\x03': {'name': 'wh40', 'long_name': 'WH40'},
        b'\x04': {'name': 'wh25', 'long_name': 'WH25'},
        b'\x05': {'name': 'wh26', 'long_name': 'WH26'},
        b'\x06': {'name': 'wh31_ch1', 'long_name': 'WH31 ch1'},
        b'\x07': {'name': 'wh31_ch2', 'long_name': 'WH31 ch2'},
        b'\x08': {'name': 'wh31_ch3', 'long_name': 'WH31 ch3'},
        b'\x09': {'name': 'wh31_ch4', 'long_name': 'WH31 ch4'},
        b'\x0a': {'name': 'wh31_ch5', 'long_name': 'WH31 ch5'},
        b'\x0b': {'name': 'wh31_ch6', 'long_name': 'WH31 ch6'},
        b'\x0c': {'name': 'wh31_ch7', 'long_name': 'WH31 ch7'},
        b'\x0d': {'name': 'wh31_ch8', 'long_name': 'WH31 ch8'},
        b'\x0e': {'name': 'wh51_ch1', 'long_name': 'WH51 ch1'},
        b'\x0f': {'name': 'wh51_ch2', 'long_name': 'WH51 ch2'},
        b'\x10': {'name': 'wh51_ch3', 'long_name': 'WH51 ch3'},
        b'\x11': {'name': 'wh51_ch4', 'long_name': 'WH51 ch4'},
        b'\x12': {'name': 'wh51_ch5', 'long_name': 'WH51 ch5'},
        b'\x13': {'name': 'wh51_ch6', 'long_name': 'WH51 ch6'},
        b'\x14': {'name': 'wh51_ch7', 'long_name': 'WH51 ch7'},
        b'\x15': {'name': 'wh51_ch8', 'long_name': 'WH51 ch8'},
        b'\x16': {'name': 'wh41_ch1', 'long_name': 'WH41 ch1'},
        b'\x17': {'name': 'wh41_ch2', 'long_name': 'WH41 ch2'},
        b'\x18': {'name': 'wh41_ch3', 'long_name': 'WH41 ch3'},
        b'\x19': {'name': 'wh41_ch4', 'long_name': 'WH41 ch4'},
        b'\x1a': {'name': 'wh57', 'long_name': 'WH57'},
        b'\x1b': {'name': 'wh55_ch1', 'long_name': 'WH55 ch1'},
        b'\x1c': {'name': 'wh55_ch2', 'long_name': 'WH55 ch2'},
        b'\x1d': {'name': 'wh55_ch3', 'long_name': 'WH55 ch3'},
        b'\x1e': {'name': 'wh55_ch4', 'long_name': 'WH55 ch4'},
        b'\x1f': {'name': 'wh34_ch1', 'long_name': 'WH34 ch1'},
        b'\x20': {'name': 'wh34_ch2', 'long_name': 'WH34 ch2'},
        b'\x21': {'name': 'wh34_ch3', 'long_name': 'WH34 ch3'},
        b'\x22': {'name': 'wh34_ch4', 'long_name': 'WH34 ch4'},
        b'\x23': {'name': 'wh34_ch5', 'long_name': 'WH34 ch5'},
        b'\x24': {'name': 'wh34_ch6', 'long_name': 'WH34 ch6'},
        b'\x25': {'name': 'wh34_ch7', 'long_name': 'WH34 ch7'},
        b'\x26': {'name': 'wh34_ch8', 'long_name': 'WH34 ch8'}
    }
    # tuple of values for sensors that are not registered with the GW1000
    not_registered = ('fffffffe', 'ffffffff')
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
                 broadcast_port=None, socket_timeout=None,
                 poll_interval=default_poll_interval,
                 max_tries=default_max_tries, retry_wait=default_retry_wait,
                 use_th32=False, lost_contact_log_period=0, debug_rain=False,
                 debug_wind=False):
        """Initialise our class."""

        # initialize my base class:
        super(Gw1000Collector, self).__init__()

        # interval between polls of the API, use a default
        self.poll_interval = poll_interval
        # how many times to poll the API before giving up, default is
        # default_max_tries
        self.max_tries = max_tries
        # period in seconds to wait before polling again, default is
        # default_retry_wait seconds
        self.retry_wait = retry_wait
        # are we using a th32 sensor
        self.use_th32 = use_th32
        # get a station object to do the handle the interaction with the
        # GW1000 API
        self.station = Gw1000Collector.Station(ip_address=ip_address,
                                               port=port,
                                               broadcast_address=broadcast_address,
                                               broadcast_port=broadcast_port,
                                               socket_timeout=socket_timeout,
                                               max_tries=max_tries,
                                               retry_wait=retry_wait,
                                               lost_contact_log_period=lost_contact_log_period)
        # Do we have a WH24 attached? First obtain our system parameters.
        _sys_params = self.station.get_system_params()
        # WH24 is indicated by the 6th byte being 0
        is_wh24 = six.indexbytes(_sys_params, 5) == 0
        # Tell our sensor id decoding whether we have a WH24 or a WH65. By
        # default we are coded to use a WH65. Is there a WH24 connected?
        if is_wh24:
            # set the WH24 sensor id decode dict entry
            self.sensor_ids[b'\x00']['name'] = 'wh24'
            self.sensor_ids[b'\x00']['long_name'] = 'WH24'
        # start off logging failures
        self.log_failures = True
        # get a parser object to parse any data from the station
        self.parser = Gw1000Collector.Parser(is_wh24, debug_rain, debug_wind)
        # create a thread property
        self.thread = None
        # we start off not collecting data, it will be turned on later when we
        # are threaded
        self.collect_data = False

    def collect_sensor_data(self):
        """Collect sensor data by polling the API.

        Loop forever waking periodically to see if it is time to quit or
        collect more data.
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
                # GW1000IOError exception
                try:
                    queue_data = self.get_live_sensor_data()
                except GW1000IOError as e:
                    # a GW1000IOError occurred, most likely because the Station
                    # object could not contact the GW1000
                    # first up log the event, but only if we are logging
                    # failures
                    if self.log_failures:
                        logerr('Unable to obtain live sensor data')
                    # assign the GW1000IOError exception so it will be sent in
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

    def get_live_sensor_data(self):
        """Get sensor data.

        Obtain live sensor data from the GW1000 API. Parse the API response.
        The parsed battery data is then further processed to filter battery
        state data for sensors that are not registered and to include sensor
        signal level data for registered sensors. The processed data is
        returned as a dict. If no data was obtained from the API the value None
        is returned.
        """

        # obtain the raw data via the GW1000 API, we may get a GW1000IOError
        # exception, if we do let it bubble up
        raw_data = self.station.get_livedata()
        # if we made it here our raw data was validated by checksum
        # get a timestamp to use in case our data does not come with one
        _timestamp = int(time.time())
        # parse the raw data
        parsed_data = self.parser.parse(raw_data, _timestamp)
        # log the parsed data but only if debug>=3
        if weewx.debug >= 3:
            logdbg("Parsed data: %s" % parsed_data)
        # The nature of the GW1000 API means that the parsed live data will
        # likely contain battery state information for sensors that do not
        # exist. The parsed live data also does not contain any sensor signal
        # level data. The GW1000 API does provide details on what sensors are
        # connected to the GW1000 and their signal levels via the
        # CMD_READ_SENSOR_ID command. The data received from the
        # CMD_READ_SENSOR_ID command can be used to filter sensor battery state
        # fields for sensors that are not registered and to add sensor signal
        # level fields to the live data.
        parsed_data = self.process_sensor_id_data(parsed_data)
        # log the processed parsed data but only if debug>=3
        if weewx.debug >= 3:
            logdbg("Processed parsed data: %s" % parsed_data)
        return parsed_data

    def process_sensor_id_data(self, parsed_data):
        """Use sensor ID data to update live sensor data.

        The CMD_READ_SENSOR_ID API command returns address, id, signal and
        battery state information for sensors registered with the GW1000.
        Whilst the CMD_GW1000_LIVEDATA API command returns sensor data and
        sensor battery state data it is not possible to tell from the
        CMD_GW1000_LIVEDATA response which sensors are in fact registered with
        the GW1000. The CMD_GW1000_LIVEDATA response does not include sensor
        signal level data. The CMD_READ_SENSOR_ID data can be used to filter
        battery state data from the live sensor data for sensors that are not
        registered with the GW1000. The CMD_READ_SENSOR_ID data can also be
        used to add sensor signal level data to the live sensor data.

        parsed_data: dict of parsed GW1000 live sensor data
        """

        # obtain details of the sensors from the GW1000 API, we may get a
        # GW1000IOError exception, but let it bubble up
        sensor_list = self.sensor_id_data
        # If we made it here our response was validated by checksum. Now create
        # a filtered list of registered sensors, these are the sensors we are
        # interested in.
        registered_sensors = [s for s in sensor_list if s['id'] not in Gw1000Collector.not_registered]
        # first filter the battery state fields
        processed_data = self.filter_battery_data(parsed_data,
                                                  registered_sensors)
        # now add any sensor signal levels
        processed_data.update(self.get_signal_level_data(registered_sensors))
        # return our processed data
        return processed_data

    @staticmethod
    def filter_battery_data(data, registered_sensors):
        """Filter battery data for unused sensors.

        The battery status data returned by the GW1000 API does not allow the
        discrimination of all used/unused sensors (it does for some but not for
        others). Some further processing of the battery status data is required
        to ensure that battery status is only provided for sensors that
        actually exist.

        data: dict of parsed GW1000 API data
        """

        # obtain a list of registered sensor names
        reg_sensor_names = [Gw1000Collector.sensor_ids[a['address']]['name'] for a in registered_sensors]
        # obtain a copy of our parsed data as we are going to alter it
        filtered = dict(data)
        # iterate over the parsed data
        for key, data in six.iteritems(data):
            # obtain the sensor name from any any battery fields
            stripped = key[:-5] if key.endswith('_batt') else key
            # if field is a battery state field, and the field pertains to an
            # unregistered sensor, remove the field from the parsed data
            if '_batt' in key and stripped not in reg_sensor_names:
                del filtered[key]
        # return our parsed data with battery state information fo unregistered
        # sensors removed
        return filtered

    @staticmethod
    def get_signal_level_data(registered_sensors):
        """Add sensor signal level data to a sensor data packet.

        Iterate over the list of registered sensors and obtain a dict of sensor
        signal level data for each registered sensor.

        registered_sensors: list of dicts of sensor ID data for each registered
                            sensor
        """

        # initialise a dict to hold the sensor signal level data
        signal_level_data = {}
        # iterate over our registered sensors
        for sensor in registered_sensors:
            # get the sensor name
            sensor_name = Gw1000Collector.sensor_ids[sensor['address']]['name']
            # create the sensor signal level field for this sensor
            signal_level_data[''.join([sensor_name, '_sig'])] = sensor['signal']
        # return our sensor signal level data
        return signal_level_data

    @property
    def rain_data(self):
        """Obtain GW1000 rain data."""

        # obtain the rain data data via the API
        response = self.station.get_raindata()
        # determine the size of the rain data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        data_dict['rain_rate'] = self.parser.decode_big_rain(data[0:4])
        data_dict['rain_day'] = self.parser.decode_big_rain(data[4:8])
        data_dict['rain_week'] = self.parser.decode_big_rain(data[8:12])
        data_dict['rain_month'] = self.parser.decode_big_rain(data[12:16])
        data_dict['rain_year'] = self.parser.decode_big_rain(data[16:20])
        return data_dict

    @property
    def mulch_offset(self):
        """Obtain GW1000 multi-channel temperature and humidity offset data."""

        # obtain the mulch offset data via the API
        response = self.station.get_mulch_offset()
        # determine the size of the mulch offset data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # initialise a counter
        index = 0
        # initialise a dict to hold our final data
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

    @property
    def pm25_offset(self):
        """Obtain GW1000 PM2.5 offset data."""

        # obtain the PM2.5 offset data via the API
        response = self.station.get_pm25_offset()
        # determine the size of the PM2.5 offset data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # initialise a counter
        index = 0
        # initialise a dict to hold our final data
        offset_dict = {}
        # iterate over the data
        while index < len(data):
            try:
                channel = six.byte2int(data[index])
            except TypeError:
                channel = data[index]
            offset_dict[channel] = struct.unpack(">h", data[index+1:index+3])[0]/10.0
            index += 3
        return offset_dict

    @property
    def co2_offset(self):
        """Obtain GW1000 WH45 CO2, PM10 and PM2.5 offset data."""

        # obtain the WH45 offset data via the API
        response = self.station.get_co2_offset()
        # determine the size of the WH45 offset data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        offset_dict = dict()
        # and decode/store the offset data
        offset_dict['co2'] = struct.unpack(">h", data[1:3])[0]
        offset_dict['pm25'] = struct.unpack(">h", data[4:6])[0]/10.0
        offset_dict['pm10'] = struct.unpack(">h", data[7:9])[0]/10.0
        return offset_dict

    @property
    def calibration(self):
        """Obtain GW1000 calibration data."""

        # obtain the calibration data via the API
        response = self.station.get_calibration_coefficient()
        # determine the size of the calibration data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        calibration_dict = dict()
        # and decode/store the calibration data
        # bytes 0 and 1 are reserved (lux to solar radiation conversion
        # gain (126.7))
        calibration_dict['uv'] = struct.unpack(">H", data[2:4])[0]/100.0
        calibration_dict['solar'] = struct.unpack(">H", data[4:6])[0]/100.0
        calibration_dict['wind'] = struct.unpack(">H", data[6:8])[0]/100.0
        calibration_dict['rain'] = struct.unpack(">H", data[8:10])[0]/100.0
        # obtain the offset calibration data via the API
        response = self.station.get_offset_calibration()
        # determine the size of the calibration data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # and decode/store the offset calibration data
        calibration_dict['intemp'] = struct.unpack(">h", data[0:2])[0]/10.0
        try:
            calibration_dict['inhum'] = struct.unpack("b", data[2])[0]
        except TypeError:
            calibration_dict['inhum'] = struct.unpack("b", six.int2byte(data[2]))[0]
        calibration_dict['abs'] = struct.unpack(">l", data[3:7])[0]/10.0
        calibration_dict['rel'] = struct.unpack(">l", data[7:11])[0]/10.0
        calibration_dict['outtemp'] = struct.unpack(">h", data[11:13])[0]/10.0
        try:
            calibration_dict['outhum'] = struct.unpack("b", data[13])[0]
        except TypeError:
            calibration_dict['outhum'] = struct.unpack("b", six.int2byte(data[13]))[0]
        calibration_dict['dir'] = struct.unpack(">h", data[14:16])[0]
        return calibration_dict

    @property
    def soil_calibration(self):
        """Obtain GW1000 soil moisture sensor calibration data.

        """

        # obtain the soil moisture calibration data via the API
        response = self.station.get_soil_calibration()
        # determine the size of the calibration data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        calibration_dict = {}
        # initialise a counter
        index = 0
        # initialise a dict to hold our final data
        calibration_dict = {}
        # iterate over the data
        while index < len(data):
            try:
                channel = six.byte2int(data[index])
            except TypeError:
                channel = data[index]
            calibration_dict[channel] = {}
            try:
                humidity = six.byte2int(data[index + 1])
            except TypeError:
                humidity = data[index + 1]
            calibration_dict[channel]['humidity'] = humidity
            calibration_dict[channel]['ad'] = struct.unpack(">h", data[index+2:index+4])[0]
            try:
                ad_select = six.byte2int(data[index + 4])
            except TypeError:
                ad_select = data[index + 4]
            calibration_dict[channel]['ad_select'] = ad_select
            try:
                min_ad = six.byte2int(data[index + 5])
            except TypeError:
                min_ad = data[index + 5]
            calibration_dict[channel]['adj_min'] = min_ad
            calibration_dict[channel]['adj_max'] = struct.unpack(">h", data[index+6:index+8])[0]
            index += 8
        return calibration_dict

    @property
    def system_parameters(self):
        """Obtain GW1000 system parameters."""

        # obtain the system parameters data via the API
        response = self.station.get_system_params()
        # determine the size of the system parameters data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        data_dict['frequency'] = six.indexbytes(data, 0)
        data_dict['sensor_type'] = six.indexbytes(data, 1)
        data_dict['utc'] = self.parser.decode_utc(data[2:6])
        data_dict['timezone_index'] = six.indexbytes(data, 6)
        data_dict['dst_status'] = six.indexbytes(data, 7) != 0
        return data_dict

    @property
    def ecowitt_net(self):
        """Obtain GW1000 Ecowitt.net service parameters.

        Obtain the GW1000 Ecowitt.net service settings.

        Returns a dictionary of settings.
        """

        # obtain the system parameters data via the API
        response = self.station.get_ecowitt_net_params()
        # determine the size of the system parameters data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        data_dict['interval'] = six.indexbytes(data, 0)
        # obtain the GW1000 MAC address
        data_dict['mac'] = self.mac_address
        return data_dict

    @property
    def wunderground(self):
        """Obtain GW1000 Weather Underground service parameters.

        Obtain the GW1000 Weather Underground service settings.

        Returns a dictionary of settings with string data in unicode format.
        """

        # obtain the system parameters data via the API
        response = self.station.get_wunderground_params()
        # determine the size of the system parameters data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # return data
        # initialise a dict to hold our final data
        data_dict = dict()
        # obtain the required data from the response decoding any bytestrings
        id_size = six.indexbytes(data, 0)
        data_dict['id'] = data[1:1+id_size].decode()
        password_size = six.indexbytes(data, 1+id_size)
        data_dict['password'] = data[2+id_size:2+id_size+password_size].decode()
        return data_dict

    @property
    def weathercloud(self):
        """Obtain GW1000 Weathercloud service parameters.

        Obtain the GW1000 Weathercloud service settings.

        Returns a dictionary of settings with string data in unicode format.
        """

        # obtain the system parameters data via the API
        response = self.station.get_weathercloud_params()
        # determine the size of the system parameters data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        # obtain the required data from the response decoding any bytestrings
        id_size = six.indexbytes(data, 0)
        data_dict['id'] = data[1:1+id_size].decode()
        key_size = six.indexbytes(data, 1+id_size)
        data_dict['key'] = data[2+id_size:2+id_size+key_size].decode()
        return data_dict

    @property
    def wow(self):
        """Obtain GW1000 Weather Observations Website service parameters.

        Obtain the GW1000 Weather Observations Website service settings.

        Returns a dictionary of settings with string data in unicode format.
        """

        # obtain the system parameters data via the API
        response = self.station.get_wow_params()
        # determine the size of the system parameters data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        # obtain the required data from the response decoding any bytestrings
        id_size = six.indexbytes(data, 0)
        data_dict['id'] = data[1:1+id_size].decode()
        password_size = six.indexbytes(data, 1+id_size)
        data_dict['password'] = data[2+id_size:2+id_size+password_size].decode()
        station_num_size = six.indexbytes(data, 1+id_size)
        data_dict['station_num'] = data[3+id_size+password_size:3+id_size+password_size+station_num_size].decode()
        return data_dict

    @property
    def custom(self):
        """Obtain GW1000 custom server parameters.

        Obtain the GW1000 settings used for uploading data to a remote server.

        Returns a dictionary of settings with string data in unicode format.
        """

        # obtain the system parameters data via the API
        response = self.station.get_custom_params()
        # determine the size of the system parameters data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        # obtain the required data from the response decoding any bytestrings
        index = 0
        id_size = six.indexbytes(data, index)
        index += 1
        data_dict['id'] = data[index:index+id_size].decode()
        index += id_size
        password_size = six.indexbytes(data, index)
        index += 1
        data_dict['password'] = data[index:index+password_size].decode()
        index += password_size
        server_size = six.indexbytes(data, index)
        index += 1
        data_dict['server'] = data[index:index+server_size].decode()
        index += server_size
        data_dict['port'] = struct.unpack(">h", data[index:index + 2])[0]
        index += 2
        data_dict['interval'] = struct.unpack(">h", data[index:index + 2])[0]
        index += 2
        data_dict['type'] = six.indexbytes(data, index)
        index += 1
        data_dict['active'] = six.indexbytes(data, index)
        # the user path is obtained separately, get the user path and add it to
        # our response
        data_dict.update(self.usr_path)
        return data_dict

    @property
    def usr_path(self):
        """Obtain the GW1000 user defined custom paths.

        The GW1000 allows definition of remote server customs paths for use
        when uploading to a custom service using Ecowitt or Weather Underground
        format. Different paths may be specified for each protocol.

        Returns a dictionary with each path as a unicode text string.
        """

        # return the GW1000 user defined custom path
        response = self.station.get_usr_path()
        # determine the size of the user path data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual system parameters data
        data = response[4:4 + raw_data_size - 3]
        # initialise a dict to hold our final data
        data_dict = dict()
        index = 0
        ecowitt_size = six.indexbytes(data, index)
        index += 1
        data_dict['ecowitt_path'] = data[index:index+ecowitt_size].decode()
        index += ecowitt_size
        wu_size = six.indexbytes(data, index)
        index += 1
        data_dict['wu_path'] = data[index:index+wu_size].decode()
        return data_dict

    @property
    def mac_address(self):
        """Obtain the MAC address of the GW1000.

        Returns the GW1000 MAC address as a string of colon separated hex
        bytes.
        """

        # obtain the GW1000 MAC address bytes
        station_mac_b = self.station.get_mac_address()
        # return the formatted string
        return bytes_to_hex(station_mac_b[4:10], separator=":")

    @property
    def firmware_version(self):
        """Obtain the GW1000 firmware version string."""

        firmware_b = self.station.get_firmware_version()
        firmware_format = "B" * len(firmware_b)
        firmware_t = struct.unpack(firmware_format, firmware_b)
        return "".join([chr(x) for x in firmware_t[5:18]])

    @property
    def sensor_id_data(self):
        """Get sensor id data.

        The GW1000 clearly shows the position of the 'signal' and
        'battery state' data in the CMD_READ_SENSOR_ID response. However, when
        decoded as per the API the CMD_READ_SENSOR_ID 'battery state' data
        does not agree with the battery battery state data obtained from
        CMD_GW1000_LIVEDATA response. However, observations of a live system
        containing a number of different sensor types shows that the
        CMD_READ_SENSOR_ID sensor 'signal' data matches the
        CMD_GW1000_LIVEDATA battery data precisely. Further observations reveal
        the CMD_READ_SENSOR_ID sensor battery states match the sensor signal
        levels shown in the WS View app.

        The inference is that the CMD_READ_SENSOR_ID 'signal' and
        'battery state' bytes are in fact transposed. No other PWS software
        developers seem to have noticed this so for the time being the
        CMD_READ_SENSOR_ID 'signal' and 'battery state' bytes have been
        swapped.
        """

        # obtain the sensor id data via the API, we may get a GW1000IOError
        # exception, if we do let it bubble up
        response = self.station.get_sensor_id()
        # if we made it here our response was validated by checksum
        # determine the size of the sensor id data
        raw_data_size = six.indexbytes(response, 3)
        # extract the actual sensor id data
        data = response[4:4 + raw_data_size - 3]
        # initialise a counter
        index = 0
        # initialise a list to hold our final data
        sensor_id_list = []
        # iterate over the data
        while index < len(data):
            sensor_id = bytes_to_hex(data[index + 1: index + 5],
                                     separator='',
                                     caps=False)
            # As per method comments above swap signal and battery state bytes,
            # the GW1000 API says signal should be byte 5 and battery byte 6,
            # we will use signal as byte 6 and battery as byte 5.
            sensor_id_list.append({'address': data[index:index + 1],
                                   'id': sensor_id,
                                   'battery': six.indexbytes(data, index + 5),
                                   'signal': six.indexbytes(data, index + 6)
                                   })
            index += 7
        return sensor_id_list

    def startup(self):
        """Start a thread that collects data from the GW1000 API."""

        try:
            self.thread = Gw1000Collector.CollectorThread(self)
            self.collect_data = True
            self.thread.setDaemon(True)
            self.thread.setName('Gw1000CollectorThread')
            self.thread.start()
        except threading.ThreadError:
            logerr("Unable to launch Gw1000Collector thread")
            self.thread = None

    def shutdown(self):
        """Shut down the thread that collects data from the GW1000 API.

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
                logerr("Unable to shut down Gw1000Collector thread")
            else:
                loginf("Gw1000Collector thread has been terminated")
        self.thread = None

    class CollectorThread(threading.Thread):
        """Class used to collect data via the GW1000 API in a thread."""

        def __init__(self, client):
            # initialise our parent
            threading.Thread.__init__(self)
            # keep reference to the client we are supporting
            self.client = client
            self.name = 'gw1000-collector'

        def run(self):
            # rather than letting the thread silently fail if an exception
            # occurs within the thread, wrap in a try..except so the exception
            # can be caught and available exception information displayed
            try:
                # kick the collection off
                self.client.collect_sensor_data()
            except:
                # we have an exception so log what we can
                log_traceback_critical('    ****  ')

    class Station(object):
        """Class to interact directly with the GW1000 API.

        A Station object knows how to:
        1.  discover a GW1000 via UDP broadcast
        2.  send a command to the GW1000 API
        3.  receive a response from the GW1000 API
        4.  verify the response as valid

        A Station object needs an ip address and port as well as a network
        broadcast address and port.
        """

        # GW1000 API commands
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
            'CMD_SET_CO2_OFFSET': b'\x54'
        }
        # header used in each API command and response packet
        header = b'\xff\xff'

        def __init__(self, ip_address=None, port=None,
                     broadcast_address=None, broadcast_port=None,
                     socket_timeout=None, max_tries=default_max_tries,
                     retry_wait=default_retry_wait, mac=None,
                     lost_contact_log_period=None):

            # network broadcast address
            self.broadcast_address = broadcast_address if broadcast_address is not None else default_broadcast_address
            # network broadcast port
            self.broadcast_port = broadcast_port if broadcast_port is not None else default_broadcast_port
            self.socket_timeout = socket_timeout if socket_timeout is not None else default_socket_timeout
            # initialise flags to indicate if ip address or port were discovered
            self.ip_discovered = ip_address is None
            self.port_discovered = port is None
            # if ip address or port was not specified (None) then attempt to
            # discover the GW1000 with a UDP broadcast
            if ip_address is None or port is None:
                for attempt in range(max_tries):
                    try:
                        # discover() returns a list of (ip address, port) tuples
                        ip_port_list = self.discover()
                    except socket.error as e:
                        _msg = "Unable to detect GW1000 ip address and port: %s (%s)" % (e, type(e))
                        logerr(_msg)
                        # signal that we have a critical error
                        raise
                    else:
                        # did we find any GW1000
                        if len(ip_port_list) > 0:
                            # we have at least one, arbitrarily choose the first one
                            # found as the one to use
                            disc_ip = ip_port_list[0][0]
                            disc_port = ip_port_list[0][1]
                            # log the fact as well as what we found
                            gw1000_str = ', '.join([':'.join(['%s:%d' % b]) for b in ip_port_list])
                            if len(ip_port_list) == 1:
                                stem = "GW1000 was"
                            else:
                                stem = "Multiple GW1000 were"
                            loginf("%s found at %s" % (stem, gw1000_str))
                            ip_address = disc_ip if ip_address is None else ip_address
                            port = disc_port if port is None else port
                            break
                        else:
                            # did not discover any GW1000 so log it
                            logdbg("Failed attempt %d to detect GW1000 ip address and/or port" % (attempt + 1,))
                            # do we try again or raise an exception
                            if attempt < max_tries - 1:
                                # we still have at least one more try left so sleep
                                # and try again
                                time.sleep(retry_wait)
                            else:
                                # we've used all our tries, log it and raise an exception
                                _msg = "Failed to detect GW1000 ip address and/or " \
                                       "port after %d attempts" % (attempt + 1,)
                                logerr(_msg)
                                raise GW1000IOError(_msg)
            # set our ip_address property but encode it first, it saves doing
            # it repeatedly later
            self.ip_address = ip_address.encode()
            self.port = port
            self.max_tries = max_tries
            self.retry_wait = retry_wait
            # start off logging failures
            self.log_failures = True
            # get my GW1000 MAC address to use later if we have to rediscover
            if mac is not None:
                self.mac = mac
            else:
                self.mac = self.get_mac_address()

        def discover(self):
            """Discover any GW1000s on the local network.

            Send a UDP broadcast and check for replies. Decode each reply to
            obtain the IP address and port number of any GW1000s on the local
            network. Since there may be multiple GW1000s on the network
            package each IP address and port as a two way tuple and construct a
            list of unique IP address/port tuples. When complete return the
            list of IP address/port tuples found.
            """

            # now create a socket object so we can broadcast to the network
            # use IPv4 UDP
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # set socket datagram to broadcast
            socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # set timeout
            socket_obj.settimeout(self.socket_timeout)
            # set TTL to 1 to so messages do not go past the local network
            # segment
            ttl = struct.pack('b', 1)
            socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            # Create packet to broadcast. Format is:
            #   fixed header, GW1000 Broadcast command, size, checksum
            size = len(self.commands['CMD_BROADCAST']) + 1 + 1
            # construct the portion of the message for which the checksum is calculated
            body = b''.join([self.commands['CMD_BROADCAST'], struct.pack('B', size)])
            # calculate the checksum
            checksum = self.calc_checksum(body)
            # construct the entire message packet
            packet = b''.join([self.header, body, struct.pack('B', checksum)])
            if weewx.debug >= 3:
                logdbg("Sending broadcast packet '%s' to '%s:%d'" % (bytes_to_hex(packet),
                                                                     self.broadcast_address,
                                                                     self.broadcast_port))
            # create a list for the results as multiple GW1000 may respond
            result_list = []
            try:
                # send the Broadcast command
                socket_obj.sendto(packet, (self.broadcast_address, self.broadcast_port))
                # obtain any responses
                while True:
                    try:
                        response = socket_obj.recv(1024)
                        # log the response if debug is high enough
                        if weewx.debug >= 3:
                            logdbg("Received broadcast response '%s'" % (bytes_to_hex(response),))
                    except socket.timeout:
                        # if we timeout then we are done
                        break
                    except socket.error:
                        # raise any other socket error
                        raise
                    # obtain the IP address, it is in bytes 11 to 14 inclusive
                    ip_address = '%d.%d.%d.%d' % struct.unpack('>BBBB', response[11:15])
                    # obtain the port, it is in bytes 15 to 16 inclusive
                    port = struct.unpack('>H', response[15: 17])[0]
                    # if we haven't seen this ip address and port add them to
                    # our results list
                    if (ip_address, port) not in result_list:
                        result_list.append((ip_address, port))
            finally:
                # we are done so close our socket
                socket_obj.close()
            return result_list

        def get_livedata(self):
            """Get GW1000 live data.

            Sends the command to obtain live data from the GW1000 to the API
            with retries. If the GW1000 cannot be contacted re-discovery is
            attempted. If rediscovery is successful the command is tried again
            otherwise the lost contact timestamp is set and the exception
            raised. Any code that calls this method should be prepared to
            handle a GW1000IOError exception.
            """

            # send the API command to obtain live data from the GW1000, be
            # prepared to catch the exception raised if the GW1000 cannot be
            # contacted
            try:
                # return the validated API response
                return self.send_cmd_with_retries('CMD_GW1000_LIVEDATA')
            except GW1000IOError:
                # there was a problem contacting the GW1000, it could be it
                # has changed IP address so attempt to rediscover
                if not self.rediscover():
                    # we could not re-discover so raise the exception
                    raise
                else:
                    # we did rediscover successfully so try again, if it fails
                    # we get another GW1000IOError exception which will be raised
                    return self.send_cmd_with_retries('CMD_GW1000_LIVEDATA')

        def get_raindata(self):
            """Get GW1000 rain data.

            Sends the command to obtain rain data from the GW1000 to the API
            with retries. If the GW1000 cannot be contacted a GW1000IOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_raindata(). Any code calling get_raindata() should
            be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_RAINDATA')

        def get_system_params(self):
            """Read GW1000 system parameters.

            Sends the command to obtain system parameters from the GW1000 to
            the API with retries. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_system_params(). Any code
            calling get_system_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_SSSS')

        def get_ecowitt_net_params(self):
            """Get GW1000 Ecowitt.net parameters.

            Sends the command to obtain the GW1000 Ecowitt.net parameters to
            the API with retries. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_ecowitt_net_params(). Any code
            calling get_ecowitt_net_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_ECOWITT')

        def get_wunderground_params(self):
            """Get GW1000 Weather Underground parameters.

            Sends the command to obtain the GW1000 Weather Underground
            parameters to the API with retries. If the GW1000 cannot be
            contacted a GW1000IOError will have been raised by
            send_cmd_with_retries() which will be passed through by
            get_wunderground_params(). Any code calling
            get_wunderground_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_WUNDERGROUND')

        def get_weathercloud_params(self):
            """Get GW1000 Weathercloud parameters.

            Sends the command to obtain the GW1000 Weathercloud parameters to
            the API with retries. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_weathercloud_params(). Any code
            calling get_weathercloud_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_WEATHERCLOUD')

        def get_wow_params(self):
            """Get GW1000 Weather Observations Website parameters.

            Sends the command to obtain the GW1000 Weather Observations Website
            parameters to the API with retries. If the GW1000 cannot be
            contacted a GW1000IOError will have been raised by
            send_cmd_with_retries() which will be passed through by
            get_wow_params(). Any code calling get_wow_params() should be
            prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_WOW')

        def get_custom_params(self):
            """Get GW1000 custom server parameters.

            Sends the command to obtain the GW1000 custom server parameters to
            the API with retries. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_custom_params(). Any code
            calling get_custom_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_CUSTOMIZED')

        def get_usr_path(self):
            """Get GW1000 user defined custom path.

            Sends the command to obtain the GW1000 user defined custom path to
            the API with retries. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_usr_path(). Any code calling
            get_usr_path() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_USR_PATH')

        def get_mac_address(self):
            """Get GW1000 MAC address.

            Sends the command to obtain the GW1000 MAC address to the API with
            retries. If the GW1000 cannot be contacted a GW1000IOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_mac_address(). Any code calling get_mac_address()
            should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_STATION_MAC')

        def get_firmware_version(self):
            """Get GW1000 firmware version.

            Sends the command to obtain GW1000 firmware version to the API with
            retries. If the GW1000 cannot be contacted a GW1000IOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_firmware_version(). Any code calling
            get_firmware_version() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_FIRMWARE_VERSION')

        def get_sensor_id(self):
            """Get GW1000 sensor ID data.

            Sends the command to obtain sensor ID data from the GW1000 to the
            API with retries. If the GW1000 cannot be contacted re-discovery is
            attempted. If rediscovery is successful the command is tried again
            otherwise the lost contact timestamp is set and the exception
            raised. Any code that calls this method should be prepared to
            handle a GW1000IOError exception.
            """

            # send the API command to obtain sensor ID data from the GW1000, be
            # prepared to catch the exception raised if the GW1000 cannot be
            # contacted
            try:
                return self.send_cmd_with_retries('CMD_READ_SENSOR_ID')
            except GW1000IOError:
                # there was a problem contacting the GW1000, it could be it
                # has changed IP address so attempt to rediscover
                if not self.rediscover():
                    # we could not re-discover so raise the exception
                    raise
                else:
                    # we did rediscover successfully so try again, if it fails
                    # we get another GW1000IOError exception which will be raised
                    return self.send_cmd_with_retries('CMD_READ_SENSOR_ID')

        def get_mulch_offset(self):
            """Get multi-channel temperature and humidity offset data.

            Sends the command to obtain the multi-channel temperature and
            humidity offset data to the API with retries. If the GW1000 cannot
            be contacted a GW1000IOError will have been raised by
            send_cmd_with_retries() which will be passed through by
            get_mulch_offset(). Any code calling get_mulch_offset() should be
            prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_MulCH_OFFSET')

        def get_pm25_offset(self):
            """Get PM2.5 offset data.

            Sends the command to obtain the PM2.5 sensor offset data to the API
            with retries. If the GW1000 cannot be contacted a GW1000IOError
            will have been raised by send_cmd_with_retries() which will be
            passed through by get_pm25_offset(). Any code calling
            get_pm25_offset() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_PM25_OFFSET')

        def get_calibration_coefficient(self):
            """Get calibration coefficient data.

            Sends the command to obtain the calibration coefficient data to the
            API with retries. If the GW1000 cannot be contacted a GW1000IOError
            will have been raised by send_cmd_with_retries() which will be
            passed through by get_calibration_coefficient(). Any code calling
            get_calibration_coefficient() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_GAIN')

        def get_soil_calibration(self):
            """Get soil moisture sensor calibration data.

            Sends the command to obtain the soil moisture sensor calibration
            data to the API with retries. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_soil_calibration(). Any code
            calling get_soil_calibration() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_GET_SOILHUMIAD')

        def get_offset_calibration(self):
            """Get offset calibration data.

            Sends the command to obtain the offset calibration data to the API
            with retries. If the GW1000 cannot be contacted a GW1000IOError
            will have been raised by send_cmd_with_retries() which will be
            passed through by get_offset_calibration(). Any code calling
            get_offset_calibration() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_CALIBRATION')

        def get_co2_offset(self):
            """Get WH45 CO2, PM10 and PM2.5 offset data.

            Sends the command to obtain the WH45 CO2, PM10 and PM2.5 sensor
            offset data to the API with retries. If the GW1000 cannot be
            contacted a GW1000IOError will have been raised by
            send_cmd_with_retries() which will be passed through by
            get_offset_calibration(). Any code calling get_offset_calibration()
            should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_GET_CO2_OFFSET')

        def send_cmd_with_retries(self, cmd, payload=b''):
            """Send a command to the GW1000 API with retries and return the
            response.

            Send a command to the GW1000 and obtain the response. If the
            the response is valid return the response. If the response is
            invalid an appropriate exception is raised and the command resent
            up to self.max_tries times after which the value None is returned.

            A GW1000 API command looks like:

            fixed header, command, size, data 1, data 2...data n, checksum

            where:
                fixed header is 2 bytes = 0xFFFF
                command is a 1 byte API command code
                size is 1 byte being the number of bytes of command to checksum
                data 1, data 2 ... data n is the data being transmitted and is n
                    bytes long
                checksum is a byte checksum of command + size + data 1 +
                    data 2 ... + data n

            cmd: A string containing a valid GW1000 API command,
                 eg: 'CMD_READ_FIRMWARE_VERSION'
            payload: The data to be sent with the API command, byte string.

            Returns the response as a byte string or the value None.
            """

            # calculate size
            try:
                size = len(self.commands[cmd]) + 1 + len(payload) + 1
            except KeyError:
                raise UnknownCommand("Unknown GW1000 API command '%s'" % (cmd,))
            # construct the portion of the message for which the checksum is calculated
            body = b''.join([self.commands[cmd], struct.pack('B', size), payload])
            # calculate the checksum
            checksum = self.calc_checksum(body)
            # construct the entire message packet
            packet = b''.join([self.header, body, struct.pack('B', checksum)])
            # attempt to send up to 'self.max_tries' times
            for attempt in range(self.max_tries):
                response = None
                # wrap in  try..except so we can catch any errors
                try:
                    response = self.send_cmd(packet)
                except socket.timeout as e:
                    # a socket timeout occurred, log it
                    if self.log_failures:
                        logdbg("Failed to obtain response to attempt %d to send command '%s': %s" % (attempt + 1,
                                                                                                     cmd,
                                                                                                     e))
                except Exception as e:
                    # an exception was encountered, log it
                    if self.log_failures:
                        logdbg("Failed attempt %d to send command '%s': %s" % (attempt + 1, cmd, e))
                else:
                    # check the response is valid
                    try:
                        self.check_response(response, self.commands[cmd])
                    except (InvalidChecksum, InvalidApiResponse) as e:
                        # the response was not valid, log it and attempt again
                        # if we haven't had too many attempts already
                        logdbg("Invalid response to attempt %d to send command '%s': %s" % (attempt + 1, cmd, e))
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
            # first of all log it
            _msg = ("Failed to obtain response to command '%s' after %d attempts" % (cmd, attempt + 1))
            if response is not None or self.log_failures:
                logerr(_msg)
            # finally raise a GW1000IOError exception
            raise GW1000IOError(_msg)

        def send_cmd(self, packet):
            """Send a command to the GW1000 API and return the response.

            Send a command to the GW1000 and return the response. Socket
            related errors are trapped and raised, code calling send_cmd should
            be prepared to handle such exceptions.

            cmd: A valid GW1000 API command

            Returns the response as a byte string.
            """

            # create socket objects for sending commands and broadcasting to the network
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_obj.settimeout(self.socket_timeout)
            try:
                socket_obj.connect((self.ip_address, self.port))
                if weewx.debug >= 3:
                    logdbg("Sending packet '%s' to '%s:%d'" % (bytes_to_hex(packet),
                                                               self.ip_address.decode(),
                                                               self.port))
                socket_obj.sendall(packet)
                response = socket_obj.recv(1024)
                if weewx.debug >= 3:
                    logdbg("Received response '%s'" % (bytes_to_hex(response),))
                return response
            except socket.error:
                raise

        def check_response(self, response, cmd_code):
            """Check the validity of a GW1000 API response.

            Checks the validity of a GW1000 API response. Two checks are
            performed:

            1.  the third byte of the response is the same as the command code
                used in the API call
            2.  the calculated checksum of the data in the response matches the
                checksum byte in the response

            If any check fails an appropriate exception is raised, if all checks
            pass the method exits without raising an exception.

            response: Response received from the GW1000 API call. Byte string.
            cmd_code: Command code send to GW1000 API. Byte string of length
                      one.
            """

            # first check that the 3rd byte of the response is the command code that was issued
            if six.indexbytes(response, 2) == six.byte2int(cmd_code):
                # now check the checksum
                calc_checksum = self.calc_checksum(response[2:-1])
                resp_checksum = six.indexbytes(response, -1)
                if calc_checksum == resp_checksum:
                    # checksum check passed, response is deemed valid
                    return
                else:
                    # checksum check failed, raise an InvalidChecksum exception
                    _msg = "Invalid checksum in API response. " \
                           "Expected '%s' (0x%s), received '%s' (0x%s)." % (calc_checksum,
                                                                            "{:02X}".format(calc_checksum),
                                                                            resp_checksum,
                                                                            "{:02X}".format(resp_checksum))
                    raise InvalidChecksum(_msg)
            else:
                # command code check failed, raise an InvalidApiResponse exception
                exp_int = six.byte2int(cmd_code)
                resp_int = six.indexbytes(response, 2)
                _msg = "Invalid command code in API response. " \
                       "Expected '%s' (0x%s), received '%s' (0x%s)." % (exp_int,
                                                                        "{:02X}".format(exp_int),
                                                                        resp_int,
                                                                        "{:02X}".format(resp_int))
                raise InvalidApiResponse(_msg)

        @staticmethod
        def calc_checksum(data):
            """Calculate the checksum for a GW1000 API call or response.

            The checksum used on the GW1000 responses is simply the LSB of the
            sum of the bytes.

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
            """Attempt to rediscover a lost GW1000.

            Use UDP broadcast to discover a GW1000 that may have changed to a
            new IP. We should not be re-discovering a GW1000 for which the user
            specified and IP, only for those for which we discovered the IP
            address on startup. If a GW1000 is discovered then change my
            ip_address and port properties as necessary to use the device in
            future. If the rediscover was successful return True otherwise
            return False.
            """

            # we will only rediscover if we first discovered
            if self.ip_discovered:
                # log that we are attempting re-discovery
                if self.log_failures:
                    loginf("Attempting to re-discover GW1000...")
                # attempt to discover up to self.max_tries times
                for attempt in range(self.max_tries):
                    # sleep before our attempt, but not if its the first one
                    if attempt > 0:
                        time.sleep(self.retry_wait)
                    try:
                        # discover() returns a list of (ip address, port) tuples
                        ip_port_list = self.discover()
                    except socket.error as e:
                        # log the error
                        logdbg("Failed attempt %d to detect any GW1000: %s (%s)" % (attempt + 1,
                                                                                    e,
                                                                                    type(e)))
                    else:
                        # did we find any GW1000
                        if len(ip_port_list) > 0:
                            # we have at least one, log the fact as well as what we found
                            gw1000_str = ', '.join([':'.join(['%s:%d' % b]) for b in ip_port_list])
                            if len(ip_port_list) == 1:
                                stem = "GW1000 was"
                            else:
                                stem = "Multiple GW1000 were"
                            loginf("%s found at %s" % (stem, gw1000_str))
                            # keep our current IP address and port in case we
                            # don't find a match as we will change our
                            # ip_address and port properties in order to get
                            # the MAC for that IP address and port
                            present_ip = self.ip_address
                            present_port = self.port
                            # iterate over each candidate checking their MAC
                            # address against my mac property. This way we know
                            # we are connecting to the GW1000 we were
                            # previously using
                            for _ip, _port in ip_port_list:
                                self.ip_address = _ip.encode()
                                self.port = _port
                                # do the MACs match, if so we have our old
                                # device and we can exit the loop
                                if self.mac == self.get_mac_address():
                                    break
                            else:
                                # exhausted the ip_port_list without a match,
                                # revert to our old IP address and port
                                self.ip_address = present_ip
                                self.port = present_port
                                # and continue the outer loop if we have any
                                # attempts left
                                continue
                            # log the new IP address and port
                            loginf("GW1000 at address %s:%d will be used" % (self.ip_address.decode(),
                                                                             self.port))
                            # return True indicating the re-discovery was successful
                            return True
                        else:
                            # did not discover any GW1000 so log it
                            if self.log_failures:
                                logdbg("Failed attempt %d to detect any GW1000" % (attempt + 1,))
                else:
                    # we exhausted our attempts at re-discovery so log it
                    if self.log_failures:
                        loginf("Failed to detect original GW1000 after %d attempts" % (attempt + 1,))
            else:
                # an IP address was specified so we cannot go searching, log it
                if self.log_failures:
                    logdbg("IP address specified in 'weewx.conf', "
                           "re-discovery was not attempted")
            # if we made it here re-discovery was unsuccessful so return False
            return False

    class Parser(object):
        """Class to parse GW1000 sensor data."""

        multi_batt = {'wh40': {'mask': 1 << 4},
                      'wh26': {'mask': 1 << 5},
                      'wh25': {'mask': 1 << 6},
                      'wh65': {'mask': 1 << 7}
                      }
        wh31_batt = {1: {'mask': 1 << 0},
                     2: {'mask': 1 << 1},
                     3: {'mask': 1 << 2},
                     4: {'mask': 1 << 3},
                     5: {'mask': 1 << 4},
                     6: {'mask': 1 << 5},
                     7: {'mask': 1 << 6},
                     8: {'mask': 1 << 7}
                     }
        wh41_batt = {1: {'shift': 0, 'mask': 0x0F},
                     2: {'shift': 4, 'mask': 0x0F},
                     3: {'shift': 8, 'mask': 0x0F},
                     4: {'shift': 12, 'mask': 0x0F}
                     }
        wh51_batt = {1: {'mask': 1 << 0},
                     2: {'mask': 1 << 1},
                     3: {'mask': 1 << 2},
                     4: {'mask': 1 << 3},
                     5: {'mask': 1 << 4},
                     6: {'mask': 1 << 5},
                     7: {'mask': 1 << 6},
                     8: {'mask': 1 << 7},
                     9: {'mask': 1 << 8},
                     10: {'mask': 1 << 9},
                     11: {'mask': 1 << 10},
                     12: {'mask': 1 << 11},
                     13: {'mask': 1 << 12},
                     14: {'mask': 1 << 13},
                     15: {'mask': 1 << 14},
                     16: {'mask': 1 << 15}
                     }
        wh55_batt = {1: {'shift': 0, 'mask': 0xFF},
                     2: {'shift': 8, 'mask': 0xFF},
                     3: {'shift': 16, 'mask': 0xFF},
                     4: {'shift': 24, 'mask': 0xFF}
                     }
        wh57_batt = {'wh57': {}}
        wh68_batt = {'wh68': {}}
        ws80_batt = {'ws80': {}}
        batt = {
            'multi': (multi_batt, 'battery_mask'),
            'wh31': (wh31_batt, 'battery_mask'),
            'wh51': (wh51_batt, 'battery_mask'),
            'wh41': (wh41_batt, 'battery_value'),
            'wh57': (wh57_batt, 'battery_value'),
            'wh68': (wh68_batt, 'battery_voltage'),
            'ws80': (ws80_batt, 'battery_voltage'),
            'wh55': (wh55_batt, 'battery_value'),
            'unused': ({}, 'battery_mask')
        }
        batt_fields = ('multi', 'wh31', 'wh51', 'wh57', 'wh68', 'ws80',
                       'unused', 'wh41', 'wh55')
        battery_state_format = "<BBHBBBBHLBB"
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
        # Dictionary keyed by GW1000 response element containing various
        # parameters for each response 'field'. Dictionary tuple format
        # is (decode function name, size of data in bytes, GW1000 field name)
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

        # tuple of field codes for rain related fields in the GW1000 live data
        # so we can isolate these fields
        rain_field_codes = (b'\x0D', b'\x0E', b'\x0F', b'\x10',
                            b'\x11', b'\x12', b'\x13', b'\x14')
        # tuple of field codes for wind related fields in the GW1000 live data
        # so we can isolate these fields
        wind_field_codes = (b'\x0A', b'\x0B', b'\x0C', b'\x19')

        def __init__(self, is_wh24=False, debug_rain=False, debug_wind=False):
            # Tell our battery state decoding whether we have a WH24 or a WH65
            # (they both share the same battery state bit). By default we are
            # coded to use a WH65. But is there a WH24 connected?
            if is_wh24:
                # We have a WH24. On startup we are set for a WH65 but if it is
                # a restart we will likely already be setup for a WH24. We need
                # to handle both cases.
                if 'wh24' not in self.multi_batt.keys():
                    # we don't have a 'wh24' entry so create one, it's the same
                    # as the 'wh65' entry
                    self.multi_batt['wh24'] = self.multi_batt['wh65']
                    # and pop off the no longer needed WH65 decode dict entry
                    self.multi_batt.pop('wh65')
            else:
                # We don't have a WH24 but a WH65. On startup we are set for a
                # WH65 but if it is a restart it is possible we have already
                # been setup for a WH24. We need to handle both cases.
                if 'wh65' not in self.multi_batt.keys():
                    # we don't have a 'wh65' entry so create one, it's the same
                    # as the 'wh24' entry
                    self.multi_batt['wh65'] = self.multi_batt['wh24']
                    # and pop off the no longer needed WH65 decode dict entry
                    self.multi_batt.pop('wh24')
            # get debug_rain and debug_wind
            self.debug_rain = debug_rain
            self.debug_wind = debug_wind

        def parse(self, raw_data, timestamp=None):
            """Parse raw sensor data.

            Parse the raw sensor data and create a dict of sensor
            observations/status data. Add a timestamp to the data if one does
            not already exist.

            Returns a dict of observations/status data."""

            # obtain the response size, it's a big endian short (two byte) integer
            resp_size = struct.unpack(">H", raw_data[3:5])[0]
            # obtain the response
            resp = raw_data[5:5 + resp_size - 4]
            # log the actual sensor data as a sequence of bytes in hex
            if weewx.debug >= 3:
                logdbg("sensor data is '%s'" % (bytes_to_hex(resp),))
            data = {}
            if len(resp) > 0:
                index = 0
                while index < len(resp) - 1:
                    try:
                        decode_str, field_size, field = self.response_struct[resp[index:index + 1]]
                    except KeyError:
                        # We struck a field 'address' we do not know how to
                        # process. Ideally we would like to skip and move onto
                        # the next field (if there is one) but the problem is
                        # we do not know how long the data of this unknown
                        # field is. We could go on guessing the field data size
                        # by looking for the next field address but we won't
                        # know if we do find a valid field address is it a
                        # field address or data from this field? Of course this
                        # could also be corrupt data (unlikely though as it was
                        # decoded using a checksum). So all we can really do is
                        # accept the data we have so far, log the issue and
                        # ignore the remaining data.
                        logerr("Unknown field address '%s' detected. "
                               "Remaining sensor data ignored." % (bytes_to_hex(resp[index:index + 1]),))
                        break
                    else:
                        _field_data = getattr(self, decode_str)(resp[index + 1:index + 1 + field_size],
                                                                field)
                        data.update(_field_data)
                        if self.debug_rain and resp[index:index + 1] in self.rain_field_codes:
                            loginf("parse: raw rain data: field:%s and "
                                   "data:%s decoded as %s=%s" % (bytes_to_hex(resp[index:index + 1]),
                                                                 bytes_to_hex(resp[index + 1:index + 1 + field_size]),
                                                                 field,
                                                                 _field_data[field]))
                        if self.debug_wind and resp[index:index + 1] in self.wind_field_codes:
                            loginf("parse: raw wind data: field:%s and "
                                   "data:%s decoded as %s=%s" % (resp[index:index + 1],
                                                                 bytes_to_hex(resp[index + 1:index + 1 + field_size]),
                                                                 field,
                                                                 _field_data[field]))
                        index += field_size + 1
            # if it does not exist add a datetime field with the current epoch timestamp
            if 'datetime' not in data or 'datetime' in data and data['datetime'] is None:
                data['datetime'] = timestamp if timestamp is not None else int(time.time() + 0.5)
            return data

        @staticmethod
        def decode_temp(data, field=None):
            """Decode temperature data.

            Data is contained in a two byte big endian signed integer and
            represents tenths of a degree.
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

            Data is contained in a single unsigned byte and represents whole units.
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
            tenths of a unit.
            """

            if len(data) == 2:
                value = struct.unpack(">H", data)[0] / 10.0
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
            whole degrees.
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
            tenths of a unit.
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

            Unknown format but length is six bytes.
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
            from 0 to 40km.
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

            The GW1000 API claims to provide 'UTC time' as a 4 byte big endian
            integer. The 4 byte integer is a unix epoch timestamp; however,
            the timestamp is offset by the stations timezone. So for a station
            in the +10 hour timezone, the timestamp returned is the present
            epoch timestamp plus 10 * 3600 seconds.

            When decoded in localtime the decoded date-time is off by the
            station time zone, when decoded as GMT the date and time figures
            are correct but the timezone is incorrect.

            In any case decode the 4 byte big endian integer as is and any
            further use of this timestamp needs to take the above time zone
            offset into account when using the timestamp.
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

            Count is an integer stored in a 4 byte big endian integer."""

            if len(data) == 4:
                value = struct.unpack(">L", data)[0]
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

        def decode_wh34(self, data, fields=None):
            """Decode WH34 sensor data.

            Data consists of three bytes:

            Byte    Field               Comments
            1-2     temperature         standard Ecowitt temperature data, two
                                        byte big endian signed integer
                                        representing tenths of a degree
            3       battery voltage     0.02 * value Volts
            """

            if len(data) == 3 and fields is not None:
                results = dict()
                results[fields[0]] = self.decode_temp(data[0:2])
                # the battery_voltage method needs a number not a byte string
                # so we need to unpack the battery state data first
                batt_data = struct.unpack('B', data[2:3])[0]
                results[fields[1]] = self.battery_voltage(batt_data)
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
                # the battery_voltage method needs a number not a byte string
                # so we need to unpack the battery state data first
                batt_data = struct.unpack('B', data[15:16])[0]
                results[fields[8]] = self.battery_value(batt_data)
                return results
            return {}

        def decode_batt(self, data, field=None):
            """Decode battery status data.

            Battery status data is provided in 16 bytes using a variety of
            representations. Different representations include:
            -   use of a single bit to indicate low/OK
            -   use of a nibble to indicate battery level
            -   use of a byte to indicate battery voltage

            WH24, WH25, WH26(WH32), WH31, WH40, WH41 and WH51
            stations/sensors use a single bit per station/sensor to indicate OK or
            low battery. WH55 and WH57 sensors use a single byte per sensor to
            indicate OK or low battery. WH68 and WS80 sensors use a single byte to
            store battery voltage.

            The battery status data is allocated as follows
            Byte #  Sensor          Value               Comments
            byte 1  WH40(b4)        0/1                 1=low, 0=normal
                    WH26(WH32?)(b5) 0/1                 1=low, 0=normal
                    WH25(b6)        0/1                 1=low, 0=normal
                    WH24(b7)        0/1                 may be WH65, 1=low, 0=normal
                 2  WH31 ch1(b0)    0/1                 1=low, 0=normal, 8 channels b0..b7
                         ...
                         ch8(b7)    0/1                 1=low, 0=normal
                 3  WH51 ch1(b0)    0/1                 1=low, 0=normal, 16 channels b0..b7 over 2 bytes
                         ...
                         ch8(b7)    0/1                 1=low, 0=normal
                 4       ch9(b0)    0/1                 1=low, 0=normal
                         ...
                         ch16(b7)   0/1                 1=low, 0=normal
                 5  WH57            0-5                 <=1 is low
                 6  WH68            0.02*value Volts
                 7  WS80            0.02*value Volts
                 8  Unused
                 9  WH41 ch1(b0-b3) 0-5                 <=1 is low
                         ch2(b4-b7) 0-5                 <=1 is low
                 10      ch3(b0-b3) 0-5                 <=1 is low
                         ch4(b4-b7) 0-5                 <=1 is low
                 11 WH55 ch1        0-5                 <=1 is low
                 12 WH55 ch2        0-5                 <=1 is low
                 13 WH55 ch3        0-5                 <=1 is low
                 14 WH55 ch4        0-5                 <=1 is low
                 15 Unused
                 16 Unused

            For stations/sensors using a single bit for battery status 0=OK and
            1=low. For stations/sensors using a single byte for battery
            status >1=OK and <=1=low. For stations/sensors using a single byte for
            battery voltage the voltage is 0.02 * the byte value.

                # WH24 F/O THWR sensor station
                # WH25 THP sensor
                # WH26(WH32) TH sensor
                # WH40 rain gauge sensor
            """

            if len(data) == 16:
                # first break out the bytes
                b_dict = {}
                batt_t = struct.unpack(self.battery_state_format, data)
                batt_dict = dict(six.moves.zip(self.batt_fields, batt_t))
                for batt_field in self.batt_fields:
                    elements, decode_str = self.batt[batt_field]
                    for elm in elements.keys():
                        # construct the field name for our battery value, how
                        # we construct the field name will depend if we have a
                        # numeric channel or not
                        # assume no numeric channel
                        try:
                            field_name = "".join([elm, '_batt'])
                        except TypeError:
                            # if we strike a TypeError it will be because we
                            # have a numeric channel number
                            field_name = ''.join([batt_field, '_ch', str(elm), '_batt'])
                        # now add the battery value to the result dict
                        b_dict[field_name] = getattr(self, decode_str)(batt_dict[batt_field],
                                                                       **elements[elm])
                return b_dict
            return {}

        @staticmethod
        def battery_mask(data, mask):
            if (data & mask) == mask:
                return 1
            return 0

        @staticmethod
        def battery_value(data, mask=None, shift=None):
            _data = data if shift is None else data >> shift
            if mask is not None:
                _value = _data & mask
                if _value == mask:
                    _value = None
            else:
                _value = _data
            return _value

        @staticmethod
        def battery_voltage(data):
            return 0.02 * data

        @staticmethod
        def binary_desc(value):
            if value is not None:
                if value == 0:
                    return "OK"
                elif value == 1:
                    return "low"
                else:
                    return None
            return None

        @staticmethod
        def voltage_desc(value):
            if value is not None:
                if value <= 1.2:
                    return "low"
                else:
                    return "OK"
            return None

        @staticmethod
        def level_desc(value):
            if value is not None:
                if value <= 1:
                    return "low"
                elif value == 6:
                    return "DC"
                else:
                    return "OK"
            return None


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

        http://nedbatchelder.com/blog/200712/human_sorting.html (See
        Toothy's implementation in the comments)
        """

        return [atoi(c) for c in re.split(r'(\d+)', text)]

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
    alphabetical order by key assists in the analysis of the the dict data.
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
        # try again coercing iterbale to a bytestring
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

    def ip_from_config_opts(opts, stn_dict):
        """Obtain the IP address from station config or command line options.

        Determine the IP address to use given a station config dict and command
        line options. The IP address is chosen as follows:
        - if specified use the ip address from the command line
        - if an IP address was not specified on the command line obtain the IP
          address from the station config dict
        - if the station config dict does not specify an IP address, or if it
          is set to 'auto', return None to force device discovery
        """

        # obtain an ip address from the command line options
        ip_address = opts.ip_address if opts.ip_address else None
        # if we didn't get an ip address check the station config dict
        if ip_address is None:
            # obtain the ip address from the station config dict
            ip_address = stn_dict.get('ip_address')
            # if the station config dict specifies some variation of 'auto'
            # then we need to return None to force device discovery
            if ip_address is not None:
                # do we have a variation of 'auto'
                if ip_address.lower() == 'auto':
                    # we need to autodetect ip address so set to None
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

    def port_from_config_opts(opts, stn_dict):
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
        port = opts.port if opts.port else None
        # if we didn't get a port number check the station config dict
        if port is None:
            # obtain the port number from the station config dict
            port = stn_dict.get('port')
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

    def system_params(opts, stn_dict):
        """Display system parameters.

        Obtain and display the GW1000 system parameters. GW1000 IP address and
        port are derived (in order) as follows:
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
        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a GW1000 Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address,
                                        port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the collector objects system_parameters property
            sys_params_dict = collector.system_parameters
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            # socket timeout so inform the user
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            # create a meaningful string for frequency representation
            freq_str = freq_decode.get(sys_params_dict['frequency'], 'Unknown')
            # if sensor_type is 0 there is a WH24 connected, if its a 1 there
            # is a WH65
            _is_wh24 = sys_params_dict['sensor_type'] == 0
            # string to use in sensor type message
            _sensor_type_str = 'WH24' if _is_wh24 else 'WH65'
            # print the system parameters
            print()
            print("GW1000 frequency: %s (%s)" % (sys_params_dict['frequency'],
                                                 freq_str))
            print("GW1000 sensor type: %s (%s)" % (sys_params_dict['sensor_type'],
                                                   _sensor_type_str))
            # The GW1000 API returns what is labelled "UTC" but is in fact the
            # current epoch timestamp adjusted by the station timezone offset.
            # So when the timestamp is converted to a human readable GMT
            # date-time string it in fact shows the local date-time. We can
            # work around this by formatting this offset UTC timestamp as a UTC
            # date-time but then calling it local time. ideally we would
            # re-adjust to remove the timezone offset to get the real
            # (unadjusted) epoch timestamp but since the timezone index is
            # stored as an arbitrary number rather than an offset in seconds
            # this is not possible. We can only do what we can.
            date_time_str = time.strftime("%-d %B %Y %H:%M:%S",
                                          time.gmtime(sys_params_dict['utc']))
            print("GW1000 date-time: %s" % date_time_str)
            print("GW1000 timezone index: %s" % (sys_params_dict['timezone_index'],))
            print("GW1000 DST status: %s" % (sys_params_dict['dst_status'],))

    def get_rain_data(opts, stn_dict):
        """Display the GW1000 rain data.

        Obtain and display the GW1000 rain data. GW1000 IP address and port are
        derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a GW1000 Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address,
                                        port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the collector objects get_rain_data property
            rain_data = collector.rain_data
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            print()
            print("%10s: %.1f mm/%.1f in" % ('Rain rate', rain_data['rain_rate'], rain_data['rain_rate'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Day rain', rain_data['rain_day'], rain_data['rain_day'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Week rain', rain_data['rain_week'], rain_data['rain_week'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Month rain', rain_data['rain_month'], rain_data['rain_month'] / 25.4))
            print("%10s: %.1f mm/%.1f in" % ('Year rain', rain_data['rain_year'], rain_data['rain_year'] / 25.4))

    def get_mulch_offset(opts, stn_dict):
        """Display the multi-channel temperature and humidity offset data from
        a GW1000.

        Obtain and display the multi-channel temperature and humidity offset
        data from the selected GW1000. GW1000 IP address and port are derived
        (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address, port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the mulch offset data from the collector object's mulch_offset
            # property
            mulch_offset_data = collector.mulch_offset
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            # did we get any mulch offset data
            if mulch_offset_data is not None:
                # now format and display the data
                print()
                print("Multi-channel Temperature and Humidity Calibration")
                # iterate over each channel for which we have data
                for channel in mulch_offset_data:
                    # print the channel and offset data
                    mulch_str = "Channel %d: Temperature offset: %5s Humidity offset: %3s"
                    # the API returns channels starting at 0, but the WS View
                    # app displays channels starting at 1, so add 1 to our
                    # channel number
                    print(mulch_str % (channel+1,
                                       "%2.1f" % mulch_offset_data[channel]['temp'],
                                       "%d" % mulch_offset_data[channel]['hum']))
            else:
                print()
                print("GW1000 did not respond.")

    def get_pm25_offset(opts, stn_dict):
        """Display the PM2.5 offset data from a GW1000.

        Obtain and display the PM2.5 offset data from the selected GW1000.
        GW1000 IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address, port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the PM2.5 offset data from the collector object's pm25_offset
            # property
            pm25_offset_data = collector.pm25_offset
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            # did we get any PM2.5 offset data
            if pm25_offset_data is not None:
                # now format and display the data
                print()
                print("PM2.5 Calibration")
                # iterate over each channel for which we have data
                for channel in pm25_offset_data:
                    # print the channel and offset data
                    print("Channel %d PM2.5 offset: %5s" % (channel, "%2.1f" % pm25_offset_data[channel]))
            else:
                print()
                print("GW1000 did not respond.")

    def get_co2_offset(opts, stn_dict):
        """Display the WH45 CO2, PM10 and PM2.5 offset data from a GW1000.

        Obtain and display the WH45 CO2, PM10 and PM2.5 offset data from the
        selected GW1000. GW1000 IP address and port are derived (in order) as
        follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address, port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the offset data from the collector object's co2_offset
            # property
            co2_offset_data = collector.co2_offset
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            # did we get any offset data
            if co2_offset_data is not None:
                # now format and display the data
                print()
                print("CO2 Calibration")
                print("CO2 offset: %5s" % ("%2.1f" % co2_offset_data['co2']))
                print("PM10 offset: %5s" % ("%2.1f" % co2_offset_data['pm10']))
                print("PM2.5 offset: %5s" % ("%2.1f" % co2_offset_data['pm25']))
            else:
                print()
                print("GW1000 did not respond.")

    def get_calibration(opts, stn_dict):
        """Display the calibration data from a GW1000.

        Obtain and display the calibration data from the selected GW1000.
        GW1000 IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address, port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the calibration data from the collector object's calibration
            # property
            calibration_data = collector.calibration
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            # did we get any calibration data
            if calibration_data is not None:
                # now format and display the data
                print()
                print("Calibration")
                print("%26s: %4.1f" % ("Solar radiation gain", calibration_data['solar']))
                print("%26s: %4.1f" % ("UV gain", calibration_data['uv']))
                print("%26s: %4.1f" % ("Wind gain", calibration_data['wind']))
                print("%26s: %4.1f" % ("Rain gain", calibration_data['rain']))
                print("%26s: %4.1f %sC" % ("Inside temperature offset", calibration_data['intemp'], u'\xb0'))
                print("%26s: %4.1f %%" % ("Inside humidity offset", calibration_data['inhum']))
                print("%26s: %4.1f hPa" % ("Absolute pressure offset", calibration_data['abs']))
                print("%26s: %4.1f hPa" % ("Relative pressure offset", calibration_data['rel']))
                print("%26s: %4.1f %sC" % ("Outside temperature offset", calibration_data['outtemp'], u'\xb0'))
                print("%26s: %4.1f %%" % ("Outside humidity offset", calibration_data['outhum']))
                print("%26s: %4.1f %s" % ("Wind direction offset", calibration_data['dir'], u'\xb0'))
            else:
                print()
                print("GW1000 did not respond.")

    def get_soil_calibration(opts, stn_dict):
        """Display the soil moisture sensor calibration data from a GW1000.

        Obtain and display the soil moisture sensor calibration data from the
        selected GW1000. GW1000 IP address and port are derived (in order) as
        follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address, port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the calibration data from the collector object's
            # soil_calibration property
            calibration_data = collector.soil_calibration
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
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
                    # the API returns channels starting at 0, but the WS View
                    # app displays channels starting at 1, so add 1 to our
                    # channel number
                    print("Channel %d (%d%%)" % (channel+1, channel_dict['humidity']))
                    print("%12s: %d" % ("Now AD", channel_dict['ad']))
                    print("%12s: %d" % ("0% AD", channel_dict['adj_min']))
                    print("%12s: %d" % ("100% AD", channel_dict['adj_max']))
            else:
                print()
                print("GW1000 did not respond.")

    def get_services(opts, stn_dict):
        """Display the GW1000 Weather Services settings.

        Obtain and display the settings for the various weather services
        supported by the GW1000. GW1000 IP address and port are derived (in
        order) as follows:
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
                # GW1000 MAC
                print("%22s: %s" % ("MAC", data_dict['mac']))

        def print_wunderground(data_dict=None):
            """Print Weather Underground settings."""

            # do we have any settings?
            if data_dict is not None:
                # Station ID
                id = data_dict['id'] if opts.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Station ID", id))
                # Station key
                key = data_dict['password'] if opts.unmask else obfuscate(data_dict['password'])
                print("%22s: %s" % ("Station Key", key))

        def print_weathercloud(data_dict=None):
            """Print Weathercloud settings."""

            # do we have any settings?
            if data_dict is not None:
                # Weathercloud ID
                id = data_dict['id'] if opts.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Weathercloud ID", id))
                # Weathercloud key
                key = data_dict['key'] if opts.unmask else obfuscate(data_dict['key'])
                print("%22s: %s" % ("Weathercloud Key", key))

        def print_wow(data_dict=None):
            """Print Weather Observations Website settings."""

            # do we have any settings?
            if data_dict is not None:
                # Station ID
                id = data_dict['id'] if opts.unmask else obfuscate(data_dict['id'])
                print("%22s: %s" % ("Station ID", id))
                # Station key
                key = data_dict['password'] if opts.unmask else obfuscate(data_dict['password'])
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
                    id = data_dict['id'] if opts.unmask else obfuscate(data_dict['id'])
                    print("%22s: %s" % ("Station ID", id))
                    key = data_dict['password'] if opts.unmask else obfuscate(data_dict['password'])
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

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a GW1000 Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address,
                                        port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # get the settings for each service know to the GW1000, store them
            # in a dict keyed by the service name
            services_data = dict()
            for service in collector.services:
                services_data[service['name']] = getattr(collector, service['name'])
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
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
                print("GW1000 did not respond.")

    def station_mac(opts, stn_dict):
        """Display the GW1000 hardware MAC address.

        Obtain and display the hardware MAC address of the selected GW1000.
        GW1000 IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a GW1000 Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address,
                                        port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # call the driver objects mac_address() method
            print()
            print("GW1000 MAC address: %s" % (collector.mac_address,))
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")

    def firmware(opts, stn_dict):
        """Display the firmware version string from a GW1000.

        Obtain and display the firmware version string from the selected
        GW1000. GW1000 IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address, port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # call the driver objects firmware_version() method
            print()
            print("GW1000 firmware version string: %s" % (collector.firmware_version,))
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")

    def sensors(opts, stn_dict):
        """Display the sensor ID information from a GW1000.

        Obtain and display the sensor ID information from the selected GW1000.
        GW1000 IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address,
                                        port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # call the driver objects get_sensor_ids() method
            sensor_id_data = collector.sensor_id_data
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            # did we get any sensor ID data
            if sensor_id_data is not None:
                # now format and display the data
                print()
                print("%-10s %s" % ("Sensor", "Status"))
                # iterate over each sensor for which we have data
                for sensor in sensor_id_data:
                    # sensor address
                    address = sensor['address']
                    # the sensor id indicates whether it is disabled, attempting to
                    # register a sensor or already registered
                    if sensor.get('id') == 'fffffffe':
                        state = 'sensor is disabled'
                    elif sensor.get('id') == 'ffffffff':
                        state = 'sensor is registering...'
                    else:
                        # the sensor is registered so we should have signal and battery
                        # data as well
                        sensor_model = Gw1000Collector.sensor_ids[address].get('name').split("_")[0]
                        battery_desc = getattr(collector.parser,
                                               collector.parser.battery_state_desc[sensor_model])(sensor.get('battery'))
                        battery_str = "%s (%s)" % (sensor.get('battery'), battery_desc)
                        state = "sensor ID: %s  signal: %s  battery: %s" % (sensor.get('id').strip('0'),
                                                                            sensor.get('signal'),
                                                                            battery_str)
                        # print the formatted data
                    print("%-10s %s" % (Gw1000Collector.sensor_ids[address].get('long_name'), state))
            else:
                print()
                print("GW1000 did not respond.")

    def live_data(opts, stn_dict):
        """Display live sensor data from a GW1000.

        Obtain and display live sensor data from the selected GW1000. GW1000
        IP address and port are derived (in order) as follows:
        1. command line --ip-address and --port parameters
        2. [GW1000] stanza in the specified config file
        3. by discovery
        """

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Collector object
            collector = Gw1000Collector(ip_address=ip_address,
                                        port=port)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                     collector.station.port))
            # call the driver objects get_live_sensor_data() method
            live_sensor_data_dict = collector.get_live_sensor_data()
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            print()
            print("GW1000 live sensor data: %s" % weeutil.weeutil.to_sorted_string(live_sensor_data_dict))

    def discover():
        """Display IP address and port data of GW1000s on the local network."""

        # get an Gw1000Collector object
        collector = Gw1000Collector()
        print()
        # call the Gw1000Collector object discover() method, wrap in a try so we can
        # catch any socket timeouts
        try:
            ip_port_list = collector.station.discover()
        except socket.timeout:
            print("Timeout. No GW1000 discovered.")
        else:
            if len(ip_port_list) > 0:
                # we have at least one result
                # first sort our list by IP address
                sorted_list = sorted(ip_port_list, key=itemgetter(0))
                found = False
                gw1000_found = 0
                for (ip, port) in sorted_list:
                    if ip is not None and port is not None:
                        print("GW1000 discovered at IP address %s on port %d" % (ip, port))
                        found = True
                        gw1000_found += 1
                else:
                    if gw1000_found > 1:
                        print()
                        print("Multiple GW1000 were found.")
                        print("If using the GW1000 driver consider explicitly specifying the IP address")
                        print("and port of the GW1000 to be used under [GW1000] in weewx.conf.")
                    if not found:
                        print("No GW1000 was discovered.")
            else:
                # we have no results
                print("No GW1000 was discovered.")

    def field_map():
        """Display the default field map."""

        # obtain a copy of the default field map, we need a copy so we can
        # augment it with the battery state map
        field_map = dict(Gw1000.default_field_map)
        # now add in the battery state field map
        field_map.update(Gw1000.battery_field_map)
        # now add in the sensor signal field map
        field_map.update(Gw1000.sensor_signal_field_map)
        print()
        print("GW1000 driver/service default field map:")
        print("(format is WeeWX field name: GW1000 field name)")
        print()
        # obtain a list of naturally sorted dict keys so that, for example,
        # xxxxx16 appears in the correct order
        keys_list = natural_sort_keys(field_map)
        # iterate over the sorted keys and print the key and item
        for key in keys_list:
            print("    %23s: %s" % (key, field_map[key]))

    def test_driver(opts, stn_dict):
        """Run the GW1000 driver.

        Exercises the GW1000 driver only. Loop packets, but no archive records,
        are emitted to the console continuously until a keyboard interrupt is
        received. A station config dict is coalesced from any relevant command
        line parameters and the config file in use with command line parameters
        overriding those in the config file.
        """

        loginf("Testing GW1000 driver...")
        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # set the IP address and port in the station config dict
        stn_dict['ip_address'] = ip_address
        stn_dict['port'] = port
        if opts.poll_interval:
            stn_dict['poll_interval'] = opts.poll_interval
        if opts.max_tries:
            stn_dict['max_tries'] = opts.max_tries
        if opts.retry_wait:
            stn_dict['retry_wait'] = opts.retry_wait
        # wrap in a try..except in case there is an error
        try:
            # get a Gw1000Driver object
            driver = Gw1000Driver(**stn_dict)
            # identify the GW1000 being used
            print()
            print("Interrogating GW1000 at %s:%d" % (driver.collector.station.ip_address.decode(),
                                                     driver.collector.station.port))
            print()
            # continuously get loop packets and print them to screen
            for pkt in driver.genLoopPackets():
                print(": ".join([weeutil.weeutil.timestamp_to_string(pkt['dateTime']),
                                 weeutil.weeutil.to_sorted_string(pkt)]))
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except KeyboardInterrupt:
            # we have a keyboard interrupt so shut down
            driver.closePort()
        loginf("GW1000 driver testing complete")

    def test_service(opts, stn_dict):
        """Test the GW1000 service.

        Uses a dummy engine/simulator to generate arbitrary loop packets for
        augmenting. Use a 10 second loop interval so we don't get too many bare
        packets.
        """

        loginf("Testing GW1000 service...")
        # Create a dummy config so we can stand up a dummy engine with a dummy
        # simulator emitting arbitrary loop packets. Include the GW1000 service
        # and StdPrint, StdPrint will take care of printing our loop packets
        # (no StdArchive so loop packets only, no archive records)
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
                    'archive_services': 'user.gw1000.Gw1000Service',
                    'report_services': 'weewx.engine.StdPrint'}}}
        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # set the IP address and port in the dummy config
        config['GW1000']['ip_address'] = ip_address
        config['GW1000']['port'] = port
        # these command line options should only be added if they exist
        if opts.poll_interval:
            config['GW1000']['poll_interval'] = opts.poll_interval
        if opts.max_tries:
            config['GW1000']['max_tries'] = opts.max_tries
        if opts.retry_wait:
            config['GW1000']['retry_wait'] = opts.retry_wait
        # assign our dummyTemp field to a unit group so unit conversion works
        # properly
        weewx.units.obs_group_dict['dummyTemp'] = 'group_temperature'
        # wrap in a try..except in case there is an error
        try:
            # create a dummy engine
            engine = weewx.engine.StdEngine(config)
            # Our GW1000 service will have been instantiated by the engine during
            # its startup. Whilst access to the service is not normally required we
            # require access here so we can obtain some info about the station we
            # are using for this test. The engine does not provide a ready means to
            # access that GW1000 service so we can do a bit of guessing and iterate
            # over all of the engine's services and select the one that has a
            # 'collector' property. Unlikely to cause a problem since there are
            # only two services in the dummy engine.
            gw1000_svc = None
            for svc in engine.service_obj:
                if hasattr(svc, 'collector'):
                    gw1000_svc = svc
            if gw1000_svc is not None:
                # identify the GW1000 being used
                print()
                print("Interrogating GW1000 at %s:%d" % (gw1000_svc.collector.station.ip_address.decode(),
                                                         gw1000_svc.collector.station.port))
            print()
            while True:
                # create an arbitrary loop packet, all it needs is a timestamp, a
                # defined unit system and a token obs
                packet = {'dateTime': int(time.time()),
                          'usUnits': weewx.US,
                          'dummyTemp': 96.3
                          }
                # send out a NEW_LOOP_PACKET event with the dummy loop packet
                # to trigger the GW1000 service to augment the loop packet
                engine.dispatchEvent(weewx.Event(weewx.NEW_LOOP_PACKET,
                                                 packet=packet,
                                                 origin='software'))
                # sleep for a bit to emulate the simulator
                time.sleep(10)
        except GW1000IOError as e:
            print()
            print("Unable to connect to GW1000: %s" % e)
        except KeyboardInterrupt:
            engine.shutDown()
        loginf("GW1000 service testing complete")

    usage = """Usage: python -m user.gw1000 --help
       python -m user.gw1000 --version
       python -m user.gw1000 --test-driver|--test-service
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--poll-interval=INTERVAL]
            [--max-tries=MAX_TRIES]
            [--retry-wait=RETRY_WAIT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --sensors
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --live-data
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --firmware-version|--mac-address|
            --system-params|--get-rain-data
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --get-mulch-offset|--get-pm25-offset|
            --get-calibration|--get-soil-calibration|--get-co2-offset
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --get-services
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--unmask] [--debug=0|1|2|3]     
       python -m user.gw1000 --discover
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--debug=0|1|2|3]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display GW1000 driver version number')
    parser.add_option('--config', dest='config_path', metavar='CONFIG_FILE',
                      help="Use configuration file CONFIG_FILE.")
    parser.add_option('--debug', dest='debug', type=int,
                      help='How much status to display, 0-3')
    parser.add_option('--discover', dest='discover', action='store_true',
                      help='discover GW1000 and display its IP address '
                           'and port')
    parser.add_option('--firmware-version', dest='firmware',
                      action='store_true',
                      help='display GW1000 firmware version')
    parser.add_option('--mac-address', dest='mac', action='store_true',
                      help='display GW1000 station MAC address')
    parser.add_option('--system-params', dest='sys_params', action='store_true',
                      help='display GW1000 system parameters')
    parser.add_option('--sensors', dest='sensors', action='store_true',
                      help='display GW1000 sensor information')
    parser.add_option('--live-data', dest='live', action='store_true',
                      help='display GW1000 sensor data')
    parser.add_option('--get-rain-data', dest='get_rain', action='store_true',
                      help='display GW1000 rain data')
    parser.add_option('--get-mulch-offset', dest='get_mulch_offset',
                      action='store_true',
                      help='display GW1000 multi-channel temperature and '
                      'humidity offset data')
    parser.add_option('--get-pm25-offset', dest='get_pm25_offset',
                      action='store_true',
                      help='display GW1000 PM2.5 offset data')
    parser.add_option('--get-co2-offset', dest='get_co2_offset',
                      action='store_true',
                      help='display GW1000 CO2 (WH45) offset data')
    parser.add_option('--get-calibration', dest='get_calibration',
                      action='store_true',
                      help='display GW1000 calibration data')
    parser.add_option('--get-soil-calibration', dest='get_soil_calibration',
                      action='store_true',
                      help='display GW1000 soil moisture calibration data')
    parser.add_option('--get-services', dest='get_services',
                      action='store_true',
                      help='display GW1000 weather services configuration data')
    parser.add_option('--default-map', dest='map', action='store_true',
                      help='display the default field map')
    parser.add_option('--test-driver', dest='test_driver', action='store_true',
                      metavar='TEST_DRIVER', help='test the GW1000 driver')
    parser.add_option('--test-service', dest='test_service',
                      action='store_true',
                      metavar='TEST_SERVICE', help='test the GW1000 service')
    parser.add_option('--ip-address', dest='ip_address',
                      help='GW1000 IP address to use')
    parser.add_option('--port', dest='port', type=int,
                      help='GW1000 port to use')
    parser.add_option('--poll-interval', dest='poll_interval', type=int,
                      help='GW1000 port to use')
    parser.add_option('--max-tries', dest='max_tries', type=int,
                      help='GW1000 port to use')
    parser.add_option('--retry-wait', dest='retry_wait', type=int,
                      help='GW1000 port to use')
    parser.add_option('--unmask', dest='unmask', action='store_true',
                      help='unmask sensitive settings')
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

    # Now we can set up the user customized logging but we need to handle both
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

    # run the driver
    if opts.test_driver:
        test_driver(opts, stn_dict)
        exit(0)

    # run the service with simulator
    if opts.test_service:
        test_service(opts, stn_dict)
        exit(0)

    if opts.sys_params:
        system_params(opts, stn_dict)
        exit(0)

    if opts.get_rain:
        get_rain_data(opts, stn_dict)
        exit(0)

    if opts.get_mulch_offset:
        get_mulch_offset(opts, stn_dict)
        exit(0)

    if opts.get_pm25_offset:
        get_pm25_offset(opts, stn_dict)
        exit(0)

    if opts.get_co2_offset:
        get_co2_offset(opts, stn_dict)
        exit(0)

    if opts.get_calibration:
        get_calibration(opts, stn_dict)
        exit(0)

    if opts.get_soil_calibration:
        get_soil_calibration(opts, stn_dict)
        exit(0)

    if opts.get_services:
        get_services(opts, stn_dict)
        exit(0)

    if opts.mac:
        station_mac(opts, stn_dict)
        exit(0)

    if opts.firmware:
        firmware(opts, stn_dict)
        exit(0)

    if opts.sensors:
        sensors(opts, stn_dict)
        exit(0)

    if opts.live:
        live_data(opts, stn_dict)
        exit(0)

    if opts.discover:
        discover()
        exit(0)

    if opts.map:
        field_map()
        exit(0)

    # if we made it here no option was selected so display our help
    parser.print_help()


if __name__ == '__main__':
    main()
