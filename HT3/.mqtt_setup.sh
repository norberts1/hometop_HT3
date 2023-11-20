#!/bin/bash
#
 ##
 # #################################################################
 ## Copyright (c) 2023 Norbert S. <junky-zs at gmx dot de>
 #
 # This program is free software: you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation, either version 3 of the License, or
 # (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 # GNU General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License
 # along with this program. If not, see <http://www.gnu.org/licenses/>.
 #
 #################################################################
 # rev.: 0.1  date: 2023-03-11 first release.
 # rev.: 0.2  date: 2023-11-20 pip3 not used anymore.
######################
 #                                                               #
 # mqtt-setup for ht-project                                     #
 #                                                               #
 #################################################################

echo "=================================="
echo "mqtt-setup for ht_project"
echo "----------------------------------"
sudo -v
if [ $? -ne 0 ]; then
 echo " -> sudo-call not allowed for this user, please ask the admin";
 exit 1
fi
echo "  >------- update os ----------<  "
sudo apt-get update
echo "  >------- mosquitto ----------<  "
sudo apt-get -y install mosquitto mosquitto-clients

echo "  >------- mqtt-config enable -<  "
grep -e 'On' ~/HT3/sw/etc/config/collgate_cfg.xml
if [ $? -ne 0 ]; then
 echo "  mqtt-interface has to be enabled, see following example:"
 echo "    <MQTT_client_if>"
 echo "      <enable>On</enable>"
 echo "      <cfg_file>./etc/config/mqtt_client_cfg.xml</cfg_file>"
 echo "    </MQTT_client_if>"
 echo
 echo -n "mqtt enable wanted (y/n) ?"
 read mqtt_enable_wanted
 echo
 if [ "$mqtt_enable_wanted" = "y" ]; then
   sed --in-place -zE 's/(<MQTT_client_if>\s*<enable>)Off(<\/enable>)/\1On\2/gm' ~/HT3/sw/etc/config/collgate_cfg.xml
 fi
fi
echo "  >------- python3-paho-mqtt --<  "
sudo apt -y install python3-paho-mqtt;
echo "----- mqtt-setup done ------------"
