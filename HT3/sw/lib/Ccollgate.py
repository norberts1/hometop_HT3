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
# Ver:0.1    / Datum 15.06.2017 first release
# Ver:0.2    / Datum 29.11.2018 __Extract_HT3_path_from_AbsPath() replaced with ht_utils
#                               __Autocreate_draw() removed, db_rrdtool.create_draw() replacement
# Ver:0.3    / Datum 03.12.2019 Issue:'Deprecated property InterCharTimeout #7'
#                                port.setInterCharTimeout() removed
#################################################################

import sys
import os
import time
import serial
import threading
import socket
import queue
import data
import ht_discode
from ht_proxy_if import cht_socket_client as ht_proxy_client
import ht_utils
import logging
import xml.etree.ElementTree as ET
import SPS_if
import ht_const

__author__  = "junky-zs"
__status__  = "draft"
__version__ = "0.3"
__date__    = "03.12.2019"

"""
#################################################################
# modul: Ccollgate.py                                           #
#  This modul is running as daemon and uses different moduls    #
#  and classes for interface-handling.                          #
#  The modulname stands for:                                    #
#      1. collector                                             #
#      and                                                      #
#      2. gateway                                               #
#    (Is not a 'clean' - modul as you could think and if you    #
#      have got problems with it, be wise and let me know :-)   #
#                                                               #
#  Currently it supports following interfaces:                  #
#   1. sqlite - interface for writing heater-data to database.  #
#       This interface can be disabled in configuration-file.   #
#                                                               #
#   2. rrdtool -interface for writing heater-data to database.  #
#       This interface can be disabled in configuration-file.   #
#                                                               #
#   3. mqtt   - interface for publish data to mqtt-broker and   #
#        for subscribing on commands for the heater-system.     #
#       This interface can be disabled in configuration-file.   #
#                                                               #
#   4. SPS    - interface for connected SPS-clients requesting  #
#        heater-data.                                           #
#       This interface can be disabled in configuration-file.   #
#                                                               #
# class: cht_if_tx_data()                                       #
#  This class is waiting for commands from the tx_queue.        #
#  That TX-command must be a mqtt-topic with attached payload.  #
#  After receiving the command / payload is parsed and the      #
#  result is send as heater-commands to the connected port.     #
#                                                               #
# class: cht_if_worker()                                        #
#  This class connects to the configured port (SOCKET or ASYNC) #
#  and receives heater RAW-data from that port.                 #
#  The RAW-data then is decoded with method: discoder() and     #
#  the result is send with queues to the database - interfaces  #
#  and (if enabled) to the mqtt-client.                         #
#  After startup, the endless running thread is waiting at      #
#  first for valid heater-data before sending them to the       #
#  enabled interfaces.                                          #
#   Remark:                                                     #
#    If the ASYNC - port is configured, only receiving of       #
#    heater - RAW data is possible.                             #
#    For sending heater-commands the ht_proxy-server is         #
ä    required.                                                  #
#                                                               #
# class: ccollgate_cfg()                                        #
#  This class is used for reading the collgate-configurationfile#
#                                                               #
# class: cstore2db()                                            #
#  This class stores the decoded heater-data into the           #
#  sqlite-database and the rrdtool-database (if enabled).       #
#  Automatic draw for rrdtool-draw ist called every 60 sec.     #
#  Automatic erase of old data is done fore the sqlite-db.      #
#  This class has the same functionality of HT3_logger and      #
#  that daemon shouldn't used anymore.                          #
#                                                               #
# class: ccollgate()                                            #
#  This class is used for the collgate-daemon.                  #
#  The configuration-file is read and dependent from that       #
#  content the interfaces are started.                          #
#  The startet interfaces are watched for alive-status.         #
#  On errors they are reported and the daemon will be           #
#  terminated.                                                  #
#                                                               #
#################################################################
"""

