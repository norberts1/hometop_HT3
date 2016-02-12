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
# Ver:0.1.5.1  / Datum 12.06.2014
# Ver:0.1.6  / Datum 10.01.2015 'max- and default-values' added
#                                crc-checkfkt moved to ht_utils.py
#                                fkt added for FW100_200 msg's
# Ver:0.1.7.1/ Datum 04.03.2015 'heizungspumpenleistung' added
#              https://www.mikrocontroller.net/topic/324673#3970615
#              logging from ht_utils added
# Ver:0.1.8  / Datum 07.02.2016 HeizkreisMsg_ID677_max33byte added
#                                 for CWxyz handling
#                               Heating-circuit assignment corrected (6F...72)
# Ver:0.1.8.1/ Datum 10.02.2016 Methode: HeizkreisMsg_ID677_max33byte()
#                                 'Tsoll_HK'      assigned to Byte12 
#                                 'Vbetriebs_art' assigned to Byte27
# Ver:0.1.8.2/ Datum 12.02.2016 'IPM_LastschaltmodulWWModeMsg()'
#                                 fix for wrong msg-detection: 'a1 00 34 00'
#################################################################

import data, time, ht_utils
import ht_utils

class cht3_decode(ht_utils.cht_utils):
    def __init__(self, gdata, logger=None):
        ht_utils.cht_utils.__init__(self)
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging=ht_utils.clog.create_logfile(self, logfilepath="./cht3_decode.log", loggertag="cht3_decode")
            else:
                self._logging=logger
        except:
            errorstr="""cht3_decode();Error;could not create logfile"""
            print(errorstr)
            raise EnvironmentError(errorstr)
        
        #check first the parameter
        if not isinstance(gdata, data.cdata):
            errorstr='cht3_decode();TypeError;Parameter "gdata" has wrong type'
            self._logging.critical(errorstr)
            raise TypeError(errorstr)

        self.__info_datum="--.--.----"
        self.__info_zeit="--:--:--"
        # save data-object
        self.__gdata=gdata
        # setup data to already available logging-object
        self.__gdata.setlogger(self._logging)
        # set default-values HG
        self.__currentHK_nickname="HG"
        self.__gdata.update(self.__currentHK_nickname,"Tvorlauf_soll",0)
        self.__gdata.update(self.__currentHK_nickname,"Tvorlauf_ist" ,0.0)
        self.__gdata.update(self.__currentHK_nickname,"Truecklauf",0.0)
        self.__gdata.update(self.__currentHK_nickname,"Tmischer",0.0)
        self.__gdata.update(self.__currentHK_nickname,"Vmodus",0)
        self.__gdata.update(self.__currentHK_nickname,"Vbrenner_motor",0)
        self.__gdata.update(self.__currentHK_nickname,"Vbrenner_flamme",0)
        self.__gdata.update(self.__currentHK_nickname,"Vleistung",0)
        self.__gdata.update(self.__currentHK_nickname,"Vheizungs_pumpe",0)
        self.__gdata.update(self.__currentHK_nickname,"Vspeicher_pumpe",0)
        self.__gdata.update(self.__currentHK_nickname,"Vzirkula_pumpe",0)
        self.__gdata.update(self.__currentHK_nickname,"V_spare1",0)
        self.__gdata.update(self.__currentHK_nickname,"V_spare2",0)
        self.__gdata.update("HK1","V_spare1",0)
        self.__gdata.update("HK1","V_spare2",0)
        self.__gdata.update("HK2","V_spare1",0)
        self.__gdata.update("HK2","V_spare2",0)
        self.__gdata.update("HK3","V_spare1",0)
        self.__gdata.update("HK3","V_spare2",0)
        self.__gdata.update("HK4","V_spare1",0)
        self.__gdata.update("HK4","V_spare2",0)
        self.__gdata.update("WW","V_WWdesinfekt",0)
        self.__gdata.update("WW","V_WWeinmalladung",0)
        self.__gdata.update("WW","V_WWdesinfekt",0)
        self.__gdata.update("WW","V_WWerzeugung",0)
        self.__gdata.update("WW","V_WWnachladung",0)
        self.__gdata.update("WW","V_WWtemp_OK",0)
        self.__gdata.update("WW","V_ladepumpe",0)
        self.__gdata.update("WW","V_zirkula_pumpe",0)
        self.__gdata.update("WW","V_spare1",0)
        self.__gdata.update("WW","V_spare2",0)

        self.__gdata.update("SO","V_speichervoll",0)
        self.__gdata.update("SO","V_kollektoraus",0)
        self.__gdata.update("SO","V_spare1",0)
        self.__gdata.update("SO","V_spare2",0)
        
        
        self.__currentHK_nickname="HK1"

    def __IsTempInRange(self, tempvalue, maxvalue=300.0, minvalue = -50.0):
        return True if (float(tempvalue)<maxvalue and float(tempvalue)>minvalue) else False

    def __Check4MaxValue(self, nickname, item, value):
        #zs# print("maxvalue:{0};type:{1}".format(self.__gdata.maxvalue(nickname, item), type(self.__gdata.maxvalue(nickname, item))))
        if self.__gdata.maxvalue(nickname, item) != None:
            if value > self.__gdata.maxvalue(nickname, item):
                return self.__gdata.defaultvalue(nickname, item)
            else:
                return value
        else:
            return value
 
    ### Datum / Uhrzeit ##            
    def DatumUhrzeitMsg(self, buffer, length):
        nickname="DT"

        if self.crc_testen(buffer, length) == True:
            iyear      = int(buffer[4]+2000)
            imonth     = int(buffer[5])
            ihour      = int(buffer[6])
            iday       = int(buffer[7])
            iminute    = int(buffer[8])
            isecond    = int(buffer[9])
            idayofweek = int(buffer[10])

            self.__info_datum="""{day:02}.{month:02}.{year:4}""".format(day=iday,
                                                                   month=imonth,
                                                                   year=iyear)
            self.__info_zeit ="""{hour:02}:{minute:02}:{second:02}""".format(hour=ihour,
                                                                        minute=iminute,
                                                                        second=isecond)
            # update values
            self.__gdata.update(nickname,"Date",self.__info_datum)
            self.__gdata.update(nickname,"Time" ,self.__info_zeit)
            temptext=nickname+" :"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            return self.__gdata.values(nickname)
        else:
            return None
            

    ### Heizgeraet ##            
    def HeizgeraetMsg(self, buffer, length):
        nickname="HG"

        if self.crc_testen(buffer, length) == True:
            # default value for CSW-typed heater
            Heatertype=0x8000
            if (buffer[15]==0x80 and buffer[16]==0x00):
                # Heatertype := CSW-like
                Heatertype=0x8000
            elif (buffer[15]==0x7d and buffer[16]==0x00):
                # Heatertype := KUB-like
                 ## forced external length=33
                Heatertype=0x7d00
            else:
                # Heatertype := CSW-like
                Heatertype=0x8000
            
            i_tvorlauf_soll =int(buffer[4])
            f_tvorlauf_ist  =float(buffer[5]*256+ buffer[6])/10
            i_leistung      =int(buffer[8])
            ## Kesselbetriebsart Heizen:=0x5x, Warmwasser:=0x6x
            ## i_betriebsmodus =1 if bool((buffer[7] & 0x50) == 0x50) else 0
            #  21.04.2014; Aenderung auf Byte9/Bit1 und Bit2
            i_betriebsmodus=int(buffer[9] & 0x03)

            # Extract Bitfeld von Byte 9
            #
            #   Bitfeld: Bit7&8 nur fuer Warmwasser; (Bits von rechts gezaehlt - beginnt 1)
            #   Bit8: bis Bit5 immer 0
            #   Bit4: Brennerflamme an
            #   Bit3: immer 0
            #   Bit2: Warmwasser-Mode deaktiv/aktiv := 0/1
            #   Bit1: Heizungs  -Mode deaktiv/aktiv := 0/1
            b_brennerflamme= 1 if bool((buffer[9] & 0x08)) else 0
            
            f_tmischer  = float(buffer[13]*256+ buffer[14])/10
            f_truecklauf= float(buffer[17]*256+ buffer[18])/10
            # KUB-like heater, dieser hat keinen Mischer- und Ruecklauf-Fuehler.
            #    Statt dessen hat dieser einen Ansaugluft- und Abgasfuehler.
            #    Z.Zeit werden die Mischer-/Ruecklauf-Buffer als Speicherort genutzt.
            #    Die Gui muss den angezeigten Text korrigieren mit Informationen aus
            #    der Konfiguration.
            if Heatertype==0x7d00:
                f_tmischer  = float(buffer[19]*256+ buffer[20])/10
                f_truecklauf= float(buffer[29]*256+ buffer[30])/10
                
            # Extract Bitfeld von Byte 11
            #
            #   Bitfeld: Bit7&8 nur fuer Warmwasser; (Bits von rechts gezaehlt - beginnt 1)
            #   Bit8: Zirkulationspumpe Warmwasser
            #   Bit7: Speicherladepumpe Warmwasser
            #   Bit6: immer 1
            #   Bit5: immer 0
            #   Bit4: Zuendung des Brenners
            #   Bit3: waehrend Verbrennung 1 mit etwas laengerem Vor- und Nachlauf vgl. Bit8
            #   Bit2: immer 0
            #   Bit1: waehrend Verbrennung 1 mit kurzem Vor- und Nachlauf
            b_brenner       = 1 if(buffer[11] & 0x01) else 0
            b_heizungspumpe = 1 if(buffer[11] & 0x20) else 0
            b_speicherladepumpe= 1 if(buffer[11] & 0x40) else 0
            b_zirkulationspumpe= 1 if(buffer[11] & 0x80) else 0

            # update values
            self.__gdata.update(nickname,"Tvorlauf_soll",self.__Check4MaxValue(nickname,"Tvorlauf_soll",i_tvorlauf_soll))
            self.__gdata.update(nickname,"Tvorlauf_ist" ,self.__Check4MaxValue(nickname,"Tvorlauf_ist" ,f_tvorlauf_ist))
            self.__gdata.update(nickname,"Truecklauf",self.__Check4MaxValue(nickname,"Truecklauf",f_truecklauf))
            self.__gdata.update(nickname,"Tmischer",self.__Check4MaxValue(nickname,"Tmischer",f_tmischer))
            self.__gdata.update(nickname,"Vmodus",i_betriebsmodus)
            self.__gdata.update(nickname,"Vbrenner_motor",b_brenner)
            self.__gdata.update(nickname,"Vbrenner_flamme",b_brennerflamme)
            self.__gdata.update(nickname,"Vleistung",i_leistung)
            self.__gdata.update(nickname,"Vheizungs_pumpe",b_heizungspumpe)
            self.__gdata.update(nickname,"Vspeicher_pumpe",b_speicherladepumpe)
            self.__gdata.update(nickname,"Vzirkula_pumpe",b_zirkulationspumpe)
            ## only deactivation, is used now in 'HeizgeraetMsg2' self.__gdata.update(nickname,"V_spare1",0)
            self.__gdata.update(nickname,"V_spare2",0)
            temptext=nickname+" :"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            values=self.__gdata.values(nickname)
            return values
        else:
            return None
        
    ### Heizgeraetmessage2 ##            
    def HeizgeraetMsg2(self, buffer, length):
        nickname="HG"

        if self.crc_testen(buffer, length) == True:
            if buffer[4] != 255:
                f_tAussen=float(buffer[4]*256+buffer[5])/10
            else:
                f_tAussen=float(255-buffer[5])/-10

            i_betriebtotal_minuten  =int(buffer[17]*65536+ buffer[18]*256+ buffer[19])
            i_betriebheizung_minuten=int(buffer[23]*65536+ buffer[24]*256+ buffer[25])
            i_brenner_gesamt_ein    =int(buffer[14]*65536+ buffer[15]*256+ buffer[16])
            i_brenner_heizung_ein   =int(buffer[26]*65536+ buffer[27]*256+ buffer[28])

            self.__gdata.update(nickname,"Taussen",self.__Check4MaxValue(nickname,"Taussen",f_tAussen))
            self.__gdata.update(nickname,"Cbetrieb_gesamt",i_betriebtotal_minuten)
            self.__gdata.update(nickname,"Cbetrieb_heizung",i_betriebheizung_minuten)
            self.__gdata.update(nickname,"Cbrenner_gesamt",i_brenner_gesamt_ein)
            self.__gdata.update(nickname,"Cbrenner_heizung",i_brenner_heizung_ein)
            # Rev.: 0.1.7 https://www.mikrocontroller.net/topic/324673#3970615
            i_pumpenleistung   =int(buffer[13])
            self.__gdata.update(nickname,"V_spare1",i_pumpenleistung)
            self.__gdata.update(nickname,"V_spare2",0)
            temptext=nickname+" :"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)

            # update HG-values
            nickname="HG"
            values=self.__gdata.values(nickname)

            # Extra-handling fuer heizgeraete mit Warmwasser-Ladenpumpensteuerung
            #  Die WW-Betriebsminuten sind hier offensichlich in diesem Telegramm
            #  enthalten. Es werden die relevanten Bytes kopiert, die CRC berechnet
            #  und die Warmwasser-Methode aufgerufen
            #  Das erste Byte wird auf (7d)hex gesetzt um anzuzeigen, dass dies kein
            #  empfangenes WW-Telegramm sondern eine künstlich erzeugte Message ist.
            #
            #  Diese Bestimmung darf nur zu Testzwecken aktiviert werden und ist hier
            #!! -->> deaktiviert
            if (False and buffer[29]==0x7d and buffer[30]==0x00):
                # Heatertype := KUB-like
                localbuffer=[0 for x in range(30)]
                localbuffer[0]=0x7d
                localbuffer[4]=int((buffer[6]*256+ buffer[7])/10)
                localbuffer[5]=buffer[8]
                localbuffer[6]=buffer[9]
                # aktuelle speichertemperatur auslesen und hier zurueckrechnen
                #  damit alter Wert nicht mit 0 ueberschrieben wird
                speichertemp  =int(self.__gdata.values("WW","Tspeicher")*10)
                localbuffer[7]=int(speichertemp/256)
                localbuffer[8]=int(speichertemp-localbuffer[7]*256)
                localbuffer[12]=3  # <-- erzwungen auf 'WW-Speicher', noetig fuer Auswertung
                localbuffer[14]=buffer[20]
                localbuffer[15]=buffer[21]
                localbuffer[16]=buffer[22]
                localbuffer[21]=self.__make_crc(localbuffer, 23)
                self.WarmwasserMsg(localbuffer, 23)
                
            # return HG-values
            return values
        else:
            return None

    ### Heizkreismessage 11 byte ##            
    def HeizkreisMsg_FW100_200_11byte(self, buffer, length):
        nickname="HK1"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
