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
#################################################################

import sys, os, serial, _thread, sqlite3
import data, ht3_dispatch, gui_worker, db_sqlite
from ht_proxy_if import cht_socket_client as ht_proxy_client
import ht_utils, logging



class ht3_cworker(object):
    # setup static data-struct
    __gdata=data.cdata()
    def __init__(self, configurationfilename, hexdump_window=True, gui_active=True, logfilename_in=None, loglevel_in=None):
        self._logging    =None
        self._loglevel   = logging.INFO
        self.__port      =None
        self.__filehandle=None
        self.__threadrun =True
        try:
            if not (isinstance(hexdump_window,int) or isinstance(hexdump_window,bool)):
                errorstr="ht3_cworker();TypeError;hexdump_window"
                print(errorstr)
                raise TypeError(errorstr)
            self.__cfgfilename =str(configurationfilename)
            self.__hexdump_window=bool(hexdump_window)
            self.__gui_active    =bool(gui_active)
            self.__gui_titel_input="ASYNC "   #default value
            
        except (EnvironmentError, TypeError) as e:
            errorstr='ht3_cworker();Error;Parameter:<{0}> has wrong type'.format(e.args[0])
            print(errorstr)
            raise e

        # read configurationfile and setup default data
        try:
            ht3_cworker.__gdata.read_db_config(self.__cfgfilename)
        except:
            errorstr='ht3_cworker();Error;could not get configuration-values'
            print(errorstr)
            raise

        try:
            if logfilename_in != None:
                ht3_cworker.__gdata.logfilename(logfilename_in)
            if loglevel_in != None:
                loglevel    = ht3_cworker.__gdata.loglevel(loglevel_in)
                
            self._loglevel  = ht3_cworker.__gdata.loglevel()                    
            logfilepath     = ht3_cworker.__gdata.logfilepathname()
            abs_logfilepath =os.path.abspath(logfilepath)
            loggertag="ht3_cworker"
        except:
            errorstr='ht3_cworker();Error;could not get cfg-logvalues'
            print(errorstr)
            raise EnvironmentError(errorstr)
        
        try:
            self._logging=ht3_cworker.__gdata.create_logfile(abs_logfilepath, self._loglevel, loggertag)
        except(EnvironmentError, TypeError) as e:
            errorstr="ht3_cworker();Error; could not create logfile:{0};{1}".format(abs_logfilepath, e.args[0])
            print(errorstr)
            raise e
        
        self.__serialdevice  =str(ht3_cworker.__gdata.AsyncSerialdevice())
        self.__baudrate      =ht3_cworker.__gdata.AsyncBaudrate()
        self.__inputfile     =ht3_cworker.__gdata.inputtestfilepath()
        if len(self.__inputfile)<5: self.__inputfile=""
        
    def __del__(self):
        if self.__port != None:
            self.__port.close()
        self._logging.info("ht3_cworker.run(); End   ----------------------")

    def run(self):
        self._logging.info("ht3_cworker.run(); Start ----------------------")
        self._logging.info("ht3_cworker.run();  Loglevel      :{0}".format(logging.getLevelName(self._loglevel)))
        
        if ((self.__inputfile!=None) and (len(self.__inputfile)>0)):
            #open input-file in readonly-binary mode for analysing binary HT3-data
            try:
                self.__filehandle=open(self.__inputfile,"rb")
                self.__gui_titel_input="FILE"
            except:
                errorstr='ht3_cworker();Error; could not open file:{0}'.format(self.__inputfile)
                self._logging.critical(errorstr)
                quit()
        else:
            # open socket for client and connect to server,
            #   socket-object is written to 'self.__port'
            if(ht3_cworker.__gdata.IsDataIf_socket()):
                try:
                    client_cfg_file =os.path.normcase(os.path.abspath(ht3_cworker.__gdata.client_cfg_file()))
                    if not os.path.exists(client_cfg_file):
                        errorstr="ht3_cworker();Error;couldn't find file:{0}".format(client_cfg_file)
                        self._logging.critical(errorstr)
                        raise EnvironmentError(errorstr)
                except:
                    errorstr="ht3_cworker();Error;couldn't find file:{0}".format(client_cfg_file)
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)
                
                try:
                    self.__port = ht_proxy_client(client_cfg_file, loglevel=self._loglevel)
                    self.__gui_titel_input="SOCKET"
                except:
                    errorstr="ht3_cworker();Error;couldn't open requested socket; cfg-file:{0}".format(client_cfg_file)
                    self._logging.critical(errorstr)
                    raise
            else:
                #open serial port for reading HT3-data
                try:
                    self.__port = serial.Serial(self.__serialdevice, self.__baudrate )
                    self.__port.setInterCharTimeout(0.1) #VTIME; set to 0.1*1sec
                    self.__gui_titel_input="ASYNC"
                except:
                    errorstr="ht3_cworker();Error;couldn't open requested device:{0}".format(self.__serialdevice)
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)

        self._logging.info("ht3_cworker.run();  Datainput-Mode:{0}".format(self.__gui_titel_input))
        if ht3_cworker.__gdata.IsDataIf_async():
            self._logging.info("ht3_cworker.run();   Baudrate     :{0}".format(self.__baudrate))
            self._logging.info("ht3_cworker.run();   Configuration:{0}".format(ht3_cworker.__gdata.AsyncConfig()))
        
        try:
            db=db_sqlite.cdb_sqlite(self.__cfgfilename, logger=self._logging)
            # create database-sqlite if required
            if db.is_sql_db_enabled():
                if not db.is_sqlite_db_available():
    ###                if self.__gui_active:
    ###                    # disply information, creating database if not available
    ###                    import tkinter.messagebox
    ###                    response=tkinter.messagebox.askyesno("SQlite-db not available","Creating ?:yes/no")
    ###                    if response:
    ###                        print("creating the database")
    ###                    else:
    ###                        print("terminating, no further run")
    ###                        quit()
    ###                else:
                    infostr="ht3_cworker();Wait a bit, database: sqlite will be created"
                else:
                    infostr="ht3_cworker();sqlite-database already available"
                    
                print(infostr)
                self._logging.info(infostr)
                    
                db.connect()
                db.createdb_sqlite()
                db.close()
                
            # start thread for dispatching
            _thread.start_new_thread(self.__DispatchThread, (0,))

            if self.__gui_active:
                # start GUI endless until 'Ende' is pressed
                GUI=gui_worker.gui_cworker(ht3_cworker.__gdata, self.__hexdump_window, self.__gui_titel_input, logger=self._logging)
                self.__threadrun=GUI.run()

        except (sqlite3.OperationalError, ValueError) as e:
            errorstr="ht3_cworker();Error; {0}".format(e)
            self._logging.critical(errorstr)
            self._logging.info("ht3_cworker.run(); End   ----------------------")
            quit()
            
    def __DispatchThread(self, parameter):
            debug=0
            # get db-instance
            database=db_sqlite.cdb_sqlite(self.__cfgfilename, logger=self._logging)
            database.connect()
            message=ht3_dispatch.cht3_dispatch(self.__port, ht3_cworker.__gdata, database, debug, self.__filehandle, logger=self._logging)
            while self.__threadrun:
                message.dispatcher()
            #close db at the end of thread
            database.close()
        

#--- class ht3_cworker end ---#

### Runs only for test ###########
if __name__ == "__main__":
    configurationfilename='./../etc/config/4test/HT3_4dispatcher_test.xml'
      #### reconfiguration has to be done in configuration-file ####
    HT3_Worker=ht3_cworker(configurationfilename)
    HT3_Worker.run()

    