class cht_if_tx_data(threading.Thread):
    """class 'cht_if_tx_data' is waiting for data from queue and parsing this.
        Valid heater-commands are send to the connected port.
    """

    def __init__(self, tx_queue, port, allowed_cmds, bustype_detector_fkt, logging=None, loglevel_in=logging.INFO):
        threading.Thread.__init__(self)
        self.__tx_queue = tx_queue
        self.__ht_if_tx_data = None
        self.__port = port
        self.__ht_if_allowed_cmds = allowed_cmds
        self.__logging = logging
        self.__loglevel = loglevel_in
        self.__thread_run = True

        # ht_data setup parameter
        self.__splitted_rx_param = []
        self.__heater_circuit = 1
        self.__param_count = 0
        self.__tempera_desired = float(21.5)
        self.__niveau_desired = 'heizen'
        self.__tempera_niveau = 'heizen'
        self.__split_allowed_parameters(allowed_cmds)
        self.__bustype_detector_fkt = bustype_detector_fkt

    def __del__(self):
        """class desctructor """
        self.__thread_run = False

    def __split_allowed_parameters(self, command_dir):
        """split the external allowed parameters to internal used parameter-list.
            only parameters not None and with length > zero are used.
        """
        ht_if_allowed_cmds = {}
        for accessname in command_dir.keys():
            parameter = command_dir[accessname]
            if parameter != None and len(parameter) > 0:
                set_parameter = parameter.split(',')
                ht_if_allowed_cmds.update({accessname:set_parameter})
        self.__ht_if_allowed_cmds = ht_if_allowed_cmds

    def __send_data_2_ht_bus(self, command, ems_flag):
        """send the bytestream to ht_bus using lib-fkts."""
        error = None
        command = command.lower()

        if ems_flag == False:
            ###############################
            # commands for heatronic-bus
            ##
            #  setup new temperatur for niveau (heizen|sparen|frost) and heater-circuit#.
            if command in 'tdesired':
                error = self.__ht_if_tx_data.set_tempniveau(self.__tempera_desired,
                                                            hcircuit_nr=self.__heater_circuit,
                                                            temperatur_mode=self.__niveau_desired)
                if error != None:
                    error = "cht_if_tx_data; " + error
                    self.__logging.warning(error)
                else:
                    debugstr = "cht_if_tx_data;  setup done for Tdesired:{0} and niveau:'{1}'; hc:{2}".format(self.__tempera_desired,
                                                                                                              self.__niveau_desired,
                                                                                                              self.__heater_circuit)
                    self.__logging.debug(debugstr)

            #  setup new temperatur-niveau (auto|heizen|sparen|frost).
            if command in 'tniveau':
                error = self.__ht_if_tx_data.set_betriebsart(self.__tempera_niveau,
                                                             hcircuit_nr=self.__heater_circuit)
                if error != None:
                    error = "cht_if_tx_data;error; cmd:{0}; ".format(command) + error
                    self.__logging.warning(error)
                else:
                    debugstr = "cht_if_tx_data;  setup done for Tniveau:{0}".format(self.__tempera_niveau)
                    self.__logging.debug(debugstr)

            if error == None:
                self.__logging.debug("cht_if_tx_data; send data to BUS_TYPE_HT3")
            ##
            # end commands for heatronic-bus
            ###############################
        else:
            ###############################
            # commands for EMS-bus
            ##
            #  setup new temperatur for niveau (temporary|comfort1|comfort2|comfort3|eco) and heater-circuit#.
            if command in 'tdesired':
                # first setup to manual- mode if required else auto- mode
                if self.__niveau_desired in ht_const.EMS_TEMP_MODE_MANUAL:
                    error = cfg.set_operation_mode(ht_const.EMS_OMODE_MANUAL,
                                                   hcircuit_nr=self.__heater_circuit)
                else:
                    error = self.__ht_if_tx_data.set_operation_mode(ht_const.EMS_OMODE_AUTO,
                                                                    hcircuit_nr=self.__heater_circuit)
                if error != None:
                    error = "cht_if_tx_data; error; cmd:{0}; ".format(command) + error
                    self.__logging.warning(error)

                # second setup temperatur for that command niveau
                if self.__niveau_desired in ht_const.EMS_TEMP_MODE_ECO:
                    error = self.__ht_if_tx_data.set_ecomode(self.__tempera_desired,
                                                                hcircuit_nr=self.__heater_circuit)
                else:
                    error = self.__ht_if_tx_data.set_tempniveau(self.__tempera_desired,
                                                                hcircuit_nr=self.__heater_circuit,
                                                                temperatur_mode=self.__niveau_desired)
                if error != None:
                    error = "cht_if_tx_data; error; cmd:{0}; ".format(command) + error
                    self.__logging.warning(error)

            #  setup new temperatur-niveau (auto|manual).
            if command in 'tniveau':
                error = self.__ht_if_tx_data.set_operation_mode(ems_omode=self.__tempera_niveau,
                                                                hcircuit_nr=self.__heater_circuit)
                if error != None:
                    error = "cht_if_tx_data; " + error
                    self.__logging.warning(error)

            if error == None:
                self.__logging.debug("cht_if_tx_data; send data to BUS_TYPE_EMS")
            ##
            # end commands for EMS-bus
            ###############################

    def run(self):
        """ """
        import ht_yanetcom
        ems_bus = False
        self.__ht_if_tx_data = ht_yanetcom.cyanetcom(self.__port, ems_bus)

        while self.__thread_run:
            # set default values
            execute_command = True
            command_name = ""
            self.__splitted_rx_param = []
            self.__param_count = 0

            try:
                # wait for queue-message
                (access_name, value) = self.__tx_queue.get()
            except:
                errorstr = "cht_if_tx_data.run();Error; on ht_if.__tx_queue.get()"
                self.__logging.critical(errorstr)
                raise

            if (access_name, value) == (None, None):
                self.stop()
                break

            # got message, split up content
            if value != None:
                self.__splitted_rx_param = value.split(',')
            else:
                self.__splitted_rx_param = ""
            debugstr = "cht_if_tx_data; access_name:{0}; value:{1}".format(access_name, self.__splitted_rx_param)
            self.__logging.debug(debugstr)

            # extract detailed parameters from configuration-context.
            if access_name in self.__ht_if_allowed_cmds.keys():
                allowed_parameter = self.__ht_if_allowed_cmds[access_name]

                # only parameter not None and length > 0 are processed
                if allowed_parameter != None and len(self.__splitted_rx_param) > 0:
                    # extract: 1. parameter := command-name
                    command_name = self.__ht_if_allowed_cmds[access_name][0]

                    # extract: 2. parameter := parameter count (int)
                    indexed_value = self.__ht_if_allowed_cmds[access_name][1]
                    self.__param_count = indexed_value
                    if type(indexed_value) == str:
                        self.__param_count = ord(indexed_value) - ord('0')

                    if self.__param_count > 1:
                        # extract: 3. parameter := heater circuit-number
                        indexed_value = self.__ht_if_allowed_cmds[access_name][2]
                        self.__heater_circuit = int(indexed_value)
                        if self.__heater_circuit > 0 and self.__heater_circuit < 5:
                            execute_command = True
                        else:
                            self.__heater_circuit = 1
                            execute_command = False

                        # extract: 4-n. parameter := special values depending on current command
                        # extract parameter for tdesired
                        if command_name.lower() in 'tdesired':
                            if self.__param_count == 3:
                                indexed_value = self.__ht_if_allowed_cmds[access_name][3]
                                if indexed_value == 'T':
                                    if len(self.__splitted_rx_param) > 1:
                                        # get temperatur-value from rx-message
                                        self.__tempera_desired = float(self.__splitted_rx_param[0])
                                        # get niveau-value from rx-message
                                        tempera_niveau = self.__splitted_rx_param[1].lower()
                                        allowed_niveaus = self.__ht_if_allowed_cmds[access_name][4]
                                        if tempera_niveau in allowed_niveaus:
                                            self.__niveau_desired = tempera_niveau
                                            execute_command = True
                                        else:
                                            # error no valid parameter received
                                            execute_command = False
                                            errorstr = "cht_if_tx_data;error; cmd:{0}; parameter:{1} wrong".format(command_name, tempera_niveau)
                                            self.__logging.warning(errorstr)
                                    else:
                                        # error no valid parameter received
                                        execute_command = False
                                        errorstr = "cht_if_tx_data;error; cmd:{0}; parameter:{1} wrong".format(command_name, self.__splitted_rx_param)
                                        self.__logging.warning(errorstr)
                            else:
                                # error no valid parameter
                                execute_command = False
                                errorstr = "cht_if_tx_data;error; cmd:{0}; amount of parameter:{1} wrong".format(command_name, self.__param_count)
                                self.__logging.warning(errorstr)
                        ########## end of: 'tdesired'

                        # extract parameter for tniveau
                        if command_name.lower() in 'tniveau':
                            if self.__param_count == 2:
                                indexed_value = self.__ht_if_allowed_cmds[access_name][3]
                                if len(self.__splitted_rx_param) > 0:
                                    if self.__splitted_rx_param[0].lower() in indexed_value:
                                        self.__tempera_niveau = self.__splitted_rx_param[0].lower()
                                        execute_command = True
                                    else:
                                        # error no valid parameter received
                                        execute_command = False
                                        errorstr = "cht_if_tx_data;error; cmd:{0}; unknown parameter:{1}".format(command_name, self.__splitted_rx_param[0])
                                        self.__logging.warning(errorstr)
                                else:
                                    # error no valid parameter received
                                    execute_command = False
                                    errorstr = "cht_if_tx_data;error; cmd:{0}; parameter:{1} wrong".format(command_name, self.__splitted_rx_param)
                                    self.__logging.warning(errorstr)
                            else:
                                # error no valid parameter
                                execute_command = False
                                errorstr = "cht_if_tx_data;error; cmd:{0}; amount of parameter:{1} wrong".format(command_name, self.__param_count)
                                self.__logging.warning(errorstr)
                        ########## end of: 'tniveau'
                    else:
                        errorstr = "cht_if_tx_data;error; cmd:{0}; amount of parameter:{1} wrong".format(command_name, self.__param_count)
                        self.__logging.warning(errorstr)
                        # error no valid parameter
                        execute_command = False
                else:
                    errorstr = "cht_if_tx_data; error; unknown command:{0} or wrong parameter received.".format(access_name)
                    self.__logging.warning(errorstr)
                    # error no valid parameter
                    execute_command = False

                # execute command if allowed
                if execute_command == True:
                    debugstr = """cht_if_tx_data; command:{0}; param_count:{1}; P1 heater-circuit:{2}; P2-Pn:{3}""".format(command_name,
                                                                                                              self.__param_count,
                                                                                                              self.__heater_circuit,
                                                                                                              self.__splitted_rx_param)
                    self.__logging.debug(debugstr)

                    # set EMS bus if it was dynamicly detected on telegramm-rx
                    #  this setup is importent to use the correct commands / Telegramms
                    #  for the EMS-like controllers.
                    if self.__bustype_detector_fkt() == ht_const.BUS_TYPE_EMS:
                        ems_bus = True
                        self.__ht_if_tx_data.set_ems_controller()
                    else:
                        ems_bus = False
                    # send data to ht-bus
                    self.__send_data_2_ht_bus(command_name.lower(), ems_bus)
                # task done, end of processing
                self.__tx_queue.task_done()
            else:
                errorstr = "cht_if_tx_data; unknown command:{0}".format(access_name)
                self.__logging.warning(errorstr)

    def stop(self):
        """ """
        self.__thread_run = False
