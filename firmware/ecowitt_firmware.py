#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ecowitt_firmware.py

Obtain firmware update metadata and files for Ecowitt gateway devices.

Based on scripts published on WXForum.net by user jbroome -
https://www.wxforum.net/index.php?topic=46414.msg469692#msg469692

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

Version: 0.2.0                                     Date: 29 June 2024

Revision History
    29 June 2024            v0.2.0
        - added support for WS3900/3910 consoles
        - --model is a now mandatory option
        - models other than those in the earlier version dict are now supported
          provided the --earlier-version option is populated
        - improved formatting of longer print() statement output
    29 April 2024           v0.1.0
        - initial release


Pre-requisites

The ecowitt_firmware.py utility requires:

-   Python 3.8 or later
-   an internet connection
-   a configure email relay/server on the machine running ecowitt_firmware.py
    if email notifications are to be used


Compatibility

The ecowitt_firmware.py utility has been developed and tested under both Linux
and macOS and should work in both environments. It has not been tested with any
version of Windows; however, the ecowitt_firmware.py utility uses standard
Python libraries only so should work under any Windows version supporting
Python 3.8 or later.


To use the ecowitt_firmware utility:

1.  save this file to the machine to be used to run the ecowitt_firmware.py
utility (this machine need not have access to any Ecowitt devices)

2.  display the ecowitt_firmware.py usage and help information using the
following command:

    $ python3 /path/to/ecowitt_firmware.py --help

3.  use the utility with command line options set as required


Using the ecowitt_firmware utility as a CRON job

To use the utility as a CRON job for downloading new firmware update files
simply create a CRON entry to run the utility at the desired frequency, eg:

    * */6 * * * /path/to/ecowitt_firmware.py --download-firmware --model GW2000C --destination /var/tmp --from someone@email.com --to you@email.com

would check for and download any new GW2000C firmware updates every 6 hours and
email download notifications to you@email.com from someone@email.com.
Downloaded firmware files will be saved to model/firmware version named
directories under /var/tmp.


Issues/Peculiarities

For some reason requests for firmware metadata for the WS3910C console using
'WS3910C' as the model number fail with an 'invalid model' error. However,
transposing the last two digits of the model number, ie 'WS3901C' return valid
metadata. Analysis of the communications between the WS3910C console and the
Ecowitt firmware endpoint confirm the metadata using 'WS3901C' is correct.
Accordingly, throughout this program 'WS3901' is used to refer to WS3910
consoles. It is unknown if similar behaviour is exhibited for other consoles.

