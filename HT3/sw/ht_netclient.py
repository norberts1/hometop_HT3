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
# Ver:0.1.8  / Datum Not Available
# Ver:0.1.9  / Datum 12.05.2016 new options for EMS handling
# Ver:0.1.10 / Datum 10.08.2016 only testversion for CWxyz
# Ver:0.2    / Datum 29.08.2016 rev. to 0.2
#################################################################

import sys, time
import argparse
sys.path.append('lib')
import ht_proxy_if, ht_transceiver, ht_yanetcom, ht_const

__author__  = "junky-zs"
__status__  = "draft"
__version__ = "0.2"
__date__    = "29.08.2016"

def set_options(ems_bus = False):
    global arguments
    arguments={}
    if (ems_bus == False) :
        parser = argparse.ArgumentParser(prog='nt_netclient.py',
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description='''----------------------------------------------------------
Setup heater-temperatur-niveau/-mode of operation
  and transceiver device-adress
----------------------------------------------------------
 example: ht_netclient.py -t 15.5 -tmod frost -hc 2
  -> temperatur-niveau:15.5 for:frost and heating-ciruit:2''')
        parser.add_argument('-t', '--temp', default = 4.0, type = float,
                       help = 'Wanted Temperatur-Niveau for heater-circuit nr.:#')
        parser.add_argument('-tmod', '--tempmod', default = ht_const.HT_TEMPNIVEAU_DUMMY, type = str,
                       help = 'Mode assigned to selected temperatur-niveau. Parameter:heizen/sparen/frost.')
        parser.add_argument('-b', '--bart', default = 'none', type = str,
                       help = 'Mode of Operation for heater-circuit nr.:# Parameter:auto/heizen/sparen/frost.')
    else:
        parser = argparse.ArgumentParser(prog='nt_netclient.py',
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description='''----------------------------------------------------------
Setup heater-temperaturniveau and transceiver device-adress
----------------------------------------------------------
 example: ht_netclient.py -tc2 21.5 -hc 2
  -> temperatur-niveau:21.5 for:Comfort2 and heating-ciruit:2''')
        parser.add_argument('-t', '--temp', default = 4.0, type = float,
                    help = 'Wanted Temperatur (Temporary) --> switching to auto mode')
        parser.add_argument('-tc1', '--tempc1', default = 11.0, type = float,
                    help = 'Wanted Temperatur (Comfort1)  --> switching to auto mode')
        parser.add_argument('-tc2', '--tempc2', default = 12.0, type = float,
                    help = 'Wanted Temperatur (Comfort2)  --> switching to auto mode')
        parser.add_argument('-tc3', '--tempc3', default = 13.0, type = float,
                    help = 'Wanted Temperatur (Comfort3)   --> switching to auto mode')
        parser.add_argument('-teco', '--tempeco', default = 14.0, type = float,
                    help = 'Wanted Temperatur (Eco)       --> switching to auto mode')
        parser.add_argument('-tman', '--tempman', default = 15.0, type = float,
                    help = 'Wanted Temperatur (Manual)    --> switching to manual mode')

        parser.add_argument('-ecomode', '--ecomode', default = -1, type = int,
                    help = 'Set eco-mode; 0:=OFF, 1:=HOLD_OUTD, 2:=HOLD_ROOM, 3:=REDUCED')

        parser.add_argument('-b','--bart', default = 'none', type = str,
                       help = 'Mode of Operation for heater-circuit nr.#;  Parameter:auto/manual')


    parser.add_argument('-hc', '--hcircuit', default = 1, type = str,
                help = 'heater-circuit number; default = 1')
    parser.add_argument('-ht_adr', '--adr', default = 0, type = int,
                help = 'Write ht_transceiver device-address, be carefull using this')
    parser.add_argument('-ht_rst', '--rst', default = 0, type = int,
                help = 'HW-reset of ht_transceiver')

    arguments = vars(parser.parse_args())

def Is_controller_type_ems():
    ems_type = False
    type_input = input("Is controller-type any of CTxyz/CRxyz/CWxyz y/n ?").upper()
    if type_input in ('J','JA','Y','YES'):
        ems_type = True
    return ems_type

