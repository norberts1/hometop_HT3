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
# Ver:0.1.8  / Datum 29.06.2015 private:'_gdata' changed to
#                               proteced:'_gdata' in modul: ht3_worker.py
#              'GetUnmixedFlagHK()' update to name 'UnmixedFlagHK()'
#              '__GetStrBetriebsart()'
# Ver:0.1.8.1 / Datum 10.02.2016 HeizkreisMsg_ID677_max33byte modified
#                  '__GetStrBetriebsart()' update with value 4:="Auto"
#                  value < 0:="Auto" and value 0:="Manual"
# Ver:0.1.8.2 / Datum 22.02.2016 'IPM_LastschaltmodulMsg()' fixed wrong
#                                 HK-circuit assignment in ht_discode.py
# Ver:0.1.9  / Datum 12.05.2016 '__GetStrBetriebsart()'  update with
#                                       value 4:="Auto" or 0xff:="Auto"
# Ver:0.1.10 / Datum 25.08.2016 (never been an official release)
#               Display- and cause-code added for error-reports.
#               message-ID added.
#               Buscoding - text removed from GUI.
#               __GetStrBetriebsart replaced with __GetStrOperationNiveau.
#                 and related return-values modified
#               'Minuten' values deleted.
#               Display-layout modified.
#               Heater active time changed from minutes to hours.
#               Display-size corrected.
# Ver:0.2    / Datum 29.08.2016 Fkt.doc added.
# Ver:0.2.1  / Datum 31.08.2016 correction of wrong path-extraction
#                               modul: ht3_worker.py.
# Ver:0.2.2  / Datum 14.10.2016 'ht_discode.py' msgID:259 modified.
#                              Msg-comment updated in GUI.
#################################################################
#

import sys
import tkinter
import time
import _thread
import os
import data
import ht_utils
import logging
import ht_const

__author__ = "junky-zs"
__status__ = "draft"
__version__ = "0.2.2"
__date__ = "14.10.2016"