"""
import argparse
import datetime
import email.message
import hashlib
import json
import pathlib
import pprint
import random
import shutil
import smtplib
import socket
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import namedtuple

# code version number
VERSION_NUMBER = 'v0.2.0'
# default model
DEFAULT_MODEL = 'GW1100C'
# dict for lookup of earlier firmware version values for different device
# models
EARLIER_VERSION_DICT = {
    'GW1100A': '2.0.0',
    'GW1100B': '2.0.0',
    'GW1100C': '2.0.0',
    'GW1100D': '2.0.2',
    'GW1200A': '1.2.0',
    'GW1200B': '1.2.0',
    'GW1200C': '1.2.0',
    'GW1200D': '1.2.0',
    'GW2000A': '3.0.0',
    'GW2000B': '3.0.0',
    'GW2000C': '3.0.0',
    'GW2000D': '3.0.0',
    'WS3900A': '1.2.6',
    'WS3900B': '1.2.6',
    'WS3900C': '1.2.6',
    'WS3900D': '1.2.6',
    'WS3901A': '1.2.6',
    'WS3901B': '1.2.6',
    'WS3901C': '1.2.6',
    'WS3901D': '1.2.6'
}
# creat a namedtuple type to hold URL components
Components = namedtuple('Components',
                        ['scheme', 'netloc', 'path', 'params', 'query', 'fragment']
                        )
# populate a namedtuple with fixed URL components
URL_COMPONENTS = Components(scheme='http',
                            netloc='ota.ecowitt.net',
                            path='/api/ota/v1/version/info',
                            params='',
                            query='',
                            fragment=''
                            )
# default download location
DEFAULT_LOCATION = '/var/tmp'
# default timeout in seconds
DEFAULT_TIMEOUT = 10
VERSION_FILE = '/var/tmp/ecowitt_firmware.txt'


# ============================================================================
#                            class EcowittFirmware
# ============================================================================

class EcowittFirmware(object):
    """Class to obtain firmware updates data for Ecowitt gateway devices.

    The EcowittFirmware class supports:
    -   downloading, parsing and display of firmware update metadata for
        Ecowitt gateway devices
    -   downloading firmware update files for Ecowitt gateway devices

    The EcowittFirmware class utilises numerous argparse based command line
    options to manage obtaining and processing firmware update metadata as well
    as downloading firmware update files for Ecowitt gateway devices. Firmware
    update metadata can be obtained, parsed and displayed to console by use of
    the --display-metadata command line option. Firmware update files may be
    downloaded by use of the --download-firmware command line option.

    The ecowitt_firmware.py utility may be used as the basis of a CRON entry to
    regularly check for and download Ecowitt gateway device firmware updates.

    This response:
    {'code': -1, 'data': [], 'msg': 'Operation too frequent', 'time': '1707819330'}
    would tend to indicate that there is throttling on metadata requests.
    Attempt to circumvent this by generating a random MAC on each run.
    """

    def __init__(self, **kwargs):
        """Initialise an EcowittFirmware object."""

        # Obtain the device model of interest, need to convert to upper case.
        # --model is a mandatory option, fail hard if not provided.
        try:
            _model = kwargs.get('model').upper()
        except AttributeError:
            print()
            print_to_console_width("Device model not specified, please specify "
                                   "a model using the '--model' option")
            exit(1)
        # We have a model, but is it one we know of (ie we have an earlier
        # version for that model) or if it is not known, has a valid earlier
        # version be specified
        # first get the --earlier_version if specified
        try:
            _e_version = kwargs.get('earlier_version').upper()
        except AttributeError:
            # no --earlier-version was specified
            _e_version = None
        # now we can finish dealing with the model
        if _model not in EARLIER_VERSION_DICT.keys() and _e_version is None:
            print()
            print_to_console_width(f"Unknown model specified - '{_model}'. Please "
                                   "specify a known model using the '--model' "
                                   "option or include a valid earlier firmware "
                                   "version using the '--earlier-version' option")
            exit(1)
        self.model = _model
        # Queries for non-GW1000 firmware metadata require a version number.
        # There is no guidance from Ecowitt on what this parameter should be,
        # or how it should be formatted but anecdotal evidence suggests it
        # needs to be in the format 'Vx.y.z' where V is the literal
        # character 'V' and x.y.z are numbers representing a previous firmware
        # release version for the device model concerned. If not specified a
        # default is obtained from a lookup dict based on model.
        _e_version = _e_version if _e_version is not None else EARLIER_VERSION_DICT.get(self.model)
        # make sure the version starts with 'V'
        if _e_version is not None and len(_e_version) > 0 and _e_version[0] != 'V':
            _e_version = ''.join(['V', _e_version])
        self.earlier_version = _e_version
        # Obtain the device MAC, need to convert to upper case. Default
        # is a random generated MAC.
        self.mac = kwargs.get('mac').upper() if kwargs.get('mac') is not None else self.random_mac
        # Obtain the destination directory for any firmware update file downloads. Default to DEFAULT_LOCATION.
        _destination = kwargs.get('destination')
        self.destination = _destination if _destination is not None else DEFAULT_LOCATION
        # obtain the timeout value in seconds to be used for any URL queries/retrievals
        try:
            self.timeout = int(kwargs.get('timeout'))
        except TypeError:
            self.timeout = DEFAULT_TIMEOUT
        # obtain from and to email addresses
        self.from_address = kwargs.get('from')
        self.to_address = kwargs.get('to')
        # Whether to silence console output or not, default is to not silence
        # console output. Useful for when using as a CRON entry.
        self.silent = kwargs.get('silent', False)
        # whether to display debug information or not, default is to not
        # display debug information
        self.debug = kwargs.get('debug', False)
        # # initialise the local version dict
        # self.version_file = pathlib.Path(VERSION_FILE)
        # self.initialise_version_dict()
        # self.version_dict = read_dict('/var/tmp/ecowitt_firmware.txt')

    # def initialise_version_dict(self):
    #     """Initialise the local firmware version file."""
    #
    #     # does the local formware version file exist
    #     if not self.version_file.exists():
    #         self.version_file.parents[0].mkdir(parents=True, exist_ok=True)
    #         self.version_file.touch(mode=0o666)
    #     else:
    #         sta = os.stat(self.version_file)

    def get_gw1000_metadata(self):
        """Obtain metadata for the current GW1000 firmware release.

        Obtaining metadata for the current GW1000 firmware release involves
        reading and parsing the file FirwaveReadme.txt at download.ecowitt.net.
        The [GW1000] stanza in FirwaveReadme.txt is structured as per the
        following example:

        [GW1000]
        VER = GW1000V1.7.7
        URL1 = http://download.ecowitt.net/down/filewave?n=GW1000_user1&v=user1_gw1000_177.bin
        URL2 = http://download.ecowitt.net/down/filewave?n=GW1000_user2&v=user2_gw1000_177.bin
        DATE =
        NOTES =	New Firmware GW1000V1.7.7;1.Support WN34D temperature sensor (Range: -55~125Celsius).;2.Supports WH46 air quality sensor.;3.Fixed some known bugs.
        NOTES20231012 = New Firmware GW1000V1.7.6:;1.Fix the bug that the yearly rainfall does not clear to zero.;2.Support multi-channel sensor data uploading to Wunderground
        NOTES20230308 = New Firmware GW1000V1.7.5:;1. Fix the bug that AP is not closed after router connection; 2. Add WN34 temperature calibration function; 3. Add outdoor temperature correction correlating to solar radiation and wind speed.;4. Weekly, monthly and yearly rainfall reset 0 at the same time as daily rainfall reset 0.
        NOTES20220422 = 1.Fixed failure to restore configuration parameters after firmware upgrade.;2.If you have upgraded directly from a version below V1.6.4 to 1.6.7, your device parameters may have been broken. This upgrade will restore factory Settings.You need to reconfigure your upload server, sorry for any trouble caused.

        Returns a dict of key, value pairs for all [GW1000] data. If the
        firmware metadata could not be obtained the value None is returned.
        """

        # the URL to be used to obtain the FirwaveReadme.txt file
        url = 'http://download.ecowitt.net/down/filewave?v=FirwaveReadme.txt'
        # obtain the FirwaveReadme.txt file, wrap in try..except so any likely
        # errors may be trapped and acted upon
        try:
            text_resource = urllib.request.urlopen(url, timeout=self.timeout)
        except urllib.error.URLError as e:
            # we encountered a protocol error, advise the user and return None
            if not self.silent:
                print(f'Error opening URL: {e}')
            return None
        except socket.timeout as e:
            # for some reason we encountered a timeout contacting the Ecowitt
            # server, advise the user and return None
            if not self.silent:
                print(f"Timeout contacting '{url}': {e}")
            return None
        else:
            # look for any encoding used; if it's specified use it, otherwise
            # try latin-1
            encoding = text_resource.headers.get_content_charset()
            if encoding is not None:
                text = text_resource.read().decode(encoding)
            else:
                text = text_resource.read().decode(encoding="latin-1")
            # close the HTTP resource
            text_resource.close()
            # obtain the GW1000 stanza
            # first initialise a list to hold our [GW1000] lines
            gw1000_lines = []
            # do we have any text to search
            if text is not None:
                # set the capture flag
                capture = False
                # iterate over lines in the text response
                for line in text.splitlines():
                    # strip any leading or trailing spaces
                    clean_line = line.strip()
                    # strip any newline, carriage return or tab characters from
                    # the line
                    for ws in '\n\t\r':
                        clean_line = clean_line.replace(ws, '')
                    # have we found the [GW1000] line
                    if clean_line.startswith('[GW1000]'):
                        # we have found hte [GW1000] line, so start capturing lines
                        capture = True
                        # append the line to our list
                        gw1000_lines.append(clean_line)
                        # move onto the next line
                        continue
                    # have we encountered the next device [] stanza
                    if clean_line.startswith('['):
                        # we have encountered the next device stanza so stop
                        # capturing lines
                        capture = False
                        # move onto the next line
                        continue
                    # if we made it here and capture is True we must have a
                    # [GW1000] line so capture it
                    if capture:
                        gw1000_lines.append(clean_line)
            # initialise a dict to hold out GW1000 settings
            gw1000 = dict()
            # do we have any lines to process
            if len(gw1000_lines) > 0:
                # iterate over the captured lines
                for line in gw1000_lines:
                    # if '=' is not in the line it cannot hold a key, value
                    # setting so skip the line
                    if '=' not in line:
                        continue
                    # split the line on the first '=' and obtain the key and value pair
                    key, value = line.split('=', 1)
                    # save the key value pair
                    gw1000[key.strip()] = value.strip()
                # The firmware version usually includes the device model immediately
                # before the Vx.y.z firmware version. We strip this detail off to give
                # just the Vx.y.z firmware version.
                if 'VER' in gw1000.keys():
                    # split on the first 'V'
                    _split_ver = gw1000['VER'].upper().split('V', 1)
                    # if the split gives two elements take the latter,
                    # prepend 'V' and save in place of the previous version
                    # string
                    if len(_split_ver) == 2:
                        gw1000['VER'] = ''.join(['V', _split_ver[1]])
                # Anecdotally the DATE value appears as an eight-digit number
                # in the format YYYYMMDD. Attempt to convert the date to a
                # datetime object and save it, otherwise leave as is and
                # continue.
                if 'DATE' in gw1000.keys():
                    try:
                        gw1000['DATE'] = datetime.datetime.strptime(gw1000['DATE'], '%Y%m%d')
                    except (TypeError, ValueError):
                        pass
            # return the dict of GW1000 metadata
            return gw1000

    def get_other_device_metadata(self):
        """Obtain metadata for a current non-GW1000 firmware release

        Obtaining metadata for the current non-GW1000 firmware release involves
        submitting a http query to an Ecowitt site and retrieving JSON data.
        The JSON data is structured as per the following example:

        {'code': 0,
         'data': {'attach1file': 'https://osswww.ecowitt.net/ota/20240425/568ad1f21d0fe5e612b0e1ae4b7adcdd.bin',
                  'attach2file': '',
                  'content': '1.Support ws85 sensor.\r\n2.Fixed some known bugs.',
                  'id': 415,
                  'name': 'V2.3.2',
                  'queryintval': 86400},
         'msg': 'Success',
         'time': '1714369479'}

        - uses the URL stem 'http://ota.ecowitt.net/api/ota/v1/version/info'
        - the querystring includes the following fields:
            - id. A MAC address, does not need to be for a real device just
                  needs to be in MAC format
            - model. Device model, includes frequency band
                     designator, eg: GW1100C, GW2000B
            - user. An integer
            - version. A firmware version previously used on this device model,
                       must start with 'V', eg: V1.6.8, V3.0.0
            - sign. A md5 hash of the URL encoded id, model, user and version
                    fields with '@ecowittnet' appended. Note '@ecowittnet' is
                    used in calculating the md5 hash, but is not included in
                    the final URL querystring.
        - response is in JSON format
        """

        # construct the query params dict, it will change later:
        # - to add the calculated md5 hash
        # - change 'version' to just 'Vx.y.z` once the md5 hash has been
        #   calculated
        query_params = {
            'id': self.mac,
            'model': self.model,
            'time': int(time.time()),
            'user': 1,
            'version': ''.join([self.earlier_version, '@ecowittnet'])
        }

        # calculate the md5 hash
        # first obtain the url encoded query parameter string that includes
        # '@ecowitt', '@' must remain untouched and cannot be encoded
        params_enc = urllib.parse.urlencode(query_params,
                                            safe='@',
                                            quote_via=urllib.parse.quote)
        # obtain the md5 hash of the encoded param string
        md5_hash = hashlib.md5(params_enc.encode()).hexdigest().upper()
        # modify our query params - reset the version and add the previously
        # calculated md5 hash
        query_params['version'] = self.earlier_version
        query_params['sign'] = md5_hash
        # obtain the url encoded query parameter string including the md5 hash and
        # revised version, '@' must remain untouched and cannot be encoded
        params_md5_enc = urllib.parse.urlencode(query_params,
                                                safe='@',
                                                quote_via=urllib.parse.quote)

        # construct the URL we will use
        # first obtain updated url components that includes the updated url
        # encoded query parameter string
        _url_components = URL_COMPONENTS._replace(query=params_md5_enc)
        # now construct the URL
        url = urllib.parse.urlunparse(_url_components)
        # hit the URL and obtain the response, it will be in JSON format
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                response_json = json.load(response)
        except urllib.error.URLError as e:
            # we encountered a protocol error, advise the user and return None
            if not self.silent:
                print(f'Error opening URL: {e}')
            return None
        except json.JSONDecodeError as e:
            # we encountered a JSON decode error, advise the user and return None
            if not self.silent:
                print(f'Error decoding URL response: {e}')
            # finally return None
            return None
        # We have a JSON object, but does it contain the necessary metadata. If
        # it does the msg field will contain 'Success'.
        if response_json['msg'].lower() == 'success':
            # we have a good response so return it
            return response_json
        else:
            # no 'Success' message, means we encountered some other issue.
            # Advise the user and display the msg field content, it might give
            # a clue to the problem.
            if not self.silent:
                print(f'An error was encountered decoding the JSON response: '
                      f' {response_json["msg"]}')
                print()
                # and display the entire raw JSON response
                print(response_json)
            # finally return None
            return None

    def parse_metadata(self, metadata):
        """Parse raw firmware metadata.

        Parse the raw metadata of an Ecowitt gateway device firmware update and
        return a dict of data as follows:
            'version':  string containing the firmware version number,
                        eg: '1.7.7' or '2.1.3'
            'urls':     list of URLs for downloading the firmware file(s),
                        ordered by file number
            'date':     date object representing the date of the firmware
                        release or None if release date could not be determined
            'notes':    list of strings containing firmware release notes
            'raw_metadata': dict containing the raw firmware metadata

        How the metadata is parsed will depend on whether the metadata is for a
        GW1000 or non-GW1000 firmware update. If the metadata is for a
        non-GW1000 firmware update, the metadata will contain a 'data' key.
        GW1000 firmware update metadata will not contain a 'data' key.

        Returns a dict of data or None is no metadata was provided.
        """

        if metadata is not None:
            parsed = dict()
            if 'data' in metadata.keys():
                # we likely have firmware for a non-GW1000 device
                # Get the firmware version, it should be in the format
                # 'Vx.y.z'. Use whatever appears after the 'V'.
                parsed['version'] = metadata['data'].get('name', 'not specified').split('V')[-1]
                # Obtain the URLs for the firmware files saving the URLs in a
                # list. There may only be one URL or there may be two.
                parsed['urls'] = list()
                if 'attach1file' in metadata['data'].keys() and len(metadata['data']['attach1file']) > 0:
                    parsed['urls'].append(metadata['data']['attach1file'])
                if 'attach2file' in metadata['data'].keys() and len(metadata['data']['attach2file']) > 0:
                    parsed['urls'].append(metadata['data']['attach2file'])
                # Obtain the firmware date, there is no dedicated date field
                # in the metadata, but we can try and extract a date from the
                # download URL.
                try:
                    _ymd = parsed['urls'][0].split('/')[-2]
                    _date = datetime.datetime.strptime(_ymd, '%Y%m%d')
                except (IndexError, AttributeError, ValueError, TypeError):
                    _date = None
                parsed['date'] = _date
                # Obtain the notes to the firmware release, the field will be a
                # string containing one or more notes with each note terminated
                # by a new line character. Save the notes as a list with each
                # element containing a single note.
                parsed['notes'] = list()
                for line in self.yield_comments(metadata['data']['content']):
                    parsed['notes'].append(line)
            else:
                # we likely have GW1000 firmware
                # Get the firmware version, it should be in the format
                # 'Vx.y.z'. Use whatever appears after the 'V'.
                parsed['version'] = metadata.get('VER', 'not specified').split('V')[-1]
                # Obtain the URLs for the firmware files saving the URLs in a
                # list. There may only be one URL or there may be two.
                parsed['urls'] = list()
                if 'URL1' in metadata.keys() and len(metadata['URL1']) > 0:
                    parsed['urls'].append(metadata['URL1'])
                if 'URL2' in metadata.keys() and len(metadata['URL2']) > 0:
                    parsed['urls'].append(metadata['URL2'])
                # Obtain the firmware date, there should be a 'DATE' field
                # containing a date in the format 'YYYYMMDD' but be prepared to
                # handle its omission or something that is not in the correct
                # format
                try:
                    _ymd = metadata['DATE']
                    _date = datetime.datetime.strptime(_ymd, '%Y%m%d')
                except (IndexError, AttributeError, ValueError, TypeError):
                    _date = None
                parsed['date'] = _date
                # Obtain the notes to the firmware release, the field will be a
                # string containing one or more notes with each note terminated
                # by a new line character. Save the notes as a list with each
                # element containing a single note.
                parsed['notes'] = list()
                for line in self.yield_comments(metadata['NOTES'], split_character=';'):
                    parsed['notes'].append(line)
            # return the parsed metadata
            return parsed
        else:
            # we have no valid metadata, return None
            return None

    def get_metadata(self):
        """Get current firmware release metadata for an Ecowitt gateway device.

        Obtains raw metadata for an Ecowitt gateway device firmware update. The
        raw metadata is parsed to create a dict of data as follows:
            'version':  string containing the firmware version number,
                        eg: '1.7.7' or '2.1.3'
            'urls':     list of URLs for downloading the firmware file(s),
                        ordered by file number
            'date':     date object representing the date of the firmware
                        release or None if release date could not be determined
            'notes':    list of strings containing firmware release notes

        The raw metadata is added to the parsed metadata dict in field
        'raw_metadata'.

        Returns a dict of data containing the augmented parsed metadata or None
        if no metadata could be obtained.
        """

        # if not silent advise what we are doing
        if not self.silent:
            print()
            print(f'Obtaining metadata for current {self.model} firmware release...')
        # obtain the raw metadata, how we do this depends on the device model
        if 'GW1000' in self.model:
            raw_metadata = self.get_gw1000_metadata()
        else:
            raw_metadata = self.get_other_device_metadata()
        # obtain the parsed metadata
        parsed_metadata = self.parse_metadata(raw_metadata)
        # add the raw metadata to the parsed metadata, it will be useful later
        if parsed_metadata is not None:
            # add the raw metadata
            parsed_metadata['raw_metadata'] = raw_metadata
        # if debug is set display the raw metadata, use pretty print to give a
        # more readable display
        if self.debug:
            print("Raw response:")
            pprint.pprint(raw_metadata, compact=True)
        # if not silent advise whether we successfully obtained the metadata
        if not self.silent:
            if parsed_metadata is None:
                print(f'Failed to obtain metadata')
            else:
                print(f'Successfully obtained metadata')
        # return the augmented parsed metadata (or None)
        return parsed_metadata

    def print_metadata(self, metadata):
        """Print metadata for an Ecowitt gateway device firmware release."""

        # advise the model we are displaying
        print(f'Current {self.model} firmware release metadata:')
        print()
        # print the firmware version
        print(f'{"Version":8}: {metadata["version"]}')
        # obtain the firmware release date in day month year format or if not
        # available the string 'not specified'
        try:
            date_str = metadata['date'].strftime('%-d %B %Y')
        except AttributeError:
            date_str = 'not specified'
        # display the firmware release date
        print(f'{"Date":8}: {date_str}')
        # display the firmware update file URLs, there may be 0, 1 or 2
        url_count = 1
        for url in metadata['urls']:
            file_str = f'File {url_count}'
            print(f'{file_str:8}: {url}')
            url_count += 1
        # display the firmware release notes, there maybe 0, 1 or more lines of
        # text
        first_line = True
        for line in metadata['notes']:
            if first_line:
                print(f'{"Comments":8}: {line}')
                first_line = False
            else:
                print(f'{"":9} {line}')

    @staticmethod
    def yield_comments(comment_data, split_character='\n'):
        """Generator to aid in formatting raw metadata comments/notes."""

        # do we have any comment data
        if len(comment_data) > 0:
            # split the comment data using the split character
            comment_lines = comment_data.split(split_character)
            # iterate over the lines and yield the line with any tab, newline
            # and carriage return characters stripped
            for comment in comment_lines:
                yield comment.strip(' \t\n\r')
        else:
            # we had no comment data so yield a single 'not specified' comment
            yield 'not specified'

    def download_file(self, url, path_file, force_overwrite=False):
        """Download a firmware file given a URL and destination file name.

        url:             the URL to be used to download the file
        path_file:       a pathlib.Path object representing the destination
                         file
        force_overwrite: whether to overwrite the destination file if it
                         already exists

        Downloads the file to a temporary location and use an atomic write to
        save the downloaded file to the final destination. If the destination
        file already exists it is not overwritten with the downloaded file
        unless force_overwrite is True.
        """

        # obtain a random file name for initial use during the download
        temp_path_file = pathlib.Path(self.destination) / '.'.join([uuid.uuid4().hex, 'tmp'])
        # are we are saving the downloaded file to the final destination, we
        # will only if the final destination file exist or is force_overwrite
        # set True
        if force_overwrite or not path_file.is_file():
            # we are saving the downloaded file to the final destination
            # first display what we are doing
            if not self.silent:
                print(f"{'':>3}Downloading '{str(path_file.name)}'...")
            # construct the final destination directory of it does not exist
            path_file.parents[0].mkdir(parents=True, exist_ok=True)
            # construct the temporary file destination directory of it does not
            # exist
            temp_path_file.parents[0].mkdir(parents=True, exist_ok=True)
            # set the default socket timeout, this is the only way we can apply
            # a timeout to urllib.request.urlretrieve
            socket.setdefaulttimeout(self.timeout)
            # download the file, wrap in a try..except so we can catch and
            # handle any likely errors
            try:
                _path, _headers = urllib.request.urlretrieve(url, filename=str(temp_path_file))
            except (urllib.error.URLError, urllib.error.ContentTooShortError) as e:
                if not self.silent:
                    print(f"{'':>3}Error downloading '{str(path_file.name)}': {e}")
            except TimeoutError as e:
                if not self.silent:
                    print(f"{'':>3}Timeout downloading '{str(path_file.name)}': {e}")
            except Exception as e:
                if not self.silent:
                    print(f"{'':>3}An unexpected error occurred downloading '{str(path_file.name)}': {e}")
            else:
                # download completed successfully, do the atomic write
                _path = temp_path_file.replace(str(path_file))
                if not self.silent:
                    print(f"{'':>3}Download saved to '{str(_path)}'")
                    print(f"{'':>3}Download complete")
                return _path
        elif not self.silent:
            print(f"{'':>3}Skipping download of '{str(path_file.name)}', file exists in '{str(path_file.parents[0])}'")
            print(f"{'':>3}Download complete")
        return None

    def download_firmware(self, metadata):
        """Download firmware for an Ecowitt gateway device.

        The firmware update for a gateway device may be provided in one or more
        (to date two) files. To date non-GW1000 firmware updates consist of two
        files and GW1000 firmware updates consist of one file only. The
        firmware update metadata for both non-GW1000 and GW1000 devices has
        provision for two files.

        Each firmware update file is downloaded and saved in a directory tree
        under a user specified directory. A directory named by model number
        (eg: 'GW1000C', 'GW2000A') is used for each model with the firmware
        files for each version for a given model being saved in a subdirectory
        named for the version number and firmware release/download date using
        the format 'version_date', eg: 'V1.7.7_20240324'.
        """

        def get_other_file_name(url):
            """Obtain the file name from a non-GW1000 firmware download URL."""

            # do we have a URL
            if url is not None and len(url) > 0:
                # we have a non-None, non-zero length URL; first parse the URL
                _parsed_url = urllib.parse.urlparse(url)
                # replace escape sequences with single character equivalents
                _unquoted_path = urllib.parse.unquote(_parsed_url.path)
                # return the name component of the parsed and converted URL
                return pathlib.Path(_unquoted_path).name
            else:
                # we did not have a URL so return None
                return None

        def get_gw1000_file_name(url):
            """Obtain the file name from a GW1000 firmware download URL."""

            # urllib.parse.unquote
            if url is not None and len(url) > 0:
                # we have a non-None, non-zero length URL; first replace
                # escape sequences with single character equivalents
                _unquoted_path = urllib.parse.unquote(url)
                # now parse the unquoted URL
                _parsed_url = urllib.parse.urlparse(url)
                # parse the query string and return the 'v' query parameter
                return urllib.parse.parse_qs(_parsed_url.query)['v'][0]
            else:
                # we did not have a URL so return None
                return None

        # initialise a list of path/files that have been downloaded
        dl_list = list()
        # advise the user what we are doing, but only if we are not 'silent'
        if not self.silent:
            print()
            print(f'Downloading {self.model} firmware...')
        # obtain a dict keyed by URL and containing the file name for the
        # required firmware update files, how we obtain the file name will
        # depend on whether we have a GW1000 or not
        if 'data' in metadata['raw_metadata'].keys():
            # we have a non-GW1000 device
            # initialise the download dict
            download_dict = dict()
            # iterate over the URL(s), obtain the respective file name and add
            # to the download dict
            for url in metadata['urls']:
                download_dict[url] = get_other_file_name(url)
        else:
            # we have a GW1000 device
            # initialise the download dict
            download_dict = dict()
            # iterate over the URL(s), obtain the respective file name and add
            # to the download dict
            for url in metadata['urls']:
                download_dict[url] = get_gw1000_file_name(url)
        # construct the versioned directory name to be used for the downloaded
        # file(s), this will be added to the destination path to obtain the
        # overall path for the downloaded file(s)
        # obtain a version string starting with 'V'
        version_string = ''.join(['V', metadata['version']])
#        # obtain a string consisting of the version number and firmware release
#        # date
#        try:
#            version_date_str = '_'.join([version_string, metadata['date'].strftime('%Y%m%d')])
#        except (AttributeError, TypeError):
#            version_date_str = '_'.join([version_string, datetime.datetime.now().strftime('%Y%m%d')])
        # construct the sub-path for the download, this consists of a directory
        # named for the model and a directory named using the version
        sub_path = '/'.join([self.model, version_string])
        # iterate over the URLs to be used for download
        for url, filename in download_dict.items():
            # if we have a file name download the file
            if filename is not None:
                # obtain the destination path and file name as a pathlib.Path
                # object
                path_file = pathlib.Path(self.destination) / sub_path / filename
                # download the file and obtain the pathlib.Path object of the
                # saved file
                _path = self.download_file(url, path_file)
                # a non-None result indicates success, save the result to the
                # download list for later reporting
                if _path is not None:
                    dl_list.append(_path)
        # finally, do our reporting
        # did we download any files, if we did download files write the
        # firmware release notes to a text file and email the results if
        # necessary
        if len(dl_list) > 0:
            # Save the firmware release notes as a text file in the same
            # directory as the downloaded firmware update files. The filename
            # comprises the string 'release_notes', the version number and
            # firmware release date, eg: 'release_notes_V3.1.2_20240312.txt'.
            # first obtain the release date as a string
            try:
                version_date_string = metadata['date'].strftime('%Y%m%d')
            except (AttributeError, TypeError):
                version_date_string = datetime.datetime.now().strftime('%Y%m%d')
            # construct the file name to be used
            _filename = '_'.join(['release_notes', version_string, version_date_string])
            notes_filename = '.'.join([_filename, 'txt'])
            # obtain as a pathlib Path object
            notes_path_file = pathlib.Path(self.destination) / sub_path / notes_filename
            # obtain the formatted release notes
            notes_string = self.gen_notes_string(metadata['notes'])
            # write the formatted release notes to file
            write_release_notes(notes_path_file, notes_string)
            # create and send an email if we have a 'to' and 'from' email
            # address
            if self.from_address is not None and self.to_address is not None:
                # advise we are preparing the email
                if not self.silent and self.debug:
                    print(f"{'':>3}Preparing email summary...")
                # construct the email message text, we do this by constructing
                # the pieces and then pulling them together at the end
                dl_summary = f"Downloaded {len(dl_list)} file{'s' if len(dl_list) > 1 else ''}:\n"
                dl_file_str = '\n'.join([f"     '{p.name}' downloaded to '{p.parents[0]}'" for p in dl_list])
                msg_text = f"Found new {self.model} firmware version {metadata['version']}. "\
                           f"{dl_summary}\n{dl_file_str}\n\n{notes_string}"
                # send the email, the send_email method takes care of
                # constructing and sending the email
                self.send_email(subject=f"New Ecowitt {self.model} firmware",
                                body=msg_text)
            # # set the version number for our model in the local firmware
            # # version dict
            # self.version_dict[self.model] = metadata['version']
            # # save the local firmware version dict to file
            # write_dict('/var/tmp/ecowitt_firmware.txt', self.version_dict)
            # we are finished, at least one file was downloaded so print a
            # suitable summary
            if not self.silent:
                print(f"Successfully downloaded {len(dl_list)} file{'s' if len(dl_list) > 1 else ''}")
        else:
            # no files were downloaded, print a suitable summary if required
            if not self.silent:
                print(f'No files were downloaded for {self.model} firmware version {metadata["version"]}')

    @staticmethod
    def gen_notes_string(notes):
        """Generate a multi-line formatted firmware notes string."""

        if len(notes) > 0:
            fw_notes_list = list()
            first_line = True
            for line in notes:
                if first_line:
                    fw_notes_list.append(f'{"Comments":8}: {line}')
                    first_line = False
                else:
                    fw_notes_list.append(f'{"":9} {line}')
            return '\n'.join(fw_notes_list)
        else:
            return ''

    def send_email(self, subject, body):
        """Send an email."""

        # create a text/plain message
        message = email.message.EmailMessage()
        message['Subject'] = subject
        message['From'] = self.from_address
        message['To'] = self.to_address
        message.add_header('Content-Type', 'text')
        message.set_content(body)
        # send the message via our own SMTP server, wrap in a try..except so
        # we can catch likely errors we may encounter and prevent them from
        # aborting the program
        try:
            with smtplib.SMTP('localhost') as s:
                s.send_message(message)
                # display a message if necessary indicating the email was sent
                if not self.silent and self.debug:
                    print(f"{'':>3}Email summary sent")
        except (smtplib.SMTPConnectError, ConnectionRefusedError) as e:
            print(f"{'':>3}Error connecting to SMTP server: {e}")
            print(f"{'':>3}Perhaps the SMTP settings are incorrect or the SMTP server does not exist")
            if not self.silent and self.debug:
                print(f"{'':>3}Email summary was not sent")

    @property
    def random_mac(self):
        """Generate a random MAC address."""

        return ':'.join(f'{random.randint(0,255):02X}' for x in range(6))


def write_release_notes(file, notes):
    """Write the firmware release notes to a file."""

    with open(file, 'w') as f:
        f.write(notes)


def write_dict(file, data):
    """Write a dict to file as a json string.

    This function is used to write a python dict to file as a JSON string.
    """

    with open(file, 'w') as f:
        f.write(json.dumps(data))


def read_dict(file):
    """Read a string from a file and decode as a JSON object.

    This function is used to read a string from a file and decode the string as
    a JSON object. When used in conjunction with write_dict the returned python
    object should be a dict.
    """

    try:
        with open(file, 'r') as f:
            _data = f.read()
            try:
                return json.loads(_data)
            except json.decoder.JSONDecodeError:
                return dict()
    except FileNotFoundError:
        return dict()


def get_console_width():
    """Get the current console width."""

    return shutil.get_terminal_size().columns


def print_to_console_width(*args, sep=' '):
    """Print text to neatly fit the current console width."""

    width = get_console_width()
    for line in sep.join(map(str, args)).splitlines(True):
        print(*textwrap.wrap(line, width), sep="\n")


class bcolors:
    """Class defining colours used for terminals."""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():

    usage = f"""{bcolors.BOLD}%(prog)s --help
                 --version 
                 --get-metadata
                    --model=MODEL 
                    [--mac=MAC] [--earlier-version=VERSION]
                    [--timeout=TIMEOUT] [--silent] [--debug]
                 --download-firmware
                    --model=MODEL 
                    [--mac=MAC] [--earlier-version=VERSION]
                    [--destination=DESTINATION] [--timeout=TIMEOUT]
                    [--to] [--from]
                    [--silent] [--debug]{bcolors.ENDC}
    """
    description = """Obtain current firmware updates for Ecowitt selected devices."""

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--version',
                        action='store_true',
                        help='display this programs version')
    parser.add_argument('--get-metadata',
                        dest='get_metadata',
                        action='store_true',
                        help='display firmware update metadata')
    parser.add_argument('--download-firmware',
                        dest='download_firmware',
                        action='store_true',
                        help='download current firmware file(s)')
    parser.add_argument('--model',
                        type=str,
                        dest='model',
                        metavar="MODEL",
                        help='obtain metadata for device model MODEL')
    parser.add_argument('--mac',
                        type=str,
                        dest='mac',
                        metavar="MAC",
                        help='use MAC as the MAC address')
    parser.add_argument('--earlier-version',
                        dest='earlier_version',
                        metavar='VERSION',
                        help='earlier firmware version VERSION')
    parser.add_argument('--destination',
                        dest='destination',
                        metavar='DESTINATION',
                        help='destination directory where firmware file(s) will be saved')
    parser.add_argument('--timeout',
                        type=int,
                        dest='timeout',
                        default=10,
                        metavar="TIMEOUT",
                        help='timeout in seconds when downloading firmware files/metadata')
    parser.add_argument('--from',
                        metavar='FROM',
                        help="email 'from' address")
    parser.add_argument('--to',
                        metavar='TO',
                        help='send emails to this address')
    parser.add_argument('--silent',
                        action='store_true',
                        help='silence all console output')
    parser.add_argument('--debug',
                        action='store_true',
                        help='display additional output')
    namespace_dict = vars(parser.parse_args())

    if len(sys.argv) == 1:
        # we have no arguments, display the help text and exit
        if not namespace_dict.get('silent', False):
            parser.print_help()
        sys.exit(0)

    # if we have been asked for the version number we can display that now
    if namespace_dict.get('version'):
        print(f"version {VERSION_NUMBER}")
        sys.exit(0)

    if namespace_dict.get('get_metadata'):
        # get an EcowittFirmware object
        meta_obj = EcowittFirmware(**namespace_dict)
        if meta_obj:
            # obtain the metadata
            response = meta_obj.get_metadata()
            # if we have a response and are not silent display the metadata
            if not namespace_dict.get('silent', False) and response is not None:
                meta_obj.print_metadata(response)
        else:
            # no metadata was returned, if we are not silent display a suitable
            # message and exit
            if not namespace_dict.get('silent', False):
                print("Unable to obtain an EcowittFirmware object.")
            sys.exit(1)

    if namespace_dict.get('download_firmware'):
        # get an EcowittFirmware object
        meta_obj = EcowittFirmware(**namespace_dict)
        if meta_obj:
            # obtain the metadata
            response = meta_obj.get_metadata()
            # if we are not silent and debug is set display the response
            if not namespace_dict.get('silent', False) and namespace_dict.get('debug'):
                print("response=%s" % (response,))
            # if we have a response download the firmware file(s)
            if response is not None:
                meta_obj.download_firmware(response)
        else:
            # no metadata was returned, if we are not silent display a suitable
            # message and exit
            if not namespace_dict.get('silent', False):
                print("Unable to obtain an EcowittFirmware object.")
            sys.exit(1)


if __name__ == '__main__':
    main()
