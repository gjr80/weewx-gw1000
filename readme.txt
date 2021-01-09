GW1000 Driver

Description

The GW1000 driver is a WeeWX driver that supports the Ecowitt GW1000 WiFi
Gateway via the GW1000 API.

The GW1000 driver utilises the GW1000 API thus using a pull methodology for
obtaining data from the GW1000 rather than the push methodology used by current
drivers. This has the advantage of giving the user more control over when the
data is obtained from the GW1000 plus also giving access to a greater range of
metrics.

The GW1000 driver can be operated as a traditional WeeWX driver where it is the
source of loop data or it can be operated as a WeeWX service where it is used
to augment loop data produced by another driver.

Pre-Requisites

The GW1000 driver requires WeeWX v3.7.0 or greater and will operate under
Python2 or Python 3.

Installation Instructions

Note: Symbolic names are used below to refer to file locations on the WeeWX
      system. Symbolic names allow a common name to be used to refer to a
      directory that may be different from system to system. The following
      symbolic name is used below:

    BIN_ROOT. The path to the directory where WeeWX executables are located.
    This directory varies depending on WeeWX installation method. Refer to
    http://weewx.com/docs/usersguide.htm#Where_to_find_things in the WeeWX
    User's Guide for further information.

Installation as a WeeWX driver

