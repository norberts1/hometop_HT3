# hometop_HT3


Most everything needed for your heater-system to be shown at your 'hometop' -> 
*pimp your heater*.

This project is limited to recording/controlling and presentation of heating and solar informations.
Currently only heater-systems from german manufacturer: **`Junkers`** and system-bus: **`Heatronic/EMS2 (c)`** are supported. 

## Description

This repo can not fulfill all wishes you could have to your 'hometop'.
Each has his ideas such as the 'home' can be 'Top'. 
The presentation of informations from the own 'home' with it's heater-system is what this repo will do.
Other projects are working too on this item, example: [FHEM](http://fhem.de/fhem.html)

This repo was started creating some different boards for the RaspberryPi(c).  
The table shows the currently available boards:  

Board-name       | function             | remark
-----------------|----------------------|-----------------------------------
HT3_Mini_Adapter | receiving Bus - data | for RaspberryPi, see: [Mini-Adapter](https://www.mikrocontroller.net/topic/317004#3432732)
HT3_Micro_Adapter| receiving Bus - data | any USB-hoster, see: [Micro-Adapter](https://www.mikrocontroller.net/topic/317004#3548193)
ht_piduino       | transmit- and receiving Bus - data | for RaspberryPi, see: [ht_piduino](https://www.mikrocontroller.net/topic/317004#3925213)
ht_pitiny        | transmit- and receiving Bus - data | for RaspberryPi, see: [ht_piduino](https://www.mikrocontroller.net/topic/317004#3925213)
ht_motherboard   | usb-interface for above boards | see: [ht_motherboard](https://www.mikrocontroller.net/topic/317004#3936050)


The **software** is written in **python** and designed for detection, decoding and controlling of HT - busdata with following features:  

Modul-name         | function                                         | remark
-------------------|--------------------------------------------------|----------------------------------------
create_databases.py| **tool** for creating databases: sqlite and rrdtool.| configureable
HT3_Analyser.py | **GUI** for system-data and raw-hexdump of decoded ht - busdata| configureable, default running as ht_proxy.client
HT3_Systemstatus.py | **GUI** to show system-data only | configureable, default running as ht_proxy.client
~~HT3_Logger.py~~ | ~~Running as daemon without GUI~~    **is replaced with ht_collgate - daemon**  | ~~configureable, default running as ht_proxy.client~~
ht_collgate.py | Running as **daemon** starting interfaces for ht_data decoding, mqtt-IF and/or SPS-IF, running without GUI | configureable, default running as ht_proxy.client and sqlite = Off; rrdtool = On, mqtt_IF = Off, SPS_IF = Off.
ht_proxy.py | **ht-server** to collect data from serial port and supporting connected clients with raw - busdata| configureable, default accepting any client
ht_netclient.py | **ht-client** sending commands to the heater-bus | configureable, default connecting to 'localhost'
ht_binlogclient.py | **ht-client** acts as logger of binary ht - busdata | configureable, default connecting to 'localhost'
ht_client_example.py | **ht-client** acts as example for your one ht-client | configureable, default connecting to 'localhost'
~/HT3/sw/etc/upgrade_rrdtool_db/ | **upgrade tool** for upgrading your old rrdtool - database to release:**0.2**| read the 'readme_add_ds_2_rrd.txt' at first.

For project - details see the documentation (folder: **`~/HT3/docu`** ) and the following links:
* RaspberryPi HT-board forum:
[HT-Boards](https://www.mikrocontroller.net/topic/317004#new)
* Software-forum:
[HT-Software](https://www.mikrocontroller.net/topic/324673#new)

The current software can be found in subfolders: **`~/HT3/sw/...`**  
Any hardware informations are in subfolders: **`~/HT3/hw/...`**


The software is still under development, but any official release should be runable *'out of the box'* under *Linux*.  
For *Windows* some improvements are required and will be done in the future.  

If you have got any problems with hard- or software, let me know.  
Also your support with binary - logfiles is good to have for further development.

Thank's to all supporting me, in the past and future.  
We all want to have the right thing in the right time.

#### Importent notes:
The reproduction and the commissioning of the adaptations is at your own risk and the description and software do not claim to be complete. A change of software modules and hardware descriptions at any time is possible without notice. Warranty, liability and claims by malfunction of heating or adaptation are hereby expressly excluded.

#### Wichtiger Hinweis:
Der Nachbau und die Inbetriebnahme der Adaptionen ist auf eigene Gefahr und die Beschreibung und die Software erheben nicht den Anspruch auf Vollständigkeit.
Eine Änderung an Software-Modulen und Hardware-Beschreibungen ist jederzeit ohne Vorankündigung möglich.
Gewährleistung, Haftung und Ansprüche durch Fehlfunktionen an Heizung oder Adaption sind hiermit ausdrücklich ausgeschlossen.


## Changelog
## 0.4.3
`2022-01-19` 
- `reason`: Issue: #17. new serial portnaming (changed from ttyAMA0 to serial0).  
- `modul `: all configuration-files (*.xml) modified.  

## 0.4.2
`2021-06-16` 
- `reason`: Issue: #16. mqtt - LWT handling corrected.  
- `modul `: `ht_2hassio.py`, `lib/mqtt_client_if.py` and `config/mqtt_client_cfg.xml` modified.  

## 0.4.1
`2021-03-12` 
- `reason`: Issue: #14. HomeAssistant IF added.  
- `modul `: `ht_2hassio.py`, `ht_2hass` and `lib/ht_release.py` added.  
- `docu  `: `HT3_Adaption.pdf` modified for HA.  

## 0.4
`2021-02-25` 
- `reason`: Issue: #13.  
- `modul `: `gui_worker.py` set to rev.:0.4.  
- `modul `: `lib/ht_proxy_if.py` port# set to 48088.  
- `config`: `etc/config/ht_proxy_cfg.xml` port# to:48088, `etc/html/httpd.py` port# to:48086.

## 0.3.3
`10.09.2020`
- `modul `: `gui_worker.py` with scrollbars and WW:'T-Soll max' added.  
- `modul `: `ht_discode.py` decoding of MsgId's 51 & 52 improved, msglength check added.  
- `config`: `etc/config/HT3_db_cfg.xml` and `etc/config/HT3_db_off_cfg.xml` WW:'V_spare_1' used as WW:'T-Soll max'.

## 0.3.2
`03.12.2019`
- `moduls`: Issue: Deprecated property InterCharTimeout #7; port.setInterCharTimeout() removed.

## 0.3.1
`20.01.2019`
- `moduls`: modified for new log-values, decoding upgraded for Cxyz Controller. See modul-header for details.
- minor modifications in configuration-files, already used databases (from 0.3) can be used further on.

## 0.3
`24.06.2017`
- `moduls`: `ht_collgate.py`, `lib/Ccollgate.py`, `lib/mqtt_client_if.py` and `lib/SPS_if.py` added.
- `modul `: ~~`HT3_Logger.py`~~ and ~~`./etc/sysconfig/ht3_logger`~~ aren't used anymore and renamed to: `*unused`
- New configuration-files added for ht_collgate, mqtt- and SPS- interfaces.

## 0.2.2
`20.10.2016`
- `autocreate_draw in minutes:` modified in moduls: ht3_worker.py, data.py, HT3_db_cfg.xml.
- `3-bytes for solarpump-runtime:` modified in modul: ht_discode.py.
- `tempniveau for FRxyz-controller:` added in moduls: ht_const.py, ht_yanetcom.py.

## 0.2.1
`31.08.2016`
- `wrong path-extraction:` corrected in modul: ht3_worker.py

## 0.2
`29.08.2016`
- `Complete redesign` of decoder and dispatcher using new modul: `ht_discode.py`.  
   - Support for new controller-type: Cxyz added.
- `moduls`: `ht_yanetcom.py` and `ht_netclinet.py` are modified for handling with new controller-type: Cxyz.
- `moduls`: ~~`ht3_dispatch.py`~~ and ~~`ht3_decoder.py`~~ aren't used anymore and renamed to: `ht3_*.py_unused`
- `autocreate_draw` added in configuration-file: *HT3_db_cfg.xml* for updating rrdtool-draw every minute.
   - Default configured to: `On`.
- `autoerase_olddata` added in configuration-file: *HT3_db_cfg.xml* for deleting old dataentries in sqlite-db.
   - Default configured to: `30 days`.
- `db-table`: ~~`rrdtool_info`~~ unused and deleted in sqlite-db.  
   - rrdtool-db is updated instead every 60 seconds with all current data.
- `modul`: ~~`db_info.py`~~ renamed to: `db_info.py_unused`.
- `MsgID ` added for every decoded message displayed as hexdump.
- `GUI` display-layout optimised for viewing all data.
- `Autodetection` of heater-circuit amount and mixed-/unmixed-circuit(s) results also now in GUI-layout update.
- `Displaycode` and `Causecode` added in GUI, database and configuration-file.
- `Betriebsstatus` added in GUI, database and configuration-file.
  - Values: `Manuell` and `Auto` are available.
- `Displayed times` changed from seconds to hours.
- `Renaming` of `Betriebsart` to `Temperatur-Niveau` in GUI, database and configuration-file.
- `Betriebsart` still in database but not supported anymore.
- `script: rrdtool_draw.pl` modified for items:`Temperatur-Niveau` and `Betriebsstatus`.
- `accessname` added in configuration-file for requesting decoded data [currently unused].
- `upgrade rrdtool_db` tool added for upgrading available rrdtool-database to this release: 0.2.
  -     you must have a lot of free space on your drive (> 1 GB in folder: /tmp) doing this upgrade.
  -     the upgrade takes a lot of time do be finished.
  -     if this space isn't available, remove the old database and create a new rrdtool-database.
- `importend notice` the current sqlite-database must be deleted or renamed and has to be recreated for this release:0.2
   using tool: ./create_databases.py.

## ~~0.1.10~~
`05.08.2016`
- `never been an official release`. Used only for testpurposes.

## ~~0.1.9~~
`27.04.2016`
- `HeizkreisMsg_ID677_max33byte()` corrected.
- `msg:9x00FF00()` handling with length of 10byte added.

## 0.1.8.2
`22.02.2016`
- `IPM_LastschaltmodulMsg()` fixed wrong HK-circuit assignment in ht3_decode.py.

## 0.1.8.1
`10.02.2016`
- `HeizkreisMsg_ID677_max33byte()` modified for better decoding.
- `__GetStrBetriebsart()` update with value 4:="Auto".

## 0.1.8
`07.02.2016`
- `HeizkreisMsg_ID677_max33byte()` added for CWxyz handling.

## 0.1.7.1
`04.03.2015`
- `heizungspumpenleistung` added.
- logging from ht_utils added.

## 0.1.6
`10.01.2015`
- `first` release on github.com.




