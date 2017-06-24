#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2017 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.8  / Datum 05.10.2015 first release
# Ver:0.2.x  / Datum xx.yy.2017 renaming modul and test-releases
# Ver:0.3    / Datum 19.06.2017 fixed errors
#################################################################

import sys
import os
import serial
import threading
import socket
import data
import ht_discode
from ht_proxy_if import cht_socket_client as ht_proxy_client
import ht_utils
import logging
import xml.etree.ElementTree as ET


__author__  = "junky-zs"
__status__  = "draft"
__version__ = "0.3"
__date__    = "19.06.2017"


class cSPS_cfg():
    """class 'cSPS_cfg' is used for reading the SPS-configurationfile
    """
    #---------------------------------------------------------------------------
    #   targettype related stuff
    #---------------------------------------------------------------------------
    TT_SERVER="SERVER"
    TT_CLIENT="CLIENT"

    def __init__(self, cfgtype=TT_CLIENT, logger=None, loglevel=logging.INFO):
        self._logger = logger
        self._adr_daemon = ''
        self._adr_server = ''
        self._portnr = 10001
        self._cfgtype = cfgtype
        self.__configfilename = ""

    def read_SPS_config(self, xmlcfgpathname="./etc/config/SPS_cfg.xml", logger=None):
        """ Method 'read_SPS_config' reads the SPS-If config-parameter from xml-file
        """
        self.__configfilename = xmlcfgpathname
        self.__tree = ET.parse(xmlcfgpathname)
        try:
            self.__root = self.__tree.getroot()
        except (NameError,EnvironmentError,IOError) as e:
            errorstr = "cSPS_cfg().read_SPS_config();Error;{0} on file:'{1}'".format(e, self.__configfilename)
            if self._logger != None:
                self._logger.critical(errorstr)
            print(errorstr)
            raise

        try:
            searchtarget = 'SPS_server'
            for cfg_part in self.__root.findall(searchtarget):
                self._adr_daemon = (cfg_part.find('serveraddress').text)
                self._portnr     = int(cfg_part.find('portnumber').text)
            searchtarget = 'SPS_client'
            for cfg_part in self.__root.findall(searchtarget):
                self._adr_server = (cfg_part.find('serveraddress').text)
                self._portnr = (cfg_part.find('portnumber').text)
        except (NameError,EnvironmentError,IOError) as e:
            errorstr = "cSPS_cfg().read_SPS_config();Error;{0} on file:'{1}'; target:{2}".format(e, self.__configfilename, searchtarget)
            if self._logger != None:
                self._logger.critical(errorstr)
            print(errorstr)
            raise

    def serveraddress(self):
        """ Method 'serveraddress' returns the serveraddress (value from cfg-xml-file)
        """
        adr = self._adr_daemon
        if self._cfgtype == cSPS_cfg.TT_CLIENT:
            adr = self._adr_server
        return adr

    def portnumber(self):
        """ Method 'portnumber' returns the portnumber (value from cfg-xml-file)
        """
        return int(self._portnr)

#--- class cSPS_cfg end ---#
################################################