#--- class cht_if_tx_data end ---#
################################################

class cht_if_worker(threading.Thread):
    """class 'cht_if_worker' is used to start the dispathing and decoding of
        ht_rawdata.
        Method 'run' calls the dispatcher and decoder and runs endless.
    """
    def __init__(self, configurationfilename,
                 putdata_flag=True,
                 logging=None,
                 loglevel_in=logging.INFO):
        threading.Thread.__init__(self)
        # setup data-struct
        self._data = data.cdata()
        # set defaults
        self._logging = logging
        self._loglevel = loglevel_in

        self.__thread_run = True
        self.__filehandle = None
        self.__cfgfilename =str(configurationfilename)
        self.__data_input_mode="ASYNC "   #default value
        self.__port      = None
        # common used queues for RX- and TX-data exchange
        self.__decoded_data_queue = queue.Queue()
        self.__decoded_data_4_DBs = queue.Queue()
        self.__data_2_send_queue = queue.Queue()
        self.__putdata_flag = putdata_flag

        # create logging-file if not already done
        if self._logging == None:
            try:
                logfilepath = self._data.logfilepathname()
                abs_logfilepath = os.path.abspath(logfilepath)
                loggertag="ht_if_worker"
                self._logging = self._data.create_logfile(abs_logfilepath, self._loglevel, loggertag)
            except(EnvironmentError, TypeError) as e:
                errorstr = "cht_if_worker();Error; could not create logfile:{0};{1}".format(abs_logfilepath, e.args[0])
                print(errorstr)
                raise e

        # read configurationfile
        try:
            self._data.read_db_config(self.__cfgfilename)
        except:
            errorstr='cht_if_worker();Error;could not get configuration-values'
            self._logging.critical(errorstr)
            print(errorstr)
            raise

        #using parameters from cfg-file
        self.__serialdevice = str(self._data.AsyncSerialdevice())
        self.__baudrate = self._data.AsyncBaudrate()
        self._loglevel = self._data.loglevel()
        #setup current loglevel read from cfg-file
        self._logging.setLevel(self._loglevel)
        # setup interface
        self.__setup()
        self.__startup_time = time.time()
        self.__allowed_cmds = {}

    def __del__(self):
        """class desctructor """
        if self.__port != None:
            self.__port.close()
        self.__thread_run = False

    def __setup(self):
        """ open socket for client and connect to ht_proxy-server,
            socket-object is written to 'self.__port'
        """
        if(self._data.IsDataIf_socket()):
            self.__data_input_mode = "SOCKET"
            try:
                client_cfg_file =os.path.normcase(os.path.abspath(self._data.client_cfg_file()))
                if not os.path.exists(client_cfg_file):
                    errorstr="cht_if_worker();Error;couldn't find file:{0}".format(client_cfg_file)
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)
            except:
                errorstr="cht_if_worker();Error;couldn't find file:{0}".format(client_cfg_file)
                self._logging.critical(errorstr)
                raise EnvironmentError(errorstr)

            try:
                self.__port = ht_proxy_client(client_cfg_file, loglevel=self._loglevel)
            except:
                errorstr="cht_if_worker();Error;couldn't open requested socket; cfg-file:{0}".format(client_cfg_file)
                self._logging.critical(errorstr)
                raise
        else:
            self.__data_input_mode = "ASYNC"
            #open serial port for reading HT-data
            try:
                self.__port = serial.Serial(self.__serialdevice, self.__baudrate )
                self.__data_input_mode="ASYNC"
            except:
                errorstr="cht_if_worker();Error;couldn't open requested device:{0}".format(self.__serialdevice)
                self._logging.critical(errorstr)
                raise EnvironmentError(errorstr)

    def __init_allowed_cmds(self):
        """ """
        for accessname in self.ht_if_data().get_access_names().keys():
            # get tuple from dir and use the accessname - context
            (Nickname, logitem, itemname, set_param) = self.ht_if_data().get_access_names()[accessname]
            self.__allowed_cmds.update({accessname:set_param})

    def WaitTimeElapsed(self):
        """Waiting more then 2 minutes for valid heater-data."""
        rtnvalue = False
        if time.time() > self.__startup_time + int(130):
            rtnvalue = True
        # force to True on debugging
        if self._loglevel == logging.DEBUG:
            rtnvalue = True
        return rtnvalue

    def decoded_data_queue(self):
        """returns handle to decoded data queue."""
        return self.__decoded_data_queue

    def decoded_data_4_DBs(self):
        """returns handle to decoded data queue for databases."""
        return self.__decoded_data_4_DBs

    def data_2_send_queue(self):
        """returns handle to sending data (ht_busdata) queue """
        return self.__data_2_send_queue

    def get_accessnames(self):
        """returns handle to all accessnames defined in cfg-file."""
        return self._data.getall_accessnames()

    def ht_if_data(self):
        return self._data

    def run(self):
        """
        """
        self.__init_allowed_cmds()

        self._logging.info("cht_if_worker(); Start ----------------------")
        self._logging.info("cht_if_worker();  Loglevel      :{0}".format(logging.getLevelName(self._loglevel)))
        self._logging.info("cht_if_worker();  Datainput-Mode:{0}".format(self.__data_input_mode))

        if self._data.IsDataIf_async():
            self._logging.info("cht_if_worker();   Baudrate     :{0}".format(self.__baudrate))
            self._logging.info("cht_if_worker();   Configuration:{0}".format(self._data.AsyncConfig()))

        try:
            # create object of tx_data class with known values
            #   tx_queue, port, logging, loglevel and access-/set_parameter- names
            self.__ht_if_tx_data = cht_if_tx_data(self.__data_2_send_queue,
                                                  self.__port,
                                                  self.__allowed_cmds,
                                                  self._data.HeaterBusType, # data.HeaterBusType() method is called
                                                  self._logging,
                                                  self._loglevel)
            # start tx_data thread
            self.__ht_if_tx_data.start()
        except:
            errorstr="cht_if_worker();Error;couldn't start 'cht_if_tx_data' thread"
            self._logging.critical(errorstr)
            self.__thread_run = False
            self.__port.close()
            raise

        # set debug:=1 if you need debug-outputs on 'stdout'
        debug = 0
        try:
            decoded_data = ht_discode.cht_discode(self.__port, self._data, debug, self.__filehandle, logger=self._logging)
        except:
            errorstr="cht_if_worker();Error;couldn't start 'ht_discode' thread"
            self._logging.critical(errorstr)
            self.__thread_run = False
            self.__port.close()
            raise

        try:
            while self.__thread_run:
                # blocking call to discoder() returns nickname/value-tuple
                (nickname, value) = decoded_data.discoder()
                if (nickname, value) == (None, None):
                    self.stop()
                    errorstr="cht_if_worker();Error;nickname:=None and value:=None got from discoder()"
                    self._logging.critical(errorstr)
                    break
                #send data only if waittime is elapsed (valid data) and value is not 'None'
                if self.WaitTimeElapsed() and value != None:
                    # put data to message-queue for Database-saving
                    self.decoded_data_4_DBs().put((nickname, value))
                    # put data to message-queue for further processing in other threads
                    if self.__putdata_flag:
                        self.decoded_data_queue().put((nickname, value))

        except:
            errorstr="cht_if_worker();Error; 'discoder()' thread terminated"
            self._logging.critical(errorstr)
            self.__thread_run = False
            self.__port.close()
            raise

        self._logging.info("cht_if_worker(); End ----------------------")

    def stop(self):
        """ """
        if self.__putdata_flag:
            self.decoded_data_queue().put((None, None))
        self.decoded_data_4_DBs().put((None, None))
        self.__thread_run = False
        self.__ht_if_tx_data.stop()