1.  If the GW1000 driver is to be installed on a fresh WeeWX installation
install WeeWX (refer to http://weewx.com/docs/usersguide.htm#installing) and
configure it to use the simulator.

2.  If installing the driver using the wee_extension utility (the recommended
method):

    -   download the GW1000 driver extension package:

        $ wget -P /var/tmp https://github.com/gjr80/weewx-gw1000/releases/download/v0.2.0/gw1000-0.2.0.tar.gz

    -   install the GW1000 driver extension:

        $ wee_extension --install=/var/tmp/gw1000-0.2.0.tar.gz
            
        Note: Depending on your system/installation the above command may need
              to be prefixed with sudo.

        Note: Depending on your WeeWX installation wee_extension may need to be
              prefixed with the path to wee_extension.

    -   skip to step 4

3.  If installing manually:

    -   download the GW1000 driver extension package:

        $ wget -P /var/tmp https://github.com/gjr80/weewx-gw1000/releases/download/v0.2.0/gw1000-0.2.0.tar.gz

    -   extract the contents of the GW1000 driver extension package:
    
        $ tar -xzf /var/tmp/gw1000-0.2.0.tar.gz -C /var/tmp
     
    -   copy the file gw1000.py to the $BIN_ROOT/user directory:
    
        $ cp /var/tmp/gw1000/bin/user/gw1000.py $BIN_ROOT/user

        Note: Depending on your system/installation the above command may need
              to be prefixed with sudo.

    -   add the following stanza to weewx.conf:

        [GW1000]
            # This section is for the GW1000

            # The driver itself
            driver = user.gw1000

    -   add the following stanza to weewx.conf:

        [Accumulator]
            [[lightning_strike_count]]
                extractor = sum
            [[lightning_last_det_time]]
                extractor = last
            [[lightning_distance]]
                extractor = last
            [[daymaxwind]]
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

        Note: If an [Accumulator] stanza already exists in weewx.conf just add
              the child settings.

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

    Note: Depending on your system/installation the above command may need
              to be prefixed with sudo.

    Note: Whilst the driver may be run independently of WeeWX the driver still
          requires WeeWX and it's dependencies be installed. Consequently, if 
          WeeWX 4.0.0 or later is installed the driver must be run under the 
          same Python version as WeeWX uses. This may be different to the Python 
          version invoked by the command 'python'. This means that on some 
          systems 'python' in the above commands may need to be changed to 
          'python2' or 'python3'.

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
          be prefixed with *sudo*.

    Note: Depending on your WeeWX installation wee_config may need to be
          prefixed with the path to wee_config.

7.  You may choose to run WeeWX directly (refer http://weewx.com/docs/usersguide.htm#Running_directly)
to observe the loop packets and archive records being generated by WeeWX.

8.  Once satisfied that the GW1000 driver is operating correctly you can
restart the WeeWX daemon:

    $ sudo /etc/init.d/weewx restart
        
    or

    $ sudo service weewx restart

    or

    $ sudo systemctl restart weewx

9.  You may wish to refer to the GW1000 driver wiki(https://github.com/gjr80/weewx-gw1000/wiki)
for further guidance on customising the operation of the GW1000 driver and
integrating GW1000 data into WeeWX generated reports.


Installation as a WeeWX service

1.  Install WeeWX (refer http://weewx.com/docs/usersguide.htm#installing) and
configure it to use either the simulator or another driver of your choice.

2.  If installing the driver using the wee_extension utility (the recommended
method) install the GW1000 driver extension using the wee_extension utility as
per Installation as a WeeWX driver step 2 above.

3.  If installing the driver manually install the GW1000 driver manually as per
Installation as a WeeWX driver step 3 above.

4.  Edit weewx.conf and under the [Engine] [[Services]] stanza add an entry
user.gw1000.Gw1000Service to the data_services option. It should look something
like:

    [Engine]

        [[Services]]
            ....
            data_services = user.gw1000.Gw1000Service

5.  Test the GW1000 service by running the driver file directly using the
--test-service command line option:

    $ PYTHONPATH=/home/weewx/bin python -m user.gw1000 --test-service

    for setup.py installs or for package installs use:

    $ PYTHONPATH=/usr/share/weewx python -m user.gw1000 --test-service
    
    Note: Depending on your system/installation the above command may need
          to be prefixed with sudo.

    Note: Whilst the driver may be run independently of WeeWX the driver still
          requires WeeWX and it's dependencies be installed. Consequently, if 
          WeeWX 4.0.0 or later is installed the driver must be run under the 
          same Python version as WeeWX uses. This may be different to the Python 
          version invoked by the command 'python'. This means that on some 
          systems 'python' in the above commands may need to be changed to 
          'python2' or 'python3'.
          
    Note: If necessary you can specify the GW1000 IP address and port using the
          --ip-address and --port command line options. Refer to the GW1000
          driver help using --help for further information.

    You should observe loop packets being emitted on a regular basis. Some, but
    not necessarily all, loop packets should include GW1000 data. Once finished
    press ctrl-c to exit.

    Note: When the GW1000 driver is run directly with the --test-service command
          line option a series of simulated loop packets are emitted every
          10 seconds to simulate a running WeeWX instance. The GW1000 is polled
          and the GW1000 data added to the loop packets when available. As the
          default GW1000 poll interval is 60 seconds not all loop packets will
          be augmented with GW1000 data.

    Note: You will only see loop packets and not archive records when running
          the service directly. This is because you are seeing the direct
          output of the driver and the GW1000 service and not WeeWX.

6.  You may choose to run WeeWX directly (refer http://weewx.com/docs/usersguide.htm#Running_directly)
to observe the loop packets and archive records being generated by WeeWX. Note
that depending on the frequency of the loop packets emitted by the in-use
driver and the polling interval of the GW1000 service not all loop packets may
include GW1000 data; however, provided that the GW1000 polling interval is less
than the frequency of the loop packets emitted by the in-use driver each
archive record should contain GW1000 data.

7.  Once satisfied that the GW1000 service is operating correctly you can
restart the WeeWX daemon:

    $ sudo /etc/init.d/weewx restart

    or

    $ sudo service weewx restart

    or

    $ sudo systemctl restart weewx

8.  You may wish to refer to the GW1000 driver wiki(https://github.com/gjr80/weewx-gw1000/wiki)
for further guidance on customising the operation of the GW1000 driver and
integrating GW1000 data into WeeWX generated reports.