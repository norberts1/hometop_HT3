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
# Ver:0.1.8  / Datum 07.02.2016 new modul based on:
#                                 ht3_dispatch.py Ver:0.1.7.1/ Datum 04.03.2015
#                               and
#                                 ht3_decode.py   Ver:0.1.7.1/ Datum 04.03.2015
#                               additonal modifications are:
#                                'new telegram 88 00 2a 00' added (TR-10F)
#                                'new telegram 90 08 1a 00' added (FW/FR1x0)
#                                'new telegram 88 10 16 00' added (heater-details)
#                                 message:88001800 with length:=31 or 33
#                                 message:9000ff00 with length:=29 added
#                                'IPM_LastschaltmodulMsg' buscoding assigned to a0...af
#                                 message:9000ff00 with length:=29 and 32 Byte added
#                                HeizkreisMsg_ID677_max33byte added for CWxyz handling
#                                Heating-circuit assignment corrected (6F...72).
# Ver:0.1.8.1/ Datum 10.02.2016 Methode: HeizkreisMsg_ID677_max33byte()
#                                 'Tsoll_HK'      assigned to Byte12
#                                 'Vbetriebs_art' assigned to Byte27
# Ver:0.1.8.2/ Datum 22.02.2016 'IPM_LastschaltmodulWWModeMsg()'.
#                                 fix for wrong msg-detection: 'a1 00 34 00'
#                               'IPM_LastschaltmodulMsg()' fixed wrong HK-circuit assignment
# Ver:0.1.9  / Datum 27.04.2016 'HeizkreisMsg_ID677_max33byte()' corrected.
#                               'msg_88002a00()' betriebsart assignment deleted
#                               'HeizkreisMsg_FW100_200_xybyte()' entfaellt.
# Ver:0.1.10 / Datum 22.08.2016 Redesign of modul for MsgID-messageshandling.
#                               'SolarMsg()' modified for msgID866 and
#                               for msgID910
#                               Display- and cause-code added for error-reports
#                               'SolarMsg()' corrected
#                               message-ID handling added
#                               "Vbetriebs_art" replaced with "Voperation_status"
#                               Heater active time changed from minutes to hours.
# Ver:0.2    / Datum 29.08.2016 Fkt.doc added, minor debugtext-changes.
# Ver:0.2.2  / Datum 14.10.2016 CW100:=157 added on MsgID 2.
#                               no decoding of 'T_Soll' anymore at msgID:=53.
#                               'msgID_259_Solar()' modified, 3-bytes for solarpump-runtime.
#                               'msgID_51_DomesticHotWater()' added.
#                               'msgID_296_ErrorMsg()' added.
#                               'msgID_188_Hybrid()' corrected.
# Ver:0.2.3  / Datum 17.01.2017 'msgID_52_DomesticHotWater()' corrected.
#                               MsgID:24 for device:(10)hex added, see:
#                    https://www.mikrocontroller.net/topic/324673#4864801
# Ver:0.3    / Datum 19.06.2017 now debug-output in _search_4_transceiver_message().
#                               controller- and bus-type handling added.
# Ver:0.3.1  / Datum 18.01.2019 modified 'deviceadr_2msgid_blacklist[]'
#                               modified msgID_22_Heaterdevice()
#                               msgID_26_HeatingCircuit_HK1() updated and renamed
#                               msgID_30_T_HydraulischeWeiche() THydr.Device added
#                               msgID_35_HydraulischeWeiche() updated with hc_pump
#                               msgID_51_DomesticHotWater() saving data on target:= 0 only
#                               msgID_596_HeatingCircuit() added
#                               msgID_597_HeatingCircuit() added
#                               msgID_697_704_HeatingCircuit() Tsoll_HK
#                               msgID_727_734_HeatingCircuit() added
#                               msgID_737_744_HeatingCircuit() added
#                               msgID_747_754_HeatingCircuit() Frostdanger added
#                               _IsRequestCall() and _RequestCall() added
#                               msgID_569_HeatingCircuit() added
#                               msgID_52_DomesticHotWater() modified for tempsensor failure detection
#                               msgID_30_T_HydraulischeWeiche() modified for 'ch_Thdrylic_switch'
#                                using logitem HG:V_spare2.
#                               msgID_25_Heaterdevice() 'ch_Thdrylic_switch' (V_spare2) added.
#                               update of display errorcode-handling.
#                               modified 'msgID_260_Solar()', SO:V_spare_1 & SO:V_spare_2 used now.
#                               SO:'V_ertrag_sum_calc' used now for SO:'Ertrag Summe'
#                               msgID_52_DomesticHotWater() storing data only if valid.
#################################################################

import serial
import data
import db_sqlite
import ht_utils
import ht_const
import ht_proxy_if

__author__ = "junky-zs"
__status__ = "draft"
__version__ = "0.3.1"
__date__ = "18.01.2019"


