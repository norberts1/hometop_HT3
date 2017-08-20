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
# Ver:0.2    / Datum 20.08.2017 waiting max 120 seconds in broker_available()
#################################################################

import xml.etree.ElementTree as ET
import os
import time
import threading
import queue
import ht_utils
import logging

import paho.mqtt.client as paho

__author__  = "junky-zs"
__status__  = "draft"
__version__ = "0.2"
__date__    = "20.08.2017"

"""
#################################################################
# modul: mqtt_client_if.py                                      #
#  This modul should be used for mqtt-handling and to create    #
#  your own mqtt-client.                                        #
#  It supports you with following classes:                      #
#   1. reading the configuration-file (XML-File),               #
#   2. mqtt-baseclass for connection, subscribing and           #
#      publishing to the broker                                 #
#       and                                                     #
#   3. mqtt_client-class using that mqtt_baseclass for special  #
#      handling on heater-messages (publish-part) and for       #
#      watching on commands for the heater (subscribe-part).    #
#      This class could be the example for your own class for   #
#      other purposes.                                          #
#                                                               #
# class: cmqtt_cfg()                                            #
#  This class reads the XML configurationfile and extracts the  #
#  content for further using.                                   #
#  It also creates the logging-file namely defined in the       #
#  config-file                                                  #
#  All parameters are accessable with there own methods.        #
#                                                               #
# class: cmqtt_baseclass()                                      #
#  This class supports you with methods for connecting to the   #
#  broker, processing after connection or reconnection and      #
#  processing for received messages (overload-able).            #
#                                                               #
# class: cmqtt_client()                                         #
#  This class uses the mqtt_baseclass and is designed for       #
#  heater-data message-handling.                                #
#  The 'topic root-name' read from configuration-file together  #
#  with the 'header accessnames' are used to create the         #
#  final topics -names for publishing.                          #
#  For subscribing the 'topic root-name' is used togehter with  #
#  the 'set/'-command as: 'set/'<topic_root_name>/#'.           #
#                                                               #
#################################################################
"""

