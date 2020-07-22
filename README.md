# GW1000 Driver #

## Description ##

The GW1000 driver is a WeeWX driver that supports the Ecowitt GW1000 WiFi Gateway via the GW1000 API.

The GW1000 driver utilise the GW1000 API thus using a pull methodology for obtaining data from the GW1000 rather than the push methodology used by current drivers. This has the advantage of giving the user more control over when the data is obtained from the GW1000 plus also giving access to a greater range of metrics.

The GW1000 driver can be operated as a traditional WeeWX driver where it is the source of loop data or it can be operated as a WeeWX service where it is used to augment loop data produced by another driver.

## Pre-Requisites ##

The GW1000 driver requires WeeWX v3.7.0 or greater.

## Installation Instructions ##

**Note**:   Symbolic names are used below to refer to some file location on the WeeWX system. These symbolic names allow a common name to be used to refer to a directory that may be different from system to system. The following symbolic names are used below:

-   *$BIN_ROOT*. The path to the directory where WeeWX executables are located. This directory varies depending on WeeWX installation method. Refer to [where to find things](http://weewx.com/docs/usersguide.htm#Where_to_find_things) in the WeeWX User's Guide for further information.

### Installation as a WeeWX driver ###

1.  If installing on a fresh WeeWX installation [install WeeWX](http://weewx.com/docs/usersguide.htm#installing) and configure it to use the *simulator*.

2.  If installing the driver using the *wee_extension* utility (the recommended method):

    -   download the GW1000 driver extension package:

            $ wget -P /var/tmp https://github.com/gjr80/weewx-gw1000/releases/download/v0.1.0b3/weewx-gw1000-0.1.0b3.tar.gz

    -   install the GW1000 driver extension:

            $ wee_extension --install=/var/tmp/weewx-gw1000.0.1.0b3.tar.gz

    -   skip to step 4

3.  If installing manually:

    -   download the GW1000 driver extension package:

            $ wget -P /var/tmp https://github.com/gjr80/weewx-gw1000/releases/download/v0.1.0b3/weewx-gw1000-0.1.0b3.tar.gz

    -   extract *gw1000.py* from the GW1000 driver extension package:
    
            $ tar -xzf /var/tmp/weewx-gw1000.0.1.0b3.tar.gz
     
    -   copy the file *gw1000.py* to the *$BIN_ROOT/user* directory:
    
            $ cp gw1000.py $BIN_ROOT/user

    -   add the following stanza to *weewx.conf*:

            [GW1000]
                # This section is for the GW1000
            
                # The driver itself
                driver = user.gw1000

    -   add the following stanza to *weewx.conf*:

            [Accumulator]
                [[lightning_strike_count]]
                    extractor = sum
                [[lightning_last_det_time]]
                    extractor = last

        **Note:** If an *[Accumulator]* stanza already exists in *weewx.conf* just add the child settings.

4.  The GW1000 driver uses a default field map to map GW1000 API fields to common WeeWX fields. If required this default field map can be overridden by adding a *[[field_map]]* stanza to the *[GW1000]* stanza in *weewx.conf*. To override the default sensor map add the following under the *[GW1000]* stanza in *weewx.conf* altering/removing/adding field maps entries as required:

        [GW1000]
            ...
            # Define a mapping to map GW1000 fields to WeeWX fields.
            #
            # Format is weewx_field = GW1000_field
            #
            # where:
            #   weewx_field is a WeeWX field name to be included in the generated loop
            #       packet
            #   GW1000_field is a GW1000 API field
            #
            #   Note: WeeWX field names will be used to populate the generated loop
            #         packets. Fields will only be saved to database if the field name
            #         is included in the in-use database schema.
            #
            [[field_map]]
               outTemp = outtemp
               ...

    Details of all supported GW1000 fields can be viewed by running the GW1000 driver with the *--default-map* command line option to display the default field map.

    However, the available GW1000 fields will depend on what sensors are connected to the GW1000. The available fields and current observation values for a given GW1000 can be viewed by running the GW1000 driver directly with the *--live-data* command line option.

    **Note:** Only WeeWX loop packet fields that exist in the in-use database schema will be saved to archive. WeeWX field names that are not included in the in-use database schema are available as *$current* tags only in WeeWX generated reports. 

5.  The default field map can also be modified without needing to specify the entire field map by adding a *[[field_map_extensions]]* stanza to the *[GW1000]* stanza in *weewx.conf*. The field mappings under *[[field_map_extensions]]* are used to modify the default field map, for example, the following could be used to map the humidity reading from WH31 channel 5 to the WeeWX *inHumidity* field whilst keeping all other field mappings as is:

        [GW1000]
            ...
            [[field_map_extensions]]
                inHumidity = humid5

6.  Test the now configured GW1000 driver using the *--test-driver* command line option. You should observe loop packets being emitted on a regular basis using the WeeWX field names from the default or modified field map.

7.  Configure the driver:

        $ sudo wee_config --reconfigure --driver=user.gw1000 --no-prompt

8.  You may chose to (run WeeWX directly](http://weewx.com/docs/usersguide.htm#Running_directly) to observe the loop packets and archive records being generated by WeeWX.

9.  Once satisfied that the GW1000 driver is operating correctly you can start the WeeWX daemon:

        $ sudo /etc/init.d/weewx start
        
    or

        $ sudo service weewx start

    or

        $ sudo systemctl start weewx

### Installation as a WeeWX service ###

1.  [Install WeeWX](http://weewx.com/docs/usersguide.htm#installing) and configure it to use either the *simulator* or another driver of your choice.

2.  Install the GW1000 driver using the *wee_extension* utility as per *Installation as a WeeWX driver* step 2 above or copy this file to *$BIN_ROOT/user*.

3.  Modify *weewx.conf* as per *Installation as a WeeWX driver* step 3 above.

4.  Under the *[Engine] [[Services]]* stanza in *weewx.conf* add an entry *user.gw1000.Gw1000Service* to the *data_services* option. It should look something like:

        [Engine]
        
            [[Services]]
                ....
                data_services = user.gw1000.Gw1000Service

5.  If required, modify the default field map to suit as per *Installation as a WeeWX driver* steps 4 and 5.

6.  Test the now configured GW1000 service using the *--test-service* command line option. You should observe loop packets being emitted on a regular basis that include GW1000 data. Note that not all loop packets will include GW1000 data.

7.  You may chose to [run WeeWX directly](http://weewx.com/docs/usersguide.htm#Running_directly) to observe the loop packets and archive records being generated by WeeWX. Note that depending on the frequency of the loop packets emitted by the in-use driver and the polling interval of the GW1000 service not all loop packets may include GW1000 data.

8.  Once satisfied that the GW1000 service is operating correctly you can start the WeeWX daemon:

        $ sudo /etc/init.d/weewx start

    or

        $ sudo service weewx start

    or

        $ sudo systemctl start weewx