#--- class cht_if_worker end ---#
################################################

class ccollgate_cfg():
    """class 'ccollgate_cfg' is used for reading the collgate-configurationfile
    """
    # common used defines for interfaces
    IF_ht = 'ht'
    IF_mqtt = 'mqtt'
    IF_sps = 'sps'

    def __init__(self, logger, loglevel=logging.INFO):
        self._logger = logger
        self.__configfilename = ""
        self.__interfaces_cfg = {}

    def read_collgate_config(self, xmlcfgpathname="./etc/config/collgate_cfg.xml", logger=None):
        """ Method 'read_collgate_config()' reads the collgate config-parameter from xml-file
             and set the informations to directory 'self.__interfaces_cfg'.
             This private informations are public available with 'get_config()'.
        """
        self.__configfilename = xmlcfgpathname
        self.__tree = ET.parse(xmlcfgpathname)
        try:
            self.__root = self.__tree.getroot()
        except (NameError,EnvironmentError,IOError) as e:
            errorstr = "ccollgate_cfg().read_collgate_config();Error;{0} on file:'{1}'".format(e, self.__configfilename)
            if self._logger != None:
                self._logger.critical(errorstr)
            print(errorstr)
            raise

        try:
            for if_part in self.__root.findall('interfaces'):
                # parameter for if: ht
                for param in if_part.findall('ht_if'):
                    cfg_file = param.find('cfg_file').text
                    self.__interfaces_cfg.update({ccollgate_cfg.IF_ht:(True, cfg_file)})

                # parameter for if: MQTT
                for param in if_part.findall('MQTT_client_if'):
                    flag = param.find('enable').text.upper()
                    if flag == 'ON' or flag == '1':
                        enable_flag = True
                    else:
                        enable_flag = False
                    cfg_file = param.find('cfg_file').text
                    self.__interfaces_cfg.update({ccollgate_cfg.IF_mqtt:(enable_flag, cfg_file)})

                # parameter for if: SPS
                for param in if_part.findall('SPS_if'):
                    flag = param.find('enable').text.upper()
                    if flag == 'ON' or flag == '1':
                        enable_flag = True
                    else:
                        enable_flag = False
                    cfg_file = param.find('cfg_file').text
                    self.__interfaces_cfg.update({ccollgate_cfg.IF_sps:(enable_flag, cfg_file)})
        except:
            errorstr = "cSPS_cfg().read_SPS_config();Error;could not read configuration from file:{0}".format(self.__configfilename)
            if self._logger != None:
                self._logger.critical(errorstr)
            print(errorstr)
            raise

    def get_config(self):
        """This method returns the current configuration for interfaces.
            return-value structure is like:
                { 'interface_nickname' : ( enable_flag, cfg_filename ) }
        """
        return self.__interfaces_cfg

    def get_enable_flag(self, interface_name):
        """returns the enable-flag value for this interface."""
        (enable_flag, file) = self.__interfaces_cfg[interface_name]
        return enable_flag

    def get_cfg_file(self, interface_name):
        """returns the cfg-filename for this interface."""
        (enable_flag, file) = self.__interfaces_cfg[interface_name]
        return file

    def logger_handle(self, set_logger_handle=None):
        """returns/sets the logger-handle """
        if set_logger_handle != None:
            self._logger = set_logger_handle
        return self._logger
