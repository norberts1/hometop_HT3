## Changelog
## 0.7.1
`2023-11-08` 
- `reason`: Issue: #28; Mixposition and TS8 added.  
- `moduls`: `lib/gui_worker.py`, `lib/ht_discode.py` and `lib/ht_release.py` are modified.  
- `config`: `HT3_db_cfg.xml` and `HT3_db_off_cfg.xml` updated.  
- `docu  `: `~/HT3/sw/etc/html/HT3-Bus_Telegramme.html` ID:866_22_0 assigned to TS8.  

## 0.7
`2023-10-06` 
- `reason`: Issues: #21, #24 and #28.  
- `moduls`: all are modified.  
- `config`: all are modified and have new content.  
- `importend notes`: it's required to recreate the databases. The old once's aren't compatible anymore.  

## 0.6.3
`2023-03-22` 
- `reason`: Issue: #25 installation-scripts and displays.  
- `modul `: `create_databases.py`, `ht_project_setup.sh`, `__post_setup.sh` modified.  
- `modul `: `db_rrdtool.py` debug-output modified.  
- `modul `: `lib/ht_release.py` updated.  

## 0.6.2
`2023-03-12` 
- `reason`: Issues: #18 and #20. GUI-display modified.  
- `modul `: `ht_discode.py`, `gui_worker.py`, `data.py` modified.  
- `modul `: `lib/ht_release.py` updated.  

## 0.6.1
`2022-12-12` 
- `reason`: socketerror cause early start of ht_collgate.py  
- `modul `: `ht_collgate.py` modified.  

## 0.6
`2022-11-22` 
- `reason`: Issue: #23. recovering from USB disconnection.  
- `modul `: `lib/ht_proxy_if.py` modified.  
- `modul `: `lib/ht_release.py` updated.  

## 0.5
`2022-01-26` 
- `reason`: Issue: #15. new DeviceID's with IPM-Modules.  
- `modul `: `ht_discode.py` modified.  

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




