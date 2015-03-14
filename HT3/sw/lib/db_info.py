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
# Ver:0.1.7.1/ Datum 04.03.2015 testvalues 'warmwasser' and 'heizkreis1'
#                               updated
#                               logging from ht_utils added
#################################################################
#
""" Class 'crrdtool_info' for creating and updating rrdtool-database with sql-database informations

crrdtool_info.__init__  -- constructor of class 'cdb_rrdtool'. this will create rrdtool-db if required
                             mandatory: parameter 'sql_db_obj' as handle to sql-database object
isrrdtool_info_active   -- returns True/False if rrdtool-database is enabled/disabled in config.
                             mandatory: none
rrdtool_update          -- return of used rrdtool-db  filename.
                             mandatory: none
                             optional : timeinterval  (default is value from configuration)
                             
"""

import time, sqlite3
import db_rrdtool, db_sqlite
import ht_utils, logging


class crrdtool_info(db_rrdtool.cdb_rrdtool, ht_utils.clog):
    # static values for sqlite-database
    __rrdtooltable     ='rrdtool_infos'
    __updatecolumnname ='rrdtool_timestamp'
    __commentcolumnname='comment'
    __errorcolumnname  ='errors'
    
    def __init__(self, sql_db_obj, logger=None):

        try:
            # init/setup logging-file
            if logger == None:
                ht_utils.clog.__init__(self)
                self._logging=ht_utils.clog.create_logfile(self, logfilepath="./crrdtool_info.log", loggertag="crrdtool_info")
            else:
                self._logging=logger
                
            if not isinstance(sql_db_obj, db_sqlite.cdb_sqlite):
                errorstr="crrdtool_info.__init__();Error; Parameter 'sql_db_obj' has wrong type"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            
            self.__sql_db         = sql_db_obj
            self.__cfgfilename    = sql_db_obj.configurationfilename()
            db_rrdtool.cdb_rrdtool.__init__(self, self.__cfgfilename, logger=self._logging)
            self.__rrdtool_active = bool(db_rrdtool.cdb_rrdtool.is_rrdtool_db_enabled(self))
            self.__step_seconds   = int(db_rrdtool.cdb_rrdtool.db_rrdtool_stepseconds(self))
            
            self.__UTCcurrentvalue=0
            self.__UTCnextvalue   =0
            self.__runstate       =0     # statemachine-startvalue
            self.__columnnames    ={}

            if self.__rrdtool_active:
                db_rrdtool.cdb_rrdtool.createdb_rrdtool(self)
                self.__prepare()

        except (OSError, EnvironmentError, TypeError, NameError) as e:
            errorstr="""crrdtool_info();Error;<{0}>""".format(str(e.args))
            self._logging.critical(errorstr)
            raise e
            
    def __del__(self):
        pass

    def __prepare(self):
        self.__addtable()
        self.__setcolumnnames()
        self.__runstate=0

    def __addtable(self):
        if self.__rrdtool_active:
            try:
                if not self.__sql_db.is_sqlite_db_available():
                    errorstr="db_info.__addtable();Error;sqlite-db not available"
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)
                else:
                    # first of all (before table-creation) set pragma auto_vacuum
                    self.__sql_db.setpragma("auto_vacuum","= full")
                    # add tables and columns
                    self.__sql_db.createtable(crrdtool_info.__rrdtooltable)
                    self.__sql_db.addcolumn(crrdtool_info.__rrdtooltable,'Local_date_time','CURRENT_TIMESTAMP')
                    self.__sql_db.addcolumn(crrdtool_info.__rrdtooltable, crrdtool_info.__updatecolumnname  ,'CURRENT_TIMESTAMP')
                    self.__sql_db.addcolumn(crrdtool_info.__rrdtooltable, crrdtool_info.__commentcolumnname ,'TEXT')
                    self.__sql_db.addcolumn(crrdtool_info.__rrdtooltable, crrdtool_info.__errorcolumnname   ,'TEXT')
            except (sqlite3.OperationalError) as e:
                errorstr="""db_info.__addtable();Error;<{0}>;database<{1}>""".format(
                        e.args[0],
                        self.__sql_db.db_sqlite_filename())
                print(errorstr)
                raise e
                

    def __setcolumnnames(self):
        if self.__rrdtool_active:
            #get all informations ('column-names') from tables
            for syspartshortname in db_rrdtool.cdb_rrdtool.syspartnames(self):
                syspartname=db_rrdtool.cdb_rrdtool.syspartnames(self)[syspartshortname]
                infos=self.__sql_db.gettableinfo(syspartname)
                # fillup dictionary with: {syspartshortname:[column1, column2,...]}
                columns=[]
                for info in infos:
                    columns.append(info[1])
                self.__columnnames.update({syspartname:columns})

    def isrrdtool_info_active(self):
        return self.__rrdtool_active

    def rrdtool_update(self, timeinterval=None):
        # preset values
        selectrtn    =[]
        rrdtooltimeinterval=60
        if timeinterval == None:
            # take it from configurationfile 'step_seconds'
            rrdtooltimeinterval=self.__step_seconds
        else:
            rrdtooltimeinterval=int(timeinterval)
            

        if self.__rrdtool_active:
            try:
                ###############################################################################################
                ########## runstate  0  #######################################################################
                ###############################################################################################
                # check for update-entries in table: rrdtool_infos,
                #  if available use them
                #  if not search in logitem-sqlite-db for first UTC entry and use is
                #
                if self.__runstate==0:
                    if __name__ == "__main__":
                        # testausgabe
                        print("runstate 0;UTCcurrent:{0}".format(self.__UTCcurrentvalue))
                        
                    self.__UTCcurrentvalue=0
                    self.__UTCnextvalue   =0
                    selectrtn      =[]
                        
                    # example: SELECT rrdtool_timestamp FROM rrdtool_infos WHERE rrdtool_timestamp NOT NULL ORDER BY rrdtool_timestamp ASC
                    #  call-IF- definition -> selectwhere(tablename, columnname, searchvalue, exp='=', what='*'):
                    sqlsearchstring ="NOT NULL"
                    sqlorderbystring="ORDER BY {0} ASC".format(crrdtool_info.__updatecolumnname)
                    selectrtn=self.__sql_db.selectwhere(crrdtool_info.__rrdtooltable, \
                                                        crrdtool_info.__updatecolumnname,\
                                                        sqlorderbystring,\
                                                        sqlsearchstring,\
                                                        crrdtool_info.__updatecolumnname)

                    if list(selectrtn)==[]:
                        # No Values found in rrdtool_infos:'rrdtool_timestamp',
                        # so take first available entry in any table as current UTC-value
                        #
                        for syspartshortname in db_rrdtool.cdb_rrdtool.syspartnames(self):
                            syspartname=db_rrdtool.cdb_rrdtool.syspartnames(self)[syspartshortname]
                            # example: SELECT UTC FROM <tablename> WHERE UTC NOT NULL ORDER BY UTC ASC
                            sqlsearchstring ="NOT NULL"
                            sqlorderbystring="ORDER BY UTC ASC"
                            rtnvalue=self.__sql_db.selectwhere( syspartname, \
                                                                'UTC',\
                                                                sqlorderbystring,\
                                                                sqlsearchstring,\
                                                                'UTC')
                            if not rtnvalue==[]:
                                #set first startvalues
                                self.__UTCcurrentvalue=rtnvalue[0][0]+1
                                # setup new running-state
                                self.__runstate = 1
                                break
                        else:
                            # no entries found in logitemtables, stay in runstate=0
                            self.__UTCcurrentvalue=0
                    else:
                        # set early defaults
                        self.__UTCcurrentvalue=1001284281
                        
                        # try to find the last timestamp-entry in column 'rrdtool_timestamp'
                        # and use it for further searching
                        # excample:
                        #  SELECT rrdtool_timestamp FROM rrdtool_infos WHERE rrdtool_timestamp NOT NULL ORDER BY rrdtool_timestamp DESC
                        sqlsearchstring ="NOT NULL"
                        sqlorderbystring="ORDER BY {0} DESC".format(crrdtool_info.__updatecolumnname)
                        selectrtn=self.__sql_db.selectwhere(crrdtool_info.__rrdtooltable, \
                                                            crrdtool_info.__updatecolumnname,\
                                                            sqlorderbystring,\
                                                            sqlsearchstring,\
                                                            crrdtool_info.__updatecolumnname)
                                
                        if not selectrtn==[]:
                            for valuetmp in list(selectrtn):
                                # get and set first UTC-timestamp
                                self.__UTCcurrentvalue=valuetmp[0:1][0]+1
                                break
                            # setup new running-state
                            self.__runstate = 1
                        else:
                            # stay in runstate=0
                            self.__runstate = 0
                        
                ###############################################################################################
                ########## runstate  1  #######################################################################
                ###############################################################################################
                elif self.__runstate==1:
                    if __name__ == "__main__":
                        # testausgabe
                        print("runstate 1;UTCcurrent:{0}".format(self.__UTCcurrentvalue))
                        
                    # check all tables for available entries and send them to rrdtool_db only,
                    # if the timestamps fit into the narrow-intervall 'rrdtooltimeinterval'
                    self.__UTCnextvalue   =self.__UTCcurrentvalue+rrdtooltimeinterval
                    
                    for syspartshortname in db_rrdtool.cdb_rrdtool.syspartnames(self):
                        # systemtime_date values are not send to rrdtool-database
                        if syspartshortname.upper() == 'DT':
                            continue
                        syspartname=db_rrdtool.cdb_rrdtool.syspartnames(self)[syspartshortname]
                        # example:
                        #  SELECT * FROM warmwasser WHERE UTC>=1391290101 AND UTC<1391290161 ORDER BY UTC ASC
                        sqlsearchstring =">= {0} AND UTC <".format(self.__UTCcurrentvalue)
                        sqlorderbystring="{0} ORDER BY UTC ASC".format(self.__UTCnextvalue)
                        rtnvalue=self.__sql_db.selectwhere(syspartname, 'UTC',sqlorderbystring,sqlsearchstring)
                        if not rtnvalue==[]:
                            UTC_timestamp=0
                            for valuetmp in list(rtnvalue):
                                # UTC-timestamp as second value
                                UTC_timestamp=valuetmp[1:2][0]
                                
                                if UTC_timestamp>=self.__UTCcurrentvalue and UTC_timestamp<self.__UTCnextvalue: # values found in time
                                    UTC_uppervalue=self.__UTCnextvalue-1
                                    comment="{0}:{1}".format(syspartshortname, UTC_timestamp)
                                    # map columnnames to values for rrdtool
                                    valuearray=self.__mapcolumnnames2values(syspartname, self.__columnnames, valuetmp)
                                    # send information to rrdtool
                                    error = db_rrdtool.cdb_rrdtool.update(self, syspartname, valuearray, UTC_uppervalue)
                                    if error:
                                        #set error and comment (syspartname) in rrdtoolinfos_table
                                        strerror="Error:{0}".format(error)
                                        values=[UTC_uppervalue, comment, strerror]
                                        self.__sql_db.insert(crrdtool_info.__rrdtooltable, values, int(time.time()))
                                        self.__sql_db.commit()
                                    else:
                                        #set success and comment (syspartname) in rrdtoolinfos_table
                                        values=[UTC_uppervalue, comment, "None"]
                                        self.__sql_db.insert(crrdtool_info.__rrdtooltable, values, int(time.time()))
                                        self.__sql_db.commit()
                                    UTC_timestamp=0
                                    break  # end for valuetmp in ...
                        else:
                            continue
                    ## end for syspartshortname
                    # all sysparts scanned for this intervall, wait for new interval in runstate:=2
                    self.__runstate=2
                    
                ###############################################################################################
                ########## runstate  2  #######################################################################
                ###############################################################################################
                elif self.__runstate==2:
                    if __name__ == "__main__":
                        # testausgabe
                        print("runstate 2;UTCcurrent:{0}".format(self.__UTCcurrentvalue))
                        
                    # setup new timeinterval if possible
                    if (self.__UTCnextvalue+rrdtooltimeinterval) < int(time.time()):
                        self.__UTCcurrentvalue += rrdtooltimeinterval
                        # go back to runstate := 1
                        self.__runstate=1
                    else:
                        # do nothing
                        pass
                    
                ###############################################################################################
                ########## wrong state  #######################################################################
                ###############################################################################################
                else:
                    # wrong state, return to zero
                    self.__runstate=0

            except (sqlite3.OperationalError) as e:
                errorstr='crrdtool_info.__rrdtool_update();Error;<{0}>'.format(e.args[0])
                self._logging.critical(errorstr)
                self.__runstate = 0
                

    def __mapcolumnnames2values(self, syspartname, columnnames, values):
        # function maps columnnames with values as array of tuples like:
        #  [(columnname1, value1),(columnname2, value2), ....]
        #
        resultarray=[]
        # tmps without Local_date_time, UTC and hexdump - entries
        columntmp=columnnames[syspartname][2:-1]
        valuetmp =values[2:-1]
        x=0
        for columnname in columntmp:
            resultarray.append((columnname, valuetmp[x]))
            x+=1
        return resultarray
        
        
