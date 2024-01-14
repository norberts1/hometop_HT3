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
 # rev.: 0.1 date: 2023-03-11
 # rev.: 0.2 date: 2023-03-20 database creation only on request.
 #                             issue: #25
 # rev.: 0.3 date: 2024-01-12 sysv startup scripts now systemd-services.
 #                             issue: #31
 # 
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
 sudo systemctl daemon-reload  >/dev/null
 # remove old sysv-scipts if available
 sudo rm -f /etc/init.d/$3  >/dev/null
 # install and enable the latest version
 sudo cp -a $2 /etc/systemd/system/ >/dev/null
 sudo systemctl --quiet enable $1
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
install_service ht_proxy.service ~/HT3/sw/etc/sysconfig/ht_proxy.service ht_proxy
install_service ht_collgate.service ~/HT3/sw/etc/sysconfig/ht_collgate.service ht_collgate
install_service httpd.service ~/HT3/sw/etc/sysconfig/httpd.service httpd
install_service ht_2hass.service ~/HT3/sw/etc/sysconfig/ht_2hass.service ht_2hass

echo
echo "----------------------------------"
read -p '  Databases required (y/n) ?' creation_required
echo
if [ "$creation_required" = "y" ]; then
  read -p '   1. Sql-Database wanted (y/n) ?' sql_db_required
  if [ "$sql_db_required" = "y" ]; then
    sed --in-place -zE 's/(<sql-db>\s*<enable>)off(<\/enable>)/\1on\2/gm' ~/HT3/sw/etc/config/HT3_db_cfg.xml
  else
    sed --in-place -zE 's/(<sql-db>\s*<enable>)on(<\/enable>)/\1off\2/gm' ~/HT3/sw/etc/config/HT3_db_cfg.xml
  fi
  read -p '   2. rrdtool-db   wanted (y/n) ?' rrdtool_db_required
  if [ "$rrdtool_db_required" = "y" ]; then
    sed --in-place -zE 's/(<rrdtool-db>\s*<enable>)off(<\/enable>)/\1on\2/gm' ~/HT3/sw/etc/config/HT3_db_cfg.xml
  else
    sed --in-place -zE 's/(<rrdtool-db>\s*<enable>)on(<\/enable>)/\1off\2/gm' ~/HT3/sw/etc/config/HT3_db_cfg.xml
  fi

  echo "  >-- create databases --------<  "
  cd ~/HT3/sw
  ./create_databases.py
else
  echo " No database-creation required"
fi
echo "----------------------------------"
echo "  >-- check serial port (UART) configuration --<"
echo "   --  configured is: --"
grep -e '<serialdevice>' ~/HT3/sw/etc/config/ht_proxy_cfg.xml
echo "   --  required   is: --"
grep -e 'serial-device' ~/HT3/sw/etc/config/ht_proxy_cfg.xml
grep -e 'dev:' ~/HT3/sw/etc/config/ht_proxy_cfg.xml
echo "   -- modify file: ~/HT3/sw/etc/config/ht_proxy_cfg.xml if required"
echo ""
echo "   -- details see URL:"
echo "   -- https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts"
echo ""
echo "----------------------------------"
echo "----- post_setup done ------------"