class cht_decode(ht_utils.cht_utils):
    """
        class cht_decode for decoding heatronic heater-messages.
    """
    oldcrc_8800bc = 0
    def __init__(self, gdata, logger=None):
        ht_utils.cht_utils.__init__(self)
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging = ht_utils.clog.create_logfile(self, logfilepath="./cht_decode.log", loggertag="cht_decode")
            else:
                self._logging = logger
        except:
            errorstr = "cht_decode();Error;could not create logfile"
            print(errorstr)
            raise EnvironmentError(errorstr)

        #check first the parameter
        if not isinstance(gdata, data.cdata):
            errorstr = 'cht_decode();TypeError;Parameter "gdata" has wrong type'
            self._logging.critical(errorstr)
            raise TypeError(errorstr)

        self.__info_datum = "--.--.----"
        self.__info_zeit = "--:--:--"
        # save data-object
        self.__gdata = gdata
        # setup data to already available logging-object
        self.__gdata.setlogger(self._logging)
        # set default-values HG
        self.__gdata.update("HG", "Tvorlauf_soll", 0)
        self.__gdata.update("HG", "Tvorlauf_ist", 0.0)
        self.__gdata.update("HG", "Truecklauf", 0.0)
        self.__gdata.update("HG", "Tmischer", 0.0)
        self.__gdata.update("HG", "Vmodus", 0)
        self.__gdata.update("HG", "Vbrenner_motor", 0)
        self.__gdata.update("HG", "Vbrenner_flamme", 0)
        self.__gdata.update("HG", "Vleistung", 0)
        self.__gdata.update("HG", "Vheizungs_pumpe", 0)
        self.__gdata.update("HG", "Vspeicher_pumpe", 0)
        self.__gdata.update("HG", "Vzirkula_pumpe", 0)
        self.__gdata.update("HG", "V_spare1", 0)
        self.__gdata.update("HG", "V_spare2", 0)
        self.__gdata.update("HK1", "V_spare1", 0)
        self.__gdata.update("HK1", "V_spare2", 0)
        self.__gdata.update("HK2", "V_spare1", 0)
        self.__gdata.update("HK2", "V_spare2", 0)
        self.__gdata.update("HK3", "V_spare1", 0)
        self.__gdata.update("HK3", "V_spare2", 0)
        self.__gdata.update("HK4", "V_spare1", 0)
        self.__gdata.update("HK4", "V_spare2", 0)
        self.__gdata.update("WW", "V_WWdesinfekt", 0)
        self.__gdata.update("WW", "V_WWeinmalladung", 0)
        self.__gdata.update("WW", "V_WWdesinfekt", 0)
        self.__gdata.update("WW", "V_WWerzeugung", 0)
        self.__gdata.update("WW", "V_WWnachladung", 0)
        self.__gdata.update("WW", "V_WWtemp_OK", 0)
        self.__gdata.update("WW", "V_ladepumpe", 0)
        self.__gdata.update("WW", "V_zirkula_pumpe", 0)
        self.__gdata.update("WW", "V_spare1", 0)
        self.__gdata.update("WW", "V_spare2", 0)

        self.__gdata.update("SO", "Vspeicher_voll", 0)
        self.__gdata.update("SO", "Vkollektor_aus", 0)
        self.__gdata.update("SO", "V_spare1", 0)
        self.__gdata.update("SO", "V_spare2", 0)
        self.__gdata.update("SO", "Vsolar_pumpe", 0)

        self.__currentHK_nickname = "HK1"

    def __IsTempInRange(self, tempvalue, maxvalue=300.0, minvalue=-50.0):
        """
            returns True if 'temperaturvalue' is in physical range, else False.
        """
        return True if (float(tempvalue) < maxvalue and float(tempvalue) > minvalue) else False

    def __Check4MaxValue(self, nickname, item, value):
        """
            returns the 'value' itself, if it is less then maxvalue defined in configuration,
             else the maxvalue from configuration.
        """
        if self.__gdata.maxvalue(nickname, item) != None:
            if value > self.__gdata.maxvalue(nickname, item):
                return self.__gdata.defaultvalue(nickname, item)
            else:
                return value
        else:
            return value

    def __DeviceIsModem(self, device_address):
        """
            returns True if the device-address in defined for 'modems', else False.
        """
        rtnvalue = False
        if (device_address & 0x7f) in [0x0a, 0x0b, 0x0c, 0x0d, 0x48]:
            rtnvalue = True
        return rtnvalue

    def GetMessageID(self, payloadheader):
        """
            returns the messageID for the payload
             decoded from the first bytes of the payload.
             return-value is a tuple of: (msgid, offset)
        """
        msgid = 0
        ems2_byte = 0
        if len(payloadheader) > 7:
            # Is EMS-typed message ?
            if payloadheader[2] >= 0xf0:
                ems2_byte = int(payloadheader[2] + 1)
                if (payloadheader[5]) == 0xff:
                    # special case handling for byte5
                    # EMS msg.; take Byte6 as multiplicator and add Byte7
                    # (byte6 + 1)*256 + byte7
                    msgid = ems2_byte + int(payloadheader[6]) * 256 + int(payloadheader[7])
                else:
                    # EMS msg.; take Byte5 as multiplicator and add Byte6
                    # (byte5 + 1)*256 + byte6
                    msgid = ems2_byte + int(payloadheader[5]) * 256 + int(payloadheader[6])
                    # Is message-request forced ?
                    if payloadheader[1] & 0x80:
                        # msgid forced to zero
                        msgid = 0
                    else:
                        if payloadheader[4] < 0xf0:
                            # EMS msg.; take Byte4 as multiplicator and add Byte5
                            # (byte4 + 1)*256 + byte5
                            msgid = ems2_byte + int(payloadheader[4]) * 256 + int(payloadheader[5])
            else:
                # normal msg.; take Byte:2 as msg-type
                msgid = int(payloadheader[2])
            #  take Byte 3 as msg-offset
        return (msgid, payloadheader[3])

    def _IsRequestCall(self, buffer):
        """
            returns True if requestflag is set on TargetDevice-Byte, else False
        """
        # if request-flag set, then make only hexdump
        if (buffer[1] & 0x80) > 0:
            return True
        else:
            return False

    def _RequestCall(self, msgtuple, buffer, length):
        """
            hexdump is created and returns (nickname,values) -tuple
        """
        (msgid, offset) = msgtuple
        nickname = "DT"
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, "req")
        for buffer_index in range(0, length):
            temptext += format(buffer[buffer_index], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_2_BusInfo(self, msgtuple, buffer, length):
        """
            decoding of msgID:2 -> Businformation.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:bus:".format(msgid, offset)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 4
        request = True if (buffer[1] & 0x80) else False
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            sourcedevicehex = format((buffer[0] & 0x7f), "02x")
            targetdevicehex = format((buffer[1] & 0x7f), "02x")

            if request == True:
                debugstr += ";Bus-Request  Source:{0}(h) to Target:{1}(h)".format(sourcedevicehex, targetdevicehex)

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                if request == False:
                    # read values from buffer and assign them
                    if raw_index == 4 and msg_bytecount >= 1:
                        i_busteilnehmer = buffer[buffer_index]
                        if i_busteilnehmer == 78:
                            str_busteilnehmer = "M400"
                        elif i_busteilnehmer == 79:
                            str_busteilnehmer = "M100"
                        elif i_busteilnehmer == 80:
                            str_busteilnehmer = "M200"
                        elif i_busteilnehmer == 95:
                            str_busteilnehmer = "Heatronic3"
                        elif i_busteilnehmer == 100:
                            str_busteilnehmer = "IPM1"
                        elif i_busteilnehmer == 101:
                            str_busteilnehmer = "ISM1"
                        elif i_busteilnehmer == 102:
                            str_busteilnehmer = "IPM2"
                        elif i_busteilnehmer == 103:
                            str_busteilnehmer = "ISM2"
                        elif i_busteilnehmer == 104:
                            str_busteilnehmer = "IUM1"
                        elif i_busteilnehmer == 105:
                            str_busteilnehmer = "FW100"
                        elif i_busteilnehmer == 106:
                            str_busteilnehmer = "FW200"
                        elif i_busteilnehmer == 107:
                            str_busteilnehmer = "FR100"
                        elif i_busteilnehmer == 108:
                            str_busteilnehmer = "FR110"
                        elif i_busteilnehmer == 109:
                            str_busteilnehmer = "FB10"
                        elif i_busteilnehmer == 110:
                            str_busteilnehmer = "FB100"
                        elif i_busteilnehmer == 111:
                            str_busteilnehmer = "FR10"
                        elif i_busteilnehmer == 116:
                            str_busteilnehmer = "FW500"
                        elif i_busteilnehmer == 147:
                            str_busteilnehmer = "FR50"
                        elif i_busteilnehmer == 157:
                            str_busteilnehmer = "CW100"
                        elif i_busteilnehmer == 189:
                            str_busteilnehmer = "Modem(MBLAN/NetCom)"
                        elif i_busteilnehmer == 191:
                            str_busteilnehmer = "FR120"
                        elif i_busteilnehmer == 192:
                            str_busteilnehmer = "FW120"
                        else:
                            str_busteilnehmer = ""

                        if len(str_busteilnehmer) == 0:
                            str_busteilnehmer = str(i_busteilnehmer)
                        # setup found controller if response is from controller (source: 90h)
                        if (buffer[0] & 0x7f) == 0x10 or (buffer[0] & 0x7f) == 0x18:
                            self.__gdata.controller_type(str_busteilnehmer)

                        if (buffer[0] & 0x7f) == 0x08:
                            self.__gdata.bus_type(str_busteilnehmer)

                        debugstr += ";Bus-Response Source:{0}(h) to Target:{1}(h)\n".format(sourcedevicehex, targetdevicehex)
                        debugstr += " ;1.Busteilnehmer:{0};Typ:{1}".format(i_busteilnehmer, str_busteilnehmer)

                    if raw_index == 5 and msg_bytecount >= 1:
                        i_softwarefamilie = buffer[buffer_index]
                        debugstr += ";Softwarefamilie:{0}".format(i_softwarefamilie)

                    if raw_index == 6 and msg_bytecount >= 1:
                        i_softwareversion = buffer[buffer_index]
                        debugstr += ";Softwareversion:{0}\n".format(i_softwareversion)

                    if raw_index == 7 and msg_bytecount >= 1:
                        i_busteilnehmer = buffer[buffer_index]
                        debugstr += " ;2.Busteilnehmer:{0}".format(i_busteilnehmer)

                    if raw_index == 8 and msg_bytecount >= 1:
                        i_major = buffer[buffer_index]
                        debugstr += ";2.Major Version:{0}".format(i_major)

                    if raw_index == 9 and msg_bytecount >= 1:
                        i_minor = buffer[buffer_index]
                        debugstr += ";2.Minor Version:{0}\n".format(i_minor)

                    if raw_index == 10 and msg_bytecount >= 1:
                        i_busteilnehmer = buffer[buffer_index]
                        debugstr += " ;3.Busteilnehmer:{0}".format(i_busteilnehmer)

                    if raw_index == 11 and msg_bytecount >= 1:
                        i_major = buffer[buffer_index]
                        debugstr += ";3.Major Version:{0}".format(i_major)

                    if raw_index == 12 and msg_bytecount >= 1:
                        i_minor = buffer[buffer_index]
                        debugstr += ";3.Minor Version:{0}\n".format(i_minor)

                    if raw_index == 13 and msg_bytecount >= 1:
                        i_marke = buffer[buffer_index]
                        if i_marke == 0:
                            strmarke = "None"
                        elif i_marke == 2:
                            strmarke = "Junkers"
                        elif i_marke == 3:
                            strmarke = "Buderus"
                        else:
                            strmarke = str(i_marke)
                        debugstr += " ;Markenzeichen:{0}".format(strmarke)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_5_SystemInfo(self, msgtuple, buffer, length):
        """
            decoding of msgID:5 -> Systeminformation.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:sys:".format(msgid, offset)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    # ## Date / Time ##
    def msgID_6_datetime(self, msgtuple, buffer, length):
        """
            decoding of msgID:6 -> Daten and Time.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 7:
                    iyear = int(buffer[buffer_index] + 2000)
                    imonth = int(buffer[buffer_index + 1])
                    ihour = int(buffer[buffer_index + 2])
                    iday = int(buffer[buffer_index + 3])
                    iminute = int(buffer[buffer_index + 4])
                    isecond = int(buffer[buffer_index + 5])
                    idayofweek = int(buffer[buffer_index + 6])

                    self.__info_datum = """{day:02}.{month:02}.{year:4}""".format(day=iday,
                                                                   month=imonth,
                                                                   year=iyear)
                    self.__info_zeit = """{hour:02}:{minute:02}:{second:02}""".format(hour=ihour,
                                                                        minute=iminute,
                                                                        second=isecond)
                    # update values
                    self.__gdata.update(nickname, "Date", self.__info_datum)
                    self.__gdata.update(nickname, "Time", self.__info_zeit)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            return (nickname, self.__gdata.values(nickname))
        else:
            return ("", None)

    def msgID_7_TokenStati(self, msgtuple, buffer, length):
        """
            decoding of msgID:7 -> Bus-Tokenstatus.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        if self._IsRequestCall(buffer):
            return self._RequestCall(msgtuple, buffer, length)

        temptext = "{0:4}_{1:<2}:".format(msgid, offset)
        # check if source-device-adr | 0x80 := buffer[0]
        if (buffer[0] == 0x88):
            nickname = "HG"
            temptext += nickname + " :"
        else:
            nickname = "DT"
            temptext += "sys:"
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

############################
#   ### Heater Device     ##
############################
    def msgID_22_Heaterdevice(self, msgtuple, buffer, length):
        """
            decoding of msgID:22 -> Heaterdevice message.
        """
        (msgid, offset) = msgtuple
        Sourcedevice = buffer[0]
        Targetdevice = buffer[1]
        TargetdeviceNr = (Targetdevice & 0x7f)
        # if request-flag set, then make only hexdump
        if self._IsRequestCall(buffer):
            return self._RequestCall(msgtuple, buffer, length)

        nickname = "HG"
        self.__currentHK_nickname = nickname

        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}:{2}".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 1:
                    heater_enable = buffer[buffer_index]
                    heater_enable_str="Off"
                    if (heater_enable == 255):
                        heater_enable_str="On"
                    debugstr += ";heat_enable:{0};TargetDevice(dez.):{1}".format(heater_enable_str, Targetdevice)

                if raw_index == 5 and msg_bytecount >= 1:
                    i_heater_maxtempvorlauf = int(buffer[buffer_index])
                    debugstr += ";MaxT_Vorlauf:{0}".format(i_heater_maxtempvorlauf)

                if raw_index == 6 and msg_bytecount >= 1:
                    i_heater_maxpower = int(buffer[buffer_index])
                    debugstr += ";heatmaxp:{0}".format(i_heater_maxpower)

                if raw_index == 7 and msg_bytecount >= 1:
                    i_heat_limit = int(buffer[buffer_index])
                    debugstr += ";heatlimit_enable:{0}".format(i_heat_limit)

                if raw_index == 8 and msg_bytecount >= 1:
                    i_heater_offhysterese = int(buffer[buffer_index])
                    debugstr += ";offhys:{0}".format(i_heater_offhysterese)

                if raw_index == 9 and msg_bytecount >= 1:
                    i_heater_onhysterese = int(buffer[buffer_index])  - 255
                    debugstr += ";offhys:{0}".format(i_heater_onhysterese)

                if raw_index == 10 and msg_bytecount >= 1:
                    i_heater_taktsperre_time = int(buffer[buffer_index])
                    debugstr += ";Time_taktsperre:{0}".format(i_heater_taktsperre_time)

                if raw_index == 11 and msg_bytecount >= 1:
                    i_heater_pumpmodus = int(buffer[buffer_index])
                    debugstr += ";pumpmodus:{0}".format(i_heater_pumpmodus)

                if raw_index == 12 and msg_bytecount >= 1:
                    i_nachlaufzeit_pumpe = int(buffer[buffer_index])
                    debugstr += ";pump_nachlaufzeit:{0}".format(i_nachlaufzeit_pumpe)

                if raw_index == 13 and msg_bytecount >= 1:
                    i_heater_maxpumppower = int(buffer[buffer_index])
                    debugstr += ";pumpmaxpow:{0}".format(i_heater_maxpumppower)

                if raw_index == 14 and msg_bytecount >= 1:
                    i_heater_minpumppower = int(buffer[buffer_index])
                    debugstr += ";pumpminpow:{0}".format(i_heater_minpumppower)

                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_24_Heaterdevice(self, msgtuple, buffer, length):
        """
            decoding of msgID:24 -> Heaterdevice message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            i_tvorlauf_soll = 0
            f_tvorlauf_ist = 0.0
            i_leistung = 0
            i_betriebsmodus = 0
            f_ionisationstrom = 0
            f_tverbrennungsluft = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 1:
                    i_tvorlauf_soll = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Tvorlauf_soll", self.__Check4MaxValue(nickname, "Tvorlauf_soll", i_tvorlauf_soll))

                if raw_index == 5 and msg_bytecount >= 2:
                    f_tvorlauf_ist = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Tvorlauf_ist", self.__Check4MaxValue(nickname, "Tvorlauf_ist", f_tvorlauf_ist))

                if raw_index == 8 and msg_bytecount >= 1:
                    i_leistung = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Vleistung", i_leistung)

                if raw_index == 9 and msg_bytecount >= 1:
                    i_betriebsmodus = int(buffer[buffer_index] & 0x03)
                    self.__gdata.update(nickname, "Vmodus", i_betriebsmodus)

                    # Extract Bitfeld von RAW-Byte 9
                    #   Bitfeld: (Bits von rechts LSB gezaehlt - beginnt mit 1)
                    #
                    #   Bit8: Status Wartungsanforderung    := 0/1
                    #   Bit7: Status blockierender Fehler   := 0/1
                    #   Bit6: Status verriegelnder Fehler   := 0/1
                    #   Bit5: Status Aufheizphase d. HG     := 0/1
                    #   Bit4: Brennerflamme an              := 0/1
                    #   Bit3: Status Servicebetrieb         := 0/1
                    #   Bit2: Warmwasser-Mode deaktiv/aktiv := 0/1
                    #   Bit1: Heizungs  -Mode deaktiv/aktiv := 0/1
                    b_brennerflamme = 1 if bool((buffer[buffer_index] & 0x08)) else 0
                    self.__gdata.update(nickname, "Vbrenner_flamme", b_brennerflamme)

                if raw_index == 10 and msg_bytecount >= 1:
                    # Extract Bitfeld von Byte 10
                    #
                    #   Bitfeld: (Bits von rechts LSB gezaehlt - beginnt mit 1)
                    #   Bit8: Status Waermeanforderung im Test-modus
                    #   Bit7: Status Waermeanforderung
                    #   Bit6: Status WWErkennung
                    #   Bit5: Status interne Waermeanforderung bei WW
                    #   Bit4: Status Waermeanforderung fuer WW bei BArt:=Frost
                    #   Bit3: Status Waermeanforderung bei BArt:=Frost
                    #   Bit2: Status Waermeanforderung am Schalter
                    #   Bit1: Status Waermeanforderung im Heizbetrieb
                    i_statusByte10 = int(buffer[buffer_index])
                    debugstr += ";Byte10:{0}".format(i_statusByte10)

                if raw_index == 11 and msg_bytecount >= 1:
                    # Extract Bitfeld von Byte 11
                    #
                    #   Bitfeld: (Bits von rechts LSB gezaehlt - beginnt mit 1)
                    #   Bit8: Status Zirkulationspumpe Warmwasser
                    #   Bit7: Status des 3-Wege Ventils 1 := Warmwasser
                    #   Bit6: Status Heizungspumpe
                    #   Bit5: Status des Oelvorwaermer (Gas := 0)
                    #   Bit4: Zuendung des Brenners
                    #   Bit3: Status des Luefter;
                    #   Bit2: 2. Brennstufe
                    #   Bit1: 1. Brennstufe; waehrend Verbrennung 1 mit kurzem Vor- und Nachlauf
                    b_brenner = 1 if(buffer[buffer_index] & 0x01) else 0
                    b_heizungspumpe = 1 if(buffer[buffer_index] & 0x20) else 0
                    b_3WegeVentil = 1 if(buffer[buffer_index] & 0x40) else 0
                    b_zirkulationspumpe = 1 if(buffer[buffer_index] & 0x80) else 0
                    self.__gdata.update(nickname, "Vbrenner_motor", b_brenner)
                    self.__gdata.update(nickname, "Vheizungs_pumpe", b_heizungspumpe)
                    self.__gdata.update(nickname, "Vspeicher_pumpe", b_3WegeVentil)
                    self.__gdata.update(nickname, "Vzirkula_pumpe", b_zirkulationspumpe)

                if raw_index == 13 and msg_bytecount >= 2:
                    # current temperatur on storage-cell temp-sensor1
                    f_tmischer = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Tmischer", self.__Check4MaxValue(nickname, "Tmischer", f_tmischer))

                if raw_index == 15 and msg_bytecount >= 2:
                    # current temperatur on storage-cell temp-sensor2
                    f_t2_storagecell = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";T2-buffer:{0}".format(f_t2_storagecell)

                if raw_index == 17 and msg_bytecount >= 2:
                    f_truecklauf = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Truecklauf", self.__Check4MaxValue(nickname, "Truecklauf", f_truecklauf))

                if raw_index == 19 and msg_bytecount >= 2:
                    f_ionisationstrom = float(buffer[19] * 256 + buffer[20]) / 10
                    debugstr += ";I-current:{0}".format(f_ionisationstrom)

                if raw_index == 21 and msg_bytecount >= 1:
                    i_systempressure = int(buffer[buffer_index])
                    debugstr += ";pressure:{0}".format(i_systempressure)

                if raw_index == 22 and msg_bytecount >= 2:
                    displaycode = buffer[buffer_index]*65536 + buffer[buffer_index+1]*256
                    if displaycode > 0:
                        self.__gdata.update(nickname, "V_displaycode", displaycode)

                if raw_index == 24 and msg_bytecount >= 2:
                    causecode = int((buffer[buffer_index] * 256) + buffer[buffer_index + 1])
                    if causecode > 0:
                        self.__gdata.update(nickname, "V_causecode", causecode)

                if raw_index == 26 and msg_bytecount >= 1:
                    i_WWflow = int(buffer[buffer_index])
                    debugstr += ";WW-flow:{0}".format(i_WWflow)

                if raw_index == 27 and msg_bytecount >= 1:
                    # Extract Bitfeld von Byte 10
                    #
                    #   Bitfeld: (Bits von rechts LSB gezaehlt - beginnt mit 1)
                    #   Bit8: Status --
                    #   Bit7: Status --
                    #   Bit6: Status Brenner Relais
                    #   Bit5: Status Zirkulationspumpe
                    #   Bit4: Status Relais im UM
                    #   Bit3: Status Waermepumpe
                    #   Bit2: Status Magnetventil
                    #   Bit1: Status Speicherladepumpe
                    i_statusByte27 = int(buffer[buffer_index])
                    debugstr += ";Byte27:{0}".format(i_statusByte27)

                if raw_index == 28 and msg_bytecount >= 1:
                    # Extract Bitfeld von Byte 10
                    #
                    #   Bitfeld: (Bits von rechts LSB gezaehlt - beginnt mit 1)
                    #   Bit8: Status Tastensprerre
                    #   Bit7: test active
                    #   Bit6: Status heater blocked
                    #   Bit5: Status burner start
                    #   Bit4: Status burner enable
                    #   Bit3: Status burner blocking
                    #   Bit2: Status Schaltmodul UM
                    #   Bit1: Status Fuellfunktion
                    i_statusByte28 = int(buffer[buffer_index])
                    debugstr += ";Byte28:{0}".format(i_statusByte28)

                if raw_index == 29 and msg_bytecount >= 2:
                    f_tverbrennungsluft = float(buffer[29] * 256 + buffer[30]) / 10
                    debugstr += ";TAbgass:{0}".format(f_tverbrennungsluft)

                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_25_Heaterdevice(self, msgtuple, buffer, length):
        """
            decoding of msgID:25 -> Heaterdevice message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            i_betriebtotal_minuten = 0
            i_betriebheizung_minuten = 0
            i_brenner_gesamt_ein = 0
            i_brenner_heizung_ein = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 2:
                    if buffer[buffer_index] != 255:
                        f_tAussen = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    else:
                        f_tAussen = float(255-buffer[buffer_index + 1]) / (-10)
                    self.__gdata.update(nickname, "Taussen", self.__Check4MaxValue(nickname, "Taussen", f_tAussen))

                # Rev.: 0.1.7 https://www.mikrocontroller.net/topic/324673#3970615
                if raw_index == 13 and msg_bytecount >= 1:
                    i_pumpenleistung = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "V_spare1", i_pumpenleistung)

                if raw_index == 14 and msg_bytecount >= 3:
                    i_brenner_gesamt_ein = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                    self.__gdata.update(nickname, "Cbrenner_gesamt", i_brenner_gesamt_ein)

                if raw_index == 17 and msg_bytecount >= 3:
                    i_betriebtotal_minuten = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                    f_betriebtotal_stunden = float(i_betriebtotal_minuten / 60)
                    self.__gdata.update(nickname, "Cbetrieb_gesamt", f_betriebtotal_stunden)

                if raw_index == 20 and msg_bytecount >= 3:
                    i_betriebszeit_2stufe = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                    # not yet written to database, only for debug-purposes
                    debugstr = "{0:4}_{1:<2};betriebszeit_2.Stufe:{2}".format(msgid, offset, i_betriebszeit_2stufe)
                    self._logging.debug(debugstr)

                if raw_index == 23 and msg_bytecount >= 3:
                    i_betriebheizung_minuten = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                    f_betriebheizung_stunden = float(i_betriebheizung_minuten / 60)
                    self.__gdata.update(nickname, "Cbetrieb_heizung", f_betriebheizung_stunden)

                if raw_index == 26 and msg_bytecount >= 3:
                    i_brenner_heizung_ein = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                    self.__gdata.update(nickname, "Cbrenner_heizung", i_brenner_heizung_ein)

                if raw_index == 29 and msg_bytecount >= 2:
                    # TIst an der hydraulischen Weiche
                    f_THydrWeiche = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    if self.__IsTempInRange(f_THydrWeiche):
                        self.__gdata.update(nickname, "V_spare2", self.__Check4MaxValue(nickname, "V_spare2", f_THydrWeiche))
                        # setup flag for Hydraulic Switch available, used in GUI
                        self.__gdata.IsTempSensor_Hydrlic_Switch(True)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_28_Service(self, msgtuple, buffer, length):
        """
            decoding of msgID:28 -> Service message.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:sys:".format(msgid, offset)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_30_T_HydraulischeWeiche(self, msgtuple, buffer, length):
        """
            decoding of msgID:30 -> Temperatur on Hydraulic device.
             This values are send by IPM/MM Powermoduls to heater-controller,
             the assignment is to systempart "HG".
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        self.__currentHK_nickname = nickname

        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}:{2}".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 2:
                    # TIst an der hydraulischen Weiche
                    f_THydrWeiche = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    if self.__IsTempInRange(f_THydrWeiche):
                        self.__gdata.update(nickname, "V_spare2", self.__Check4MaxValue(nickname, "V_spare2", f_THydrWeiche))
                        # setup flag for Hydraulic Switch available, used in GUI
                        self.__gdata.IsTempSensor_Hydrlic_Switch(True)
                    debugstr += ";T_HydraulicDevice:{0}".format(f_THydrWeiche)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            # not yet written to database, only for debug-purposes
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)


    def msgID_35_HydraulischeWeiche(self, msgtuple, buffer, length):
        """
            decoding of msgID:35 -> Hydraulic device message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            pump_running_flag = 0
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 1:
                    # TSoll hinter der hydraulischen Weiche
                    i_tsoll = buffer[buffer_index]
                    debugstr += ";TSoll:{0}".format(i_tsoll)
                # if msg-bytes [5] or [6] are > 0 then hc_pump is running
                if raw_index == 5 and msg_bytecount >= 1:
                    i_leistung_soll = buffer[buffer_index]
                    if i_leistung_soll > 0:
                        pump_running_flag += 1
                    debugstr += ";Leistung:{0}".format(i_leistung_soll)
                if raw_index == 6 and msg_bytecount >= 1:
                    i_drehzahl_pumpe_soll = buffer[buffer_index]
                    if i_drehzahl_pumpe_soll > 0:
                        pump_running_flag += 1
                    debugstr += ";Drehzahl:{0}".format(i_drehzahl_pumpe_soll)
                if raw_index == 8 and msg_bytecount >= 1:
                    i_betriebsart_heizung = buffer[buffer_index]
                    debugstr += ";Betriebsart:{0}".format(i_betriebsart_heizung)
                if raw_index == 9 and msg_bytecount >= 2:
                    i_erweiterter_tsoll = buffer[buffer_index] + buffer[buffer_index + 1]
                    debugstr += ";TSoll_erweitert:{0}".format(i_erweiterter_tsoll)

                raw_index += 1

            if pump_running_flag > 0:
                self.__gdata.update(nickname, "V_spare2", 1)
            else:
                self.__gdata.update(nickname, "V_spare2", 0)

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            # not yet written to database, only for debug-purposes
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_36_Heater_Configuration(self, msgtuple, buffer, length):
        """
            decoding of msgID:36 -> Heaterconfiguration message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_42_Heaterdevice(self, msgtuple, buffer, length):
        """
            decoding of msgID:42 -> Heaterdevice message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_162_DisplayCause(self, msgtuple, buffer, length):
        """
            decoding of msgID:162 -> Display-code message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        for x in range(0, length):
            temptext = temptext + format(buffer[x], "02x") + " "
        first_payload_index = 4
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            displaycode = 0
            causecode = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[x], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 3:
                    # Auswertung display-code
                    displaycode = buffer[buffer_index]*65536 + buffer[buffer_index+1]*256 + buffer[buffer_index+2]
                    self.__gdata.update(nickname, "V_displaycode", displaycode)
                if raw_index == 7 and msg_bytecount >= 2:
                    causecode = buffer[buffer_index] * 256 + buffer[buffer_index + 1]
                    self.__gdata.update(nickname, "V_causecode", causecode)
                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            debugstr = "{0:4}_{1:<2};display:{2};cause:{3}".format(msgid, offset, displaycode, causecode)
            self._logging.debug(debugstr)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_190_DisplayAndCauseCode(self, msgtuple, buffer, length):
        """
            decoding of msgID:190 -> Display- and Cause-code message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:".format(msgid, offset)

        if(buffer[4] == 0x18 or buffer[4] == 0x20):
            # remote controller FBxy/RC | IPM1/2
            nickname = "HK1"
            temptext += nickname + ":"
        elif(buffer[4] == 0x21):
            # IPM1/2
            nickname = "HK2"
            temptext += nickname + ":"
            self.__gdata.heatercircuits_amount(2)
        elif(buffer[4] == 0x22):
            # IPM1/2
            nickname = "HK3"
            temptext += nickname + ":"
            self.__gdata.heatercircuits_amount(3)
        elif(buffer[4] == 0x23):
            # IPM1/2
            nickname = "HK4"
            temptext += nickname + ":"
            self.__gdata.heatercircuits_amount(4)
        elif(buffer[4] == 0x10):
            # main controller Fxyz | Cxyz
            nickname = "HK1"
            temptext += nickname + ":"
        elif(buffer[4] == 0x30):
            # solar controller ISM1/2 | MSxyz ...
            nickname = "SO"
            temptext += nickname + " :"
        else:
            nickname = "DT"
            temptext += "???:"

        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_296_ErrorMsg(self, msgtuple, buffer, length):
        """
            decoding of msgID:296 -> Error message.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:sys:".format(msgid, offset)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

