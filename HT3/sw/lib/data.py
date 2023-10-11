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
# Ver:0.1.6  / Datum 10.01.2015 'data_interface' handling added
#                               'max- and default-values' added
# Ver:0.1.7.1/ Datum 04.03.2015 'socket option' activated
#                               logging from ht_utils added
# Ver:0.1.8  / Datum 05.10.2015 'GetUnmixedFlagHK()' update to name
#                               'UnmixedFlagHK()'
#                               'getall_sorted_logitem_names()' added
# Ver:0.1.10 / Datum 18.08.2016 Flag and getter-fkt added for Bus-type
#                               'GetBuscodierungHK' removed
#                               'IsSolarAvailable' added
#                               'create_mylogger' added
#                               'syspartnames()' added
# Ver:0.2    / Datum 29.08.2016 Fkt.doc added
# Ver:0.2.2  / Datum 05.10.2016 'rrdtool_autocreate_draw'-handling now for
#                                 x minutes
# Ver:0.2.x  / Datum 10.05.2017 'accessname'-handling added
# Ver:0.3    / Datum 19.06.2017 'set_param' -handling added
#                               controller_type and bus_type added.
# Ver:0.3.1  / Datum 17.01.2019 'controller_type_nr()' added
#                               'GetAllMixedFlags()' added
#                               'IsTempSensor_Hydrlic_Switch()' added.
#                               'IsSecondCollectorValue_SO()' added.
# Ver:0.3.2  / 2023-03-12       __busmodulAdr string added.
#                               HeaterBusType() and controller_type() handling
#                                modified.
# Ver:0.4    / 2023-09-29       tempfile handling added in create_mylogger()
#                               IsSecondBuffer_SO() modified.
#                               IsReloadbuffer_Option_IJ_SO() added.
#                               setall_values2default() and showall_values() added.
#                               defaultvalue() updated.
#                               getall_nicknames(), getfiltered_sorted_items_with_values() added.
#################################################################

import xml.etree.ElementTree as ET
import sys
import os
import tempfile
import _thread
import ht_utils
import logging
import ht_const