#--- class ccollgate_cfg end ---#
################################################

class cstore2db(threading.Thread):
    """StoreData to DB: created databases are required fore storing the results in db.
        automatic draw for rrdtool-draw ist called every 60 sec. if db is enabled.
        automatic erase of old data is done in sqlite-db if it is enabled.
    """
    def __init__(self, cfg_file, ht_if, logging):
        threading.Thread.__init__(self)
        self._ht_if = ht_if
        self._cfg_file = cfg_file
        self._logging = logging
        self.__thread_run = True
        self.__autoerasechecktime = int(time.time()) + 120

    def __del__(self):
        """class desctructor """

    def __Autoerasing_sqlitedb(self, h_database):
        """check sqlite database for the oldest entries and delete them if time_limit is reached."""
        if int(time.time()) >= int(self.__autoerasechecktime):
            time_limit = int(time.time()) - int(self._ht_if._data.Sqlite_autoerase_seconds())
            # get oldest UTC in database
            firstentry_UTC = self.__GetOldestEntry(h_database)
            if firstentry_UTC == None:
                firstentry_UTC = int(time.time())

            if firstentry_UTC < time_limit:
                debugstr = "Autoerasing_sqlitedb(); UTCs current:{0}; oldest in db:{1}; limit:{2}".format(int(time.time()), firstentry_UTC, time_limit)
                self._logging.info(debugstr)

                try:
                    debugstr = "sqlite-db autoerasing started;  time:{0}".format(int(time.time()))
                    self._logging.info(debugstr)
                    # erase old datacontend in sqlite-db
                    for systempartname in self._ht_if._data.syspartnames():
                        h_database.delete(systempartname, "UTC", str(time_limit), "<")
                        debugstr = "table-content:<{0}> deleted where UTC is less then:<{1}>".format(systempartname, time_limit)
                        self._logging.info(debugstr)
                    # cleanup db
                    h_database.vacuum()
                    debugstr = "sqlite-db autoerasing finished; time:{0}".format(int(time.time()))
                    self._logging.info(debugstr)
                except (sqlite3.OperationalError, ValueError) as e:
                    errorstr = "cstore2db.__Autoerasing_sqlitedb();Error; {0}".format(e)
                    self._logging.critical(errorstr)

            # setup next check-time
            self.__autoerasechecktime = int(time.time()) + 120

    def __GetOldestEntry(self, h_database):
        """try to find the first timestamp-entry in column 'UTC' and table
            'heizgeraet' and return the value. If not found then return 'None'
             search - excample:
              SELECT UTC FROM heizgeraet WHERE UTC NOT NULL ORDER UTC ASC
        """
        sqlsearchstring = "NOT NULL"
        sqlorderbystring = "ORDER BY UTC ASC"
        rtnvalue = None
        try:
            selectrtn = h_database.selectwhere('heizgeraet', 'UTC', sqlorderbystring, sqlsearchstring, 'UTC')
            if not selectrtn == []:
                for valuetmp in list(selectrtn):
                    # get first UTC-timestamp
                    rtnvalue = int(valuetmp[0:1][0])
                    break
        except (sqlite3.OperationalError, ValueError) as e:
            errorstr = "cstore2db.__GetOldestEntry();Error; {0}".format(e)
            self._logging.critical(errorstr)
            rtnvalue = None
        return rtnvalue

    def run(self):
        """worker thread for sqlite-db using 'threading.Thread'"""
        import sqlite3
        import db_sqlite
        import db_rrdtool
        debug = 0
        rrdtooldb = None
        nextTimeStep = time.time()
        nextTimeautocreate = time.time()
        sqlite_autoerase = False

        # get db-instance
        database = db_sqlite.cdb_sqlite(self._cfg_file, logger=self._logging)
        database.connect()

        # set flag for erasing sqlite-db if enabled
        if database.is_sql_db_enabled() and self._ht_if.ht_if_data().Sqlite_autoerase_seconds() > 0:
            sqlite_autoerase = True

        if self._ht_if.ht_if_data().is_db_rrdtool_enabled():
            try:
                rrdtooldb = db_rrdtool.cdb_rrdtool(self._cfg_file, self._logging)
                rrdtooldb.createdb_rrdtool()
                # setup the first 'nextTimeStep' to 3 times stepseconds waiting for valid data
                nextTimeStep = time.time() + int(self._ht_if.ht_if_data().db_rrdtool_stepseconds()) * 3
            except:
                errorstr = "cstore2db.run();Error; could not init rrdtool-db"
                self._logging.critical(errorstr)
                self._logging.info("cstore2db.run(); End   ----------------------")
                quit()
            # setup first timestep-value for autocreating draw
            if self._ht_if.ht_if_data().IsAutocreate_draw() > 0:
                nextTimeautocreate = time.time() + 240

        while self.__thread_run:
            try:
                # read values from queue, wait if empty or stop if (None, None)
                (nickname, value) = self._ht_if.decoded_data_4_DBs().get()
                # terminate thread if both values are None, else process them
                if (nickname, value) == (None, None):
                    self.stop()
                    break

                if database.is_sql_db_enabled():
                    database.insert(str(self._ht_if.ht_if_data().getlongname(nickname)), value)
                    database.commit()

                if self._ht_if.ht_if_data().is_db_rrdtool_enabled() and rrdtooldb != None:
                    # write data to rrdtool-db after 'stepseconds' seconds
                    if time.time() >= nextTimeStep:
                        # setup next timestep
                        nextTimeStep = time.time() + int(self._ht_if.ht_if_data().db_rrdtool_stepseconds())
                        # update rrdtool database
                        for syspartshortname in rrdtooldb.syspartnames():
                            if syspartshortname.upper() == 'DT':
                                continue
                            syspartname = rrdtooldb.syspartnames()[syspartshortname]
                            itemvalue_array = self._ht_if.ht_if_data().getall_sorted_items_with_values(syspartshortname)
                            error = rrdtooldb.update(syspartname, itemvalue_array, time.time())
                            if error:
                                self._logging.critical("rrdtooldb.update();Error;syspartname:{0}".format(syspartname))

                if self._ht_if.ht_if_data().is_db_rrdtool_enabled() and self._ht_if.ht_if_data().IsAutocreate_draw() > 0:
                    if time.time() >= nextTimeautocreate:
                        # setup next timestep for autocreating draw
                        nextTimeautocreate = time.time() + 60 * self._ht_if.ht_if_data().IsAutocreate_draw()
                        # create draw calling script
                        (db_path, dbfilename) = self._ht_if.ht_if_data().db_rrdtool_filepathname()
                        (html_path, filename) = self._ht_if.ht_if_data().db_rrdtool_filepathname('.')
                        rrdtooldb.create_draw(db_path, html_path,
                                              self._ht_if.ht_if_data().heatercircuits_amount(),
                                              self._ht_if.ht_if_data().controller_type_nr(),
                                              self._ht_if.ht_if_data().GetAllMixerFlags())

                if sqlite_autoerase:
                    self.__Autoerasing_sqlitedb(database)

                # clear last queue-entry with task_done()
                self._ht_if.decoded_data_4_DBs().task_done()
            except:
                errorstr = "cstore2db.run();Error; on ht_if.decoded_data_4_DBs().get()"
                self._logging.critical(errorstr)
                self.stop()
                raise
        #close db at the end of thread
        database.close()
        errorstr = "cstore2db.run();Error; thread terminated unexpected"
        self._logging.critical(errorstr)

    def stop(self):
        """ """
        self.__thread_run = False
        self._ht_if.decoded_data_4_DBs().put(None, None)
