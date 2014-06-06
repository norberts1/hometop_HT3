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
#################################################################

import serial
import ht3_decode, data, db_sqlite
import db_info

class cht3_dispatch(object):
    def __init__(self, port, commondata, database, debug=0, filehandle=None):
        try:
            #check at first the parameters
            if filehandle==None:
                if not isinstance(port, serial.serialposix.Serial): raise TypeError("port")
            if not isinstance(commondata, data.cdata)  : raise TypeError("commondata")
            if not isinstance(database, db_sqlite.cdb_sqlite): raise TypeError("database")
        except (TypeError) as e:
            print('cht3_dispatch();Error;Parameter:<{0}> has wrong type'.format(e.args[0]))
            raise e

        self.port=port
        self.filehandle=filehandle
        self.data=commondata
        self.decode=ht3_decode.cht3_decode(self.data)
        self.database=database
        self.buffer=[0 for x in range(100)]
        self.debug=debug

        try:
            self.__rrdtool_info=db_info.crrdtool_info(database)
        except (OSError, EnvironmentError, TypeError, NameError) as e:
            print('cht3_dispatch();Error;{0}; rrdtool_info init failed'.format(e.args[0]))
            self.__rrdtool_info=None
            raise e

    def __read(self):
        if self.filehandle==None:
            return ord(self.port.read())
        else:
            rtn=self.filehandle.read(1)
            return ord(rtn) if len(rtn) > 0 else ord('0')
            

    ## check Msg-header and call decode-functions
    def dispatcher(self):
        length=0
        value=[]
        nickname=""
        try:
            firstbyte=self.__read()
            if firstbyte == 0x88:
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                if self.buffer[1] == 0:
                    ## Telegram: Heizgeraet Msg1(88001800) ##
                    if (self.buffer[2] == 0x18 and self.buffer[3] == 0):
                        nickname="HG"
                        length=31
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        # check for heater-type and modify length if required
                        #   Heatertype := KUB-like
                        if (self.buffer[15]==0x7d and self.buffer[16]==0x00):
                            for x in range (length, length+2):
                                self.buffer[x] = self.__read()
                            length=33
                        value=self.decode.HeizgeraetMsg(self.buffer, length)
                        if not value == None:
                            if self.debug:
                                print("'{0}':{1}\n".format(nickname, value))
                            if self.database.is_sql_db_enabled():
                                self.database.insert(str(self.data.getlongname(nickname)), value)
                                self.database.commit()
                            
                    ## Telegram: Heizgeraet Msg2 (88001900) ##
                    elif (self.buffer[2] == 0x19 and self.buffer[3] == 0):
                        nickname="HG"
                        length=33
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        value=self.decode.HeizgeraetMsg2(self.buffer, length)
                        if not value == None:
                            if self.debug:
                                print("'{0}':{1}\n".format(nickname, value))
                            if self.database.is_sql_db_enabled():
                                self.database.insert(str(self.data.getlongname(nickname)), value)
                                self.database.commit()
                            
                    ## Telegram: Warmwasser (88003400) ##
                    elif (self.buffer[2] == 0x34 and self.buffer[3] == 0):
                        nickname="WW"
                        length=23
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        value=self.decode.WarmwasserMsg(self.buffer, length)
                        if not value == None:
                            if self.debug:
                                print("'{0}':{1}\n".format(nickname, value))
                            if self.database.is_sql_db_enabled():
                                self.database.insert(str(self.data.getlongname(nickname)), value)
                                self.database.commit()
                            
                    ## Telegram: Request    (88000700) ##
                    elif (self.buffer[2] == 0x07 and self.buffer[3] == 0):
                        nickname=""
                        length=21
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        self.decode.RequestMsg(self.buffer, length)
                        # nothing to do for database

            ## Telegram: HK / Datum ##
            if firstbyte == 0x90:
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                if self.buffer[1] == 0:
                    ## Telegram: Heizkreis Msg (9000FF00) ##
                    if (self.buffer[2] == 0xff and self.buffer[3] == 0):
                        nickname="HK1"
                        length=17
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        value   =self.decode.HeizkreisMsg_FW100_200Msg(self.buffer, length)
                        nickname=self.decode.CurrentHK_Nickname()
                        if not value == None:
                            if self.debug:
                                print("'{0}':{1}\n".format(nickname, value))
                            if self.database.is_sql_db_enabled():
                                self.database.insert(str(self.data.getlongname(nickname)), value)
                                self.database.commit()
                            
                    ## Telegram: Datum / Uhrzeit (90000600) ##
                    elif (self.buffer[2] == 6 and self.buffer[3] == 0):
                        nickname="DT"
                        length=14
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        value=self.decode.DatumUhrzeitMsg(self.buffer, length)
                        if not value == None:
                            if self.debug:
                                print("'{0}':{1}\n".format(nickname, value))
                            if self.database.is_sql_db_enabled():
                                self.database.insert(str(self.data.getlongname(nickname)), value)
                                self.database.commit()

            ## Telegram: Heizkreis Msg (9x00FF00 und 9x10FF00 wobei: x <- 8 bis F) ##
            ##  Fernbedienungen FB1xy
            elif firstbyte >= 0x98 and firstbyte <= 0x9f:
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                if (self.buffer[1] == 0 and self.buffer[2] == 0xff and self.buffer[3] == 0):
                    nickname="HK1"
                    length=17
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.HeizkreisMsg_FW100_200Msg(self.buffer, length)
                    nickname=self.decode.CurrentHK_Nickname()
                    if not value == None:
                        if self.debug:
                            print("'{0}':{1}\n".format(nickname, value))
                        if self.database.is_sql_db_enabled():
                            self.database.insert(str(self.data.getlongname(nickname)), value)
                            self.database.commit()

                elif (self.buffer[1] == 0x10 and self.buffer[2] == 0xff and self.buffer[3] == 0):
                    nickname="HK1"
                    length=12
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value=self.decode.HeizkreisMsg_FB1xyMsg(self.buffer, length)
                
            ## Telegram: ISM Solarinfo (B000FF00) ##
            elif firstbyte == 0xb0:
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                if (self.buffer[1] == 0 and self.buffer[2] == 0xff and self.buffer[3] == 0):
                    nickname="SO"
                    length=21 # <--- default length for solar-msgtype:=3
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                        
                    # check for solar-msgtype:=4 -> 24 Byte length
                    #   +-> additional read required
                    if self.buffer[5]==4:
                        for x in range (length, length+3):
                            self.buffer[x] = self.__read()
                        length=24
                    value=self.decode.SolarMsg(self.buffer, length)
                    if not value == None:
                        if self.debug:
                            print("'{0}':{1}\n".format(nickname, value))
                        if self.database.is_sql_db_enabled():
                            self.database.insert(str(self.data.getlongname(nickname)), value)
                            self.database.commit()

            ## Telegram: IPM Lastschaltmodul (Ax00...) wobei x := (0...7)##
            elif (firstbyte>=0xa0 and firstbyte<=0xa7):
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                    
                ## Telegram: IPM Lastschaltmodul (Ax00FF00)
                if (self.buffer[1] == 0 and self.buffer[2] == 0xff and self.buffer[3] == 0):
                    length=14
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value=self.decode.IPM_LastschaltmodulMsg(self.buffer, length, firstbyte)
                            
                ## Telegram: IPM Lastschaltmodul (Ax003400) (WW-Mode) 
                elif (self.buffer[1] == 0 and self.buffer[2] == 0x34 and self.buffer[3] == 0):
                    nickname="WW"
                    length=15
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value=self.decode.IPM_LastschaltmodulWWModeMsg(self.buffer, length)
                    if not value == None:
                        if self.debug:
                            print("'{0}':{1}\n".format(nickname, value))
                        if self.database.is_sql_db_enabled():
                            self.database.insert(str(self.data.getlongname(nickname)), value)
                            self.database.commit()
                            
            else:                
                # do db_info-tests if enabled
                if  self.__rrdtool_info.isrrdtool_info_active():
                    self.__rrdtool_info.rrdtool_update()
            
        except (LookupError, IndexError, KeyError, TypeError, IOError, UnboundLocalError) as e:
            print('cht3_dispatch.dispatcher();Error;<{0}>'.format(e.args[0]))
            