class cdata(ht_utils.clog):
    """
    Class 'cdata' for reading xml-configfile and generating dependent datastructur.
    """
    def __init__(self):
        """
        initialisation of class 'cdata'.
        """
        ht_utils.clog.__init__(self)
        self.__nickname = {}
        self.__logitemHG = {}
        self.__HKcount = 1
        self.__logitemHK1 = {}
        self.__logitemHK2 = {}
        self.__logitemHK3 = {}
        self.__logitemHK4 = {}
        self.__logitemWW = {}
        self.__logitemSO = {}
        self.__logitemDT = {}
        self.__logitemNN = {}
        self.__valuesHG = []
        self.__valuesHK1 = []
        self.__valuesHK2 = []
        self.__valuesHK3 = []
        self.__valuesHK4 = []
        self.__valuesWW = []
        self.__valuesSO = []
        self.__valuesDT = []
        self.__valuesNN = []
        self.__UpdateHG = False
        self.__UpdateHK1 = False
        self.__UpdateHK2 = False
        self.__UpdateHK3 = False
        self.__UpdateHK4 = False
        self.__UpdateWW = False
        self.__UpdateSO = False
        self.__UpdateDT = False
        self.__UpdateNN = False
        # dir's for hardwaretype to be displayed
        self.__hwtypeHG = ""
        self.__hwtypeHK1 = ""
        self.__hwtypeHK2 = ""
        self.__hwtypeHK3 = ""
        self.__hwtypeHK4 = ""
        self.__hwtypeWW = ""
        self.__hwtypeSO = ""
        self.__hwtypeDT = ""
        self.__hwtypeNN = ""
        self.__logitemMapHG = {}
        self.__logitemMapHK1 = {}
        self.__logitemMapHK2 = {}
        self.__logitemMapHK3 = {}
        self.__logitemMapHK4 = {}
        self.__logitemMapWW = {}
        self.__logitemMapSO = {}
        self.__logitemMapDT = {}
        self.__logitemMapNN = {}
        # dir's for Logitem Display-Names
        self.__logitemDisplaynameHG = {}
        self.__logitemDisplaynameHK1 = {}
        self.__logitemDisplaynameHK2 = {}
        self.__logitemDisplaynameHK3 = {}
        self.__logitemDisplaynameHK4 = {}
        self.__logitemDisplaynameWW = {}
        self.__logitemDisplaynameSO = {}
        self.__logitemDisplaynameDT = {}
        self.__logitemDisplaynameNN = {}
        # dir's for Logitem: 'unit' to be displayed
        self.__logitemUnitHG = {}
        self.__logitemUnitHK1 = {}
        self.__logitemUnitHK2 = {}
        self.__logitemUnitHK3 = {}
        self.__logitemUnitHK4 = {}
        self.__logitemUnitWW = {}
        self.__logitemUnitSO = {}
        self.__logitemUnitDT = {}
        self.__logitemUnitNN = {}
        # dir's for Logitem: 'maxvalue'
        self.__maxvalueHG = {}
        self.__maxvalueHK1 = {}
        self.__maxvalueHK2 = {}
        self.__maxvalueHK3 = {}
        self.__maxvalueHK4 = {}
        self.__maxvalueWW = {}
        self.__maxvalueSO = {}
        self.__maxvalueDT = {}
        self.__maxvalueNN = {}
        # dir's for Logitem: 'defaultvalue'
        self.__defaultvalueHG = {}
        self.__defaultvalueHK1 = {}
        self.__defaultvalueHK2 = {}
        self.__defaultvalueHK3 = {}
        self.__defaultvalueHK4 = {}
        self.__defaultvalueWW = {}
        self.__defaultvalueSO = {}
        self.__defaultvalueDT = {}
        self.__defaultvalueNN = {}
        # dir's for Logitem: 'accessname'
        self.__accessnameHG = {}
        self.__accessnameHK1 = {}
        self.__accessnameHK2 = {}
        self.__accessnameHK3 = {}
        self.__accessnameHK4 = {}
        self.__accessnameWW = {}
        self.__accessnameSO = {}
        self.__accessnameDT = {}
        self.__accessnameNN = {}
        # dir's for Logitem: 'minvalue'
        self.__minvalueHG = {}
        self.__minvalueHK1 = {}
        self.__minvalueHK2 = {}
        self.__minvalueHK3 = {}
        self.__minvalueHK4 = {}
        self.__minvalueWW = {}
        self.__minvalueSO = {}
        self.__minvalueDT = {}
        self.__minvalueNN = {}
        # other required values
        self.__accesscontext = {}
        self.__syspartnames = []
        self.__unmixedHK1_HK4 = {}
        self.__LoadpumpWW = False
        self.__SecondBufferSO = False
        self.__SecondCollect_ValueSO = False
        self.__ReloadBuffer_OptionIJ_SO = False
        self.__TempSensor_HydraulicSwitch = 0
        self.__data = {}
        self.__thread_lock = _thread.allocate_lock()
        self.__newdata_available = False
        self.__configfilename = ""
        self.__dbname_sqlite = ""
        self.__sql_enable = False
        self.__dbname_rrdtool = ""
        self.__rrdtool_enable = False
        self.__rrdtool_stepseconds = 0
        self.__rrdtool_starttime_utc = 0
        self._SetDataIf_async()  # "ASYNC":=1; "SOCKET":=2
        self._SetDataIf_raw()   # "RAW"  :=1; "TRX"   :=2
        self.AsyncSerialdevice("/dev/ttyAMA0")
        self.AsyncBaudrate(9600)
        self.AsyncConfig("8N1")
        self.client_cfg_file("./etc/config/ht_proxy_cfg.xml")
        self._logging = None
        self._heater_bustype = ht_const.BUS_TYPE_HT3
        self._IsSolarAvailable = False
        self._sqlite_autoerase_afterSeconds = 0
        self._rrdtool_autocreate_draw_minutes = 0
        # system-infos
        self.__controller_type = ht_const.CONTROLLER_TYPE_STR_Fxyz
        self.__controller_type_nr = ht_const.CONTROLLER_TYPE_NR_Fxyz
        self.__bus_type = "---"
        self.__busmodulAdr = ""


    def setlogger(self, logger):
        """
        setup logger-handler.
        """
        self._logging = logger

    def create_mylogger(self, filepath="", tag="cdata"):
        """
        creating logger with default values (overwrite-able).
        """
        rtnvalue = None
        try:
            ht_utils.clog.__init__(self)
            if len(filepath) == 0:
                filepath = os.path.join(tempfile.gettempdir(),"cdata.log")
            rtnvalue = ht_utils.clog.create_logfile(self, logfilepath=filepath, loggertag=tag)
        except:
            errorstr = "data.create_mylogger();could not create logger-file"
            print(errorstr)
            raise EnvironmentError(errorstr)
        return rtnvalue

    def read_db_config(self, xmlconfigpathname, logger=None):
        """
        reading xml-configfile and setup datastructure.
            The 'shortname' from config-file is used as main-key 'nickname'
            data-structur:
            {nickname:[{itemname:arrayindex},[value1,value2,...],Update-Flag,{itemname:logitem},
                                                                {itemname:displayname},
                                                                {itemname:unit},
                                                                {itemname:maxvalue},
                                                                {itemname:defaultvalue},
                                                                {itemname:minvalue},
                                                                hardwaretype]}
        """
        # init/setup logging-file if not already forced from external call
        if self._logging == None:
            if logger == None:
                self._logging = self.create_mylogger()
            else:
                self._logging = logger
        try:
            self.__configfilename = xmlconfigpathname
            self.__tree = ET.parse(xmlconfigpathname)
        except (NameError, EnvironmentError) as e:
            errorstr = "data.read_db_config();Error;{0} on file:'{1}'".format(e.args[0], xmlconfigpathname)
            self._logging.critical(errorstr)
            print(errorstr)
            raise
        else:
            try:
                self.__root = self.__tree.getroot()
            except:
                errorstr = "data.read_db_config();Error on getroot()"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

            try:
                #  find sql_db-entries
                self.__dbname_sqlite = self.__root.find('dbname_sqlite').text
                for sql_db_part in self.__root.findall('sql-db'):
                    self.__sql_enable = sql_db_part.find('enable').text.upper()
                    if self.__sql_enable == 'ON' or self.__sql_enable == '1':
                        self.__sql_enable = True
                    else:
                        self.__sql_enable = False
                    try:
                        tmperasevalue = int(sql_db_part.find('autoerase_olddata').text)
                        if tmperasevalue > 0:
                            # set autoerase-handling to 86400 seconds * day(s)
                            self._sqlite_autoerase_afterSeconds = 86400 * tmperasevalue
                        else:
                            # autoerase-handling is disabled
                            self._sqlite_autoerase_afterSeconds = 0
                    except:
                        # set autoerase-handling to disabled
                        self._sqlite_autoerase_afterSeconds = 0
            except:
                errorstr = "data.read_db_config();Error on db_sqlite parameter"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

            try:
                # find rrdtool-entries
                self.__dbname_rrdtool = self.__root.find('dbname_rrd').text
                for rrdtool_part in self.__root.findall('rrdtool-db'):
                    self.__rrdtool_enable = rrdtool_part.find('enable').text.upper()
                    if self.__rrdtool_enable == 'ON' or self.__rrdtool_enable == '1':
                        self.__rrdtool_enable = True
                    else:
                        self.__rrdtool_enable = False

                    self.__rrdtool_stepseconds = int(rrdtool_part.find('step_seconds').text)
                    if self.__rrdtool_stepseconds < 60:
                        self.__rrdtool_stepseconds = 60

                    self.__rrdtool_starttime_utc = int(rrdtool_part.find('starttime_utc').text)
                    if self.__rrdtool_starttime_utc < 1344000000 or self.__rrdtool_starttime_utc > 1999999999:
                        self.__rrdtool_starttime_utc = 1344000000

                    try:
                        self._rrdtool_autocreate_draw_minutes = 0
                        autocreate_draw_value = rrdtool_part.find('autocreate_draw').text.upper()
                        if autocreate_draw_value == 'ON':
                            self._rrdtool_autocreate_draw_minutes = 2
                        elif int(autocreate_draw_value) > 0:
                            self._rrdtool_autocreate_draw_minutes = int(autocreate_draw_value)
                        else:
                            self._rrdtool_autocreate_draw_minutes = 0
                    except:
                        self._rrdtool_autocreate_draw_minutes = 0

            except:
                errorstr = "data.read_db_config();Error on db_rrdtool parameter"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

            try:
                #find datainterface-entries
                for data_if in self.__root.findall('data_interface'):
                    commtype = data_if.find('comm_type').text.upper()[0:3]
                    if commtype in ("SOC"):
                        # if "SOCKET" set socket-active
                        self._SetDataIf_socket()
                    else:
                        # else set async-active
                        self._SetDataIf_async()

                    prototype = data_if.find('proto_type').text.upper()[0:3]
                    if prototype in ("TRX"):
                        # force value 'TRX' currently to "RAW"
                        self._SetDataIf_raw()
                        # TBD ## self.__SetDataIf_trx()
                    else:
                        # else set value to "RAW"
                        self._SetDataIf_raw()

                    for param in data_if.findall('parameter'):
                        if param.attrib["name"].upper()[0:3] in ("ASY"):
                            self.AsyncSerialdevice(str(param.find('serialdevice').text))
                            testfilepath = str(param.find('inputtestfilepath').text)
                            if (len(testfilepath) > 0):
                                self.inputtestfilepath(testfilepath)
                            self.AsyncBaudrate(int(param.find('baudrate').text))
                            self.__dataif_param_config = str(param.find('config').text)

                        if param.attrib["name"].upper()[0:3] in ("SOC"):
                            self.__dataif_param_proxy_cfg_file = str(param.find('proxy_config_file').text)
            except:
                errorstr = "data.read_db_config();Error on data_interface parameter"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

            try:
                #  find logging -entries
                for logging_param in self.__root.findall('logging'):
                    path = logging_param.find('path').text
                    default_filename = logging_param.find('default_filename').text
                    self.logpathname(path)
                    self.logfilename(default_filename)
                    #  join both 'path' and 'default_filename' an save it
                    logfilepathname = os.path.normcase(os.path.join(path, default_filename))
                    self.logfilepathname(logfilepathname)
                    #  get and save loglevel
                    self.loglevel(logging_param.find('loglevel').text.upper())
            except:
                errorstr = "data.read_db_config();Error on logging parameter"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

            try:
                #  find amount of heizkreise -entries
                self.__HKcount = int(self.__root.find('anzahl_heizkreise').text)
            except:
                errorstr = "data.read_db_config();Error on anzahl_heizkreise parameter"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

            if self.__HKcount > 4 or self.__HKcount < 1:
                errorstr = "data.read_db_config();Error;amount of:'anzahl_heizkreise' out of range (1...4)"
                self._logging.critical(errorstr)
                raise IndexError(errorstr)

            try:
                syspart = ""
                for syspart in self.__root.findall('systempart'):
                    syspartname = syspart.attrib["name"]
                    self.__syspartnames.append(syspartname)
                    shortname = ""
                    hardwaretype = ""
                    for shortname in syspart.findall('shortname'):
                        shortname = shortname.attrib["name"].upper()
                        if shortname in ("HK1", "HK2", "HK3", "HK4"):
                            if syspart.find('unmixed').text.upper() in ('TRUE'):
                                self.__unmixedHK1_HK4.update({shortname: True})
                            else:
                                self.__unmixedHK1_HK4.update({shortname: False})

                        try:
                            if shortname in ("WW"):
                                self.__LoadpumpWW = True if syspart.find('load_pump').text.upper() == "TRUE" else False

                        except (KeyError, IndexError, AttributeError) as e:
                            errorstr = "data.read_db_config();Error on xml-tag:{0}".format(e.args[0])
                            self._logging.critical(errorstr)
                            print(errorstr)

                    hardwaretype = syspart.find('hardwaretype').text

                    # set nicknames
                    self._setnickname(shortname, syspartname)
                    logitem = ""
                    try:
                        for logitem in syspart.findall('logitem'):
                            name = logitem.attrib["name"]
                            maxvalue = logitem.find('maxvalue').text
                            default = logitem.find('default').text
                            unit = logitem.find('unit').text
                            displayname = logitem.find('displayname').text
        ##### unused values from xml-file in data-context ###
        ##                    datatype= logitem.find('datatype').text
        ##                    datause = logitem.find('datause').text
        ##                    values=[datatype,datause]
        #####
                            try:
                                accessname = logitem.find('accessname').text
                            except:
                                accessname = ""

                            try:
                                set_parameter = logitem.find('set_param').text
                            except:
                                set_parameter = ""

                            try:
                                minvalue = logitem.find('minvalue').text
                            except:
                                minvalue = None

                            # add itemname and values to table
                            self.update(shortname, logitem=name, value=default, displayname=displayname, unit=unit, 
                                        hwtype=hardwaretype, maxvalue=maxvalue, default=default, 
                                        accessname=accessname, set_parameter=set_parameter, minvalue=minvalue )
                        else:
                            if not len(logitem):
                                errorstr = "data.read_db_config();Error;AttributeError(logitem)"
                                self._logging.critical(errorstr)
                                raise AttributeError(errorstr)
                    except:
                        errorstr = """data.read_db_config();Error on reading items:
                            name:{0};
                            maxvalue:{1};
                            unit:{2};
                            displayname:{3}""".format(name, maxvalue, unit, displayname)
                        print(errorstr)
                        self._logging.critical(errorstr)
                        raise AttributeError(errorstr)

                else:
                    if not len(syspart):
                        errorstr = "data.read_db_config();Error;AttributeError(syspart)"
                        self._logging.critical(errorstr)
                        raise AttributeError(errorstr)

            except (KeyError, IndexError, AttributeError) as e:
                if not type(e) == AttributeError:
                    errorstr = "data.read_db_config();Error on xml-tag:{0}".format(e.args[0])
                else:
                    errorstr = "data.read_db_config();Error on xml-tag"
                print(errorstr)
                self._logging.critical(errorstr)
                raise

    def configfilename(self, xmlconfigpathname=""):
        """
        return and setup of used xml-config filename.
        """
        if len(xmlconfigpathname):
            self.__configfilename = xmlconfigpathname
        return self.__configfilename

    def db_sqlite_filename(self, xmlconfigpathname=""):
        """
        return and setup of used sqlite-db  filename.
        """
        if len(xmlconfigpathname):
            self.__configfilename = xmlconfigpathname
            self.read_db_config(xmlconfigpathname)
        return self.__dbname_sqlite

    def is_sql_db_enabled(self):
        """
        return True/False for sql-db config-tag 'enable'.
        """
        return self.__sql_enable

    def db_rrdtool_filename(self, xmlconfigpathname=""):
        """
        return and setup of used rrdtool-db filename.
        """
        if len(xmlconfigpathname):
            self.__configfilename = xmlconfigpathname
            self.read_db_config(xmlconfigpathname)
        return self.__dbname_rrdtool

    def db_rrdtool_filepathname(self, xmlconfigpathname=""):
        """
        return a tuple of absolute-path and filename as: (path, filename).
         This is independent from OS.
        """
        (normpath, filename) = (".", "")
        if len(xmlconfigpathname):
            (path, filename) = os.path.split(xmlconfigpathname)
        else:
            (path, filename) = os.path.split(self.__dbname_rrdtool)
        normpath = os.path.abspath(os.path.normcase(path))
        return (normpath, filename)

    def is_db_rrdtool_enabled(self):
        """
        return True/False for rrdtool-db config-tag 'enable'.
        """
        return self.__rrdtool_enable

    def db_rrdtool_stepseconds(self):
        """
        return value 'step_seconds' for rrdtool-db.
        """
        return self.__rrdtool_stepseconds

    def db_rrdtool_starttime_utc(self):
        """
        return value 'starttime_utc' for rrdtool-db.
        """
        return self.__rrdtool_starttime_utc

    def heatercircuits_amount(self, hc_counts=0):
        """
        return the number of heater-circuits.
         Value is set in configuration-file or is
         dynamicly updated in the application.
        """
        if hc_counts > self.__HKcount:
            self.__HKcount = hc_counts
        return self.__HKcount

    def _setnickname(self, shortname, longname):
        """
        save nickname attached to longname. Additional the assignment for
        'Systempart' to the attached value-arrays are done here.
         Values are set in configuration-file.
        """
        shortname = shortname.upper()[0:3]
        try:
            if not len(shortname):
                errorstr = "data._setnickname();Error; shortname undefined')"
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(longname):
                errorstr = "data._setnickname();Error; longname undefined')"
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            self.__nickname.update({shortname: longname})
            if "HG" in shortname:
                self.__data.update({"HG": [self.__logitemHG,
                                          self.__valuesHG,
                                          self.__UpdateHG,
                                          self.__logitemMapHG,
                                          self.__logitemDisplaynameHG,
                                          self.__logitemUnitHG,
                                          self.__maxvalueHG,
                                          self.__defaultvalueHG,
                                          self.__accessnameHG,
                                          self.__minvalueHG,
                                          self.__hwtypeHG]})
            elif "HK1" in shortname:
                self.__data.update({"HK1": [self.__logitemHK1,
                                          self.__valuesHK1,
                                          self.__UpdateHK1,
                                          self.__logitemMapHK1,
                                          self.__logitemDisplaynameHK1,
                                          self.__logitemUnitHK1,
                                          self.__maxvalueHK1,
                                          self.__defaultvalueHK1,
                                          self.__accessnameHK1,
                                          self.__minvalueHK1,
                                          self.__hwtypeHK1]})
            elif "HK2" in shortname:
                self.__data.update({"HK2": [self.__logitemHK2,
                                          self.__valuesHK2,
                                          self.__UpdateHK2,
                                          self.__logitemMapHK2,
                                          self.__logitemDisplaynameHK2,
                                          self.__logitemUnitHK2,
                                          self.__maxvalueHK2,
                                          self.__defaultvalueHK2,
                                          self.__accessnameHK2,
                                          self.__minvalueHK2,
                                          self.__hwtypeHK2]})

            elif "HK3" in shortname:
                self.__data.update({"HK3": [self.__logitemHK3,
                                          self.__valuesHK3,
                                          self.__UpdateHK3,
                                          self.__logitemMapHK3,
                                          self.__logitemDisplaynameHK3,
                                          self.__logitemUnitHK3,
                                          self.__maxvalueHK3,
                                          self.__defaultvalueHK3,
                                          self.__accessnameHK3,
                                          self.__minvalueHK3,
                                          self.__hwtypeHK3]})

            elif "HK4" in shortname:
                self.__data.update({"HK4": [self.__logitemHK4,
                                          self.__valuesHK4,
                                          self.__UpdateHK4,
                                          self.__logitemMapHK4,
                                          self.__logitemDisplaynameHK4,
                                          self.__logitemUnitHK4,
                                          self.__maxvalueHK4,
                                          self.__defaultvalueHK4,
                                          self.__accessnameHK4,
                                          self.__minvalueHK4,
                                          self.__hwtypeHK4]})

            elif "WW" in shortname:
                self.__data.update({"WW": [self.__logitemWW,
                                          self.__valuesWW,
                                          self.__UpdateWW,
                                          self.__logitemMapWW,
                                          self.__logitemDisplaynameWW,
                                          self.__logitemUnitWW,
                                          self.__maxvalueWW,
                                          self.__defaultvalueWW,
                                          self.__accessnameWW,
                                          self.__minvalueWW,
                                          self.__hwtypeWW]})

            elif "SO" in shortname:
                self.__data.update({"SO": [self.__logitemSO,
                                          self.__valuesSO,
                                          self.__UpdateSO,
                                          self.__logitemMapSO,
                                          self.__logitemDisplaynameSO,
                                          self.__logitemUnitSO,
                                          self.__maxvalueSO,
                                          self.__defaultvalueSO,
                                          self.__accessnameSO,
                                          self.__minvalueSO,
                                          self.__hwtypeSO]})

            elif "DT" in shortname:
                self.__data.update({"DT": [self.__logitemDT,
                                          self.__valuesDT,
                                          self.__UpdateDT,
                                          self.__logitemMapDT,
                                          self.__logitemDisplaynameDT,
                                          self.__logitemUnitDT,
                                          self.__maxvalueDT,
                                          self.__defaultvalueDT,
                                          self.__accessnameDT,
                                          self.__minvalueDT,
                                          self.__hwtypeDT]})

            else:
                self.__data.update({"NN": [self.__logitemNN,
                                          self.__valuesNN,
                                          self.__UpdateNN,
                                          self.__logitemMapNN,
                                          self.__logitemDisplaynameNN,
                                          self.__logitemUnitNN,
                                          self.__maxvalueNN,
                                          self.__defaultvalueNN,
                                          self.__accessnameNN,
                                          self.__minvalueNN,
                                          self.__hwtypeNN]})

        except (NameError, AttributeError) as e:
            errorstr = "data._setnickname();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def getlongname(self, shortname):
        """
        return the 'systempart' longname attached to input:'shortname'.
         Only the first three chars of 'shortname' are used, upper-
         and lower-case is possible.
         Undefined 'shortnames' returns: 'None'
        """
        try:
            return self.__nickname[shortname.upper()[0:3]]
        except (KeyError, IndexError, AttributeError) as e:
            errorstr = "data.getlongname();Error;longname'{0}' not found".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)
            return None

    def getall_sorted_logitem_names(self, nickname, rtn_internal_itemname=False):
        """
        returns sorted list of logitem-names for the nickname.
        """
        nickname = nickname.upper()[0:3]
        all_logitem_names = []
        length = 0
        if nickname in self.__nickname:
            length = len(self.__data[nickname][0])
            for x in range(0, length):
                all_logitem_names.append("")

            for (key, value) in self.__data[nickname][0].items():
                itemname = key
                if not rtn_internal_itemname:
                    itemname = self.__data[nickname][3][key]
                all_logitem_names[int(value)] = itemname
            return all_logitem_names
        else:
            errorstr = "getall_sorted_logitem_names();Error;nickname'{0}' not found".format(nickname)
            print(errorstr)
            self._logging.critical(errorstr)
            return None

    def getfiltered_sorted_items_with_values(self, nickname):
        """
        This function returns the sorted tuple-array of items and attached values
         except undefined (out of range) temperaturvalues.
        """
        nickname = nickname.upper()[0:3]
        all_logitem_names = self.getall_sorted_logitem_names(nickname)
        rtntuple_array = []
        defined = True
        for itemname in all_logitem_names:
            if not itemname == "hexdump":
                internal_itemname = itemname.replace("_", "").lower()
                index = int(self.__data[nickname][0][internal_itemname])
                value = self.__data[nickname][1][index]
                if self.Is_Value_defined((itemname, value)):
                    rtntuple_array.append((itemname, value))
        return rtntuple_array

    def getall_sorted_items_with_values(self, nickname):
        """
        This function returns the sorted tuple-array of items and attached values.
        """
        nickname = nickname.upper()[0:3]
        all_logitem_names = self.getall_sorted_logitem_names(nickname)
        rtntuple_array = []
        for itemname in all_logitem_names:
            if not itemname == "hexdump":
                internal_itemname = itemname.replace("_", "").lower()
                index = int(self.__data[nickname][0][internal_itemname])
                value = self.__data[nickname][1][index]
                rtntuple_array.append((itemname, value))
        return rtntuple_array

    def getall_sorted_accessnames(self, nickname):
        """
        returns sorted list of access-names for the nickname.
        """
        nickname = nickname.upper()[0:3]
        all_sorted_access_names = []
        length = 0
        if nickname in self.__nickname:
            length = len(self.__data[nickname][0])
            for x in range(0, length):
                all_sorted_access_names.append("")

            for (key, value) in self.__data[nickname][0].items():
                accessname = self.__data[nickname][8][key]
                all_sorted_access_names[int(value)] = accessname
            return all_sorted_access_names
        else:
            errorstr = "getall_sorted_accessnames();Error;nickname'{0}' not found".format(nickname)
            print(errorstr)
            self._logging.critical(errorstr)
            return None

    def getall_accessnames(self):
        """ returns sorted list of access-names for all available nicknames. """
        all_access_names = {}
        for nickname in self.__nickname:
            all_access_names.update({nickname:self.getall_sorted_accessnames(nickname)})
        return all_access_names

    def getall_nicknames(self):
        """ returns all nicknames """
        return self.__nickname

    def setall_values2default(self):
        """ set all default-values for nicknames (without 'DT'). """
        for nickname in self.__nickname:
            if nickname.upper() in "DT":
                pass
            else:
                for (item, value) in self.__data[nickname][0].items():
                    defaultvalue = self.defaultvalue(nickname, item)
                    self.update(nickname, logitem=item, value=defaultvalue, default=defaultvalue)

    def showall_values(self):
        """ printout all values for all nicknames """
        for nickname in self.__nickname:
            for (item, value) in self.__data[nickname][0].items():
                defaultvalue = self.defaultvalue(nickname, item)
                savedvalue=self.values(nickname, item)
                print("showall_values(); nickname:{};item:{};value:{};default:{}".format(nickname, item, savedvalue, defaultvalue))

    def update(self, nickname, logitem, value=0.0, displayname="", unit="", hwtype="",
               maxvalue=100.0, default=0.0, accessname="", set_parameter="", minvalue=None):
        """
        updates an already created data.member (logitem) with the new value or
         will create it, if not yet available.
         parameter 'logitem' is assigned to 'value' (default:=0)
         data-structur:
          {nickname:[ {itemname:arrayindex},[value1,value2,...],Update-Flag,{itemname:logitem},
                                                                        {itemname:displayname},
                                                                        {itemname:unit},
                                                                        {itemname:maxvalue},
                                                                        {itemname:defaultvalue},
                                                                        {itemname:accessname},
                                                                        {itemname:minvalue},
                                                                        hardwaretype]}
        """

        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.update();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(itemname):
                errorstr = "data.update();Error;itemname:'{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    # update value, get index first from dir{itemname:index}
                    index = int(self.__data[nickname][0][itemname])
                    self.__data[nickname][1][index] = value
                    # set 'IsSyspartUpdate' true
                    self.__data[nickname][2] = True
                    if len(displayname) > 0:
                        self.__data[nickname][4][itemname] = displayname
                    if len(unit) > 0:
                        self.__data[nickname][5][itemname] = unit
                    if maxvalue != 100.0:
                        self.__data[nickname][6][itemname] = maxvalue
                    if default != 0.0:
                        self.__data[nickname][7][itemname] = default
                    if len(accessname) > 0:
                        self.__data[nickname][8][itemname] = accessname
                    if minvalue != -1000.0:
                        self.__data[nickname][9][itemname] = minvalue
                        
                else:
                    # add new item and value, index is the current array-length
                    # and is set to dir{itemname:index}
                    index = len(self.__data[nickname][1])
                    self.__data[nickname][0].update({itemname: index})
                    self.__data[nickname][1].append(value)
                    # set internal itemname to external logitem
                    self.__data[nickname][3].update({itemname: logitem})

                    if not displayname == None and len(displayname) > 0:
                        self.__data[nickname][4].update({itemname: displayname})
                    else:
                        self.__data[nickname][4].update({itemname: ""})

                    if not unit == None and len(unit) > 0:
                        self.__data[nickname][5].update({itemname: unit})
                    else:
                        self.__data[nickname][5].update({itemname: ""})

                    self.__data[nickname][6].update({itemname: maxvalue})
                    self.__data[nickname][7].update({itemname: default})

                    if len(set_parameter) > 0:
                        cmd_parameter = set_parameter
                    else:
                        cmd_parameter = None
                    if not accessname == None and len(accessname) > 0:
                        # setup accessname to tuple:
                        #   (nickname, external logitem, internal itemname. command-parameter)
                        self.__accesscontext.update({accessname: (nickname, logitem, itemname, cmd_parameter)})
                    else:
                        # setup dummy_accessname to tuple:
                        #   (nickname, external logitem, internal itemname. command-parameter)
                        accessname = str(nickname).lower() + "_unused_" + str(index)
                        self.__accesscontext.update({accessname: (nickname, logitem, itemname, cmd_parameter)})

                    self.__data[nickname][8].update({itemname: accessname})

                    self.__data[nickname][9].update({itemname: minvalue})
                       

                if not hwtype == None and len(hwtype) > 0:
                    self.__data[nickname][10] = hwtype
            else:
                errorstr = "data.update();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)

            self.__thread_lock.acquire()
            self.__newdata_available = True
            self.__thread_lock.release()

        except (KeyError, NameError, AttributeError) as e:
            errorstr = "data.update();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)
            self.__thread_lock.acquire()
            self.__newdata_available = False
            self.__thread_lock.release()

    def values(self, nickname, logitem=""):
        """
        returns all values (array) for 'nickname or value (single one) for
         'nickname' and 'logitem'.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            self.__thread_lock.acquire()
            if not len(nickname):
                errorstr = "data.values();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if len(itemname):
                    if itemname in self.__data[nickname][0]:
                        index = int(self.__data[nickname][0][itemname])
                        return self.__data[nickname][1][index]
                    else:
                        errorstr = "data.values();Error;itemname:'{0}' not found".format(logitem)
                        self._logging.critical(errorstr)
                        raise NameError(errorstr)
                else:
                    return self.__data[nickname][1]
            else:
                errorstr = "data.values();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.values();Error;{0}".format(e.args[0])
            self._logging.critical(errorstr)

        finally:
            self.__thread_lock.release()

    def displayname(self, nickname, logitem):
        """
        returns the 'name' to be displayed for the logitem.
         Value is set in configuration-file.
         parameters 'nickname' and 'logitem' are required.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.displayname();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(logitem):
                errorstr = "data.displayname();Error;logitem: '{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    return str(self.__data[nickname][4][itemname])
                else:
                    errorstr = "data.displayname();Error;itemname:'{0}' not found in nicknames:'{1}'".format(logitem, nickname)
                    self._logging.critical(errorstr)
                    raise NameError(errorstr)
            else:
                errorstr = "data.displayname();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.displayname();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def displayunit(self, nickname, logitem):
        """
        returns the 'unit' to be displayed for the logitem.
         Value is set in configuration-file.
         parameters 'nickname' and 'logitem' are required.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.displayunit();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(logitem):
                errorstr = "data.displayunit();Error;logitem: '{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    return self.__data[nickname][5][itemname]
                else:
                    errorstr = "data.displayunit();Error;itemname:'{0}' not found".format(logitem)
                    self._logging.critical(errorstr)
                    raise NameError(errorstr)
            else:
                errorstr = "data.displayunit();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.displayunit();Error;displayname();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def minvalue(self, nickname, logitem):
        """
        returns the 'minvalue' for the logitem.
         Value is set in configuration-file.
         parameters 'nickname' and 'logitem' are required.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.minvalue();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(logitem):
                errorstr = "data.minvalue();Error;logitem: '{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    #check for float- or int-value and return the correct type
                    if "." in (str(self.__data[nickname][9][itemname])):
                        return float(self.__data[nickname][9][itemname])
                    else:
                        return int(self.__data[nickname][9][itemname])
                else:
                    errorstr = "data.minvalue();Error;itemname:'{0}' not found".format(logitem)
                    self._logging.critical(errorstr)
                    raise NameError(errorstr)
            else:
                errorstr = "data.minvalue();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.minvalue();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def maxvalue(self, nickname, logitem):
        """
        returns the 'maxvalue' for the logitem.
         Value is set in configuration-file.
         parameters 'nickname' and 'logitem' are required.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.maxvalue();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(logitem):
                errorstr = "data.maxvalue();Error;logitem: '{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    #check for float- or int-value and return the correct type
                    if "." in (str(self.__data[nickname][6][itemname])):
                        return float(self.__data[nickname][6][itemname])
                    else:
                        return int(self.__data[nickname][6][itemname])
                else:
                    errorstr = "data.maxvalue();Error;itemname:'{0}' not found".format(logitem)
                    self._logging.critical(errorstr)
                    raise NameError(errorstr)
            else:
                errorstr = "data.maxvalue();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.maxvalue();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def defaultvalue(self, nickname, logitem):
        """
        returns the 'default'-value for the logitem.
         Value is set in configuration-file.
         parameters 'nickname' and 'logitem' are required.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.defaultvalue();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(logitem):
                errorstr = "data.defaultvalue();Error;logitem: '{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    default = self.__data[nickname][7][itemname]
                    if not default in ['"','""']:
                        #check for float- or int-value and return the correct type
                        if "." in str(default):
                            return float(default)
                        else:
                            return int(default)
                    else:
                        return default
                else:
                    errorstr = "data.defaultvalue();Error;itemname:'{0}' not found".format(logitem)
                    self._logging.critical(errorstr)
                    raise NameError(errorstr)
            else:
                errorstr = "data.defaultvalue();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.defaultvalue();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def accessname(self, nickname, logitem):
        """
        returns the 'accessname' for the logitem.
         Value is set in configuration-file.
         parameters 'nickname' and 'logitem' are required.
        """
        nickname = nickname.upper()[0:3]
        itemname = logitem.replace("_", "").lower()
        try:
            if not len(nickname):
                errorstr = "data.accessname();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if not len(logitem):
                errorstr = "data.accessname();Error;logitem: '{0}' undefined".format(logitem)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    return self.__data[nickname][8][itemname]
                else:
                    errorstr = "data.accessname();Error;itemname:'{0}' not found".format(logitem)
                    self._logging.critical(errorstr)
                    raise NameError(errorstr)
            else:
                errorstr = "data.accessname();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.accessname();Error;{0}".format(e.args[0])
            print(errorstr)
            self._logging.critical(errorstr)

    def hardwaretype(self, nickname):
        """
        returns the hardwaretype read from configuration-file.
        """
        nickname = nickname.upper()[0:3]
        try:
            if not len(nickname):
                errorstr = "data.hardwaretype();Error;nickname: '{0}' undefined".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
            if nickname in self.__nickname:
                return str(self.__data[nickname][10])
            else:
                errorstr = "data.hardwaretype();Error;nickname:'{0}' not found".format(nickname)
                self._logging.critical(errorstr)
                raise NameError(errorstr)
        except(KeyError, NameError, AttributeError) as e:
            errorstr = "data.hardwaretype();Error;{0}".format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)

    def controller_type(self, c_type=""):
        """returns/sets the found controller-type as string.
            if heaterbus-type EMS was detected then Cxyz-controller is default set.
        """
        if len(c_type) > 0:
            self.__controller_type = c_type
        return self.__controller_type

    def controller_type_nr(self, i_type = -1):
        """returns/sets the controller-type-number as int.
        """
        if (i_type != -1):
            self.__controller_type_nr = int(i_type)
        return int(self.__controller_type_nr)


    def bus_type(self, b_type=""):
        """returns/sets the found bus-type as string."""
        if len(b_type) > 0:
            self.__bus_type = b_type
        return self.__bus_type

    def busmodulAdr(self, b_modulAdr=""):
        """returns/sets the found busmodul Adresses as string."""
        if len(b_modulAdr) > 0:
            self.__busmodulAdr = b_modulAdr
        return self.__busmodulAdr

    def get_access_context(self, accessname):
        """
        returns the context attached to 'accessname' as tuple.
         accessname-Values are set in configuration-file or set to
         default-values if there aren't any.
         The returned tuple-values are defined as:
           (Systempart-Nickname, logitem, itemname)
             where:
               'Nickname'  is the 'shortname' from configuration-file.
               'logitem'   is the logitem-name from configuration-file.
               'itemname'  is the internal application-used access-name.
               'set_param' is the set-parameter from configuration-file.
        returns '("", "", "", "")' if there isn't any context available.
        """
        rtntuple = ("", "", "", "")
        try:
            if accessname in self.__accesscontext:
                rtntuple = self.__accesscontext.get(accessname)
        except:
            pass
        return rtntuple

    def get_access_names(self):
        return self.__accesscontext

    def _SetDataIf_async(self):
        """
        setup Data-interface to type: async.
        """
        self.__dataif_commtype = 1

    def IsDataIf_async(self):
        """
        returns True if data-Interface is configured to be in asychron-mode, else False.
         Value is set in configuration-file.
        """
        return True if (self.__dataif_commtype == 1) else False

    def _SetDataIf_socket(self):
        """
        setup Data-interface to type: socket.
        """
        self.__dataif_commtype = 2

    def IsDataIf_socket(self):
        """
        returns True if data-Interface is configured to be in socket-mode, else False.
         Value is set in configuration-file.
        """
        return True if (self.__dataif_commtype == 2) else False

    def dataif_comm_type_str(self):
        """
        returns the currently defined communication-mode as string.
         Values are "ASYNC" or "SOCKET".
        """
        rtnstr = ""
        if self.IsDataIf_async():
            rtnstr = "ASYNC"
        else:
            if self.IsDataIf_socket():
                rtnstr = "SOCKET"
        return rtnstr

    def _SetDataIf_raw(self):
        """
        setup Data-interface to protocoll-type: raw.
        """
        self.__dataif_prototype = 1

    def _SetDataIf_trx(self):
        """
        setup Data-interface to protocoll-type: TX/RX.
        """
        self.__dataif_prototype = 2

    def IsDataIf_raw(self):
        """
        returns True if data-Interface has RAW-mode protokoll configuration else False.
         Values is set in configuration-file.
        """
        return True if (self.__dataif_prototype == 1) else False

    def IsDataIf_trx(self):
        """
        returns True if data-Interface has TRX-mode protokoll configuration else False.
         Value is set in configuration-file.
        """
        return True if (self.__dataif_prototype == 2) else False

    def dataif_protocoll_type_str(self):
        """
        returns the protocoll-type as string-value.
        """
        rtnstr = ""
        if self.IsDataIf_raw():
            rtnstr = "RAW"
        if self.IsDataIf_trx():
            rtnstr = "TRX"
        return rtnstr

    def AsyncSerialdevice(self, serialdevice=None):
        """
        returns the currently defined devicename for async-mode.
         Value is set in configuration-file.
        """
        if serialdevice != None:
            self.__dataif_param_serialdevice = serialdevice
        return self.__dataif_param_serialdevice

    def AsyncBaudrate(self, baudrate=None):
        """
        returns the currently defined Baudrate for async-mode.
         Value is set in configuration-file.
        """
        if baudrate != None:
            self.__dataif_param_baudrate = baudrate
        return self.__dataif_param_baudrate

    def AsyncConfig(self, config=None):
        """
        returns the currently defined Parameter for async-mode (fixed to 8N1).
         Value is set in configuration-file.
        """
        if config != None:
            self.__dataif_param_config = config
        return self.__dataif_param_config

    def inputtestfilepath(self, testfilepath=None):
        """
        return and setup of testfilename and path.
        """
        if testfilepath != None:
            self.__dataif_param_testfilepath = testfilepath
        return self.__dataif_param_testfilepath

    def client_cfg_file(self, client_cfg_file=None):
        """
        returns the currently defined 'client configuration file' for socket-purposes.
        """
        if client_cfg_file != None:
            self.__dataif_param_proxy_cfg_file = client_cfg_file
        return self.__dataif_param_proxy_cfg_file

    def IsAnyUpdate(self):
        """
        returns True/False if any update was set.
        """
        return self.__newdata_available

    def UpdateRead(self):
        """
        resets the status of new-data available flag.
        """
        self.__thread_lock.acquire()
        self.__newdata_available = False
        self.__thread_lock.release()

    def IsSyspartUpdate(self, nickname):
        """
        returns True/False for parameter 'nickname' if new data is available and resets the flag.
        """
        nickname = nickname.upper()[0:3]
        self.__thread_lock.acquire()
        Rtn = self.__data[nickname][2]
        self.__data[nickname][2] = False
        self.__thread_lock.release()
        return Rtn

    def UnmixedFlagHK(self, nickname, unmixed=None):
        """
        returns True for parameter 'nickname' if heater-circuit (HK1..4) has no mixer else False.
         Values are set in configuration-file.
        """
        nickname = nickname.upper()[0:3]
        if unmixed != None:
            self.__unmixedHK1_HK4.update({nickname: unmixed})
        return bool(self.__unmixedHK1_HK4.get(nickname))

    def GetAllMixerFlags(self):
        """
        returns True-values if heater-circuits has a mixer, else False.
         a list of 4 values will be returned (HK1...4)
        """
        mixed_flags = []
        for HeizkreisNummer in range(1, 5):
            nickname = "HK" + str(HeizkreisNummer)
            mixed = 1 if not bool(self.UnmixedFlagHK(nickname)) else 0
            # set result to tuple rtn-values, starting with index:=0
            mixed_flags.append(mixed)
        return mixed_flags

    def IsLoadpump_WW(self):
        """
        returns True, if heater-external water-loadpump is available else False.
         Value is set in configuration-file.
        """
        return self.__LoadpumpWW


    def IsSecondBuffer_SO(self, Secondbuffer=None):
        """
        returns True, if second solar-buffer is available else False.
         Value is set automatic on temperature sensor-detection.
        """
        if Secondbuffer != None:
            self.__SecondBufferSO = bool(Secondbuffer)
        return bool(self.__SecondBufferSO)

    def IsSecondCollectorValue_SO(self, SecondValue=None):
        """
        returns True, if second collector values are available else False.
         Value is set during decoding of MsgID 260.
        """
        if SecondValue != None:
            self.__SecondCollect_ValueSO = bool(SecondValue)
        return bool(self.__SecondCollect_ValueSO)

    def IsReloadbuffer_Option_IJ_SO(self, ReloadBuffer=None):
        """
        returns True, if ReloadBuffer is used else False.
         Value is set if TS10 solarsensor is available.
        """
        if ReloadBuffer != None:
            self.__ReloadBuffer_OptionIJ_SO = bool(ReloadBuffer)
        return bool(self.__ReloadBuffer_OptionIJ_SO)

    def IsTempSensor_Hydrlic_Switch(self, SensorAvailable=None):
        """
        returns 1, if the Temperatursensor at Hydraulic Switch is available else 0.
         Value is set during decoding of MsgID 25 and 30.
        """
        if SensorAvailable != None:
            self.__TempSensor_HydraulicSwitch = int(SensorAvailable)
        return int(self.__TempSensor_HydraulicSwitch)

    def Is_Value_defined(self, logitem_value_tuple):
        """ returns True, if value is available and in valid range """
        rtnvalue = True
        (logitem, value) = logitem_value_tuple
        if value == None or len(logitem) == 0:
            rtnvalue = False
        else:
            # check for Temperatur-logitemname and test the range
            if ('T' in logitem) and logitem[0] == 'T':
                rtnvalue = ht_utils.cht_utils.IsTempInRange(self, value)