############################
#   ### Heating Circuit   ##
############################
    # ## HeatingCircuit 1 ... 4 supported ##
    def msgID_26_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:26 -> heating circuit 1 message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if buffer[0] == 0x88 or buffer[0] == 0x90 or buffer[0] == 0x98 or buffer[0] == 0xa0:
            nickname = "HK1"
        elif buffer[0] == 0x89 or buffer[0] == 0x99 or buffer[0] == 0xa1:
            nickname = "HK2"
        elif buffer[0] == 0x9a or buffer[0] == 0xa2:
            nickname = "HK3"
        elif buffer[0] == 0x9b or buffer[0] == 0xa3:
            nickname = "HK4"
        else:
            nickname = "HK1"
        self.__currentHK_nickname = nickname

        # If PowerModul in system, then the values are NOT written to database
        IPM_MM_Modul_Flag = False
        if buffer[0] == 0xa0 or buffer[0] == 0xa1 or buffer[0] == 0xa2 or buffer[0] == 0xa3:
            IPM_MM_Modul_Flag = True

        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            pump_running_flag = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                if raw_index == 4 and msg_bytecount >= 1:
                    i_tvorlauf_soll = int(buffer[buffer_index])
                    if (IPM_MM_Modul_Flag == False):
                        self.__gdata.update(nickname, "V_spare1", self.__Check4MaxValue(nickname, "V_spare1", i_tvorlauf_soll))
                # if msg-bytes [5] or [6] are > 0 then hc_pump is running
                if raw_index == 5 and msg_bytecount >= 1:
                    if int(buffer[buffer_index]) > 0:
                        pump_running_flag += 1
                if raw_index == 6 and msg_bytecount >= 1:
                    if int(buffer[buffer_index]) > 0:
                        pump_running_flag += 1

                raw_index += 1

            if (IPM_MM_Modul_Flag == False):
                if pump_running_flag > 0:
                    self.__gdata.update(nickname, "V_spare2", 1)
                else:
                    self.__gdata.update(nickname, "V_spare2", 0)

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_268_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:268 -> heating circuit (1...4) message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if buffer[0] == 0x88 or buffer[0] == 0x98 or buffer[0] == 0xa0:
            nickname = "HK1"
        elif buffer[0] == 0x89 or buffer[0] == 0x99 or buffer[0] == 0xa1:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        elif buffer[0] == 0x9a or buffer[0] == 0xa2:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        elif buffer[0] == 0x9b or buffer[0] == 0xa3:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        else:
            nickname = "HK1"
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                ### Handling for IPM-moduls following:
                if buffer[0] >= 0xa0 and buffer[0] <= 0xa3:
                    if raw_index == 6 and msg_bytecount >= 1:
                        # setup mixerstatus:= mixer available or not
                        i_IPM_Mixerstatus = int(buffer[buffer_index])
                        if (i_IPM_Mixerstatus & 0x01):
                            self.__gdata.UnmixedFlagHK(nickname, True)
                        if (i_IPM_Mixerstatus & 0x02):
                            self.__gdata.UnmixedFlagHK(nickname, False)
                        debugstr += ";status_mixer:{0}".format(i_IPM_Mixerstatus)
                    if raw_index == 7 and msg_bytecount >= 1:
                        # status heating-circuit (bit1(LSBit) - to bit8(MSBit))
                        #  bit1 := status heating-circuit pump in this circuit
                        #  bit2 := status relay for mixermotor
                        #  bit3 := mixervalve closed
                        i_IPM_Byte7 = int(buffer[buffer_index])
                        debugstr += ";status_hcircuit:{0}".format(i_IPM_Byte7)
                    if raw_index == 8 and msg_bytecount >= 1:
                        i_IPM_Mischerstellung = int(buffer[buffer_index])
                        self.__gdata.update(nickname, "VMischerstellung", i_IPM_Mischerstellung)
                        debugstr += ";mixerposition:{0}%".format(i_IPM_Mischerstellung)
                    if raw_index == 9 and msg_bytecount >= 2:
                        f_IPM_VorlaufTemp = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                        if self.__IsTempInRange(f_IPM_VorlaufTemp):
                            self.__gdata.update(nickname, "Tvorlaufmisch_HK", self.__Check4MaxValue(nickname, "Tvorlaufmisch_HK", f_IPM_VorlaufTemp))
                            debugstr += ";IPM Vorlauf:{0}%".format(f_IPM_VorlaufTemp)
                    if raw_index == 11 and msg_bytecount >= 1:
                        i_IPM_SollVorlaufTemp = int(buffer[buffer_index])
                        debugstr += ";IPM Soll:{0}%".format(i_IPM_SollVorlaufTemp)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_357_360_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:357 until 360 -> heating circuit (1...4) message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if msgid == 357:
            nickname = "HK1"
        if msgid == 358:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 359:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 360:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                if raw_index == 20 and msg_bytecount >= 1:
                    i_tempniveau = int(buffer[buffer_index])
                    # values above 3 like 4:='Auto' will be suppressed cause:
                    #  ! no mix between temperatur-niveau and operation-status are allowed !
                    #    bloddy hell of telegramms (with msgID:367) and mixed content.
                    if i_tempniveau < 4:
                        self.__gdata.update(nickname, "Vtempera_niveau", i_tempniveau)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_367_370_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:367 until 370 -> heating circuit (1...4) message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if msgid == 367:
            nickname = "HK1"
        if msgid == 368:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 369:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 370:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "

                if raw_index == 6 and msg_bytecount >= 1:
                    i_tempniveau = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Vtempera_niveau", i_tempniveau)
                    debugstr += ";temperaturniveau:{0}".format(i_tempniveau)

                if raw_index == 7 and msg_bytecount >= 1:
                    i_operationstatus = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Voperation_status", i_operationstatus)
                    debugstr += ";operation_status:{0}".format(i_operationstatus)

                if raw_index == 8 and msg_bytecount >= 2:
                    f_Soll_HK = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    if self.__IsTempInRange(f_Soll_HK):
                        self.__gdata.update(nickname, "Tsoll_HK", f_Soll_HK)
                    debugstr += ";TSoll_HK:{0}".format(f_Soll_HK)

                if raw_index == 10 and msg_bytecount >= 2:
                    f_Ist_HK = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    if self.__IsTempInRange(f_Ist_HK):
                        self.__gdata.update(nickname, "Tist_HK", self.__Check4MaxValue(nickname, "Tist_HK", f_Ist_HK))
                    debugstr += ";TIst_HK:{0}".format(f_Ist_HK)

                if raw_index == 12 and msg_bytecount >= 2:
                    # not stored to database
                    f_Taussen_HK = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";T???_HK:{0}".format(f_Taussen_HK)

                if raw_index == 14 and msg_bytecount >= 1:
                    i_TsolarSupport = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "V_spare1", i_TsolarSupport)
                    debugstr += ";TSolarSupport:{0}".format(i_TsolarSupport)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_NN_unknown(self, msgtuple, buffer, length):
        """
            decoding of msgID:??? -> for message unknown handling.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, "???")
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_596_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:596 -> heating circuit message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}:{2}".format(msgid, offset, nickname)

        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "

        # length > first index + payload-bytes + crc-byte + break-byte
        #  at least there must be 5 payload-bytes for decoding
        if (length > first_payload_index + 6):
            # init values
            raw_index = first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                #  596_0_0 Measured Temp (2 Bytes)
                #  596_2_0 Measured Temp high resolution (2 Bytes)
                #  596_4_0 Valid Flag for temp's

                # check validity at first
                if bool(buffer[first_payload_index + 4]) == True:
                # read values from buffer and assign them
                    if raw_index == 6 and msg_bytecount >= 2:
                        f_Ist_HK = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                        self.__gdata.update(nickname, "Tist_HK", self.__Check4MaxValue(nickname, "Tist_HK", f_Ist_HK))

                        debugstr += ";Tist:{0}".format(f_Ist_HK)
                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            if bool(buffer[first_payload_index + 4]) == True:
                self._logging.debug(debugstr)
            else:
                self._logging.debug(temptext)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)


    def msgID_597_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:597 -> heating circuit message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        Sourcedevice = buffer[0]
        if Sourcedevice == 0xa0:
            nickname = "HK1"
        if Sourcedevice == 0xa1:
            nickname = "HK2"
        if Sourcedevice == 0xa2:
            nickname = "HK3"
        if Sourcedevice == 0xa3:
            nickname = "HK4"
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}:{2}".format(msgid, offset, nickname)

        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "

        # length > first index + crc-byte + break-byte and send to 'all' targetdevices
        if (length > first_payload_index + 2):
            # init values
            raw_index = first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1:
                    i_value = int(buffer[buffer_index])
                    debugstr += ";value:{0}".format(i_value)
                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_615_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:615 -> for drymode status
                615_0_0 -> current status
                615_1_0 -> flow setpoint temperature
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_677_680_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:677 until 680 -> heating circuit (1...4) message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        if msgid == 677:
            nickname = "HK1"
        if msgid == 678:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 679:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 680:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)

        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 2:
                    f_Ist_HK = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Tist_HK", self.__Check4MaxValue(nickname, "Tist_HK", f_Ist_HK))

                if raw_index == 12 and msg_bytecount >= 1:
                    f_Soll_HK = float(buffer[buffer_index] / 2)
                    self.__gdata.update(nickname, "Tsoll_HK", f_Soll_HK)

                if raw_index == 17 and msg_bytecount >= 1:
                    i_tempniveau = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Vtempera_niveau", i_tempniveau)

                if raw_index == 27 and msg_bytecount >= 1:
                    i_operationstatus = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Voperation_status", i_operationstatus)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_697_704_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:697 until 704 -> heating circuit (1...4) message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        Targetdevice = buffer[1]
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        if msgid == 697:
            nickname = "HK1"
        if msgid == 698:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 699:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 700:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)

        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "

        # length > first index + crc-byte + break-byte and send to 'all' targetdevices
        if (length > first_payload_index + 2) and Targetdevice == 0:
            # init values
            raw_index = first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1 and offset in range(1,4):
                    # offset        Temperatur-type
                    #  1            comfort3
                    #  2            comfort2
                    #  3            comfort1
                    #  4            ECO
                    f_Soll = float(buffer[buffer_index]) / 2
                    if self.__IsTempInRange(f_Soll):
                        self.__gdata.update(nickname, "Tsoll_HK", f_Soll)
                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_727_734_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:727 until 730 -> heating circuit (1...4) message.
              Message used with Cxyz-controller types.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        if msgid == 727:
            nickname = "HK1"
        if msgid == 728:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 729:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 730:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1:
                    i_HK_FlowPump = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "V_spare2", i_HK_FlowPump)
                if raw_index == 7 and msg_bytecount >= 1:
                    i_HK_MixerRequest = int(buffer[buffer_index])
                    if (i_HK_MixerRequest > 0):
                        self.__gdata.UnmixedFlagHK(nickname, False)
                if raw_index == 8 and msg_bytecount >= 1:
                    i_IPM_Mischerstellung = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "VMischerstellung", i_IPM_Mischerstellung)
                if raw_index == 9 and msg_bytecount >= 2:
                    f_IPM_VorlaufTemp = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    if self.__IsTempInRange(f_IPM_VorlaufTemp):
                        self.__gdata.update(nickname, "Tvorlaufmisch_HK", self.__Check4MaxValue(nickname, "Tvorlaufmisch_HK", f_IPM_VorlaufTemp))
                if raw_index == 11 and msg_bytecount >= 1:
                    # V-Spare-1 benutzt fuer 'T-Soll (Vorlauf)'
                    i_tvorlauf_soll = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "V_spare1", self.__Check4MaxValue(nickname, "V_spare1", i_tvorlauf_soll))
                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_737_744_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:737 until 740 -> heating circuit (1...4) message.
              Message used with Cxyz-controller types.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        if msgid == 737:
            nickname = "HK1"
        if msgid == 738:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 739:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 740:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}:{2}".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1:
                    i_req_season = int(buffer[buffer_index])
                    debugstr += ";season:{0}".format(i_req_season)
                if raw_index == 7 and msg_bytecount >= 1:
                    i_supply_temp = int(buffer[buffer_index])
                    debugstr += ";supply_T:{0}".format(i_supply_temp)
                if raw_index == 8 and msg_bytecount >= 1:
                    i_req_power = int(buffer[buffer_index])
                    debugstr += ";power:{0}".format(i_req_power)
                if raw_index == 9 and msg_bytecount >= 1:
                    i_fast_mode = int(buffer[buffer_index])
                    debugstr += ";fast_mode:{0}".format(i_fast_mode)
                if raw_index == 10 and msg_bytecount >= 1:
                    i_prio = int(buffer[buffer_index])
                    debugstr += ";Prio:{0}".format(i_prio)
                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_747_754_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:747 until 750 -> heating circuit (1...4) message.
              Message used with Cxyz-controller types.
              (Frostdanger message)
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        if msgid == 747:
            nickname = "HK1"
        if msgid == 748:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 749:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 750:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length):
                temptext += format(buffer[buffer_index], "02x")+" "

            self.__gdata.update(nickname, "hexdump", temptext)
            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_290_RemoteController_FB10(self, msgtuple, buffer, length):
        """
            decoding of msgID:290 -> remote controller FB10 message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        if buffer[0] == 0x98:
            nickname = "HK1"
        elif buffer[0] == 0x99:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        elif buffer[0] == 0x9a:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        elif buffer[0] == 0x9b:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        else:
            nickname = "HK1"

        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_291_RemoteController_FB10(self, msgtuple, buffer, length):
        """
            decoding of msgID:291 -> remote controller FB10 message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if buffer[0] == 0x98:
            nickname = "HK1"
        elif buffer[0] == 0x99:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        elif buffer[0] == 0x9a:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        elif buffer[0] == 0x9b:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        else:
            nickname = "HK1"
        self.__currentHK_nickname = nickname
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 2:
                    f_Steuer_FB = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Tsteuer_FB", self.__Check4MaxValue(nickname, "Tsteuer_FB", f_Steuer_FB))

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_377_380_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:377 until 380 -> heating circuit (1...4) message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        if msgid == 377:
            nickname = "HK1"
        if msgid == 378:
            nickname = "HK2"
            self.__gdata.heatercircuits_amount(2)
        if msgid == 379:
            nickname = "HK3"
            self.__gdata.heatercircuits_amount(3)
        if msgid == 380:
            nickname = "HK4"
            self.__gdata.heatercircuits_amount(4)
        self.__currentHK_nickname = nickname
        systempart_tag = nickname
        device_address = buffer[0] & 0x7f
        if self.__DeviceIsModem(device_address):
            systempart_tag = "mod"
        temptext = "{0:4}_{1:<2}:{2:<3}:".format(msgid, offset, systempart_tag)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1:
                    i_bauart_HK = buffer[buffer_index]
                    debugstr += ";bauart_HK:{0}".format(i_bauart_HK)

                if raw_index == 10 and msg_bytecount >= 1:
                    i_betriebsart_HK = buffer[buffer_index]
                    debugstr += ";betriebsart_HK:{0}".format(i_betriebsart_HK)

                if raw_index == 11 and msg_bytecount >= 1:
                    i_tempniveau_frost = buffer[buffer_index]
                    debugstr += ";Tniveau_frost:{0}".format(i_tempniveau_frost)

                if raw_index == 12 and msg_bytecount >= 1:
                    i_tempniveau_sparen = buffer[buffer_index]
                    debugstr += ";Tniveau_sparen:{0}".format(i_tempniveau_sparen)

                if raw_index == 13 and msg_bytecount >= 1:
                    i_tempniveau_normal = buffer[buffer_index]
                    debugstr += ";Tniveau_normal:{0}".format(i_tempniveau_normal)

                if raw_index == 14 and msg_bytecount >= 1:
                    i_urlaubsprogramm_HK = buffer[buffer_index]
                    debugstr += ";Urlaubsprogr:{0}".format(i_urlaubsprogramm_HK)

                if raw_index == 15 and msg_bytecount >= 1:
                    i_status_optimierung = buffer[buffer_index]
                    debugstr += ";Statusoptimier:{0}".format(i_status_optimierung)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_569_HeatingCircuit(self, msgtuple, buffer, length):
        """
            decoding of msgID:569 message.
        """
        nickname = "HK1"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:<3}:".format(msgid, offset, systempart_tag)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        self._logging.debug(temptext)

        values = self.__gdata.values(nickname)
        return (nickname, values)


    def msgID_188_Hybrid(self, msgtuple, buffer, length):
        """
            decoding of msgID:188 -> hybrid message for mixed heater-systems.
        """
        nickname = "HG"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "

                if raw_index == 4 and msg_bytecount >= 2:
                    Toben_pufferspeicher = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";Toben_puffer:{0}".format(Toben_pufferspeicher)

                if raw_index == 6 and msg_bytecount >= 2:
                    Tunten_pufferspeicher = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";Tunten_puffer:{0}".format(Tunten_pufferspeicher)

                if raw_index == 8 and msg_bytecount >= 2:
                    Tvorlauf_verfluessiger = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";Tvorlauf_verfluessiger:{0}".format(Tvorlauf_verfluessiger)

                if raw_index == 10 and msg_bytecount >= 2:
                    Truecklauf_verfluessiger = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";Truecklauf_verfluessiger:{0}".format(Truecklauf_verfluessiger)

                if raw_index == 12 and msg_bytecount >= 1:
                    i_betriebsstatus_wpumpe = int(buffer[buffer_index] & 0x01)
                    debugstr += ";Betriebsstatus Waermepumpe:{0}".format(i_betriebsstatus_wpumpe)

                if raw_index == 13 and msg_bytecount >= 1:
                    i_betriebsstatus_verdichter = int(buffer[buffer_index] & 0x02)
                    debugstr += ";Betriebsstatus Verdichter:{0}".format(i_betriebsstatus_verdichter)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

############################
#   ### Domestic Hotwater ##
############################

    def msgID_27_DomesticHotWater(self, msgtuple, buffer, length):
        """
            decoding of msgID:27 -> Domestic Hot Water(DHW) message.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 4 and msg_bytecount >= 1:
                    i_Soll = int(buffer[buffer_index])
                    self.__gdata.update(nickname, "Tsoll", self.__Check4MaxValue(nickname, "Tsoll", i_Soll))
                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_51_DomesticHotWater(self, msgtuple, buffer, length):
        """
            decoding of msgID:51 -> Domestic Hot Water(DHW) message.
             see also: https://www.mikrocontroller.net/topic/317004#4716820
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        Targetadress = buffer[1]
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                #saving data only if target-adresse is := 0
                if(Targetadress == 0):
                    # read values from buffer and assign them
                    if raw_index == 4 and msg_bytecount >= 1:
                    # kennzahl bussystem; 8:=EMS, 0:=NN
                        if int(buffer[buffer_index]) == 8:
                            self.__gdata.bus_type("EMS")
                    if raw_index == 6 and msg_bytecount >= 1:
                        i_Soll = int(buffer[buffer_index])
                        self.__gdata.update(nickname, "Tsoll", self.__Check4MaxValue(nickname, "Tsoll", i_Soll))
                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_52_DomesticHotWater(self, msgtuple, buffer, length):
        """
            decoding of msgID:52 -> Domestic Hot Water(DHW) message.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            b_decoding = True

            # check type of domestic hotwater generation
            if msg_bytecount >= 9:
                #  (0 :=> no hotwater generation is done be this heater, so no further decoding)
                # not active anymore, decoding is done anyway.
                if buffer[12] == 0:
                    #zs#test#               b_decoding = False
                    pass

            # if target-device is controller (wrong detection) then stop decoding
            if buffer[0] == 0x90:
                b_decoding = False

            if length > 10:
                # if MsgId:52_1_0-Value or 52_3_0-Value >= 0x7000 Tempsensor failure or not connected ->
                #      no decoding done then
                MsgID_52_1_0 = float(buffer[5] * 256 + buffer[6])
                MsgID_52_3_0 = float(buffer[7] * 256 + buffer[8])
                if MsgID_52_1_0 > 0x7000 or MsgID_52_3_0 > 0x7000:
                    b_decoding = False
            else:
                b_decoding = False

            # at least decode the stuff
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                if b_decoding == True:
                    # read values from buffer and assign them
                    if raw_index == 4 and msg_bytecount >= 1:
                        i_Soll = int(buffer[buffer_index])
                        self.__gdata.update(nickname, "Tsoll", self.__Check4MaxValue(nickname, "Tsoll", i_Soll))
                    if raw_index == 5 and msg_bytecount >= 2:
                        f_Ist = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                        self.__gdata.update(nickname, "Tist", self.__Check4MaxValue(nickname, "Tist", f_Ist))
                    if raw_index == 7 and msg_bytecount >= 2:
                        f_Speicheroben = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                        self.__gdata.update(nickname, "Tspeicher", self.__Check4MaxValue(nickname, "Tspeicher", f_Speicheroben))
                    if raw_index == 9 and msg_bytecount >= 1:
                        # Bitfeld Byte9
                        i_WW_einmallad = 1 if(buffer[buffer_index] & 0x02) else 0
                        i_WW_desinfekt = 1 if(buffer[buffer_index] & 0x04) else 0
                        i_WW_erzeugung = 1 if(buffer[buffer_index] & 0x08) else 0
                        i_WW_nachladung = 1 if(buffer[buffer_index] & 0x10) else 0
                        i_WW_temp_OK = 1 if(buffer[buffer_index] & 0x20) else 0
                        self.__gdata.update(nickname, "VWW_einmalladung", i_WW_einmallad)
                        self.__gdata.update(nickname, "VWW_desinfekt", i_WW_desinfekt)
                        self.__gdata.update(nickname, "VWW_erzeugung", i_WW_erzeugung)
                        self.__gdata.update(nickname, "VWW_nachladung", i_WW_nachladung)
                        self.__gdata.update(nickname, "VWW_temp_OK", i_WW_temp_OK)
                    if raw_index == 11 and msg_bytecount >= 1:
                        # Bitfeld Byte11
                        i_lade_pump_ein = 1 if(buffer[buffer_index] & 0x08) else 0
                        i_zirkula_pump_ein = 1 if(buffer[buffer_index] & 0x04) else 0
                        self.__gdata.update(nickname, "V_lade_pumpe", i_lade_pump_ein)
                        self.__gdata.update(nickname, "V_zirkula_pumpe", i_zirkula_pump_ein)
                    if raw_index == 14 and msg_bytecount >= 3:
                        # checking of wrong values, store only if valid
                        if buffer[14] != 0x89:
                            i_betriebszeit = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                            f_betriebszeit_stunden = float(i_betriebszeit / 60)
                        self.__gdata.update(nickname, "Cbetriebs_zeit", f_betriebszeit_stunden)
                    if raw_index == 17 and msg_bytecount >= 3:
                        # checking of wrong values, store only if valid
                        if buffer[17] != 0x89:
                            i_brennerww_ein = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                            self.__gdata.update(nickname, "Cbrenner_ww", i_brennerww_ein)
                    raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            if b_decoding == True:
                values = self.__gdata.values(nickname)
                return (nickname, values)
            else:
                return ("", None)
        else:
            return ("", None)

    def msgID_53_DomesticHotWater(self, msgtuple, buffer, length):
        """
            decoding of msgID:53 -> Domestic Hot Water(DHW) message.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 4
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 7 and msg_bytecount >= 1:
                    ############################  this is disabled ######
                    # cause this message is send by the controller to the heater
                    # and the heater will respond with message:52.
                    #  so the value will be set there.
                    # i_Soll = int(buffer[buffer_index])
                    # self.__gdata.update(nickname, "Tsoll", self.__Check4MaxValue(nickname, "Tsoll", i_Soll))
                    ####################################################
                    pass
                raw_index += 1

            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_269_DomesticHotWater_fromIPM(self, msgtuple, buffer, length):
        """
            decoding of msgID:269 -> Domestic Hot Water(DHW) message.
             Fkt returns hexdump for 'DHW' messages.
             Messages is for: Status NTC and Thermostat in WW-storagecell.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        for x in range(0, length):
            temptext = temptext + format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_467_468_DomesticHotWater_System1_2(self, msgtuple, buffer, length):
        """
            decoding of msgID:467 until 468 -> Domestic Hot Water(DHW) system 1 and 2 message.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            b_WWanfoderung = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1:
                    b_WWanfoderung = 1 if(buffer[buffer_index] & 0x08) else 0
                    debugstr = "{0:4}_{1:<2};WW1-Sofort;Anforderung:{2}".format(msgid, offset, b_WWanfoderung)
                    self._logging.debug(debugstr)
                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_797_DomesticHotWoter(self, msgtuple, buffer, length):
        """
            decoding of msgID:797 -> Domestic Hot Water(DHW) message.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

