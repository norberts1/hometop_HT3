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
# Ver:0.1.5.1/ Datum 12.06.2014
# Ver:0.1.6  / Datum 10.01.2015 'main testconfiguration changed'
#                               'updated telegramm-handling WW'
#                               'modem-telegramms added (draft)'
# Ver:0.1.7.1/ Datum 04.03.2015 'socket interface added'
#                               logging from ht_utils added
#################################################################

import serial
import ht3_decode, data, db_sqlite
import db_info, ht_utils
import ht_proxy_if

class cht3_dispatch(ht_utils.cht_utils, ht_utils.clog):
    def __init__(self, port, commondata, database, debug=0, filehandle=None, logger=None):
        ht_utils.cht_utils.__init__(self)
        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging=ht_utils.clog.create_logfile(self, logfilepath="./cht3_dispatch.log", loggertag="cht3_dispatch")
            else:
                self._logging=logger
        except:
            errorstr="""cht3_dispatch();Error;could not create logfile"""
            print(errorstr)
            raise EnvironmentError(errorstr)
        
        try:
            #check at first the parameters
            if filehandle==None:
                if not (isinstance(port, serial.serialposix.Serial) or isinstance(port, ht_proxy_if.cht_socket_client)):
                    errorstr="cht3_dispatch();TypeError;port"
                    self._logging.critical(errorstr)
                    raise TypeError(errorstr)
            
            if not isinstance(commondata, data.cdata)  :
                errorstr="cht3_dispatch();TypeError;commondata"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            if not isinstance(database, db_sqlite.cdb_sqlite):
                errorstr="cht3_dispatch();TypeError;database"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
        except (TypeError) as e:
            errorstr='cht3_dispatch();Error;Parameter:<{0}> has wrong type'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

        self.port=port
        self.filehandle=filehandle
        self.data=commondata
        self.decode=ht3_decode.cht3_decode(self.data, logger=self._logging)
        self.database=database
        self.buffer=[0 for x in range(100)]
        self.debug=debug

        try:
            self.__rrdtool_info=db_info.crrdtool_info(database, self._logging)
        except (OSError, EnvironmentError, TypeError, NameError) as e:
            errorstr='cht3_dispatch();Error;{0}; rrdtool_info init failed'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
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
                        if value==None:
                            # read additonal 2bytes from port (new message-length 25 Bytes) and check again
                            #  see description on: https://www.mikrocontroller.net/topic/317004#3684428
                            length=25
                            for x in range (23, length):
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

            ## Telegram: Modem ##
            ### still under development ###
            #
            if (firstbyte == 0x8d or firstbyte == 0x8a):
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                if (self.buffer[1]==0x10 and self.buffer[2]==0xff and self.buffer[3]==0x11):
                    nickname="MO1"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_1(self.buffer, length)

                elif (self.buffer[1]==0x10 and self.buffer[2]==0xff and self.buffer[3]==0x07):
                    nickname="MO2"
                    length=9
                    # check first with 9 bytes (Netcom100), if byte[7]=0 take 11 Bytes
                    # for MB-Lan
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    # take the rest for MB-lan
                    if self.buffer[7] == 0:
                        length=11
                        for x in range (9, length):
                            self.buffer[x] = self.__read()
                    value   =self.decode.Modem_2(self.buffer, length)

                elif (self.buffer[1]==0x18 and self.buffer[2]==0xff and self.buffer[3]==0x11):
                    nickname="MO3"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_3(self.buffer, length)
                        
                    
                elif (self.buffer[1]==0x18 and self.buffer[2]==0xff and self.buffer[3]==0x07):
                    nickname="MO4"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_4(self.buffer, length)
                        
                    
                elif (self.buffer[1]==0x90 and self.buffer[2]==0xff and self.buffer[3]==0x11):
                    nickname="MO5"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_5(self.buffer, length)
                        
                elif (self.buffer[1]==0x90 and self.buffer[2]==0xff and self.buffer[3]==0x07):
                    nickname="MO6"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_6(self.buffer, length)
                    
                elif (self.buffer[1]==0x10 and self.buffer[2]==0xff and self.buffer[3]==0x0e):
                    nickname="MO7"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_7(self.buffer, length)

                elif (self.buffer[1]==0x18 and self.buffer[2]==0xff and self.buffer[3]==0x0e):
                    nickname="MO8"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_8(self.buffer, length)

                elif (self.buffer[1]==0x90 and self.buffer[2]==0xff and self.buffer[3]==0x0e):
                    nickname="MO9"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_9(self.buffer, length)

                #MB-lan messages
                elif (self.buffer[1]==0x90 and self.buffer[2]==0xff and self.buffer[3]==0x06):
                    nickname="MB1"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_MB_1(self.buffer, length)
                    
                elif (self.buffer[1]==0x90 and self.buffer[2]==0xff and self.buffer[3]==0x0a):
                    nickname="MB2"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_MB_2(self.buffer, length)

                 #### Spar-mode ???                    
                elif (self.buffer[1]==0x10 and self.buffer[2]==0xff and self.buffer[3]==0x06):
                    nickname="MB3"
                    length=9
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_MB_3(self.buffer, length)
                        
                 #### Frost-mode ???                    
                elif (self.buffer[1]==0x10 and self.buffer[2]==0xff and self.buffer[3]==0x00):
                    nickname="MB4"
                    length=8
                    for x in range (4, length):
                        self.buffer[x] = self.__read()
                    value   =self.decode.Modem_MB_4(self.buffer, length)
                        
                       
                    
            ## Telegram: HK / Datum ##
            if firstbyte == 0x90:
                self.buffer[0] = firstbyte
                for x in range (1,4):
                    self.buffer[x] = self.__read()
                if self.buffer[1] == 0:
                    ## Telegram: Heizkreis Msg (9000FF00) ##
                    if (self.buffer[2] == 0xff and self.buffer[3] == 0):
                        nickname="HK1"
                        #1. Message with 9 Byte length
                        #  see: https://www.mikrocontroller.net/topic/317004#3693015
                        length=9
                        for x in range (4, length):
                            self.buffer[x] = self.__read()
                        if (self.crc_testen(self.buffer, length)) :
                            value   =self.decode.HeizkreisMsg_FW100_200Msg_9byte(self.buffer, length)
                        else:
                            #2. load rest of byte until length=11
                            # see: https://www.mikrocontroller.net/topic/317004#3687762
                            length=11
                            for x in range (9, length):
                                self.buffer[x] = self.__read()
                             #check for 11 byte message
                            if (self.crc_testen(self.buffer, length) and self.buffer[5]==0xd3) :
                                value   =self.decode.HeizkreisMsg_FW100_200_11byte(self.buffer, length)
                            else:
                                #load rest of 6 bytes for length=17
                                length=17
                                for x in range (11, length):
                                    self.buffer[x] = self.__read()
                                value   =self.decode.HeizkreisMsg_FW100_200Msg(self.buffer, length)
                                
                        if not value == None:
                            nickname=self.decode.CurrentHK_Nickname()
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
            errorstr='cht3_dispatch.dispatcher();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)

            
################################################
if __name__ == "__main__":
    import serial, sys, os
    import data, db_sqlite
    
    configurationfilename='./../etc/config/4test/HT3_4dispatcher_test.xml'
    testdata=data.cdata()
    testdata.read_db_config(configurationfilename)
    #### reconfiguration has to be done in configuration-file ####
    serialdevice=testdata.AsyncSerialdevice()
    baudrate=testdata.AsyncBaudrate()
    
    print("----- do some real checks -----")
    print(" used device       :<{0}>".format(serialdevice))
    print(" used configuration:<{0}>".format(configurationfilename))
    print()    
    print("For this test it is required to have:")
    print(" 1. Hardware connected to the above serial-device.")
    print("    If not, change the name in config-file and start again.")
    print(" 2. Hardware connected to the Heater HT-bus")
    print("As result it is:")
    try:
        port = serial.Serial(serialdevice, baudrate )
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
