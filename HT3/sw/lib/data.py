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
#################################################################

""" Class 'cdata' for reading xml-configfile and generating dependent datastructur

read_db_config          -- reading xml-configfile and setup datastructure.
                           The 'shortname' from config-file is used as main-key 'nickname'
    # data-structur:
    #   {nickname:[{itemname:arrayindex},[value1,value2,...],Update-Flag,{itemname:logitem},
    #                                                                    {itemname:displayname},
    #                                                                    {itemname:unit},
    #                                                                    {itemname:maxvalue},
    #                                                                    {itemname:defaultvalue},
    #                                                                    hardwaretype]}

configfilename           -- returns and setup of used xml-config filename.
db_sqlite_filename       -- returns and setup of used sqlite-db  filename.
is_sql_db_enabled        -- returns True/False for sql-db config-tag 'enable'
db_rrdtool_filename      -- returns and setup of used rrdtool-db filename.
is_db_rrdtool_enabled    -- returns True/False for rrdtool-db config-tag 'enable'
db_rrdtool_stepseconds   -- returns value 'step_seconds' for rrdtool-db
db_rrdtool_starttime_utc -- returns value 'starttime_utc' for rrdtool-db
heatercircuits_amount    -- returns the number of heater-circuits
                            Value is set in configuration-file.
getlongname              -- returns the 'systempart' longname with input:'shortname'
                             Only the first three chars of 'shortname' are used, upper-
                             and lower-case is possible.
                             Undefined 'shortnames' returns: 'None'
update                   -- updates an already created data.member (logitem)
                             with the new value or will create it, if not yet available
                             parameter 'logitem' is set to 'value' (default:=0)
values                   -- returns the values (array) for 'nickname and unset 'logitem' or
                             value (single one) for 'nickname' and 'logitem'
displayname              -- returns the 'name' to be displayed for the logitem.
                            Value is set in configuration-file.
                             parameters 'nickname' and 'logitem' are required
displayunit              -- returns the 'unit' to be displayed for the logitem.
                            Value is set in configuration-file.
                             parameters 'nickname' and 'logitem' are required
maxvalue                 -- returns the 'maxvalue' for the logitem.
                            Value is set in configuration-file.
                             parameters 'nickname' and 'logitem' are required
defaultvalue             -- returns the 'default'-value for the logitem.
                            Value is set in configuration-file.
                             parameters 'nickname' and 'logitem' are required
IsDataIf_async           -- returns True if data-Interface is configured to be in
                            asychron-mode, else False. Values is set in configuration-file.
IsDataIf_socket          -- returns True if data-Interface is configured to be in
                            socket-mode, else False. Values is set in configuration-file.
dataif_comm_type_str     -- returns the currently defined communication-mode as string.
                            Values are "ASYNC" or "SOCKET"
IsDataIf_raw             -- returns True if data-Interface has RAW-mode protokoll configuration,
                            else False. Values is set in configuration-file.
IsDataIf_trx             -- returns True if data-Interface has TRX-mode protokoll configuration,
                            else False. Value is set in configuration-file.
AyncSerialdevice         -- returns the currently defined devicename for async-mode.
                            Value is set in configuration-file.
AyncBaudrate             -- returns the currently defined Baudrate for async-mode.
                            Value is set in configuration-file.
AyncConfig               -- returns the currently defined Parameter for async-mode (fixed to 8N1).
                            Value is set in configuration-file.
Serveradress             -- returns the currently defined 'serveradresse' for socket-mode.
                            Value is set in configuration-file.
Servername               -- returns the currently defined 'servername' for socket-mode.
                            Value is set in configuration-file.
Serverport               -- returns the currently defined 'serverport' for socket-mode.
                            Value is set in configuration-file.
IsAnyUpdate              -- returns True/False if any update was set
UpdateRead               -- resets status of new-update flag
IsSyspartUpdate          -- returns True/False for parameter 'nickname' if new data is
                            available and resets the flag
GetUnmixedFlagHK         -- returns True for parameter 'nickname' if heater-circuit (HK1..4) has
                            no mixer, else False. Values are set in configuration-file.
GetBuscodierungHK        -- returns the Buscodierung-number for parameter 'nickname' (HK1..4).
                            Values are set in configuration-file.
IsLoadpump_WW            -- returns True, if heater-external water-loadpump is available, else False.
                            Value is set in configuration-file.
IsSecondHeater_SO        -- returns True, if second heater in system is available, else False.
                            Value is set in configuration-file.
IsSecondBuffer_SO        -- returns True, if extra water-buffer for second heater is available, else False.
                            Value is set in configuration-file.

"""