#zs not yet decoded #                
            debugstr="cht3_decode.HeizkreisMsg_FW100_200_11byte();HK_11B;hex:{0}".format(temptext)
            self._logging.debug(debugstr)
            return None
        else:
            return None


    ### Heizkreismessage 17 byte ##            
    def HeizkreisMsg_FW100_200Msg(self, buffer, length):
        nickname="HK1"
        if self.crc_testen(buffer, length) == True:
            i_betriebsart   =int(buffer[6])
            f_Soll_HK   =float(buffer[8]*256+ buffer[9])/10
            f_Ist_HK    =float(buffer[10]*256+ buffer[11])/10
            f_Steuer_FB =float(buffer[12]*256+ buffer[13])/10
            if self.__IsTempInRange(f_Soll_HK) and self.__IsTempInRange(f_Ist_HK):
                nickname="HK1"
                self.__currentHK_nickname=nickname
                if buffer[5] == 111:
                    # //6F Heizkreis 1
                    nickname="HK1"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 112:
                    # //70 Heizkreis 2
                    nickname="HK2"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 113:
                    # //71 Heizkreis 3
                    nickname="HK3"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 114:
                    # //72 Heizkreis 4
                    nickname="HK4"
                    self.__currentHK_nickname=nickname

                # buffer[14] unbekannter Wert als "WW":V_spare1 gespeichert
                i_spare1=int(buffer[14])

                self.__gdata.update(nickname,"Vbetriebs_art",i_betriebsart)
                self.__gdata.update(nickname,"Tsoll_HK",f_Soll_HK)
                self.__gdata.update(nickname,"Tist_HK",self.__Check4MaxValue(nickname,"Tist_HK",f_Ist_HK))
                self.__gdata.update(nickname,"Tsteuer_FB",self.__Check4MaxValue(nickname,"Tsteuer_FB",f_Steuer_FB))
                self.__gdata.update(nickname,"V_spare1",i_spare1)
                self.__gdata.update(nickname,"V_spare2",0)
                temptext=nickname+":"
                for x in range (0,length):
                    temptext = temptext+" "+format(buffer[x],"02x")
                self.__gdata.update(nickname,"hexdump",temptext)
                
                values=self.__gdata.values(nickname)
                return values
            else:
                return None
        else:
            return None

    def HeizkreisMsg_FW100_200Msg_9byte(self, buffer, length):
        nickname="HK1"
        if self.crc_testen(buffer, length) == True:
            i_betriebsart   =int(buffer[6])
            nickname="HK1"
            self.__currentHK_nickname=nickname
            if buffer[5] == 111:
                # //6F Heizkreis 1
                nickname="HK1"
                self.__currentHK_nickname=nickname
            elif buffer[5] == 112:
                # //70 Heizkreis 2
                nickname="HK2"
                self.__currentHK_nickname=nickname
            elif buffer[5] == 113:
                # //71 Heizkreis 3
                nickname="HK3"
                self.__currentHK_nickname=nickname
            elif buffer[5] == 114:
                # //72 Heizkreis 4
                nickname="HK4"
                self.__currentHK_nickname=nickname

            self.__gdata.update(nickname,"Vbetriebs_art",i_betriebsart)
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            values=self.__gdata.values(nickname)
            return values
        else:
            return None

    ### Heizkreismessage 2 ##            
    def IPM_LastschaltmodulMsg(self, buffer, length, firstbyte):
        # select IPM-Modulnumber/BusCodierung ?? a0:=1; a1:=2; a2:=3; a3:=4
        #  A0/A3 -> IPM2 Modul 1/ 1;4 ??
        #  A1/A2 -> IPM2 Modul 2/ 2;3 ??
        
        if firstbyte == 0xa0:
            nickname="HK1"
        elif firstbyte == 0xa1:
            nickname="HK3"
        elif firstbyte == 0xa2:
            nickname="HK4"
        elif firstbyte == 0xa3:
            nickname="HK2"
        else:
            nickname="HK1"
            
        if self.crc_testen(buffer, length) == True:
            i_IPM_Byte6  =int(buffer[6])
            i_IPM_Byte7  =int(buffer[7])
            i_IPM_Mischerstellung =int(buffer[8])
            f_IPM_VorlaufTemp     =float(buffer[9]*256+ buffer[10])/10
            self.__gdata.update(nickname,"V_spare1",0)
            self.__gdata.update(nickname,"V_spare2",0)
            if self.__IsTempInRange(f_IPM_VorlaufTemp):
                self.__gdata.update(nickname,"VMischerstellung",i_IPM_Mischerstellung)
                self.__gdata.update(nickname,"Tvorlaufmisch_HK",self.__Check4MaxValue(nickname,"Tvorlaufmisch_HK",f_IPM_VorlaufTemp))
                temptext=nickname+":"
                for x in range (0,length):
                    temptext = temptext+" "+format(buffer[x],"02x")
                self.__gdata.update(nickname,"hexdump",temptext)
                values=self.__gdata.values(nickname)
                return values
            else:
                return None
        else:
            return None
        

    ### Heizkreismessage 3 (Fernbedienung FB10/FB100) 9x10FF00 wobei: x <- 8 bis F) ##            
    def HeizkreisMsg_FB1xyMsg(self, buffer, length):
        nickname="HK1"
        
        if self.crc_testen(buffer, length) == True:
            f_Steuer_FB =float(buffer[6]*256+ buffer[7])/10 # T-Raum
            f_Soll_HK   =float(buffer[8]/2)                 # Wert * 0.5 Grad
            i_T_warmkalt_abgleich=int(buffer[9])
            f_T_warmkalt_ableich_HK = float(i_T_warmkalt_abgleich/2)
            if i_T_warmkalt_abgleich > 0xf5:
                f_T_warmkalt_ableich_HK = -1*float((256 - i_T_warmkalt_abgleich)/2)
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.HeizkreisMsg_FB1xyMsg();FB1xyMsg; T-Raum:{0}; T-Soll:{1}; V-Ableich:{2}".format(f_Steuer_FB,f_Soll_HK,f_T_warmkalt_ableich_HK)
            self._logging.debug(debugstr)
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            values=self.__gdata.values(nickname)
            return values
        else:
            return None

    def HeizkreisMsg_FW100_200_14byte(self, buffer, length):
        nickname="HK1"
        if self.crc_testen(buffer, length) == True:
            i_betriebsart   =int(buffer[6])
            f_Soll_HK   =float(buffer[8]*256+ buffer[9])/10
            f_Ist_HK    =float(buffer[10]*256+ buffer[11])/10
            if self.__IsTempInRange(f_Soll_HK) and self.__IsTempInRange(f_Ist_HK):
                nickname="HK1"
                self.__currentHK_nickname=nickname
                if buffer[5] == 111:
                    # //6F Heizkreis 1
                    nickname="HK1"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 112:
                    # //70 Heizkreis 2
                    nickname="HK2"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 113:
                    # //71 Heizkreis 3
                    nickname="HK3"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 114:
                    # //72 Heizkreis 4
                    nickname="HK4"
                    self.__currentHK_nickname=nickname

                self.__gdata.update(nickname,"Vbetriebs_art",i_betriebsart)
                self.__gdata.update(nickname,"Tsoll_HK",f_Soll_HK)
                self.__gdata.update(nickname,"Tist_HK",self.__Check4MaxValue(nickname,"Tist_HK",f_Ist_HK))
                temptext = nickname+":"
                for x in range (0,length):
                    temptext = temptext+" "+format(buffer[x],"02x")
                self.__gdata.update(nickname,"hexdump",temptext)
                
                values = self.__gdata.values(nickname)
                return values
            else:
                return None
        else:
            return None


    def HeizkreisMsg_ID677_max33byte(self, buffer, length):
        if self.crc_testen(buffer, length) == True:
            #check bytes for msg-ID:=677
            if (buffer[4] == 1 and buffer[5] == 0xa5):
                i_betriebsart   =int(buffer[27])
                f_Ist_HK    =float(buffer[6]*256+ buffer[7])/10
                f_Soll_HK   =float(buffer[12] / 2)
                nickname="HK1"
                self.__currentHK_nickname=nickname
                if buffer[5] == 165:
                    # //A5 Heizkreis 1
                    nickname="HK1"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 166:
                    # //A6 Heizkreis 2
                    nickname="HK2"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 167:
                    # //A7 Heizkreis 3
                    nickname="HK3"
                    self.__currentHK_nickname=nickname
                elif buffer[5] == 168:
                    # //A8 Heizkreis 4
                    nickname="HK4"
                    self.__currentHK_nickname=nickname

                self.__gdata.update(nickname,"Vbetriebs_art",i_betriebsart)
                self.__gdata.update(nickname,"Tsoll_HK",f_Soll_HK)
                self.__gdata.update(nickname,"Tist_HK",self.__Check4MaxValue(nickname,"Tist_HK",f_Ist_HK))
                temptext = nickname+":"
                for x in range (0,length):
                    temptext = temptext+" "+format(buffer[x],"02x")
                self.__gdata.update(nickname,"hexdump",temptext)
                values = self.__gdata.values(nickname)
                return values
            else:
                return None
        else:
            return None


    def IPM_LastschaltmodulWWModeMsg(self, buffer, length):
        # 0.1.8.2 modification for wrong detection, see:
        # https://www.mikrocontroller.net/topic/324673#4466160
        nickname="WW"
        if ((self.crc_testen(buffer, length) == True) and (buffer[length-1] == 0)):
            i_Soll=int(buffer[4])
            f_Ist              = float(buffer[5]*256+ buffer[6])/10
            f_WWSpeicherextern = float(buffer[7]*256+ buffer[8])/10
            i_Ladepumpe=1 if (buffer[9]&0x08) else 0

            self.__gdata.update(nickname,"Tsoll",self.__Check4MaxValue(nickname,"Tsoll",i_Soll))
            self.__gdata.update(nickname,"Tist",self.__Check4MaxValue(nickname,"Tist",f_Ist))
            self.__gdata.update(nickname,"Tspeicher",self.__Check4MaxValue(nickname,"Tspeicher",f_WWSpeicherextern))
            self.__gdata.update(nickname,"Vladepumpe", i_Ladepumpe)
            self.__gdata.update(nickname,"V_spare1",0)
            self.__gdata.update(nickname,"V_spare2",0)
            temptext=nickname+" :"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            values=self.__gdata.values(nickname)
            return values
        else:
            return None

    def CurrentHK_Nickname(self):
        return self.__currentHK_nickname        

    def WarmwasserMsg(self, buffer, length):
        nickname="WW"
        
        if self.crc_testen(buffer, length) == True:
            # Art der Warmwasserzeugung durch Brenner;
            #  0 :=> hat keine eigene WW-Erzeugung/Umschaltung, siehe Doku
            if buffer[12] == 0:
                # keine direkte Warmwasser-Bereitung durch heater,
                # daher wird dieses Telegramm nicht gesendet bzw. falls
                # doch, die Werte auf 0 erzwungen.
                i_Soll         =0
                f_Ist          =0.0
                f_Speicheroben =0.0
                i_betriebszeit =0
                i_WW_einmallad =0
                i_WW_desinfekt =0
                i_WW_erzeugung =0
                i_WW_nachladung=0
                i_WW_temp_OK   =0
                i_lade_pump_ein=0
                i_zirkula_pump_ein=0
            else:
                i_Soll         =int(buffer[4])
                f_Ist          =float(buffer[5]*256+ buffer[6])/10
                f_Speicheroben =float(buffer[7]*256+ buffer[8])/10
                i_betriebszeit =int(buffer[14]*65536+ buffer[15]*256+ buffer[16])
                i_brennerww_ein=int(buffer[17]*65536+ buffer[18]*256+ buffer[19])
                # Bitfelder von Byte9 und Byte11
                i_WW_einmallad    =1 if(buffer[9]&0x02) else 0
                i_WW_desinfekt    =1 if(buffer[9]&0x04) else 0
                i_WW_erzeugung    =1 if(buffer[9]&0x08) else 0
                i_WW_nachladung   =1 if(buffer[9]&0x10) else 0
                i_WW_temp_OK      =1 if(buffer[9]&0x20) else 0
                i_lade_pump_ein   =1 if(buffer[11]&0x08) else 0
                i_zirkula_pump_ein=1 if(buffer[11]&0x04) else 0


            # update values
            self.__gdata.update(nickname,"Tsoll",self.__Check4MaxValue(nickname,"Tsoll",i_Soll))
            self.__gdata.update(nickname,"Tist",self.__Check4MaxValue(nickname,"Tist",f_Ist))
            self.__gdata.update(nickname,"Tspeicher",self.__Check4MaxValue(nickname,"Tspeicher",f_Speicheroben))
            self.__gdata.update(nickname,"Cbetriebs_zeit",i_betriebszeit)
            self.__gdata.update(nickname,"Cbrenner_ww",i_brennerww_ein)
            self.__gdata.update(nickname,"VWW_einmalladung",i_WW_einmallad)
            self.__gdata.update(nickname,"VWW_desinfekt",i_WW_desinfekt)
            self.__gdata.update(nickname,"VWW_erzeugung",i_WW_erzeugung)
            self.__gdata.update(nickname,"VWW_nachladung",i_WW_nachladung)
            self.__gdata.update(nickname,"VWW_temp_OK",i_WW_temp_OK)
            self.__gdata.update(nickname,"V_lade_pumpe",i_lade_pump_ein)
            self.__gdata.update(nickname,"V_zirkula_pumpe",i_zirkula_pump_ein)
            self.__gdata.update(nickname,"V_spare1",0)
            self.__gdata.update(nickname,"V_spare2",0)
            
            temptext=nickname+" :"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            return self.__gdata.values(nickname)
        else:
            return None

 
    ### Solarmessage ##            
    def SolarMsg(self, buffer, length):
        nickname="SO"

        if self.crc_testen(buffer, length) == True:
            f_kollektor    =0.0
            f_speicherunten=0.0
            i_ertrag_letztestunde=0
            i_ertrag_2     =0
            b_pumpe        =0
            i_laufzeit_minuten=0
            i_laufzeit_stunden=0
            i_speicher_voll=0
            i_kollektor_aus=0
            
            # solar-msgtype := 3 handling
            if buffer[5] == 3:
                # Solarkreis1
                if buffer[10] != 255:
                    f_kollektor     =float(buffer[10]*256+ buffer[11])/10
                    f_speicherunten =float(buffer[12]*256+ buffer[13])/10
                else:
                    f_kollektor     = float(255 - buffer[11])/(-10)
                    f_speicherunten = float(buffer[12]*256+ buffer[13])/10

                # Auswertung eines ertrages, zuordnung noch TBD  Bytes: 6-7
                i_ertrag_2 = int(buffer[6]*256+ buffer[7])
                # Auswertung der Solarertrag letzte Stunde Bytes: 8-9
                i_ertrag_letztestunde =int(buffer[8]*256+ buffer[9])
                b_pumpe = 1 if (buffer[14] & 0x01) else 0

                # Auswertung der Solarlaufzeiten
                i_laufzeit_minuten =int(buffer[17]*256+buffer[18])
                i_laufzeit_stunden =int(i_laufzeit_minuten/60)

                # Auswertung Solar Systemstatus
                i_kollektor_aus=1 if(buffer[15] & 0x01) else 0
                i_speicher_voll=1 if(buffer[15] & 0x04) else 0

                # update values
                self.__gdata.update(nickname,"Tkollektor",self.__Check4MaxValue(nickname,"Tkollektor",f_kollektor))
                self.__gdata.update(nickname,"Tspeicher_unten",self.__Check4MaxValue(nickname,"Tspeicher_unten",f_speicherunten))
                self.__gdata.update(nickname,"V_ertrag_stunde",i_ertrag_letztestunde)
                self.__gdata.update(nickname,"V_ertrag_2",i_ertrag_2)
                self.__gdata.update(nickname,"Vsolar_pumpe",b_pumpe)
                self.__gdata.update(nickname,"Claufzeit",i_laufzeit_minuten)
                self.__gdata.update(nickname,"Vkollektor_aus",i_kollektor_aus)
                self.__gdata.update(nickname,"Vspeicher_voll",i_speicher_voll)
                self.__gdata.update(nickname,"V_spare1",0)
                self.__gdata.update(nickname,"V_spare2",0)

            # solar-msgtype := 4 handling
            if buffer[5] == 4:
                f_t41 =float(buffer[6]*256+ buffer[7])/10
                f_t42 =float(buffer[8]*256+ buffer[9])/10
                # enable 'debug'-logging for test ->
                debugstr="cht3_decode.SolarMsg();SO : T41:{0}, T42:{1}".format(f_t41, f_t42)
                self._logging.debug(debugstr)
                # update values
                self.__gdata.update(nickname,"Thybrid_buffer",f_t41)
                self.__gdata.update(nickname,"Thybrid_sysinput",f_t42)
                
            temptext=nickname+" :"
            for x in range (0,length):
                temptext = temptext+" "+format(buffer[x],"02x")
            self.__gdata.update(nickname,"hexdump",temptext)
            return self.__gdata.values(nickname)
        else:
            return None

    ### Requestmessage ##            
    def RequestMsg(self, buffer, length):
        # keine Auswertung
        return None