def main(configfile, ems_bus):
    global arguments
    error = None
    heater_circuit = 1
    temp_mode = ht_const.HT_TEMPNIVEAU_NORMAL
    
    try:
        client= ht_proxy_if.cht_socket_client(configfile, devicetype = ht_proxy_if.DT_MODEM)
    except:
        print("couldn't connect to server")
        raise

    trx = ht_transceiver.ctransceiver(client)
    cfg = ht_yanetcom.cyanetcom(client, ems_bus)
     
    if ems_bus == False:
        if arguments['hcircuit'] != 1:
            heater_circuit = arguments['hcircuit']

        if arguments['tempmod'] != ht_const.HT_TEMPNIVEAU_DUMMY:
            temp_mode = arguments['tempmod']
        else:
            temp_mode = ht_const.HT_TEMPNIVEAU_NORMAL

        if arguments['temp'] != 4.0:
            error = cfg.set_tempniveau(arguments['temp'], hcircuit_nr = heater_circuit, temperatur_mode = temp_mode)
            if error != None:
                print("{0}".format(error)) 
                
        if arguments['bart'] != 'none':
            error = cfg.set_betriebsart(arguments['bart'])
            if error != None:
                print("{0}".format(error))
    else:
        if arguments['temp'] != 4.0:
            # first setup to auto-mode
            error = cfg.set_operation_mode(ht_const.EMS_OMODE_AUTO)
            if error != None:
                print("{0}".format(error)) 
            time.sleep(1)
            # second setup temperatur (temporary)
            error = cfg.set_tempniveau(arguments['temp'], temperatur_mode = ht_const.EMS_TEMP_MODE_TEMPORARY)
            if error != None:
                print("{0}".format(error)) 

        if arguments['tempc1'] != 11.0:
            # first setup to auto-mode
            error = cfg.set_operation_mode(ht_const.EMS_OMODE_AUTO)
            if error != None:
                print("{0}".format(error)) 
            time.sleep(1)
            # second setup temperatur (comfort1)
            error=cfg.set_tempniveau(arguments['tempc1'], temperatur_mode = ht_const.EMS_TEMP_MODE_COMFORT1)
            if error != None:
                print("{0}".format(error)) 

        if arguments['tempc2'] != 12.0:
            # first setup to auto-mode
            error = cfg.set_operation_mode(ht_const.EMS_OMODE_AUTO)
            if error != None:
                print("{0}".format(error)) 
            time.sleep(1)
            # second setup temperatur (comfort2)
            error=cfg.set_tempniveau(arguments['tempc2'], temperatur_mode = ht_const.EMS_TEMP_MODE_COMFORT2)
            if error != None:
                print("{0}".format(error)) 

        if arguments['tempc3'] != 13.0:
            # first setup to auto-mode
            error = cfg.set_operation_mode(ht_const.EMS_OMODE_AUTO)
            if error != None:
                print("{0}".format(error)) 
            time.sleep(1)
            # second setup temperatur (comfort3)
            error=cfg.set_tempniveau(arguments['tempc3'], temperatur_mode = ht_const.EMS_TEMP_MODE_COMFORT3)
            if error != None:
                print("{0}".format(error)) 

        if arguments['tempeco'] != 14.0:
            # first setup to auto-mode
            error = cfg.set_operation_mode(ht_const.EMS_OMODE_AUTO)
            if error != None:
                print("{0}".format(error)) 
            time.sleep(1)
            # second setup temperatur (eco)
            error=cfg.set_tempniveau(arguments['tempeco'], temperatur_mode = ht_const.EMS_TEMP_MODE_ECO)
            if error != None:
                print("{0}".format(error)) 

        if arguments['tempman'] != 15.0:
            # first setup to manual-mode
            error = cfg.set_operation_mode(ht_const.EMS_OMODE_MANUAL)
            if error != None:
                print("{0}".format(error)) 
            time.sleep(1)
            # second setup temperatur (manual)
            error=cfg.set_tempniveau(arguments['tempman'], temperatur_mode = ht_const.EMS_TEMP_MODE_MANUAL)
            if error != None:
                print("{0}".format(error))

        if arguments['ecomode'] != -1:
            error=cfg.set_ecomode(arguments['ecomode'])
            if error != None:
                print("{0}".format(error))

        if arguments['bart'] != 'none':
            if  str(arguments['bart']).lower() in ('manual','man','m'):
                omode = ht_const.EMS_OMODE_MANUAL
            else:
                omode = ht_const.EMS_OMODE_AUTO
            error=cfg.set_operation_mode(omode)
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
               
###################################################################################
#### !!! setup this flag to:'True' if EMS-typed controller is available         ###
##       else to 'False'                                                         ##
##         Controller-Name       EMS-type Flag                                   ##
##          FR/FWxyz              False                                          ##
##          CR/CW/CTxyz           True                                           ##
Is_EMS_Controller_available = None                                               ##
###################################################################################

if Is_EMS_Controller_available == None:
    ems_bus = Is_controller_type_ems()
else:
    ems_bus = Is_EMS_Controller_available
    
set_options(ems_bus)
configfile="./etc/config/ht_proxy_cfg.xml"
main(configfile, ems_bus)



