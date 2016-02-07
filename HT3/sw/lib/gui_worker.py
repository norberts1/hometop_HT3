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
# Ver:0.1.6  / Datum 10.01.2015
# Ver:0.1.7.1/ Datum 04.03.2015 'heizungspumpenleistung' added
#              https://www.mikrocontroller.net/topic/324673#3970615
#              logging from ht_utils added
# Ver:0.1.8  / Datum 07.02.2016 HeizkreisMsg_ID677_max33byte added
#                                 for CWxyz handling
#################################################################
#
""" Class 'gui_cworker' for creating HT3 - Graphical User Interface (GUI)

gui_cworker.__init__    -- constructor of class 'gui_cworker'. this will main-object to tkinter.Tk and frames
                             mandatory: parameter 'gdata' as handle to cdata object
                             optional : hexdump_window  (default is value 'True')
run                     -- main loop to start GUI endless
                             mandatory: none
                             
"""

import sys, tkinter, time
import _thread, os
import data
import ht_utils, logging

__author__  = "Norbert S <junky-zs@gmx.de>"
__status__  = "draft"
__version__ = "0.1.8"
__date__    = "7 Februar 2016"

class gui_cworker(ht_utils.clog):
    def __init__(self, gdata, hexdump_window=True, titel_input="ASYNC", logger=None):
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging=ht_utils.clog.create_logfile(self, logfilepath="./gui_cworker.log", loggertag="gui_cworker")
            else:
                self._logging=logger
            
            if not isinstance(gdata, data.cdata):
                errorstr="gui_cworker;Error;TypeError:gdata"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            if not (isinstance(hexdump_window, int) or isinstance(hexdump_window, bool)):
                errorstr="gui_cworker;Error;TypeError:hexdump_window"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            self.__gdata  = gdata
            self.__current_display="system"
            self.__hexdump_window =hexdump_window
            self.__threadrun=True
            self.__info_calledfirsttime=True

            self.__main = tkinter.Tk()
            self.__gui_titel_input = titel_input

            # Frame 1,2,3 with Buttons 
            self.__fr1 = tkinter.Frame(self.__main, relief="sunken", bd=5)
            self.__fr1.pack(side="top")
            if self.__hexdump_window :
                self.__main.title('Heatronic Analyser Rev:{0} (Input:{1})'.format(__version__, self.__gui_titel_input))
                self.__main.geometry("1000x800+330+230")
                self.__fr2 = tkinter.Frame(self.__fr1, relief="sunken", bd=2)
                self.__fr2.pack(side="left")
            else:
                self.__main.title('Heatronic Systemstatus Rev:{0} (Input:{1})'.format(__version__, self.__gui_titel_input))
                self.__main.geometry("550x750+330+230")
                self.__fr2 = None
                
            self.__fr3 = tkinter.Frame(self.__fr1, relief="sunken", bd=3)
            self.__fr3.pack(side="right")

            if self.__hexdump_window :
                self.__bhexdclear = tkinter.Button(self.__fr2, text="Hexdump clear",
                                                highlightbackground="red",
                                                command = self.__hexclear)
                self.__bhexdclear.pack(padx=5, pady=5, side="left")
                
                self.__bende = tkinter.Button(self.__fr2, text = "Ende",
                                            highlightbackground="black",
                                            command = self.__ende)
                self.__bende.pack(padx=5, pady=5, side="right")
                self.__bende = tkinter.Button(self.__fr2, text = "Info",
                                            highlightbackground="black",
                                            command = self.__info)
                self.__bende.pack(padx=5, pady=5, side="right")
            else:
                self.__bende = tkinter.Button(self.__fr3, text = "Ende",
                                            highlightbackground="black",
                                            command = self.__ende)
                self.__bende.pack(padx=5, pady=5, side="right")
                
            self.__bsys = tkinter.Button(self.__fr3, text="System",
                                         highlightbackground="yellow",
                                         command = self.__system_button)
            self.__bsys.pack(padx=5, pady=5, side="left")
            self.__bhge = tkinter.Button(self.__fr3, text="Heizgeraet",
                                         highlightbackground="orange",
                                         command = self.__Heizgeraet_button)
            self.__bhge.pack(padx=5, pady=5, side="left")
            self.__bhkr = tkinter.Button(self.__fr3,text="Heizkreis",
                                         highlightbackground="moccasin",
                                         command = self.__Heizkreis_button)
            self.__bhkr.pack(padx=5, pady=5, side="left")
            self.__bwwa = tkinter.Button(self.__fr3, text="Warmwasser",
                                         highlightbackground="lightblue",
                                         command = self.__Warmwasser_button)
            self.__bwwa.pack(padx=5, pady=5, side="left")
            self.__bsola = tkinter.Button(self.__fr3, text="Solar",
                                         highlightbackground="lightgreen",
                                          command = self.__Solar_button)
            self.__bsola.pack(padx=5, pady=5, side="left")

            self.__g_i_hexheader_counter=0
            if self.__hexdump_window :
                #frame for hexdump
                self.__hexdumpfr = tkinter.Frame(self.__main, width=1000, relief="sunken", bd=1)
                self.__hexdumpfr.pack(side="left", expand=1, fill="both")
                self.__hextext = tkinter.Text(self.__hexdumpfr)
                self.__hextext.pack(side="left", expand=1, fill="both")
                self.__colourconfig(self.__hextext)
                self.__Hextext_bytecomment()

            #frame for data
            self.__datafr = tkinter.Frame(self.__main, width=1, relief="sunken", bd=4)
            self.__datafr.pack(side="left", fill="both")
            self.__text = tkinter.Text(self.__datafr)
            self.__text.pack(side="left", expand=1, fill="both")
            self.__colourconfig(self.__text)

            #browser-details
            self.__browsername=""
            self.__browser_found=False
            self.__search4browser()
        
        except (TypeError) as e:
            errorstr='gui_cworker();Error;Parameter:<{0}> has wrong type'.format(e.args[0])
            self._logging.critical(errorstr)
            raise TypeError(errorstr)
        
    def __del__(self):
        pass


    def __search4browser(self):
        self.__browser_found=False
        for browsername in ("dillo","midori","firefox","iceweasel"):
            cmd="which "+browsername
            rtnliste=list(os.popen(cmd))
            for name in rtnliste:
                if browsername in name:
                    self.__browsername=browsername
                    self.__browser_found=True
                    return

    def run(self):
        # start thread for updating display
        _thread.start_new_thread(self.__anzeigethread, (0,))
        # run endless
        while self.__threadrun:
            self.__main.mainloop()
        return False

    def __anzeigethread(self, parameter):
        self.__cleardata()
        while self.__threadrun:
            self.__anzeigesteuerung()
            if self.__threadrun:
                time.sleep(1)
            else:
                break
            
    def __ende(self):
        self.__threadrun=False
        self.__main.destroy()

    def __info(self):
        if self.__browser_found:
            if __name__ == "__main__":
                cmd=self.__browsername+" ./../etc/html/HT3-Bus_Telegramme.html"
            else:
                cmd=self.__browsername+" ./etc/html/HT3-Bus_Telegramme.html"
            os.popen(cmd)
                
            if self.__info_calledfirsttime==True:
                time.sleep(3)
                self.__info_calledfirsttime=False
            
            
    def __IsTemperaturValid(self, tempvalue):
        return True if float(tempvalue) < 300.0 else False

    def __IsTemperaturInValidRange(self, tempvalue):
        return True if (float(tempvalue) < 300.0 and float(tempvalue) != 0.0) else False
    
    def __IsValueNotZero(self, tempvalue):
        return True if (int(tempvalue) != 0 and float(tempvalue) != 0.0) else False

    def __DisplayColumn(self, nickname, itemname, value=None):
        Column=""
        try:
            tmptext=self.__gdata.displayname(nickname,itemname)
            if len(tmptext)>0:
                if value==None:
                    Column=" {0:21.21}: {1} {2}\n".format(tmptext,
                                                        self.__gdata.displayvalue(nickname,itemname),
                                                        self.__gdata.displayunit(nickname,itemname))
                else:
                    Column=" {0:21.21}: {1} {2}\n".format(tmptext,
                                                        value,
                                                        self.__gdata.displayunit(nickname,itemname))
            else:
                Column=""
                
        except:
            errorstr="""gui_cworker.__DisplayColumn();Error;display-name/unit are not available
                       for nickname:{0};itemname:{1}""".format(nickname,itemname)
            print(errorstr)
            self._logging.critical(errorstr)
            
        return Column
            
    def __system_button(self):
        self.__current_display="system"
        self.__clear()
        self.__System()

        
    def __System(self):
        temptext="{0:13.13}: {1}\n".format("Systemstatus","Junkers Heatronic")
        self.__text.insert("end", temptext,"b_ye")
        self.__Info()
        self.__Heizgeraet()
        self.__Heizkreis()
        self.__Warmwasser()
        self.__Solar()
        self.__text.insert("end", "                                 \n","u")

    def __Info(self):
        nickname="DT"
        self.__text.insert("end", "System-Infos                     \n","b_gray")
        datum  =""" {0:12.12}: {1:11.11}| Aktuelles Datum: {2:11.11} \n""".format(self.__gdata.displayname(nickname,"Date"),
                                                                                self.__gdata.values(nickname,"Date"),
                                                                                time.strftime("%d.%m.%Y"))
        self.__text.insert("end", datum)
        uhrzeit=""" {0:12.12}: {1:11.11}| Aktuelle  Zeit : {2:11.11} \n""".format(self.__gdata.displayname(nickname,"Time"),
                                                                                self.__gdata.values(nickname,"Time"),
                                                                                time.strftime("%H:%M:%S"))
        self.__text.insert("end", uhrzeit)
        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext=self.__gdata.values(nickname,"hexdump")
            temptext+="\n"
            self.__hextext.insert("end",temptext,"b_gray")

    def __cleardata(self):
        # dummy-read to clear flags
        self.__gdata.IsSyspartUpdate("HG")
        self.__gdata.IsSyspartUpdate("HK1")
        self.__gdata.IsSyspartUpdate("HK2")
        self.__gdata.IsSyspartUpdate("HK3")
        self.__gdata.IsSyspartUpdate("HK4")
        self.__gdata.IsSyspartUpdate("WW")
        self.__gdata.IsSyspartUpdate("SO")
        self.__gdata.IsSyspartUpdate("DT")
        
    def __systempart_text(self, nickname):
        systempartname=self.__gdata.getlongname(nickname).upper()
        if "HK" in nickname:
            # heizkreis-nummer am Ende entfernen und 'E' dranhaengen falls noetig
            systempartname=systempartname[:len(systempartname)-1]
            if self.__gdata.heatercircuits_amount()>1:
                systempartname=systempartname+"E"
            
        temptext="{0:13.13}: {1}\n".format("Systempart", systempartname)
        self.__text.insert("end", temptext,"b_ye")
        

    def __Heizgeraet_button(self):
        nickname="HG"
        # dummy-read to clear flag
        self.__gdata.IsSyspartUpdate(nickname)
        self.__current_display=str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Heizgeraet()

    def __Heizgeraet(self):
        nickname="HG"
        temptext="{0:21.21} ({1})\n".format("Heizgeraet", self.__gdata.hardwaretype(nickname))
        self.__text.insert("end", temptext,"b_or")
        tempvalue=format(float(self.__gdata.values(nickname,"Taussen")),".1f")
        temptext =self.__DisplayColumn(nickname,"Taussen",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)

        tempvalue=format(int(self.__gdata.values(nickname,"Tvorlauf_soll")),"2d")
        temptext =self.__DisplayColumn(nickname,"Tvorlauf_soll",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)

        tempvalue=format(float(self.__gdata.values(nickname,"Tvorlauf_ist")),".1f")
        temptext =self.__DisplayColumn(nickname,"Tvorlauf_ist",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        Truecklauf=format(float(self.__gdata.values(nickname,"Truecklauf")),".1f")
        if self.__IsTemperaturValid(Truecklauf):
            temptext =self.__DisplayColumn(nickname,"Truecklauf",Truecklauf)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
        Tmischer=format(float(self.__gdata.values(nickname,"Tmischer")),".1f")
        if self.__IsTemperaturValid(Tmischer):
            temptext =self.__DisplayColumn(nickname,"Tmischer",Tmischer)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
        tempvalue=self.__GetStrBetriebsmodus(self.__gdata.values(nickname,"Vmodus"))
        temptext =self.__DisplayColumn(nickname,"Vmodus",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vbrenner_motor"))
        temptext =self.__DisplayColumn(nickname,"Vbrenner_motor",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vbrenner_flamme"))
        temptext =self.__DisplayColumn(nickname,"Vbrenner_flamme",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(int(self.__gdata.values(nickname,"Vleistung")),"d")
        temptext =self.__DisplayColumn(nickname,"Vleistung",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vheizungs_pumpe"))
        temptext =self.__DisplayColumn(nickname,"Vheizungs_pumpe",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        if not self.__gdata.IsLoadpump_WW():
            tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vzirkula_pumpe"))
            temptext =self.__DisplayColumn(nickname,"Vzirkula_pumpe",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vspeicher_pumpe"))
            temptext =self.__DisplayColumn(nickname,"Vspeicher_pumpe",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
        
        betrieb_gesamt_ein=int(self.__gdata.values(nickname,"Cbetrieb_gesamt"))
        tempvalue=format(betrieb_gesamt_ein,"d")+' Minuten := '+format(int(betrieb_gesamt_ein/60),".0f")+' Stunden'
        temptext =self.__DisplayColumn(nickname,"Cbetrieb_gesamt",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        betrieb_heizung_ein=int(self.__gdata.values(nickname,"Cbetrieb_heizung"))
        tempvalue=format(betrieb_heizung_ein,"d")+' Minuten := '+format(int(betrieb_heizung_ein/60),".0f")+' Stunden'
        temptext =self.__DisplayColumn(nickname,"Cbetrieb_heizung",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(int(self.__gdata.values(nickname,"Cbrenner_gesamt")),"d")
        temptext =self.__DisplayColumn(nickname,"Cbrenner_gesamt",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(int(self.__gdata.values(nickname,"Cbrenner_heizung")),"d")
        temptext =self.__DisplayColumn(nickname,"Cbrenner_heizung",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        # Rev.: 0.1.7 https://www.mikrocontroller.net/topic/324673#3970615
        tempvalue=format(int(self.__gdata.values(nickname,"Vspare1")))
        temptext =self.__DisplayColumn(nickname,"Vspare1",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)

        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext=self.__gdata.values(nickname,"hexdump")
            temptext+="\n"
            self.__hextext.insert("end",temptext,"b_or")

        
        if self.__current_display==str(self.__gdata.getlongname(nickname))  and self.__hexdump_window:
            self.__text.insert("end","\n")
            self.__text.insert("end","Nr. Msg-Header(hex) Systempart Hardware    Bemerkung\n","b_gray")
            self.__text.insert("end","1   88 00 18 00     Heizgeraet Steuermodul\n")
            self.__text.insert("end","2   88 00 19 00     Heizgeraet Steuermodul\n")
            self.__text.insert("end","\n")
            if self.__hexdump_window :
                self.__text.insert("end"," Details siehe 'Info'\n")


    def __Heizkreis_button(self):
        # dummy-read to clear flag
        for HeizkreisNummer in range (1, 5):
            nickname="HK"+str(HeizkreisNummer)
            self.__gdata.IsSyspartUpdate(nickname)
        nickname="HK1"
        self.__current_display=str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Heizkreis()

    def __Heizkreis(self):
        for HeizkreisNummer in range (1, self.__gdata.heatercircuits_amount()+1):
            nickname="HK"+str(HeizkreisNummer)
            ungemischt  =self.__gdata.GetUnmixedFlagHK(nickname).upper()
            ungemischt=True if ungemischt == "TRUE" else False
            buscodierung=self.__gdata.GetBuscodierungHK(nickname)
            if ungemischt:
                temptext="""{0}{1} ({2} ohne Mischer, Buscode:{3})\n""".format("Heizkreis",
                                                                                        HeizkreisNummer,
                                                                                        self.__gdata.hardwaretype(nickname),
                                                                                        buscodierung
                                                                                        )
                self.__text.insert("end", temptext,"b_mocca")
            else:
                temptext="""{0}{1} ({2}  mit Mischer, Buscode:{3})\n""".format("Heizkreis",
                                                                                        HeizkreisNummer,
                                                                                        self.__gdata.hardwaretype(nickname),
                                                                                        buscodierung
                                                                                        )
                self.__text.insert("end", temptext,"b_mocca")

               
            tempvalue=self.__GetStrBetriebsart(self.__gdata.values(nickname,"Vbetriebs_art"))
            temptext =self.__DisplayColumn(nickname,"Vbetriebs_art",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=format(float(self.__gdata.values(nickname,"Tsoll_HK")),".1f")
            temptext =self.__DisplayColumn(nickname,"Tsoll_HK",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=format(float(self.__gdata.values(nickname,"Tist_HK")),".1f")
            temptext =self.__DisplayColumn(nickname,"Tist_HK",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            TsteuerFB=float(self.__gdata.values(nickname,"Tsteuer_FB"))
            if self.__IsTemperaturInValidRange(TsteuerFB):
                tempvalue=format(TsteuerFB,".1f")
                temptext =self.__DisplayColumn(nickname,"Tsteuer_FB",tempvalue)
                if len(temptext)>0: self.__text.insert("end",temptext)
                
            if ungemischt==False:
                tempvalue=format(float(self.__gdata.values(nickname,"Tvorlaufmisch_HK")),".1f")
                temptext =self.__DisplayColumn(nickname,"Tvorlaufmisch_HK",tempvalue)
                if len(temptext)>0: self.__text.insert("end",temptext)
                
                tempvalue=format(int(self.__gdata.values(nickname,"VMischerstellung")),"d")
                temptext =self.__DisplayColumn(nickname,"VMischerstellung",tempvalue)
                if len(temptext)>0: self.__text.insert("end",temptext)

            if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
                temptext=self.__gdata.values(nickname,"hexdump")
                temptext+="\n"
                self.__hextext.insert("end",temptext,"b_mocca")


        nickname="HK1"
        if self.__current_display==str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end","\n")
            self.__text.insert("end","Nr. Msg-Header(hex) Systempart Hardware    Bemerkung\n","b_gray")
            self.__text.insert("end","1   90 00 FF 00     Heizkreis  Steuermodul\n")
            self.__text.insert("end","2   9x 00 FF 00     Heizkreis  FB10/FB100  Systemanhängig\n")
            self.__text.insert("end","                                           x := (8 ... F)\n")
            self.__text.insert("end","3   Ay 00 FF 00     Heizkreis  IPM1/IPM2   Systemanhängig\n")
            self.__text.insert("end","                                           y := (0 ... 7)\n")
            self.__text.insert("end","\n")
            if self.__hexdump_window :
                self.__text.insert("end"," Details siehe 'Info'\n")

    def __Warmwasser_button(self):
        nickname="WW"
        # dummy-read to clear flag
        self.__gdata.IsSyspartUpdate(nickname)
        self.__current_display=str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Warmwasser()

    def __Warmwasser(self):
        nickname="WW"
                
        temptext="{0:21.21} ({1})\n".format("Warmwasser", self.__gdata.hardwaretype(nickname))
        self.__text.insert("end", temptext,"b_bl")
        tempvalue=format(int(self.__gdata.values(nickname,"Tsoll")),"2d")
        temptext =self.__DisplayColumn(nickname,"Tsoll",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(float(self.__gdata.values(nickname,"Tist")),".1f")
        temptext =self.__DisplayColumn(nickname,"Tist",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(float(self.__gdata.values(nickname,"Tspeicher")),".1f")
        temptext =self.__DisplayColumn(nickname,"Tspeicher",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        betriebszeit=int(self.__gdata.values(nickname,"Cbetriebs_zeit"))
        if self.__IsValueNotZero(betriebszeit):
            tempvalue=format(betriebszeit,"d")+' Minuten := '+format(int(betriebszeit/60),".0f")+' Stunden'
            temptext =self.__DisplayColumn(nickname,"Cbetriebs_zeit",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)

        brenner_ww_ein_counter=int(self.__gdata.values(nickname,"Cbrenner_ww"))
        if self.__IsValueNotZero(brenner_ww_ein_counter):
            tempvalue=format(brenner_ww_ein_counter,"d")
            temptext =self.__DisplayColumn(nickname,"Cbrenner_ww",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
        
        if self.__gdata.IsLoadpump_WW():
            tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vladepumpe"))
            temptext =self.__DisplayColumn(nickname,"Vladepumpe",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vladepumpe"))
            temptext =self.__DisplayColumn(nickname,"Vladepumpe",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
        else:
            ##### Anzeigen teilweise noch deaktiv, da nicht schluessig, weitere Kontrolle erforderlich
            # temptext=" Zirkulationspumpe    : "+self.__GetStrOnOff(self.__gdata.values(nickname,"V_zirkula_pumpe"))+'\n'
            # self.__text.insert("end",temptext)
            # temptext=" Speicherladepumpe    : "+self.__GetStrOnOff(self.__gdata.values(nickname,"V_lade_pumpe"))+'\n'
            # self.__text.insert("end",temptext)
            ##
            tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"VWW_erzeugung"))
            temptext =self.__DisplayColumn(nickname,"VWW_erzeugung",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=self.__GetStrJaNein(self.__gdata.values(nickname,"VWW_temp_OK"))
            temptext =self.__DisplayColumn(nickname,"VWW_temp_OK",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"VWW_nachladung"))
            temptext =self.__DisplayColumn(nickname,"VWW_nachladung",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            ####
            # temptext=" Einmalladung         : "+self.__GetStrOnOff(self.__gdata.values(nickname,"VWW_einmalladung"))+'\n'
            # self.__text.insert("end",temptext)
            # temptext=" Desinfektion         : "+self.__GetStrOnOff(self.__gdata.values(nickname,"VWW_desinfekt"))+'\n'
            # self.__text.insert("end",temptext)
            ##
        
        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext=self.__gdata.values(nickname,"hexdump")
            temptext+="\n"
            self.__hextext.insert("end",temptext,"b_bl")
            
        if self.__current_display==str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end","\n")
            self.__text.insert("end","Nr. Msg-Header(hex) Systempart Hardware    Bemerkung\n","b_gray")
            self.__text.insert("end","1   88 00 34 00     Warmwasser Steuermodul\n")
            self.__text.insert("end","2   Ax 00 34 00     Warmwasser IPM1/IPM2   Systemanhängig\n")
            self.__text.insert("end","                                           x := (0 ... 7)\n")
            self.__text.insert("end","\n")
            if self.__hexdump_window :
                self.__text.insert("end"," Details siehe 'Info'\n")


    def __Solar_button(self):
        nickname="SO"
        # dummy-read to clear flag
        self.__gdata.IsSyspartUpdate(nickname)
        self.__current_display=str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Solar()

    def __Solar(self):
        nickname="SO"

        if self.__gdata.IsSecondHeater_SO():
            temptext="{0:21.21} ({1})\n".format("Solar / Hybridanlage", self.__gdata.hardwaretype(nickname))
            self.__text.insert("end", temptext,"b_gr")
        else:
            temptext="{0:21.21} ({1})\n".format("Solar", self.__gdata.hardwaretype(nickname))
            self.__text.insert("end", temptext,"b_gr")
        tempvalue=format(float(self.__gdata.values(nickname,"Tkollektor")),".1f")
        temptext =self.__DisplayColumn(nickname,"Tkollektor",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(float(self.__gdata.values(nickname,"Tspeicher_unten")),".1f")
        temptext =self.__DisplayColumn(nickname,"Tspeicher_unten",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=format(int(self.__gdata.values(nickname,"V_ertrag_stunde")),"d")
        temptext =self.__DisplayColumn(nickname,"V_ertrag_stunde",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        ##### Anzeige noch deaktiv, da keine Zuordnung moeglich, weitere Kontrolle erforderlich
        # temptext=" Ertrag Wert 2        : "+format(int(self.__gdata.values(nickname,"V_ertrag_2")),"d")+'\n'
        # self.__text.insert("end",temptext)
        ##
        
        laufzeit_minuten=int(self.__gdata.values(nickname,"Claufzeit"))
        tempvalue=format(laufzeit_minuten,"d")+' Minuten := '+format(int(laufzeit_minuten/60),".0f")+' Stunden'
        temptext =self.__DisplayColumn(nickname,"Claufzeit",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        tempvalue=self.__GetStrOnOff(self.__gdata.values(nickname,"Vsolar_pumpe"))
        temptext =self.__DisplayColumn(nickname,"Vsolar_pumpe",tempvalue)
        if len(temptext)>0: self.__text.insert("end",temptext)
        
        if self.__gdata.IsSecondBuffer_SO():
            tempvalue=format(float(self.__gdata.values(nickname,"Thybrid_buffer")),".1f")
            temptext =self.__DisplayColumn(nickname,"Thybrid_buffer",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=format(float(self.__gdata.values(nickname,"Thybrid_sysinput")),".1f")
            temptext =self.__DisplayColumn(nickname,"Thybrid_sysinput",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
        else:
            tempvalue=self.__GetStrJaNein(self.__gdata.values(nickname,"Vkollektor_aus"))
            temptext =self.__DisplayColumn(nickname,"Vkollektor_aus",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
            tempvalue=self.__GetStrJaNein(self.__gdata.values(nickname,"Vspeicher_voll"))
            temptext =self.__DisplayColumn(nickname,"Vspeicher_voll",tempvalue)
            if len(temptext)>0: self.__text.insert("end",temptext)
            
        
        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext=self.__gdata.values(nickname,"hexdump")
            temptext+="\n"
            self.__hextext.insert("end",temptext,"b_gr")
            
        if self.__current_display==str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end","\n")
            self.__text.insert("end","Nr. Msg-Header(hex) Systempart Hardware    Bemerkung\n","b_gray")
            self.__text.insert("end","1   B0 00 FF 00     Solar      ISM1/ISM2   Systemabhängig\n")
            self.__text.insert("end","\n")
            if self.__hexdump_window :
                self.__text.insert("end"," Details siehe 'Info'\n")

    def __clear(self):
            self.__text.delete(1.0,"end")

    def __hexclear(self):
            self.__hextext.delete(1.0,"end")
            self.__Hextext_bytecomment()
            self.__g_i_hexheader_counter=0


    def __GetStrOnOff(self, bitvalue):
            if bitvalue == 0:
                return "Aus"
            else: return "An"

    def __GetStrJaNein(self, bitvalue):
            if bitvalue == 0:
                return "Nein"
            else: return "Ja"
            
    def __GetStrBetriebsmodus(self, ivalue):
            #  21.04.2014; Aenderung auf Byte9/Bit1 und Bit2 --> Werte 1 oder 2
            if ivalue == 1:
                return "Heizen"
            elif  ivalue == 0:
                return "Standby"
            elif  ivalue == 2:
                return "Warmwasser"
            else:
                return "--"

    def __GetStrBetriebsart(self, ivalue):
            if ivalue == 1:
                return "Frost"
            elif ivalue == 2:
                return "Sparen"
            elif ivalue == 3:
                return "Heizen"
            else:
                return "---"

    def __colourconfig(self, obj):
        obj.tag_config("f_bl", foreground="black")
        obj.tag_config("b_ye", background="yellow")
        obj.tag_config("b_bl", background="lightblue")
        obj.tag_config("b_gr", background="lightgreen")
        obj.tag_config("b_rd", background="red")
        obj.tag_config("b_mocca", background="moccasin")
        obj.tag_config("b_gray", background="lightgray")
        obj.tag_config("b_or", background="orange")
        obj.tag_config("u", underline=True)

    def __Hextext_bytecomment(self):
        temptext="BNr:"
        for x in range (0,33):
            temptext = temptext+" "+format(x,"02d")
        self.__hextext.insert("end",temptext+'\n',"b_ye")

    def __anzeigesteuerung(self):
        # if newdata available, display them
        if self.__gdata.IsAnyUpdate():
            self.__clear()
            if self.__current_display=="system":
                self.__System()
            elif self.__current_display==str(self.__gdata.getlongname("HG")): #"heizgeraet"
                self.__systempart_text("HG")
                self.__Info()
                self.__Heizgeraet()
            elif self.__current_display==str(self.__gdata.getlongname("HK1")): #"heizkreise"
                self.__systempart_text("HK1")
                self.__Info()
                self.__Heizkreis()
            elif self.__current_display==str(self.__gdata.getlongname("WW")): #"warmwasser"
                self.__systempart_text("WW")
                self.__Info()
                self.__Warmwasser()
            elif self.__current_display==str(self.__gdata.getlongname("SO")): #"solar"
                self.__systempart_text("SO")
                self.__Info()
                self.__Solar()
            else:
                self.__System()

            if self.__hexdump_window :
                self.__g_i_hexheader_counter+=1
                if not self.__g_i_hexheader_counter%40:
                    self.__Hextext_bytecomment()
                
            self.__gdata.UpdateRead()
               

#--- class gui_cworker end ---#

### Runs only for test ###########
if __name__ == "__main__":
    import data
    configurationfilename='./../etc/config/4test/HT3_4dispatcher_test.xml'
    testdata=data.cdata()
    testdata.read_db_config(configurationfilename)
    
    hexdump_window=1
    GUI=gui_cworker(testdata, hexdump_window)
    GUI.run()
    print("must be never reached")
    ############ end main - task ###############