#zs ####################################
#   still under development
#
    ### Modem message 1 ##            
    def Modem_1(self, buffer, length):
        nickname="MO1"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_1();{0};F#xy !;T-setup:{1};mode:{2:02X};value:{3:02X}".format(temptext, float(buffer[6]/2),buffer[3],buffer[5])
            self._logging.debug(debugstr)
            return None

    ### Modem message 2 ##            
    def Modem_2(self, buffer, length):
        nickname="MO2"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_2();{0};F#xy !;T-setup:{1};mode:{2:02X};value:{3:02X};Auto-Mode".format(temptext, float(buffer[6]/2),buffer[3],buffer[5])
            self._logging.debug(debugstr)
            return None
        
    ### Modem message 3 ##            
    def Modem_3(self, buffer, length):
        nickname="MO3"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_3();{0};FBxy !;T-setup:{1};mode:{2:02X};value:{3:02X}".format(temptext, float(buffer[6]/2),buffer[3],buffer[5])
            self._logging.debug(debugstr)
            return None

    ### Modem message 4 ##            
    def Modem_4(self, buffer, length):
        nickname="MO4"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_4();{0};FBxy !;T-setup:{1};mode:{2:02X};value:{3:02X}".format(temptext, float(buffer[6]/2),buffer[3],buffer[5])
            self._logging.debug(debugstr)
            return None

    ### Modem message 5 ##            
    def Modem_5(self, buffer, length):
        nickname="MO5"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_5();{0};F#xy ?;Question:{1}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[6])
            self._logging.debug(debugstr)
            return None

    ### Modem message 6 ##            
    def Modem_6(self, buffer, length):
        nickname="MO6"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_6();{0};F#xy ?;Question:{1}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[6])
            self._logging.debug(debugstr)
            return None
                      
    ### Modem message 7 ##            
    def Modem_7(self, buffer, length):
        nickname="MO7"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_7();{0};F#xy !;V1:{1}  V2:{4}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[5],buffer[6])
            self._logging.debug(debugstr)
            return None
                      
    ### Modem message 8 ##            
    def Modem_8(self, buffer, length):
        nickname="MO8"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_8();{0};F#xy !;V1:{1}  V2:{4}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[5],buffer[6])
            self._logging.debug(debugstr)
            return None
                      
    ### Modem message 9 ##            
    def Modem_9(self, buffer, length):
        nickname="MO9"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_8();{0};F#xy ?;Question:{1}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[6])
            self._logging.debug(debugstr)
            return None

    ### Modem MB-Lan message 1 ##            
    def Modem_MB_1(self, buffer, length):
        nickname="MB1"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_MB_1();{0};F#xy ?;Question:{1}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[6])
            self._logging.debug(debugstr)
            return None

    def Modem_MB_2(self, buffer, length):
        nickname="MB2"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_MB_2();{0};F#xy ?;Question:{1}  ;mode:{2:02X};value:{3:02X}".format(temptext, buffer[4],buffer[3],buffer[6])
            self._logging.debug(debugstr)
            return None

    def Modem_MB_3(self, buffer, length):
        nickname="MB3"
        if self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