#                print("logitem:{}; value:{}; rtnvalue:{}".format(logitem,value,rtnvalue))
        return rtnvalue

    def HeaterBusType(self, bustype=None):
        """
        returns and setup the heater-bustype.
         The available values are defined in: ht_const.py.
         If bus-telegrams are EMS-types, then Cxyz controllertypes are set.
        """
        if not bustype == None:
            self._heater_bustype = bustype

        # change controller-type only, if default value is set
        if self._heater_bustype == ht_const.BUS_TYPE_EMS:
            if self.__controller_type_nr == ht_const.CONTROLLER_TYPE_NR_Fxyz:
                self.__controller_type_nr = ht_const.CONTROLLER_TYPE_NR_Cxyz
                self.__controller_type    = ht_const.CONTROLLER_TYPE_STR_Cxyz
        else:
            if self.__controller_type_nr == ht_const.CONTROLLER_TYPE_NR_Cxyz:
                self.__controller_type_nr = ht_const.CONTROLLER_TYPE_NR_Fxyz
                self.__controller_type    = ht_const.CONTROLLER_TYPE_STR_Fxyz
            
        return self._heater_bustype

    def IsSolarAvailable(self, available=None):
        """
        returns and setup solar systempart availability.
        """
        if not available == None:
            self._IsSolarAvailable = available
        return self._IsSolarAvailable

    def syspartnames(self):
        """ return of all system-partnames.
                read from configuration.
        """
        return self.__syspartnames

    def Sqlite_autoerase_seconds(self):
        return self._sqlite_autoerase_afterSeconds

    def IsAutocreate_draw(self):
        return int(self._rrdtool_autocreate_draw_minutes)

