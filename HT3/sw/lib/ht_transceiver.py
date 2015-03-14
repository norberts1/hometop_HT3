#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2015 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.7  / Datum 25.02.2015 first release
# Ver:0.1.7.1/ Datum 28.02.2015 'cfg_deviceaddress()' modified
#################################################################

import sys, time
sys.path.append('lib')
import ht_proxy_if

class ctransceiver():
    """

    """
    def __init__(self, clienthandle):
        self._clienthandle=clienthandle
        
    def __del__(self):
        pass
    
    def cfg_mode(self, mode):
        error=None
        # transceiver-mode :  '#',<length>,'!','C',1,int(mode)
        set_transceiver_mode = [0x23,4,0x21,0x43,1,int(mode)]
        try:
           self._clienthandle.write(set_transceiver_mode)
           time.sleep(1)
        except:
            error=str("ctransceiver.cfg_mode();Error;could not write bytes to socket")
        return error

    def cfg_deviceaddress(self, deviceaddress):
        error=None
        # deviceaddress    :  '#',<length>,'!','C',2,int(deviceaddress)
        device_address       = [0x23,4,0x21,0x43,2,int(deviceaddress)]
        try:
           self._clienthandle.write(device_address)
           time.sleep(1)
        except:
            error=str("ctransceiver.cfg_deviceaddress();Error;could not write bytes to socket")
        return error

    def reset(self):
        error=None
        # reset-command :  '#',<length>,'!','M',240
        reset_transceiver = [0x23,3,0x21,0x4D,0xF0]
        try:
           self._clienthandle.write(reset_transceiver)
           time.sleep(1)
        except:
            error=str("ctransceiver.reset();Error;could not write bytes to socket")
        return error