#            print("{0};{1};F#xy ?;Question:{2}  ;mode:{3:02X};value:{4:02X}".format(zeit, temptext, buffer[4],buffer[3],buffer[6]))
            # enable 'debug'-logging for test ->
            debugstr="cht3_decode.Modem_MB_3();{0};FBxy !;T-setup:{1};mode:{2:02X};Spar-Mode".format(temptext, float(buffer[6]/2),buffer[3])
            self._logging.debug(debugstr)
            return None

    def Modem_MB_4(self, buffer, length):
        nickname="MB4"
##        print("{0};CRC calculated:{1:02X}".format(nickname,self.__make_crc(buffer, length)))
##ZS    ## CRC check hier immer falsch ???? obwohl laenge mit 8 zeichen richtig ist
        ## deshalb CRC-check deaktiviert
        if True or self.crc_testen(buffer, length) == True:
            temptext=nickname+":"
            for x in range (0,length):
                temptext = temptext+";"+format(buffer[x],"02x")
            # check valid range for temperatur
            if (buffer[5] > 20 and buffer[5] < 80):
                debugstr="cht3_decode.Modem_MB_4();{0};FBxy !;T-setup:{1};mode:{2:02X};Frost-Mode".format(temptext, float(buffer[5]/2),buffer[3])
            else:
                debugstr="cht3_decode.Modem_MB_4();{0};FBxy !;           ;mode:{1:02X};Frost-Mode".format(temptext, buffer[3])

            # enable 'debug'-logging for test ->
            self._logging.debug(debugstr)
            return None


                      