########################
#   ### Solarmessages ##
########################
    def msgID_866_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:866 -> solar message.
        """
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            f_kollektor = 0.0
            f_speicherunten = 0.0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 2:
                    if buffer[buffer_index] != 255:
                        f_kollektor = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    else:
                        f_kollektor = float(255 - buffer[buffer_index + 1]) / (-10)
                    self.__gdata.update(nickname, "Tkollektor", self.__Check4MaxValue(nickname, "Tkollektor", f_kollektor))

                if raw_index == 8 and msg_bytecount >= 2:
                    f_speicherunten = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Tspeicher_unten", self.__Check4MaxValue(nickname, "Tspeicher_unten", f_speicherunten))

                # secondary collector-filed temperatur
                if raw_index == 12 and msg_bytecount >= 2:
                    f_second_kollektor = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";second Tcollector:{0}".format(f_second_kollektor)
                    if not self.__IsTempInRange(f_second_kollektor):
                        debugstr += " -> not available"

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(temptext) if offset > 10 else self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_867_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:867 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                    ## cause: no values decoded yet this loop is disabled currently
                    #for buffer_index in range(first_payload_index, length - 2):
                    #    # read values from buffer and assign them
                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_868_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:868 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 9:
                    solar_status = buffer[buffer_index]
                    i_kollektor_aus = (1 if (solar_status & 0x02) else 0)
                    i_speicher_voll = (1 if (solar_status & 0x01) else 0)
                    self.__gdata.update(nickname, "Vkollektor_aus", i_kollektor_aus)
                    self.__gdata.update(nickname, "Vspeicher_voll", i_speicher_voll)
                    debugstr += ";collector_deactive:{0}%;storage_full:{1}".format(i_kollektor_aus, i_speicher_voll)

                if raw_index == 15:
                    pump_power = buffer[buffer_index]
                    debugstr += ";solarpump power:{0}%".format(pump_power)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_872_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:872 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        return self.msgID_Solarcommon(msgtuple, buffer, length)

    def msgID_873_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:873 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                f_ertrag_letztestunde = 0.0
                if raw_index == 6 and msg_bytecount >= 4:
                    f_ertrag_letztestunde = float(buffer[buffer_index] * 1048576 +
                                                  buffer[buffer_index + 1] * 65536 +
                                                  buffer[buffer_index + 2] * 256 +
                                                  buffer[buffer_index + 3]) / 10
                    self.__gdata.update(nickname, "V_ertrag_stunde", f_ertrag_letztestunde)

                if raw_index == 10 and msg_bytecount >= 4:
                    f_ertrag_day = float(buffer[buffer_index] * 1048576 +
                                              buffer[buffer_index + 1] * 65536 +
                                              buffer[buffer_index + 2] * 256 +
                                              buffer[buffer_index + 3]) / 1000
                    self.__gdata.update(nickname, "V_ertrag_tag_calc", f_ertrag_day)

                if raw_index == 14 and msg_bytecount >= 4:
                    f_ertrag_gesamt = float(buffer[buffer_index] * 1048576 +
                                            buffer[buffer_index + 1] * 65536 +
                                            buffer[buffer_index + 2] * 256 +
                                            buffer[buffer_index + 3]) / 10
                    self.__gdata.update(nickname, "V_ertrag_sum_calc", f_ertrag_gesamt)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_874_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:874 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 16:
                    statusbyte = buffer[buffer_index]
                    b_pumpe = 0
                    if (statusbyte == 4):
                        b_pumpe = 1
                    self.__gdata.update(nickname, "Vsolar_pumpe", b_pumpe)
                    debugstr += ";solarpump status:{0}".format(b_pumpe)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_910_SolarGain(self, msgtuple, buffer, length):
        """
            decoding of msgID:910 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        if not self.__DeviceIsModem(buffer[0]):
            self.__gdata.HeaterBusType(ht_const.BUS_TYPE_EMS)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            f_ertrag_letztestunde = 0.0
            f_ertrag_day = 0.0
            f_ertrag_total = 0.0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 4:
                    # Auswertung der Solarertrag letzte Stunde Bytes: 8-9
                    f_ertrag_letztestunde = float(buffer[buffer_index] * 1048576 +
                                                  buffer[buffer_index + 1] * 65536 +
                                                  buffer[buffer_index + 2] * 256 +
                                                  buffer[buffer_index + 3]) / 10
                    self.__gdata.update(nickname, "V_ertrag_stunde", f_ertrag_letztestunde)
                    debugstr += ";Ertrag Stunde:{0}Wh".format(f_ertrag_letztestunde)
                if raw_index == 10 and msg_bytecount >= 4:
                    f_ertrag_day = float(buffer[buffer_index] * 1048576 +
                                              buffer[buffer_index + 1] * 65536 +
                                              buffer[buffer_index + 2] * 256 +
                                              buffer[buffer_index + 3]) / 1000
                    self.__gdata.update(nickname, "V_ertrag_tag_calc", f_ertrag_day)
                    debugstr += ";tag:{0}kWh".format(f_ertrag_day)
                if raw_index == 14 and msg_bytecount >= 4:
                    f_ertrag_total = float(buffer[buffer_index] * 1048576 +
                                              buffer[buffer_index + 1] * 65536 +
                                              buffer[buffer_index + 2] * 256 +
                                              buffer[buffer_index + 3]) / 10
                    self.__gdata.update(nickname, "V_ertrag_sum_calc", f_ertrag_total)
                    debugstr += ";gesamt:{0}kWh".format(f_ertrag_total)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_913_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:913 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            i_laufzeit_minuten = 0
            i_laufzeit_stunden = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 4:
                    # Auswertung der Solarlaufzeiten
                    i_laufzeit_minuten = int(buffer[buffer_index] * 1048576 +
                                             buffer[buffer_index + 1] * 65536 +
                                             buffer[buffer_index + 2] * 256 +
                                             buffer[buffer_index + 3])
                    f_laufzeit_stunden = float(i_laufzeit_minuten / 60)
                    self.__gdata.update(nickname, "Claufzeit", f_laufzeit_stunden)
                    debugstr += ";Laufzeit minuten:{0}".format(i_laufzeit_minuten)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_259_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:259 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2
            f_kollektor = 0.0
            f_speicherunten = 0.0
            i_ertrag_letztestunde = 0
            b_pumpe = 0
            i_laufzeit_minuten = 0
            i_laufzeit_stunden = 0
            i_speicher_voll = 0
            i_kollektor_aus = 0

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x")+" "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 1:
                    # Optimierungsfaktor f. WW und solarer Unterstuetzung  Byte: 6
                    i_ofaktorWW = int(buffer[buffer_index])
                    debugstr += ";Optim.Faktor_WW:{0}".format(i_ofaktorWW)

                if raw_index == 7 and msg_bytecount >= 1:
                    # Optimierungsfaktor f. HG und solarer Unterstuetzung  Byte: 7
                    i_ofaktorHG = int(buffer[buffer_index])
                    debugstr += ";Optim.Faktor_HG:{0}".format(i_ofaktorHG)

                if raw_index == 8 and msg_bytecount >= 2:
                    i_ertrag_letztestunde = int(buffer[buffer_index] * 256 + buffer[buffer_index + 1])
                    self.__gdata.update(nickname, "V_ertrag_stunde", i_ertrag_letztestunde)
                    debugstr += ";Ertrag letzte Std.:{0}".format(i_ertrag_letztestunde)

                if raw_index == 10 and msg_bytecount >= 2:
                    # Solarkreis1
                    if buffer[buffer_index] != 255:
                        f_kollektor = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    else:
                        f_kollektor = float(255 - buffer[buffer_index + 1]) / (-10)
                    self.__gdata.update(nickname, "Tkollektor", self.__Check4MaxValue(nickname, "Tkollektor", f_kollektor))
                    debugstr += ";Tkollektor:{0}".format(f_kollektor)

                if raw_index == 12 and msg_bytecount >= 2:
                    f_speicherunten = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Tspeicher_unten", self.__Check4MaxValue(nickname, "Tspeicher_unten", f_speicherunten))
                    debugstr += ";Tspeicher:{0}".format(f_speicherunten)

                if raw_index == 14 and msg_bytecount >= 1:
                    # Auswertung solar-pump status
                    b_pumpe = 1 if (buffer[buffer_index] & 0x01) else 0
                    self.__gdata.update(nickname, "Vsolar_pumpe", b_pumpe)
                    debugstr += ";pump status:{0}".format(b_pumpe)

                if raw_index == 15 and msg_bytecount >= 1:
                    # Auswertung Solar Systemstatus
                    i_kollektor_aus = 1 if(buffer[buffer_index] & 0x01) else 0
                    i_speicher_voll = 1 if(buffer[buffer_index] & 0x04) else 0
                    self.__gdata.update(nickname, "Vkollektor_aus", i_kollektor_aus)
                    self.__gdata.update(nickname, "Vspeicher_voll", i_speicher_voll)
                    debugstr += ";Kollektor aus:{0}; Speicher voll:{1}".format(i_kollektor_aus, i_speicher_voll)

                if raw_index == 16 and msg_bytecount >= 3:
                    # Auswertung der Solarlaufzeiten
                    i_laufzeit_minuten = int(buffer[buffer_index] * 65536 + buffer[buffer_index + 1] * 256 + buffer[buffer_index + 2])
                    f_laufzeit_stunden = float(i_laufzeit_minuten / 60)
                    self.__gdata.update(nickname, "Claufzeit", f_laufzeit_stunden)
                    debugstr += ";laufzeit Min.:{0}".format(i_laufzeit_minuten)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_260_Solar(self, msgtuple, buffer, length):
        """
            decoding of msgID:2603 -> solar message.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        debugstr = "{0:4}_{1:<2}".format(msgid, offset)
        first_payload_index = 6
        for x in range(0, first_payload_index):
            temptext += format(buffer[x], "02x") + " "
        # length > first index + crc-byte + break-byte
        if length > first_payload_index + 2:
            # init values
            raw_index = offset + first_payload_index
            msg_bytecount = length - first_payload_index - 2

            for buffer_index in range(first_payload_index, length - 2):
                temptext += format(buffer[buffer_index], "02x") + " "
                # read values from buffer and assign them
                if raw_index == 6 and msg_bytecount >= 2:
                    f_t41 = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Thybrid_buffer", f_t41)
                    debugstr += ";T3 hybrid_buffer:{0}".format(f_t41)

                if raw_index == 8 and msg_bytecount >= 2:
                    f_t42 = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    self.__gdata.update(nickname, "Thybrid_sysinput", f_t42)
                    debugstr += ";T heizruecklauf:{0}".format(f_t42)

                if raw_index == 14 and msg_bytecount >= 2:
                    f_t2collectorfeld = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    if self.__IsTempInRange(f_t2collectorfeld):
                        self.__gdata.update(nickname, "V_spare_1", f_t2collectorfeld)
                        #setup flag for 2.collector-field values and GUI
                        self.__gdata.IsSecondCollectorValue_SO(True)
                        debugstr += "; 2.Coll_feld Temperatur:{0}".format(f_t2collectorfeld)

                if raw_index == 16 and msg_bytecount >= 2:
                    f_t3pufferspeicher = float(buffer[buffer_index] * 256 + buffer[buffer_index + 1]) / 10
                    debugstr += ";TB buffer_zell top:{0}".format(f_t3pufferspeicher)

                if raw_index == 22 and msg_bytecount >= 1:
                    so_pump_2collector = 1 if (buffer[buffer_index] & 0x04) else 0
                    self.__gdata.update(nickname, "V_spare_2", so_pump_2collector)
                    debugstr += "; 2.Coll_feld PumpStatus:{0}".format(so_pump_2collector)

                raw_index += 1
            for buffer_index in range(length - 2, length):
                temptext += format(buffer[buffer_index], "02x") + " "
            self.__gdata.update(nickname, "hexdump", temptext)
            self._logging.debug(debugstr)

            values = self.__gdata.values(nickname)
            return (nickname, values)
        else:
            return ("", None)

    def msgID_Solarcommon(self, msgtuple, buffer, length):
        """
            decoding of msgID: others -> solar common used messages other then previous.
        """
        self.__gdata.IsSolarAvailable(True)
        nickname = "SO"
        (msgid, offset) = msgtuple
        temptext = "{0:4}_{1:<2}:{2:3}:".format(msgid, offset, nickname)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        self._logging.debug(temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_AnyMessage(self, msgtuple, buffer, length):
        """
            decoding of msgID: any -> any messages not handled yet separately.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        systempart_tag = nickname
        device_address = buffer[0] & 0x7f
        if self.__DeviceIsModem(device_address):
            systempart_tag = "mod"
        else:
            systempart_tag = "???"

        temptext = "{0:4}_{1:<2}:{2:<3}:".format(msgid, offset, systempart_tag)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        self._logging.debug(temptext)

        values = self.__gdata.values(nickname)
        return (nickname, values)

