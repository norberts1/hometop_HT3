#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2013 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.5  / Datum 25.05.2014
#################################################################

import sys, time
sys.path.append('lib')
import ht3_worker

configurationfilename='./etc/config/HT3_db_cfg.xml'
##### activate the valid devicename for the HT3-Port
#
deviceport="/dev/ttyAMA0"
# deviceport="/dev/ttyUSB0"
# deviceport="/dev/ttyUSB1"
#####

HT3_logger=ht3_worker.ht3_cworker(configurationfilename, deviceport, False, False)
HT3_logger.run()
while True:
    time.sleep(2)