class cmqtt_cfg(ht_utils.clog):
    """reading configuration-values from XML-file."""
    #common used configuration-values
    my_userdata = 'my_heatersystem'

    def __init__(self, cfg_filename):
        """class constructor."""
        ht_utils.clog.__init__(self)

        self._cfg_filename = cfg_filename
        self._logging = None

        self._logfilepathname = None
        self._loglevel = logging.INFO

        self.__user = ""
        self.__password = ""
        self.__brokeraddress = "localhost"
        self.__portnumber = 1883
        self.__topic_root_name = "ht"
        self.__QoS = 1
        self.__CleanSession = False
        self.__Retain = True
        self.__LastWillRetain = True
        self.__Publish_OnlyNewValues = False
        self.__client_id = "myID"

    def __del__(self):
        """class destructor."""

    def _create_logger(self, filepath="./var/log/mqtt_client.log", tag="cmqtt_client"):
        """creates the logger with default values (overwrite able)."""
        rtnvalue = None
        try:
            (path, filename) = os.path.split(filepath)
            if len(filename) == 0:
                filename = 'mqtt_client.log'
            logfilepathname = ht_utils.cht_utils.MakeAbsPath2FileName(self, (path, filename))
            self.cfg_logfilepathname(logfilepathname)
            rtnvalue = ht_utils.clog.create_logfile(self, logfilepath=logfilepathname, loggertag=tag)
        except:
            errorstr = "cmqtt_cfg.create_logger();could not create logger-file:{0}; logger-tag:{1}".format(filepath, tag)
            raise EnvironmentError(errorstr)
        return rtnvalue

    def cfg_filename(self):
        """returns the current cfg-filename. """
        return self._cfg_filename

    def cfg_logging(self, logging=None):
        """returns/sets the logging-handle."""
        if logging != None:
            self._logging = logging
        return self._logging

    def cfg_logfilepathname(self, filepathname=None):
        """returns/sets the used log- file and path name."""
        if filepathname != None:
            self._logfilepathname = filepathname
        return self._logfilepathname

    def cfg_loglevel(self, loglevel_str=""):
        """returns/sets the loglevel as int-value (see logging)."""
        if len(loglevel_str) > 0:
            self._loglevel = ht_utils.clog.loglevel(self, loglevel_str)
        return self._loglevel

    def cfg_brokeraddress(self):
        """returns the broker-URL from cfg-file."""
        return self.__brokeraddress

    def cfg_portnumber(self):
        """returns the portnumber from cfg-file."""
        return self.__portnumber

    def cfg_username(self):
        """returns the username from cfg-file."""
        return self.__user

    def cfg_password(self):
        """returns the password from cfg-file."""
        return self.__password

    def cfg_topic_root_name(self):
        """returns the topic root-name from cfg-file."""
        return self.__topic_root_name

    def cfg_QoS(self):
        """returns the current Quality of Service cfg-value."""
        return self.__QoS

    def cfg_CleanSession(self):
        """returns the current CleanSession cfg-flag."""
        return self.__CleanSession

    def cfg_RetainFlag(self):
        """returns the current retain cfg-flag."""
        return self.__Retain

    def cfg_LastWillRetain(self):
        """returns the current LW retain cfg-flag."""
        return self.__LastWillRetain

    def cfg_OnlyNewValues(self):
        """returns the current OnlyNewValue cfg-flag."""
        return self.__Publish_OnlyNewValues

    def cfg_client_ID(self):
        """returns the client-ID configured in cfg-file."""
        return self.__client_id

    def cfg_read(self):
        """read the configuration-file and sets the private parameter."""
        try:
            self.__tree = ET.parse(self._cfg_filename)
        except (NameError, EnvironmentError) as e:
            # if not already done create logger with default values
            if self.cfg_logging() == None:
                self.cfg_logging(self._create_logger())
            errorstr = "cmqtt_cfg.cfg_read();Error;{0} on file:'{1}'".format(e.args[0], self._cfg_filename)
            self.cfg_logging().critical(errorstr)
            raise
        else:
            try:
                self.__root = self.__tree.getroot()
            except:
                errorstr = "cmqtt_cfg.read_db_config();Error on getroot()"
                self.cfg_logging().critical(errorstr)
                raise
            try:
                # find logging -entries
                for logging_param in self.__root.findall('logging'):
                    path = logging_param.find('path').text
                    default_filename = logging_param.find('filename').text
                    #  join both 'path' and 'filename' and save it
                    logfilepathname = os.path.normcase(os.path.join(path, default_filename))
                    self.cfg_logfilepathname(logfilepathname)
                    if self.cfg_logging() == None:
                        # check if called from itself or used from outside
                        if __name__ == "__main__":
                            self.cfg_logging(self._create_logger())
                        else:
                            self.cfg_logging(self._create_logger(logfilepathname))
                    #  get and save loglevel
                    self.cfg_loglevel( logging_param.find('loglevel').text.upper() )
            except:
                # if not already done create logger with default values
                errorstr = "cmqtt_cfg.read_db_config();Error on logging parameter"
                self.cfg_logging().critical(errorstr)
                raise

            try:
                # find broker-entries
                search_tag='mqtt_broker'
                for broker_param in self.__root.findall(search_tag):
                    search_tag='serveraddress'
                    self.__brokeraddress = broker_param.find(search_tag).text
                    search_tag='portnumber'
                    self.__portnumber = int(broker_param.find(search_tag).text)
                    search_tag='user'
                    self.__user = str(broker_param.find(search_tag).text)
                    search_tag='password'
                    self.__password = str(broker_param.find(search_tag).text)
            except:
                errorstr = "cmqtt_cfg.read_db_config();Error reading parameter:{0}".format(search_tag)
                self.cfg_logging().critical(errorstr)
                raise

            try:
                # find client-entries
                search_tag='mqtt_client'
                for client_param in self.__root.findall(search_tag):
                    search_tag='topic_root_name'
                    self.__topic_root_name = str(client_param.find(search_tag).text)
                    search_tag='QoS'
                    self.__QoS = int(client_param.find(search_tag).text)
                    if not self.__QoS in (0,1,2):
                        self.__QoS = 0
                    search_tag='CleanSession'
                    self.__CleanSession = str(client_param.find(search_tag).text).upper()
                    self.__CleanSession = bool(True if self.__CleanSession == 'TRUE' else False)
                    search_tag='Retain'
                    self.__Retain = str(client_param.find(search_tag).text).upper()
                    self.__Retain = bool(True if self.__Retain == 'TRUE' else False)
                    search_tag='LastWillRetain'
                    self.__LastWillRetain = str(client_param.find(search_tag).text).upper()
                    self.__LastWillRetain = bool(True if self.__LastWillRetain == 'TRUE' else False)
                    search_tag='Publish_OnlyNewValues'
                    self.__Publish_OnlyNewValues = str(client_param.find(search_tag).text).upper()
                    self.__Publish_OnlyNewValues = bool(True if self.__Publish_OnlyNewValues == 'TRUE' else False)
                    search_tag='client_id'
                    self.__client_id = client_param.find(search_tag).text
            except:
                errorstr = "cmqtt_cfg.read_db_config();Error reading parameter:{0}".format(search_tag)
                self.cfg_logging().critical(errorstr)
                raise