import xml.etree.ElementTree as ET
import sys, _thread

class cdata(object):
    def __init__(self):
        self.__nickname={}
        self.__logitemHG={}
        self.__HKcount=1
        self.__logitemHK1={}
        self.__logitemHK2={}
        self.__logitemHK3={}
        self.__logitemHK4={}
        self.__logitemWW={}
        self.__logitemSO={}
        self.__logitemDT={}
        self.__logitemNN={}
        self.__valuesHG =[]
        self.__valuesHK1 =[]
        self.__valuesHK2 =[]
        self.__valuesHK3 =[]
        self.__valuesHK4 =[]
        self.__valuesWW =[]
        self.__valuesSO =[]
        self.__valuesDT =[]
        self.__valuesNN =[]
        self.__UpdateHG =False
        self.__UpdateHK1 =False
        self.__UpdateHK2 =False
        self.__UpdateHK3 =False
        self.__UpdateHK4 =False
        self.__UpdateWW =False
        self.__UpdateSO =False
        self.__UpdateDT =False
        self.__UpdateNN =False
        # dir's for hardwaretype to be displayed
        self.__hwtypeHG=""
        self.__hwtypeHK1=""
        self.__hwtypeHK2=""
        self.__hwtypeHK3=""
        self.__hwtypeHK4=""
        self.__hwtypeWW=""
        self.__hwtypeSO=""
        self.__hwtypeDT=""
        self.__hwtypeNN=""
        self.__logitemMapHG={}
        self.__logitemMapHK1={}
        self.__logitemMapHK2={}
        self.__logitemMapHK3={}
        self.__logitemMapHK4={}
        self.__logitemMapWW={}
        self.__logitemMapSO={}
        self.__logitemMapDT={}
        self.__logitemMapNN={}
        # dir's for Logitem Display-Names
        self.__logitemDisplaynameHG={}
        self.__logitemDisplaynameHK1={}
        self.__logitemDisplaynameHK2={}
        self.__logitemDisplaynameHK3={}
        self.__logitemDisplaynameHK4={}
        self.__logitemDisplaynameWW={}
        self.__logitemDisplaynameSO={}
        self.__logitemDisplaynameDT={}
        self.__logitemDisplaynameNN={}
        # dir's for Logitem: 'unit' to be displayed
        self.__logitemUnitHG={}
        self.__logitemUnitHK1={}
        self.__logitemUnitHK2={}
        self.__logitemUnitHK3={}
        self.__logitemUnitHK4={}
        self.__logitemUnitWW={}
        self.__logitemUnitSO={}
        self.__logitemUnitDT={}
        self.__logitemUnitNN={}
        # dir's for Logitem: 'maxvalue'
        self.__maxvalueHG={}
        self.__maxvalueHK1={}
        self.__maxvalueHK2={}
        self.__maxvalueHK3={}
        self.__maxvalueHK4={}
        self.__maxvalueWW={}
        self.__maxvalueSO={}
        self.__maxvalueDT={}
        self.__maxvalueNN={}
        # dir's for Logitem: 'defaultvalue'
        self.__defaultvalueHG={}
        self.__defaultvalueHK1={}
        self.__defaultvalueHK2={}
        self.__defaultvalueHK3={}
        self.__defaultvalueHK4={}
        self.__defaultvalueWW={}
        self.__defaultvalueSO={}
        self.__defaultvalueDT={}
        self.__defaultvalueNN={}
        self.__unmixedHK1_HK4={}
        self.__buscodierungHK1_HK4={}
        self.__LoadpumpWW =False
        self.__SecondHeaterSO =False
        self.__SecondBufferSO =False
        self.__data={}
        self.__thread_lock=_thread.allocate_lock()
        self.__newdata_available=False
        self.__configfilename=""
        self.__dbname_sqlite=""
        self.__sql_enable=False
        self.__dbname_rrdtool=""
        self.__rrdtool_enable=False
        self.__rrdtool_stepseconds  =0
        self.__rrdtool_starttime_utc=0
        self._SetDataIf_async() #"ASYNC":=1; "SOCKET":=2
        self._SetDataIf_raw()   #"RAW"  :=1; "TRX"   :=2
        self.AsyncSerialdevice("/dev/ttyAMA0")
        self.AsyncBaudrate(9600)
        self.AsyncConfig("8N1")
        self.Serveradress("192.168.2.1")
        self.Servername("dummy")
        self.Serverport(8088)
        

    def read_db_config(self,xmlconfigpathname):
        try:
            self.__configfilename=xmlconfigpathname
            self.__tree = ET.parse(xmlconfigpathname)
        except (NameError, EnvironmentError) as e:
            print("data.read_db_config();Error;{0} on file:'{1}'".format(e.args[0], xmlconfigpathname))
            sys.exit(1)
        else:            
            try:
                self.__root = self.__tree.getroot()

                                
                #find sql_db-entries
                self.__dbname_sqlite =self.__root.find('dbname_sqlite').text
                for sql_db_part in self.__root.findall('sql-db'):
                    self.__sql_enable    = sql_db_part.find('enable').text.upper()
                    if self.__sql_enable=='ON' or self.__sql_enable=='1':
                        self.__sql_enable=True
                    else:
                        self.__sql_enable=False

                #find rrdtool-entries
                self.__dbname_rrdtool=self.__root.find('dbname_rrd').text
                for rrdtool_part in self.__root.findall('rrdtool-db'):
                    self.__rrdtool_enable    = rrdtool_part.find('enable').text.upper()
                    if self.__rrdtool_enable=='ON' or self.__rrdtool_enable=='1':
                        self.__rrdtool_enable=True
                    else:
                        self.__rrdtool_enable=False
                        
                    self.__rrdtool_stepseconds  =int(rrdtool_part.find('step_seconds').text)
                    if self.__rrdtool_stepseconds < 60:
                        self.__rrdtool_stepseconds=60
                        
                    self.__rrdtool_starttime_utc=int(rrdtool_part.find('starttime_utc').text)
                    if self.__rrdtool_starttime_utc<1344000000 or self.__rrdtool_starttime_utc>1999999999:
                        self.__rrdtool_starttime_utc=1344000000

                #find datainterface-entries
                for data_if in self.__root.findall('data_interface'):
                    commtype = data_if.find('comm_type').text.upper()[0:3]
                    if commtype in ("SOC"):
                        # force value 'SOCKET' currently to "ASCNC"
                        self._SetDataIf_async()
                        # TBD ## self._SetDataIf_socket()
                    else:
                        # else set value to "ASCNC"
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
                            self.__dataif_param_config    = str(param.find('config').text)

                        if param.attrib["name"].upper()[0:3] in ("SOC"):
                            self.__dataif_param_serveradr  = str(param.find('serveradress').text)
                            self.__dataif_param_servername = str(param.find('servername').text)
                            self.__dataif_param_portnumber = int(param.find('portnumber').text)
                            
                #find amount of heizkreise -entries
                self.__HKcount=int(self.__root.find('anzahl_heizkreise').text)
                if self.__HKcount>4 or self.__HKcount<1:
                    raise IndexError("amount of:'anzahl_heizkreise' out of range (1...4)")

                syspart=""
                for syspart in self.__root.findall('systempart'):
                    syspartname = syspart.attrib["name"]
                    shortname=""
                    hardwaretype=""
                    for shortname in syspart.findall('shortname'):
                        shortname = shortname.attrib["name"].upper()
                        if shortname in ("HK1","HK2","HK3","HK4"):
                            self.__unmixedHK1_HK4.update({shortname : syspart.find('unmixed').text})
                            self.__buscodierungHK1_HK4.update({shortname : int(syspart.find('buscodierung').text)})
                                                            
                        try:
                            if shortname in ("WW"):
                                self.__LoadpumpWW=True if syspart.find('load_pump').text.upper()=="TRUE" else False

                            if shortname in ("SO"):
                                self.__SecondHeaterSO=True if syspart.find('second_heater').text.upper()=="TRUE" else False
                                self.__SecondBufferSO=True if syspart.find('second_buffer').text.upper()=="TRUE" else False
                        except (KeyError, IndexError, AttributeError) as e:
                            print("data.read_db_config();Error on xml-tag:",e.args[0])

                    hardwaretype = syspart.find('hardwaretype').text
                            
                    # set nicknames
                    self._setnickname(shortname, syspartname)
                    logitem=""
                    for logitem in syspart.findall('logitem'):
                        name       = logitem.attrib["name"]
                        maxvalue   = logitem.find('maxvalue').text
                        default    = logitem.find('default').text
                        unit       = logitem.find('unit').text
                        displayname= logitem.find('displayname').text
    ##### unused values from xml-file in data-context ###                    
    ##                    datatype= logitem.find('datatype').text
    ##                    datause = logitem.find('datause').text
    ##                    values=[datatype,datause]
    #####                    
                        # add itemname and values to table
                        self.update(shortname,name,default,displayname,unit,hardwaretype,maxvalue,default)
                    else:
                        if not len(logitem): raise AttributeError("logitem")
                else:
                    if not len(syspart): raise AttributeError("syspart")
                
            except (KeyError, IndexError, AttributeError) as e:
                if not type(e) == AttributeError:
                    print("data.read_db_config();Error on xml-tag:",e.args[0])
                else:
                    print("data.read_db_config();Error on xml-tag")                        
                sys.exit(1)
            
    def configfilename(self, xmlconfigpathname=""):
        if len(xmlconfigpathname):
            self.__configfilename=xmlconfigpathname
        return self.__configfilename
    
    def db_sqlite_filename(self, xmlconfigpathname=""):
        if len(xmlconfigpathname):
            self.__configfilename=xmlconfigpathname
            self.read_db_config(xmlconfigpathname)
        return self.__dbname_sqlite

    def is_sql_db_enabled(self):
        return self.__sql_enable

    def db_rrdtool_filename(self, xmlconfigpathname=""):
        if len(xmlconfigpathname):
            self.__configfilename=xmlconfigpathname
            self.read_db_config(xmlconfigpathname)
        return self.__dbname_rrdtool

    def is_db_rrdtool_enabled(self):
        return self.__rrdtool_enable

    def db_rrdtool_stepseconds(self):
        return self.__rrdtool_stepseconds

    def db_rrdtool_starttime_utc(self):
        return self.__rrdtool_starttime_utc

    def heatercircuits_amount(self):
        return self.__HKcount
    
    def _setnickname(self,shortname,longname):
        shortname=shortname.upper()[0:3]
        try:
            if not len(shortname): raise NameError("shortname undefined")
            if not len(longname) : raise NameError("longname undefined")
            self.__nickname.update({shortname:longname})
            if   "HG" in shortname:
                self.__data.update({"HG":[self.__logitemHG,
                                          self.__valuesHG,
                                          self.__UpdateHG,
                                          self.__logitemMapHG,
                                          self.__logitemDisplaynameHG,
                                          self.__logitemUnitHG,
                                          self.__maxvalueHG,
                                          self.__defaultvalueHG,
                                          self.__hwtypeHG]})
            elif "HK1" in shortname:
                self.__data.update({"HK1":[self.__logitemHK1,
                                          self.__valuesHK1,
                                          self.__UpdateHK1,
                                          self.__logitemMapHK1,
                                          self.__logitemDisplaynameHK1,
                                          self.__logitemUnitHK1,
                                          self.__maxvalueHK1,
                                          self.__defaultvalueHK1,
                                          self.__hwtypeHK1]})
            elif "HK2" in shortname:
                self.__data.update({"HK2":[self.__logitemHK2,
                                          self.__valuesHK2,
                                          self.__UpdateHK2,
                                          self.__logitemMapHK2,
                                          self.__logitemDisplaynameHK2,
                                          self.__logitemUnitHK2,
                                          self.__maxvalueHK2,
                                          self.__defaultvalueHK2,
                                          self.__hwtypeHK2]})
                                           
            elif "HK3" in shortname:
                self.__data.update({"HK3":[self.__logitemHK3,
                                          self.__valuesHK3,
                                          self.__UpdateHK3,
                                          self.__logitemMapHK3,
                                          self.__logitemDisplaynameHK3,
                                          self.__logitemUnitHK3,
                                          self.__maxvalueHK3,
                                          self.__defaultvalueHK3,
                                          self.__hwtypeHK3]})
                                    
            elif "HK4" in shortname:
                self.__data.update({"HK4":[self.__logitemHK4,
                                          self.__valuesHK4,
                                          self.__UpdateHK4,
                                          self.__logitemMapHK4,
                                          self.__logitemDisplaynameHK4,
                                          self.__logitemUnitHK4,
                                          self.__maxvalueHK4,
                                          self.__defaultvalueHK4,
                                          self.__hwtypeHK4]})
                                    
            elif "WW" in shortname:
                self.__data.update({"WW":[self.__logitemWW,
                                          self.__valuesWW,
                                          self.__UpdateWW,
                                          self.__logitemMapWW,
                                          self.__logitemDisplaynameWW,
                                          self.__logitemUnitWW,
                                          self.__maxvalueWW,
                                          self.__defaultvalueWW,
                                          self.__hwtypeWW]})
                                          
            elif "SO" in shortname:
                self.__data.update({"SO":[self.__logitemSO,
                                          self.__valuesSO,
                                          self.__UpdateSO,
                                          self.__logitemMapSO,
                                          self.__logitemDisplaynameSO,
                                          self.__logitemUnitSO,
                                          self.__maxvalueSO,
                                          self.__defaultvalueSO,
                                          self.__hwtypeSO]})
                                          
            elif "DT" in shortname:
                self.__data.update({"DT":[self.__logitemDT,
                                          self.__valuesDT,
                                          self.__UpdateDT,
                                          self.__logitemMapDT,
                                          self.__logitemDisplaynameDT,
                                          self.__logitemUnitDT,
                                          self.__maxvalueDT,
                                          self.__defaultvalueDT,
                                          self.__hwtypeDT]})
                                          
            else:
                self.__data.update({"NN":[self.__logitemNN,
                                          self.__valuesNN,
                                          self.__UpdateNN,
                                          self.__logitemMapNN,
                                          self.__logitemDisplaynameNN,
                                          self.__logitemUnitNN,
                                          self.__maxvalueNN,
                                          self.__defaultvalueNN,
                                          self.__hwtypeNN]})
                                          
            
        except (NameError, AttributeError) as e:
            print("data._setnickname();Error;{0}".format(e.args[0]))

            
    def getlongname(self,shortname):
        try:
            return self.__nickname[shortname.upper()[0:3]]
        except (KeyError, IndexError, AttributeError) as e:
            print("data.getlongname();Error;longname'{0}' not found".format(e.args[0]))
            return None

    ############################
    # function updates tableentry, if not yet available tableentry is created and set
    #
    # data-structur:
    #   {nickname:[ {itemname:arrayindex},[value1,value2,...],Update-Flag,{itemname:logitem},
    #                                                                     {itemname:displayname},
    #                                                                     {itemname:unit},
    #                                                                     {itemname:maxvalue},
    #                                                                     {itemname:defaultvalue},
    #                                                                     hardwaretype]}
    #
    def update(self, nickname, logitem, value=0.0,displayname="",unit="",hwtype="", maxvalue=100.0, default=0.0):
        nickname=nickname.upper()[0:3]
        itemname=logitem.replace("_","").lower()
        try:
            if not len(nickname): raise NameError("nickname undefined")
            if not len(itemname): raise NameError("itemname undefined")
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    # update value, get index first from dir{itemname:index}
                    index=int(self.__data[nickname][0][itemname])
                    self.__data[nickname][1][index]=value
                    # set 'IsSyspartUpdate' true
                    self.__data[nickname][2]=True
                    if len(displayname) > 0:self.__data[nickname][4][itemname]=displayname 
                    if len(unit) > 0       :self.__data[nickname][5][itemname]=unit        
                    if maxvalue !=100.0    :self.__data[nickname][6][itemname]=maxvalue        
                    if default  !=0.0      :self.__data[nickname][7][itemname]=default        
                else:
                    # add new item and value, index is the current array-length
                    # and is set to dir{itemname:index}
                    index=len(self.__data[nickname][1])
                    self.__data[nickname][0].update({itemname:index})
                    self.__data[nickname][1].append(value)
                    # set internal itemname to external logitem
                    self.__data[nickname][3].update({itemname:logitem})
                    
                    if not displayname==None and len(displayname)>0:
                        self.__data[nickname][4].update({itemname:displayname})
                    else:
                        self.__data[nickname][4].update({itemname:""})
                        
                    if not unit==None and len(unit)>0:
                        self.__data[nickname][5].update({itemname:unit})
                    else:
                        self.__data[nickname][5].update({itemname:""})

                    self.__data[nickname][6].update({itemname:maxvalue})
                    self.__data[nickname][7].update({itemname:default})
                        
                if not hwtype==None and len(hwtype)>0:
                    self.__data[nickname][8]=hwtype
                        
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
            self.__thread_lock.acquire()
            self.__newdata_available=True
            self.__thread_lock.release()
            
        except (KeyError, NameError, AttributeError) as e:
            print("data.update();Error;{0}".format(e.args[0]))
            self.__thread_lock.acquire()
            self.__newdata_available=False
            self.__thread_lock.release()
                
    def values(self, nickname, logitem=""):
        nickname=nickname.upper()[0:3]
        itemname=logitem.replace("_","").lower()
        try:
            self.__thread_lock.acquire()
            if not len(nickname): raise NameError("nickname undefined")
            if nickname in self.__nickname:
                if len(itemname):
                    if itemname in self.__data[nickname][0]:
                        index=int(self.__data[nickname][0][itemname])
                        return self.__data[nickname][1][index]
                    else:
                        raise NameError("itemname:'{0}' not found".format(logitem))
                else:
                    return self.__data[nickname][1]
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
        except(KeyError, NameError, AttributeError) as e:
            print("data.values();Error;{0}".format(e.args[0]))

        finally:
            self.__thread_lock.release()


    def displayname(self, nickname, logitem):
        nickname=nickname.upper()[0:3]
        itemname=logitem.replace("_","").lower()
        try:
            if not len(nickname): raise NameError("nickname undefined")
            if not len(logitem) : raise NameError("logitem undefined")
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    return str(self.__data[nickname][4][itemname])
                else:
                    raise NameError("itemname:'{0}' in nickname:'{1}' not found".format(logitem, nickname))
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
        except(KeyError, NameError, AttributeError) as e:
            print("data.displayname();Error;{0}".format(e.args[0]))

    def displayunit(self, nickname, logitem):
        nickname=nickname.upper()[0:3]
        itemname=logitem.replace("_","").lower()
        try:
            if not len(nickname): raise NameError("nickname undefined")
            if not len(logitem) : raise NameError("logitem undefined")
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    return self.__data[nickname][5][itemname]
                else:
                    raise NameError("itemname:'{0}' not found".format(logitem))
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
        except(KeyError, NameError, AttributeError) as e:
            print("data.displayname();Error;{0}".format(e.args[0]))

    def maxvalue(self, nickname, logitem):
        nickname=nickname.upper()[0:3]
        itemname=logitem.replace("_","").lower()
        try:
            if not len(nickname): raise NameError("nickname undefined")
            if not len(logitem) : raise NameError("logitem undefined")
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    #check for float- or int-value and return the correct type
                    if "." in (str(self.__data[nickname][6][itemname])):
                        return float(self.__data[nickname][6][itemname])
                    else:
                        return int(self.__data[nickname][6][itemname])
                else:
                    raise NameError("itemname:'{0}' not found".format(logitem))
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
        except(KeyError, NameError, AttributeError) as e:
            print("data.maxvalue();Error;{0}".format(e.args[0]))

    def defaultvalue(self, nickname, logitem):
        nickname=nickname.upper()[0:3]
        itemname=logitem.replace("_","").lower()
        try:
            if not len(nickname): raise NameError("nickname undefined")
            if not len(logitem) : raise NameError("logitem undefined")
            if nickname in self.__nickname:
                if itemname in self.__data[nickname][0]:
                    #check for float- or int-value and return the correct type
                    if "." in (str(self.__data[nickname][7][itemname])):
                        return float(self.__data[nickname][7][itemname])
                    else:
                        return int(self.__data[nickname][7][itemname])
                else:
                    raise NameError("itemname:'{0}' not found".format(logitem))
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
        except(KeyError, NameError, AttributeError) as e:
            print("data.defaultvalue();Error;{0}".format(e.args[0]))

    def hardwaretype(self, nickname):
        nickname=nickname.upper()[0:3]
        try:
            if not len(nickname): raise NameError("nickname undefined")
            if nickname in self.__nickname:
                return str(self.__data[nickname][8])
            else:
                raise NameError("nickname:'{0}' not found".format(nickname))
        except(KeyError, NameError, AttributeError) as e:
            print("data.hardwaretype();Error;{0}".format(e.args[0]))

    def _SetDataIf_async(self):
        self.__dataif_commtype = 1
    
    def IsDataIf_async(self):
        return True if (self.__dataif_commtype == 1) else False

    def _SetDataIf_socket(self):
        self.__dataif_commtype = 2

    def IsDataIf_socket(self):
        return True if (self.__dataif_commtype == 2) else False
    
    def dataif_comm_type_str(self):
        rtnstr=""
        if self.IsDataIf_async():
            rtnstr="ASYNC"
        else:
            if self.IsDataIf_socket():
                rtnstr="SOCKET"
        return rtnstr

    def _SetDataIf_raw(self):
        self.__dataif_prototype = 1
        
    def _SetDataIf_trx(self):
        self.__dataif_prototype = 2

    def IsDataIf_raw(self):
        return True if (self.__dataif_prototype == 1) else False

    def IsDataIf_trx(self):
        return True if (self.__dataif_prototype == 2) else False

    def dataif_protocoll_type_str(self):
        rtnstr=""
        if self.IsDataIf_raw():
            rtnstr="RAW"
        if self.IsDataIf_trx():
            rtnstr="TRX"
        return rtnstr

    def AsyncSerialdevice(self, serialdevice=None):
        if serialdevice != None:
            self.__dataif_param_serialdevice=serialdevice
        return self.__dataif_param_serialdevice

    def AsyncBaudrate(self, baudrate=None):
        if baudrate != None:
            self.__dataif_param_baudrate=baudrate
        return self.__dataif_param_baudrate

    def AsyncConfig(self, config=None):
        if config != None:
            self.__dataif_param_config=config
        return self.__dataif_param_config

    def inputtestfilepath(self, testfilepath=None):
        if testfilepath != None:
            self.__dataif_param_testfilepath=testfilepath
        return self.__dataif_param_testfilepath

    def Serveradress(self, serveradress=None):
        if serveradress != None:
            self.__dataif_param_serveradr=serveradress
        return self.__dataif_param_serveradr

    def Servername(self, servername=None):
        if servername != None:
            self.__dataif_param_servername=servername
        return self.__dataif_param_servername

    def Serverport(self, serverport=None):
        if serverport != None:
            self.__dataif_param_portnumber=serverport
        return self.__dataif_param_portnumber

    def IsAnyUpdate(self):
        return self.__newdata_available

    def UpdateRead(self):
        self.__thread_lock.acquire()
        self.__newdata_available=False
        self.__thread_lock.release()

    def IsSyspartUpdate(self, nickname):
        nickname=nickname.upper()[0:3]
        Rtn=self.__data[nickname][2]
        self.__data[nickname][2]=False
        return Rtn

    def GetUnmixedFlagHK(self, nickname):
        nickname=nickname.upper()[0:3]
        return self.__unmixedHK1_HK4.get(nickname)

    def GetBuscodierungHK(self, nickname):
        nickname=nickname.upper()[0:3]
        return self.__buscodierungHK1_HK4.get(nickname)

    def IsLoadpump_WW(self):
        return self.__LoadpumpWW
    
    def IsSecondHeater_SO(self):
        return self.__SecondHeaterSO

    def IsSecondBuffer_SO(self):
        return self.__SecondBufferSO
    
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
    #                                                                     hardwaretype]}
    #
    testtype=1
    
    if testtype == 0:
        #---------------- testtype=0 -------------------
        data=cdata()
        print("-- setup nicknames --")
        data._setnickname("HG","heizgeraet")
        data._setnickname("Hklein","heizkreis")
        data._setnickname("HK1","heizkreis1")
        data._setnickname("HK2","heizkreis2")
        data._setnickname("HK3","heizkreis3")
        data._setnickname("HK4","heizkreis4")
        data._setnickname("WW","warmwasser")
        data._setnickname("SO","solar")
        data._setnickname("DT","datetime")
        data._setnickname("data","dadadata")
        #----------------
        print("-- updata data --")
        data.update("SO","T_Collector")
        data.update("SO","T_Collector",33.5)
        data.update("SO","T_Soll")
        data.update("SO","T_Soll",13.4)
        data.update("SO","T_Speicherunten",20.2)
        data.update("SO","T_Laufzeit",3456)
        data.update("SO","T_Pumpe",1)
        data.update("HK1","T_Ist",12.3)
        data.update("HK2","T_Ist",23.4)
        data.update("HK3","T_Ist",34.5)
        data.update("HK4","T_Ist",45.6)
        data.update("SO","T_Aussen",0.2)
        data.update("DT","Date","23.03.2013")
        data.update("DT","Time","11:12:13")
        print("----------- unknown values check ----------")
        print(" -- setup nickname with wrong value --")
        data._setnickname("","solar")
        data._setnickname("WW","")
        print(" -- check unavailable names    --")
        data.update("ST","T_Collector")
        data.update("","T_Collector")
        data.update("ST","")
        print(' -- check for unknown longname --')
        print(data.getlongname("LO"))
        print(""" -- check for unknown values in ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print(data.values("SO","T_blabla"))
        print(data.values("","T_Pumpe"))
        #----------------
        print("----------- normal operation   ----------")
        print("-- Known values get and update --")

        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        print(data.values("HK1","T_Ist"))
        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(
                                    data.getlongname("HK2")))
        print(data.values("HK2","T_Ist"))
        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(
                                    data.getlongname("HK3")))
        print(data.values("HK3","T_Ist"))
        print(""" -- get: value:'T_Ist' from ["{0}"] ---""".format(
                                    data.getlongname("HK4")))
        print(data.values("HK4","T_Ist"))

        print(""" -- get: all values from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print(data.values("SO"))
        print(""" -- get: value:'T_Laufzeit' from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print(data.values("SO","T_Laufzeit"))
        print(""" -- update: value:'T_Laufzeit' at ["{0}"] to 654321 ---""".format(
                                    data.getlongname("SO")))
        data.update("SO","T_Laufzeit",654321)
        print(""" -- again get: value:'T_Laufzeit' from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print(data.values("SO","T_Laufzeit"))
        print(""" -- get: values:'Date' and 'Time' from ["{0}"] ---""".format(
                                    data.getlongname("DT")))
        print("{0} {1}".format(data.values("DT","Date"),data.values("DT","Time")))
    else:
        #---------------- testtype=1 -------------------
        import os
        print("current path   :'{0}'".format(os.getcwd()))

        data=cdata()
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
            print(" device      :{0}".format(data.AsyncSerialdevice()))
            print(" Baudrate    :{0}".format(data.AsyncBaudrate()))
            print(" Config      :{0}".format(data.AsyncConfig()))
            print(" Testfilepath:{0}".format(data.inputtestfilepath()))
            
        if data.IsDataIf_socket():
            print(" Serveradress:{0}".format(data.Serveradress()))
            print(" Servername  :{0}".format(data.Servername()))
            print(" Serverport  :{0}".format(data.Serverport()))

        print("dataif  protocoll_type:{0}".format(data.dataif_protocoll_type_str()))
        
        print("Heatercircuits_amount :{0}".format(data.heatercircuits_amount()))
        
        print(""" -- get: all values from ["{0}"] ---""".format(
                                    data.getlongname("HG")))
        print(data.values("HG"))
        for circuit_number in range (1,data.heatercircuits_amount()+1):
            strHKname="HK"+str(circuit_number)
            print(""" -- get: all values from ["{0}"] ---""".format(
                                    data.getlongname(strHKname)))
            print(data.values(strHKname))

        print(""" -- get: all values from ["{0}"] ---""".format(
                                    data.getlongname("WW")))
        print(data.values("WW"))
        print(""" -- get: all values from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print(data.values("SO"))

        print(""" -- get       value:'T_Kollektor' from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print("{0} = {1} {2}".format(data.displayname("SO","T_kollektor"),
                                     data.values("SO","T_Kollektor"),
                                     data.displayunit("SO","T_Kollektor")))
        print(""" -- update    value:'T_Kollektor' at   ["{0}"] to 89.1 ---""".format(
                                    data.getlongname("SO")))
        data.update("SO","T_Kollektor",89.1)
        print(""" -- again get value:'T_Kollektor' from ["{0}"] ---""".format(
                                    data.getlongname("SO")))
        print("{0} = {1} {2}".format(data.displayname("SO","T_kollektor"),
                                     data.values("SO","T_Kollektor"),
                                     data.displayunit("SO","T_Kollektor")))

        # print maxvalue and defaultvalue
        print(""" -- get default-/maxvalues:'T_ist_HK' from ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        print("{0} = maxvalue:{1} ".format(data.displayname("HK1","T_ist_HK"),
                                     data.maxvalue("HK1","T_ist_HK")))
        print("{0} = default :{1} ".format(data.displayname("HK1","T_ist_HK"),
                                     data.defaultvalue("HK1","T_ist_HK")))
        print(""" -- Set default(10)/maxvalue(60):'T_ist_HK' to   ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        data.update("HK1","T_ist_HK",32.1,"T-Ist  (Regler/Wand)","Celsius","ZSB14",60,10)
        print(""" -- Get again default-/maxvalues:'T_ist_HK' from ["{0}"] ---""".format(
                                    data.getlongname("HK1")))
        print("{0} = maxvalue:{1} ".format(data.displayname("HK1","T_ist_HK"),
                                     data.maxvalue("HK1","T_ist_HK")))
        print("{0} = default :{1} ".format(data.displayname("HK1","T_ist_HK"),
                                     data.defaultvalue("HK1","T_ist_HK")))
        

        print(""" -- Update Systemtime ---""")
        # update system-date and time and print it
        data.update("DT","Date","01.12.2013","System Datum")
        data.update("DT","Time","11:12:13","Zeit")
        print("{0}: {1}; {2}: {3}".format(data.displayname("DT","Date"),
                                        data.values("DT","Date"),
                                        data.displayname("DT","Time"),
                                        data.values("DT","Time")))
        
        print(" -- show all hardwaretypes ---")
        for nickname in ["HG","HK1","HK2","HK3","HK4","WW","SO","DT"]:
            print("Nickname:{0:3.3}; HWtype:{1}".format(nickname, data.hardwaretype(nickname)))
        
