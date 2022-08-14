#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
api_data.py

A python program to selectively interrogate the GW1100/GW2000 Wi-Fi Gateway API.
"""

# Python imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import socket
import struct
import time

# Python 2/3 compatibility shims
import six


VERSION = '0.1.0'

# various defaults used throughout
# default port used by GW1000/GW1100
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
# When run as a service the default age in seconds after which GW1000/GW1100
# API data is considered stale and will not be used to augment loop packets
default_max_age = 60
# default device poll interval
default_poll_interval = 20
# default period between lost contact log entries during an extended period of
# lost contact when run as a Service
default_lost_contact_log_period = 21600
# default battery state filtering
default_show_battery = False
# my API command vocabulary
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
    'CMD_WRITE_RAIN': b'\x58'
}
# header used in each API command and response packet
header = b'\xff\xff'
# known device models
known_models = ('GW1000', 'GW1100', 'GW2000', 'WH2650', 'WH2850', 'WN1900')

manifest = ['CMD_READ_SSSS', 'CMD_READ_SENSOR_ID_NEW', 'CMD_READ_RAINDATA', 'CMD_READ_RSTRAIN_TIME', 'CMD_READ_RAIN']


def hex_to_bytes(hex_string):
    """Takes a string of hex character pairs and returns a string of bytes.

    Allows us to specify a byte string in a little more human readable format.
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


def calc_checksum(data):
    """Calculate the checksum for an API call or response."""

    # initialise the checksum to 0
    checksum = 0
    # iterate over each byte in the response
    for b in six.iterbytes(data):
        # add the byte to the running total
        checksum += b
    # we are only interested in the least significant byte
    return checksum % 256