#--- class cmqtt_cfg end ---#
################################################

class cmqtt_baseclass(threading.Thread, cmqtt_cfg):
    """class 'cmqtt_baseclass' is the baseclass for mqtt-handling.
            the configuration-file is read to get the mqtt-values.
            the 'run()' method must be implemented in deriving class.
    """
    def __init__(self, cfg_filename):
        """class constructor."""
        threading.Thread.__init__(self)
        cmqtt_cfg.__init__(self, cfg_filename)

        self.__thread_run = True
        self._wait4connection = True
        self.__client = None

    def __del__(self):
        """class destructor."""
        self.stop()

    def _client_handle(self, client_handle=None):
        """returns/sets the handle to the connected/reconnected client."""
        if client_handle != None:
            self.__client = client_handle
        return self.__client


    def stop(self):
        """setting flag for thread-termination."""
        self.__thread_run = False

    def run(self):
        """This must be defined in using class."""

    def loop(self):
        """ """
        return self.__thread_run

    ###############################################
    ####### callback functions for mqtt ##########
    def on_connect(self, client, userdata, flags, rc):
        """callback fkt to be called after connection."""
        self.processing_on_connect(client, userdata, flags, rc)

    def on_disconnect(self, client, userdata, mid):
        """callback fkt to be called after disconnection."""
        pass

    def on_publish(self, client, userdata, mid):
        """callback fkt to be called on publish."""
        pass
        # print("mid: {0}; userdata:{1}".format(str(mid), userdata))

    def on_subscribe(self, mosq, obj, mid, granted_qos):
        """callback fkt to be called on subscribe."""
        debugstr = "Subscribed: {0} {1}".format(str(mid), str(granted_qos))
        self.cfg_logging().debug(debugstr)

    def on_message(self, client1, userdata, message):
        """callback fkt to be called on message received."""
        self.processing_payload(userdata, message.topic, str(message.payload.decode("utf-8")))

    def on_log(self, client, userdata, level, buf):
        """callback fkt to be called for logging."""
        debugstr = "mqtt-log:{0}".format(buf)
        self.cfg_logging().debug(debugstr)
    ####### callback functions for mqtt ##########
    ###############################################

    def processing_on_connect(self, client, userdata, flags, rc):
        """overwrite this methode for your own connect-handling."""
        infostr = "CONNACK received with code: {0}; client_obj: {1}.".format(rc, client)
        self.cfg_logging().info(infostr)
        print(infostr)
        if rc == 0:
            self._wait4connection = False

    def processing_payload(self, userdata, topic, payload):
        """overwrite this methode for your own message-handling."""

    def broker_available(self):
        """checking availability of broker.
            waiting at least for 120 seconds for availability of
            the mqtt-broker server.
            mainly used once at startup of the mqtt-client.
        """
        rtnvalue = False
        import socket
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.setblocking(False)
        address = (self.cfg_brokeraddress(), self.cfg_portnumber())
        loop = 0
        try:
            infostr = "mqtt-broker server availability check:{0}".format(address)
            self.cfg_logging().info(infostr)
            infostr = ""
            dotstr = ""
            # waiting 120 seconds at least for connection
            while loop < 120:
                connect_status = my_socket.connect_ex(address)
                if connect_status == 0:
                    rtnvalue = True
                    break
                loop += 1
                dotstr = dotstr + "."
                if not (loop % 5):
                    infostr = " waiting" + dotstr + "{0} seconds".format(loop)
                    self.cfg_logging().info(infostr)
                    infostr = ""
                    dotstr = ""
                time.sleep(1.0)
        except:
            rtnvalue = False
        my_socket.close()
        return rtnvalue

    def mqtt_init(self):
        """initialisation of mqtt-client with values from cfg-file."""
        rtnvalue = False
        #check broker availability at first
        self.cfg_logging().info("-----------------------------")
        if not self.broker_available():
            errorstr = """cmqtt_baseclass.mqtt_init() broker not available:{0}; port:{1}""".format(self.cfg_brokeraddress(),
                                                                                                  self.cfg_portnumber())
            self.cfg_logging().critical(errorstr)
            print(errorstr)
            rtnvalue = False
            self.stop()
        else:
            #broker is available, so connect using paho
            self.__client = paho.Client(client_id=self.cfg_client_ID(),
                                    clean_session=self.cfg_CleanSession(),
                                    userdata=cmqtt_cfg.my_userdata)
