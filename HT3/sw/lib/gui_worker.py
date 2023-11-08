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
# Ver:0.2.3  / Datum 20.11.2016 'ht_discode.py' msgID:52 modified.
#                               DHW WW-Betriebzeit always displayed.
# Ver:0.3    / Datum 19.06.2017 controller- and bus-type added.
# Ver:0.3.1  / Datum 20.01.2019 T-Soll Vorlauf im HK added.
#                               T-Hydraulische Weiche added.
#                               __MakeDisplaycodeString() added,
#                                update of displaycode-handling.
#                               IsSecondCollectorValue_SO() handling added,
#                                SO:V_spare_1 & SO:V_spare_2 used now.
#                               Display of SO:V_ertrag_sum_calc ('TotalSolarGain') and
#                                SO:V_ertrag_tag_calc ('DalySolarGain') added.
#                               Betriebszeit Gesamt und Heizung im Heizgeraet-Anzeigemode korrigiert.
#                               Unit 'Stunden' - String entfernt -> jetzt aus Cfg-file.
# Ver:0.3.2  / Datum 03.12.2019 Issue:'Deprecated property InterCharTimeout #7'
#                                port.setInterCharTimeout() removed
# Ver:0.3.3  / Datum 08.09.2020 Modified 'geometry' for the display
#                               Scrollbars added.
#                               DHW display 'T-Soll max' added.
# Ver:0.4    / 2021-02-25  Portnumbers changed in project-config:
#                           from 8086 to 48086
#                           from 8088 to 48088
#                           see Issue: #13
# Ver:0.4.1  / 2021-03-12  Release-File imported
# Ver:0.4.2  / 2021-06-16  Issue #16 LWL handling corrected.
# Ver:0.4.3  / 2022-01-19  Issue #17 New serial port naming corrected.
# Ver:0.5    / 2023-03-12  busmodulAdr - handling added.
#                           solar-part now at right side.
#                           V_pressure, V_ch_optimize, V_dhw_optimize added but
#                            not yet activated.
# Ver:0.6    / 2023-04-22  __MakeDisplaycodeString() modified for dynamic str-generation.
#                          pressure, V_ch_optimize, V_dhw_optimize activated.
# Ver:0.6.1  / 2023-06-29  tempfile handling added in __init__()
#                          __MakeDisplaycodeString() replaced with utils.IntegerToString()
# Ver:0.6.2  / 2023-10-22  Mixerposition solar-optionG added using spare-value:sol_V_spare_1
#                            ID:868_15_0
#################################################################
#

import sys
import tkinter
import time
import _thread
import os
import tempfile
import data
import ht_utils
import logging
import ht_const
import ht_release

__author__ = "junky-zs"
__status__ = "draft"


