# Kamstrup to MQTT

Using this script, I periodically check my Kamstrup Multical 402. I'm sending the data to my Home Assistant server using MQTT. This way I can track my heat consumption. This script was created with some parts of code I found online. Unfortunately, I can't track the original creators.

<h3>Needed hardware:</h3>
- Orange Pi Zero (any Linux board will do)
- RJ-OPUSB-IEC USB optical probe (https://nl.aliexpress.com/i/1731230485.html)

<img src="https://user-images.githubusercontent.com/8334400/160201827-0614c814-c154-4e33-af3c-3fae28fd52a0.png" alt="drawing" width="200"/> <img src="https://user-images.githubusercontent.com/8334400/160201809-d6fad319-2fe9-4951-ad78-31123c12bbc1.png" alt="drawing" width="200"/>

<h3>Step 1:</h3>
Install Debian or another Linux based OS. Installed the following components:
<ul>
  <li>pip3</li>
  <li>python3</li>
  <li>paho mqtt</li>
  <li>pyserial</li>
</ul>

<h3>Step 2:</h3>
Plug in the USB optical probe and check if the port corresponds to the one in the file (kamstrup.py).

<h3>Step 3:</h3>
Change the following details in the file (kamstrup.py):
<ul>
  <li>broker = '_BROKERSIPADDRESS_'</li>
  <li>username = '_YOURMQTTUSERNAME_'</li>
  <li>password = '_YOURMQTTPASSWORD_'</li>
 </ul>

<h3>Step 4:</h3>
Upload the file and set a cron that runs the script every X minutes. My cron runs every 20 minutes. A high interval can drain the battery of the Kamtrup meter, so be careful. If you are using Home Assistant, make sure you add the sensors to your _configuration.yaml_. I use the following:

<pre>
    ### Kamtrup MQTT sensors ###
  - platform: mqtt
    state_topic: "kamstrup/gj"
    name: "Heat consumption"
    unit_of_measurement: "Gj"
    value_template: "{{ value | round(3) }}"
  - platform: mqtt
    state_topic: "kamstrup/temp1"
    name: "Heating temperature in"
    unit_of_measurement: "°C"
  - platform: mqtt
    state_topic: "kamstrup/temp2"
    name: "Heating temperature out"
    unit_of_measurement: "°C"
  - platform: mqtt
    state_topic: "kamstrup/flow"
    name: "Heating flow"
    unit_of_measurement: "L/min"
 </pre>