def discover():
    """Discover any gateway devices on the local network."""

    # create a socket object so we can broadcast to the network via
    # IPv4 UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set socket datagram to broadcast
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # set timeout
    s.settimeout(default_broadcast_timeout)
    # set TTL to 1 to so messages do not go past the local network
    # segment
    ttl = struct.pack('b', 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    cmd_code = commands['CMD_BROADCAST']
    size = len(cmd_code) + 2
    body = b''.join([cmd_code, struct.pack('B', size)])
    checksum = calc_checksum(body)
    cmd_packet = b''.join([header, body, struct.pack('B', checksum)])
    print("%s (%s):" % ('CMD_BROADCAST', bytes_to_hex(cmd_code)))
    print("    Sending broadcast packet '%s' to '%s:%d'" % (bytes_to_hex(cmd_packet),
                                                        default_broadcast_address,
                                                        default_broadcast_port))
    # initialise a list for the results as multiple GW1000/GW1100 may
    # respond
    result_list = []
    # send the Broadcast command
    s.sendto(cmd_packet, (default_broadcast_address, default_broadcast_port))
    # obtain any responses
    while True:
        try:
            response = s.recv(1024)
            # print the response if debug is high enough
            print("    Received broadcast response '%s'" % (bytes_to_hex(response),))
        except socket.timeout:
            # if we timeout then we are done
            break
        except socket.error:
            # raise any other socket error
            raise
        else:
            try:
                check_response(response, commands['CMD_BROADCAST'])
            except Exception as e:
                # Some other error occurred in check_response(),
                # perhaps the response was malformed. Log the stack
                # trace but continue.
                print("    Unexpected exception occurred while checking response "
                      "to command '%s': %s" % ('CMD_BROADCAST', e))
            else:
                # we have a valid response so decode the response
                # and obtain a dict of device data
                device = decode_broadcast_response(response)
                # if we haven't seen this MAC before attempt to obtain
                # and save the device model then add the device to our
                # results list
                if not any((d['mac'] == device['mac']) for d in result_list):
                    result_list.append(device)
    # close our socket
    s.close()
    # now return our results
    return result_list


def decode_broadcast_response(raw_data):
    """Decode a broadcast response and return the results as a dict."""

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


def check_response(response, cmd_code):
    """Check the validity of an API response."""

    # first check that the 3rd byte of the response is the command code
    # that was issued
    if six.indexbytes(response, 2) == six.byte2int(cmd_code):
        # now check the checksum
        c_checksum = calc_checksum(response[2:-1])
        resp_checksum = six.indexbytes(response, -1)
        if c_checksum == resp_checksum:
            # checksum check passed, response is deemed valid
            return
        else:
            # checksum check failed, raise an InvalidChecksum exception
            _msg = "    Invalid checksum in API response. " \
                   "Expected '%s' (0x%s), received '%s' (0x%s)." % (calc_checksum,
                                                                    "{:02X}".format(c_checksum),
                                                                    resp_checksum,
                                                                    "{:02X}".format(resp_checksum))
    else:
        # command code check failed, raise an InvalidApiResponse
        # exception
        exp_int = six.byte2int(cmd_code)
        resp_int = six.indexbytes(response, 2)
        _msg = "    Invalid command code in API response. " \
               "Expected '%s' (0x%s), received '%s' (0x%s)." % (exp_int,
                                                                "{:02X}".format(exp_int),
                                                                resp_int,
                                                                "{:02X}".format(resp_int))


def send_cmd(ip_address, port, command=None, cmd=None,
             max_tries=default_max_tries,
             retry_wait=default_retry_wait,
             socket_timeout=default_socket_timeout):
    """Send a command to the device API and return the response."""

    cmd_code = cmd if cmd is not None else commands[command]
    size = len(cmd_code) + 2
    body = b''.join([cmd_code, struct.pack('B', size)])
    checksum = calc_checksum(body)
    cmd_packet = b''.join([header, body, struct.pack('B', checksum)])
    print("%s (%s):" % (command, bytes_to_hex(cmd_code)))
    print("%12s: %s" % ('sending', bytes_to_hex(cmd_packet)))
    for attempt in range(max_tries):
        response = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(socket_timeout)
            try:
                s.connect((ip_address, port))
                s.sendall(cmd_packet)
                response = s.recv(1024)
            except socket.error:
                raise
            finally:
                s.close()
        except socket.timeout as e:
            print("Failed to obtain response to attempt %d to "
                  "send command '%s': %s" % (attempt + 1, cmd_code, e))
        except Exception as e:
            print("Failed attempt %d to send command '%s': %s" % (attempt + 1, cmd_code, e))
        else:
            if six.indexbytes(response, 2) == six.byte2int(cmd_code):
                csum = 0
                for b in six.iterbytes(response[2:-1]):
                    csum += b
                checksum = csum % 256
                if checksum != six.indexbytes(response, -1):
                    _msg = "Invalid checksum in API response. " \
                           "Expected '%s' (0x%s), received '%s' (0x%s)." % (checksum,
                                                                            "{:02X}".format(checksum),
                                                                            six.indexbytes(response, -1),
                                                                            "{:02X}".format(six.indexbytes(response, -1)))
                    print(_msg)
                    if attempt < max_tries - 1:
                        time.sleep(retry_wait)
                    continue
                else:
                    break
            else:
                _msg = "Invalid command code in API response. " \
                       "Expected '%s' (0x%s), received '%s' (0x%s)." % (six.byte2int(cmd_code),
                                                                        "{:02X}".format(six.byte2int(cmd_code)),
                                                                        six.indexbytes(response, 2),
                                                                        "{:02X}".format(six.indexbytes(response, 2)))
                print(_msg)
                if attempt < max_tries - 1:
                    time.sleep(retry_wait)
                continue
    print("%12s: %s" % ('received', bytes_to_hex(response)))
    return response


def gather_api_data(ip_address, port, cmd=None,
                    max_tries=default_max_tries,
                    retry_wait=default_retry_wait,
                    socket_timeout=default_socket_timeout):
    """Collect and display API response data."""

    if cmd is not None:
        cmd_code = hex_to_bytes(cmd)
        response = send_cmd(cmd=cmd_code, ip_address=ip_address, port=port,
                            max_tries=max_tries, retry_wait=retry_wait, socket_timeout=socket_timeout)
    else:
        # first discover any available gateway devices
        device_list = discover()
        for device in device_list:
            print("    Discovered device: %s" % (device,))
        # now try to identify the model of the specified device
        response = send_cmd(command='CMD_READ_FIRMWARE_VERSION', ip_address=ip_address, port=port,
                            max_tries=max_tries, retry_wait=retry_wait, socket_timeout=socket_timeout)
        model = None
        _firmware_t = struct.unpack("B" * len(response), response)
        _firmware_str = "".join([chr(x) for x in _firmware_t[5:5 + _firmware_t[4]]])
        if _firmware_str is not None:
            for m in known_models:
                if m in _firmware_str.upper():
                    model = m
                    break
        if model is not None:
            print("Device appears to be a '%s'" % model)
        else:
            print("Device model is unknown")
        # now issue all api_commands in the manifest
        for command in manifest:
            response = send_cmd(command=command, ip_address=ip_address, port=port, max_tries=max_tries,
                                retry_wait=retry_wait, socket_timeout=socket_timeout)


# To run this code on setup.py installs use:
#
#   $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --run --ip-address=IP_ADDRESS
#
# or for package installs use:
#
#   $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --run --ip-address=IP_ADDRESS
#
# Depending on your system you may need change 'python' in the above api_commands
# to 'python2' or 'python3'.

def main():
    import optparse

    usage = """Usage: python -m user.api_data --help
       python -m user.api_data --version
       python -m user.api_data --run
            --ip-address=IP_ADDRESS
            [--port=PORT]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display version number')
    parser.add_option('--run', dest='run', action='store_true',
                      help='gather data from the device API')
    parser.add_option('--ip-address', dest='ip_address',
                      help='device IP address to use')
    parser.add_option('--port', dest='port', type=int,
                      help='device port to use')
    parser.add_option('--cmd', dest='cmd',
                      help="command code to issue, must be in format xy "
                           "where x and y are hexadecimal digits")
    (opts, args) = parser.parse_args()

    # display version number
    if opts.version:
        print("version: %s" % VERSION)
    elif opts.run:
        if opts.ip_address is not None:
            port = opts.port if opts.port is not None else default_port
            if opts.cmd is not None:
                gather_api_data(opts.ip_address, port, cmd=str(opts.cmd))
            else:
                gather_api_data(opts.ip_address, port)
        else:
            print()
            print("You must use the --ip-address option to specify an IP address to use.")
            print("Exiting.")


if __name__ == '__main__':
    main()
