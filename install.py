"""
This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

                        Installer for GW1000 Driver

Version: 0.1.0                                        Date: 17 July 2020

Revision History
    17 July 2020        v0.1.0
        - initial implementation
"""

import weewx

from distutils.version import StrictVersion
from setup import ExtensionInstaller

REQUIRED_VERSION = "3.7.0"
GW1000_VERSION = "0.1.0"


def loader():
    return Gw1000Installer()


class Gw1000Installer(ExtensionInstaller):
    def __init__(self):
        if StrictVersion(weewx.__version__) < StrictVersion(REQUIRED_VERSION):
            msg = "%s requires WeeWX %s or greater, found %s" % (''.join(('GW1000 driver ', GW1000_VERSION)),
                                                                 REQUIRED_VERSION,
                                                                 weewx.__version__)
            raise weewx.UnsupportedFeature(msg)
        super(Gw1000Installer, self).__init__(
            version=GW1000_VERSION,
            name='GW1000',
            description='WeeWX driver for GW1000 WiFi gateway.',
            author="Gary Roderick",
            author_email="gjroderick<@>gmail.com",
            files=[('bin/user', ['bin/user/gw1000.py'])],
            config={
                'GW1000': {
                    'driver': 'user.gw1000'
                },
                'Accumulator': {
                    'lightning_strike_count': {
                        'extractor': 'sum'
                    },
                    'lightning_last_det_time': {
                        'extractor': 'last'
                    }
                }
            }
        )
