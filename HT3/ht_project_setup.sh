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
 # rev.: 0.2 date: 2023-03-17
 # rev.: 0.3 date: 2023-03-22 export 'LANGUGAGE' added for perl-install.
 # 
 #################################################################
 #                                                               #
 # setup for ht-project                                          #
 #                                                               #
 #################################################################

echo "=================================="
echo "+==== Checking for user:pi   ====+"
currentuser=$(whoami)
if expr "${currentuser}" : '^\(pi\)' >/dev/null
  then
    echo " >--- installation as default user:pi  <---"
  else
    echo " >--- installation as user:${currentuser}  <---"
    echo " >---  Manually modification of service-scripts required for user: ${currentuser} <---"
fi

# export language environment if not set
if [ ! ${LC_ALL} ]; then
  if [ ${LANG} ]; then
    LC_ALL=$LANG
    LANGUAGE=$LANG
  else
    LC_ALL=en_GB.UTF-8
    LANGUAGE=en_GB.UTF-8
  fi
  export LC_ALL
  export LANGUAGE
fi

echo "+==== Setup OS               ====+"
 ./__pre_setup.sh
if [ $? -ne 0 ]; then
  echo "!!! Error in 'pre_setup.sh' occurred, check outputs !!!"
  exit 1
fi
 
echo "+==== Load project           ====+"
# get latest project from github.com
if [ -d /tmp/hometop ]; then
 sudo rm -rf /tmp/hometop;
fi
git clone https://github.com/norberts1/hometop_HT3.git /tmp/hometop

 # remove old saved HT3 if available
if [ -d ~/.hometop/old_saved/HT3 ]; then
 sudo rm -rf ~/.hometop/old_saved/HT3; 
fi

# save current project-folder if available and update requested
clone_ht_release=$(grep -e VERSION /tmp/hometop/HT3/sw/lib/ht_release.py) >/dev/null
if [ -d ~/HT3 ]; then
 # compare release-infos between clone and current release
 sdiff -s /tmp/hometop/HT3/sw/lib/ht_release.py ~/HT3/sw/lib/ht_release.py >/dev/null
 if [ $? -eq 0 ]; then
   echo
   echo "------------------------------------------------"
   echo " Release: ${clone_ht_release} already installed."
   echo "  Installation anyway (y/n) ?"
   read installation_requested
   echo
   if [ "$installation_requested" = "n" ]; then
     echo " No Installation requested, revision: ${clone_ht_release} already installed"
     exit 0
   fi
 fi

 mkdir -p ~/.hometop/old_saved/HT3/sw/etc
 mkdir -p ~/.hometop/old_saved/HT3/sw/lib
 mkdir -p ~/.hometop/old_saved/HT3/sw/var/log
 mkdir -p ~/.hometop/old_saved/HT3/docu
 mkdir -p ~/.hometop/old_saved/HT3/hw
 mv ~/HT3/sw/etc ~/.hometop/old_saved/HT3/sw;
 mv ~/HT3/sw/lib ~/.hometop/old_saved/HT3/sw;
 mv ~/HT3/sw/var/log ~/.hometop/old_saved/HT3/sw/var;
 mv ~/HT3/docu ~/.hometop/old_saved/HT3;
 mv ~/HT3/hw ~/.hometop/old_saved/HT3;
fi

echo "----------------------------------------------"
echo " Installation of revision: ${clone_ht_release}"

# copy it to target-folder, if already available then update it
cp -a -u /tmp/hometop/HT3 ~/
echo "----------------------------------------------"
echo -n "is mqtt-interface required (y/n) ?"
read mqtt_required
echo
if [ "$mqtt_required" = "y" ]; then
 ./__mqtt_setup.sh
fi

currentuser=$(whoami)
if expr "${currentuser}" : '^\(pi\)' >/dev/null
  then
    ./__post_setup.sh
  else
    echo " >--- Setup stopped, currently NOT default user:pi                                <---"
    echo " >---  Manually modification of service-scripts required for user: ${currentuser} <---"
    echo " <---  after modification call script: './__post_setup.sh' and reboot system      <---"
    exit 1
fi
echo "---- ht_project setup done -------"
echo "=================================="
echo " --- Now, reboot required !! ---  "
echo " >--- call: sudo reboot -------<  "
