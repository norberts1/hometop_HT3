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
#################################################################

import time

__author__  = "Norbert S <junky-zs@gmx.de>"
__status__  = "draft"
__version__ = "0.1.7"
__date__    = "25 February 2015"


#################################################################
# class: yet another netcom  -> yanetcom                        #
#                                                               #
#  This class supports you with methods used for heater-setup   #
#  The setup is only possible, if you are using the hardware    #
#  called: ht_transceiver.                                      #
#  The boards:ht_piduino and ht_pitiny are ht_transceivers,     #
#  have the same functionality and fitt on the RaspberryPi B.   #
#                                                               #
#  If you have problems to setup your heater-system let me know.#
#  Send me an E-Mail (see above) and perhaps a logfile so I     #
#  can support you with more informations and perhaps updated   #
#  software.                                                    #
#  I'm using heater-system 'CSW' with 'FW100', 'ISM1' and 'FB10'#
#  If your system is different, perhaps the required handling   #
#  is a bit different.                                          #
#  On problems give me also same informations about your        #
#  heater-system.                                               #
#################################################################
class cyanetcom():
    def __init__(self, clienthandle):
        self._clienthandle=clienthandle
        
    def __del__(self):
        pass

    def set_betriebsart(self, betriebsart, fernbedienung=False):
        """ set betriebsart with netcom-like commands
             valid parameters are:
              auto,a,au; heizen,h,he; sparen,s,sp; and frost,f,fr
            These commands will set the heater-system to the requested
             working-type.
            As result, the display on regulator (FWxyz) will show 'NC'
            This means 'NetCom-mode'
        """
        betriebswert=0
        error=None
        if   betriebsart.lower() in ['auto','a','au']:
            betriebswert=4
        elif betriebsart.lower() in ['heizen','h','he']:
            betriebswert=3
        elif betriebsart.lower() in ['sparen','s','sp']:
            betriebswert=2
        elif betriebsart.lower() in ['frost','f','fr']:
            betriebswert=1
        else:
            return str("cyanc.set_betriebsart();Error;wrong input-value:{0}".format(betriebsart))

        try:
            # send 1. netcom-bytes to transceiver
            data  = [0x10,0xff,0x0e,0x00,0x65,betriebswert]
            # header   :  '#',<length>,'!','S',0x11
            header= [0x23,(len(data)+3),0x21,0x53,0x11]
            block=header+data
            self._clienthandle.write(block)
        except:
            error=str("cyanc.set_betriebsart();Error;could not write byte-array(1) to socket")
            return error
        
        time.sleep(1.0)
        try:
            # send 2. netcom-bytes to transceiver
            data  = [0x10,0xff,0x04,0x00,0x79,betriebswert]
            block=header+data
            self._clienthandle.write(block)
        except:
            error=str("cyanc.set_betriebsart();Error;could not write byte-array(2) to socket")
            return error
        
        time.sleep(1.0)
        #if remote-sensor (FB10/FB100) is available then send information to them
        if fernbedienung:
            try:
                # send 3. netcom-bytes to transceiver
                data  = [0x18,0xff,0x0e,0x00,0x65,betriebswert]
                header= [0x23,(len(data)+3),0x21,0x53,0x11]
                block=header+data
                self._clienthandle.write(block)
            except:
                error=str("cyanc.set_betriebsart();Error;could not write byte-array(3) to socket")
                return error
            
            time.sleep(1.0)
            try:
                # send 4. netcom-bytes to transceiver
                data  = [0x18,0xff,0x04,0x00,0x79,betriebswert]
                block=header+data
                self._clienthandle.write(block)
            except:
                error=str("cyanc.set_betriebsart();Error;could not write byte-array(4) to socket")
            time.sleep(1.0)
            
        return error

    def set_tempniveau(self, T_soll, fernbedienung=False):
        """ set temperatur-niveau with netcom-like commands
             This temperatur-niveau is currently set for
             working-type 'heizen'.
             Keep in mind this temp-niveau is always selected if the
             heater-system switches back to 'auto' or 'heating'-mode
        """
        tsoll=int(T_soll*2)
        error=None
        try:
            # send 1. netcom-bytes to transceiver
            data  = [0x10,0xff,0x11,0x00,0x65,tsoll]
            # header   :  '#',<length>,'!','S',0x11
            header= [0x23,(len(data)+3),0x21,0x53,0x11]
            block=header+data
            self._clienthandle.write(block)
        except:
            error=str("cyanc.set_tempniveau();Error;could not write byte-array(1) to socket")
            return error
        
        time.sleep(1.0)
        try:
            # send 2. netcom-bytes to transceiver
            data  = [0x10,0xff,0x07,0x00,0x79,tsoll]
            block=header+data
            self._clienthandle.write(block)
        except:
            error=str("cyanc.set_tempniveau();Error;could not write byte-array(2) to socket")
            return error

        time.sleep(1.0)
        #if remote-sensor (FB10/FB100) is available then send information to them
        if fernbedienung:
            try:
                # send 3. netcom-bytes to transceiver
                data  = [0x18,0xff,0x11,0x00,0x65,tsoll]
                header= [0x23,(len(data)+3),0x21,0x53,0x11]
                block=header+data
                self._clienthandle.write(block)
            except:
                error=str("cyanc.set_tempniveau();Error;could not write byte-array(3) to socket")
                return error
            
            time.sleep(1.0)
            try:
                # send 4. netcom-bytes to transceiver
                data  = [0x18,0xff,0x07,0x00,0x79,tsoll]
                block=header+data
                self._clienthandle.write(block)
                time.sleep(1.0)
            except:
                error=str("cyanc.set_tempniveau();Error;could not write byte-array(4) to socket")
            time.sleep(1.0)
            
        return error