#--- class crrdtool_info end ---#

### Runs only for test ###########
if __name__ == "__main__":
    import db_sqlite
    configurationfilename='./../etc/config/4test/HT3_4rrdtool_db_test.xml'
    HT3_db=db_sqlite.cdb_sqlite(configurationfilename)
    dbfilename=HT3_db.db_sqlite_filename()
    print("main:Create HT3-database:{0} for testpurposes".format(dbfilename))
    HT3_db.connect()
    HT3_db.createdb_sqlite()
    
    if not HT3_db.is_sqlite_db_available(dbfilename):
        print("main:HT3-database not available")
        HT3_db.close()
        quit()
        
    print("main:  sqlite  database ok ?:{0}".format(HT3_db.is_sqlite_db_available(dbfilename)))
    print("main:Create datatable 'rrdtool_info' if enable-flag is set in configuration\n")
    db_info=crrdtool_info(HT3_db)
    if not db_info.isrrdtool_info_active():
        print("main:Datatable 'rrdtool_info' will not be created")
        print("main:   enable-flag is set to 'False' in configuration\n")
        HT3_db.close()
        print("main: test terminated")
    else:
        print("main:  rrdtool database ok ?:{0}".format(db_info.is_rrdtool_db_available()))
        print("main:  ------------------------")
        print("main:   - insert testvalues in db_sqlite ")
        time.sleep(3)
        print("main:   now insert the first value")
        tablename="warmwasser"
        values=[16.1,21.5,20.7,1234,0,1,2,3,4,5,6,7,8,9,'WW: test start']
        HT3_db.insert(tablename,values);
        time.sleep(1)
        HT3_db.commit()
        # check for new rrdtool-infos
        db_info.rrdtool_update()

        counter=0
        while counter< 6:
            # check for new rrdtool-infos
            db_info.rrdtool_update()
            print("main:   sleep 33 seconds")
            time.sleep(33)
            # check for new rrdtool-infos
            db_info.rrdtool_update()
            print("main:   now insert new values, Loop{0}".format(counter+1))
            tablename="warmwasser"
            comment="{0}: test:{1}".format(tablename, int(time.time()))
            values=[16.3,21.6,20.8,1235,0,1,2,3,4,5,6,7,8,9,comment]
            HT3_db.insert(tablename,values);
            HT3_db.commit()
            time.sleep(1)
            tablename="heizkreis1"
            comment="{0}: test:{1}".format(tablename, int(time.time()))
            values=[17.1,21.9,21.8,1236,1,2,3,4,comment]
            HT3_db.insert(tablename,values);
            time.sleep(1)
            HT3_db.commit()
            # check for new rrdtool-infos
            db_info.rrdtool_update()
            
            print("main:   insert done,           Loop{0}".format(counter+1))
            counter +=1
            
        counter=0
        while counter< 12:
            # check for new rrdtool-infos
            db_info.rrdtool_update()
            time.sleep(2)
            db_info.rrdtool_update()
            print("continue info-checking, UTC:{0}".format(int(time.time())))
            time.sleep(15)
            counter +=1

        HT3_db.close()
        print("main:Insert-Loop terminated")
