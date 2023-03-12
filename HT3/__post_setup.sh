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
 # date: 2023-03-11
 # rev.: 0.1
 #################################################################
 #                                                               #
 # post-setup for ht-project                                     #
 #                                                               #
 #################################################################

echo "=================================="
echo "postsetup for ht_project"
echo "----------------------------------"
sudo -v >/dev/null
if [ $? -ne 0 ]; then
 echo " -> sudo-call not allowed for this user, please ask the admin";
 exit 1
fi
if [ ! -d ~/HT3 ]; then
 echo " -> ~/HT3 folder must be available"
 exit 1
fi
##### sub-functions #####
install_service()
 # installation of service
 # used parameter:
 #  $1=service, $2=source, $3=short_name
{
 # echo "service:$1, source:$2, short_name:$3"
 echo "   $1 -> install latest version";
 # stop and disable current version of service if available
 sudo systemctl --quiet stop $1  >/dev/null
 sudo systemctl --quiet disable $1  >/dev/null
 # install and enable the latest version
 chmod + $2
 sudo rm -f /etc/init.d/$3  >/dev/null
 sudo cp -a $2 /etc/init.d  >/dev/null
 sudo systemctl --quiet enable $3
 if [ $? -ne 0 ]; then
  echo "    ! failed to enable: $1 !"
  exit 1
 else
  sudo systemctl --quiet is-enabled $1
  if [ $? -ne 0 ]; then
   echo "    ! $1 is not enabled !"
   exit 1
  fi
 fi
}

sudo apt-get -y autoremove

# installation of systemd startup-scripts
echo "  >-- enable startup-scripts --<  "
install_service ht_proxy.service ~/HT3/sw/etc/sysconfig/ht_proxy ht_proxy
install_service ht_collgate.service ~/HT3/sw/etc/sysconfig/ht_collgate ht_collgate
install_service httpd.service ~/HT3/sw/etc/sysconfig/httpd httpd
install_service ht_2hass.service ~/HT3/sw/etc/sysconfig/ht_2hass ht_2hass

echo
echo "  >-- create databases --------<  "
cd ~/HT3/sw
./create_databases.py

echo "----- post_setup done ------------"



