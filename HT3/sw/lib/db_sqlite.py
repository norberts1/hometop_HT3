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
#
""" Class 'cdb_sqlite' for creating, reading and writing data from/to sqlite-database

cdb_sqlite.__init__     -- constructor of class 'cdb_sqlite'
                             mandatory: parameter 'configurationfilename' (Path and name)
createdb_sqlite         -- creating database 'sqlite'
                             The db-structur is taken from xml-configurefile
                             mandatory: to be connected to database
configurationfilename   -- returns the used xml-config filename.
                             mandatory: none
db_sqlite_filename      -- returns and setup of used sqlite-db  filename.
                             mandatory: none
is_sqlite_db_available  -- returns True/False on status sqlite-db available/not available
                             mandatory: none
addcolumn               -- add named column of columntype for table using sql-commands
                             mandatory: tablename, columnname, columntype
close                   -- close cursor and connection to sql-database
                             mandatory: none
connect                 -- connect and get cursor of sql-database
                             mandatory: none
commit                  -- send commit to database using sql-commands
                             mandatory: to be connected to database
createindex             -- creating index on named column for table using sql-commands
                             mandatory: tablename, indexname, columnname
                                        to be connected to database
createtable             -- creating table if not exists using sql-commands
                             mandatory: tablename
                                        to be connected to database
delete                  -- delete columns where contentvalue and expression is found in table
                             mandatory: tablename, columnname, contentvalue
                                        to be connected to database
                             optional : expression (default is '=')
insert                  -- insert values in table using sql-commands
                             mandatory: tablename, values [bunch of values]
                                        to be connected to database
                             optional : timestamp (default is current Localtime and UTC are used)
selectwhere             -- returns values from table with named column, expression, searchvalue and what
                             mandatory: tablename, columnname, searchvalue
                                        to be connected to database
                             optional : expression (default is '=')
                                        what       (default is '*')
setpragma               -- Set pragma for the database using sql-commands
                             mandatory: pragmaname, pragmavalue
                                        to be connected to database
gettableinfo            -- returns the current tableinfo using sql-commands
                             mandatory: tablename
                                        to be connected to database
vacuum                  -- execute command 'vaccum' on database using sql-commands
                             mandatory: to be connected to database
"""

import sqlite3, time, os
import xml.etree.ElementTree as ET

dbNotConnectedError = ValueError('Attempting to use "db_sqlite" that is not connected')

