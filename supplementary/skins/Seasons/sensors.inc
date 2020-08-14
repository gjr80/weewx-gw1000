## sensors module for weewx skins
## Copyright Tom Keffer, Matthew Wall
## See LICENSE.txt for your rights
## modified for operation with the GW1000 driver
#errorCatcher Echo
#encoding UTF-8
##
## this is a conditional display of sensor data, including connectivity,
## battery status, and various voltages.  if there are no data available,
## then this degenerates to nothing displayed.
##
## To include GW1000 sensor battery state information in the Seasons skin
## Sensor Panel list the sensor battery states to display in the
## $sensor_batt_data list. Sensors will be displayed in the order listed. Each
## entry is in the format:
##      (WeeWX sensor battery state field name, decode function name)
## where 'WeeWX sensor battery state field name' is the WeeWX field holding the
## battery state data and 'decode function name' is set as follows depending on
## the sensor type:
##      WH24: 'get_binary_battery_status'
##      WH25: 'get_binary_battery_status'
##      WH26: 'get_binary_battery_status'
##      WH31: 'get_binary_battery_status'
##      WH32: 'get_binary_battery_status'
##      WH40: 'get_binary_battery_status'
##      WH41: 'get_multi_battery_status'
##      WH51: 'get_binary_battery_status'
##      WH55: 'get_multi_battery_status'
##      WH57: 'get_multi_battery_status'
##      WH65: 'get_binary_battery_status'
##
#set $sensor_batt_data = [('wh31_ch1_batt', 'get_binary_battery_status'),
                          ('wh31_ch2_batt', 'get_binary_battery_status'),
                          ('wh41_ch1_batt', 'get_multi_battery_status'),
                          ('wh51_ch1_batt', 'get_binary_battery_status'),
                          ('wh51_ch2_batt', 'get_binary_battery_status'),
                          ('wh51_ch3_batt', 'get_binary_battery_status'),
                          ('wh51_ch4_batt', 'get_binary_battery_status'),
                          ('wh57_batt', 'get_multi_battery_status')
                         ]
##
#def get_binary_battery_status($x)
#if $x == 0
<span class="status_ok">OK</span>
#else
<span class="status_low">LOW</span>
#end if
#end def
##
#def get_multi_battery_status($x)
  #if $x <= 1
<span class="status_low">LOW</span>
  #elif $x <= 5
<span class="status_ok">OK</span>
  #elif $x == 6
<span class="status_ok">DC</span>
  #end if
#end def
##
## first see what sensor data are available
##
#set $have_conn = 0
#for $x in [$day.rxCheckPercent]
  #if $x.has_data
    #set $have_conn = 1
  #end if
#end for
##
#set $have_battery_status = 0
#for $x in $sensor_batt_data
  #try
      #if getattr($current, $x[0]).has_data
        #set $have_battery_status = 1
      #end if
  #except AttributeError
    ## there is no battery state data for this sensor
    #pass
  #end try
#end for
##
#set $have_voltage = 0
#for $x in [$day.consBatteryVoltage, $day.heatingVoltage, $day.supplyVoltage, $day.referenceVoltage]
  #if $x.has_data
    #set $have_voltage = 1
  #end if
#end for
##
## now display the available data only
##
#if $have_conn or $have_battery_status or $have_voltage
<div id='sensors_widget' class="widget">
  <div class="widget_title">
    <a href="telemetry.html">Sensor Status</a>
    <a class="widget_control"
      onclick="toggle_widget('sensors')">&diams;</a>
  </div>
  <div class="widget_contents">
  <table>
##
#if $have_conn
  <tr><th>Connectivity</th><th></th></tr>
#if $day.rxCheckPercent.has_data
  <tr>
    <td class="label">$obs.label.rxCheckPercent</td>
    <td class="data">$current.rxCheckPercent</td>
  </tr>
#end if
#end if
##
#if $have_battery_status
  <tr><th>Battery Status</th><th></th></tr>
  #for $battery in $sensor_batt_data
    #try
      #if getattr($current, $battery[0]).has_data
        #set $state = getattr(self, $battery[1])(getattr($current, $battery[0]).raw)
  <tr>
    <td class="label">$obs.label[$battery[0]]</td>
    <td class="data">$state</td>
  </tr>
      #end if
    #except AttributeError
      ## there is no battery state data for this sensor
      #pass
    #end try
  #end for
#end if
##
#if $have_voltage
    <tr><th>Voltage</th><th></th></tr>
#if $day.consBatteryVoltage.has_data
    <tr>
      <td class="label">$obs.label.consBatteryVoltage</td>
      <td class="data">$current.consBatteryVoltage</td>
    </tr>
#end if
#if $day.heatingVoltage.has_data
    <tr>
      <td class="label">$obs.label.heatingVoltage</td>
      <td class="data">$current.heatingVoltage</td>
    </tr>
#end if
#if $day.supplyVoltage.has_data
    <tr>
      <td class="label">$obs.label.supplyVoltage</td>
      <td class="data">$current.supplyVoltage</td>
    </tr>
#end if
#if $day.referenceVoltage.has_data
    <tr>
      <td class="label">$obs.label.referenceVoltage</td>
      <td class="data">$current.referenceVoltage</td>
    </tr>
#end if
#end if
  </table>
  </div>
##
</div>
#end if
