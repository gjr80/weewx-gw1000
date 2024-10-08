#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ec_check.py

A python program to interrogate an Ecowitt gateway device and confirm local
device API support.

To run this program:

1.  copy this file to the machine to be used

2.  run the program and display the help information:

    $ python3 /path/to/ec_check.py --help

3.  discover Ecowitt devices on the local LAN segment:

    $ python3 /path/to/ec_check.py --discover

4.  interrogate a specific Ecowitt device:

    $ python3 /path/to/ec_check.py --ip-address=1.2.3.4

    where 1.2.3.4 is the IP address of the device of interest
"""

# Python imports
import itertools
import json
import socket
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from operator import itemgetter
from urllib.error import URLError

VERSION = '0.1.0'
NAME = 'Ecowitt API Check'

# various defaults used throughout

# default port used by telnet API devices
DEFAULT_PORT = 45000
# default socket timeout
DEFAULT_SOCKET_TIMEOUT = 2
# default retry/wait time
DEFAULT_RETRY_WAIT = 5
# default max tries when polling the API
DEFAULT_MAX_TRIES = 3
DEFAULT_DISCOVERY_PERIOD = 15
DEFAULT_DISCOVERY_PORT = 59387
DEFAULT_DISCOVERY_TIMEOUT = 10
KNOWN_MODELS = ('GW1000', 'GW1100', 'GW1200', 'GW2000', 'WH2650',
                'WH2680', 'WN1900', 'WS3800', 'WS3900', 'WS3910')

class ChecksumError(Exception):
    """Exception raised when a response checksum is invalid."""

class CommandError(Exception):
    """Exception raised when an API command is invalid."""

class JSONError(Exception):
    """Exception raised when a local HTTP API response is not valid JSON."""

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

def split_str(string, width=20):
    """Split a string in sub-strings of a fixed width.

    Splits a string into one or more sub-strings each no longer than 'width'
    and returns a list containing these sub-strings. The default maximum length
    of each sub-string is 20 characters. The length of the last sub-string in
    the result is >=1 and <= width, all other sub-strings are of length
    'width'. If 'string' is None or a zero length string a list containing a
    single zero length string is returned.

    The function calls itself iteratively.

    Returns a list of strings.
    """

    # is string None
    if string is not None:
        # obtain the sub-string
        out = [string[:width]]
        # if we have not exhausted our string call myself again using the yet
        # to be processed portion of string
        if len(string) > width:
            out += split_str(string[width:], width)
    else:
        # string is None so return a list containing a zero length string
        out = ['']
    # return the result
    return out

def print_indent(title, text, max_width=70, separator=' '):
    """Pretty print text over multiples lines with a lead-in title."""

    for left, right in itertools.zip_longest([title],
                                             split_str(text, max_width - len(title) - len(separator)),
                                             fillvalue=len(title)*" "):
        print(f"{left:<}{separator}{right}")

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
    data_dict = {'mac': bytes_to_hex(data[0:6], separator=":"),
                 'ip_address': '%d.%d.%d.%d' % struct.unpack('>BBBB',
                                                             data[6:10]),
                 'port': struct.unpack('>H', data[10: 12])[0]
                 }
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

def get_model_from_firmware(ssid):
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
    if ssid is not None:
        # we have a string, now do we have a know model in the string,
        # if so return the model string
        for model in KNOWN_MODELS:
            if model in ssid.upper():
                return model
    # we don't have a known model so return None
    return ssid

def discover(namespace):
    """Discover any devices on the local network.

    To discover Ecowitt devices monitor UDP port 59387 for a set period of
    time and capture all port 59387 UDP broadcasts received. Decode each
    reply to obtain details of any devices on the local network. Create a
    dict of details for each device including a derived model name.
    Construct a list of dicts with details of each unique MAC address that
    responded. When complete return the list of devices found.
    """

    # create a socket object so we can receive IPv4 UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set timeout
    s.settimeout(namespace.discover_timeout)
    # bind our socket to the port we are using
    s.bind(("", namespace.discover_port))
    # initialise a list for the results as multiple devices may respond
    result_list = []
    # get the current time
    start_ts = time.time()
    # start receiving continuously, we will stop once our discovery period
    # has elapsed
    while True:
        # wrap in try .. except to capture any errors
        try:
            # receive a response
            response = s.recv(1024)
        except socket.timeout:
            # if we time out then we are done with this attempt
            break
        except socket.error:
            # raise any other socket error
            raise
        # Check the response is valid. As it happens the broadcast from
        # each device on port 59387 is identical to the response to a
        # device response to CMD_BROADCAST telnet API command. The validity
        # of the response can be checked by (1) confirming byte 2 is 0x12
        # and (2) verifying the packet checksum in last byte.
        # first check we have a response
        if response is not None and len(response) > 3:
            # now check that byte 2 == 0x12
            if response[2] != 0x12:
                continue
            # and finally verify the checksum
            if calc_checksum(response[2:-1]) != response[-1]:
                continue
        else:
            continue
        # if we made it here we have a valid broadcast response, so decode
        # the response and obtain a dict of device data
        found_device_dict = decode_broadcast_response(response)
        # if we haven't seen this MAC before attempt to obtain and save the
        # device model then add the device to our result list
        if not any((d['mac'] == found_device_dict['mac']) for d in result_list):
            # determine the device model based on the device SSID and add
            # the model to the device dict
            found_device_dict['model'] = get_model_from_firmware(found_device_dict.get('ssid'))
            # append the device to our list
            result_list.append(found_device_dict)
        # has our discovery period elapsed, if it has break out of the
        # loop
        if time.time() - start_ts > namespace.discover_period:
            break
    # we are done, close our socket
    s.close()
    # now return our results
    return result_list

def display_discovered_devices(namespace):
    """Display discovered devices.

    Discover and display details of Ecowitt devices on the local network.
    """

    print()
    print('Discovering Ecowitt devices...')
    print()
    # discover the devices
    device_list = discover(namespace)
    # did we discover any devices
    if len(device_list) > 0:
        # we have at least one result
        # first sort our list by IP address
        sorted_list = sorted(device_list, key=itemgetter('ip_address'))
        # iterate over the unique devices that were found
        for device in sorted_list:
            if device['ip_address'] is not None:
                if device['model'] in KNOWN_MODELS:
                    print(f"{device['model']} discovered at IP address {device['ip_address']}")
                else:
                    print(f"Unknown device model with AP SSID '{device['ssid']}' "
                          f"discovered at IP address {device['ip_address']}")
    else:
        # we have no results
        print("No devices were discovered.")

def calc_checksum(data):
    """Calculate the checksum for an API call or response."""

    # initialise the checksum to 0
    checksum = 0
    # iterate over each byte in the response
    for b in bytes(data):
        # add the byte to the running total
        checksum += b
    # we are only interested in the least significant byte
    return checksum % 256

def send_cmd(ip_address, port, command_packet,
             max_tries=DEFAULT_MAX_TRIES,
             retry_wait=DEFAULT_RETRY_WAIT,
             socket_timeout=DEFAULT_SOCKET_TIMEOUT):
    """Send a telnet API command to a device and return the response.

    Sends the API command and receives the response. Basic error checking of
    the response is performed and if the response is valid the response is
    returned. Error checking consists of:

    1. confirming the API command code is returned at byte 2 of the response
    2. the response checksum is correct

    If a valid response is not received the command it is re-sent for a maximum
    of max_tries attempts. There is a delay of retry_wait seconds between
    attempts. The socket connection timeout value is set to socket_timeout seconds.

    If a valid response is not received after max_tries attempts an exception is
    raised.
    """

    # initialise a variable to hold the response
    response = None
    # attempt to send the command and obtain a response max_tries times
    for attempt in range(max_tries):
        # wrap in a try..except in case we encounter an error
        try:
            # obtain a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # set the timeout
            s.settimeout(socket_timeout)
            # connect to the socket
            s.connect((ip_address, port))
            # send the command packet
            s.sendall(command_packet)
            # receive the response
            response = s.recv(1024)
        except Exception as e:
            # we encountered an error, print details, and try again after a
            # delay if we have any attempts left
            print(f"            failed to obtain response on attempt {attempt + 1} of {max_tries}")
            print(f"               exception: {e}")
            # sleep for the retry_wait period
            time.sleep(retry_wait)
            # continue with the next attempt
            continue
        # when we are finished close the socket
        finally:
            s.close()
        # if we made it here we have a response, now we need to check it
        # wrap in a try except in case the response is not valid
        try:
            # Do we have the correct command code in the response
            if response[2] == command_packet[2]:
                # we have a valid command code, now calculate the expected checksum
                csum = 0
                for b in response[2:-1]:
                    csum += b
                checksum = csum % 256
                # is the response checksum correct
                if checksum != response[-1]:
                    # the checksum is invalid, so create a suitable message and
                    # raise a ChecksumError exception
                    _msg = f"            invalid checksum in API response, " \
                           f"expected '{checksum}' (0x{checksum:02X}), " \
                           f"received '{response[-1]}' (0x{response[-1]:02X})"
                    raise ChecksumError(_msg)
            else:
                # the command code is invalid, so create a suitable message and
                # raise a CommandError exception
                _msg = f"            invalid command code in API response, " \
                       f"expected '{command_packet[2]}' (0x{command_packet[2]:02X}), " \
                       f"received '{response[2]}' (0x{response[2]:02X})."
                raise CommandError(_msg)
        except (ChecksumError, CommandError) as e:
            # the response was not valid, print details, and try again after a
            # delay if we have any attempts left
            if attempt < max_tries - 1:
                # print the error message
                print(e)
                # sleep for the retry_wait period
                time.sleep(retry_wait)
                # continue with the next attempt
                continue
            else:
                # we have used our attempts, give up and raise the exception
                raise
    # we have a valid response, return it
    return response

def send_req(ip_address, command,
             max_tries=DEFAULT_MAX_TRIES,
             retry_wait=DEFAULT_RETRY_WAIT,
             show = False):

    # initialise a variable to hold the response
    response = None
    # construct the scheme and host portions of the URL
    stem = ''.join(['http://', ip_address])
    # now add the 'path'
    full_url = '/'.join([stem, command])
    # create a Request object
    req = urllib.request.Request(url=full_url)
    # attempt to send the request and obtain a response max_tries times
    for attempt in range(max_tries):
        # wrap in a try..except in case we encounter an error
        try:
            # submit the request and obtain the raw response
            with urllib.request.urlopen(req) as w:
                # get charset used so we can decode the stream correctly
                char_set = w.headers.get_content_charset()
                # Now get the response and decode it using the headers
                # character set. Be prepared for charset==None.
                if char_set is not None:
                    resp = w.read().decode(char_set)
                else:
                    resp = w.read().decode()
        except Exception as e:
            if attempt < max_tries - 1:
                # we encountered an error
                if show:
                    # print details, and try again after a delay if we have any
                    # attempts left
                    print(f"            failed to obtain response on attempt {attempt + 1} of {max_tries}")
                    print(f"               exception: {e}")
                # sleep for the retry_wait period
                time.sleep(retry_wait)
                # continue with the next attempt
                continue
            else:
                # we have exhausted our attempts and whilst we have a response
                # it is not valid JSON, raise a JSONError
                raise URLError(e) from e
        # If we made it here we have a charset decoded response, now we need to
        # check its validity. First check we can deserialise the response to a
        # python object. Wrap in a try except in case we cannot.
        try:
            # obtain the response a JSON object
            response = json.loads(resp)
        except json.JSONDecodeError as e:
            # cannot deserialize the response, so print a suitable message and
            # try again after a delay if we have any attempts left
            # The response was not valid, print details, and try again after a
            # delay if we have any attempts left. If we have used all of our
            # attempts re-raise the JSONDecodeError.
            if attempt < max_tries - 1:
                if show:
                    # print a suitable message
                    print("            API response is not valid JSON")
                # sleep for the retry_wait period
                time.sleep(retry_wait)
                # continue with the next attempt
                continue
            else:
                # we have exhausted our attempts and whilst we have a response
                # it is not valid JSON, raise a JSONError
                raise JSONError(f"            API response is not valid JSON: {e}")
        # we have valid JSON, return it
        return response

def check_http_api(namespace):
    """Check if the device supports the local HTTP API

    Attempts to obtain the device MAC address and live data from the device via
    the get_network_info and get_livedata_info local HTTP API commands.
    Displays progress/summary info to console as commands are
    executed/responses processed.

    If both commands provide responses that pass basic validity checks
    (response is valid JSON and JSON response contains a representative field)
    the device is considered to support the local HTTP API. If only one command
    results in a valid response the user is warned the device may or may not
    support the local HTTP API. Devices that provide invalid responses to both
    commands are considered to not support the local HTTP API.
    """

    # initialise flags for API command failures
    mac_fail = data_fail = False
    # advise the user what we are doing
    print(f"{bcolors.BOLD}{'checking local HTTP API...':>29}{bcolors.ENDC}")
    print("      attempting to read device network information...")
    try:
        response = send_req(namespace.ip_address,
                            command='get_network_info',
                            show=namespace.show)
    except (URLError, JSONError) as e:
        # the response was invalid, tell the user
        print(f"      exception: {e}")
        print("      unable to obtain device MAC address via the local HTTP API")
        # set a flag indicating the MAC address could not be obtained
        mac_fail = True
    else:
        # valid JSON was received, now get the MAC address from the response
        mac = response.get('mac')
        if mac is not None:
            # we have a valid response, tell the user
            if namespace.show:
                print("         response is valid JSON and contains a field 'mac'")
            print(f"         device reports MAC address '{mac.upper()}'")
        else:
            # the response was invalid, tell the user
            print("      unable to obtain device MAC address via local HTTP API")
            # set a flag indicating the MAC address could not be obtained
            mac_fail = True
    print()
    print("      attempting to read live data from device...")
    try:
        response = send_req(namespace.ip_address,
                            command='get_livedata_info',
                            show=namespace.show)
    except (URLError, JSONError) as e:
        # the response was invalid, tell the user
        print(f"{'exception':>16} {e}")
        print(f"{'unable to obtain live data from the device via the local HTTP API':>71}")
        # set a flag indicating the MAC address could not be obtained
        data_fail = True
    else:
        # valid JSON was received, now check that we have an array named
        # 'common_list' in the JSON
        common = response.get('common_list')
        if common is not None:
            # we have a valid response, tell the user
            print(f"{'response is valid JSON and appears to contains valid data':>66}")
        else:
            # the response was invalid, tell the user
            print("      unable to obtain live data via local HTTP API")
            # set a flag indicating live data could not be obtained
            data_fail = True
    # give the user feedback depending on which command(s) failed
    if not (mac_fail or data_fail):
        # all commands were successful, the device appears to support the
        # local HTTP API
        print(f"{bcolors.BOLD}"
              f"{'device appears to support the Ecowitt local HTTP API':>55}"
              f"{bcolors.ENDC}")
    elif mac_fail and data_fail:
        # all commands were unsuccessful, the device does not appear to support
        # the local HTTP API
        print(f"{bcolors.BOLD}"
              f"{'device does NOT appear to support the Ecowitt local HTTP API':>63}"
              f"{bcolors.ENDC}")
    elif mac_fail:
        # the device MAC address could not be obtained, the device may/may not
        # support the local HTTP API
        print(f"{bcolors.BOLD}"
              f"{'device MAC address could not be obtained via the Ecowitt local HTTP API':>74}"
              f"{bcolors.ENDC}")
        print(f"{bcolors.BOLD}"
              f"{'unable to confirm if device does or does not support the Ecowitt local HTTP API':>82}"
              f"{bcolors.ENDC}")
    else:
        # live data could not be obtained from the device, the device may/may
        # not support the local HTTP API
        print(f"{bcolors.BOLD}"
              f"{'live data could not be obtained from the device via the Ecowitt local HTTP API':>81}"
              f"{bcolors.ENDC}")
        print(f"{bcolors.BOLD}"
              f"{'unable to confirm if device does or does not support the Ecowitt local HTTP API':>82}"
              f"{bcolors.ENDC}")

def check_telnet_api(namespace):
    """Check if the device supports the telnet API

    Attempts to obtain the device MAC address and live data from the device via
    the CMD_READ_STATION_MAC and CMD_GW1000_LIVEDATA telnet API commands.
    Displays progress/summary info to console as commands are
    executed/responses processed.

    If both command provide responses that pass basic validity checks (correct
    command code and valid checksum) the device is considered to support the
    telnet API. If only one command results in a valid response the user is
    warned the device may or may not be telnet API compatible. Devices that
    provide invalid responses to both commands are considered to not support
    the telnet API.
    """

    # initialise flags for API command failures
    mac_fail = data_fail = False
    # advise the user what we are doing
    print(f"{bcolors.BOLD}{'checking telnet API...':>25}{bcolors.ENDC}")
    print(f"{'attempting to read device MAC address...':>46}")
    # create the command packet for CMD_READ_STATION_MAC
    command_packet = b'\xff\xff\x26\x03\x29'
    if namespace.show:
        # print details of the command packet
        print(f"{'sending':>16} '{command_packet.hex(' ').upper()}' "
              f"to {namespace.ip_address}")
    # send the command packet, wrap in a try.except so we can catch any
    # exceptions
    try:
        # send the command and obtain the API response, if the response is
        # invalid a ChecksumError or CommandError exception will be raised
        response = send_cmd(command_packet=command_packet,
                            ip_address=namespace.ip_address,
                            port=namespace.port,
                            max_tries=namespace.max_tries,
                            retry_wait=namespace.retry_wait,
                            socket_timeout=namespace.timeout)
    except (ChecksumError, CommandError) as e:
        # the response was invalid, tell the user
        print(f"      exception: {e}")
        print(f"{'unable to obtain device MAC address via telnet API':>56}")
        # set a flag indicating the MAC address could not be obtained
        mac_fail = True
    else:
        # a valid response was received
        if namespace.show:
            # print the response and tell the user
            print_indent("         response received",
                         f"{response.hex(' ').upper()}",
                         max_width=72)
            print(f"{'response has a valid checksum and a valid command code':>63}")
        print(f"         device reports MAC address '{response[4:-1].hex(':').upper()}'")
    # tell the user we will now attempt to read live data from the device
    print()
    print("      attempting to read live data from device...")
    # create the command packet for CMD_GW1000_LIVEDATA
    command_packet = b'\xff\xff\x27\x03\x2A'
    if namespace.show:
        # print details of the command packet
        print(f"         sending '{command_packet.hex(' ').upper()}' "
              f"to {namespace.ip_address}")
    try:
        # send the command and obtain the API response, if the response is
        # invalid a ChecksumError or CommandError exception will be raised
        response = send_cmd(command_packet=command_packet,
                            ip_address=namespace.ip_address,
                            port=namespace.port,
                            max_tries=namespace.max_tries,
                            retry_wait=namespace.retry_wait,
                            socket_timeout=namespace.timeout)
    except (ChecksumError, CommandError) as e:
        # the response was invalid, tell the user
        print(f"      exception: {e}")
        print(f"{'unable to obtain live data from the device via telnet API':>63}")
        # set a flag indicating that live data could not be obtained
        data_fail = True
    else:
        # a valid response was received
        if namespace.show:
            # print the response and tell the user
            print_indent(f"{'response received':>26}",
                         f"{response.hex(' ').upper()}",
                         max_width=72)
            print(f"{'response has a valid checksum and a valid command code':>63}")
        print(f"{'device appears to provide valid live data':>50}")
    # give the user feedback depending on which command(s) failed
    if not (mac_fail or data_fail):
        # all commands were successful, the device appears to support the
        # telnet API
        print(f"{bcolors.BOLD}{'device appears to support the Ecowitt telnet API':>51}{bcolors.ENDC}")
    elif mac_fail and data_fail:
        # all commands were unsuccessful, the device does not appear to support
        # the telnet API
        print(f"{bcolors.BOLD}{'device does NOT appear to support the Ecowitt telnet API':>59}{bcolors.ENDC}")
    elif mac_fail:
        # the device MAC address could not be obtained, the device may/may not
        # support the telnet API
        print(f"{bcolors.BOLD}{'device MAC address could not be obtained via the Ecowitt telnet API':>70}{bcolors.ENDC}")
        print(f"{bcolors.BOLD}{'unable to confirm if device does or does not support the Ecowitt telnet API':>78}{bcolors.ENDC}")
    else:
        # live data could not be obtained from the device, the device may/may
        # not support the telnet API
        print(f"{bcolors.BOLD}{'live data could not be obtained from the device via the Ecowitt telnet API':>77}{bcolors.ENDC}")
        print(f"{bcolors.BOLD}{'unable to confirm if device does or does not support the Ecowitt telnet API':>78}{bcolors.ENDC}")
    print()

# To run this code:
#
#   $ python3 /path/to/ec_check.py --help

def main():
    import argparse

    usage = f"""{bcolors.BOLD}%(prog)s --help
                --version
                --ip-address=IP_ADDRESS 
                     [--port=PORT]
                     [--max-tries=MAX_TRIES] [--retry-wait=RETRY_WAIT]
                     [--show]
                --discover
                     [--port=PORT]
                     [--period=PERIOD] [--timeout=TIMEOUT]{bcolors.ENDC}
    """
    description = """Interrogate an Ecowitt device and display details of supported local APIs."""
    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version',
                        dest='version',
                        action='store_true',
                        help='display version number')
    parser.add_argument('--discover',
                        dest='discover',
                        action='store_true',
                        help='discover and display Ecowitt devices on the local network segment')
    parser.add_argument('--ip-address',
                        dest='ip_address',
                        metavar='IP_ADDRESS',
                        help='device IP address to use')
    parser.add_argument('--max-tries',
                        dest='max_tries',
                        type=int,
                        default=DEFAULT_MAX_TRIES,
                        metavar='MAX_TRIES',
                        help='max number of attempts to contact the device')
    parser.add_argument('--retry-wait',
                        dest='retry_wait',
                        type=int,
                        default=DEFAULT_RETRY_WAIT,
                        metavar='RETRY_WAIT',
                        help='how long to wait between attempts to contact the device')
    parser.add_argument('--timeout',
                        dest='timeout',
                        type=int,
                        metavar='TIMEOUT',
                        help='how long to wait before a connection times out')
    parser.add_argument('--port',
                        dest='port',
                        type=int,
                        metavar='PORT',
                        help='port to use for discovery or for telnet API commands')
    parser.add_argument('--period',
                        dest='period',
                        type=int,
                        default=DEFAULT_DISCOVERY_PERIOD,
                        metavar='PERIOD',
                        help='how long in seconds to listen when discovering devices')
    parser.add_argument('--show',
                        dest='show',
                        action='store_true',
                        help='show data sent to and response from the device')
    namespace = parser.parse_args()

    if len(sys.argv) == 1:
        # we have no arguments, display the help text and exit
        parser.print_help()
        sys.exit(0)

    # if we have been asked for the version number we can display that now
    if namespace.version:
        print(f"{NAME} utility version {VERSION}")
        sys.exit(0)
    if namespace.discover:
        if namespace.port is None:
            namespace.port = DEFAULT_DISCOVERY_PORT
        if namespace.timeout is None:
            namespace.timeout = DEFAULT_DISCOVERY_TIMEOUT
        display_discovered_devices(namespace)
    if namespace.ip_address is not None:
        if namespace.port is None:
            namespace.port = DEFAULT_PORT
        if namespace.timeout is None:
            namespace.timeout = DEFAULT_SOCKET_TIMEOUT
        print(f"Interrogating Ecowitt device at "
              f"{bcolors.BOLD}{namespace.ip_address}{bcolors.ENDC}...")
        check_telnet_api(namespace)
        check_http_api(namespace)
        print(f"Finished interrogating device")
        sys.exit(0)

if __name__ == '__main__':
    main()