class cdb_sqlite(object):
    def __init__(self, configurationfilename):
        try:
            if not isinstance(configurationfilename, str):
                raise TypeError("Parameter: configurationfilename")

            self.__cfgfilename=configurationfilename
            #get database-name from configuration
            tree  = ET.parse(configurationfilename)
            self.__root  = tree.getroot()
            self.__dbname=self.__root.find('dbname_sqlite').text
            if not len(self.__dbname):
                raise NameError("'dbname_sqlite' not found in configuration")
            
            self.__path    = os.path.dirname (self.__dbname)
            self.__basename= os.path.basename(self.__dbname)
            if not os.path.isabs(self.__dbname):
                abspath=os.path.abspath(".")
                self.__fullpathname=os.path.join(abspath,os.path.abspath(self.__dbname))
            else:
                self.__fullpathname=self.__dbname
            
            self.__sql_enable=False
            self.__connection=None
            self.__cursor    =None

            for sql_part in self.__root.findall('sql-db'):
                self.__sql_enable    =sql_part.find('enable').text.upper()
                if self.__sql_enable=='ON' or self.__sql_enable=='1':
                    self.__sql_enable=True
                else:
                    self.__sql_enable=False
                    
        except (OSError, EnvironmentError, TypeError, NameError) as e:
            print("""cdb_sqlite();Error;<{0}>""".format(str(e.args)))
            raise e

        except (sqlite3.OperationalError) as e:
            print("""cdb_sqlite.__init__();Error;<{0}>;database<{1}>""".format(
                    e.args[0],
                    self.__dbname,))
            raise e

    def __del__(self):
        if not self.__connection==None:
            self.close()

    def addcolumn(self, tablename, columnname, columntype):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                # check first is column available, if not create the column
                try:
                    #do nothing if column is already available
                    str_select="SELECT * FROM "+tablename+" WHERE "+columnname+" NOT NULL;"
                    self.__cursor.execute(str_select)
                except:
                    str_alter="ALTER TABLE "+tablename+" ADD COLUMN "+columnname+" "+columntype+";"
                    try:
                        self.__cursor.execute(str_alter)
                    except (sqlite3.OperationalError) as e:
                        print("""cdb_sqlite.addcolumn();Error;<{0}>;Table<{1}>;Column<{2}>""".format(
                                e.args[0],
                                tablename,
                                columnname))

    def close(self):
        if self.__sql_enable==True:
            try:
                if not self.__connection==None:
                    self.__cursor.close()
                    self.__connection.close()
                    self.__cursor=None
                    self.__connection=None
            except:
                print("cdb_sqlite.close();Error;couldn't close sql-database")

    def connect(self):
        if self.__sql_enable==True:
            try:
                if self.__connection==None:
                    self.__connection=sqlite3.connect(self.__dbname)
                    self.__cursor=self.__connection.cursor()
            except:
                print("cdb_sqlite.connect();Error;couldn't connect to sql-database")
            

    def commit(self):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                try:
                    if not self.__connection==None:
                        self.__connection.commit()
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.commit();Error;<{0}>'.format(e.args[0]))

    def createindex(self, tablename, indexname, columnname):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                strcmd="CREATE INDEX IF NOT EXISTS "+indexname+" ON "+tablename+"("+columnname+");"
                try:
                    self.__cursor.execute(strcmd)
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.createindex();Error;<{0}>;Table<{1}>'.format(e.args[0],tablename))

    def createtable(self, tablename):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                strcmd="CREATE TABLE IF NOT EXISTS "+tablename+" (Local_date_time CURRENT_TIMESTAMP, UTC INT);"
                try:
                    self.__cursor.execute(strcmd)
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.createtable();Error;<{0}>;Table<{1}>'.format(e.args[0],tablename))

    def delete(self, tablename, columnname, contentvalue, exp='='):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                try:
                    strcmd="DELETE FROM "+tablename+" WHERE "+columnname+exp+contentvalue
                    self.__cursor.execute(strcmd)
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.delete();Error;<{0}>'.format(e.args[0]))
            
    def insert(self, tablename, values, timestamp=None):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                if timestamp==None:
                    itimestamp=int(time.time())
                else:
                    itimestamp=int(timestamp)
                localtime=time.localtime(itimestamp)
                # first column:='Local_date_time' default set to Local-time
                __strdatetime="""{:4d}.{:02d}.{:02d} {:02d}:{:02d}:{:02d}""".format(localtime.tm_year, \
                                                                                    localtime.tm_mon, \
                                                                                    localtime.tm_mday, \
                                                                                    localtime.tm_hour, \
                                                                                    localtime.tm_min, \
                                                                                    localtime.tm_sec)

                strcmd="""INSERT INTO '{0}' VALUES('{1}','{2}',{3});""".format(
                    tablename,
                    __strdatetime,
                    itimestamp,
                    ",".join("""'{0}'""".format(str(val).replace('"', '""')) for val in values))
                try:
                    self.__cursor.execute(strcmd)
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.insert();Error;<{0}>'.format(e.args[0]))

    def is_sql_db_enabled(self):
        return self.__sql_enable

    def selectwhere(self, tablename, columnname, searchvalue, exp='=', what='*'):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                # function returns the a list of values or empty list on none match
                try:
                    strcmd="SELECT "+what+" FROM "+tablename+" WHERE "+columnname+" "+exp+" "+searchvalue+";"
                    return list(self.__cursor.execute(strcmd))
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.selectwhere();Error;<{0}>'.format(e.args[0]))
        else:
            return list()

    def setpragma(self, pragmaname, pragmavalue):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                try:
                    strcmd="PRAGMA "+pragmaname+" "+pragmavalue
                    self.__cursor.execute(strcmd)
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.setpragma();Error;<{0}>'.format(e.args[0]))
        
    def gettableinfo(self, tablename):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                try:
                    strcmd="PRAGMA table_info ({0})".format(tablename)
                    return self.__cursor.execute(strcmd)
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.gettableinfo();Error;<{0}>'.format(e.args[0]))
        else:
            return list()
        
    def vacuum(self):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                try:
                    self.__cursor.execute("VACUUM")
                except (sqlite3.OperationalError) as e:
                    print('cdb_sqlite.vacuum();Error;<{0}>'.format(e.args[0]))

    #---------------------
    def createdb_sqlite(self):
        if self.__sql_enable==True:
            if self.__connection==None:
                raise dbNotConnectedError
            else:
                try:
                    #first of all (before table-creation) set pragma auto_vacuum
                    self.setpragma("auto_vacuum","= full")
                    
                    for syspart in self.__root.findall('systempart'):
                        syspartname = syspart.attrib["name"]
                        # create table
                        self.createtable(syspartname)
                        # set index for first column 'data_time'
                        self.createindex(syspartname,"idate_time","Local_date_time")
                        
                        for logitem in syspart.findall('logitem'):
                            name = logitem.attrib["name"]
                            datatype = logitem.find('datatype').text
                            datause = logitem.find('datause').text
                            maxvalue= logitem.find('maxvalue').text
                            default = logitem.find('default').text
                            unit    = logitem.find('unit').text
                    #        print(name,datatype,datause,maxvalue,default,unit)
                            self.addcolumn(syspartname,name,datatype.upper())
                    self.commit()
                except (sqlite3.OperationalError, EnvironmentError) as e:
                    print('create_db.sqlite();Error;<{0}>'.format(e.args[0]))
                    raise e

    def configurationfilename(self):
        return self.__cfgfilename
    
    def db_sqlite_filename(self, pathname=None):
        # function sets / returns the db-name
        if not pathname==None:
            self.__dbname=pathname
        return self.__dbname

    def is_sqlite_db_available(self, dbname=None):
        dbfilename=dbname if not dbname==None else self.__dbname
        if os.access(dbfilename,os.W_OK and os.R_OK):
            return True
        else:
            return False

