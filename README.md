# hometop_HT3


Most everything needed for your heater-system to be shown at your 'hometop' -> 
*pimp your heater*.

This project is limited to the recording/controlling and presentation of heating and solar informations.
Currently only heater-systems from german manufacturer: **`Junkers`** and system-bus: **'Heatronic/EMS2 (c)'** are supported. 

## Description

This repo can not fulfill all wishes you could have to your 'hometop'.
Each has his ideas such as the 'home' can be 'Top'. 
The presentation of informations from the own 'home' with it's heater-system is what this repo will do.
Other projects are working too on this item, example: [FHEM](www.fhem.de)

This repo was started creating some different boards for the RaspberryPi(c).  
The table shows the currently available boards:
Board-name       | function | remark
-----------------|----------|-------
HT3_Mini_Adapter | receiving Bus - data | for RaspberryPi, see: [Mini-Adapter](https://www.mikrocontroller.net/topic/317004#3432732)
HT3_Micro_Adapter| receiving Bus - data *(with UART<->USB converter)* | any USB-hoster, see: [Micro-Adapter](https://www.mikrocontroller.net/topic/317004#3548193)
ht_piduino       | transmit- and receiving Bus - data *(with ATmega 328)* | for RaspberryPi, see: [ht_piduino](https://www.mikrocontroller.net/topic/317004#3925213)
ht_pitiny        | transmit- and receiving Bus - data *(with ATtiny 841)* | for RaspberryPi, see: [ht_piduino](https://www.mikrocontroller.net/topic/317004#3925213)
ht_motherboard   | usb-interface for above boards *(not for 'HT3_Micro_Adapter')* | see: [ht_motherboard](https://www.mikrocontroller.net/topic/317004#3936050)


The **software** is written in **python** and designed for detection, decoding and controlling of HT - busdata with following features:
Modul-name       | function                                         | remark
-----------------|--------------------------------------------------|--------
create_databases.py  | **tool** for creating databases: sqlite and rrdtool with data from configurationfile.  remark: **run this tool at first before you are starting any other application** | configureable, default: sqlite and rrdtool-db are enabled
HT3_Analyser.py  | **GUI** for system-data and raw-hexdump of decoded ht - busdata *(App writes it's data also to databases sqlite and rrdtool)* | configureable, default running as ht_proxy.client
HT3_Systemstatus.py | **GUI** to show system-data only *(App writes it's data also to databases sqlite and rrdtool)* | configureable, default running as ht_proxy.client
HT3_Logger.py | Running as **daemon** without GUI *(App writes it's data to databases sqlite and rrdtool)* | configureable, default running as ht_proxy.client
ht_proxy.py | **ht-server** to collect data from serial port and supporting connected clients with raw - busdata *(App is running as daemon)* | configureable, default accepting any client
ht_netclient.py | **ht-client** sending commands to the heater-bus *(App needs the running ht_proxy.server and one of the boards: ht_pitiny or ht_piduino)* | configureable, default connecting to 'localhost'
ht_binlogclient.py | **ht-client** acts as logger of binary ht - busdata *(App needs the running ht_proxy.server)* | configureable, default connecting to 'localhost'
ht_client_example.py | **ht-client** acts as example for your one ht-client *(App needs the running ht_proxy.server)* | configureable, default connecting to 'localhost'
~/HT3/sw/etc/upgrade_rrdtool_db/ | **upgrade tool** for upgrading your old rrdtool - database to release:**0.2 and above** *(App needs a lot of space in /tmp folder {>1 GB})* | read the 'readme_add_ds_2_rrd.txt' at first for installation of CPAN-moduls. In case of problems you should rename or delete the current databases and create new ones.

For project - details see the documentation (folder: **~/HT3/docu** ) and the following links:
* RaspberryPi HT-board forum:
[HT-Boards](https://www.mikrocontroller.net/topic/317004#new)
* Software-forum:
[HT-Software](https://www.mikrocontroller.net/topic/324673#new)

The current software can be found in subfolders: **~/HT3/sw/...**  
Any hardware informations are in subfolders: **~/HT3/hw/...**


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

## 0.1.9
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




