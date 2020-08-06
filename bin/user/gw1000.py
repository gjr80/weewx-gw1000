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

Version: 0.1.0b11                                 Date: 5 August 2020

Revision History
    ?? ????? 2020      v0.1.0
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

Note. Whilst the driver may be run independently of WeeWX the driver still
requires WeeWX and it's dependencies be installed. Consequently, if WeeWX 4.0.0
or later is installed the driver must be run under the same Python version as
WeeWX uses. This means that on some systems 'python' in the above commands may
need to be changed to 'python2' or 'python3'.

Note. The nature of the GW1000 API and the GW1000 driver mean that the GW1000
driver can be run directly from the command line while the GW1000 continues to
serve data to any existing drivers/services. This makes it possible to
configure and test the GW1000 driver without taking an existing GW1000 based
system off-line.

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
            [[24havpm251]]
                extractor = last
            [[24havpm252]]
                extractor = last
            [[24havpm253]]
                extractor = last
            [[24havpm254]]
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

    $ sudo /etc/init.d/weewx start

    or

    $ sudo service weewx start

    or

    $ sudo systemctl start weewx
"""
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
# TODO. Test service shutdown when network lost

# Python imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import socket
import struct
import threading
import time
from operator import itemgetter

# python 2/3 compatibility shim
import six

# WeeWX imports
import weecfg
import weeutil.weeutil
import weewx.drivers
import weewx.engine
import weewx.wxformulas

# import/setup logging, WeeWX v3 is syslog based but WeeWX v4 is logging based,
# try v4 logging and if it fails use v3 logging
try:
    # WeeWX4 logging
    import logging
    from weeutil.logger import log_traceback

    log = logging.getLogger("%s: %s" % ('gw1000', __name__))


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
DRIVER_VERSION = '0.1.0b11'

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
# When run as a service the default age in seconds after which GW1000 API data
# is considered stale and will not be used to augment loop packets
default_max_age = 60
# default GW1000 poll interval
default_poll_interval = 60


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
        'windDir': 'winddir',
        'windSpeed': 'windspeed',
        'windGust': 'gustspeed',
        'rain': 'rain',
        'stormRain': 'rainevent',
        'rainRate': 'rainrate',
        'hourRain': 'rainhour',
        'dayRain': 'rainday',
        'weekRain': 'rainweek',
        'monthRain': 'rainmonth',
        'yearRain': 'rainyear',
        'totalRain': 'raintotals',
        'luminosity': 'light',
        'uvradiation': 'uv',
        'UV': 'uvi',
        'dateTime': 'datetime',
        'daymaxwind': 'daymaxwind',
        'extraTemp1': 'temp1',
        'extraTemp2': 'temp2',
        'extraTemp3': 'temp3',
        'extraTemp4': 'temp4',
        'extraTemp5': 'temp5',
        'extraTemp6': 'temp6',
        'extraTemp7': 'temp7',
        'extraTemp8': 'temp8',
        'extraHumid1': 'humid1',
        'extraHumid2': 'humid2',
        'extraHumid3': 'humid3',
        'extraHumid4': 'humid4',
        'extraHumid5': 'humid5',
        'extraHumid6': 'humid6',
        'extraHumid7': 'humid7',
        'extraHumid8': 'humid8',
        'pm2_5': 'pm251',
        'pm2_52': 'pm252',
        'pm2_53': 'pm253',
        'pm2_54': 'pm254',
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
        '24havpm251': '24havpm251',
        '24havpm252': '24havpm252',
        '24havpm253': '24havpm253',
        '24havpm254': '24havpm254',
        'leak1': 'leak1',
        'leak2': 'leak2',
        'leak3': 'leak3',
        'leak4': 'leak4',
        'lightning_distance': 'lightningdist',
        'lightning_last_det_time': 'lightningdettime',
        'lightning_strike_count': 'lightning_strike_count'
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
            # now add in the battery state field map
            field_map.update(Gw1000.battery_field_map)
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
            for k,v in six.iteritems(field_map_copy):
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
        # how many times to poll the API before giving up, default is 3
        self.max_tries = int(gw1000_config.get('max_tries', 3))
        # wait time in seconds between retries, default is 10 seconds
        self.retry_wait = int(gw1000_config.get('retry_wait', 10))
        # how often (in seconds) we should poll the API, default is 60 seconds
        self.poll_interval = int(gw1000_config.get('poll_interval', 60))
        # age (in seconds) before API data is considered too old to use,
        # default is 60 seconds
        self.max_age = int(gw1000_config.get('max_age', default_max_age))
        # Is a WH32 in use. WH32 TH sensor can override/provide outdoor TH data
        # to the GW1000. In tems of TH data the process is transparent and we
        # do not need to know if a WH32 or other sensor is providing outdoor TH
        # data but in terms of battery state we need to know so the battery
        # state data can be reported against the correct sensor.
        use_th32 = weeutil.weeutil.tobool(gw1000_config.get('th32', False))
        # what does the collector do if it strikes an IO error after startup,
        # does it retry forever or cause WeeWX to exit
        loop_on_ioerror = weeutil.weeutil.tobool(gw1000_config.get('loop_on_ioerror',
                                                                   True))
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
                                         loop_on_ioerror=loop_on_ioerror)
        # initialise last lightning count and last rain properties
        self.last_lightning = None
        self.last_rain = None
        self.rain_mapping_confirmed = False
        self.rain_total_field = None
        # finally log any config that is not being pushed any further down
        # sensor map to be used
        # Dict output will be in unsorted key order. It is easier to read if
        # sorted alphanumerically but we have keys such as xxxxx16 that do not
        # sort well. Use a custom natural sort of the keys in a manually
        # produced formatted dict representation.
        sorted_dict_fields = ["'%s': '%s'" % (k, self.field_map[k]) for k in natural_sort_dict(self.field_map)]
        sorted_dict_str = "{%s}" % ", ".join(sorted_dict_fields)
        loginf('field map is %s' % sorted_dict_str)

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

    def get_cumulative_rain_field(self, parsed_data):
        """Determine the cumulative rain field used to derive field 'rain'.

        Ecowitt rain gauges/GW1000 emit various rain totals but WeeWX needs a
        per period value for field rain. Try the 'big' (4 byte) counters
        starting at the longest period and working our way down. This should
        only need be done once.
        """

        # if raintotals is present used that as our first choice
        if 'raintotals' in parsed_data:
            self.rain_total_field = 'raintotals'
            self.rain_mapping_confirmed = True
        # raintotals is not present so now try rainyear
        elif 'rainyear' in parsed_data:
            self.rain_total_field = 'rainyear'
            self.rain_mapping_confirmed = True
        # rainyear is not present so now try rainmonth
        elif 'rainmonth' in parsed_data:
            self.rain_total_field = 'rainmonth'
            self.rain_mapping_confirmed = True
        # otherwise do nothing, we can try again next packet
        else:
            self.rain_total_field = None
        # if we found a field log what we are using
        if self.rain_mapping_confirmed:
            loginf("using '%s' for rain total" % self.rain_total_field)

    def calculate_rain(self, parsed_data):
        """Calculate total rainfall for a period.

        'rain' is calculated as the change in a user designated cumulative rain
        field between successive periods. 'rain' is only calculated if the
        field to be used has been selected and the designated field exists.
        """

        # have we decided on a field to use and is the field present
        if self.rain_mapping_confirmed and self.rain_total_field in parsed_data:
            # yes on both counts, so get the new total
            new_total = parsed_data[self.rain_total_field]
            # now calculate field rain as the difference between the new and
            # old totals
            parsed_data['rain'] = self.delta_rain(new_total, self.last_rain)
            # save the new total as the old total for next time
            self.last_rain = new_total

    def calculate_lightning_count(self, parsed_data):
        """Calculate total lightning strike count for a period.

        'lightning_strike_count' is calculated as the change in field
        'lighningcount' between successive periods. 'lightning_strike_count' is
        only calculated if 'lightningcount' exists.
        """

        # is the ligthningcount field present
        if 'lightningcount' in parsed_data:
            # yes, so get the new total
            new_total = parsed_data['lightningcount']
            # now calculate field lightning_strike_count as the difference
            # between the new and old totals
            parsed_data['lightning_strike_count'] = self.delta_lightning(new_total,
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
        """

        # do we have a last count
        if last_count is None:
            # no, log it and return None
            loginf("skipping lightning count of %s: no last count" % count)
            return None
        # do we have a non-None current count
        if count is None:
            # no, log it and return None
            loginf("skipping lightning count: no current count")
            return None
        # is the last count greater than the current count
        if count < last_count:
            # it is, assume a counter wrap around/reset, log it and return the
            # latest count
            loginf("lightning counter wraparound detected: new=%s last=%s" % (count, last_count))
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

        # Check the queue to get the latest GW1000 sensor data. Wrap in a try
        # to catch any instances where the queue is empty but also be prepared
        # to pop off any old records to get the most recent.
        try:
            # get any data from the collector queue, but don't dwell very long
            entry = self.collector.queue.get(True, 0.5)
        except six.moves.queue.Empty:
            # there was nothing in the queue so continue
            pass
        else:
            # did we get data or our signal to shutdown
            if entry is not None:
                # we received data
                # if not already determined determine which cumulative rain
                # field will be used to determine the per period rain field
                if not self.rain_mapping_confirmed:
                    self.get_cumulative_rain_field(entry)
                # get the rainfall this period from total
                self.calculate_rain(entry)
                # get the lightning strike count this period from total
                self.calculate_lightning_count(entry)
                # map the raw data to WeeWX fields
                mapped_data = self.map_data(entry)
                # and finally augment the loop packet with the mapped data
                self.augment_packet(event.packet, mapped_data)
                # log the augmented packet but only if debug>=2
                if weewx.debug >= 2:
                    logdbg('Augmented packet: %s' % event.packet)
            else:
                # we received the signal that the Gw1000Collector needs to
                # shutdown
                self.shutDown()

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
            # get a converter
            converter = weewx.units.StdUnitConverters[packet['usUnits']]
            # convert the mapped data to the same unit system as the packet to
            # be augmented
            converted_data = converter.convertDict(data)
            # now we can freely augment the packet with any of our mapped obs
            for field, data in six.iteritems(converted_data):
                if field not in packet:
                    packet[field] = data

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

    accumulator_config = {
        'daymaxwind': {
            'extractor': 'last'
        },
        'lightning_distance': {
            'extractor': 'last'
        },
        'lightning_strike_count': {
            'extractor': 'sum'
        },
        'lightning_last_det_time': {
            'extractor': 'last'
        },
        'stormRain': {
            'extractor': 'last'
        },
        'hourRain': {
            'extractor': 'last'
        },
        'dayRain': {
            'extractor': 'last'
        },
        'weekRain': {
            'extractor': 'last'
        },
        'monthRain': {
            'extractor': 'last'
        },
        'yearRain': {
            'extractor': 'last'
        },
        'totalRain': {
            'extractor': 'last'
        },
        '24havpm251': {
            'extractor': 'last'
        },
        '24havpm252': {
            'extractor': 'last'
        },
        '24havpm253': {
            'extractor': 'last'
        },
        '24havpm254': {
            'extractor': 'last'
        },
        'wh40_batt': {
            'extractor': 'last'
        },
        'wh26_batt': {
            'extractor': 'last'
        },
        'wh25_batt': {
            'extractor': 'last'
        },
        'wh65_batt': {
            'extractor': 'last'
        },
        'wh31_ch1_batt': {
            'extractor': 'last'
        },
        'wh31_ch2_batt': {
            'extractor': 'last'
        },
        'wh31_ch3_batt': {
            'extractor': 'last'
        },
        'wh31_ch4_batt': {
            'extractor': 'last'
        },
        'wh31_ch5_batt': {
            'extractor': 'last'
        },
        'wh31_ch6_batt': {
            'extractor': 'last'
        },
        'wh31_ch7_batt': {
            'extractor': 'last'
        },
        'wh31_ch8_batt': {
            'extractor': 'last'
        },
        'wh41_ch1_batt': {
            'extractor': 'last'
        },
        'wh41_ch2_batt': {
            'extractor': 'last'
        },
        'wh41_ch3_batt': {
            'extractor': 'last'
        },
        'wh41_ch4_batt': {
            'extractor': 'last'
        },
        'wh51_ch1_batt': {
            'extractor': 'last'
        },
        'wh51_ch2_batt': {
            'extractor': 'last'
        },
        'wh51_ch3_batt': {
            'extractor': 'last'
        },
        'wh51_ch4_batt': {
            'extractor': 'last'
        },
        'wh51_ch5_batt': {
            'extractor': 'last'
        },
        'wh51_ch6_batt': {
            'extractor': 'last'
        },
        'wh51_ch7_batt': {
            'extractor': 'last'
        },
        'wh51_ch8_batt': {
            'extractor': 'last'
        },
        'wh51_ch9_batt': {
            'extractor': 'last'
        },
        'wh51_ch10_batt': {
            'extractor': 'last'
        },
        'wh51_ch11_batt': {
            'extractor': 'last'
        },
        'wh51_ch12_batt': {
            'extractor': 'last'
        },
        'wh51_ch13_batt': {
            'extractor': 'last'
        },
        'wh51_ch14_batt': {
            'extractor': 'last'
        },
        'wh51_ch15_batt': {
            'extractor': 'last'
        },
        'wh51_ch16_batt': {
            'extractor': 'last'
        },
        'wh55_ch1_batt': {
            'extractor': 'last'
        },
        'wh55_ch2_batt': {
            'extractor': 'last'
        },
        'wh55_ch3_batt': {
            'extractor': 'last'
        },
        'wh55_ch4_batt': {
            'extractor': 'last'
        },
        'wh57_batt': {
            'extractor': 'last'
        },
        'wh68_batt': {
            'extractor': 'last'
        },
        'ws80_batt': {
            'extractor': 'last'
        }
    }

    @property
    def default_stanza(self):
        return """
    [GW1000]
        # This section is for the GW1000 API driver.

        # The driver to use:
        driver = user.gw1000

        # How often to poll the GW1000 API:
        poll_interval = 60
    """

    def prompt_for_settings(self):

        print("Specify GW1000 IP address, for example: 192.168.1.100")
        print("Set to 'auto' to autodiscover GW1000 IP address")
        ip_address = self._prompt('IP address')
        print("Specify GW1000 network port, for example: 45000")
        port = self._prompt('port', default_port)
        print("Specify how often to poll the GW1000 API in seconds")
        poll_interval = self._prompt('Poll interval', default_poll_interval)
        return {'ip_address': ip_address,
                'port': port,
                'poll_interval': poll_interval
                }

    def modify_config(self, config_dict):

        default_loop_on_init = config_dict.get('loop_on_init', '1')
        print("""The GW1000 driver requires a network connection to the 
                 GW1000. Consequently, the absence of a network connection 
                 when WeeWX starts will cause WeeWX to exit. This situation 
                 can occur on system startup. The 'loop_on_init' setting 
                 can be used to mitigate such problems by having WeeWX 
                 retry startup indefinitely. Set to '0' to attempt startup 
                 once only or '1' to attempt startup indefinitely.""")
        config_dict['loop_on_init'] = self._prompt('loop_on_init',
                                                   default_loop_on_init)
        print("""Setting record_generation to software.""")
        config_dict['StdArchive']['record_generation'] = 'software'
        print("""Setting accumulator extractor functions.""")
        if 'Accumulator' in config_dict:
            config_dict['Accumulator'].update(Gw1000ConfEditor.accumulator_config)
        else:
            config_dict['Accumulator'] = Gw1000ConfEditor.accumulator_config


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

        # initialize my superclasses
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
                entry = self.collector.queue.get(True, 10)
            except six.moves.queue.Empty:
                # there was nothing in the queue so continue
                pass
            else:
                # did we get data or our signal to shutdown
                if entry is not None:
                    # we received data
                    # create a loop packet and initialise with dateTime and usUnits
                    packet = {'dateTime': int(time.time() + 0.5)}
                    # if not already determined, determine which cumulative rain
                    # field will be used to determine the per period rain field
                    if not self.rain_mapping_confirmed:
                        self.get_cumulative_rain_field(entry)
                    # get the rainfall this period from total
                    self.calculate_rain(entry)
                    # get the lightning strike count this period from total
                    self.calculate_lightning_count(entry)
                    # map the raw data to WeeWX loop packet fields
                    mapped_data = self.map_data(entry)
                    # add the mapped data to the empty packet
                    packet.update(mapped_data)
                    # log the packet but only if debug>=2
                    if weewx.debug >= 2:
                        logdbg('Packet: %s' % packet)
                    # yield the loop packet
                    yield packet
                else:
                    # we received the signal to shutdown, so call closePort()
                    self.closePort()
                    # and raise an exception to cause the engine to shutdown
                    raise GW1000IOError("Gw1000Collector needs to shutdown")


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

        # in this case there is no port to close, just the collector thread
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

    def __init__(self, ip_address=None, port=None,
                 broadcast_address=None, broadcast_port=None,
                 socket_timeout=None, poll_interval=60,
                 max_tries=3, retry_wait=10, use_th32=False,
                 loop_on_ioerror=True):
        """Initialise our class."""

        # initialize my base class:
        super(Gw1000Collector, self).__init__()

        # interval between polls of the API, default is 60 seconds
        self.poll_interval = poll_interval
        # how many times to poll the API before giving up, default is 3
        self.max_tries = max_tries
        # period in seconds to wait before polling again, default is 10 seconds
        self.retry_wait = retry_wait
        # are we using a th32 sensor
        self.use_th32 = use_th32
        # what do we do if we receive an IO error, do we retry forever or exit
        self.loop_on_ioerror = loop_on_ioerror
        # get a station object to do the handle the interaction with the
        # GW1000 API
        self.station = Gw1000Collector.Station(ip_address=ip_address,
                                               port=port,
                                               broadcast_address=broadcast_address,
                                               broadcast_port=broadcast_port,
                                               socket_timeout=socket_timeout,
                                               max_tries=max_tries,
                                               retry_wait=retry_wait)
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
        # get a parser object to parse any data from the station
        self.parser = Gw1000Collector.Parser(is_wh24)
        self._thread = None
        self._collect_data = False

    def collect_sensor_data(self):
        """Collect sensor data by polling the API.

        Loop forever waking periodically to see if it is time to quit.
        """

        # initialise ts of last time API was polled
        last_poll = 0
        # collect data continuously while we are told to collect data
        while self._collect_data:
            now = time.time()
            # is it time to poll?
            if now - last_poll > self.poll_interval:
                # it is time to poll
                try:
                    filtered_data = self.get_live_sensor_data()
                except GW1000IOError as e:
                    # a GW1000IOError occurred, most likely because the Station
                    # object could not contact the GW1000
                    # first up log the event
                    logerr("Did not collect sensor data: %s" % (e,))
                    # what we do next depends on loop_on_ioerror, if True then
                    # we wait for the next poll to come around, if false we put
                    # None in the queue to tell our collector to shutdown
                    if not self.loop_on_ioerror:
                        self.queue.put(None)
                    # we are retrying, so reset the last_poll timestamp so we
                    # wait until the next poll to retry
                    last_poll = now
                else:
                    # did we get any data
                    if filtered_data is not None:
                        # put the data in the queue
                        self.queue.put(filtered_data)
                    # reset the last poll ts
                    last_poll = now
                    # debug log when we will next poll the API
                    logdbg('Next update in %s seconds' % self.poll_interval)
            # sleep for a second and then see if its time to poll again
            time.sleep(1)

    def get_live_sensor_data(self):
        """Get sensor data.

        Obtain live sensor data from the GW1000 API. Parse the API response.
        The parsed battery data is then further processed to filter out battery
        state data for non-existent sensors. The filtered data is returned as a
        dict. If no data was obtained from the API the value None is returned.
        """

        # obtain the raw data via the GW1000 API
        raw_data = self.station.get_livedata()
        # get a timestamp to use in case our data does not come with one
        _timestamp = int(time.time())
        if raw_data is not None:
            # parse the raw data
            parsed_data = self.parser.parse(raw_data, _timestamp)
            # log the parsed data but only if debug>=3
            if weewx.debug >= 3:
                logdbg("Parsed data: %s" % parsed_data)
            filtered_data = self.filter_battery_data(parsed_data)
            if filtered_data is not None:
                # log the filtered parsed data but only if debug>=3
                if weewx.debug >= 3:
                    logdbg("Filtered parsed data: %s" % filtered_data)
                return filtered_data
            else:
                logdbg("Could not obtain filtered parsed data")
        else:
            # we did not get any data so log it and continue
            logerr("Failed to get sensor data")
        return None

    def filter_battery_data(self, parsed_data):
        """Filter out battery data for unused sensors.

        The battery status data returned by the GW1000 API does not allow the
        discrimination of all used/unused sensors (it does for some but not for
        others). Some further processing of the battery status data is required
        to ensure that battery status is only provided for sensors that
        actually exist.
        """

        # tuple of values for sensors that are not registered with the GW1000
        not_registered = ('fffffffe', 'ffffffff')
        # obtain details of the sensors from the GW1000 API
        sensor_list = self.sensor_id_data
        if sensor_list is not None:
            # determine which sensors are registered, these are the sensors for
            # which we desire battery state information
            registered_sensors = [s['address'] for s in sensor_list if s['id'] not in not_registered]
            # obtain a list of registered sensor names
            reg_sensor_names = [Gw1000Collector.sensor_ids[a]['name'] for a in registered_sensors]
            # obtain a copy of our parsed data as we are going to alter it
            filtered = dict(parsed_data)
            # iterate over the parsed data
            for key, data in six.iteritems(parsed_data):
                # obtain the sensor name from any any battery fields
                stripped = key[:-5] if key.endswith('_batt') else key
                # if field is a battery state field, and the field pertains to an
                # unregistered sensor, remove the field from the parsed data
                if '_batt' in key and stripped not in reg_sensor_names:
                    del filtered[key]
            # return our parsed data with battery state information fo unregistered
            # sensors removed
            return filtered
        else:
            logdbg("No sensor ID data available. Could not filter battery data.")
            return None

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
        data_dict['timezone'] = six.indexbytes(data, 6)
        return data_dict

    @property
    def mac_address(self):
        """Obtain the MAC address of the GW1000."""

        station_mac_b = self.station.get_mac_address()
        return self.bytes_to_hex(station_mac_b[4:10], separator=":")

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
        CMD_GW1000_LIVEDATA battery data precisely. Furter observations reveal
        the CMD_READ_SENSOR_ID sensor battery states match the sensor signal
        levels shown in the WS View app.

        The inference is that the CMD_READ_SENSOR_ID 'signal' and
        'battery state' bytes are in fact transposed. No other PWS software
        developers seem to have noticed this so for the time being the
        CMD_READ_SENSOR_ID 'signal' and 'battery state' bytes have been
        swapped.
        """

        # obtain the sensor id data via the API
        response = self.station.get_sensor_id()
        if response is not None:
            # determine the size of the sensor id data
            raw_data_size = six.indexbytes(response, 3)
            # extract the actual sensor id data
            data = response[4:4 + raw_data_size - 3]
            # initialise a counter
            index = 0
            # initialise a list to hold our final data
            sensor_id_list = []
            # iterate over
            while index < len(data):
                sensor_id = self.bytes_to_hex(data[index + 1: index + 5],
                                              separator='',
                                              caps=False)
                # As per method comments above swap signal and battery state bytes,
                # the GW1000 API says signal should be byte 5 and battery byte 6,
                # we will use signal as byte 6 and battery as byte 5.
                sensor_id_list.append({'address': data[index:index + 1],
                                       'id': sensor_id,
                                       'signal': six.indexbytes(data, index + 6),
                                       'battery': six.indexbytes(data, index + 5)
                                       })
                index += 7
            return sensor_id_list
        else:
            return None

    def startup(self):
        """Start a thread that collects data from the GW1000 API."""

        self._thread = Gw1000Collector.CollectorThread(self)
        self._collect_data = True
        self._thread.setDaemon(True)
        self._thread.setName('Gw1000CollectorThread')
        self._thread.start()

    def shutdown(self):
        """Shut down the thread that collects data from the GW1000 API.

        Tell the thread to stop, then wait for it to finish.
        """

        # we only need do something if a thread exists
        if self._thread:
            # tell the thread to stop collecting data
            self._collect_data = False
            # terminate the thread
            self._thread.join(10.0)
            # log the outcome
            if self._thread.isAlive():
                logerr("Unable to shut down Gw1000Collector thread")
            else:
                logdbg("Gw1000Collector thread has been terminated")
        self._thread = None

    @staticmethod
    def bytes_to_hex(iterable, separator=' ', caps=True):
        """Produce a hex string representation of a sequence of bytes."""

        # assume 'iterable' can be iterated by iterbytes and the individual
        # elements can be formatted with {:02X}
        format_str = "{:02X}" if caps else "{:02x}"
        try:
            return separator.join(format_str.format(c) for c in six.iterbytes(iterable))
        except (TypeError, ValueError):
            # ValueError - cannot format c as {:02X}
            # TypeError - 'iterable' is not iterable
            # either way we can't represent as a string of hex bytes
            return "cannot represent '%s' as hexadecimal bytes" % (iterable,)

    class CollectorThread(threading.Thread):
        """Class used to collect data via the GW1000 API in a thread."""

        def __init__(self, client):
            # initialise our parent
            threading.Thread.__init__(self)
            # keep reference to the client we are supporting
            self.client = client
            self.name = 'gw1000-client'

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
            'CMD_READ_CUSTOMIZED': b'\x2A',
            'CMD_WRITE_CUSTOMIZED': b'\x2B',
            'CMD_WRITE_UPDATE': b'\x43',
            'CMD_READ_FIRMWARE_VERSION': b'\x50',
            'CMD_READ_USR_PATH': b'\x51',
            'CMD_WRITE_USR_PATH': b'\x52',
            'CMD_GW1000_LIVEDATA': b'\x27',
            'CMD_GET_SOILHUMIAD': b'\x28',
            'CMD_SET_SOILHUMIAD': b'\x29',
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
            'CMD_WRITE_SENSOR_ID_NEW': b'\x3C',
            'CMD_WRITE_REBOOT': b'\x40',
            'CMD_WRITE_RESET': b'\x41'
        }
        # header used in each API command and response packet
        header = b'\xff\xff'

        def __init__(self, ip_address=None, port=None,
                     broadcast_address=None, broadcast_port=None,
                     socket_timeout=None, max_tries=3, retry_wait=5):

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
                            _msg = "Failed to detect GW1000 ip address and/or port after %d attempts" % (attempt + 1,)
                            logerr(_msg)
                            raise GW1000IOError(_msg)
            # set our ip_address property but encode it first, it saves doing
            # it repeatedly later
            self.ip_address = ip_address.encode()
            self.port = port
            self.max_tries = max_tries
            self.retry_wait = retry_wait

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
                logdbg("Sending broadcast packet '%s' to '%s:%d'" % (Gw1000Collector.bytes_to_hex(packet),
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
                            logdbg("Received broadcast response '%s'" % (Gw1000Collector.bytes_to_hex(response),))
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

            Sends the command to the API with retries to obtain live data from
            the GW1000. If the GW1000 cannot be contacted rediscovery is
            attempted and None is returned.
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
                self.rediscover()
                raise

        def get_raindata(self):
            """Get GW1000 rain data.

            Sends the command to the API with retries to obtain rain data from
            the GW1000. If the GW1000 cannot be contacted a GW1000IOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_raindata(). Any code calling get_raindata() should
            be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_RAINDATA')

        def get_system_params(self):
            """Read GW1000 system parameters.

            Sends the command to the API with retries to obtain system
            parameters from the GW1000. If the GW1000 cannot be contacted a
            GW1000IOError will have been raised by send_cmd_with_retries()
            which will be passed through by get_system_params(). Any code
            calling get_system_params() should be prepared to handle this
            exception.
            """

            return self.send_cmd_with_retries('CMD_READ_SSSS')

        def get_mac_address(self):
            """Get GW1000 MAC address.

            Sends the command to the API with retries to obtain the GW1000 MAC
            address. If the GW1000 cannot be contacted a GW1000IOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_mac_address(). Any code calling get_mac_address()
            should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_STATION_MAC')

        def get_firmware_version(self):
            """Get GW1000 firmware version.

            Sends the command to the API with retries to obtain GW1000 firmware
            version. If the GW1000 cannot be contacted a GW1000IOError will
            have been raised by send_cmd_with_retries() which will be passed
            through by get_firmware_version(). Any code calling
            get_firmware_version() should be prepared to handle this exception.
            """

            return self.send_cmd_with_retries('CMD_READ_FIRMWARE_VERSION')

        def get_sensor_id(self):
            """Get GW1000 sensor ID data.

            Sends the command to the API with retries to obtain sensor ID data
            from the GW1000. If the GW1000 cannot be contacted rediscovery is
            attempted and None is returned.
            """

            # send the API command to obtain sensor ID data from the GW1000, be
            # prepared to catch the exception raised if the GW1000 cannot be
            # contacted
            try:
                return self.send_cmd_with_retries('CMD_READ_SENSOR_ID')
            except GW1000IOError:
                # there was a problem contacting the GW1000, it could be it
                # has changed IP address so attempt to rediscover
                self.rediscover()
                raise
            # rediscover has finished, but we have no data so return None
            return None

        def send_cmd_with_retries(self, cmd, payload=b''):
            """Send a command to the GW1000 API with retries and return the
            response.

            Send a command to the GW1000 and obtain the response. If the
            the response is valid return the response. If the response is
            invalid an appropriate exception is raised and the command resent
            up to self.max_tries times after which the value None is returned.

            A GW1000 API command looks like:

            fixed header, command, size, data1, data2...datan, checksum

            where:
            fixed header is 2 bytes = 0xFFFF
            command is a 1 byte API command code
            size is 1 byte being the number of bytes of command to checksum
            data1, data2...datan is the data being transmitted and is n bytes long
            checksum is a byte checksum of command + size + data1 + data2 ... + datan

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
                # wrap in  try..except so we can catch any errors
                try:
                    response = self.send_cmd(packet)
                except socket.timeout as e:
                    # a socket timeout occurred, log it then wait retry_wait
                    # seconds and continue
                    logdbg("Failed attempt %d to send command '%s': %s" % (attempt + 1, cmd, e))
                    time.sleep(self.retry_wait)
                except Exception as e:
                    # an exception was encountered, log it
                    logdbg("Failed attempt %d to send command '%s': %s" % (attempt + 1, cmd, e))
                else:
                    # if we made it here we have a response, check that it is
                    # valid
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
            # if we made it here we failed after self.max_tries attempts
            # first of all log it
            _msg = ("Failed to send command '%s' after %d attempts" % (cmd, attempt + 1))
            logerr(_msg)
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
                    logdbg("Sending packet '%s' to '%s:%d'" % (Gw1000Collector.bytes_to_hex(packet),
                                                               self.ip_address.decode(),
                                                               self.port))
                socket_obj.sendall(packet)
                response = socket_obj.recv(1024)
                if weewx.debug >= 3:
                    logdbg("Received response '%s'" % (Gw1000Collector.bytes_to_hex(response),))
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
            """Attempt to rediscover a lost GW1000."""

            # we will only rediscover if we first discovered
            if self.ip_discovered:
                loginf("Attempting to re-discover GW1000...")
                for attempt in range(self.max_tries):
                    try:
                        # discover() returns a list of (ip address, port) tuples
                        ip_port_list = self.discover()
                    except socket.error as e:
                        _msg = "Unable to detect GW1000: %s (%s)" % (e, type(e))
                        logerr(_msg)
                        # signal that we have a critical error
                        raise GW1000IOError(_msg)
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
                        self.ip_address = disc_ip
                        self.port = disc_port
                        break
                    else:
                        # did not discover any GW1000 so log it
                        logdbg("Failed attempt %d to detect GW1000" % (attempt + 1,))
                        # do we try again or raise an exception
                        if attempt < self.max_tries - 1:
                            # we still have at least one more try left so sleep
                            # and try again
                            time.sleep(self.retry_wait)
                        else:
                            # we've used all our tries, log it and raise an exception
                            _msg = "Failed to detect GW1000 after %d attempts" % (attempt + 1,)
                            logerr(_msg)
                            raise GW1000IOError(_msg)

            else:
                # ip address specified so we cannot go searching, fail hard
