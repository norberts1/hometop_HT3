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
# Ver:0.1.8  / Datum 28.06.2015 heater circuit (heizkreis-nr) added
# Ver:0.1.9  / Datum 12.05.2016 'request_...'-functions added
#                              EMS+ typed controller-handling added
# Ver:0.1.10 / Datum 10.08.2016 set_ecomode() added
# Ver:0.2    / Datum 29.08.2016 Fkt.doc added, minor debugtext-changes.
#################################################################

import time
import ht_const

__author__ = "junky-zs"
__status__ = "draft"
__version__ = "0.2"
__date__ = "29.08.2016"


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
    """
    """
    def __init__(self, clienthandle, ems_bus=False):
        """
        """
        self._clienthandle = clienthandle
        self._ems_bus = ems_bus

    def __del__(self):
        """
        """
        pass

    def set_betriebsart(self, betriebsart, hcircuit_nr=1, controller_adr=0x10):
        """ set betriebsart with netcom-like commands
             valid parameters are:
              auto,a,au; heizen,h,he; sparen,s,sp; and frost,f,fr
            These commands will set the heater-system to the requested
             working-type.
            As result, the display on regulator (FWxyz) will show 'NC'
            This means 'NetCom-mode'
        """
        error = None
        if self._ems_bus == False:
            betriebswert = 0
            if betriebsart.lower() in ['auto', 'a', 'au']:
                betriebswert = 4
            elif betriebsart.lower() in ['heizen', 'h', 'he']:
                betriebswert = 3
            elif betriebsart.lower() in ['sparen', 's', 'sp']:
                betriebswert = 2
            elif betriebsart.lower() in ['frost', 'f', 'fr']:
                betriebswert = 1
            else:
                return str("cyanetcom.set_betriebsart();Error;wrong input-value:{0}".format(betriebsart))

            # 1. setup value for msgid := 357 - 360
            _offset = ht_const.HT_OFFSET_357_360_OP_MODE_HC
            _id = ht_const.ID357_TEMP_NIVEAU_HC1 - 1 + hcircuit_nr
            error = self.setup_integer_data(setup_value=betriebswert, msg_id=_id, target_deviceadr=controller_adr, msg_offset=_offset)
            time.sleep(2.0)
            if (controller_adr != 0x18):
                error = self.setup_integer_data(setup_value=betriebswert, msg_id=_id, target_deviceadr=0x18, msg_offset=_offset)
                time.sleep(2.0)

            # 2. setup value for msgid := 377 - 380
            _offset = ht_const.HT_OFFSET_377_380_OP_MODE_HC
            _id = ht_const.ID377_CIRCUIT_TYPE_HC1 - 1 + hcircuit_nr
            error = self.setup_integer_data(setup_value=betriebswert, msg_id=_id, target_deviceadr=controller_adr, msg_offset=_offset)
            time.sleep(2.0)
            if (controller_adr != 0x18):
                error = self.setup_integer_data(setup_value=betriebswert, msg_id=_id, target_deviceadr=0x18, msg_offset=_offset)
                time.sleep(2.0)
        else:
            error = str("cyanetcom.set_betriebsart();Error;command only for heatronic-bus available")
        return error

    def set_operation_mode(self, ems_omode, hcircuit_nr=1, controller_adr=0x10):
        """ This function setup the 'operation-mode' (manual / auto)
             The name: 'operation-mode' will be displayed as 'operation status' used
              only in heating-circuit context
        """
        error = None
        if self._ems_bus == True:
            _id = ht_const.ID697_RTSD_HC1 - 1 + hcircuit_nr
            # setup for controller adr 0x10
            error = self.setup_integer_data(setup_value=ems_omode,
                                             msg_id=_id,
                                             target_deviceadr=controller_adr,
                                             msg_offset=ht_const.EMS_OFFSET_RTSP_OPERATION_MODE)
            time.sleep(1)
            if (controller_adr != 0x18):
                # setup for controller adr 0x18 (e.g. CW100 as controller)
                error = self.setup_integer_data(setup_value=ems_omode,
                                             msg_id=_id,
                                             target_deviceadr=0x18,
                                             msg_offset=ht_const.EMS_OFFSET_RTSP_OPERATION_MODE)
                time.sleep(1)
        else:
            error = str("cyanetcom.set_operation_mode();Error;command only for ems-bus available but isn't active;")
        return error


    def _get_msg_offset_4_settemperatur(self, temperatur_mode):
        """ Fkt returns msg_offset as integer used for
            setting temperatur on that assigned mode
        """
        _temperatur_mode = temperatur_mode.lower()
        if self._ems_bus == True:
            _set_temperatur_msg_offset = {
                ht_const.EMS_TEMP_MODE_COMFORT1: ht_const.EMS_OFFSET_COMFORT1_SP,
                ht_const.EMS_TEMP_MODE_COMFORT2: ht_const.EMS_OFFSET_COMFORT2_SP,
                ht_const.EMS_TEMP_MODE_COMFORT3: ht_const.EMS_OFFSET_COMFORT3_SP,
                ht_const.EMS_TEMP_MODE_ECO: ht_const.EMS_OFFSET_ECO_SP,
                ht_const.EMS_TEMP_MODE_TEMPORARY: ht_const.EMS_OFFSET_TEMPORARY_SP,
                ht_const.EMS_TEMP_MODE_MANUAL: ht_const.EMS_OFFSET_MANUAL_SP}
            return int(_set_temperatur_msg_offset.get(_temperatur_mode))
        else:
            _set_temperatur_msg_offset = {
                ht_const.HT_TEMPNIVEAU_FROST: ht_const.HT_OFFSET_357_360_TEMPNIVEAU_FROST,
                ht_const.HT_TEMPNIVEAU_SPAREN: ht_const.HT_OFFSET_357_360_TEMPNIVEAU_SPAREN,
                ht_const.HT_TEMPNIVEAU_NORMAL: ht_const.HT_OFFSET_357_360_TEMPNIVEAU_NORMAL,
                ht_const.HT_TEMPNIVEAU_HEIZEN: ht_const.HT_OFFSET_357_360_TEMPNIVEAU_NORMAL}
            return int(_set_temperatur_msg_offset.get(_temperatur_mode))

    def set_tempniveau(self, T_wanted, temperatur_mode, hcircuit_nr=1, controller_adr=0x10):
        """ set temperatur-niveau for the selected temperatur_mode.
             Keep in mind this temp-niveau is always selected if the
             heater-system program select this temperatur_mode.
        """
        hcircuit_nr = int(hcircuit_nr)
        if int(hcircuit_nr) < 1 or hcircuit_nr > 4:
            hcircuit_nr = 1
        t_wanted_4_htbus = int(T_wanted * 2)

        if self._ems_bus == True:
            # handling for Cxyz - typed controller
            _temperatur_mode = ht_const.EMS_TEMP_MODE_TEMPORARY
            if temperatur_mode.lower() in (ht_const.EMS_TEMP_MODE_COMFORT1,
                                        ht_const.EMS_TEMP_MODE_COMFORT2,
                                        ht_const.EMS_TEMP_MODE_COMFORT3,
                                        ht_const.EMS_TEMP_MODE_ECO,
                                        ht_const.EMS_TEMP_MODE_TEMPORARY,
                                        ht_const.EMS_TEMP_MODE_MANUAL):
                _temperatur_mode = temperatur_mode
            _offset = self._get_msg_offset_4_settemperatur(_temperatur_mode)
            _id = ht_const.ID697_RTSD_HC1 - 1 + hcircuit_nr
            error = self.setup_integer_data(setup_value=t_wanted_4_htbus, msg_id=_id, target_deviceadr=controller_adr, msg_offset=_offset)
            time.sleep(2.0)
            if (controller_adr != 0x18):
                # setup for controller adr 0x18 (CW100 as controller)
                error = self.setup_integer_data(setup_value=t_wanted_4_htbus, msg_id=_id, target_deviceadr=0x18, msg_offset=_offset)
                time.sleep(2.0)
        elif self._ems_bus != True:
            # handling for Fxyz - typed controller
            _temperatur_mode = ht_const.HT_TEMPNIVEAU_NORMAL
            if temperatur_mode.lower() in (ht_const.HT_TEMPNIVEAU_FROST,
                                    ht_const.HT_TEMPNIVEAU_SPAREN,
                                    ht_const.HT_TEMPNIVEAU_NORMAL,
                                    ht_const.HT_TEMPNIVEAU_HEIZEN):
                _temperatur_mode = temperatur_mode
            _offset = self._get_msg_offset_4_settemperatur(_temperatur_mode)
            _id = ht_const.ID357_TEMP_NIVEAU_HC1 - 1 + hcircuit_nr
            error = self.setup_integer_data(setup_value=t_wanted_4_htbus, msg_id=_id, target_deviceadr=controller_adr, msg_offset=_offset)
            time.sleep(2.0)
            if (controller_adr != 0x18):
                # setup for controller adr 0x18 (CW100 as controller)
                error = self.setup_integer_data(setup_value=t_wanted_4_htbus, msg_id=_id, target_deviceadr=0x18, msg_offset=_offset)
                time.sleep(2.0)
        return error

    def set_ecomode(self, eco_mode, hcircuit_nr=1, controller_adr=0x10):
        """ set eco-mode for EMS2 -typed controller Cxyz.
             Values are: 0:=OFF, 1:=HOLD_OUTD, 2:=HOLD_ROOM, 3:=REDUCED
        """
        hcircuit_nr = int(hcircuit_nr)
        if int(hcircuit_nr) < 1 or hcircuit_nr > 4:
            hcircuit_nr = 1

        if self._ems_bus == True:
            _eco_mode = ht_const.EMS_ECO_MODE_HOLD_OUTD
            if eco_mode in (ht_const.EMS_ECO_MODE_OFF,
                            ht_const.EMS_ECO_MODE_HOLD_OUTD,
                            ht_const.EMS_ECO_MODE_HOLD_ROOM,
                            ht_const.EMS_ECO_MODE_REDUCED):
                _eco_mode = eco_mode
            _offset = ht_const.EMS_OFFSET_ECO_MODE
            _id = ht_const.ID697_RTSD_HC1 - 1 + hcircuit_nr
            error = self.setup_integer_data(setup_value=_eco_mode, msg_id=_id, target_deviceadr=controller_adr, msg_offset=_offset)
            time.sleep(2.0)
            if (controller_adr != 0x18):
                # setup for controller adr 0x18 (CW100 as controller)
                error = self.setup_integer_data(setup_value=_eco_mode, msg_id=_id, target_deviceadr=0x18, msg_offset=_offset)
                time.sleep(2.0)
        else:
            error = str("cyanetcom.set_ecomode();Error;command is only for ems-bus available;")
        return error

    def request_heatercircuit_type(self, heater_circuit=1, target_deviceadr=0x10, msg_offset=0, bytes_requested=3):
        """ request heatercircuit details with netcom-like commands
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        #hc1:=0x65, hc2:=0x66, hc3:=0x67 ... for 1. send-msg
        heater_circuit = int(heater_circuit)
        if (heater_circuit < 1 or heater_circuit > 8):
            heater_circuit = 1
        hc_nr = int(0x64+heater_circuit)
        poll_adr = 0x80 | target_deviceadr
        error = None
        try:
            # send 1. netcom-bytes to transceiver
            #  message: 3xy_0_0; where xy := 57 to 64
            data = [poll_adr, 0xff, msg_offset, bytes_requested, 0x00, hc_nr]
            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
############## only for test ##############
##            temptext = ""
##            for x in range (0,len(block)):
##                temptext = temptext+" "+format(block[x],"02x")
##            print("Block:{0}".format(temptext))
###########################################
        except:
            error = str("cyanetcom.request_heatercircuit_details();Error;could not write byte-array(1) to socket")
            return error

        time.sleep(1)
        #hc1:=0x79, hc2:=0x7a, hc3:=0x7b ... for 2. send-msg
            #  message: 3xy_0_0; where xy := 77 to 84
        hc_nr2 = int(0x78 + heater_circuit)
        try:
            # send 2. netcom-bytes to transceiver
            data = [poll_adr, 0xff, msg_offset, bytes_requested, 0x00, hc_nr2]
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_heatercircuit_details();Error;could not write byte-array(2) to socket")
            return error
        time.sleep(1)
        return error

    def request_heatercircuit_operationmode(self, heater_circuit=1, target_deviceadr=0x10):
        """ request operationmode for this heatercircuit with netcom-like commands
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        #hc1:=0x65, hc2:=0x66, hc3:=0x67 ... for 1. send-msg
        heater_circuit = int(heater_circuit)
        if (heater_circuit < 1 or heater_circuit > 8):
            heater_circuit = 1
        hc_nr = int(0x64+heater_circuit)
        poll_adr = 0x80 | target_deviceadr
        error = None
        try:
            # send 1. netcom-bytes to transceiver
            #  message: 3xy_0_0; where xy := 57 to 64 and offset: (0e)hex.
            msg_offset = 0x0e
            data = [poll_adr, 0xff, msg_offset, 0x01, 0x00, hc_nr]
            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_heatercircuit_operationmode();Error;could not write byte-array(1) to socket")
            return error

        time.sleep(1)
        #hc1:=0x79, hc2:=0x7a, hc3:=0x7b ... for 2. send-msg
            #  message: 3xy_0_0; where xy := 77 to 84 and offset: (04)hex.
        hc_nr2 = int(0x78 + heater_circuit)
        try:
            # send 2. netcom-bytes to transceiver
            msg_offset = 0x04
            data = [poll_adr, 0xff, msg_offset, 0x01, 0x00, hc_nr2]
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_heatercircuit_operationmode();Error;could not write byte-array(2) to socket")
            return error

        time.sleep(1)
        return error

    def request_sollist_temperatur(self, heater_circuit=1, target_deviceadr=0x10, bytes_requested=6):
        """ request temperaturniveau for this heatercircuit with netcom-like commands
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        # hc1:=0x6f, hc2:=0x70, hc3:=0x71 ...
        if (heater_circuit < 1 or heater_circuit > 8):
            heater_circuit = 1
        hc_nr = int(0x6e+heater_circuit)
        poll_adr = 0x80 | target_deviceadr
        error = None
        try:
            # send 1. netcom-bytes to transceiver
            #  message: 3xy_0_0; where xy := 67 to 74 and offset: (0e)hex.
            data = [poll_adr, 0xff, 0x00, bytes_requested, 0x00, hc_nr]
            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data)+3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_temperaturniveau();Error;could not write byte-array() to socket")
            return error

        time.sleep(1)
        return error

    def request_temperatur_niveaus(self, heater_circuit=1, target_deviceadr=0x10, bytes_requested=3):
        """ request temperaturniveau for this heatercircuit with netcom-like commands
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        # hc1:=0x65, hc2:=0x66, hc3:=0x67 ...
        if (heater_circuit < 1 or heater_circuit > 8):
            heater_circuit = 1
        hc_nr = int(0x64+heater_circuit)
        poll_adr = 0x80 | target_deviceadr
        msg_offset = 0x0f
        error = None
        try:
            # send 1. netcom-bytes to transceiver
            #  message: 3xy_0_0; where xy := 57 to 64 and offset: (0f)hex.
            data = [poll_adr, 0xff, msg_offset, bytes_requested, 0x00, hc_nr]
            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_temperaturniveau();Error;could not write byte-array() to socket")
            return error

        time.sleep(1)
        return error

    def request_msg_ID677(self, heater_circuit=1, target_deviceadr=0x10, bytes_requested=22, msg_offset=0):
        """ request msg ID677 for this heatercircuit with netcom-like commands
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        if (heater_circuit < 1 or heater_circuit > 8):
            heater_circuit = 1
        if (bytes_requested > 22):
            bytes_requested = 22
        # hc1:=0xA5, hc2:=0xA6, hc3:=0xA7 ...
        hc_nr = int(0xA4 + heater_circuit)
        poll_adr = 0x80 | target_deviceadr
        error = None
        try:
            # send 1. netcom-bytes to transceiver
            #  message: 6xy_0_0; where xy := 77 to 84 and offset: (00)hex.
            data = [poll_adr, 0xff, msg_offset, bytes_requested, 0x01, hc_nr]
            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_msg_ID677();Error;could not write byte-array() to socket")
            return error

        time.sleep(1)
        return error

    def request_error_history(self, target_deviceadr=0x10, msg_offset=0):
        """ request error-history for this heatercircuit with netcom-like commands
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        poll_adr = 0x80 | target_deviceadr
        error = None
        try:
            # send 1. netcom-bytes to transceiver
            #  message: 296_0_0;
            # <source><Target>ff00180028
            data = [poll_adr, 0xff, msg_offset, 0x18, 0x00, 0x28]
            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.request_error_history();Error;could not write byte-array() to socket")
            return error

        time.sleep(1)
        return error

    def request_data(self, msg_id=677, target_deviceadr=0x10, msg_offset=0, bytes_requested=1):
        """ request data from target using offset and amount of bytes
             The response is send from the device to the requester.
             Receiving is not done in this function and must be done
             in an external thread.
        """
        if msg_id > 255:
            # calculate high,low byte from msg_id
            Lowbyte = int(msg_id % 256)
            Highbyte = int(msg_id / 256)
            if Highbyte > 0:
                Highbyte -= 1
        if (msg_offset > 21):
            msg_offset = 21
        if (msg_offset + bytes_requested > 22):
            bytes_requested = 1
        poll_adr = 0x80 | target_deviceadr
        error = None
        try:
            # send to transceiver
            if msg_id > 255:
                data = [poll_adr, 0xff, msg_offset, bytes_requested, Highbyte, Lowbyte]
            else:
                data = [poll_adr, msg_id, msg_offset, bytes_requested]

            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