class gui_cworker(ht_utils.clog):
    """
        Class 'gui_cworker' for creating HT3 - Graphical User Interface (GUI)
    """
    def __init__(self, gdata, hexdump_window=True, titel_input="ASYNC", logger=None):
        """
        constructor of class 'gui_cworker'. This is using tkinter,Tk and frames for the GUI.
         mandatory: parameter 'gdata' as handle to cdata object
         optional : hexdump_window  (default is value 'True')
        """
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging = ht_utils.clog.create_logfile(self, logfilepath="./gui_cworker.log", loggertag="gui_cworker")
            else:
                self._logging = logger

            if not isinstance(gdata, data.cdata):
                errorstr = "gui_cworker;Error;TypeError:gdata"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            if not (isinstance(hexdump_window, int) or isinstance(hexdump_window, bool)):
                errorstr = "gui_cworker;Error;TypeError:hexdump_window"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            self.__gdata = gdata
            self.__current_display = "system"
            self.__hexdump_window = hexdump_window
            self.__threadrun = True
            self.__info_calledfirsttime = True

            self.__main = tkinter.Tk()
            self.__gui_titel_input = titel_input

            # Frame 1,2,3 with Buttons
            self.__fr1 = tkinter.Frame(self.__main, relief="sunken", bd=5)
            self.__fr1.pack(side="top")
            if self.__hexdump_window:
                self.__main.title('Heatronic Analyser Rev:{0} (Input:{1})'.format(__version__, self.__gui_titel_input))
                self.__main.geometry("1200x800+330+230")
                self.__fr2 = tkinter.Frame(self.__fr1, relief="sunken", bd=2)
                self.__fr2.pack(side="left")
            else:
                self.__main.title('Heatronic Systemstatus Rev:{0} (Input:{1})'.format(__version__, self.__gui_titel_input))
                self.__main.geometry("600x750+330+230")
                self.__fr2 = None

            self.__fr3 = tkinter.Frame(self.__fr1, relief="sunken", bd=3)
            self.__fr3.pack(side="right")

            if self.__hexdump_window:
                self.__bhexdclear = tkinter.Button(self.__fr2, text="Hexdump clear",
                                                highlightbackground="red",
                                                command=self.__hexclear)
                self.__bhexdclear.pack(padx=5, pady=5, side="left")

                self.__bende = tkinter.Button(self.__fr2, text="Ende",
                                            highlightbackground="black",
                                            command=self.__ende)
                self.__bende.pack(padx=5, pady=5, side="right")
                self.__bende = tkinter.Button(self.__fr2, text = "Info",
                                            highlightbackground="black",
                                            command=self.__info)
                self.__bende.pack(padx=5, pady=5, side="right")
            else:
                self.__bende = tkinter.Button(self.__fr3, text = "Ende",
                                            highlightbackground="black",
                                            command = self.__ende)
                self.__bende.pack(padx=5, pady=5, side="right")

            self.__bsys = tkinter.Button(self.__fr3, text="System",
                                         highlightbackground="yellow",
                                         command=self.__system_button)
            self.__bsys.pack(padx=5, pady=5, side="left")
            self.__bhge = tkinter.Button(self.__fr3, text="Heizgeraet",
                                         highlightbackground="orange",
                                         command=self.__Heizgeraet_button)
            self.__bhge.pack(padx=5, pady=5, side="left")
            self.__bhkr = tkinter.Button(self.__fr3, text="Heizkreis",
                                         highlightbackground="moccasin",
                                         command=self.__Heizkreis_button)
            self.__bhkr.pack(padx=5, pady=5, side="left")
            self.__bwwa = tkinter.Button(self.__fr3, text="Warmwasser",
                                         highlightbackground="lightblue",
                                         command=self.__Warmwasser_button)
            self.__bwwa.pack(padx=5, pady=5, side="left")
            self.__bsola = tkinter.Button(self.__fr3, text="Solar",
                                         highlightbackground="lightgreen",
                                          command=self.__Solar_button)
            self.__bsola.pack(padx=5, pady=5, side="left")

            self.__g_i_hexheader_counter = 0
            if self.__hexdump_window:
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
            self.__browsername = ""
            self.__browser_found = False
            self.__search4browser()

        except (TypeError) as e:
            errorstr = 'gui_cworker();Error;Parameter:<{0}> has wrong type'.format(e.args[0])
            self._logging.critical(errorstr)
            raise TypeError(errorstr)

    def __del__(self):
        """
            destructor for class: gui_cworker.
        """
        pass

    def __search4browser(self):
        """
            searching for available browser in system.
        """
        self.__browser_found = False
        for browsername in ("dillo", "midori", "firefox", "iceweasel"):
            cmd = "which " + browsername
            rtnliste = list(os.popen(cmd))
            for name in rtnliste:
                if browsername in name:
                    self.__browsername = browsername
                    self.__browser_found = True
                    return

    def run(self):
        """
            main loop to start GUI endless running.
        """
        # start thread for updating display
        _thread.start_new_thread(self.__anzeigethread, (0,))
        # run endless
        while self.__threadrun:
            self.__main.mainloop()
        return False

    def __anzeigethread(self, parameter):
        """
            main threat for GUI-display.
        """
        self.__cleardata()
        while self.__threadrun:
            self.__anzeigesteuerung()
            if self.__threadrun:
                time.sleep(1)
            else:
                break

    def __ende(self):
        """
            button:end handling. End of GUI.
        """
        self.__threadrun = False
        self.__main.destroy()

    def __info(self):
        """
            handling for button: 'info' displaying html-doc.
        """
        if self.__browser_found:
            if __name__ == "__main__":
                cmd = self.__browsername + " ./../etc/html/HT3-Bus_Telegramme.html"
            else:
                cmd = self.__browsername + " ./etc/html/HT3-Bus_Telegramme.html"
            os.popen(cmd)

            if self.__info_calledfirsttime == True:
                time.sleep(3)
                self.__info_calledfirsttime = False

    def __IsTemperaturValid(self, tempvalue):
        """
            Returns True if temperaturvalues is less then 300 degrees, else False.
        """
        return True if float(tempvalue) < 300.0 else False

    def __IsTemperaturInValidRange(self, tempvalue):
        """
            Returns True if temperaturvalues is less then 300 degrees and not 0, else False.
        """
        return True if (float(tempvalue) < 300.0 and float(tempvalue) != 0.0) else False

    def __IsValueNotZero(self, tempvalue):
        """
            Returns True if temperaturvalue is not 0, else False.
        """
        return True if (int(tempvalue) != 0 and float(tempvalue) != 0.0) else False

    def __DisplayColumn(self, nickname, itemname, value=None, endofline=True, right=False):
        """
            Formatted output of the current item attached to the nickname.
             Flag: 'endofline' will add Carriage Return (True) or not (False),
             Flag: 'right' will do the same as 'endofline' but not force CR.
        """
        Column = ""
        try:
            tmptext = self.__gdata.displayname(nickname, itemname)
            if value == None:
                displayvalue = self.__gdata.displayvalue(nickname, itemname)
            else:
                displayvalue = value

            if len(tmptext) > 0:
                if right == True or endofline == True:
                    Column = " {0:21.21}: {1} {2}".format(tmptext,
                                                        displayvalue,
                                                        self.__gdata.displayunit(nickname, itemname))
                else:
                    Column = " {0:21.21}: {1:7.7} {2:8.8}".format(tmptext,
                                                        displayvalue,
                                                        self.__gdata.displayunit(nickname, itemname))
            else:
                Column = ""

        except:
            errorstr = """gui_cworker.__DisplayColumn();Error;display-name/unit are not available
                       for nickname:{0};itemname:{1}""".format(nickname, itemname)
            print(errorstr)
            self._logging.critical(errorstr)
        if endofline == True:
            Column += "\n"
        return Column

    def __system_button(self):
        """
            handling for button: 'system' setting the displaymode to 'system'.
        """
        self.__current_display = "System"
        self.__clear()
        self.__System()

    def __System(self):
        """
            'system'-GUI is displayed.
        """
        temptext = "{0:13.13}: {1}\n".format("Systemstatus", "Junkers Heatronic")
        self.__text.insert("end", temptext, "b_ye")
        self.__Info()
        self.__heater_dhw()
        self.__Heizkreis()
        self.__Solar()
        self.__text.insert("end", "                                 \n", "u")

    def __Info(self):
        """
            System-date and time is displayed.
        """
        nickname = "DT"
        self.__text.insert("end", "System-Infos                     \n", "b_gray")
        datum = """ {0:12.12}: {1:11.11}| Aktuelles Datum: {2:11.11} \n""".format(self.__gdata.displayname(nickname, "Date"),
                                                                                self.__gdata.values(nickname, "Date"),
                                                                                time.strftime("%d.%m.%Y"))
        self.__text.insert("end", datum)
        uhrzeit = """ {0:12.12}: {1:11.11}| Aktuelle  Zeit : {2:11.11} \n""".format(self.__gdata.displayname(nickname, "Time"),
                                                                                self.__gdata.values(nickname, "Time"),
                                                                                time.strftime("%H:%M:%S"))
        self.__text.insert("end", uhrzeit)
        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname, "hexdump")
            temptext += "\n"
            self.__hextext.insert("end", temptext, "b_gray")

    def __cleardata(self):
        """
            dummy-read of data is forced to clear flags.
        """
        self.__gdata.IsSyspartUpdate("HG")
        self.__gdata.IsSyspartUpdate("HK1")
        self.__gdata.IsSyspartUpdate("HK2")
        self.__gdata.IsSyspartUpdate("HK3")
        self.__gdata.IsSyspartUpdate("HK4")
        self.__gdata.IsSyspartUpdate("WW")
        self.__gdata.IsSyspartUpdate("SO")
        self.__gdata.IsSyspartUpdate("DT")

    def __systempart_text(self, nickname):
        """
        """
        systempartname = self.__gdata.getlongname(nickname).upper()
        if "HK" in nickname:
            # heizkreis-nummer am Ende entfernen und 'E' dranhaengen falls noetig
            systempartname = systempartname[:len(systempartname)-1]
            if self.__gdata.heatercircuits_amount() > 1:
                systempartname = systempartname + "E"

        temptext = "{0:13.13}: {1}\n".format("Systempart", systempartname)
        self.__text.insert("end", temptext, "b_ye")

    def __Heizgeraet_button(self):
        """
            handling for button: 'Heizgeraet'.
        """
        nickname = "HG"
        self.__gdata.IsSyspartUpdate(nickname)
        self.__current_display = str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Heizgeraet()

    def __heater_dhw(self):
        """
            Decoded data for 'Heizgeraet' and 'DomesticHotWater' are displayed.
        """
        nickname_HG = "HG"
        nickname_WW = "WW"
        temptext = "{0:21.39} {1: ^54.20}\n".format("Heizgeraet", "Warmwasser        ")
