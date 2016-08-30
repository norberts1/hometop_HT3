#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2013 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.5  / Datum 25.05.2014
# Ver:0.1.6  / Datum 10.01.2015 'reading configuration changed'
#            'constructor without <serialdevice> and <inputfile>'
# Ver:0.1.7.1/ Datum 04.03.2015 'socket interface added'
#                               logging from ht_utils added
# Ver:0.1.8  / Datum 05.10.2015 private:'__gdata' changed to
#                               proteced:'_gdata'
#                               ht3_dispatch replaced with ht_discode
# Ver:0.1.10 / Datum 25.08.2016 rrdtool-db update controlled by time
#                               db_info-class - handling removed
#                               Autoerasing_sqlitedb-handling added
# Ver:0.2    / Datum 29.08.2016 Fkt.doc added
#################################################################

import sys
import os
import serial
import _thread
import sqlite3
import data
import ht_discode
import gui_worker
import db_sqlite
from ht_proxy_if import cht_socket_client as ht_proxy_client
import ht_utils
import logging
import db_rrdtool
import time


class ht3_cworker(object):
    """
        class ht3_cworker for starting GUI if required, open ports,
        watching and writing results.
    """
    # setup static data-struct
    _gdata = data.cdata()

    def __init__(self, configurationfilename, hexdump_window=True, gui_active=True, logfilename_in=None, loglevel_in=None):
        """
            Initialisiation of class.
        """
        self._logging = None
        self._loglevel = logging.INFO
        self.__port = None
        self.__filehandle = None
        self.__threadrun = True
        try:
            if not (isinstance(hexdump_window, int) or isinstance(hexdump_window, bool)):
                errorstr = "ht3_cworker();TypeError;hexdump_window"
                print(errorstr)
                raise TypeError(errorstr)
            self.__cfgfilename = str(configurationfilename)
            self.__hexdump_window = bool(hexdump_window)
            self.__gui_active = bool(gui_active)
            self.__gui_titel_input = "ASYNC "   # default value

        except (EnvironmentError, TypeError) as e:
            errorstr = 'ht3_cworker();Error;Parameter:<{0}> has wrong type'.format(e.args[0])
            print(errorstr)
            raise e

        # read configurationfile and setup default data
        try:
            ht3_cworker._gdata.read_db_config(self.__cfgfilename)
        except:
            errorstr = 'ht3_cworker();Error;could not get configuration-values'
            print(errorstr)
            raise

        try:
            if logfilename_in != None:
                ht3_cworker._gdata.logfilename(logfilename_in)
            if loglevel_in != None:
                loglevel = ht3_cworker._gdata.loglevel(loglevel_in)

            self._loglevel = ht3_cworker._gdata.loglevel()
            logfilepath = ht3_cworker._gdata.logfilepathname()
            abs_logfilepath = os.path.abspath(logfilepath)
            loggertag = "ht3_cworker"
        except:
            errorstr = 'ht3_cworker();Error;could not get cfg-logvalues'
            print(errorstr)
            raise EnvironmentError(errorstr)

        try:
            self._logging = ht3_cworker._gdata.create_logfile(abs_logfilepath, self._loglevel, loggertag)
        except(EnvironmentError, TypeError) as e:
            errorstr = "ht3_cworker();Error; could not create logfile:{0};{1}".format(abs_logfilepath, e.args[0])
            print(errorstr)
            raise e

        self.__serialdevice = str(ht3_cworker._gdata.AsyncSerialdevice())
        self.__baudrate = ht3_cworker._gdata.AsyncBaudrate()
        self.__inputfile = ht3_cworker._gdata.inputtestfilepath()
        if len(self.__inputfile) < 5:
            self.__inputfile = ""
        self.__autoerasechecktime = int(time.time()) + 120

    def __del__(self):
        """
            Destructor of class.
        """
        if self.__port != None:
            self.__port.close()
        self._logging.info("ht3_cworker.run(); End   ----------------------")

    def run(self):
        """
            Main loop doing the work.
        """
        self._logging.info("ht3_cworker.run(); Start ----------------------")
        self._logging.info("ht3_cworker.run();  Loglevel      :{0}".format(logging.getLevelName(self._loglevel)))

        if ((self.__inputfile != None) and (len(self.__inputfile) > 0)):
            # open input-file in readonly-binary mode for analysing binary HT3-data
            try:
                self.__filehandle = open(self.__inputfile, "rb")
                self.__gui_titel_input = "FILE"
            except:
                errorstr = 'ht3_cworker();Error; could not open file:{0}'.format(self.__inputfile)
                self._logging.critical(errorstr)
                quit()
        else:
            # open socket for client and connect to server,
            #   socket-object is written to 'self.__port'
            if(ht3_cworker._gdata.IsDataIf_socket()):
                try:
                    client_cfg_file = os.path.normcase(os.path.abspath(ht3_cworker._gdata.client_cfg_file()))
                    if not os.path.exists(client_cfg_file):
                        errorstr = "ht3_cworker();Error;couldn't find file:{0}".format(client_cfg_file)
                        self._logging.critical(errorstr)
                        raise EnvironmentError(errorstr)
                except:
                    errorstr = "ht3_cworker();Error;couldn't find file:{0}".format(client_cfg_file)
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)
                try:
                    self.__port = ht_proxy_client(client_cfg_file, loglevel=self._loglevel)
                    self.__gui_titel_input = "SOCKET"
                except:
                    errorstr = "ht3_cworker();Error;couldn't open requested socket; cfg-file:{0}".format(client_cfg_file)
                    self._logging.critical(errorstr)
                    raise
            else:
                #open serial port for reading HT3-data
                try:
                    self.__port = serial.Serial(self.__serialdevice, self.__baudrate)
                    self.__port.setInterCharTimeout(0.1)  # VTIME; set to 0.1*1sec
                    self.__gui_titel_input = "ASYNC"
                except:
                    errorstr = "ht3_cworker();Error;couldn't open requested device:{0}".format(self.__serialdevice)
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)

        self._logging.info("ht3_cworker.run();  Datainput-Mode:{0}".format(self.__gui_titel_input))
        if ht3_cworker._gdata.IsDataIf_async():
            self._logging.info("ht3_cworker.run();   Baudrate     :{0}".format(self.__baudrate))
            self._logging.info("ht3_cworker.run();   Configuration:{0}".format(ht3_cworker._gdata.AsyncConfig()))

        try:
            db=db_sqlite.cdb_sqlite(self.__cfgfilename, logger=self._logging)
            # create database-sqlite if required
            if db.is_sql_db_enabled():
                if not db.is_sqlite_db_available():
                    infostr = "ht3_cworker();Wait a bit, database: sqlite will be created"
                else:
                    infostr = "ht3_cworker();sqlite-database already available"
                print(infostr)
                self._logging.info(infostr)

                db.connect()
                db.createdb_sqlite()
                db.close()

            # start thread for dispatching
            _thread.start_new_thread(self.__DispatchThread, (0,))

            if self.__gui_active:
                # start GUI endless until 'Ende' is pressed
                GUI = gui_worker.gui_cworker(ht3_cworker._gdata, self.__hexdump_window, self.__gui_titel_input, logger=self._logging)
                self.__threadrun=GUI.run()

        except (sqlite3.OperationalError, ValueError) as e:
            errorstr = "ht3_cworker();Error; {0}".format(e)
            self._logging.critical(errorstr)
            self._logging.info("ht3_cworker.run(); End   ----------------------")
            quit()

    def __Autoerasing_sqlitedb(self, h_database):
        """
        check sqlite database for the oldest entries and delete them if time_limit is reached.
        """
        if int(time.time()) >= int(self.__autoerasechecktime):
            time_limit = int(time.time()) - int(ht3_cworker._gdata.Sqlite_autoerase_seconds())
            # get oldest UTC in database
            firstentry_UTC = self.__GetOldestEntry(h_database)
            if firstentry_UTC == None:
                firstentry_UTC = int(time.time())

            debugstr = "autoerasing check; UTCs current:{0}; oldest in db:{1}; limit:{2}".format(int(time.time()), firstentry_UTC, time_limit)
            self._logging.info(debugstr)

            if firstentry_UTC < time_limit:
                try:
                    debugstr = "sqlite-db autoerasing started;  time:{0}".format(int(time.time()))
                    self._logging.info(debugstr)
                    # erase old datacontend in sqlite-db
                    for systempartname in ht3_cworker._gdata.syspartnames():
                        h_database.delete(systempartname, "UTC", str(time_limit), "<")
                        debugstr = "table-content:<{0}> deleted where UTC is less then:<{1}>".format(systempartname, time_limit)
                        self._logging.info(debugstr)
                    # cleanup db
                    h_database.vacuum()
                    debugstr = "sqlite-db autoerasing finished; time:{0}".format(int(time.time()))
                    self._logging.info(debugstr)
                except (sqlite3.OperationalError, ValueError) as e:
                    errorstr = "ht3_cworker.__Autoerasing_sqlitedb();Error; {0}".format(e)
                    self._logging.critical(errorstr)

            # setup next check-time
            self.__autoerasechecktime = int(time.time()) + 120

    def __GetOldestEntry(self, h_database):
        """
           try to find the first timestamp-entry in column 'UTC' and table
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
            errorstr = "ht3_cworker.__GetOldestEntry();Error; {0}".format(e)
            self._logging.critical(errorstr)
            rtnvalue = None
        return rtnvalue

    def __Autocreate_draw(self, path_2_db, path_2_draw, hc_count=1, start_time=None, stoptime=None):
        """
            automatic calling the rrdtool-draw script if rrdtool-db is enabled.
        """
        debugstr = "Autocreate draw();\n path2db  :{0};\n path2draw:{1};\n hc_count:{2}".format(path_2_db, path_2_draw, hc_count)
        self._logging.debug(debugstr)
        AbsPathandFilename = os.path.abspath(os.path.normcase('./etc/rrdtool_draw.pl'))
        index2db = path_2_db.find('HT3')
        Abspath2_db = os.path.abspath(os.path.normcase(path_2_db[:index2db]))

        index2draw = path_2_draw.find('HT3')
        Abspath_2_draw = os.path.abspath(os.path.normcase(path_2_draw[:index2draw]))

        strsystemcmd = AbsPathandFilename + ' ' + Abspath2_db + ' ' + Abspath_2_draw + ' ' + str(hc_count)
        self._logging.debug(strsystemcmd)
        try:
            #execute perl-script for drawing 'rrdtool' dbinfos
            error = os.system(strsystemcmd)
            if error:
                errorstr = "ht3_cworker.__Autocreate_draw();Error:{0}; cmd:{1}".format(error, strsystemcmd)
                self._logging.critical(errorstr)
        except:
            errorstr = "ht3_cworker.__Autocreate_draw();Error; os.system-call"
            self._logging.critical(errorstr)

    def __DispatchThread(self, parameter):
        """
            Dispatch-Thread: open databases if required and storing the results in db.
             automatic draw for rrdtool-draw ist called every 60 sec. if db is enabled.
             automatic erase of old data is done in sqlite-db if it is enabled.
        """
        debug = 0
        rrdtooldb = None
        nextTimeStep = time.time()
        sqlite_autoerase = False

        # get db-instance
        database = db_sqlite.cdb_sqlite(self.__cfgfilename, logger=self._logging)
        database.connect()

        # set flag for erasing sqlite-db if enabled
        if database.is_sql_db_enabled() and ht3_cworker._gdata.Sqlite_autoerase_seconds() > 0:
            sqlite_autoerase = True

        if ht3_cworker._gdata.is_db_rrdtool_enabled():
            try:
                rrdtooldb = db_rrdtool.cdb_rrdtool(self.__cfgfilename, logger=self._logging)
                rrdtooldb.createdb_rrdtool()
                # setup the first 'nextTimeStep' to 3 times stepseconds waiting for valid data
                nextTimeStep = time.time() + int(ht3_cworker._gdata.db_rrdtool_stepseconds()) * 3
            except:
                errorstr = "ht3_cworker();Error; could not init rrdtool-db"
                self._logging.critical(errorstr)
                self._logging.info("ht3_cworker.run(); End   ----------------------")
                quit()

        rawdata = ht_discode.cht_discode(self.__port, ht3_cworker._gdata, debug, self.__filehandle, logger=self._logging)

        while self.__threadrun:
            # get the decoded values and store them to db if enabled.
            (nickname, value) = rawdata.discoder()
            if value != None:
                if database.is_sql_db_enabled():
                    database.insert(str(ht3_cworker._gdata.getlongname(nickname)), value)
                    database.commit()

                if ht3_cworker._gdata.is_db_rrdtool_enabled() and rrdtooldb != None:
                    # write data to rrdtool-db after 'stepseconds' seconds
                    if time.time() > nextTimeStep:
                        for syspartshortname in rrdtooldb.syspartnames():
                            if syspartshortname.upper() == 'DT':
                                continue
                            syspartname = rrdtooldb.syspartnames()[syspartshortname]
                            itemvalue_array = ht3_cworker._gdata.getall_sorted_items_with_values(syspartshortname)
                            error = rrdtooldb.update(syspartname, itemvalue_array, time.time())
                            if error:
                                self._logging.critical("rrdtooldb.update();Error;syspartname:{0}".format(syspartname))

                        if ht3_cworker._gdata.IsAutocreate_draw():
                            (db_path, dbfilename) = ht3_cworker._gdata.db_rrdtool_filepathname()
                            (html_path, filename) = ht3_cworker._gdata.db_rrdtool_filepathname('./etc/html/index.html')
                            self.__Autocreate_draw(db_path, html_path, ht3_cworker._gdata.heatercircuits_amount())

                        nextTimeStep = time.time() + int(ht3_cworker._gdata.db_rrdtool_stepseconds()) - 5

                if sqlite_autoerase:
                    self.__Autoerasing_sqlitedb(database)

        #close db at the end of thread
        database.close()

#--- class ht3_cworker end ---#

### Runs only for test ###########
if __name__ == "__main__":
    configurationfilename = './../etc/config/4test/HT3_4dispatcher_test.xml'
      #### reconfiguration has to be done in configuration-file ####
    HT3_Worker = ht3_cworker(configurationfilename)
    HT3_Worker.run()