#                                    userdata='my_heatersystem')
            try:
                #setup callback-fkt's
                self.__client.on_connect = self.on_connect
                self.__client.on_disconnect = self.on_disconnect
                self.__client.on_publish = self.on_publish
                self.__on_subscribe = self.on_subscribe
                self.__client.on_message = self.on_message
                self.__client.on_log = self.on_log
                #setup user and password if available
                if len(self.cfg_username()) > 0 and len(self.cfg_password()) > 0:
                    self.__client.username_pw_set(self.cfg_username(), self.cfg_password())
                #connect to broker
                infostr = "MQTT Pub-Client try to connected to MQTT-broker at address:{0}; port:{1}".format(self.cfg_brokeraddress(),
                                                                                        self.cfg_portnumber())
                self.cfg_logging().info(infostr)
                self.__client.connect(host=self.cfg_brokeraddress(), port=self.cfg_portnumber(), keepalive=60)
                self.__client.loop_start()
                rtnvalue = True
            except:
                errorstr = """mqtt_client_if.mqtt_init() connect error on host:{0}; port:{1}""".format(self.cfg_brokeraddress(),
                                                                                                   self.cfg_portnumber())
                self.cfg_logging().critical(errorstr)
                self.stop()
                rtnvalue = False
                raise
            #wait for connection response 'on_connect()'
            timer_counter = 0
            while self._wait4connection == True and timer_counter < 10:
                timer_counter += 1
                time.sleep(1.0)
            try:
                if timer_counter >= 10:
                    #no connection in time, raise error
                    rtnvalue = False
                    raise
            except:
                errorstr = "MQTT-Client !!!NO connection in time!!! to address:{0};port:{1}".format(self.cfg_brokeraddress(), self.cfg_portnumber())
                print(errorstr)
                self.cfg_logging().critical(errorstr)
                self.stop()
                rtnvalue = False
            else:
                infostr = "MQTT Pub-Client connected to address:{0}; port:{1}".format(self.cfg_brokeraddress(), self.cfg_portnumber())
                self.cfg_logging().info(infostr)
                self.cfg_logging().info(" Parameter:")
                infostr = """  Topic_rootname:{0}; Qos:{1}; CleanSession:{2}""".format(self.cfg_topic_root_name(),
                                                                                   self.cfg_QoS(),
                                                                                   self.cfg_CleanSession())
                self.cfg_logging().info(infostr)
                infostr = """  RetainFlag:{0}; LastWillRetain:{1}; OnlyNewValues:{2}""".format(self.cfg_RetainFlag(),
                                                                                           self.cfg_LastWillRetain(),
                                                                                           self.cfg_OnlyNewValues())
                self.cfg_logging().info(infostr)
                infostr = """  Client_ID:{0}""".format(self.cfg_client_ID())
                self.cfg_logging().info(infostr)
                rtnvalue = True
        return rtnvalue
#--- class cmqtt_baseclass end ---#
################################################

