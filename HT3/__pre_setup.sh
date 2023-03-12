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
 # prepare os-parts and configuration for ht-project             #
 #                                                               #
 #################################################################

echo "=================================="
echo "update and upgrade os"
echo "----------------------------------"
sudo -v
if [ $? -ne 0 ]; then
 echo " -> sudo-call not allowed for this user, please ask the admin.";
 exit 1
fi

sudo apt-get update
sudo apt-get -y upgrade
echo "check and install required packages"
echo "----------------------------------"
echo "  >------- pip3 ---------------<  "
which pip3 >/dev/null
if [ $? -eq 0 ]; then
 echo " -> pip3 available";
else
 echo "pip3 NOT available -> installation started";
 sudo apt-get -y install pip3;
fi
echo "----------------------------------"
echo "  >------- python3 --- --------<  "
which python3 >/dev/null
if [ $? -eq 0 ]; then
 echo " -> python3 available";
else
 echo "python3 NOT available -> installation started";
 sudo pip3 python3;
fi
echo "----------------------------------"
echo "  >------- python3-serial -----<  "
pip3 show pyserial >/dev/null
if [ $? -eq 0 ]; then
 echo " -> python3-serial available";
else
 echo "python3-serial NOT available -> installation started";
 sudo apt-get -y install python3-serial;
fi
echo "----------------------------------"
echo "  >------- python3-setuptools -<  "
pip3 show setuptools >/dev/null
if [ $? -eq 0 ]; then
 echo " -> python3-setuptools available";
else
 echo "python3-setuptools NOT available -> installation started";
 sudo apt-get -y install python3-setuptools;
fi

echo "----------------------------------"
echo "  >------- python3-tk ---------<  "
sudo apt-get -y install python3-tk;
echo "----------------------------------"
echo "  >------- librrdtool-oo-perl--<  "
sudo apt-get -y install librrdtool-oo-perl;
echo "----------------------------------"
echo "  >------- rrdtool ------------<  "
sudo apt-get -y install rrdtool;
echo "----------------------------------"
echo "  >------- RPI.GPIO -----------<  "
sudo apt-get -y install RPI.GPIO;
echo "----------------------------------"
currentuser=$(users)
echo "  >------- set user:${currentuser} dialout <  "
sudo adduser ${currentuser} dialout
echo "  >------- git ----------------<  "
which git >/dev/null
if [ $? -eq 0 ]; then
 echo " -> git available";
else
 echo "git NOT available -> installation started";
 sudo apt-get -y install git;
fi

machine=$(uname -m)
if expr "${machine}" : '^\(arm\|aarch\)' >/dev/null
  then
    # disable Bluetooth on RaspberryPi
    sudo systemctl disable hciuart >/dev/null
fi
echo "----- pre-setup done -------------"