#--- class cdb_sqlite end ---#

### Runs only for test ###########
if __name__ == "__main__":
    configurationfilename='./../etc/config/4test/create_db_test.xml'
    HT3_db=cdb_sqlite(configurationfilename)
    dbfilename=HT3_db.db_sqlite_filename()
    print("------------------------")
    print("Config: get sql-database configuration at first")
    print("configfile            :'{0}'".format(configurationfilename))
    print("sql db-file           :'{0}'".format(dbfilename))
    print("sql db_enabled        :{0}".format(HT3_db.is_sql_db_enabled()))
    HT3_db.connect()
    print("Create database:{}".format(dbfilename))
    HT3_db.createdb_sqlite()
    if HT3_db.is_sqlite_db_available(dbfilename):
        print("database available")
    else:
        print("database not available")
        
    print("Create table 'testtable'")    
    HT3_db.createtable("testtable")
    
    print("Add column to table")    
    HT3_db.addcolumn("testtable","Messwert1_int","INT")
    HT3_db.addcolumn("testtable","Messwert_real","REAL")
    HT3_db.addcolumn("testtable","Counter_int","INT")
    HT3_db.addcolumn("testtable","hexdump","TEXT")
    
    HT3_db.createindex("testtable","idate_time","Local_date_time")
    HT3_db.commit()
    counter=0
    print("Insert values to table")
    values=[44,35.1,2345,"hexdump1"]
    HT3_db.insert("testtable",values)
    while counter<10:
        values=[(43+counter*2),32.1,(2340+counter),"counting"]
        HT3_db.insert("testtable",values)
        time.sleep(1)
        print(counter+1)
        counter +=1
    HT3_db.commit()

    values=[34,45.6,3456,"liste eintragen"]
    HT3_db.insert("testtable",values);
    HT3_db.commit()
    print("-------------------------------------------")    
    print("view   'Counter_int'-raws equal 2347")    
    selectvalues=HT3_db.selectwhere("testtable","Counter_int","2347")
    for zeile in selectvalues:
        print(zeile)

    print("-------------------------------------------")    
    print("delete 'Counter_int'-raws if equal 2347")    
    HT3_db.delete("testtable","Counter_int","2347")
    HT3_db.commit()
    print(" view must be empty")    
    selectvalues=HT3_db.selectwhere("testtable","Counter_int","2347")
    for zeile in selectvalues:
        print(zeile)
        
    print("-------------------------------------------")    
    print("view   'Counter_int'-raws less then 2347")    
    selectvalues=HT3_db.selectwhere("testtable","Counter_int","2347","<")
    for zeile in selectvalues:
        print(zeile)

    print("-------------------------------------------")    
    print("delete 'Counter_int'-raws if less then 2347")    
    HT3_db.delete("testtable","Counter_int","2347","<")
    HT3_db.commit()
    print(" view must be empty")    
    selectvalues=HT3_db.selectwhere("testtable","Counter_int","2347","<")
    for zeile in selectvalues:
        print(zeile)

    print("-------------------------------------------")    
    print(" select 'Messwert1_int'-raws greather then '50'")    
    print("  and view attached Local_date_time")    
    selectvalues=HT3_db.selectwhere("testtable","Messwert1_int","50",">","Local_date_time")
    for zeile in selectvalues:
        print(zeile)

    print("-------------------------------------------")    
    print(" table_info from 'solar'")    
    infos=HT3_db.gettableinfo("solar")
    for info in infos:
        print(info)
                                                                                          
    HT3_db.vacuum()
    HT3_db.close()
    