#                raise GW1000IOError("IP address specified in weewx.conf, unable to re-discover GW1000")
                logerr("IP address specified in weewx.conf, unable to re-discover GW1000")


    class Parser(object):
        """Class to parse GW1000 sensor data."""

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
            b'\x2A': ('decode_aq', 2, 'pm251'),
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
            b'\x4D': ('decode_aq', 2, '24havpm251'),
            b'\x4E': ('decode_aq', 2, '24havpm252'),
            b'\x4F': ('decode_aq', 2, '24havpm253'),
            b'\x50': ('decode_aq', 2, '24havpm254'),
            b'\x51': ('decode_aq', 2, 'pm252'),
            b'\x52': ('decode_aq', 2, 'pm253'),
            b'\x53': ('decode_aq', 2, 'pm254'),
            b'\x58': ('decode_leak', 1, 'leak1'),
            b'\x59': ('decode_leak', 1, 'leak2'),
            b'\x5A': ('decode_leak', 1, 'leak3'),
            b'\x5B': ('decode_leak', 1, 'leak4'),
            b'\x60': ('decode_distance', 1, 'lightningdist'),
            b'\x61': ('decode_utc', 4, 'lightningdettime'),
            b'\x62': ('decode_count', 4, 'lightningcount'),
            b'\x63': ('decode_temp_batt', 3, 'usertemp1'),
            b'\x64': ('decode_temp_batt', 3, 'usertemp2'),
            b'\x65': ('decode_temp_batt', 3, 'usertemp3'),
            b'\x66': ('decode_temp_batt', 3, 'usertemp4'),
            b'\x67': ('decode_temp_batt', 3, 'usertemp5'),
            b'\x68': ('decode_temp_batt', 3, 'usertemp6'),
            b'\x69': ('decode_temp_batt', 3, 'usertemp7'),
            b'\x6A': ('decode_temp_batt', 3, 'usertemp8'),
        }

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

        def __init__(self, is_wh24=False):
            # Tell our battery state decoding whether we have a WH24 or a WH65
            # (they both share the same battery state bit). By default we are
            # coded to use a WH65. Is there a WH24 connected?
            if is_wh24:
                # there is a WH24 connected so create the WH24 decode dict
                # entry, it's the same as the WH65 decode entry
                self.multi_batt['wh24'] = self.multi_batt['wh65']
                # and pop off the no longer needed WH65 decode dict entry
                self.multi_batt.pop('wh65')

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
                logdbg("sensor data is '%s'" % (Gw1000Collector.bytes_to_hex(resp),))
            if len(resp) > 0:
                index = 0
                data = {}
                while index < len(resp) - 1:
                    decode_str, field_size, field = self.response_struct[resp[index:index + 1]]
                    data.update(getattr(self, decode_str)(resp[index + 1:index + 1 + field_size],
                                                          field))
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

            if len(data) > 0:
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

            if len(data) >= 4:
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

            if len(data) >= 6:
                value = struct.unpack("BBBBBB", data)
            else:
                value = None
            if field is not None:
                return {field: value}
            else:
                return value

        def decode_temp_batt(self, data, field=None):
            """Decode combined temperature and battery status data.

            Data consists of three bytes; bytes 0 and 1 are normal temperature data
            and byte 3 is battery status data.
            """

            # do we have valid data
            if len(data) == 3:
                # yes, decode temperature from bytes 0 and 1
                temp = self.decode_temp(data[0:2], field)
                # decode battery voltage from byte 2
                batt = self.battery_voltage(data[2])
                # were we given a field to use for the return
                if field is not None:
                    # we have a field, 'temp' will be a dict so add the battery
                    # state data and return the resulting dict
                    temp['%s_batt' % field] = batt
                    return temp
                else:
                    # No field provided, so 'temp' will just be a value.
                    # Package temperature and battery state data in a generic
                    # dict and return
                    return {'temperature': temp,
                            'battery': batt
                            }
            else:
                # invalid data assumed, return None
                return None

        @staticmethod
        def decode_distance(data, field=None):
            """Decode lightning distance.

            Data is contained in a single byte integer and represents a value
            from 0 to 40km.
            """

            if len(data) >= 1:
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

            if len(data) >= 4:
                # unpack the 4 byte int
                value = struct.unpack(">L", data)[0]
                # when processing the last lightning strike time if the value
                # is 0xFFFFFFFF it means we have never seen a strike so return
                # None
                value = value if value != 0xFFFFFFFF else None
                print("utc value=%s" % (value,))
            else:
                resp = None
            if field is not None:
                return {field: value}
            else:
                return value

        @staticmethod
        def decode_count(data, field=None):
            """Decode lightning count.

            Count is an integer stored in a 4 byte big endian integer."""

            if len(data) >= 4:
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
        decode_aq = decode_press
        decode_leak = decode_humid

        def decode_batt(self, data, field):
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
                for field in self.batt_fields:
                    elements, decode_str = self.batt[field]
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
                            field_name = ''.join([field, '_ch', str(elm), '_batt'])
                        # now add the battery value to the result dict
                        b_dict[field_name] = getattr(self, decode_str)(batt_dict[field],
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
            if value == 0:
                return "OK"
            elif value == 1:
                return "low"
            else:
                return None

        @staticmethod
        def voltage_desc(value):
            if value <= 1.2:
                return "low"
            else:
                return "OK"

        @staticmethod
        def level_desc(value):
            if value <= 1:
                return "low"
            elif value == 6:
                return "DC"
            else:
                return "OK"


# ============================================================================
#                             Utility functions
# ============================================================================

def natural_sort_dict(source_dict):
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
        """Display system parameters."""

        # dict for decoding system parameters frequency byte, at present all we
        # know is 0 = 433MHz
        freq_decode = {
            0: '433MHz',
            1: '868Mhz',
            2: '915MHz'
        }
        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # get a GW1000 Gw1000Collector object
        collector = Gw1000Collector(ip_address=ip_address,
                                    port=port)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                 collector.station.port))
        # get the collector objects system_parameters property, wrap in a try so
        # we can catch any socket timeouts
        try:
            sys_params_dict = collector.system_parameters
            # create a meaningful string for frequncy representation
            freq_str = freq_decode.get(sys_params_dict['frequency'], 'Unknown')
            # if sensor_type is 0 there is a WH24 connected, if its a 1 there
            # is a WH65
            _is_wh24 = sys_params_dict['sensor_type'] == 0
            # string to use in sensor type message
            _sensor_type_str = 'WH24' if _is_wh24 else 'WH65'
        except socket.timeout:
            # socket timeout so inform the user
            print()
            print("Timeout. GW1000 did not respond.")
        else:
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
            # (unadjusted) epoch timestamp but since the timezone is stored as
            # an arbitrary number rather than an offset in seconds this is not
            # possible. We can only do what we can.
            date_time_str = time.strftime("%-d %B %Y %H:%M:%S",
                                          time.gmtime(sys_params_dict['utc']))
            print("GW1000 date-time: %s" % date_time_str)
            print("GW1000 timezone: %s" % (sys_params_dict['timezone'],))

    def rain_data(opts, stn_dict):
        """Display rain data."""

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # get a GW1000 Gw1000Collector object
        collector = Gw1000Collector(ip_address=ip_address,
                                    port=port)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                 collector.station.port))
        # get the collector objects rain_data property, wrap in a try so we can
        # catch any socket timeouts
        try:
            rain_data = collector.rain_data
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

    def station_mac(opts, stn_dict):

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # get a GW1000 Gw1000Collector object
        collector = Gw1000Collector(ip_address=ip_address,
                                    port=port)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                 collector.station.port))
        # call the driver objects mac_address() method, wrap in a try so
        # we can catch any socket timeouts
        try:
            print()
            print("GW1000 MAC address: %s" % (collector.mac_address,))
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")

    def firmware(opts, stn_dict):

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # get a Gw1000Collector object
        collector = Gw1000Collector(ip_address=ip_address,
                                    port=port)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                 collector.station.port))
        # call the driver objects firmware_version() method, wrap in a try so
        # we can catch any socket timeouts
        try:
            print()
            print("GW1000 firmware version string: %s" % (collector.firmware_version,))
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")

    def sensors(opts, stn_dict):

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # get a Gw1000Collector object
        collector = Gw1000Collector(ip_address=ip_address,
                                    port=port)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                 collector.station.port))
        # call the driver objects get_sensor_ids() method
        sensor_id_data = collector.sensor_id_data
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

        # obtain the IP address and port number to use
        ip_address = ip_from_config_opts(opts, stn_dict)
        port = port_from_config_opts(opts, stn_dict)
        # get a Gw1000Collector object
        collector = Gw1000Collector(ip_address=ip_address,
                                    port=port)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (collector.station.ip_address.decode(),
                                                 collector.station.port))
        # call the driver objects get_live_sensor_data() method, wrap in a try
        # so we can catch any socket timeouts
        try:
            live_sensor_data_dict = collector.get_live_sensor_data()
        except socket.timeout:
            print()
            print("Timeout. GW1000 did not respond.")
        else:
            print()
            print("GW1000 live sensor data: %s" % weeutil.weeutil.to_sorted_string(live_sensor_data_dict))

    def discover():

        # get an Gw1000Collector object
        collector = Gw1000Collector()
        # call the Gw1000Collector object discover() method, wrap in a try so we can
        # catch any socket timeouts
        print()
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
        print()
        print("GW1000 driver/service default field map:")
        print("(format is WeeWX field name: GW1000 field name)")
        print()
        # obtain a list of naturally sorted dict keys so that, for example,
        # xxxxx16 appears in the correct order
        keys_list = natural_sort_dict(field_map)
        # iterate over the sorted keys and print the key and item
        for key in keys_list:
            print("    %23s: %s" % (key, field_map[key]))

    def test_driver(opts, stn_dict):
        """Run the GW1000 driver."""

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
        # get a Gw1000Driver object
        driver = Gw1000Driver(**stn_dict)
        # identify the GW1000 being used
        print()
        print("Interrogating GW1000 at %s:%d" % (driver.collector.station.ip_address.decode(),
                                                 driver.collector.station.port))
        print()
        # wrap in a try..except so we can pickup a keyboard interrupt
        try:
            # continuously get loop packets and print them to screen
            for pkt in driver.genLoopPackets():
                print(": ".join([weeutil.weeutil.timestamp_to_string(pkt['dateTime']),
                                 weeutil.weeutil.to_sorted_string(pkt)]))
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
        try:
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
        except KeyboardInterrupt:
            engine.shutDown()
        loginf("GW1000 service testing complete")

    usage = """Usage: python -m user.gw1000 --help
       python -m user.gw1000 --version
       python -m user.gw1000 --test-driver
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--poll-interval=INTERVAL]
            [--max-tries=MAX_TRIES]
            [--retry-wait=RETRY_WAIT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --test-service
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--poll-interval=INTERVAL]
            [--max-tries=MAX_TRIES]
            [--retry-wait=RETRY_WAIT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --firmware-version
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --mac-address
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --sensors
            [CONFIG_FILE|--config=CONFIG_FILE]
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --live-data
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --system-params
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
       python -m user.gw1000 --rain-data
            [CONFIG_FILE|--config=CONFIG_FILE]  
            [--ip-address=IP_ADDRESS] [--port=PORT]
            [--debug=0|1|2|3]     
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
    parser.add_option('--firmware-version', dest='firmware', action='store_true',
                      help='display GW1000 firmware version')
    parser.add_option('--mac-address', dest='mac', action='store_true',
                      help='display GW1000 station MAC address')
    parser.add_option('--system-params', dest='sys_params', action='store_true',
                      help='display GW1000 system parameters')
    parser.add_option('--sensors', dest='sensors', action='store_true',
                      help='display GW1000 sensor information')
    parser.add_option('--live-data', dest='live', action='store_true',
                      help='display GW1000 sensor data')
    parser.add_option('--rain-data', dest='rain', action='store_true',
                      help='display GW1000 rain data')
    parser.add_option('--default-map', dest='map', action='store_true',
                      help='display the default field map')
    parser.add_option('--test-driver', dest='test_driver', action='store_true',
                      metavar='TEST_DRIVER', help='test the GW1000 driver')
    parser.add_option('--test-service', dest='test_service', action='store_true',
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
    (opts, args) = parser.parse_args()

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

    # display driver version number
    if opts.version:
        print("%s driver version: %s" % (DRIVER_NAME, DRIVER_VERSION))
        exit(0)

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

    if opts.rain:
        rain_data(opts, stn_dict)
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
