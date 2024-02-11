Ecowitt Gateway (formerly GW1000) Driver

Note: The instructions and links in this readme have been produced for
      WeeWX v5. In general, the same concepts apply to earlier WeeWX versions;
      however, the detailed steps and commands required will be different. If
      you wish to persist with an earlier WeeWX version you may wish to refer
      to the legacy installation instructions
      (https://github.com/gjr80/weewx-gw1000/wiki/Legacy-installation-instructions).
      Alternatively, you may find it easier to just upgrade to WeeWX v5 -
      after all it is free.

Note: General support issues for the Ecowitt Gateway driver should be raised in
      the Google Groups weewx-user forum
      (https://groups.google.com/g/weewx-user). The Ecowitt Gateway driver
      Issues Page (https://github.com/gjr80/weewx-gw1000/issues) should only be
      used for specific bugs in the Ecowitt Gateway driver code. It is
      recommended that even if an Ecowitt Gateway driver bug is suspected users
      first post to the Google Groups weewx-user forum.


Description

The Ecowitt Gateway driver (formerly the GW1000 driver) is a WeeWX driver that
supports devices compatible with the Ecowitt LAN/Wi-Fi Gateway API.

The Ecowitt Gateway driver utilises the Ecowitt LAN/Wi-Fi Gateway API thus
using a pull methodology for obtaining data from the gateway device rather than
the push methodology used by other drivers. This has the advantage of giving
the user more control over when the data is obtained from the gateway device.

The Ecowitt Gateway driver can be operated as a traditional WeeWX driver where
it is the source of loop data, or it can be operated as a WeeWX service where
it is used to augment loop data produced by another driver.


Pre-Requisites

The Ecowitt Gateway driver requires WeeWX v3.7.0 or greater and will operate
under Python2 or Python 3.


Installation Instructions


Installation as a WeeWX driver

Note: The following instructions are for installation under WeeWX v5.0.0 or
      later. For installation under earlier WeeWX versions refer to the legacy
      WeeWX installation instructions
      (https://github.com/gjr80/weewx-gw1000/wiki/Legacy-installation-instructions).

1.  If the Ecowitt Gateway driver is to be installed on a fresh WeeWX
installation, first install WeeWX (http://weewx.com/docs/5.0/usersguide/installing/)
and configure WeeWX to use the simulator driver.

2.  Install the latest version of the Ecowitt Gateway driver using the weectl
utility (http://weewx.com/docs/5.0/utilities/weectl-extension/#install-an-extension).

    Note: The exact command syntax to invoke weectl on your system will depend
          on the installer used to install WeeWX. Refer to Installation methods
          (http://weewx.com/docs/5.0/usersguide/installing/#installation-methods)
          in the WeeWX User's Guide
          (http://weewx.com/docs/5.0/usersguide/introduction/).

    For WeeWX package installs:

        weectl extension install https://github.com/gjr80/weewx-gw1000/releases/latest/download/gw1000.zip

    For WeeWX *pip* installs the Python virtual environment must be activated
    before the extension is installed:

        source ~/weewx-venv/bin/activate
        weectl extension install https://github.com/gjr80/weewx-gw1000/releases/latest/download/gw1000.zip

    For WeeWX installs from *git* the Python virtual environment must be
    activated before the extension is installed:

        source ~/weewx-venv/bin/activate
        python3 ~/weewx/src/weectl.py extension install \
            https://github.com/gjr80/weewx-gw1000/releases/latest/download/gw1000.zip

3.  Test the Ecowitt Gateway driver by running the driver file directly using
the --test-driver command line option.

    For WeeWX package installs use:

        PYTHONPATH=/usr/share/weewx python3 /etc/weewx/bin/user/gw1000.py \
        --test-driver --ip-address=device_ip_address

    where device_ip_address is the IP address of the gateway device being used.

    For WeeWX pip installs the Python virtual environment must be activated
    before the driver is invoked:

        source ~/weewx-venv/bin/activate
        python3 ~/weewx-data/bin/user/gw1000.py --test-driver \
            --ip-address=device_ip_address

    where device_ip_address is the IP address of the gateway device being used.

    For WeeWX installs from git the Python virtual environment must be
    activated before the driver is invoked using the path to the local WeeWX
    git clone:

        source ~/weewx-venv/bin/activate
        PYTHONPATH=~/weewx/src python3 ~/weewx-data/bin/user/gw1000.py \
            --test-driver --ip-address=device_ip_address

    where device_ip_address is the IP address of the gateway device being used.

    You should observe loop packets being emitted on a regular basis. Once
    finished press ctrl-c to exit.

    Note: You will only see loop packets and not archive records when running
          the driver directly. This is because you are seeing output not from
          WeeWX, but rather directly from the driver.

4.  Select and configure the driver.

    For WeeWX package installs use:

        weectl station reconfigure --driver=user.gw1000

    For WeeWX pip installs the Python virtual environment must be activated
    before weectl is used to select and configure the driver:

        source ~/weewx-venv/bin/activate
        weectl station reconfigure --driver=user.gw1000

    For WeeWX installs from git the Python virtual environment must be
    activated before weectl.py is used to select and configure the driver:

        source ~/weewx-venv/bin/activate
        python3 ~/weewx/src/weectl.py station reconfigure --driver=user.gw1000


5.  You may choose to run WeeWX directly
(http://weewx.com/docs/usersguide.htm#Running_directly) to observe the loop
packets and archive records being generated by WeeWX. If WeeWX is already
running stop WeeWX before running the driver directly.

6.  Once satisfied that the Ecowitt Gateway driver is operating correctly you
can restart the WeeWX daemon:

    sudo /etc/init.d/weewx restart
        
    or

    sudo service weewx restart

    or

    sudo systemctl restart weewx

7.  You may wish to refer to the Ecowitt Gateway driver wiki
(https://github.com/gjr80/weewx-gw1000/wiki) for further guidance on
customising the operation of the Ecowitt Gateway driver and integrating gateway
device data into WeeWX generated reports.


Installation as a WeeWX service

1.  Install WeeWX (refer to http://weewx.com/docs/5.0/usersguide/installing/)
and configure it to use either the simulator driver or another driver of your
choice.

2.  Install the Ecowitt Gateway driver extension using the weectl utility as
per Installation as a WeeWX driver at step 2 above.

3.  Edit weewx.conf and under the [Engine] [[Services]] stanza add an entry
user.gw1000.GatewayService to the data_services option. It should look
something like:

    [Engine]

        [[Services]]
            ....
            data_services = user.gw1000.GatewayService

4.  Test the Ecowitt Gateway service by running the driver file directly using
the --test-service command line option.

    For WeeWX package installs use:

        PYTHONPATH=/usr/share/weewx python3 /etc/weewx/bin/usergw1000.py \
        --test-service --ip-address=device_ip_address

    where device_ip_address is the IP address of the gateway device being used.

    For WeeWX pip installs the Python virtual environment must be activated
    before the driver is invoked:

        source ~/weewx-venv/bin/activate
        python3 ~/weewx-data/bin/user/gw1000.py --test-service \
            --ip-address=device_ip_address

    where device_ip_address is the IP address of the gateway device being used.

    For WeeWX installs from git the Python virtual environment must be
    activated before the driver is invoked using the path to the local WeeWX
    git clone:

        source ~/weewx-venv/bin/activate
        PYTHONPATH=~/weewx/src python3 ~/weewx-data/bin/user/gw1000.py \
            --test-service --ip-address=device_ip_address

    where device_ip_address is the IP address of the gateway device being used.

    You should observe loop packets being emitted on a regular basis.

    Note: When the Ecowitt Gateway driver is run directly with the
          --test-service command line option a series of simulated loop packets
          are emitted every 10 seconds to simulate a running WeeWX instance.
          The gateway device is polled and the gateway device data added to the
          loop packets when available. As the default gateway device poll
          interval is 20 seconds not all loop packets will be augmented with
          gateway device data.

    Note: You will only see loop packets and not archive records when running
          the service directly. This is because you are seeing the direct
          output of the simulated loop packets and the Ecowitt Gateway service
          and not WeeWX.

5.  You may choose to run WeeWX directly
(http://weewx.com/docs/5.0/usersguide/running/#running-directly) to observe
the loop packets and archive records being generated by WeeWX. Note that
depending on the frequency of the loop packets emitted by the in-use driver and
the polling interval of the Ecowitt Gateway service, not all loop packets may
include gateway device data; however, provided the gateway device polling
interval is less than the frequency of the loop packets emitted by the in-use
driver each archive record should contain gateway device data.

6.  Once satisfied that the Ecowitt Gateway service is operating correctly you
can restart the WeeWX daemon:

    sudo /etc/init.d/weewx restart

    or

    sudo service weewx restart

    or

    sudo systemctl restart weewx

7.  You may wish to refer to the Ecowitt Gateway driver wiki
(https://github.com/gjr80/weewx-gw1000/wiki) for further guidance on
customising the operation of the Ecowitt Gateway driver and integrating gateway
device data into WeeWX generated reports.


Upgrade Instructions

Note: Before upgrading the Ecowitt Gateway driver, check the Instructions for
      specific versions section
      (https://github.com/gjr80/weewx-gw1000/wiki/Upgrade-Guide#instructions-for-specific-versions)
      of the Ecowitt Gateway driver Upgrade Guide
      (https://github.com/gjr80/weewx-gw1000/wiki/Upgrade-Guide) to see if any
      specific actions are required as part of the upgrade.

To upgrade from an earlier version of the Ecowitt Gateway driver or GW1000
driver (installed as either a WeeWX driver or a WeeWX service) simply install
the Ecowitt Gateway driver version you wish to upgrade to as per the
Installation Instructions above.


Support

General support issues for the Ecowitt Gateway driver should be raised in the
Google Groups weewx-user forum (https://groups.google.com/g/weewx-user). The
Ecowitt Gateway driver Issues Page
(https://github.com/gjr80/weewx-gw1000/issues) should only be used for specific
bugs in the Ecowitt Gateway driver code. It is recommended that even if an
Ecowitt Gateway driver bug is suspected users first post to the Google Groups
weewx-user forum.


Licensing

The Ecowitt Gateway driver/GW1000 driver is licensed under the GNU Public
License v3 (https://github.com/gjr80/weewx-gw1000/blob/master/LICENSE).