class gui_cworker(ht_utils.cht_utils, ht_utils.clog):
    """
        Class 'gui_cworker' for creating HT3 - Graphical User Interface (GUI)
    """
    def __init__(self, gdata, hexdump_window=True, titel_input="ASYNC", logger=None):
        """
        constructor of class 'gui_cworker'. This is using tkinter,Tk and frames for the GUI.
         mandatory: parameter 'gdata' as handle to cdata object
         optional : hexdump_window  (default is value 'True')
        """
        ht_utils.cht_utils.__init__(self)
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                logfilenamepath = os.path.join(tempfile.gettempdir(),"gui_cworker.log")
                self._logging = ht_utils.clog.create_logfile(self, logfilepath=logfilenamepath, loggertag="gui_cworker")
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
                self.__main.title('Heizungs Analyser Rev:{0} (Input:{1})'.format(ht_release.VERSION, self.__gui_titel_input))
                self.__main.geometry("1570x800+5+0")
                self.__fr2 = tkinter.Frame(self.__fr1, relief="sunken", bd=2)
                self.__fr2.pack(side="left")
            else:
                self.__main.title('Heizungs Systemstatus Rev:{0} (Input:{1})'.format(ht_release.VERSION, self.__gui_titel_input))
                self.__main.geometry("690x800+5+0")
                self.__fr2 = None

            self.__fr3 = tkinter.Frame(self.__fr1, relief="sunken", bd=3)
            self.__fr3.pack(side="right")

            # setup Buttons for controlling the frame-context
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
                #frame for hexdump with scrollbar on the left side
                self.__hexdumpfr = tkinter.Frame(self.__main, width=1000, relief="sunken", bd=1)
                self.__hexdumpfr.pack(side="left", expand=1, fill="both")

                scrollbar_hexdump = tkinter.Scrollbar(self.__hexdumpfr, orient=tkinter.VERTICAL ,bg="lightgray")
                scrollbar_hexdump.pack(side="left", fill = tkinter.Y)

                self.__hextext = tkinter.Text(self.__hexdumpfr, yscrollcommand = scrollbar_hexdump.set)
                self.__hextext.pack(side="left", expand=1, fill="both")

                scrollbar_hexdump.config(command = self.__hextext.yview)

                self.__colourconfig(self.__hextext)
                self.__Hextext_bytecomment()

            #frame for data
            self.__datafr = tkinter.Frame(self.__main, width=1, relief="sunken", bd=4)
            self.__datafr.pack(side="left", fill="both")

            scrollbar_data = tkinter.Scrollbar(self.__datafr, orient=tkinter.VERTICAL ,bg="lightgray")
            scrollbar_data.pack(side="right", fill = tkinter.Y)

            self.__text = tkinter.Text(self.__datafr, yscrollcommand = scrollbar_data.set)
            self.__text.pack(side="left", expand=1, fill="both")

            scrollbar_data.config(command = self.__text.yview)

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

    def __DrawColumn(self, leftparameter_t=("","",None), rightparameter_t=("","",None)):
        """
            Formated text output of the current items attached to the nicknames.
             tuple: 'leftparameter_t'  assigned to left-printed item and value,
             tuple: 'rightparameter_t' assigned to rigth-printed item and value,
        """
        Column = ""
        nicknameL, itemnameL, valueL = leftparameter_t
        nicknameR, itemnameR, valueR = rightparameter_t
        Column = ""
        try:
            display_name= ""
            if len(nicknameL) > 0 and len(itemnameL) > 0:
                display_name = self.__gdata.displayname(nicknameL, itemnameL)
                if valueL == None:
                    displayvalueL = self.__gdata.displayvalue(nicknameL, itemnameL)
                else:
                    displayvalueL = valueL

                if len(display_name) > 0:
                    Column = " {0:21.21}: {1:7.7} {2:8.8}".format(display_name,
                                                        displayvalueL,
                                                        self.__gdata.displayunit(nicknameL, itemnameL))
            else:
                Column =  "                                        "
        except:
            errorstr = """gui_cworker.__DrawColumn();Error;display-name/unit are not available
                       for nicknameL:{0};itemnameL:{1}""".format(nicknameL, itemnameL)
            self._logging.critical(errorstr)
            nicknameL = ""

        try:
            display_name= ""
            if len(nicknameR) > 0 and len(itemnameR) > 0:
                display_name = self.__gdata.displayname(nicknameR, itemnameR)
                if valueR == None:
                    displayvalueR = self.__gdata.displayvalue(nicknameR, itemnameR)
                else:
                    displayvalueR = valueR

                if len(display_name) > 0:
                    Column += " {0:21.21}: {1:7.7} {2:8.8}".format(display_name,
                                                        displayvalueR,
                                                        self.__gdata.displayunit(nicknameR, itemnameR))
        except:
            errorstr = """gui_cworker.__DrawColumn();Error;display-name/unit are not available
                       for nicknameR:{0};itemnameR:{1}""".format(nicknameR, itemnameR)
            self._logging.critical(errorstr)
            nicknameR = ""

        if (len(nicknameL) > 0) or (len(nicknameR) > 0):
            Column += "\n"
            self.__text.insert("end", Column)

    def __DisplayColumn(self, nickname, itemname, value=None, endofline=True, right=False):
        """
            Formated output of the current item attached to the nickname.
             Flag: 'endofline' will add Carriage Return (True) or not (False),
        """
        Column = ""
        try:
            tmptext = self.__gdata.displayname(nickname, itemname)
            if value == None:
                displayvalue = self.__gdata.displayvalue(nickname, itemname)
            else:
                displayvalue = value

        except:
            errorstr = """gui_cworker.__DisplayColumn();Error;displayvalue is not available
                       for nickname:{0};itemname:{1}""".format(nickname, itemname)
            print(errorstr)
            self._logging.critical(errorstr)

        if len(tmptext) > 0:
            try:
                Column = " {0:21.21}: {1:7.7} {2}".format(tmptext,
                                                    displayvalue,
                                                    self.__gdata.displayunit(nickname, itemname))
            except:
                errorstr = """gui_cworker.__DisplayColumn();Error;displayunit is not available
                           for nickname:{0};itemname:{1}""".format(nickname, itemname)
                print(errorstr)
                self._logging.critical(errorstr)
        else:
            Column = ""

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
        temptext = "{0:13.13}: {1}\n".format("Systemstatus", "Junkers Heatersystem")
        self.__text.insert("end", temptext, "b_ye")
        self.__Info()
        self.__heater_dhw_solar()
        self.__Heizkreis()
        self.__text.insert("end", "                                 \n", "u")
        self.__text.tag_add("system", 'end-2c linestart', 'end-2c')
        self.__text.tag_config("system", foreground="black")

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
        str_controller = " Regler-Typ  : {0:11.11}| Bus-Typ        : {1}\n".format(self.__gdata.controller_type(), self.__gdata.bus_type())
        self.__text.insert("end", str_controller)

        str_deviceIDs  = " Busmodul-Adr: (hex) {0}\n".format(self.__gdata.busmodulAdr())
        self.__text.insert("end", str_deviceIDs)

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

    def __heater_dhw_solar(self):
        """
            Decoded data for 'Heizgeraet', 'DomesticHotWater' and 'Solar' are displayed.
        """
        nickname_HG = "HG"
        nickname_WW = "WW"
        nickname_SO = "SO"
        leftparameter_t  = ("", "", None)
        rightparameter_t = ("", "", None)

        temptext = "{0:21.39} {1: ^57.20}\n".format("Heizgeraet", "Warmwasser        ")
        self.__text.insert("end", temptext)
        self.__text.tag_add("heater", "7.0", "7.39")
        self.__text.tag_config("heater", background="orange", foreground="black")
        self.__text.tag_add("water", "7.39", "7.90")
        self.__text.tag_config("water", background="lightblue", foreground="black")

        # 1. line
        tempvalue = format(float(self.__gdata.values(nickname_HG, "Taussen")), ".1f")
        leftparameter_t  = (nickname_HG, "Taussen", tempvalue)

        tempvalue = format(int(self.__gdata.values(nickname_WW, "Tsoll")), "2d")
        rightparameter_t = (nickname_WW, "Tsoll", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 2. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Tvorlauf_soll")), "2d")
        leftparameter_t  = (nickname_HG, "Tvorlauf_soll", tempvalue)

        tempvalue = format(float(self.__gdata.values(nickname_WW, "Tist")), ".1f")
        rightparameter_t = (nickname_WW, "Tist", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 3. line
        tempvalue = format(float(self.__gdata.values(nickname_HG, "Tvorlauf_ist")), ".1f")
        leftparameter_t  = (nickname_HG, "Tvorlauf_ist", tempvalue)

        tempvalue = format(float(self.__gdata.values(nickname_WW, "Tspeicher")), ".1f")
        rightparameter_t = (nickname_WW, "Tspeicher", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 4. line
        leftparameter_t  = ("", "", None)
        Truecklauf = format(float(self.__gdata.values(nickname_HG, "Truecklauf")), ".1f")
        if self.IsTemperaturValid(Truecklauf):
            leftparameter_t  = (nickname_HG, "Truecklauf", Truecklauf)

        betriebszeit = float(self.__gdata.values(nickname_WW, "Cbetriebs_zeit"))
        tempvalue = format(betriebszeit, ".1f")
        rightparameter_t = (nickname_WW, "Cbetriebs_zeit", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 5. line
        leftparameter_t  = ("", "", None)
        Tmischer = format(float(self.__gdata.values(nickname_HG, "Tmischer")), ".1f")
        if self.IsTemperaturValid(Tmischer):
            leftparameter_t  = (nickname_HG, "Tmischer", Tmischer)

        brenner_ww_ein_counter = int(self.__gdata.values(nickname_WW, "Cbrenner_ww"))
        tempvalue = format(brenner_ww_ein_counter, "d")
        rightparameter_t = (nickname_WW, "Cbrenner_ww", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 6. line
        tempvalue = self.__GetStrBetriebsmodus(self.__gdata.values(nickname_HG, "Vmodus"))
        leftparameter_t  = (nickname_HG, "Vmodus", tempvalue)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_WW, "VWW_erzeugung"))
        rightparameter_t = (nickname_WW, "VWW_erzeugung", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 7. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vbrenner_motor"))
        leftparameter_t  = (nickname_HG, "Vbrenner_motor", tempvalue)

        tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname_WW, "VWW_temp_OK"))
        rightparameter_t = (nickname_WW, "VWW_temp_OK", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 8. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vbrenner_flamme"))
        leftparameter_t  = (nickname_HG, "Vbrenner_flamme", tempvalue)

        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_WW, "VWW_nachladung"))
        rightparameter_t = (nickname_WW, "VWW_nachladung", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 9. line
        rightparameter_t = ("", "", None)
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Vleistung")), "d")
        leftparameter_t  = (nickname_HG, "Vleistung", tempvalue)

        #modified 08.09.2020 WW:'T-Soll max' added on GUI
        tempvalue_int = int(self.__gdata.values(nickname_WW, "T_setpoint_max"))
        tempvalue = format(tempvalue_int, "2d")
        if (tempvalue_int > 0):
            rightparameter_t = (nickname_WW, "T_setpoint_max", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 10. line
        rightparameter_t = ("", "", None)
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vheizungs_pumpe"))
        leftparameter_t  = (nickname_HG, "Vheizungs_pumpe", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 11. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vzirkula_pumpe"))
        leftparameter_t  = (nickname_HG, "Vzirkula_pumpe", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 12. line
        tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_HG, "Vspeicher_pumpe"))
        leftparameter_t  = (nickname_HG, "Vspeicher_pumpe", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 13. line
        temptextsolar = ""
        if self.__gdata.IsSolarAvailable():
            temptextsolar = "{0} ({1})".format("Solar", self.__gdata.hardwaretype(nickname_SO))

            temptext = "{0:21.39} {1:^57.20}\n".format("Heizgeraet", temptextsolar)
            self.__text.insert("end", temptext)
            self.__text.tag_add("heater", "20.0", "20.39")
            self.__text.tag_config("heater", background="orange", foreground="black")
            self.__text.tag_add("solar", "20.39", "20.90")
            self.__text.tag_config("solar", background="lightgreen", foreground="black")
        else:
            temptext = "{0:21.39} {1:^57.20}\n".format("Heizgeraet", "                  ")
            self.__text.insert("end", temptext)
            self.__text.tag_add("heater", "20.0", "20.39")
            self.__text.tag_config("heater", background="orange", foreground="black")

        betrieb_gesamt_ein = float(self.__gdata.values(nickname_HG, "Cbetrieb_gesamt"))
        tempvalue = format(betrieb_gesamt_ein, ".1f")
        leftparameter_t  = (nickname_HG, "Cbetrieb_gesamt", tempvalue)
        rightparameter_t = ("", "", None)

        if self.__gdata.IsSolarAvailable():
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Tkollektor")), ".1f")
            rightparameter_t = (nickname_SO, "Tkollektor", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 14. line
        betrieb_heizung_ein = float(self.__gdata.values(nickname_HG, "Cbetrieb_heizung"))
        tempvalue = format(betrieb_heizung_ein, ".1f")
        leftparameter_t  = (nickname_HG, "Cbetrieb_heizung", tempvalue)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Tspeicher_unten")), ".1f")
            rightparameter_t = (nickname_SO, "Tspeicher_unten", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 15. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Cbrenner_gesamt")), "d")
        leftparameter_t  = (nickname_HG, "Cbrenner_gesamt", tempvalue)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            f_laufzeit_stunden = float(self.__gdata.values(nickname_SO, "Claufzeit"))
            tempvalue = format(f_laufzeit_stunden, ".1f")
            rightparameter_t = (nickname_SO, "Claufzeit", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 16. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Cbrenner_heizung")), "d")
        leftparameter_t  = (nickname_HG, "Cbrenner_heizung", tempvalue)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_SO, "V_sol_pump"))
            rightparameter_t = (nickname_SO, "V_sol_pump", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 17. line
        tempvalue = format(int(self.__gdata.values(nickname_HG, "Vch_pump_power")), "d")
        leftparameter_t  = (nickname_HG, "Vch_pump_power", tempvalue)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            tempvalue = format(int(self.__gdata.values(nickname_SO, "Vsol_pump_power")), "d")
            rightparameter_t = (nickname_SO, "Vsol_pump_power", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 18. line
        # show:display-code if errors
        displaycode = int(self.__gdata.values(nickname_HG, "Vdisplaycode"))
        if displaycode > 0:
            displaycode_str = self.IntegerToString(displaycode)
        else:
            displaycode_str = "---"

        leftparameter_t  = (nickname_HG, "Vdisplaycode", displaycode_str)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname_SO, "Vkollektor_aus"))
            rightparameter_t = (nickname_SO, "Vkollektor_aus", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 19. line
        # show: cause-code if errors
        causecode = str(format(self.__gdata.values(nickname_HG, "Vcausecode")))
        leftparameter_t  = (nickname_HG, "Vcausecode", causecode)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname_SO, "Vspeicher_voll"))
            rightparameter_t = (nickname_SO, "Vspeicher_voll", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 20. line
        # if setup flag for Hydraulic Switch is True, then display T-value
        temptext = ""
        leftparameter_t  = ("", "", None)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsTempSensor_Hydrlic_Switch():
            Thydraulic_switch = format(float(self.__gdata.values(nickname_HG, "T_hyd_switch")), ".1f")
            if self.IsTemperaturValid(Thydraulic_switch):
                leftparameter_t = (nickname_HG, "T_hyd_switch", Thydraulic_switch)
        if self.__gdata.IsSolarAvailable():
            tempvalue = format(int(self.__gdata.values(nickname_SO, "V_ertrag_stunde")), "d")
            rightparameter_t = (nickname_SO, "V_ertrag_stunde", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 21. line
        leftparameter_t  = ("", "", None)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            if self.__gdata.controller_type_nr() == ht_const.CONTROLLER_TYPE_NR_Cxyz:
                tempvalue = format(float(self.__gdata.values(nickname_SO, "V_ertrag_tag_calc")), ".1f")
                rightparameter_t = (nickname_SO, "V_ertrag_tag_calc", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 22. line
        leftparameter_t  = ("", "", None)
        rightparameter_t = ("", "", None)
        tempvalue = format(float(self.__gdata.values(nickname_HG, "V_pressure")), ".1f")
        if self.IsSensorAvailable(tempvalue):
            leftparameter_t = (nickname_HG, "V_pressure", tempvalue)

        if self.__gdata.IsSolarAvailable():
            if self.__gdata.controller_type_nr() == ht_const.CONTROLLER_TYPE_NR_Cxyz:
                tempvalue = format(float(self.__gdata.values(nickname_SO, "V_ertrag_sum_calc")), ".1f")
                rightparameter_t = (nickname_SO, "V_ertrag_sum_calc", tempvalue)
        self.__DrawColumn(leftparameter_t, rightparameter_t)

        # 23... line(s)
        leftparameter_t  = ("", "", None)
        rightparameter_t = ("", "", None)
        if self.__gdata.IsSolarAvailable():
            tempvalue = format(int(self.__gdata.values(nickname_SO, "V_ch_optimize")), "d")
            rightparameter_t = (nickname_SO, "V_ch_optimize", tempvalue)
            self.__DrawColumn(leftparameter_t, rightparameter_t)

            leftparameter_t  = ("", "", None)
            rightparameter_t = ("", "", None)
            tempvalue = format(int(self.__gdata.values(nickname_SO, "V_dhw_optimize")), "d")
            rightparameter_t = (nickname_SO, "V_dhw_optimize", tempvalue)
            self.__DrawColumn(leftparameter_t, rightparameter_t)

            leftparameter_t  = ("", "", None)
            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Tsp1_3_TS10")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "Tsp1_3_TS10", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Tspeicher_mid")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "Tspeicher_mid", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Tspeicher2_unten")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "Tspeicher2_unten", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "T_kollektor2")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "T_kollektor2", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Tmix_TS4")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "Tmix_TS4", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Twtauscher_TS6")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "Twtauscher_TS6", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            tempvalue = format(float(self.__gdata.values(nickname_SO, "Theat_return_TS8")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                rightparameter_t = (nickname_SO, "Theat_return_TS8", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

            rightparameter_t = ("", "", None)
            if self.__gdata.IsSecondBuffer_SO():
                if self.__gdata.IsReloadbuffer_Option_IJ_SO():
                    tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname_SO, "Vsol_pump2_reload"))
                    rightparameter_t = (nickname_SO, "Vsol_pump2_reload", tempvalue)
                    self.__DrawColumn(leftparameter_t, rightparameter_t)
                else:
                    tempvalue = format(float(self.__gdata.values(nickname_SO, "Vsol_pump2")), ".1f")
                    rightparameter_t = (nickname_SO, "Vsol_pump2", tempvalue)
                    self.__DrawColumn(leftparameter_t, rightparameter_t)

                rightparameter_t = ("", "", None)
                tempvalue = format(int(self.__gdata.values(nickname_SO, "Vsol_pump2_power")), "d")
                rightparameter_t = (nickname_SO, "Vsol_pump2_power", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

                rightparameter_t = ("", "", None)
                tempvalue = format(int(self.__gdata.values(nickname_SO, "V_3weg_mixer_VS1")), "d")
                rightparameter_t = (nickname_SO, "V_3weg_mixer_VS1", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

                rightparameter_t = ("", "", None)
                tempvalue = format(int(self.__gdata.values(nickname_SO, "V_3weg_mixer_VS2")), "d")
                rightparameter_t = (nickname_SO, "V_3weg_mixer_VS2", tempvalue)
                self.__DrawColumn(leftparameter_t, rightparameter_t)

                rightparameter_t = ("", "", None)
                ivalue = int(self.__gdata.values(nickname_SO, "sol_V_spare_1"))
                if ivalue > 0:
                    tempvalue = format(ivalue, "d")
                    rightparameter_t = (nickname_SO, "sol_V_spare_1", tempvalue)
                    self.__DrawColumn(leftparameter_t, rightparameter_t)

        if (self.__gdata.IsSyspartUpdate(nickname_HG) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname_HG, "hexdump") + "\n"
            self.__hextext.insert("end", temptext, "b_or")

        if (self.__gdata.IsSyspartUpdate(nickname_WW) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname_WW, "hexdump") + "\n"
            self.__hextext.insert("end", temptext, "b_bl")

        if (self.__gdata.IsSyspartUpdate(nickname_SO) and self.__hexdump_window):
            temptext = self.__gdata.values(nickname_SO, "hexdump") + "\n"
            self.__hextext.insert("end", temptext, "b_gr")


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
        if self.IsTemperaturValid(Truecklauf):
            temptext = self.__DisplayColumn(nickname, "Truecklauf", Truecklauf)
            if len(temptext) > 0: self.__text.insert("end", temptext)

        Tmischer = format(float(self.__gdata.values(nickname, "Tmischer")), ".1f")
        if self.IsTemperaturValid(Tmischer):
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

        betrieb_gesamt_ein = float(self.__gdata.values(nickname, "Cbetrieb_gesamt"))
        tempvalue = format(betrieb_gesamt_ein, ".1f")
        temptext = self.__DisplayColumn(nickname, "Cbetrieb_gesamt", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        betrieb_heizung_ein = float(self.__gdata.values(nickname, "Cbetrieb_heizung"))
        tempvalue = format(betrieb_heizung_ein, ".1f")
        temptext = self.__DisplayColumn(nickname, "Cbetrieb_heizung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(int(self.__gdata.values(nickname, "Cbrenner_gesamt")), "d")
        temptext = self.__DisplayColumn(nickname, "Cbrenner_gesamt", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        tempvalue = format(int(self.__gdata.values(nickname, "Cbrenner_heizung")), "d")
        temptext = self.__DisplayColumn(nickname, "Cbrenner_heizung", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # Rev.: 0.1.7 https://www.mikrocontroller.net/topic/324673#3970615
        tempvalue = format(int(self.__gdata.values(nickname, "Vch_pump_power")))
        temptext = self.__DisplayColumn(nickname, "Vch_pump_power", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # show:display-code and cause-code if errors
        displaycode = int(self.__gdata.values(nickname, "Vdisplaycode"))
        if displaycode > 0:
            displaycode_str = self.IntegerToString(displaycode)
        else:
            displaycode_str = "---"

        temptext = self.__DisplayColumn(nickname, "Vdisplaycode", displaycode_str)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        causecode = str(self.__gdata.values(nickname, "Vcausecode"))
        temptext = self.__DisplayColumn(nickname, "Vcausecode", causecode)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        # 19. line
        # if setup flag for Hydraulic Switch is True, then display T-value
        if self.__gdata.IsTempSensor_Hydrlic_Switch():
            Thydraulic_switch = format(float(self.__gdata.values(nickname, "T_hyd_switch")), ".1f")
            if self.IsTemperaturValid(Thydraulic_switch):
                temptext = self.__DisplayColumn(nickname, "T_hyd_switch", Thydraulic_switch)
                if len(temptext) > 0: self.__text.insert("end", temptext)


        # 20. line
        systempressure = format(float(self.__gdata.values(nickname, "V_pressure")), ".1f")
        if self.IsSensorAvailable(systempressure):
            temptext = self.__DisplayColumn(nickname, "V_pressure", systempressure)
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
            self.__text.insert("end", "  30   so ta 1E 00 P1 P2  heater     heater      2 wire bus\n")
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

            tempvalue = format(int(self.__gdata.values(nickname, "T_flow_desired")), "d")
            temptext = self.__DisplayColumn(nickname, "T_flow_desired", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tsoll_HK")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tsoll_HK", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tist_HK")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tist_HK", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            TsteuerFB = float(self.__gdata.values(nickname, "Tsteuer_FB"))
            if self.IsTemperaturInValidRange(TsteuerFB):
                tempvalue = format(TsteuerFB, ".1f")
                temptext = self.__DisplayColumn(nickname, "Tsteuer_FB", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "V_hk_pumpe"))
            temptext = self.__DisplayColumn(nickname, "V_hk_pumpe", tempvalue)
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
        tempvalue = format(betriebszeit, ".1f")
        temptext = self.__DisplayColumn(nickname, "Cbetriebs_zeit", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        brenner_ww_ein_counter = int(self.__gdata.values(nickname, "Cbrenner_ww"))
        tempvalue = format(brenner_ww_ein_counter, "d")
        temptext = self.__DisplayColumn(nickname, "Cbrenner_ww", tempvalue)
        if len(temptext) > 0: self.__text.insert("end", temptext)

        if self.__gdata.IsLoadpump_WW():
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

            #modified 08.09.2020 'T-Soll max' added on GUI
            tempvalue_int = int(self.__gdata.values(nickname, "T_setpoint_max"))
            tempvalue = format(tempvalue_int, "2d")
            temptext = self.__DisplayColumn(nickname, "T_setpoint_max", tempvalue)
            if ((len(temptext) > 0) and tempvalue_int > 0): self.__text.insert("end", temptext)

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
            temptext="{0:21.21} ({1})\n".format("Solar", self.__gdata.hardwaretype(nickname))
            self.__text.insert("end", temptext, "b_gr")
            tempvalue = format(float(self.__gdata.values(nickname, "Tkollektor")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tkollektor", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tspeicher_unten")), ".1f")
            temptext = self.__DisplayColumn(nickname, "Tspeicher_unten", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            f_laufzeit_stunden = float(self.__gdata.values(nickname, "Claufzeit"))
            tempvalue = format(f_laufzeit_stunden, ".1f")
            temptext = self.__DisplayColumn(nickname, "Claufzeit", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "V_sol_pump"))
            temptext = self.__DisplayColumn(nickname, "V_sol_pump", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(int(self.__gdata.values(nickname, "V_sol_pump_power")), "d")
            temptext = self.__DisplayColumn(nickname, "V_sol_pump_power", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname, "Vkollektor_aus"))
            temptext = self.__DisplayColumn(nickname, "Vkollektor_aus", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = self.__GetStrJaNein(self.__gdata.values(nickname, "Vspeicher_voll"))
            temptext = self.__DisplayColumn(nickname, "Vspeicher_voll", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(int(self.__gdata.values(nickname, "V_ertrag_stunde")), "d")
            temptext = self.__DisplayColumn(nickname, "V_ertrag_stunde", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            # if Controller is 'Cxyz'-type then display: 'DailySolarGain' and 'TotalSolarGain'
            if self.__gdata.controller_type_nr() == ht_const.CONTROLLER_TYPE_NR_Cxyz:
                tempvalue = format(float(self.__gdata.values(nickname, "V_ertrag_tag_calc")), ".1f")
                temptext = self.__DisplayColumn(nickname, "V_ertrag_tag_calc", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = format(float(self.__gdata.values(nickname, "V_ertrag_sum_calc")), ".1f")
                temptext = self.__DisplayColumn(nickname, "V_ertrag_sum_calc", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(int(self.__gdata.values(nickname, "V_ch_optimize")), "d")
            temptext = self.__DisplayColumn(nickname, "V_ch_optimize", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(int(self.__gdata.values(nickname, "V_dhw_optimize")), "d")
            temptext = self.__DisplayColumn(nickname, "V_dhw_optimize", tempvalue)
            if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tsp1_3_TS10")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "Tsp1_3_TS10", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tspeicher_mid")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "Tspeicher_mid", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tspeicher2_unten")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "Tspeicher2_unten", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "T_kollektor2")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "T_kollektor2", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Tmix_TS4")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "Tmix_TS4", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Twtauscher_TS6")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "Twtauscher_TS6", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            tempvalue = format(float(self.__gdata.values(nickname, "Theat_return_TS8")), ".1f")
            if self.IsTemperaturInValidRange(tempvalue):
                temptext = self.__DisplayColumn(nickname, "Theat_return_TS8", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

            if self.__gdata.IsSecondBuffer_SO():
                # if solar-option I or J active, then reload-system with PS7 pump is running
                if self.__gdata.IsReloadbuffer_Option_IJ_SO():
                    tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vsol_pump2_reload"))
                    temptext = self.__DisplayColumn(nickname, "Vsol_pump2_reload", tempvalue)
                    if len(temptext) > 0: self.__text.insert("end", temptext)
                else:
                #  else solarpump2 PS2/3/4
                    tempvalue = self.__GetStrOnOff(self.__gdata.values(nickname, "Vsol_pump2"))
                    temptext = self.__DisplayColumn(nickname, "Vsol_pump2", tempvalue)
                    if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = format(int(self.__gdata.values(nickname, "Vsol_pump2_power")), "d")
                temptext = self.__DisplayColumn(nickname, "Vsol_pump2_power", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = format(int(self.__gdata.values(nickname, "V_3weg_mixer_VS1")), "d")
                temptext = self.__DisplayColumn(nickname, "V_3weg_mixer_VS1", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                tempvalue = format(int(self.__gdata.values(nickname, "V_3weg_mixer_VS2")), "d")
                temptext = self.__DisplayColumn(nickname, "V_3weg_mixer_VS2", tempvalue)
                if len(temptext) > 0: self.__text.insert("end", temptext)

                ivalue = int(self.__gdata.values(nickname, "sol_V_spare_1"))
                if ivalue > 0:
                    tempvalue = format(ivalue, "d")
                    temptext = self.__DisplayColumn(nickname, "sol_V_spare_1", tempvalue)
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
            self.__text.insert("end", " 866   so ta FF 00 02 62  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 867   so ta FF 00 02 63  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 868   so ta FF 00 02 64  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 870   so ta FF 00 02 66  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 872   so ta FF 00 02 68  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 873   so ta FF 00 02 69  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 874   so ta FF 00 02 6A  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 910   so ta FF 00 02 8E  Solar      MS100/200   EMS2\n")
            self.__text.insert("end", " 913   so ta FF 00 02 91  Solar      MS100/200   EMS2\n")
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
        temptext = " MsgID ;BNr:"
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