##################################
#   ### Modem-Handling messages ##
##################################

    def msgID_239_datahandling(self, msgtuple, buffer, length):
        """
            display of msgID:239 -> modem messages if device-adr is modem.
        """
        nickname = "DT"
        (msgid, offset) = msgtuple
        # select systempart-tag from source-byte buffer[0]
        systempart_tag = "???"
        device_address = buffer[0] & 0x7f
        if self.__DeviceIsModem(device_address):
            systempart_tag = "mod"
        temptext = "{0:4}_{1:<2}:{2:<3}:".format(msgid, offset, systempart_tag)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        self._logging.debug(temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_787_788_extDHWhandling(self, msgtuple, buffer, length):
        """
            decoding of msgID:787 until 788 -> Domestic Hot Water(DHW) message.
        """
        nickname = "WW"
        (msgid, offset) = msgtuple
        # select systempart-tag from source-byte buffer[0]
        systempart_tag = "WW"
        device_address = buffer[0] & 0x7f
        if self.__DeviceIsModem(device_address):
            systempart_tag = "mod"
        temptext = "{0:4}_{1:<2}:{2:<3}:".format(msgid, offset, systempart_tag)
        for x in range(0, length):
            temptext += format(buffer[x], "02x") + " "
        self.__gdata.update(nickname, "hexdump", temptext)
        self._logging.debug(temptext)
        values = self.__gdata.values(nickname)
        return (nickname, values)

    def msgID_xzy_suppress_it(self, msgtuple, buffer, length):
        """
            used to suppress the message, no display and no decoding.
        """
        return ("", None)

#--- class cht_decode end ---#
################################################


class cht_discode(cht_decode, ht_utils.cht_utils, ht_utils.clog):
    """
    Dispatcher-class reading raw-data from serial port, dispatching
    and decoding raw-data using 'cht_decode()'-class.
    There is a statemachine implemented to handle different situations
     # static value-definitions
     # # runstate sequences can be:
     # #  0 --> 1 (if tranceiver-type  found)--> 2 --> 3 --> 4
     # #  0 --> 1 (if pur rawdata-type found)--> 3 --> 5
     # #  4 (if transceiver-header not found)--> 2 --> 3 --> 4
     #
    """
    _STATE_INIT                     = 0  # preset values, runs once
    _STATE_MESSAGETYPE_SEARCH       = 1  # message-type detection, runs once
    _STATE_TRANS_HEADER_SEARCH      = 2  # searching for transceiver-message
    _STATE_PRERUN                   = 3  # preset values before running-mode
    _STATE_TRANSMITTER_MSG_HANDLING = 4  # transmitter-msg handling
    _STATE_PUR_RAWDATA_HANDLING     = 5  # None transmitter-msg handling

    def __init__(self, port, commondata, debug=0, filehandle=None, logger=None):
        """
            initialisation of class
        """
        cht_decode.__init__(self, commondata, logger)
        ht_utils.cht_utils.__init__(self)
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging = ht_utils.clog.create_logfile(self, logfilepath="./cht_discode.log", loggertag="cht_discode")
            else:
                self._logging = logger
        except:
            errorstr = """cht_discode();Error;could not create logfile"""
            print(errorstr)
            raise EnvironmentError(errorstr)

        try:
            #check at first the parameters
            if filehandle == None:
                if not (isinstance(port, serial.serialposix.Serial) or isinstance(port, ht_proxy_if.cht_socket_client)):
                    errorstr = "cht_discode();TypeError;port"
                    self._logging.critical(errorstr)
                    raise TypeError(errorstr)

            if not isinstance(commondata, data.cdata):
                errorstr = "cht_discode();TypeError;commondata"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
        except (TypeError) as e:
            errorstr = 'cht_discode();Error;Parameter:<{0}> has wrong type'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

        self.port = port
        self.filehandle = filehandle
        self.data = commondata
        self.debug = debug
        ## protected variables
        self._run_state = cht_discode._STATE_INIT
        # buffer for read bus-data
        self._rawdata = []
        self._max_messagesize = 40
        self._ht_transceiver_header_found = False

    def __read(self):
        """
            reading bytes from interface.
             That interface can be:
             1. File if 'filehandle' is set,
             2. socket- or port-read else.
        """
        if self.filehandle == None:
            return ord(self.port.read())
        else:
            rtn = self.filehandle.read(1)
# ###########################
#zs#only 4 test ############
# #            import time
# #            time.sleep(0.005)
# ###########################
            return ord(rtn) if len(rtn) > 0 else ord('0')

    def __dump_rawbuffer(self, size, offset=0):
        """
            displays the current available N-bytes from buffer,
             using offset as start-index.
             where N := size.
        """
        if size > len(self._rawdata):
            size = len(self._rawdata)
        if offset >= size:
            offset = 0
        temptext = ""
        for dump_index in range(offset, size):
            temptext += format(self._rawdata[dump_index], "02x") + " "
        print(temptext)

    def _ValidSourceTargetBytes(self, sourcebyte, targetbyte):
        """
            checking the source- and target-byte for valid range.
        """
        rtn = False
        # source- and target-bytes with valid addresses
        #  remark: target without request (MSB) set
        if (sourcebyte > 0x80 and targetbyte < 0x80):
            # get the deviceaddress from sourcebyte
            source_deviceaddress = (0x7f & sourcebyte)
            # compare this bytes to the whitelist
            if source_deviceaddress in self.deviceaddress_white_list and \
                (targetbyte == 0 or targetbyte in self.deviceaddress_white_list):
                rtn = True
        return rtn

    def _remove_black_sequences(self):
        """
            removing bytes from buffer using predefined unusable sequences.
        """
        for value in self.black_sequence.values():
            if value[0] in self._rawdata:
                found_index = self._rawdata.index(value[0])
                if len(self._rawdata) > found_index + len(value):
                    search_index = 1
                    compare_counter = 1
                    while search_index < len(value):
                        if value[search_index] == self._rawdata[found_index + search_index]:
                            compare_counter += 1
                        search_index += 1

                    if compare_counter == len(value):
                        del self._rawdata[0:(found_index + compare_counter)]

    def _IsValidMessageID(self, deviceaddress, msgid):
        """
            checking msgid, must be > 0 and is compared to predefinitions.
        """
        isvalid = False
        if msgid > 0:
            adr_found = False
            deviceaddress = deviceaddress & 0x7f
            for address in self.deviceadr_2msgid_mapping:
                if deviceaddress == address:
                    adr_found = True
                    if msgid in self.deviceadr_2msgid_mapping[address]:
                        isvalid = True
                    break
            # force this to True for all other unmapped device-addresses
            if adr_found == False:
                isvalid = True
        return isvalid

    def _IsInBlacklist(self, deviceaddress, msgid):
        """
            check deviceaddress attached to msgid using the blacklist
             returns True if messageid is in blacklist for this deviceaddress,
             returns False else.
        """
        isinlist = False
        if msgid > 0:
            adr_found = False
            deviceaddress = deviceaddress & 0x7f
            for address in self.deviceadr_2msgid_blacklist:
                if deviceaddress == address:
                    adr_found = True
                    if msgid in self.deviceadr_2msgid_blacklist[address]:
                        isinlist = True
                    break
            # force this to False for all other unmapped device-addresses
            if adr_found == False:
                isinlist = False
        return isinlist

    def _read_rawdata(self):
        """
            reading raw-data to buffer for at least 'max_messagesize'.
        """
        rtnvalue = 0
        if len(self._rawdata) < self._max_messagesize:
            #read data to rawbuffer
            readcounter = self._max_messagesize - len(self._rawdata)
            while readcounter > 0:
                value = self.__read()
                if value == None:
                    rtnvalue = -1
                    break
                else:
                    self._rawdata.append(value)
                readcounter -= 1
        if not rtnvalue == -1:
            rtnvalue = len(self._rawdata)
        return rtnvalue

    def _IsTransceiverMsgHeader(self, buffer):
        """
            returns True if ht_transceiver Msg-header available, else False.
        """
        rtn_flag = False
        try:
             # search for start-tag '#' and 'H','R'
            if (buffer[0] == 0x23 and buffer[1] == 0x48 and buffer[2] == 0x52):
                rtn_flag = True
        except:
            rtn_flag = False
        return rtn_flag

    def _search_4_transceiver_message(self):
        """
            searching for ht_transceiver message-header.
             returns True if found, else False.
        """
        try:
            transceiver_found = False
            self._max_messagesize = 40
            size = self._read_rawdata()
            if size > 5:
                size -= 5
                # searching header from byte 0 to max-buffersize - header-size
                for check_index in range(0, size):
                    transceiver_found = self._IsTransceiverMsgHeader(self._rawdata[check_index:])
                    if (transceiver_found):
                        del self._rawdata[0:check_index]
                        break
            else:
                transceiver_found = False
        except:
            errorstr = "cht_discode._search_4_transceiver_message();Error"
            self._logging.critical(errorstr)
            transceiver_found = False
        tempstr = "cht_discode._search_4_transceiver_message(); found: {0}".format(transceiver_found)
        self._logging.debug(tempstr)

        return transceiver_found

    ####################################
    # # common used mapping for dispatching messageID to function-calls
      #  the numbers are the messageID's
      #  the names are references to the callable functions
      #   function-parameters have to be:
      #     1. tuple  := (msgid, offset)
      #     2. referenz to the payload-buffer
      #     3. length := payload-length and terminating CRC- and break-byte
    dispatch = {
        2: cht_decode.msgID_2_BusInfo,
        5: cht_decode.msgID_5_SystemInfo,
        6: cht_decode.msgID_6_datetime,
        7: cht_decode.msgID_7_TokenStati,
#zs#          9: cht_decode.msgID_AnyMessage, <---- Deactivated cause, to many wrong detections
        9: cht_decode.msgID_xzy_suppress_it,
        22: cht_decode.msgID_22_Heaterdevice,
        24: cht_decode.msgID_24_Heaterdevice,
        25: cht_decode.msgID_25_Heaterdevice,
        26: cht_decode.msgID_26_HeatingCircuit,
        27: cht_decode.msgID_27_DomesticHotWater,
        28: cht_decode.msgID_28_Service,
        30: cht_decode.msgID_30_T_HydraulischeWeiche,
        35: cht_decode.msgID_35_HydraulischeWeiche,
        36: cht_decode.msgID_36_Heater_Configuration,
        42: cht_decode.msgID_42_Heaterdevice,
        48: cht_decode.msgID_xzy_suppress_it,
        51: cht_decode.msgID_51_DomesticHotWater,
        52: cht_decode.msgID_52_DomesticHotWater,
        53: cht_decode.msgID_53_DomesticHotWater,
        59: cht_decode.msgID_xzy_suppress_it,
        65: cht_decode.msgID_xzy_suppress_it,
        66: cht_decode.msgID_xzy_suppress_it,
        136: cht_decode.msgID_xzy_suppress_it,
        162: cht_decode.msgID_162_DisplayCause,
        176: cht_decode.msgID_xzy_suppress_it,
        188: cht_decode.msgID_188_Hybrid,
        190: cht_decode.msgID_190_DisplayAndCauseCode,
        191: cht_decode.msgID_AnyMessage,
        239: cht_decode.msgID_239_datahandling,
        259: cht_decode.msgID_259_Solar,
        260: cht_decode.msgID_260_Solar,
        268: cht_decode.msgID_268_HeatingCircuit,
        269: cht_decode.msgID_269_DomesticHotWater_fromIPM,
        290: cht_decode.msgID_290_RemoteController_FB10,
        291: cht_decode.msgID_291_RemoteController_FB10,
        296: cht_decode.msgID_296_ErrorMsg,
        357: cht_decode.msgID_357_360_HeatingCircuit,
        358: cht_decode.msgID_357_360_HeatingCircuit,
        359: cht_decode.msgID_357_360_HeatingCircuit,
        360: cht_decode.msgID_357_360_HeatingCircuit,
        367: cht_decode.msgID_367_370_HeatingCircuit,
        368: cht_decode.msgID_367_370_HeatingCircuit,
        369: cht_decode.msgID_367_370_HeatingCircuit,
        370: cht_decode.msgID_367_370_HeatingCircuit,
        377: cht_decode.msgID_377_380_HeatingCircuit,
        378: cht_decode.msgID_377_380_HeatingCircuit,
        379: cht_decode.msgID_377_380_HeatingCircuit,
        380: cht_decode.msgID_377_380_HeatingCircuit,
        467: cht_decode.msgID_467_468_DomesticHotWater_System1_2,
        468: cht_decode.msgID_467_468_DomesticHotWater_System1_2,
        569: cht_decode.msgID_569_HeatingCircuit,
        596: cht_decode.msgID_596_HeatingCircuit,
        597: cht_decode.msgID_597_HeatingCircuit,
        615: cht_decode.msgID_615_HeatingCircuit,
        660: cht_decode.msgID_AnyMessage,
        661: cht_decode.msgID_AnyMessage,
        662: cht_decode.msgID_AnyMessage,
        677: cht_decode.msgID_677_680_HeatingCircuit,
        678: cht_decode.msgID_677_680_HeatingCircuit,
        679: cht_decode.msgID_677_680_HeatingCircuit,
        680: cht_decode.msgID_677_680_HeatingCircuit,
        681: cht_decode.msgID_AnyMessage,
        682: cht_decode.msgID_AnyMessage,
        689: cht_decode.msgID_AnyMessage,
        697: cht_decode.msgID_697_704_HeatingCircuit,
        698: cht_decode.msgID_697_704_HeatingCircuit,
        699: cht_decode.msgID_697_704_HeatingCircuit,
        700: cht_decode.msgID_697_704_HeatingCircuit,
        701: cht_decode.msgID_697_704_HeatingCircuit,
        702: cht_decode.msgID_697_704_HeatingCircuit,
        703: cht_decode.msgID_697_704_HeatingCircuit,
        704: cht_decode.msgID_697_704_HeatingCircuit,
        727: cht_decode.msgID_727_734_HeatingCircuit,
        728: cht_decode.msgID_727_734_HeatingCircuit,
        729: cht_decode.msgID_727_734_HeatingCircuit,
        730: cht_decode.msgID_727_734_HeatingCircuit,
        737: cht_decode.msgID_737_744_HeatingCircuit,
        738: cht_decode.msgID_737_744_HeatingCircuit,
        739: cht_decode.msgID_737_744_HeatingCircuit,
        740: cht_decode.msgID_737_744_HeatingCircuit,
        747: cht_decode.msgID_747_754_HeatingCircuit,
        748: cht_decode.msgID_747_754_HeatingCircuit,
        749: cht_decode.msgID_747_754_HeatingCircuit,
        750: cht_decode.msgID_747_754_HeatingCircuit,
        787: cht_decode.msgID_787_788_extDHWhandling,
        788: cht_decode.msgID_787_788_extDHWhandling,
        797: cht_decode.msgID_797_DomesticHotWoter,
        866: cht_decode.msgID_866_Solar,
        867: cht_decode.msgID_867_Solar,
        868: cht_decode.msgID_868_Solar,
        870: cht_decode.msgID_Solarcommon,
        872: cht_decode.msgID_872_Solar,
        873: cht_decode.msgID_873_Solar,
        874: cht_decode.msgID_874_Solar,
        902: cht_decode.msgID_AnyMessage,
        910: cht_decode.msgID_910_SolarGain,
        913: cht_decode.msgID_913_Solar,
        1087: cht_decode.msgID_AnyMessage,
        1088: cht_decode.msgID_AnyMessage,
        1089: cht_decode.msgID_AnyMessage,
        1090: cht_decode.msgID_AnyMessage,
        1091: cht_decode.msgID_AnyMessage,
        1092: cht_decode.msgID_AnyMessage,
        1093: cht_decode.msgID_AnyMessage,
        1094: cht_decode.msgID_AnyMessage,
        1097: cht_decode.msgID_AnyMessage,
        1098: cht_decode.msgID_AnyMessage,
        1099: cht_decode.msgID_AnyMessage,
        1100: cht_decode.msgID_AnyMessage,
        1101: cht_decode.msgID_AnyMessage,
        1102: cht_decode.msgID_AnyMessage,
        1103: cht_decode.msgID_AnyMessage,
        1104: cht_decode.msgID_AnyMessage,
        1105: cht_decode.msgID_AnyMessage,
        1106: cht_decode.msgID_AnyMessage,
        1107: cht_decode.msgID_AnyMessage,
        1108: cht_decode.msgID_AnyMessage,
        1109: cht_decode.msgID_AnyMessage,
        1110: cht_decode.msgID_AnyMessage,
        1111: cht_decode.msgID_AnyMessage,
        1112: cht_decode.msgID_AnyMessage,
        1113: cht_decode.msgID_AnyMessage,
        1114: cht_decode.msgID_AnyMessage,
        1129: cht_decode.msgID_AnyMessage,
        1130: cht_decode.msgID_AnyMessage,
        1131: cht_decode.msgID_AnyMessage,
        1132: cht_decode.msgID_AnyMessage,
    }
    ####################################
    # devices-addresses marked as valid (to support searching)
    #  valid bytes are then: (80 + deviceaddress)hex
    #  remark: address-whitelist is currently limitted to:
    #      max 4 heatercircuits,
    #          2 solar-circuits
    #          2 domestic hotwater-circuits
    deviceaddress_white_list = [0x08, 0x0a, 0x0b, 0x0c, 0x0d, 0x10, 0x18, 0x19, 0x1a,
                                0x20, 0x21, 0x22, 0x23, 0x28, 0x29,
                                0x30, 0x31, 0x48]

    ####################################
    # device-adr mapped with not valid message-IDs for detailed message - searching.
    #  1.modification reagarding:
    #   https://www.mikrocontroller.net/topic/324673#5169108
    deviceadr_2msgid_blacklist = {
        0x10: [11, 12, 24, 46, 47, 64, 100, 106],
        0x1b: [17, 56, 74, 89],
        0x20: [13, 14, 15, 21, 23, 25, 29, 45, 49, 51, 61, 81, 88, 92, 95, 97, 101, 104, 107],
        0x21: [13, 14, 15, 21, 23, 25, 29, 45, 49, 51, 61, 81, 88, 92, 95, 97, 101, 104, 107],
        0x22: [13, 14, 15, 21, 23, 25, 29, 45, 49, 51, 61, 81, 88, 92, 95, 97, 101, 104, 107],
        0x23: [13, 14, 15, 21, 23, 25, 29, 45, 49, 51, 61, 81, 88, 92, 95, 97, 101, 104, 107],
    }

    ####################################
    # polling sequences with no datacontent to be removed from RAW-string (to
    #  support the searching)
    #  currently unused
    black_sequence = {
        0: [9, 0, 0x89, 0],
        1: [9, 0, 0x89, 0, 0x30, 0, 0xb0, 0, 9, 0, 0x89, 0],
    }
    ####################################
    # device-adr mapped with attached message-IDs for detailed message - searching
    deviceadr_2msgid_mapping = {
        0x30: [259, 260, 866, 867, 868, 870, 872, 873, 874, 906, 910, 913]
    }

    def discoder(self):
        """
            Searching for msg-header, decode it and calling decode-functions.
        """
        (msgid, offset) = (0, 0)
        payload_size = 0
        message_size = 0
        value = None
        nickname = ""

        ############################
        # preset values, runs once
        if self._run_state == cht_discode._STATE_INIT:
            self._ht_transceiver_header_found = False
            self._max_messagesize = 40
            # setup next state
            self._run_state = cht_discode._STATE_MESSAGETYPE_SEARCH

        ############################
        # message-type detection, runs once
        if self._run_state == cht_discode._STATE_MESSAGETYPE_SEARCH:
            # searching for ht_transceiver message-header
            try:
                self._ht_transceiver_header_found = self._search_4_transceiver_message()
                if (self._ht_transceiver_header_found):
                    tempstr = "cht_discode.discoder() --> ht_transceiver-header found <--"
                    # setup next state to transceiver-search
                    self._run_state = cht_discode._STATE_TRANS_HEADER_SEARCH
                else:
                    tempstr = "cht_discode.discoder() --> common CRC-detection procedure <--"
                    # setup next state to preset data
                    self._run_state = cht_discode._STATE_PRERUN
                self._logging.info(tempstr)
            except:
                self._ht_transceiver_header_found = False
                self._run_state = cht_discode._STATE_PRERUN

        ############################
        # searching for transceiver-message
        if self._run_state == cht_discode._STATE_TRANS_HEADER_SEARCH:
            self._max_messagesize = 40
            self._ht_transceiver_header_found = self._search_4_transceiver_message()
            # setup next state
            self._run_state = cht_discode._STATE_PRERUN

        ############################
        # preset values before running-mode
        if self._run_state == cht_discode._STATE_PRERUN:
            self._max_messagesize = 10
            # setup next state
            if (self._ht_transceiver_header_found):
                self._run_state = cht_discode._STATE_TRANSMITTER_MSG_HANDLING
            else:
                self._run_state = cht_discode._STATE_PUR_RAWDATA_HANDLING

        ############################
        # transmitter-msg handling
        if self._run_state == cht_discode._STATE_TRANSMITTER_MSG_HANDLING:
            payload_size = 0
            message_size = 0
            crc_ok = False
            try:
                if self._IsTransceiverMsgHeader(self._rawdata):
                    # get payload-size from header and rest of msg (including terminating CRC)
                    #  msg-struct: #HR(11)h<size><payload-bytes><CRC-byte>
                    payload_size = self._rawdata[4]
                    # msg-size := payload-size + header-size + CRC-byte
                    message_size = payload_size + 6
                    if ((payload_size > 5) and (payload_size < 35)):
                        # check current buffer-size and load the rest, if is less then msg-size
                        if len(self._rawdata) < message_size:
                            readcounter = message_size - len(self._rawdata)
                            while readcounter > 0:
                                value = self.__read()
                                self._rawdata.append(value)
                                readcounter -= 1
                        # check CRC
                        crc_ok = self.crc_testen(self._rawdata[5:], payload_size)
                        # handle message if CRC is ok and terminating 'break' := 0 is available
                        if ((crc_ok == True) and self._rawdata[message_size - 2] == 0):
                            (msgid, offset) = self.GetMessageID(self._rawdata[5:])
                            if (msgid > 0):
                                try:
                                    (nickname, value) = self.dispatch[msgid](self, (msgid, offset), self._rawdata[5:], payload_size)
                                except:
                                    self.msgID_NN_unknown((msgid, offset), self._rawdata[5:], payload_size)
                                    nickname = ""
                                    value = None
                        else:
                            nickname = ""
                            value = None

                    # delete old message from buffer
                    del self._rawdata[0:message_size]
                    # read new heaterbus-data
                    self._read_rawdata()
                else:
                    if len(self._rawdata) > 0:
                        del self._rawdata[0]
                    self._run_state = cht_discode._STATE_TRANS_HEADER_SEARCH

                if len(nickname) < 2:
                    value = None
                return (nickname, value)

            except (LookupError, IndexError, KeyError, TypeError, IOError, UnboundLocalError) as e:
                errorstr = 'cht_discode.discoder();Error;<{0}>'.format(e.args[0])
                self._logging.critical(errorstr)
                print(errorstr)
                raise

        ############################
        # None transmitter-msg handling
        if self._run_state == cht_discode._STATE_PUR_RAWDATA_HANDLING:
            message_size = 0
            crc_ok = False
            self._max_messagesize = 40
            try:
                self._read_rawdata()
                # searching for message with valid source and target-bytes
                while len(self._rawdata) > 1:
                    if self._ValidSourceTargetBytes(self._rawdata[0], self._rawdata[1]):
                        break
                    else:
                        del self._rawdata[0]
                        self._read_rawdata()

                if self._ValidSourceTargetBytes(self._rawdata[0], self._rawdata[1]):
                    # search for a valid CRC
                    crc_ok = False
                    message_size = 0
                    for crc_checklength in range(6, (len(self._rawdata) - 2)):
                        crc_ok = self.crc_testen(self._rawdata, crc_checklength)
                        if crc_ok == True:
                            # message_size includes that terminating 0 := break-signal
                            message_size = crc_checklength
                            break

                    # check valid crc for that current raw-buffer content and the terminating Break-Sign := 0
                    #  if valid then process message
                    if crc_ok == True and message_size > 6:
                        (msgid, offset) = self.GetMessageID(self._rawdata)
                        if self._IsValidMessageID(self._rawdata[0], msgid) and not self._IsInBlacklist(self._rawdata[0], msgid):
                            # dispatch data if terminating 0 := break-signal is available
                            if self._rawdata[message_size - 1] == 0:
                                try:
                                    (nickname, value) = self.dispatch[msgid](self, (msgid, offset), self._rawdata, message_size)
                                except:
                                    self.msgID_NN_unknown((msgid, offset), self._rawdata, message_size)
                                    nickname = ""
                                    value = None
                        else:
                            nickname = ""
                            value = None
                        del self._rawdata[0:message_size]
                    else:
                        del self._rawdata[0]
                else:
                    del self._rawdata[0]

                if len(nickname) < 2:
                    value = None
                return (nickname, value)
            except:
                raise


#--- class cht_discode end ---#
################################################
if __name__ == "__main__":
    """
        used for modultest-purposes.
    """
    import serial
    import sys
    import os
    import data
    import db_sqlite

    configurationfilename = './../etc/config/4test/HT3_4dispatcher_test.xml'
    testdata = data.cdata()
    testdata.read_db_config(configurationfilename)
    #### reconfiguration has to be done in configuration-file ####
            # open socket for client and connect to server,
            #   socket-object is written to 'self.__port'
    if(testdata.IsDataIf_socket()):
        from ht_proxy_if import cht_socket_client as ht_proxy_client
        try:
            client_cfg_file = os.path.normcase(os.path.abspath(testdata.client_cfg_file()))
            if not os.path.exists(client_cfg_file):
                errorstr = "ht_discode();Error;couldn't find file:{0}".format(client_cfg_file)
                print(errorstr)
        except:
            errorstr = "ht_discode();Error;couldn't find file:{0}".format(client_cfg_file)
            print(errorstr)
        try:
            serialdevice = ht_proxy_client(client_cfg_file)
        except:
            errorstr = "ht_discode();Error;couldn't open requested socket; cfg-file:{0}".format(client_cfg_file)
            print(errorstr)
            raise
        input_mode = "SOCKET"
    else:
        #open serial port for reading HT3-data
        serialdevice = testdata.AsyncSerialdevice()
        baudrate = testdata.AsyncBaudrate()
        input_mode = "ASYNC"

    print("----- do some real checks -----")
    print(" used device       :<{0}>".format(serialdevice))
    print(" used configuration:<{0}>".format(configurationfilename))
    print()
    print("For this test it is required to have:")
    print(" 1. Hardware connected to the above serial-device.")
    print("    If not, change the name in config-file and start again.")
    print(" 2. Hardware connected to the Heater HT-bus")
    print("As result it is:")
    debugstr = "ht_discode.test();  Datainput-Mode:{0}".format(input_mode)
    print(debugstr)
    if testdata.IsDataIf_async():
        try:
            port = serial.Serial(serialdevice, baudrate)
        except:
            print()
            print("couldn't open requested device: <{0}>".format(serialdevice))
            print()
            sys.exit(1)
    else:
        port = serialdevice

    print("--> Intercepted data written to stdout")

    debug = 1
    HT3 = cht_discode(port, testdata, debug)
    while True:
        (nickname, value) = HT3.discoder()
        if value != None:
            print("{0};{1}".format(nickname, value))

    # must be never reached but for completeness
    print("!!! Error in ht3_discoder occured !!!")
