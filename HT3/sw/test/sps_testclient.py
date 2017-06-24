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
# Ver:0.1    / Datum 20.06.2017
#################################################################
######
# This testfile can be used as an example for communication 
#   with the running 'ht_collgate' and to getting decoded heater-data
#   with short commands.
#   This commands you can implement in your SPS-source and running
#   that application for getting data from your heater-system.
#
# Keep in mind that you have to enable the SPS-Interface in the 
# ht_collgate config-file (restart of ht_collgate is required).
#
################################

import sys, os, serial, threading, socket

# SPS server - IP address
SPS_server_IP="localhost"

class csps_testclient(threading.Thread):
    """class 'csps_testclient' is used for sps-communication-server
    """
    def __init__(self, logfilename_in=None, loglevel_in=None):
        threading.Thread.__init__(self)
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__tcp_port    = 10001
        self.__buffer_size = 2048

    def __del__(self):
        pass

    def __helptxt(self):
        print("SPS testclient")
        print(" for sending request-commands to ht_collgate-server")
        print("  connection to:{0}; port:{1}".format(SPS_server_IP, self.__tcp_port))
        print("")
        print("  currently available inputs for test:")
        print("   0, 1, 2, 3, 4: used as SPS short commands")
        print("   10, 11, 12, 13, 14: used as special commands")
        print("   20, 21, 22, 23, 24: used as accessname - commands")
        print("   88 := this help-txt")
        print("   90 := cmd-map output to csv-file in ~/HT3/sw/var/log")

    def run(self):
        self.__helptxt()
        try:
            self.__socket.connect((SPS_server_IP, self.__tcp_port))

            while True:
                nachricht=""
                auswahl = input("Auswahl (99 := quit): ")
                # SPS short commands to ht_collgate
                if auswahl == '0':
                    nachricht="A00"
                if auswahl == '1':
                    nachricht="A01"
                if auswahl == '2':
                    nachricht="A02"
                if auswahl == '3':
                    nachricht="A03"
                if auswahl == '4':
                    nachricht="A04"
                if auswahl == '10':
                    nachricht="S00"
                if auswahl == '11':
                    nachricht="S01"
                if auswahl == '12':
                    nachricht="H00"
                if auswahl == '13':
                    nachricht="H01"
                if auswahl == '14':
                    nachricht="G14"
                # accessname commands to ht_collgate
                if auswahl == '20':
                    nachricht="ch_Tflow_desired"
                if auswahl == '21':
                    nachricht="ch_Tflow_measured"
                if auswahl == '22':
                    nachricht="ch_Treturn"
                if auswahl == '23':
                    nachricht="ch_T3waymixer"
                if auswahl == '24':
                    nachricht="ch_mode"
                if auswahl == '90':
                    nachricht="S09"
                if auswahl == '98':
                    nachricht="bad_command"
                if len(nachricht) > 1:
                    print("send     -> :{0}".format(nachricht))
                    self.__socket.sendall(bytes(nachricht, "utf-8"))
                    antwort = self.__socket.recv(self.__buffer_size)
                    print ("response <- :{0}".format(antwort.decode()))
                else:
                    if auswahl == '99':
                        print("Ende")
                        break
                    if auswahl == '88':
                        self.__helptxt()
                    else:
                        print("unknown command, nothing to send")
        except:
            errorstr = "client socket-error"
            print(errorstr)
            
           
        finally:
            self.__socket.close()
            

#--- class csps_testclient end ---#
################################################


### Runs only for test ###########
if __name__ == "__main__":
    sps_if=csps_testclient()
    sps_if.start()
    

