#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gw_api_data.py

A python program to interrogate an Ecowitt gateway device via the GW1100/GW2000
Wi-Fi Gateway API and display the raw and decoded response.
"""

# Python imports
import itertools
import socket
import struct
import time

# WeeWX imports
import user.gw1000


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
# my API command vocabulary, these are 'read only' commands, ie they read data
# only and do not change the gateway device state
commands = {
    # 'CMD_BROADCAST': b'\x12',
    # 'CMD_READ_ECOWITT': b'\x1E',
    # 'CMD_READ_WUNDERGROUND': b'\x20',
    # 'CMD_READ_WOW': b'\x22',
    # 'CMD_READ_WEATHERCLOUD': b'\x24',
    'CMD_READ_STATION_MAC': {'code': b'\x26', 'parse_fn': 'mac'},
    'CMD_GW1000_LIVEDATA': {'code': b'\x27', 'parse_fn': 'livedata'},
    # 'CMD_GET_SOILHUMIAD': b'\x28',
    # 'CMD_READ_CUSTOMIZED': b'\x2A',
    # 'CMD_GET_MulCH_OFFSET': b'\x2C',
    # 'CMD_GET_PM25_OFFSET': b'\x2E',
    'CMD_READ_SSSS': {'code': b'\x30', 'parse_fn': 'ssss'},
    # 'CMD_READ_RAINDATA': b'\x34',
    # 'CMD_READ_GAIN': b'\x36',
    # 'CMD_READ_CALIBRATION': b'\x38',
    # 'CMD_READ_SENSOR_ID': b'\x3A',
    # 'CMD_READ_SENSOR_ID_NEW': b'\x3C',
    'CMD_READ_FIRMWARE_VERSION': {'code': b'\x50', 'parse_fn': 'firmware_version'},
    # 'CMD_READ_USR_PATH': b'\x51',
    # 'CMD_GET_CO2_OFFSET': b'\x53',
    # 'CMD_READ_RSTRAIN_TIME': b'\x55',
    # 'CMD_READ_RAIN': b'\x57'
}
# header used in each API command and response packet
header = b'\xff\xff'


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


def split_str(str, out=None):

    if out is None:
        out = []
    out.append(str[:60])
    if len(str) > 60:
        split_str(str[60:], out)
    return out


def parse_mac(response):
    """Parse a CMD_READ_STATION_MAC response."""

    result = dict()
    result['all'] = split_str(response.hex(' ').upper())
    result['header'] = response[:2].hex(' ').upper()
    result['cmd_code'] = response[2:3].hex(' ').upper()
    result['size'] = response[3:4].hex(' ').upper()
    _data = response[4:-1]
    api_parser = user.gw1000.ApiParser()
    result['data'] = [f"{_data.hex(' ').upper()} ({api_parser.parse_read_station_mac(response)})",]
    result['checksum'] = response[-1:].hex(' ').upper()
    return result


def parse_firmware_version(response):
    """Parse a CMD_READ_FIRMWARE_VERSION response."""

    result = dict()
    result['all'] = split_str(response.hex(' ').upper())
    result['header'] = response[:2].hex(' ').upper()
    result['cmd_code'] = response[2:3].hex(' ').upper()
    result['size'] = response[3:4].hex(' ').upper()
    _data = response[4:-1]
    api_parser = user.gw1000.ApiParser()
    result['data'] = [f"{_data.hex(' ').upper()} ({api_parser.parse_read_firmware_version(response)})",]
    result['checksum'] = response[-1:].hex(' ').upper()
    return result


def parse_ssss(response):
    """Parse a CMD_READ_SSS response."""

    result = dict()
    result['all'] = split_str(response.hex(' ').upper())
    result['header'] = response[:2].hex(' ').upper()
    result['cmd_code'] = response[2:3].hex(' ').upper()
    result['size'] = response[3:4].hex(' ').upper()
    _data = response[4:-1]
    api_parser = user.gw1000.ApiParser()
    _parsed_ssss = api_parser.parse_read_ssss(response)
    result['data'] = []
    _decode_str = f"({_parsed_ssss['frequency']})"
    result['data'].append(f"{response[4:5].hex(' ').upper():<12} {_decode_str:<14}(Frequency)")
    _decode_str = f"({_parsed_ssss['sensor_type']})"
    result['data'].append(f"{response[5:6].hex(' ').upper():<12} {_decode_str:<14}(Sensor type)")
    _decode_str = f"({_parsed_ssss['utc']})"
    result['data'].append(f"{response[6:10].hex(' ').upper():<12} {_decode_str:<14}(UTC)")
    _decode_str = f"({_parsed_ssss['timezone_index']})"
    result['data'].append(f"{response[10:11].hex(' ').upper():<12} {_decode_str:<14}(Timezone index)")
    _decode_str = f"({_parsed_ssss['dst_status']})"
    result['data'].append(f"{response[11:12].hex(' ').upper():<12} {_decode_str:<14}(DST status)")
    result['checksum'] = response[-1:].hex(' ').upper()
    return result


def parse_livedata(response):
    """Parse a CMD_GW1000_LIVEDATA response."""

    def into_rows(data):

        api_parser = user.gw1000.ApiParser()
        # initialise a list to hold data for each field
        fields = []
        # set our position index
        index = 0
        while index < len(data) - 1:
            # obtain the field code
            field_code = data[index:index + 1]
            try:
                # obtain the decode function, field size and field name
                fn, size, field_name = api_parser.live_data_struct[field_code]
            except KeyError as e:
                # we don't know about this field, maybe it is a new field
                print(f"Possible unknown field '{field_code.hex(' ').upper()}'")
                print()
                # or maybe it's something other than a new field, in that case
                # raise the exception so we can see what happened and where
                raise
            else:
                # obtain the field data
                field_data = data[index + 1:index + 1 + size]
                # do we have any field data?
                if field_data is not None:
                    field_data_str = f"{field_data.hex(' ').upper():<14}"
                    # obtain the decoded field data if we know how
                    if hasattr(api_parser, fn):
                        decoded = "(%s)" % getattr(api_parser, fn)(field_data)
                    else:
                        decoded = '(unknown)'
                    # we have data so add it to our result list
                    fields.append('   '.join([field_code.hex(' ').upper(),
                                              field_data_str,
                                              decoded]))
                else:
                    # this shouldn't happen, but it could mean the field is
                    # marked as 'reserved' in the API documentation
                    pass
                # we are finished with this field, move onto the next field
                index += size + 1
        # return our data
        return fields

    result = dict()
    result['all'] = split_str(response.hex(' ').upper())
    result['header'] = response[:2].hex(' ').upper()
    result['cmd_code'] = response[2:3].hex(' ').upper()
    result['size'] = response[3:5].hex(' ').upper()
    result['data'] = into_rows(response[5:-1])
    result['checksum'] = response[-1:].hex(' ').upper()
    return result


def send_cmd(ip_address, port, command_packet,
             max_tries=default_max_tries,
             retry_wait=default_retry_wait,
             socket_timeout=default_socket_timeout):
    """Send a command to the device API and return the response."""

    for attempt in range(max_tries):
        response = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(socket_timeout)
            try:
                s.connect((ip_address, port))
                s.sendall(command_packet)
                response = s.recv(1024)
            except socket.error:
                raise
            finally:
                s.close()
        except socket.timeout as e:
            print("Failed to obtain response to attempt %d to "
                  "send command: %s" % (attempt + 1, e))
        except Exception as e:
            print("Failed attempt %d to send command: %s" % (attempt + 1, e))
        else:
            if response[2] == command_packet[2]:
                csum = 0
                for b in response[2:-1]:
                    csum += b
                checksum = csum % 256
                if checksum != response[-1]:
                    _msg = "Invalid checksum in API response. " \
                           "Expected '%s' (0x%s), received '%s' (0x%s)." % (checksum,
                                                                            "{:02X}".format(checksum),
                                                                            response[-1],
                                                                            "{:02X}".format(response[-1]))
                    print(_msg)
                    if attempt < max_tries - 1:
                        time.sleep(retry_wait)
                    continue
                else:
                    break
            else:
                _msg = "Invalid command code in API response. " \
                       "Expected '%s' (0x%s), received '%s' (0x%s)." % (command_packet[2],
                                                                        "{:02X}".format(command_packet[2]),
                                                                        response[2],
                                                                        "{:02X}".format(response[2]))
                print(_msg)
                if attempt < max_tries - 1:
                    time.sleep(retry_wait)
                continue
    return response


def construct_cmd_packet(command):
    """Construct a command packet.

    Accepts an API command name and returns a bytestring containing sequence of
    bytes to be sent to the gateway device.
    """

    cmd_code = commands[command].get('code')
    size = len(cmd_code) + 2
    body = b''.join([cmd_code, struct.pack('B', size)])
    checksum = calc_checksum(body)
    return b''.join([header, body, struct.pack('B', checksum)])


def print_response(command, response):
    """Format and print a response packet."""

    for title, data in itertools.zip_longest(['Response',], response['all']):
        title_str = f"{title:>15}:" if title is not None else f"{'':>15} "
        print(f"{title_str} {data}")
    print()
    print("Response components:")
    print(f"{'Header':>15}: {response['header']}")
    print(f"{'Command code':>15}: {response['cmd_code']}")
    print(f"{'Size':>15}: {response['size']}")
    for title, data in itertools.zip_longest(['Data',], response['data']):
        title_str = f"{title:>15}:" if title is not None else f"{'':>15} "
        print(f"{title_str} {data}")
    print(f"{'Checksum':>15}: {response['checksum']}")


def gather_api_data(ip_address, port, command,
                    max_tries=default_max_tries,
                    retry_wait=default_retry_wait,
                    socket_timeout=default_socket_timeout):
    """Collect and display API response data."""

    # obtain the command packet to be used
    command_packet = construct_cmd_packet(command)
    # print details of the command and command packet
    print(f"{command} ({commands[command].get('code').hex(' ').upper()}):")
    print()
    print(f"{'Sent':>15}: {command_packet.hex(' ').upper()}")
    print()
    # obtain the API response
    response = send_cmd(command_packet=command_packet,
                        ip_address=ip_address,
                        port=port,
                        max_tries=max_tries,
                        retry_wait=retry_wait,
                        socket_timeout=socket_timeout)
    # parse the API response
    parsed_resp = globals()['_'.join(['parse', commands[command].get('parse_fn')])](response)
    # print the parsed response
    print_response(command, parsed_resp)


# To run this code on pip installs use:
#
#   $ PYTHONPATH=~/weewx-data/bin python3 -m user.gw_api_data --help
#
# or for git installs use:
#
#   $ PYTHONPATH=~/weewx-data/bin:~/weewx/src python3 -m user.gw_api_data --help


def main():
    import optparse

    usage = """Usage: python3 -m user.gw_api_data --help
       python3 -m user.gw_api_data --version
       python3 -m user.gw_api_data --cmd
            --cmd=CMD_READ_STATION_MAC | CMD_GW1000_LIVEDATA |
                  CMD_READ_SSSS | CMD_READ_FIRMWARE_VERSION
            --ip-address=IP_ADDRESS
            [--port=PORT]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display version number')
    parser.add_option('--ip-address', dest='ip_address',
                      help='device IP address to use')
    parser.add_option('--port', dest='port', type=int,
                      help='device port to use')
    parser.add_option('--cmd', dest='command',
                      help='API command to use')
    (opts, args) = parser.parse_args()

    # display version number
    if opts.version:
        print("version: %s" % VERSION)
    elif opts.command is not None:
        if opts.ip_address is not None:
            port = opts.port if opts.port is not None else default_port
            gather_api_data(opts.ip_address, port, command=opts.command)
        else:
            print()
            print("You must specify a gateway device IP address using the --ip-address option.")
            print("Exiting.")
    else:
        print()
        print("You must specify an API command using the --cmd option.")
        print("Exiting.")


if __name__ == '__main__':
    main()