#class cSPS_if(threading.Thread, cSPS_cfg, heater_data=data.cdata):
class cSPS_if(threading.Thread, cSPS_cfg):
    """class 'cSPS_if' is used as SPS-communication-server and cmd-parsing
        Method 'run' is the SPS-server and runs endless. 
          It listen to one SPS-client for connection, execute his command
          and returns the value to client.
        Method 'stop' stops the current running SPS-server. 
        Method 'dump_command_mapping' writes the SPS command-mapping to one
          CSV-File.
        Method 'get_command_mapping' returns the SPS command-mapping.
    """
    def __init__(self, cfgfilename, heater_data_obj, configtype=cSPS_cfg.TT_CLIENT,
                 logfilename_in=None,
                 loglevel_in=None,
                 csvfilepathname_in=None):
        # init inherited classes
        threading.Thread.__init__(self)
        cSPS_cfg.__init__(self, cfgtype = configtype)

        self.__heater_data = heater_data_obj
        # read SPS - configuration
        self.read_SPS_config(cfgfilename)

        self.__thread_run = True
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__tcp_port = self.portnumber()
        self.__buffer_size = 1024
        self.__conn = None
        self.__addr = None
        if loglevel_in != None:
            self._loglevel = loglevel_in
        else:
            self._loglevel = logging.INFO

        if logfilename_in != None:
            self.__heater_data.logfilename(logfilename_in)
            logfilepath     = self.__heater_data.logfilepathname()
        else:
            logfilepath = "./var/log/SPS_if.log"
        abs_logfilepath = os.path.abspath(logfilepath)

        if csvfilepathname_in != None:
            self.__csvfilepath = os.path.abspath(csvfilepathname_in)
        else:
            self.__csvfilepath = os.path.abspath("./var/log/sps_accessname_cmdmap.csv")

        # array of tuple for ht-nickname-mapping
        self.__SPS_nickname_map = []
        # setup ht-nickname array
        self.__SPS_ht_nickname_mapping()

        # array of tuple for special command mapping
        self.__SPS_special_map  = []
        # setup special command mapping
        self.__SPS_special_cmd_mapping()

        # directory of SPS-cmd's to tuple: (nickname, logitem-names)
        self.__SPS_accessname_cmd_map = {}
        self.__SPS_accessname_cmd_indexed = []
        # setup SPS-cmd directory
        self.__SPS_cmd_mapping()

        # setup logging
        try:
            loggertag = "SPS_if"
            self._logging = self.__heater_data.create_logfile(abs_logfilepath, self._loglevel, loggertag)
        except(EnvironmentError, TypeError) as e:
            errorstr="cSPS_if();Error; could not create logfile:{0};{1}".format(abs_logfilepath, e.args[0])
            print(errorstr)
            raise e

    def __del__(self):
        """
        """
        pass

    def __SPS_ht_nickname_mapping(self):
        """
        """
        self.__SPS_nickname_map.append(("HG" ,"A"))
        self.__SPS_nickname_map.append(("HK1","B"))
        self.__SPS_nickname_map.append(("HK2","C"))
        self.__SPS_nickname_map.append(("HK3","D"))
        self.__SPS_nickname_map.append(("HK4","E"))
        self.__SPS_nickname_map.append(("WW" ,"F"))
        self.__SPS_nickname_map.append(("SO" ,"G"))
        self.__SPS_nickname_map.append(("DT" ,"H"))

    def __SPS_special_cmd_mapping(self):
        """
        """
        self.__SPS_special_map.append(("special", "S"))

    def __SPS_cmd_mapping(self):
        """ This method generates command-mapping from sps_command to 
            ht-bus nickname and logitem-names.
            This is required to get the real nickname and logitem-name 
            for reading the values from the global data-structure 'data.cdata'.
            The real nickname and logitem-names are already defined in the
            central heater-configurationfile (xml) and here only used and
            are NOT redefined in this SPS-if class.
        """
        name_index = 0
        while name_index < len(self.__SPS_nickname_map):
            (nickname, cmd_letter) = self.__SPS_nickname_map[name_index]
            all_logitem_names      = self.__heater_data.getall_sorted_logitem_names(nickname)
            # now create command-mapping for the current nickname
            # all sps-commands will start with one 'letter' and index
            # and the resulting sps-command is saved to a map-directory
            command_index = 0
            while command_index < len(all_logitem_names):
                SPS_cmd = "{0}{1:02}".format(cmd_letter, command_index)
                # save to map-directory for parsing
                accessname = self.__heater_data.accessname(nickname, all_logitem_names[command_index])
                self.__SPS_accessname_cmd_map.update( {bytes(SPS_cmd, 'utf-8'): (nickname, accessname)} )
                self.__SPS_accessname_cmd_map.update( {bytes(accessname, 'utf-8'): (nickname, accessname)} )
                # save to indexed array for dump-purposes
                self.__SPS_accessname_cmd_indexed.append((SPS_cmd, nickname, accessname))
                command_index += 1
            name_index += 1

        # add special commands to map-directory
        name_index    = 0
        command_index = 0
        (speciname, cmd_letter) = self.__SPS_special_map[name_index]
        SPS_cmd = "{0}{1:02}".format(cmd_letter, command_index)
        # save to map-directory for parsing
        self.__SPS_accessname_cmd_map.update( {bytes(SPS_cmd, 'utf-8'): (speciname, "hostname")} )
        # save to indexed array for dump-purposes
        self.__SPS_accessname_cmd_indexed.append((SPS_cmd, speciname, "hostname"))

        command_index += 1
        SPS_cmd = "{0}{1:02}".format(cmd_letter, command_index)
        # save to map-directory for parsing
        self.__SPS_accessname_cmd_map.update( {bytes(SPS_cmd, 'utf-8'): (speciname, "os_sys")} )
        # save to indexed array for dump-purposes
        self.__SPS_accessname_cmd_indexed.append((SPS_cmd, speciname, "os_sys"))

        command_index = 9   # index fixed to '9' for mapping-dump
        SPS_cmd = "{0}{1:02}".format(cmd_letter, command_index)
        # save to map-directory for parsing
        self.__SPS_accessname_cmd_map.update( {bytes(SPS_cmd, 'utf-8'): (speciname, "map_dump")} )
        # save to indexed array for dump-purposes
        self.__SPS_accessname_cmd_indexed.append((SPS_cmd, speciname, "map_dump"))

        if self._loglevel == logging.DEBUG:
            self.dump_command_mapping()

    def __parser(self, data_in):
        """ parsing commands and execute them.
            allowed commands are SPS-short commands (see mapping) and 'accessname'-commands.
        """
        rtn = ( None, None )
        (nickname, accessname) = ( None, None )
        try:
            (nickname, accessname) = self.__SPS_accessname_cmd_map.get(data_in)
            if nickname != 'special':
                (__nickname, logitem, itemname, set_parameter) = self.__heater_data.get_access_context(accessname)
            else:
                itemname = accessname
            rtn = (nickname, itemname)
        except:
            errorstr = "cSPS_if.__parser();Error;wrong cmd: {0}".format(data_in)
            self._logging.warning(errorstr)
            rtn = ( None, None )
        return rtn
            

    def run(self):
        """ endless running thread waiting for clients to be connected and command-requests.
        """
        errorstr = "cSPS_if.run().Thread started"
        self._logging.info(errorstr)
        try:
            self.__socket.bind(("",self.__tcp_port))
            self.__socket.listen(1)
            self.__thread_run = True
        except:
            self.__thread_run = False
            errorstr = "cSPS_if.run();Error;socket-error"
            self._logging.critical(errorstr)
            print(errorstr)

        while self.__thread_run:
            try:
                self.__conn, self.__addr = self.__socket.accept()
            except:
                errorstr = "cSPS_if.run();Error;socket accept-error"
                self._logging.critical(errorstr)
                self.__thread_run = False
                break

            errorstr = "cSPS_if.run();Address:{0} connected".format(self.__addr)
            self._logging.info(errorstr)
            if self._loglevel == logging.DEBUG:
                print(errorstr)

            while True:
                try:
                    data = self.__conn.recv(self.__buffer_size)
                except:
                    pass
                if not data:
                    self.__conn.close()
                    errorstr = "cSPS_if.run();Address:{0} closed".format(self.__addr)
                    self._logging.info(errorstr)
                    break
                else:
                    try:
                        (nickname, itemname)  = self.__parser(data)
                    except:
                        errorstr="cSPS_if.run();Error;parsing error:cmd: {0}".format(data)
                        self._logging.info(errorstr)
                            
                    if nickname != 'special' and nickname != None:
                        itemvalue = self.__heater_data.values(nickname, itemname)
                    else:
                        if itemname == 'hostname':
                            itemvalue = socket.gethostname()
                        if itemname == 'os_sys':
                            itemvalue = os.name
                        if itemname == 'map_dump':
                            self.dump_command_mapping(self.__csvfilepath)
                            itemvalue = self.__csvfilepath

                    try:
                        if itemname != None:
                            self.__conn.send(bytes(str(data)[2:-1] + "=" + str(itemvalue) + ";\r\n", "utf-8"))
                            if self._loglevel == logging.DEBUG:
                                log_cmd = "cmd:{0};response:{1}".format(data, str(data)[2:-1]+"="+str(itemvalue)+";"+str(itemname)+";"+str(nickname))
                                self._logging.debug(log_cmd)
                        else:
                            send_cmd = bytes("unknown cmd,\r\n", "utf-8")
                            self.__conn.send(send_cmd)
                            self._logging.warning(send_cmd)
                    except:
                        errorstr="cSPS_if.run();Error;socket send error"
                        self._logging.critical(errorstr)

        self.__socket.close()
        errorstr = "cSPS_if.run().Thread terminated"
        self._logging.info(errorstr)
        print(errorstr)

    def stop(self):
        """ stopping the current running thread and close the connection to client.
        """
        self.__thread_run = False
        self.__conn.close()

    def dump_command_mapping(self, csvfilepath=None):
        """ dumping the SPS / accessname command-mapping to one csv-file
        """
        index  = 0
        rtnstr = ""
        writecsvfile = False
        hcsvfile = None
        if csvfilepath != None:
            try:
                hcsvfile = open(csvfilepath,"w")
                writecsvfile = True
            except:
                errorstr = "cSPS_if.dump_command_mapping();Error;can't open csv-file:{0}".format(csvfilepath)
                self._logging.critical(errorstr)
                
        tmpstr = "sps_cmd; nickname; accessname\n"
        if writecsvfile:
            hcsvfile.write(tmpstr)
            
        while index < len(self.__SPS_accessname_cmd_indexed):
            ( cmd, nickname, item ) = self.__SPS_accessname_cmd_indexed[index]
            strtemp = "{0};{1};{2}\n".format(cmd, nickname, item)
            rtnstr += strtemp
            index += 1

        if writecsvfile:
            hcsvfile.write(rtnstr)
            hcsvfile.flush()
            hcsvfile.close()
        return rtnstr

    def get_command_mapping(self):
        """
        """
        return self.__SPS_accessname_cmd_indexed

#--- class cSPS_if end ---#
################################################

### Runs only for test ###########
if __name__ == "__main__":

    # create dummy-data
    dummydata = data.cdata()
    dummydata.setlogger(dummydata.create_mylogger())
    dummydata.read_db_config("./../etc/config/4test/create_db_test.xml")

    # set SPS filename
    configurationfilename = './../etc/config/SPS_cfg.xml'

    # call interface-class
    sps_if = cSPS_if(configurationfilename, dummydata, cSPS_cfg.TT_SERVER)
    #  return interface-data
    print("SPS-serveraddress:{0}".format(sps_if.serveraddress()))
    print("SPS-serverport   :{0}".format(sps_if.portnumber()))