#        self.__text.insert("end", temptext,"b_or")
        self.__text.insert("end", temptext)
        self.__text.tag_add("heater", "5.0", "5.39")
        self.__text.tag_config("heater", background="orange", foreground="black")
        self.__text.tag_add("water", "5.39", "5.80")
        self.__text.tag_config("water", background="lightblue", foreground="black")
        # 1. line
        tempvalue = format(float(self.__gdata.values(nickname_HG, "Taussen")), ".1f")
        temptext = self.__DisplayColumn(nickname_HG, "Taussen", tempvalue, endofline=False)

        tempvalue = format(int(self.__gdata.values(nickname_WW, "Tsoll")), "2d")
        temptext += self.__DisplayColumn(nickname_WW, "Tsoll", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 2. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Tvorlauf_soll")), "2d")
        temptext = self.__DisplayColumn(nickname_HG, "Tvorlauf_soll", tempvalue, endofline=False)

        tempvalue = format(float(self.__gdata.values(nickname_WW, "Tist")), ".1f")
        temptext += self.__DisplayColumn(nickname_WW, "Tist", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 3. line
        tempvalue = format(float(self.__gdata.values(nickname_HG, "Tvorlauf_ist")), ".1f")
        temptext = self.__DisplayColumn(nickname_HG, "Tvorlauf_ist", tempvalue, endofline=False)

        tempvalue = format(float(self.__gdata.values(nickname_WW, "Tspeicher")), ".1f")
        temptext += self.__DisplayColumn(nickname_WW, "Tspeicher", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 4. line
        Truecklauf = format(float(self.__gdata.values(nickname_HG, "Truecklauf")), ".1f")
        temptext = ""
        if self.__IsTemperaturValid(Truecklauf):
            temptext = self.__DisplayColumn(nickname_HG, "Truecklauf", Truecklauf, endofline=False)

        betriebszeit = float(self.__gdata.values(nickname_WW, "Cbetriebs_zeit"))
        if self.__IsValueNotZero(betriebszeit):
            tempvalue = format(betriebszeit, ".1f") + ' Stunden'
            temptext += self.__DisplayColumn(nickname_WW, "Cbetriebs_zeit", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 5. line
        Tmischer = format(float(self.__gdata.values(nickname_HG, "Tmischer")), ".1f")
        temptext = ""
        if self.__IsTemperaturValid(Tmischer):
            temptext = self.__DisplayColumn(nickname_HG, "Tmischer", Tmischer, endofline=False)

        brenner_ww_ein_counter = int(self.__gdata.values(nickname_WW, "Cbrenner_ww"))
        if self.__IsValueNotZero(brenner_ww_ein_counter):
            tempvalue = format(brenner_ww_ein_counter, "d")
            temptext += self.__DisplayColumn(nickname_WW, "Cbrenner_ww", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 6. line
        tempvalue = self.__GetStrBetriebsmodus(self.__gdata.values(nickname_HG, "Vmodus"))
        temptext = self.__DisplayColumn(nickname_HG, "Vmodus", tempvalue, endofline=False)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_WW, "VWW_erzeugung"))
        temptext += self.__DisplayColumn(nickname_WW, "VWW_erzeugung", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 7. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vbrenner_motor"))
        temptext = self.__DisplayColumn(nickname_HG, "Vbrenner_motor", tempvalue, endofline=False)

        tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname_WW, "VWW_temp_OK"))
        temptext += self.__DisplayColumn(nickname_WW, "VWW_temp_OK", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 8. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vbrenner_flamme"))
        temptext = self.__DisplayColumn(nickname_HG, "Vbrenner_flamme", tempvalue, endofline=False)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_WW, "VWW_nachladung"))
        temptext += self.__DisplayColumn(nickname_WW, "VWW_nachladung", tempvalue, right=True)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 9. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Vleistung")), "d")
        temptext = self.__DisplayColumn(nickname_HG, "Vleistung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 10. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vheizungs_pumpe"))
        temptext = self.__DisplayColumn(nickname_HG, "Vheizungs_pumpe", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 11. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vzirkula_pumpe"))
        temptext = self.__DisplayColumn(nickname_HG, "Vzirkula_pumpe", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 12. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vspeicher_pumpe"))
        temptext = self.__DisplayColumn(nickname_HG, "Vspeicher_pumpe", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 13. line
        betrieb_gesamt_ein = float(self.__gdata.values(nickname_HG, "Cbetrieb_gesamt"))
        tempvalue = format(betrieb_gesamt_ein, ".1f") + ' Stunden'
        temptext = self.__DisplayColumn(nickname_HG, "Cbetrieb_gesamt", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 14. line
        betrieb_heizung_ein = float(self.__gdata.values(nickname_HG, "Cbetrieb_heizung"))
        tempvalue = format(betrieb_heizung_ein, ".1f") + ' Stunden'
        temptext = self.__DisplayColumn(nickname_HG, "Cbetrieb_heizung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 15. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Cbrenner_gesamt")), "d")
        temptext = self.__DisplayColumn(nickname_HG, "Cbrenner_gesamt", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 16. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Cbrenner_heizung")), "d")
        temptext = self.__DisplayColumn(nickname_HG, "Cbrenner_heizung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 17. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Vspare1")))
        temptext = self.__DisplayColumn(nickname_HG, "Vspare1", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 18. line
        # show:display-code and cause-code if errors
        displaycode_int = int(format(self.__gdata.values(nickname_HG, "Vdisplaycode")))
        if displaycode_int == 0:
            displaycode = "--"
        else:
            upper_part = int(displaycode_int / 256)
            lower_part = int(displaycode_int % 256)
            displaycode = "{0:c}{1:c}".format(upper_part, lower_part)
        temptext = self.__DisplayColumn(nickname_HG, "Vdisplaycode", displaycode)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        causecode = str(format(self.__gdata.values(nickname_HG, "Vcausecode")))
        temptext = self.__DisplayColumn(nickname_HG, "Vcausecode", causecode)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        if (self.__gdata.IsSyspartUpdate(nickname_HG) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname_HG, "hexdump")
            temptext += "\n"
            self.__hextext.insert("end", temptext, "b_or")

        if (self.__gdata.IsSyspartUpdate(nickname_WW) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname_WW, "hexdump")
            temptext += "\n"
            self.__hextext.insert("end", temptext, "b_bl")

    def __Heizgeraet(self):
        """
            Decoded data for 'Heizgeraet' is displayed.
        """
        nickname = "HG"
        temptext = "{0:21.21} ({1})\n".format("Heizgeraet", self.__gdata.hardwaretype(nickname))
        self.__text.insert("end", temptext, "b_or")
        tempvalue = format(float(self.__gdata.values(nickname, "Taussen")), ".1f")
        temptext = self.__DisplayColumn(nickname, "Taussen", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(int(self.__gdata.values(nickname, "Tvorlauf_soll")), "2d")
        temptext = self.__DisplayColumn(nickname, "Tvorlauf_soll", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(float(self.__gdata.values(nickname, "Tvorlauf_ist")), ".1f")
        temptext = self.__DisplayColumn(nickname, "Tvorlauf_ist", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        Truecklauf = format(float(self.__gdata.values(nickname, "Truecklauf")), ".1f")
        if self.__IsTemperaturValid(Truecklauf):
            temptext = self.__DisplayColumn(nickname, "Truecklauf", Truecklauf)
            if len(temptext) > 0: self.__text.insert("end", temptext)

        Tmischer = format(float(self.__gdata.values(nickname, "Tmischer")), ".1f")
        if self.__IsTemperaturValid(Tmischer):
            temptext = self.__DisplayColumn(nickname, "Tmischer", Tmischer)
            if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = self.__GetStrBetriebsmodus(self.__gdata.values(nickname, "Vmodus"))
        temptext = self.__DisplayColumn(nickname, "Vmodus", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vbrenner_motor"))
        temptext = self.__DisplayColumn(nickname, "Vbrenner_motor", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vbrenner_flamme"))
        temptext = self.__DisplayColumn(nickname, "Vbrenner_flamme", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(int(self.__gdata.values(nickname, "Vleistung")), "d")
        temptext = self.__DisplayColumn(nickname, "Vleistung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vheizungs_pumpe"))
        temptext = self.__DisplayColumn(nickname, "Vheizungs_pumpe", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        if not self.__gdata.IsLoadpump_WW():
            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vzirkula_pumpe"))
            temptext = self.__DisplayColumn(nickname, "Vzirkula_pumpe", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vspeicher_pumpe"))
            temptext = self.__DisplayColumn(nickname, "Vspeicher_pumpe", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

        betrieb_gesamt_ein = int(self.__gdata.values(nickname, "Cbetrieb_gesamt"))
        tempvalue = format(int(betrieb_gesamt_ein / 60), ".0f") + ' Stunden'
        temptext = self.__DisplayColumn(nickname, "Cbetrieb_gesamt", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        betrieb_heizung_ein = int(self.__gdata.values(nickname, "Cbetrieb_heizung"))
        tempvalue = format(int(betrieb_heizung_ein / 60), ".0f") + ' Stunden'
        temptext = self.__DisplayColumn(nickname, "Cbetrieb_heizung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(int(self.__gdata.values(nickname, "Cbrenner_gesamt")), "d")
        temptext = self.__DisplayColumn(nickname, "Cbrenner_gesamt", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(int(self.__gdata.values(nickname, "Cbrenner_heizung")), "d")
        temptext = self.__DisplayColumn(nickname, "Cbrenner_heizung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # Rev.: 0.1.7 https://www.mikrocontroller.net/topic/324673#3970615
        tempvalue = format(int(self.__gdata.values(nickname, "Vspare1")))
        temptext = self.__DisplayColumn(nickname, "Vspare1", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # show:display-code and cause-code if errors
        displaycode_int = int(format(self.__gdata.values(nickname, "Vdisplaycode")))
        if displaycode_int == 0:
            displaycode = "--"
        else:
            upper_part = int(displaycode_int / 256)
            lower_part = int(displaycode_int % 256)
            displaycode = "{0:c}{1:c}".format(upper_part, lower_part)
        temptext = self.__DisplayColumn(nickname, "Vdisplaycode", displaycode)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        causecode_int = int(format(self.__gdata.values(nickname, "Vcausecode")))
        temptext = self.__DisplayColumn(nickname, "Vcausecode", causecode_int)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname, "hexdump")
            temptext += "\n"
            self.__hextext.insert("end", temptext, "b_or")

        if self.__current_display == str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end", "\n")
            self.__text.insert("end", "Msg-ID Msg-example(hex)   Systempart Hardware    Comment\n", "b_gray")
            self.__text.insert("end", "  22   so ta 16 00 P1 P2  heater     heater      2 wire bus\n")
            self.__text.insert("end", "  24   so ta 18 00 P1 P2  heater     heater      2 wire bus\n")
            self.__text.insert("end", "  25   so ta 19 00 P1 P2  heater     heater      2 wire bus\n")
            self.__text.insert("end", "  42   so ta 2A 00 P1 P2  heater     heater      2 wire bus\n")
            self.__text.insert("end", "       so := source (88)\n")
            self.__text.insert("end", "          ta := target\n")
            self.__text.insert("end", "                   P1 := first payload Byte\n")
            self.__text.insert("end", "                      P2 := second payload Byte\n")
            self.__text.insert("end", "\n")
            if self.__hexdump_window:
                self.__text.insert("end", " for details press button: 'Info'\n")

    def __Heizkreis_button(self):
        """
            handling for button: 'Heizkreis'.
        """
        # dummy-read to clear flag
        for HeizkreisNummer in range(1, 5):
            nickname = "HK" + str(HeizkreisNummer)
            self.__gdata.IsSyspartUpdate(nickname)
        nickname = "HK1"
        self.__current_display = str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Heizkreis()

    def __Heizkreis(self):
        """
            Decoded data for 'Heizkreis' are displayed.
             This depends on how many heater-circuits are currently decoded.
             Also the unmixedFlag depends on currently received messages from heater-bus
              decoding which type of heater-circuit it is.
        """
        for HeizkreisNummer in range(1, self.__gdata.heatercircuits_amount() + 1):
            nickname = "HK" + str(HeizkreisNummer)
            ungemischt = self.__gdata.UnmixedFlagHK(nickname)
            if ungemischt:
                temptext = """{0}{1} ({2} ohne Mischer)\n""".format("Heizkreis", HeizkreisNummer,
                                                            self.__gdata.hardwaretype(nickname))
                self.__text.insert("end", temptext, "b_mocca")
            else:
                temptext="""{0}{1} ({2}  mit Mischer)\n""".format("Heizkreis", HeizkreisNummer,
                                                            self.__gdata.hardwaretype(nickname))
                self.__text.insert("end", temptext, "b_mocca")

            tempvalue = self.__GetStrOperationNiveau(self.__gdata.values(nickname, "Vtempera_niveau"))
            temptext = self.__DisplayColumn(nickname, "Vtempera_niveau", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOperationStatus(self.__gdata.values(nickname, "Voperation_status"))
            temptext = self.__DisplayColumn(nickname, "Voperation_status", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tsoll_HK")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tsoll_HK", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tist_HK")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tist_HK", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            TsteuerFB = float(self.__gdata.values(nickname, "Tsteuer_FB"))
            if self.__IsTemperaturInValidRange(TsteuerFB):
                tempvalue = format(TsteuerFB, ".1f")
                temptext = self.__DisplayColumn(nickname, "Tsteuer_FB", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            if ungemischt == False:
                tempvalue = format(float(self.__gdata.values(nickname, "Tvorlaufmisch_HK")), ".1f")
                temptext = self.__DisplayColumn(nickname, "Tvorlaufmisch_HK", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = format(int(self.__gdata.values(nickname, "VMischerstellung")), "d")
                temptext = self.__DisplayColumn(nickname, "VMischerstellung", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
                temptext = self.__gdata.values(nickname, "hexdump")
                temptext += "\n"
                self.__hextext.insert("end", temptext, "b_mocca")

        nickname = "HK1"
        if self.__current_display == str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end", "\n")
            self.__text.insert("end", "Msg-ID Msg-example(hex)   Systempart     Hardware    Comment\n", "b_gray")
            self.__text.insert("end", "  26   so ta 1A 00 P1 P2  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", "  35   so ta 23 00 P1 P2  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " 268   so ta FF 00 00 0C  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " 357   so ta FF 00 00 65  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " ...\n")
            self.__text.insert("end", " 360   so ta FF 00 00 68  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " 367   so ta FF 00 00 6F  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " ...\n")
            self.__text.insert("end", " 370   so ta FF 00 00 72  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " 377   so ta FF 00 00 79  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " ...\n")
            self.__text.insert("end", " 380   so ta FF 00 00 7C  heating-ciruit Controller  2 wire bus\n")
            self.__text.insert("end", " 615   so ta FF 00 01 67  heating-ciruit Controller  EMS2\n")
            self.__text.insert("end", " 677   so ta FF 00 01 A5  heating-ciruit Controller  EMS2\n")
            self.__text.insert("end", " ...\n")
            self.__text.insert("end", " 680   so ta FF 00 01 A8  heating-ciruit Controller  EMS2\n")
            self.__text.insert("end", " 697   so ta FF 00 01 B9  heating-ciruit Controller  EMS2\n")
            self.__text.insert("end", " ...\n")
            self.__text.insert("end", " 704   so ta FF 00 01 C0  heating-ciruit Controller  EMS2\n")
            self.__text.insert("end", "       so := source (90; 9x with x := 8...F; Ay with y := 0...7)\n")
            self.__text.insert("end", "          ta := target\n")
            self.__text.insert("end", "                   P1 := first payload Byte\n")
            self.__text.insert("end", "                      P2 := second payload Byte\n")
            self.__text.insert("end", "\n")
            if self.__hexdump_window:
                self.__text.insert("end", " for details press button: 'Info'\n")

    def __Warmwasser_button(self):
        """
            handling for button: 'Warmwasser'.
        """
        nickname = "WW"
        # dummy-read to clear flag
        self.__gdata.IsSyspartUpdate(nickname)
        self.__current_display = str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Warmwasser()

    def __Warmwasser(self):
        """
            Decoded data for 'Warmwasser' is displayed.
        """
        nickname = "WW"

        temptext = "{0:21.21} ({1})\n".format("Warmwasser", self.__gdata.hardwaretype(nickname))
        self.__text.insert("end", temptext, "b_bl")
        tempvalue = format(int(self.__gdata.values(nickname, "Tsoll")), "2d")
        temptext = self.__DisplayColumn(nickname, "Tsoll", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(float(self.__gdata.values(nickname, "Tist")), ".1f")
        temptext = self.__DisplayColumn(nickname, "Tist", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(float(self.__gdata.values(nickname, "Tspeicher")), ".1f")
        temptext = self.__DisplayColumn(nickname, "Tspeicher", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        betriebszeit = float(self.__gdata.values(nickname, "Cbetriebs_zeit"))
        if self.__IsValueNotZero(betriebszeit):
            tempvalue = format(betriebszeit, ".1f") + ' Stunden'
            temptext = self.__DisplayColumn(nickname, "Cbetriebs_zeit", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

        brenner_ww_ein_counter = int(self.__gdata.values(nickname, "Cbrenner_ww"))
        if self.__IsValueNotZero(brenner_ww_ein_counter):
            tempvalue = format(brenner_ww_ein_counter, "d")
            temptext = self.__DisplayColumn(nickname, "Cbrenner_ww", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

        if self.__gdata.IsLoadpump_WW():
            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vladepumpe"))
            temptext = self.__DisplayColumn(nickname, "Vladepumpe", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vladepumpe"))
            temptext = self.__DisplayColumn(nickname, "Vladepumpe", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)
        else:
            ##### Anzeigen teilweise noch deaktiv, da nicht schluessig, weitere Kontrolle erforderlich
            # temptext=" Zirkulationspumpe    : "+self.__GetStrOnOff(self.__gdata.values(nickname,"V_zirkula_pumpe"))+'\n'
            # self.__text.insert("end",temptext)
            # temptext=" Speicherladepumpe    : "+self.__GetStrOnOff(self.__gdata.values(nickname,"V_lade_pumpe"))+'\n'
            # self.__text.insert("end",temptext)
            ##
            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "VWW_erzeugung"))
            temptext = self.__DisplayColumn(nickname, "VWW_erzeugung", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname, "VWW_temp_OK"))
            temptext = self.__DisplayColumn(nickname, "VWW_temp_OK", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "VWW_nachladung"))
            temptext = self.__DisplayColumn(nickname, "VWW_nachladung", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)
            ####
            # temptext=" Einmalladung         : "+self.__GetStrOnOff(self.__gdata.values(nickname,"VWW_einmalladung"))+'\n'
            # self.__text.insert("end",temptext)
            # temptext=" Desinfektion         : "+self.__GetStrOnOff(self.__gdata.values(nickname,"VWW_desinfekt"))+'\n'
            # self.__text.insert("end",temptext)
            ##

        if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname, "hexdump")
            temptext += "\n"
            self.__hextext.insert("end", temptext, "b_bl")

        if self.__current_display == str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end", "\n")
            self.__text.insert("end", "Msg-ID Msg-example(hex)   Systempart Hardware    Comment\n", "b_gray")
            self.__text.insert("end", "  27   so ta 1B 00 P1 P2  Hotwater   heater      2 wire bus\n")
            self.__text.insert("end", "  51   so ta 33 00 P1 P2  Hotwater   heater      2 wire bus\n")
            self.__text.insert("end", "  52   so ta 34 00 P1 P2  Hotwater   heater      2 wire bus\n")
            self.__text.insert("end", "  53   so ta 35 00 P1 P2  Hotwater   heater      2 wire bus\n")
            self.__text.insert("end", " 269   so ta FF 00 00 0D  Hotwater   IPM         system dependent\n")
            self.__text.insert("end", " 467   so ta FF 00 00 D3  Hotwater   heater      2 wire bus\n")
            self.__text.insert("end", " 468   so ta FF 00 00 D4  Hotwater   heater      2 wire bus\n")
            self.__text.insert("end", " 797   so ta FF 00 02 1D  Hotwater   Cxyz        EMS2\n")
            self.__text.insert("end", "       so := source (88; 90; Ax with x := 0...7)\n")
            self.__text.insert("end", "          ta := target\n")
            self.__text.insert("end", "                   P1 := first payload Byte\n")
            self.__text.insert("end", "                      P2 := second payload Byte\n")
            self.__text.insert("end", "\n")
            if self.__hexdump_window:
                self.__text.insert("end", " for details press button: 'Info'\n")

    def __Solar_button(self):
        """
            handling for button: 'Solar'.
        """
        nickname = "SO"
        # dummy-read to clear flag
        self.__gdata.IsSyspartUpdate(nickname)
        self.__current_display = str(self.__gdata.getlongname(nickname))
        self.__clear()
        self.__systempart_text(nickname)
        self.__Info()
        self.__Solar()

    def __Solar(self):
        """
            Decoded data for 'Solar' is displayed.
             This depends on solar-messages already decoded to enable the display.
        """
        nickname = "SO"

        if self.__gdata.IsSolarAvailable():
            if self.__gdata.IsSecondHeater_SO():
                temptext = "{0:21.21} ({1})\n".format("Solar / Hybridanlage", self.__gdata.hardwaretype(nickname))
                self.__text.insert("end", temptext, "b_gr")
            else:
                temptext="{0:21.21} ({1})\n".format("Solar", self.__gdata.hardwaretype(nickname))
                self.__text.insert("end", temptext, "b_gr")
            tempvalue = format(float(self.__gdata.values(nickname, "Tkollektor")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tkollektor", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tspeicher_unten")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tspeicher_unten", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(int(self.__gdata.values(nickname, "V_ertrag_stunde")), "d")
            temptext = self.__DisplayColumn(nickname, "V_ertrag_stunde", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            f_laufzeit_stunden = float(self.__gdata.values(nickname, "Claufzeit"))
            tempvalue = format(f_laufzeit_stunden, ".1f") + ' Stunden'
            temptext = self.__DisplayColumn(nickname, "Claufzeit", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vsolar_pumpe"))
            temptext = self.__DisplayColumn(nickname, "Vsolar_pumpe", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            if self.__gdata.IsSecondBuffer_SO():
                tempvalue = format(float(self.__gdata.values(nickname, "Thybrid_buffer")), ".1f")
                temptext = self.__DisplayColumn(nickname, "Thybrid_buffer", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = format(float(self.__gdata.values(nickname, "Thybrid_sysinput")), ".1f")
                temptext = self.__DisplayColumn(nickname, "Thybrid_sysinput", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)
            else:
                tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname, "Vkollektor_aus"))
                temptext = self.__DisplayColumn(nickname, "Vkollektor_aus", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname, "Vspeicher_voll"))
                temptext = self.__DisplayColumn(nickname, "Vspeicher_voll", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            if (self.__gdata.IsSyspartUpdate(nickname) and self.__hexdump_window):
                temptext=self.__gdata.values(nickname, "hexdump")
                temptext += "\n"
                self.__hextext.insert("end", temptext, "b_gr")

        if self.__current_display == str(self.__gdata.getlongname(nickname)) and self.__hexdump_window:
            self.__text.insert("end", "\n")
            self.__text.insert("end", "Msg-ID Msg-example(hex)   Systempart Hardware    Comment\n", "b_gray")
            self.__text.insert("end", " 259   so ta FF 00 00 03  Solar      ISM1/ISM2   2 wire bus\n")
            self.__text.insert("end", " 260   so ta FF 00 00 04  Solar      ISM1/ISM2   2 wire bus\n")
            self.__text.insert("end", " 866   so ta FF 00 02 62  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 867   so ta FF 00 02 63  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 868   so ta FF 00 02 64  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 870   so ta FF 00 02 66  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 872   so ta FF 00 02 68  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 873   so ta FF 00 02 69  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 874   so ta FF 00 02 6A  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 910   so ta FF 00 02 8E  Solar      MS100       EMS2\n")
            self.__text.insert("end", " 913   so ta FF 00 02 91  Solar      MS100       EMS2\n")
            self.__text.insert("end", "       so := source (B0)\n")
            self.__text.insert("end", "          ta := target\n")
            self.__text.insert("end", "\n")
            if self.__hexdump_window:
                self.__text.insert("end", " for details press button: 'Info'\n")

    def __clear(self):
        """
            handling for clearing the current displayed data.
        """
        self.__text.delete(1.0, "end")

    def __hexclear(self):
        """
            handling for button: 'Hexdump clear'.
        """
        self.__hextext.delete(1.0, "end")
        self.__Hextext_bytecomment()
        self.__g_i_hexheader_counter = 0

    def __GetStrOnOff(self, bitvalue):
        """
            Return of: 'An' if input > 0, else 'Aus'.
        """
        if bitvalue == 0:
            return "Aus"
        else:
            return "An"

    def __GetStrJaNein(self, bitvalue):
        """
            Return of: 'Ja' if input > 0, else 'Nein'.
        """
        if bitvalue == 0:
            return "Nein"
        else:
            return "Ja"

    def __GetStrBetriebsmodus(self, ivalue):
        """
            return of betriebsmode for heater-device.
        """
        if ivalue == 1:
            return "Heizen"
        elif ivalue == 0:
            return "Standby"
        elif ivalue == 2:
            return "Warmwasser"
        else:
            return "--"

    def __GetStrOperationStatus(self, ivalue):
        """
            return of operationstatus (as string).
             this depends on current underlaying heaterbus-type.
        """
        rtnstr = "---"
        if self.__gdata.HeaterBusType() == ht_const.BUS_TYPE_HT3:
            if ivalue == 0:
                rtnstr = "---"
            elif ivalue == 1:
                rtnstr = "Manuell"
            elif ivalue == 2:
                rtnstr = "Auto"
            elif ivalue == 3:
                rtnstr = "Urlaub"
            elif ivalue == 4 or ivalue == 5:
                rtnstr = "E-Trocknung"
        elif self.__gdata.HeaterBusType() == ht_const.BUS_TYPE_EMS:
            if ivalue == 0:
                rtnstr = "Off"
            if ivalue == 1:
                rtnstr = "Summer"
            elif ivalue == 2:
                rtnstr = "Manual"
            elif ivalue == 3:
                rtnstr = "Comfort"
            elif ivalue == 4:
                rtnstr = "Eco"
        return rtnstr

    def __GetStrOperationNiveau(self, ivalue):
        """
            return of operation-niveau (as string).
             this depends on current underlaying heaterbus-type.
        """
        rtnstr = "---"
        ivalue = int(ivalue)
        if self.__gdata.HeaterBusType() == ht_const.BUS_TYPE_HT3:
            if ivalue == 0:
                rtnstr = "---"
            if ivalue == 1:
                rtnstr = "Frost"
            elif ivalue == 2:
                rtnstr = "Sparen"
            elif ivalue == 3:
                rtnstr = "Heizen"
        elif self.__gdata.HeaterBusType() == ht_const.BUS_TYPE_EMS:
            if ivalue == 1:
                rtnstr = "Eco"
            elif ivalue == 2:
                rtnstr = "Comfort1"
            elif ivalue == 3:
                rtnstr = "Comfort2"
            elif ivalue == 4:
                rtnstr = "Comfort3"
        return rtnstr

    def __colourconfig(self, obj):
        """
            configuration of used colours.
        """
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
        """
            MsgID textoutput for hexdump display.
        """
        temptext = " MsgID :BNr:"
        for x in range(0, 33):
            temptext = temptext+format(x, "02d") + " "
        self.__hextext.insert("end", temptext + '\n', "b_ye")

    def __anzeigesteuerung(self):
        """
            GUI display-controller.
        """
        # if newdata available, display them
        if self.__gdata.IsAnyUpdate():
            self.__clear()
            if self.__current_display == "system":
                self.__System()
            elif self.__current_display == str(self.__gdata.getlongname("HG")):  # "heizgeraet"
                self.__systempart_text("HG")
                self.__Info()
                self.__Heizgeraet()
            elif self.__current_display == str(self.__gdata.getlongname("HK1")):  # "heizkreise"
                self.__systempart_text("HK1")
                self.__Info()
                self.__Heizkreis()
            elif self.__current_display == str(self.__gdata.getlongname("WW")):  # "warmwasser"
                self.__systempart_text("WW")
                self.__Info()
                self.__Warmwasser()
            elif self.__current_display == str(self.__gdata.getlongname("SO")):  # "solar"
                self.__systempart_text("SO")
                self.__Info()
                self.__Solar()
            else:
                self.__System()

            if self.__hexdump_window:
                self.__g_i_hexheader_counter += 1
                if not self.__g_i_hexheader_counter % 40:
                    self.__Hextext_bytecomment()
            self.__gdata.UpdateRead()

#--- class gui_cworker end ---#

### Runs only for test ###########
if __name__ == "__main__":
    """
        This is used for testpurposes.
    """
    import data
    configurationfilename = './../etc/config/4test/HT3_4dispatcher_test.xml'
    testdata = data.cdata()
    testdata.read_db_config(configurationfilename)

    hexdump_window = 1
    GUI = gui_cworker(testdata, hexdump_window)
    GUI.run()
    print("must never been reached")
    ############ end main - task ###############