class cmqtt_client(cmqtt_baseclass):
    """class 'cmqtt_client' is used to handle communication with mqtt-broker
        and sends data (publish) to broker.
    """
    def __init__(self, cfg_filename, accessnames_in):
        cmqtt_baseclass.__init__(self, cfg_filename)

        self.__accessnames = accessnames_in
        self.__topic_item_context = {}
        self.__old_values_4_nicknames = {}
        self.__printheader = True

    def __del__(self):
        """class destructor."""
        self.stop()

    def _create_topicnames(self):
        """ Method for creating topicnames.
            The accessnames ares used together with topic-rootname
            from configuration.
        """
        for (nickname, values) in self.__accessnames.items():
            topic_names = []
            for x in range(0, len(values)):
                topic_name = self.cfg_topic_root_name() + "/" + values[x]
                topic_names.append(topic_name)
            self.__topic_item_context.update({nickname:topic_names})

    def __InitialValues_onetime(self, nickname, topic_names):
        """One time initialisation of old_value storages."""
        if self.__old_values_4_nicknames.get(nickname) == None:
            topic_and_values = {}
            #initiate that values
            for x in range(0, len(topic_names)):
                topic_and_values.update({topic_names[x]:999999999})
            self.__old_values_4_nicknames.update({nickname:topic_and_values})

            debugstr = "initial old values for nickname:{0}".format(nickname)
            self._logging.debug(debugstr)

    def __IsNewValue(self, nickname, topic_name, newvalue):
        """returns True/False depending on:
            1. configuration-flag: 'Publish_OnlyNewValues'
            2. compare between old-value and new-value
        """
        if self.cfg_OnlyNewValues():
            if newvalue != self.__old_values_4_nicknames.get(nickname).get(topic_name):
                rtnvalue = True
            else:
                rtnvalue = False
        else:
            # no filtering, all values are set as 'new'
            rtnvalue = True
        # returns the current boolean result
        return rtnvalue

    def __UpdateOldValue(self, nickname, topic, value):
        """This stores the current value for that topic to the object-context
            for later value-comparisions.
        """
        nickname_topic_values = self.__old_values_4_nicknames.get(nickname)
        nickname_topic_values[topic] = value

    def __Topicrequired(self, topic):
        """returns True if the topic is required, else False."""
        rtnvalue = True
        if '_unused_' in topic:
            rtnvalue = False
        return rtnvalue

    def __print_header(self):
        """prints the formatted topic/value-header for debugging."""
        if self.__printheader == True:
            debugstr1 = " -----------------------------------------+-----------"
            debugstr2 = " Topic                                    | value"
            # print(debugstr1)
            # print(debugstr2)
            # print(debugstr1)
            self.cfg_logging().debug(debugstr1)
            self.cfg_logging().debug(debugstr2)
            self.cfg_logging().debug(debugstr1)
            self.__enable_header_print(False)

    def __enable_header_print(self, flag = True):
        self.__printheader = flag

    def __print_topic_value(self, topic, value):
        """prints the formatted topic and value for debugging."""
        debugstr = " {0:40.40} | {1}".format(topic, value)
        self.cfg_logging().debug(debugstr)

    def set_dataqueues(self, dataqueues_rx_tx):
        # tuple for rx and tx-queue
        (self.__data_queue_rx, self.__data_queue_tx) = dataqueues_rx_tx

    def publish_data(self, topic, value):
        """sending data to known and connected broker."""
        try:
            (rc, mid) = self._client_handle().publish(topic,str(value), qos=self.cfg_QoS(), retain=self.cfg_RetainFlag())
            if rc != 0:
                errorstr = "cmqtt_client.publish_data() error occured; topic:{0}; mid:{1}".format(topic, mid)
                self.cfg_logging().warning(errorstr)
            self._client_handle().will_set(topic, payload=value, qos=self.cfg_QoS(), retain=self.cfg_LastWillRetain())
        except:
            errorstr = "cmqtt_client.publish_data() error occured on topic:{0}".format(topic)
            self.cfg_logging().critical(errorstr)
            raise

        if self.cfg_loglevel() == logging.DEBUG:
            self.__print_topic_value(topic, value)

    def subscribe_settopics(self, subscribe_topic=""):
        """subscribes to the topic-parameter, default:'set/<topic_root_name>/#' is used."""
        if len(subscribe_topic) == 0:
            #subscribe to default topic: "set/<topic_root_name>/#"
            subscribe_topic = "set/" + str(self.cfg_topic_root_name()) + "/#"
        #subscribe that topic
        (result, mid) = self._client_handle().subscribe(subscribe_topic, qos=self.cfg_QoS())
        if result != paho.MQTT_ERR_SUCCESS:
            #error occured un subscribing, log it
            errorstr = """cmqtt_client.subscribe_settopics() subscrib-error:{0}""".format(result)
            self.cfg_logging().critical(errorstr)

    def processing_payload(self, userdata, topic, payload):
        """processing payload from received msg. """
        debugstr = "mqtt- userdata:{0}; topic:{1}; payload:{2}".format(userdata, topic, payload)
        self.cfg_logging().debug(debugstr)
        if userdata != cmqtt_cfg.my_userdata:
            #nothing to do, not for me
            pass
        else:
            if len(topic) > 0 and len(payload) > 0:
                if '/' in topic:
                    accessname = topic[topic.rfind('/')+1:]
                else:
                    accessname = topic
                # send setup-tuple to ht_if
                self.__data_queue_tx.put((accessname, payload))
            else:
                errorstr = """cmqtt_client.processing_payload(); error on topic:{0}; payload:{1}.""".format(topic, payload)
                self.cfg_logging().warning(errorstr)

    def processing_on_connect(self, client, userdata, flags, rc):
        """ my own connect handling."""
        infostr = "My CONNACK received with code:{0}.".format(rc)
        self.cfg_logging().info(infostr)
        print(infostr)
        if rc == 0:
            self._wait4connection = False
            self._client_handle(client)
            self.subscribe_settopics()

    def run(self):
        """This task reads the XML-configuration, creates topic-names and is
            waiting for data from rx_queue and processes them.
            topic-names marked with '..._unused_...' are not send to broker.
        """
        debug = False
        init_OK = False
        self.cfg_read()
        if self.cfg_loglevel() == logging.DEBUG:
            debug = True
        #setup topicnames
        self._create_topicnames()
        try:
            # mqtt client initialisation
            init_OK = self.mqtt_init()
        except:
            errorstr = "cmqtt_client.mqtt_init() error"
            self.cfg_logging().critical(errorstr)
            raise SystemExit

        if init_OK:
            try:
                self.subscribe_settopics()
            except:
                errorstr = "cmqtt_client.subscribe() error"
                self.cfg_logging().critical(errorstr)
                raise SystemExit

        try:
            while self.loop() and init_OK:
                # waiting for new data from rx_queue and process it
                (nickname, values) = self.__data_queue_rx.get()
                if (nickname, values) == (None, None):
                    #stop processing if both values are none
                    break

                nickname_topic_names = self.__topic_item_context.get(nickname)
                self.__InitialValues_onetime(nickname, nickname_topic_names)

                # output only for debug-purposes
                if debug:
                    self.__enable_header_print()

                # processing data
                for x in range(0, len(nickname_topic_names)):
                    topic = nickname_topic_names[x]
                    if self.__Topicrequired(topic):
                        if self.__IsNewValue(nickname, topic, values[x]):
                            if debug:
                                self.__print_header()
                            # send data to broker
                            self.publish_data(topic, values[x])
                            # update old value for next comparision
                            self.__UpdateOldValue(nickname, topic, values[x])

                self.__data_queue_rx.task_done()
        except:
            errorstr = "mqtt_client_if() terminated!"
            self.cfg_logging().critical(errorstr)
            if self._client_handle() != None:
                self._client_handle().disconnect()
                self._client_handle().loop_stop()
            raise SystemExit


        if self._client_handle() != None:
            self._client_handle().disconnect()
            self._client_handle().loop_stop()

        errorstr = "mqtt_client_if() terminated!"
        print(errorstr)
        self.cfg_logging().critical(errorstr)
        import sys
        sys.exit(1)