#zs#test#
#            for byte in block:
#                print("byte:" + format(byte,"02x"))
        except:
            error = str("cyanetcom.request_data();Error;could not write byte-array() to socket")
            return error
        time.sleep(1)
        return error

    def setup_integer_data(self, setup_value, msg_id=697, target_deviceadr=0x10, msg_offset=0):
        """ setup integer data to target using offset and value
        """
        if msg_id > 255:
            # calculate high,low byte from msg_id
            Lowbyte = int(msg_id % 256)
            Highbyte = int(msg_id / 256)
            if Highbyte > 0:
                Highbyte -= 1
        if (msg_offset > 21):
            msg_offset = 21
        error = None
        try:
            # send to transceiver
            if msg_id > 255:
                data = [target_deviceadr, 0xff, msg_offset, Highbyte, Lowbyte, int(setup_value)]
            else:
                data = [target_deviceadr, msg_id, msg_offset, int(setup_value)]

            # header   :  '#',<length>,'!','S',0x11
            header = [0x23, (len(data) + 3), 0x21, 0x53, 0x11]
            block = header + data
            self._clienthandle.write(block)
        except:
            error = str("cyanetcom.setup_integer_data();Error;could not write byte-array() to socket")
            return error

        time.sleep(1)
        return error

    def setup_temperatur_data(self, setup_value, msg_id=697, target_deviceadr=0x10, msg_offset=0):
        """ setup data to target using offset and value
        """
        # dobble the value
        setup_value *= 2
        error = None
        try:
            error = self.setup_integer_data(int(setup_value), msg_id, target_deviceadr, msg_offset)
        except:
            error = str("cyanetcom.setup_data();Error;could not write byte-array() to socket")
            return error
        time.sleep(1)
        return error