################################################
if __name__ == "__main__":
    import serial, sys, os
    import data, db_sqlite

##################### configure as required ####
    serialdevice="/dev/ttyUSB0"
#    serialdevice="/dev/ttyUSB1"
###########################
    configurationfilename='./../etc/config/4test/HT3_4dispatcher_test.xml'


    print("----- do some real checks -----")
    print(" used device       :<{0}>".format(serialdevice))
    print(" used configuration:<{0}>".format(configurationfilename))
    print()    
    print("For this test it is required to have:")
    print(" 1. Hardware connected to the above serial-device.")
    print("    If not, change the name in this file and start again.")
    print(" 2. Hardware connected to the Heater HT3-bus")
    print("As result it is:")
    try:
        port = serial.Serial(serialdevice, 9600 )
    except:
        print()
        print("couldn't open requested device: <{0}>".format(serialdevice))
        print()
        sys.exit(1)
        
    db=db_sqlite.cdb_sqlite(configurationfilename)
    if db.is_sql_db_enabled():
        print("--> Database created if not available")
        print("-- create database")
        db.connect()
        db.createdb_sqlite()
        DB_path_and_name=db.db_sqlite_filename()
        if os.access(DB_path_and_name,os.W_OK and os.R_OK):
            print("Database:'{0}' created and access possible".format(DB_path_and_name))
        else:
            print("Database:'{0}' not available".format(DB_path_and_name))
            quit()
        print("--> Intercepted data written to sqlite database")
    else:
        print("--> Database disabled in config-file, no creation done")
    
    print("--> Intercepted data written to stdout")
    
    testdata=data.cdata()
    testdata.read_db_config(configurationfilename)
    
    debug=1
    HT3=cht3_dispatch(port, testdata, db, debug)
    while True:
        HT3.dispatcher()

    try:
        # must be never reached but for completeness
        if db.is_sql_db_enabled():
            db.close()
    except:
        print("!!! Error in ht3_dispatcher occured !!!")
