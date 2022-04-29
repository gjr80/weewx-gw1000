# Ecowitt Gateway (formerly GW1000) Driver #

**Note:** General support issues for the Ecowitt Gateway driver should be raised in the Google Groups [weewx-user forum](https://groups.google.com/g/weewx-user "Google Groups weewx-user forum"). The Ecowitt Gateway driver [Issues Page](https://github.com/gjr80/weewx-gw1000/issues "Ecowitt Gateway driver Issues") should only be used for specific bugs in the Ecowitt Gateway driver code. It is recommended that even if an Ecowitt Gateway driver bug is suspected users first post to the Google Groups [weewx-user forum](https://groups.google.com/g/weewx-user "Google Groups weewx-user forum").

## Description ##

The Ecowitt Gateway driver (formerly the GW1000 driver) is a WeeWX driver that supports devices compatible with the Ecowitt LAN/Wi-Fi Gateway API.

The Ecowitt Gateway driver utilises the Ecowitt LAN/Wi-Fi Gateway API thus using a pull methodology for obtaining data from the gateway device rather than the push methodology used by other drivers. This has the advantage of giving the user more control over when the data is obtained from the gateway device.

The Ecowitt Gateway driver can be operated as a traditional WeeWX driver where it is the source of loop data or it can be operated as a WeeWX service where it is used to augment loop data produced by another driver.

## Pre-Requisites ##

The Ecowitt Gateway driver requires WeeWX v3.7.0 or greater and will operate under Python2 or Python 3.

## Installation Instructions ##

**Note**:   Symbolic names are used below to refer to file locations on the WeeWX system. Symbolic names allow a common name to be used to refer to a directory that may be different from system to system. The following symbolic name is used below:

-   *BIN_ROOT*. The path to the directory where WeeWX executables are located. This directory varies depending on WeeWX installation method. Refer to [where to find things](http://weewx.com/docs/usersguide.htm#Where_to_find_things) in the WeeWX User's Guide for further information.

### Installation as a WeeWX driver ###

1.  If the Ecowitt Gateway driver is to be installed on a fresh WeeWX installation first [install WeeWX](http://weewx.com/docs/usersguide.htm#installing) and configure it to use the *simulator*.

2.  Install the driver using the *wee_extension* utility:

    - download the Ecowitt Gateway driver extension package:

            $ wget -P /var/tmp https://github.com/gjr80/weewx-gw1000/releases/download/v0.5.0/gw1000-0.5.0.tar.gz

    - install the Ecowitt Gateway driver extension:

            $ wee_extension --install=/var/tmp/gw1000-0.5.0.tar.gz
            
        **Note:** Depending on your system/installation the above command may need to be prefixed with *sudo*.

        **Note:** Depending on your WeeWX installation *wee_extension* may need to be prefixed with the path to *wee_extension*.
   
3.  Confirm that WeeWX is set to use software [record generation](http://weewx.com/docs/usersguide.htm#record_generation). In *weewx.conf* under *[StdArchive]* ensure the *record_generation* setting is set to *software*:
    
        [StdArchive]
            ....
            record_generation = software
    
    If *record_generation* is set to *hardware* change it to *software*.
        
4.  Test the Ecowitt Gateway driver by running the driver file directly using the *--test-driver* command line option:

        $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --test-driver

    for *setup.py* installs or for package installs use:

        $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --test-driver
    
    **Note:** Depending on your system/installation the above command may need to be prefixed with *sudo*.

    **Note:** Whilst the driver may be run independently of WeeWX the driver still requires WeeWX and it's dependencies be installed. Consequently, if WeeWX 4.0.0 or later is installed the driver must be run under the same Python version as WeeWX uses. This may be different to the Python version invoked by the command 'python'. This means that on some systems 'python' in the above commands may need to be changed to 'python2' or 'python3'.
    
    **Note:** If necessary you can specify the device IP address and port using the *--ip-address* and *--port* command line options. Refer to the Ecowitt Gateway driver help by using the *--help* command line option for further information.

    You should observe loop packets being emitted on a regular basis. Once finished press *ctrl-c* to exit.

    **Note:** You will only see loop packets and not archive records when running the driver directly. This is because you are seeing output directly from the driver and not WeeWX. 

5.  Configure the driver:

        $ wee_config --reconfigure --driver=user.gw1000

    **Note:** Depending on your system/installation the above command may need to be prefixed with *sudo*.

    **Note:** Depending on your WeeWX installation *wee_config* may need to be prefixed with the path to *wee_config*.

6.  You may choose to [run WeeWX directly](http://weewx.com/docs/usersguide.htm#Running_directly) to observe the loop packets and archive records being generated by WeeWX.

7.  Once satisfied that the Ecowitt Gateway driver is operating correctly you can restart the WeeWX daemon:

        $ sudo /etc/init.d/weewx restart
        
    or

        $ sudo service weewx restart

    or

        $ sudo systemctl restart weewx

8.  You may wish to refer to the [GW1000 driver wiki](https://github.com/gjr80/weewx-gw1000/wiki) for further guidance on customising the operation of the Ecowitt Gateway driver and integrating gateway device data into WeeWX generated reports. 

### Installation as a WeeWX service ###

1. [Install WeeWX](http://weewx.com/docs/usersguide.htm#installing) and configure it to use either the *simulator* or another driver of your choice.

2. Install the Ecowitt Gateway driver extension using the *wee_extension* utility as per *Installation as a WeeWX driver* step 2 above.

3. Edit *weewx.conf* and under the *[Engine] [[Services]]* stanza add an entry *user.gw1000.GatewayService* to the *data_services* option. It should look something like:

        [Engine]
        
            [[Services]]
                ....
                data_services = user.gw1000.GatewayService

4. Test the GW1000 service by running the driver file directly using the *--test-service* command line option:

        $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --test-service

    for *setup.py* installs or for package installs use:

        $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --test-service
    
    **Note:** Depending on your system/installation the above command may need to be prefixed with *sudo*.

    **Note:** Whilst the Ecowitt Gateway driver may be run as a service independently of WeeWX the driver/service still requires WeeWX and it's dependencies be installed. Consequently, if WeeWX 4.0.0 or later is installed the driver/service must be run under the same Python version as WeeWX uses. This may be different to the Python version invoked by the command 'python'. This means that on some systems 'python' in the above commands may need to be changed to 'python2' or 'python3'.
    
    **Note:** If necessary you can specify the gateway device IP address and port using the *--ip-address* and *--port* command line options. Refer to the GW1000 driver help using *--help* for further information.

    You should observe loop packets being emitted on a regular basis. Some, but not necessarily all, loop packets should include gateway device data. Once finished press *ctrl-c* to exit.

    **Note:** When the Ecowitt Gateway driver is run directly with the *--test-service* command line option a series of simulated loop packets are emitted every 10 seconds to simulate a running WeeWX instance. The gateway device is polled and the gateway device data added to the loop packets when available. As the default gateway device poll interval is 60 seconds not all loop packets will be augmented with gateway device data.

    **Note:** You will only see loop packets and not archive records when running the service directly. This is because you are seeing the direct output of the driver and the Ecowitt Gateway service and not WeeWX. 

6. You may choose to [run WeeWX directly](http://weewx.com/docs/usersguide.htm#Running_directly) to observe the loop packets and archive records being generated by WeeWX. Note that depending on the frequency of the loop packets emitted by the in-use driver and the polling interval of the Ecowitt Gateway service not all loop packets may include gateway device data; however, provided that the gateway device polling interval is less than the frequency of the loop packets emitted by the in-use driver each archive record should contain gateway device data.

7. Once satisfied that the Ecowitt Gateway service is operating correctly you can restart the WeeWX daemon:

        $ sudo /etc/init.d/weewx restart

    or

        $ sudo service weewx restart

    or

        $ sudo systemctl restart weewx

8. You may wish to refer to the [GW1000 driver wiki](https://github.com/gjr80/weewx-gw1000/wiki) for further guidance on customising the operation of the GW1000 driver and integrating GW1000 data into WeeWX generated reports. 

## Upgrade Instructions ##

**Note:** Before upgrading the Ecowitt Gateway driver, check the [Instructions for specific versions](https://github.com/gjr80/weewx-gw1000/wiki/Upgrade-Guide#instructions-for-specific-versions) section of the Ecowitt Gateway driver [Upgrade Guide](https://github.com/gjr80/weewx-gw1000/wiki/Upgrade-Guide) to see if any specific actions are required as part of the upgrade.

To upgrade from an earlier version of the Ecowitt Gateway driver or GW1000 driver (installed as either a WeeWX driver or a WeeWX service) simply install the Ecowitt Gateway driver version you wish to upgrade to as per the [Installation Instructions](#installation-instructions) above.

**Note:** The [Installation Instructions](#installation-instructions) refer to the current release only. It is recommended that users upgrade to the latest release rather than an earlier release.

## Downgrade Instructions ##

To downgrade to an earlier release first uninstall the currently installed Ecowitt Gateway driver (or GW1000 driver) and then install the desired release as per the [Installation Instructions](#installation-instructions) above. 

**Note:** Care should be taken when downgrading to an earlier release as subsequent releases may have entailed enduring changes; for example database schema changes, that are not undone by simply uninstalling the driver.

## Support ##

General support issues for the Ecowitt Gateway driver should be raised in the Google Groups [weewx-user forum](https://groups.google.com/g/weewx-user "Google Groups weewx-user forum"). The Ecowitt Gateway driver [Issues Page](https://github.com/gjr80/weewx-gw1000/issues "Ecowitt Gateway driver Issues") should only be used for specific bugs in the Ecowitt Gateway driver code. It is recommended that even if an Ecowitt Gateway driver bug is suspected users first post to the Google Groups [weewx-user forum](https://groups.google.com/g/weewx-user "Google Groups weewx-user forum").

## Licensing ##

The Ecowitt Gateway driver/GW1000 driver is licensed under the [GNU Public License v3](https://github.com/gjr80/weewx-gw1000/blob/master/LICENSE "Ecowitt Gateway Driver License").