#--- class cmqtt_client end ---#
################################################

### Runs only for test ###########
if __name__ == "__main__":
    mqtt_cfg_filename = './../etc/config/4test/mqtt_client_cfg_test.xml'
    dataqueues = (queue.Queue(), queue.Queue())
    accessnames = {}

    mqtt_client = cmqtt_client(mqtt_cfg_filename, accessnames)
    mqtt_client.set_dataqueues(dataqueues)
    mqtt_client.setDaemon(True)

    print("MQTT broker: address          : '{0}'".format(mqtt_client.cfg_brokeraddress()))
    print("MQTT broker: port             : {0}".format(mqtt_client.cfg_portnumber()))
    print("MQTT Client: topic_rootname   : {0}".format(mqtt_client.cfg_topic_root_name()))
    print("MQTT Client: QualitiyofService: {0}".format(mqtt_client.cfg_QoS()))
    print("MQTT Client: CleanSession-Flag: {0}".format(mqtt_client.cfg_CleanSession()))
    print("MQTT Client: Retain-Flag      : {0}".format(mqtt_client.cfg_RetainFlag()))
    print("MQTT Client: LastWill Retain  : {0}".format(mqtt_client.cfg_LastWillRetain()))
    print("MQTT Client: Only New Values  : {0}".format(mqtt_client.cfg_OnlyNewValues()))
    print("MQTT Client: Client ID        : {0}".format(mqtt_client.cfg_client_ID()))

    print("-----------------------------------------")

    mqtt_client.start()
    time.sleep(2)
    mqtt_client.stop()
