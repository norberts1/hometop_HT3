#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2015 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.7  / Datum 25.02.2015 first release
#################################################################

import sys, time
import argparse
sys.path.append('lib')
import ht_proxy_if, ht_transceiver, ht_yanetcom

__author__  = "Norbert S <junky-zs@gmx.de>"
__status__  = "draft"
__version__ = "0.1.7"
__date__    = "25 February 2015"

def set_options():
     global arguments
     arguments={}
     parser = argparse.ArgumentParser(description='Setup heater-temperaturniveau/runningmode and transceiver-configuration')
     parser.add_argument('-t','--temp', default=10.0, type=float,
                   help='Gewuenschte Temperatur')
     parser.add_argument('-b','--bart', default='none', type=str,
                   help='Betriebsart der Heizung    Parameter:auto/heizen/sparen/frost')
     parser.add_argument('-ht_cfg','--cfg', default=10, type=int,
                   help='Write ht_transceiver config  Parameter:0/1/2/3')
     parser.add_argument('-ht_adr','--adr', default=0, type=int,
                   help='Write ht_transceiver device-address, be carefull using this')
     parser.add_argument('-ht_rst','--rst', default=0, type=int,
                   help='HW-reset of ht_transceiver')
     
     arguments = vars(parser.parse_args())
     
                     
def main():
     global arguments
     error=None
     configfile="./etc/config/ht_proxy_cfg.xml"
     try:
          client= ht_proxy_if.cht_socket_client(configfile, devicetype=ht_proxy_if.DT_MODEM)
     except:
          print("couldn't connect to server")
          raise

     trx=ht_transceiver.ctransceiver(client)
     cfg=ht_yanetcom.cyanetcom(client)
     
     if arguments['temp'] != 10.0:
          error=cfg.set_tempniveau(arguments['temp'])
          if error != None:
               print("{0}".format(error)) 

     if arguments['bart'] != 'none':
          error=cfg.set_betriebsart(arguments['bart'])
          if error != None:
               print("{0}".format(error))

     if arguments['cfg'] != 10:
          error=trx.cfg_mode(arguments['cfg'])
          if error != None:
               print("{0}".format(error))

     if arguments['adr'] != 0:
          error=trx.cfg_deviceaddress(arguments['adr'])
          if error != None:
               print("{0}".format(error))
     
     if arguments['rst'] != 0:
          error=trx.reset()
          if error != None:
               print("{0}".format(error))
               
#################################################################
               
set_options()
main()



