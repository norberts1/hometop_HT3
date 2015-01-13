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
#################################################################

import sys, serial, _thread, sqlite3
import data, ht3_dispatch, gui_worker, db_sqlite

class ht3_cworker(object):
    # setup static data-struct
    __gdata=data.cdata()
    def __init__(self, configurationfilename, hexdump_window=True, gui_active=True):
        try:
            if not (isinstance(hexdump_window,int) or isinstance(hexdump_window,bool)):
                raise TypeError("hexdump_window")
            self.__cfgfilename =str(configurationfilename)
            self.__hexdump_window=bool(hexdump_window)
            self.__gui_active    =bool(gui_active)
            
            # read configurationfile and setup default data
            try:
                ht3_cworker.__gdata.read_db_config(self.__cfgfilename)
            except:
                print('ht3_cworker();Error;could not get configuration-values')
                raise e

            self.__serialdevice  =str(ht3_cworker.__gdata.AsyncSerialdevice())
            self.__baudrate      =ht3_cworker.__gdata.AsyncBaudrate()
            self.__inputfile     =ht3_cworker.__gdata.inputtestfilepath()
            if len(self.__inputfile)<5: self.__inputfile=""
            
            self.__port=None
            self.__filehandle=None
            self.__threadrun=True

        except (TypeError) as e:
            print('ht3_cworker();Error;Parameter:<{0}> has wrong type'.format(e.args[0]))
            raise e

        
    def __del__(self):
        if self.__port != None:
            self.__port.close()

    def run(self):
        if ((self.__inputfile!=None) and (len(self.__inputfile)>0)):
            #open input-file in readonly-binary mode for analysing binary HT3-data
            try:
                self.__filehandle=open(self.__inputfile,"rb")
            except:
                print('ht3_cworker();Error; could not open file:{0}'.format(self.__inputfile))
                quit()
        else:
            #open serial port for reading HT3-data
            try:
                self.__port = serial.Serial(self.__serialdevice, self.__baudrate )
                self.__port.setInterCharTimeout(0.1) #VTIME; set to 0.1*1sec
            except:
                print("ht3_cworker();Error;couldn't open requested device:{0}".format(self.__serialdevice))
                quit()

        try:
            db=db_sqlite.cdb_sqlite(self.__cfgfilename)
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
                    print("Wait a bit, database: sqlite will be created");
                else:
                    print("database already available")
                    
                db.connect()
                db.createdb_sqlite()
                db.close()
                
            # start thread for dispatching
            _thread.start_new_thread(self.__DispatchThread, (0,))

            if self.__gui_active:
                # start GUI endless until 'Ende' is pressed
                GUI=gui_worker.gui_cworker(ht3_cworker.__gdata, self.__hexdump_window)
                self.__threadrun=GUI.run()

        except (sqlite3.OperationalError, ValueError) as e:
            print("ht3_cworker();Error; {0}".format(e))
            quit()
            
    def __DispatchThread(self, parameter):
            debug=0
            # get db-instance
            database=db_sqlite.cdb_sqlite(self.__cfgfilename)
            database.connect()
            message=ht3_dispatch.cht3_dispatch(self.__port, ht3_cworker.__gdata, database, debug, self.__filehandle)
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

    

