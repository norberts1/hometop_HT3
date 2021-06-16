#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2021 Norbert S. <junky-zs at gmx dot de>
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
# Ver:0.1    / 2021-02-28 first release
# Ver:0.2    / 2021-06-14 using subscribe_settopics() with topicname
#                          from config-file.
#################################################################

import sys
from time import sleep
sys.path.append('lib')

#import mqtt_baseclass
from mqtt_client_if import cmqtt_baseclass as mqtt_client
import paho.mqtt.client as paho
import json


__author__  = "junky-zs"
__status__  = "draft"
__version__ = "0.2"
__date__    = "2021-02-14"

#global used values
HA_base_topic = 'homeassistant'
MySensorName  = 'heatersystem'
g_logitem_value_dict = dict()

class c_hometop2HA_if(mqtt_client):
    """ mqtt-class used as interface from hometop_ht to homeassistant mqtt-informations.
         Implemantation is as:
           1.subscribing - modify RX-topic - 2.publish new TX-topic
            with collected payload in json.format.
            1. subscribe to topic: <topic_root_name> from config-file ('hometop/ht')
            2. publishing that received payload with new topic-name:HA_base_topic (homeassistant)
    """

    def __init__(self, cfg_filename):
        super().__init__(cfg_filename)

    def __del__(self):
        pass

    def subscribe_settopics(self, subscribe_topic="hometop/ht/#"):
        """subscribes to the topic-parameter, default:'set/<topic_root_name>/#' is used."""
        #subscribe that topic
        (result, mid) = self._client_handle().subscribe(subscribe_topic, qos=1)
        if result != paho.MQTT_ERR_SUCCESS:
            #error occured un subscribing, log it
            errorstr = """c_hometop2HA_if.subscribe_settopics() subscrib-error:{0}""".format(result)
            self.critical(errorstr)
        else:
            mystring="-->> subscribe:{} <<--".format(subscribe_topic)
            self.debug(mystring)

    def publish_data(self, topic, value):
        """sending data to known and connected broker."""
        try:
            (rc, mid) = self._client_handle().publish(topic,str(value), qos=self.cfg_QoS(), retain=self.cfg_RetainFlag())
            if rc != 0:
                errorstr = "c_hometop2HA_if.publish_data() error occured; topic:{0}; mid:{1}".format(topic, mid)
                print(errorstr)
                self.warning(errorstr)
            else:
                debugstr = "publish_data {0}: {1}".format(topic, value)
                self.debug(debugstr+"\n--------------------------------------------")

                self._client_handle().will_set(topic, payload=value, qos=self.cfg_QoS(), retain=self.cfg_LastWillRetain())
        except Exception as e:
            errorstr = "c_hometop2HA_if.publish_data();error:{} on topic:{}".format(e, topic)
            self.critical(errorstr)
            raise

    def run(self):
        """ method reads that attached config-file and connects to the mqtt-broker.
            running endless startet with start().
        """
        self.cfg_read()
        init_OK = False
        try:
            # mqtt client initialisation
            new_client_id = self.cfg_device_ID() + '_hometop2HA_if'
            init_OK = self.mqtt_init(my_client_id = new_client_id)
        except Exception as e:
            errorstr = "c_hometop2HA_if.mqtt_init();error:{}".format(e)
            self.critical(errorstr)
            print (errorstr)
            raise SystemExit

        while init_OK:
            # do nothing here, everything is done with 'processing_payload()'
            sleep(1.0)

        self.critical("!! hometop2HA_if unexpected terminated !!")

    def processing_on_connect(self, client, userdata, flags, rc):
        """ handler for connection-response to mqtt-broaker."""
        infostr = "My CONNACK received with code: {0}; client_obj: {1}.".format(rc, client)
        self.info(infostr)
        print(infostr)
        if rc == 0:
            self._wait4connection = False
            self._client_handle(client)
            self.subscribe_settopics(subscribe_topic=self.cfg_topic_root_name()+'/#')

    def processing_payload(self, userdata, topic, payload):
        """ handler for processing that received topic and payload.
             1. if 'topic' is received first time, then hassio/config will be generated.
             2. the 'payload' will be added to a json.formated dump as new publish.
        """
        if self._wait4connection == True:
            return

        if 'set/' in topic or HA_base_topic in topic:
            return
        else:
            item_name = topic.replace(self.cfg_topic_root_name()+'/','')

            #create hassio-config for new values, do this only one time for that new value
            if not item_name in g_logitem_value_dict.keys():
                hassio_topic_path   = "{}/sensor/{}".format(HA_base_topic, MySensorName)
                base_payload = {
                    "state_topic": "{}/state".format(hassio_topic_path)
                }
                hassio_payload = dict(base_payload.items())
                json_str = "{{ "+"value_json.{0}".format(item_name) + " }}"
                hassio_payload['value_template'] = json_str
                hassio_payload['name'] = "{}".format(item_name)
                hassio_payload['uniq_id'] = item_name
                if '_T' in item_name and not 'Tniveau' in item_name and not 'Tok' in item_name:
                    # Temperature
                    hassio_payload['device_class'] = 'temperature'
                    hassio_payload['unit_of_measurement'] = '°C'
                else:
                    if 'power' in item_name or 'mixerposition' in item_name:
                        hassio_payload['device_class'] = 'power_factor'
                        hassio_payload['unit_of_measurement'] = '%'
                    else:
                        # others
                        hassio_payload['unit_of_measurement'] = ''
                    
                mqtt_topic_str   = "{}/sensor/{}/{}/config".format(HA_base_topic, MySensorName, item_name)
                mqtt_payload_str = json.dumps(hassio_payload)
                infostr = "Config->topic  :{}\nhassio_payload:{}".format(mqtt_topic_str, mqtt_payload_str)
                self.publish_data(mqtt_topic_str, mqtt_payload_str)
                self.debug(infostr+"\n--------------------------------------------")
                    

            # add logitem_name and attached value to global dict()
            g_logitem_value_dict[item_name] = payload
               
                
            #checking for values and send them to hassio/state
            data = dict()
            mqtt_topic_str   = "{}/sensor/{}/state".format(HA_base_topic, MySensorName)
            for key in g_logitem_value_dict.keys():
                data[key] = "{0}".format(g_logitem_value_dict.get(key))
                mqtt_payload_str = json.dumps(data)

            self.publish_data(mqtt_topic_str, mqtt_payload_str)
#
################## main #####################
#
# common mqtt config-file used
configfile="./etc/config/mqtt_client_cfg.xml"
hometop2HA_if=c_hometop2HA_if(configfile)
# set loglevel as required to: INFO or DEBUG
hometop2HA_if.cfg_loglevel('INFO')
#hometop2HA_if.cfg_loglevel('DEBUG')
logger=hometop2HA_if._create_logger('./var/log/hometop2HA_if.log')
hometop2HA_if.cfg_logging(logger)
hometop2HA_if.start()