#--- class cht3_decode end ---#
################################################

if __name__ == "__main__":
    print("----- do some checks -----")
    import data
    g_data=data.cdata()
    g_data.read_db_config("./../etc/config/HT3_db_cfg.xml")

    HT3_decode=cht3_decode(g_data)
    print("-- check with valid 'heizgeraet' Message 1 --")
    # Heizgeraet
    # HG: 88 00 18 00 27 01 31 54 00 01 03 20 c0 01 c5 80
    #     00 01 2c ff ff ff 00 00 00 00 00 00 00 e9 00
    length=31
    heizgeraet = [ \
       0x88, 0x00 ,0x18, 0x00, 0x27, 0x01, 0x31, 0x54,
       0x00, 0x01, 0x03, 0x20, 0xC0, 0x01, 0xC5, 0x80,
       0x00, 0x01, 0x2C, 0xFF, 0xFF, 0xFF, 0x00, 0x00,
       0x00, 0x00, 0x00, 0x00, 0x00, 0xE9, 0x00]
    values=HT3_decode.HeizgeraetMsg(heizgeraet, length)
    print(values)
    print("+-> OK") if values[3]==45.3 else print("+-> Error")
    print("-- check with valid 'heizgeraet' Message 2 --")
    # Heizgeraetmessage 2
    # HK: 88 00 19 00 ff fc 80 00 80 00 ff ff 00 41 00 15
    #     fa 02 97 fd 00 00 00 02 5d 3d 00 0b 51 80 00 d5 00
    length=33
    heizgeraettestbuffer2 = [ \
       0x88, 0x00 ,0x19, 0x00, 0xFF, 0xFC, 0x80, 0x00,
       0x80, 0x00, 0xFF, 0xFF, 0x00, 0x41, 0x00, 0x15,
       0xFA, 0x02, 0x97, 0xFD, 0x00, 0x00, 0x00, 0x02,
       0x5D, 0x3D, 0x00, 0x0B, 0x51, 0x80, 0x00, 0xD5, 0x00]
    values=HT3_decode.HeizgeraetMsg2(heizgeraettestbuffer2, length)
    print(values)
    print("+-> OK") if values[12]== 169981 else print("+-> Error")
    
    print("-- check with valid 'heizkreis'  Message 1 --")
    # Heizkreismessage
    # HK: 90 00 ff 00 00 6f 03 02 00 d7 00 e1 00 d8 00 23 00    
    length=17
    heizkreistestbuffer = [ \
       0x90, 0x00 ,0xFF, 0x00, 0x00, 0x6F, 0x03, 0x02,
       0x00, 0xD7, 0x00, 0xE1, 0x00, 0xD8, 0x00, 0x23, 0x00]
    values=HT3_decode.HeizkreisMsg_FW100_200Msg(heizkreistestbuffer, length)
    print(values)
    print("+-> OK") if values[2]==21.6 else print("+-> Error")
    print("-- check with valid 'heizkreis'  Message 2 --")
    # Heizkreismessage 2
    # HK: a0 00	ff 00 00 0c 02 05 00 01 11 1c 5e 00
    length=14
    heizkreistestbuffer2 = [ \
       0xA0, 0x00 ,0xFF, 0x00, 0x00, 0x0C, 0x02, 0x05,
       0x00, 0x01, 0x11, 0x1C, 0x5E, 0x00]
    IPMModul=1
    values=HT3_decode.IPM_LastschaltmodulMsg(heizkreistestbuffer2, length, IPMModul)
    print(values)
    print("+-> OK") if values[5]==27.3 else print("+-> Error")
    print("-- check with valid 'heizkreis'  Message 3 --")
    # Heizkreismessage 3
    # HK: a1 00 ff 00 00 0c 02 01 35 01 36 26 13 00
    heizkreistestbuffer3 = [ \
       0xA1, 0x00 ,0xFF, 0x00, 0x00, 0x0C, 0x02, 0x01,
       0x35, 0x01, 0x36, 0x26, 0x13, 0x00]
    IPMModul=2
    values=HT3_decode.IPM_LastschaltmodulMsg(heizkreistestbuffer3, length, IPMModul)
    print(values)
    print("+-> OK") if values[4]==53 else print("+-> Error")
    
    print("-- check with valid 'warmwasser' Message --")
    # Warmwassermessage
    # WW: 88 00 34 00 32 01 c1 01 bd a1 00 04 03 00 00 3a c0
    #     00 0a a9 00 4a 00
    length=23
    warmwassertestbuffer = [ \
       0x88, 0x00 ,0x34, 0x00, 0x32, 0x01, 0xC1, 0x01,
       0xBD, 0xA1, 0x00, 0x04, 0x03, 0x00, 0x00, 0x3A,
       0xC0, 0x00, 0x0A, 0xA9, 0x00, 0x4A, 0x00]
    values=HT3_decode.WarmwasserMsg(warmwassertestbuffer, length)
    print(values)
    print("+-> OK") if values[3]==15040 else print("+-> Error")

    print("-- check with valid 'solar'      Message --")
    # SO: b0 00 ff 00 00 03 00 00 00 00 00 38 00 fd 00 00
    #     00 42 70 b1 00
    length=21
    solartestbuffer = [ \
       0xB0, 0x00 ,0xFF, 0x00, 0x00, 0x03, 0x00, 0x00,
       0x00, 0x00, 0x00, 0x38, 0x00, 0xFD, 0x00, 0x00,
       0x00, 0x42, 0x70, 0xB1, 0x00]
    values=HT3_decode.SolarMsg(solartestbuffer, length)
    print(values)
    print("-------------------- check with wrong values -----------------------------------")
    print("-- check with wrong length on 'solar' Message --")
    values=HT3_decode.SolarMsg(solartestbuffer, length-1)
    print("+->CRC-check:OK\n") if values==None else print("+->CRC-check:Error\n")
    print("---  check exception-handling with wrong length ---")
    values=HT3_decode.SolarMsg(solartestbuffer, length+10)
    print("---  check exception-handling with no (empty) data-struct ---")
    empty_data=data.cdata()
    wrong_HT3_decode=cht3_decode(empty_data)
    wrong_HT3_decode.SolarMsg(solartestbuffer, length)
    print("---  check exception-handling with wrong type-call ---")
    print("---    !!!!! Traceback must occure !!!!! ---")
    HT3_decode=cht3_decode("wrong Type")