#--- class cdata end ---#

if __name__ == "__main__":
    ########
    ##
    # testtype:= 0 -> basic 'cdata'-classtest
    # testtype:= 1 -> test including xml-configfile-data extract
    #
    # data-structur:
    #   {nickname:[ {itemname:arrayindex},[value1,value2,...],Update-Flag,{itemname:logitem},
    #                                                                     {itemname:displayname},
    #                                                                     {itemname:unit},
    #                                                                     {itemname:maxvalue},
    #                                                                     {itemname:default},
    #                                                                     {itemname:accessname},
    #                                                                     {itemname:minvalue},
    #                                                                     hardwaretype]}
    #
    testtype = 1

    if testtype == 0:
        #---------------- testtype=0 -------------------
        data = cdata()
        data.setlogger(data.create_mylogger())
        print("-- setup nicknames --")
        data._setnickname("HG", "heizgeraet")
        data._setnickname("Hklein", "heizkreis")
        data._setnickname("HK1", "heizkreis1")
        data._setnickname("HK2", "heizkreis2")
        data._setnickname("HK3", "heizkreis3")
        data._setnickname("HK4", "heizkreis4")
        data._setnickname("WW", "warmwasser")
        data._setnickname("SO", "solar")
        data._setnickname("DT", "datetime")
        data._setnickname("data", "dadadata")
        #----------------
        print("-- updata data --")
        data.update("SO", "T_Collector")
        data.update("SO", "T_Collector", 33.5)
        data.update("SO", "T_Soll")
        data.update("SO", "T_Soll", 13.4)
        data.update("SO", "T_Speicherunten", 20.2)
        data.update("SO", "T_Laufzeit", 3456)
        data.update("SO", "T_Pumpe", 1)
        data.update("HK1", "T_Ist", 12.3)
        data.update("HK2", "T_Ist", 23.4)
        data.update("HK3", "T_Ist", 34.5)
        data.update("HK4", "T_Ist", 45.6)
        data.update("SO", "T_Aussen", 0.2)
        data.update("DT", "Date", "23.03.2013")
        data.update("DT", "Time", "11:12:13")
        print("----------- unknown values check ----------")
        print(" -- setup nickname with wrong value --")
        data._setnickname("", "solar")
        data._setnickname("WW", "")
        print(" -- check unavailable names    --")
        data.update("ST", "T_Collector")
        data.update("", "T_Collector")
        data.update("ST", "")
        print(' -- check for unknown longname --')
        print(data.getlongname("LO"))
        print(""" -- check for unknown values in ["{0}"] ---""".format(data.getlongname("SO")))
        print(data.values("SO", "T_blabla"))
        print(data.values("", "T_Pumpe"))
        #----------------
        print("----------- normal operation   ----------")
        print("-- Known values get and update --")

        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(data.getlongname("HK1")))
        print(data.values("HK1", "T_Ist"))
        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(data.getlongname("HK2")))
        print(data.values("HK2", "T_Ist"))
        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(data.getlongname("HK3")))
        print(data.values("HK3", "T_Ist"))
        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(data.getlongname("HK4")))
        print(data.values("HK4", "T_Ist"))

        print(""" -- get: all values from ["{0}"] ---""".format(data.getlongname("SO")))
        print(data.values("SO"))
        print(""" -- get: value:'T_Laufzeit' from ["{0}"] ---""".format(data.getlongname("SO")))
        print(data.values("SO", "T_Laufzeit"))
        print(""" -- update: value:'T_Laufzeit' at ["{0}"] to 654321 ---""".format(
                                    data.getlongname("SO")))
        data.update("SO", "T_Laufzeit", 654321)
        print(""" -- again get: value:'T_Laufzeit' from ["{0}"] ---""".format(data.getlongname("SO")))
        print(data.values("SO", "T_Laufzeit"))
        print(""" -- get: values:'Date' and 'Time' from ["{0}"] ---""".format(
                                    data.getlongname("DT")))
        print("{0} {1}".format(data.values("DT", "Date"), data.values("DT", "Time")))
    else:
        #---------------- testtype=1 -------------------
        print("current path   :'{0}'".format(os.getcwd()))

        data = cdata()
        data.read_db_config("./../etc/config/4test/create_db_test.xml")

        print("configfile            :'{0}'".format(data.configfilename()))
        print("Sqlite  db-file       :'{0}'".format(data.db_sqlite_filename()))
        print("Sqlite  db_enabled    :{0}".format(data.is_sql_db_enabled()))
        print("rrdtool db-file       :'{0}'".format(data.db_rrdtool_filename()))
        print("rrdtool db_enabled    :{0}".format(data.is_db_rrdtool_enabled()))
        print("rrdtool db_stepseconds:{0}".format(data.db_rrdtool_stepseconds()))
        print("rrdtool db_starttime  :{0}".format(data.db_rrdtool_starttime_utc()))
        print("dataif  comm_type     :{0}".format(data.dataif_comm_type_str()))
        if data.IsDataIf_async():
            print(" device                :{0}".format(data.AsyncSerialdevice()))
            print(" Baudrate              :{0}".format(data.AsyncBaudrate()))
            print(" Config                :{0}".format(data.AsyncConfig()))
            print(" Testfilepath          :{0}".format(data.inputtestfilepath()))

        if data.IsDataIf_socket():
            print(" Client-cfg-file       :{0}".format(data.client_cfg_file()))

        print("dataif  protocoll_type:{0}".format(data.dataif_protocoll_type_str()))
        print("logging-path          :{0}".format(data.logpathname()))
        print("logging-filename      :{0}".format(data.logfilename()))
        print("logging-filepathname  :{0}".format(data.logfilepathname()))
        print("logging-level         :{0}".format(logging.getLevelName(data.loglevel())))

        print("Heatercircuits_amount :{0}".format(data.heatercircuits_amount()))
        dberase_seconds = data.Sqlite_autoerase_seconds()
        if dberase_seconds > 0:
            tmptext = "{0} seconds".format(dberase_seconds)
        else:
            tmptext = "disabled".format(dberase_seconds)
        print("SQlite autoerase after:{0}\n".format(tmptext))

        print(""" -- get: all values from ["{0}"] ---""".format(data.getlongname("HG")))
        print(data.values("HG"))
        for circuit_number in range(1, data.heatercircuits_amount() + 1):
            strHKname = "HK" + str(circuit_number)
            print(""" -- get: all values from ["{0}"] ---""".format(data.getlongname(strHKname)))
            print(data.values(strHKname))

        print(""" -- get: all values from ["{0}"] ---""".format(data.getlongname("WW")))
        print(data.values("WW"))
        print(""" -- get: all values from ["{0}"] ---""".format(data.getlongname("SO")))
        print(data.values("SO"))

        print(""" -- get       value:'T_Kollektor' from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print("{0} = {1} {2}".format(data.displayname("SO", "T_kollektor"),
                                     data.values("SO", "T_Kollektor"),
                                     data.displayunit("SO", "T_Kollektor")))
        print(""" -- update    value:'T_Kollektor' at   ["{0}"] to 89.1 ---""".format(
                                    data.getlongname("SO")))
        data.update("SO", "T_Kollektor", 89.1)
        print(""" -- again get value:'T_Kollektor' from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print("{0} = {1} {2}".format(data.displayname("SO", "T_kollektor"),
                                     data.values("SO", "T_Kollektor"),
                                     data.displayunit("SO", "T_Kollektor")))

        # print maxvalue and defaultvalue
        print(""" -- get default-/maxvalues:'T_ist_HK' from ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        print("{0} = maxvalue:{1} ".format(data.displayname("HK1", "T_ist_HK"),
                                     data.maxvalue("HK1", "T_ist_HK")))
        print("{0} = default :{1} ".format(data.displayname("HK1", "T_ist_HK"),
                                     data.defaultvalue("HK1", "T_ist_HK")))
        print(""" -- Set default(10)/maxvalue(60):'T_ist_HK' to   ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        data.update("HK1", "T_ist_HK", 32.1, "T-Ist  (Regler/Wand)", "Celsius", "ZSB14", 60, 10)
        print(""" -- Get again default-/maxvalues:'T_ist_HK' from ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        print("{0} = maxvalue:{1} ".format(data.displayname("HK1", "T_ist_HK"),
                                     data.maxvalue("HK1", "T_ist_HK")))
        print("{0} = default :{1} ".format(data.displayname("HK1", "T_ist_HK"),
                                     data.defaultvalue("HK1", "T_ist_HK")))

        print(""" -- Update Systemtime ---""")
        # update system-date and time and print it
        data.update("DT", "Date", "01.12.2013", "System Datum")
        data.update("DT", "Time", "11:12:13", "Zeit")
        print("{0}: {1}; {2}: {3}".format(data.displayname("DT", "Date"),
                                        data.values("DT", "Date"),
                                        data.displayname("DT", "Time"),
                                        data.values("DT", "Time")))

        print(" -- show all hardwaretypes ---")
        for nickname in ["HG", "HK1", "HK2", "HK3", "HK4", "WW", "SO", "DT"]:
            print("Nickname:{0:3.3}; HWtype:{1}".format(nickname, data.hardwaretype(nickname)))

        print(" -- show all sorted logitemnames of nickname: 'HG' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("HG")))
        print(" -- show all sorted logitemnames of nickname: 'HK1' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("HK1")))
        print(" -- show all sorted logitemnames of nickname: 'HK2' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("HK2")))
        print(" -- show all sorted logitemnames of nickname: 'HK3' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("HK3")))
        print(" -- show all sorted logitemnames of nickname: 'HK4' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("HK4")))
        print(" -- show all sorted logitemnames of nickname: 'WW' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("WW")))
        print(" -- show all sorted logitemnames of nickname: 'SO' ---")
        print("logitem_names:{0}".format(data.getall_sorted_logitem_names("SO")))


        print(" -- show all items_with_values of nickname: 'HG' ---")
        print("{0}".format(data.getall_sorted_items_with_values("HG")))
        print(" -- show all items_with_values of nickname: 'HK1' ---")
        print("{0}".format(data.getall_sorted_items_with_values("HK1")))

        print(""" -- Get access-context for accessname    ---""")
        print("""      using access-name: 'ch_Tflow_desired'""")
        (nickname, logitem, itemname, set_parameter) = data.get_access_context("ch_Tflow_desired")
        if nickname == 'HG' and len(itemname) > 0:
            print("      Result OK -> Nickname:{0}; Logitem:{1}; Itemname:{2}; Set-Parameter:{3}".format(nickname, logitem, itemname, set_parameter))
        else:
            print("      Failed    -> Nickname:{0}; Logitem:{1}; Itemname:{2}; Set-Parameter:{3}".format(nickname, logitem, itemname, set_parameter))


        print(""" -------------------------------------------""")
        print(""" -- Set values to defaults               ---""")
        print("""      before update""")
        print("{0}".format(data.getall_sorted_items_with_values("SO")))
        data.setall_values2default()
        print("""      after  update""")
        print("{0}".format(data.getall_sorted_items_with_values("SO")))