#--- class cstore2db end ---#
################################################

class ccollgate(threading.Thread, ccollgate_cfg, ht_utils.clog):
    """
    """
    def __init__(self, collgate_cfgfilename, loglevel_in=logging.INFO):
        threading.Thread.__init__(self)
        ccollgate_cfg.__init__(self, logger=None, loglevel=loglevel_in)
        ht_utils.clog.__init__(self)
        self.__configfilename = collgate_cfgfilename
        self.__loglevel_in = loglevel_in
        try:
            self._logger = self._create_logger()
        except:
            errorstr = "ccollgate().__init__();Error;could not create logfile"
            print(errorstr)
            raise

        self.logger_handle(self._logger)

        try:
            # read collgate - configuration
            self.read_collgate_config(collgate_cfgfilename)
        except:
            errorstr = "ccollgate().__init__();Error;could not get configurationfile-infos from file:'{0}'".format(self.__configfilename)
            self._logger.critical(errorstr)
            print(errorstr)
            raise

        self.__thread_run = True
        self._ht_if = None
        self._store2db = None
        self._mqtt_pub_client = None
        self._sps_if = None

    def __del__(self):
        """
        """
        self.__thread_run = False

    def __Queuedata_required(self):
        """
        """
        rtnvalue = ccollgate.get_enable_flag(self, ccollgate_cfg.IF_mqtt)
        return bool(rtnvalue)

    def _create_logger(self, filepath="./var/log/Ccollgate.log", tag="Ccollgate"):
        """creating logger with default values (overwrite-able)."""
        rtnvalue = None
        try:
            self._logger_tag = tag
            ht_utils.clog.__init__(self)
            (path, filename) = os.path.split(filepath)
            if len(filename) == 0:
                filename = 'Ccollgate.log'
            absfilepath = ht_utils.cht_utils.MakeAbsPath2FileName(self, (path, filename))
            rtnvalue = ht_utils.clog.create_logfile(self,
                                                    logfilepath=absfilepath,
                                                    loggertag=tag)
        except:
            errorstr = "ccollgate.create_logger();could not create logger-file:{0}; logger-tag:{1}".format(filepath, tag)
            raise EnvironmentError(errorstr)
        return rtnvalue

    def run(self):
        """ starting the interfaces if cfg-flag is set."""
        data_flag = False
        accessnames = {}
        infostr = "Starting 'Ccollgate.run()"
        self._logger.info(infostr)

        try:
            try:
                data_flag = self.__Queuedata_required()
                ht_cfg_filename = self.get_cfg_file(ccollgate_cfg.IF_ht)
                # start ht - interface for receiving and decoding heater bus-data
                self._ht_if = cht_if_worker(ht_cfg_filename,
                                  putdata_flag=data_flag,
                                  logging=self._logger,
                                  loglevel_in=self.__loglevel_in)
                self._ht_if.setDaemon(True)
                self._ht_if.start()
                accessnames = self._ht_if.get_accessnames()
            except:
                errorstr = "ccollgate().run();Error;could not start 'ht-interface' with file:'{0}'".format(ht_cfg_filename)
                self._logger.critical(errorstr)
                self.stop()
                raise SystemExit

            try:
                # start thread storing decoded data to databases sqlite and rrdtool
                cfg_file = self.get_cfg_file(ccollgate_cfg.IF_ht)
                self._store2db = cstore2db(cfg_file, self._ht_if, logging=self._logger)
                self._store2db.setDaemon(True)
                self._store2db.start()
            except:
                errorstr = "ccollgate().run();Error;could not start 'sqlite / rrdtool-DBinterface''"
                self._logger.critical(errorstr)
                self.stop()
                raise SystemExit

            # start mqtt - interface if enabled
            if self.get_enable_flag(ccollgate_cfg.IF_mqtt):
                try:
                    import mqtt_client_if
                    cfg_file = self.get_cfg_file(ccollgate_cfg.IF_mqtt)
                    dataqueues = (self._ht_if.decoded_data_queue(), self._ht_if.data_2_send_queue())
                    self._mqtt_pub_client = mqtt_client_if.cmqtt_client(cfg_file, accessnames_in=accessnames)
                    self._mqtt_pub_client.set_dataqueues(dataqueues_rx_tx=dataqueues)
                    self._mqtt_pub_client.setDaemon(True)
                    self._mqtt_pub_client.start()
                except:
                    errorstr = "ccollgate().run();Error;could not start 'mqtt-interface' with file:'{0}'".format(cfg_file)
                    self._logger.critical(errorstr)
                    print(errorstr)
                    self.stop()
                    raise SystemExit

            # start SPS - interface if enabled
            if self.get_enable_flag(ccollgate_cfg.IF_sps):
                try:
                    import SPS_if
                    cfg_file = self.get_cfg_file(ccollgate_cfg.IF_sps)
                    self._sps_if = SPS_if.cSPS_if(cfg_file, heater_data_obj=self._ht_if.ht_if_data())
                    self._sps_if.setDaemon(True)
                    self._sps_if.start()
                except:
                    errorstr = "ccollgate().run();Error;could not start 'sps-interface' with file:'{0}'".format(cfg_file)
                    self._logger.critical(errorstr)
                    print(errorstr)
                    self.stop()
                    raise SystemExit

            while self.__thread_run:
                # sleep a bit
                time.sleep(2.0)
                #check running threads, on error raise exception
                if self._ht_if != None:
                    if not self._ht_if.is_alive():
                        errorstr = "ccollgate().run();Error;cht_if_worker-thread terminated."
                        self._logger.critical(errorstr)
                        raise
                if self._store2db != None:
                    if not self._store2db.is_alive():
                        errorstr = "ccollgate().run();Error;cstore2db_if-thread terminated."
                        self._logger.critical(errorstr)
                        raise
                if self._mqtt_pub_client != None:
                    if not self._mqtt_pub_client.is_alive():
                        errorstr = "ccollgate().run();Error;mqtt_client_if-thread terminated, see mqtt-logfile for details."
                        self._logger.critical(errorstr)
                        raise
                if self._sps_if != None:
                    if not self._sps_if.is_alive():
                        errorstr = "ccollgate().run();Error;SPS_if-thread terminated."
                        self._logger.critical(errorstr)
                        raise
        except:
            self.stop()
            errorstr = "ccollgate().run();Error; terminated"
            self._logger.critical(errorstr)
            print(errorstr)
            raise SystemExit

    def stop(self):
        """ """
        self.__thread_run = False
        if self._ht_if != None:
            self._ht_if.stop()
            self._ht_if = None
        if self._store2db != None:
            self._store2db.stop()
            self._store2db = None
        if self._mqtt_pub_client != None:
            self._mqtt_pub_client.stop()
            self._mqtt_pub_client = None
        if self._sps_if != None:
            self._sps_if.stop()
            self._sps_if = None
#--- class ccollgate end ---#
################################################

### Runs only for test ###########
if __name__ == "__main__":
    collgate_configurationfilename = './../etc/config/4test/collgate_cfg_test.xml'
# only4debug #    collgate = ccollgate(collgate_configurationfilename, loglevel_in=logging.DEBUG)
    collgate = ccollgate(collgate_configurationfilename)
    cfg = collgate.get_config()
    print("---------------+-------------+-------------------")
    print("Interface-Name | Enable-Flag | Configuration-File")
    print("---------------+-------------+-------------------")
    for key in cfg.keys():
        (flag, file) = cfg[key]
        print("  {0:12.12} |  {1:10.10} | {2}".format(key, str(flag), file))
    print("---------------+-------------+-------------------")
##
#   for testpurposes
#    print("if:{0};flag:{1};file:{2}".format(ccollgate_cfg.IF_ht,
#                                            collgate.get_enable_flag(ccollgate_cfg.IF_ht),
#                                            collgate.get_cfg_file(ccollgate_cfg.IF_ht)))
##

    collgate.start()
