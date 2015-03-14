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
# Ver:0.1.7.1/ Datum 04.03.2015 logging from ht_utils added
#################################################################
#
""" Module 'create_databases.py' creats databases 'sqlite' and 'rrdtool'

    All necessary informations are taken from xml-configurationfile.
    
    Database 'sqlite' is created if not yet available.
      If available, it will not be overwritten.
    Database 'rrdtool' is only created if the 'enable'-tag in configurationfile
      is set to 'on' or '1'.
      If creation is enabled and the database is already available,
      it will not be overwritten.
"""

import sys, os
sys.path.append('lib')
import db_sqlite
import db_rrdtool
import ht_utils

####################################
## create logfile
filepathname="./var/log/create_databases.log"
 # if folder isn't available it will be created
abslogpath=os.path.normcase(os.path.abspath(os.path.dirname(filepathname)))
if not os.path.exists(abslogpath):
    try:
        os.mkdir(abslogpath)
    except:
        # couldn't create folder, so
        #  upper folders not available?, try again with makedirs
        try:
            os.makedirs(abslogpath)
        except:
            errorstr="create_databases();Error;Can't create folder:{0}".format(abslogpath)
            print(errorstr)
            raise
else:
    #zs#test#   print("Folder already available:{0}".format(abslogpath))
    pass
    
logfilepathname=os.path.join(abslogpath, os.path.basename(filepathname))
try:
    logobj=ht_utils.clog()
    logging=logobj.create_logfile(logfilepathname, loggertag="create_db")
except:
    errorstr="create_databases();Error;Can't create logfile:{0}".format(logfilepathname)
    print(errorstr)
    raise

####################################
## set configuration-filename and create sqlite-db
configurationfilename='./etc/config/HT3_db_cfg.xml'
sqlitedb=db_sqlite.cdb_sqlite(configurationfilename, logger=logging)
sqlitedb.connect()
infostr="------------------------------------------------"
logging.info(infostr)
print(infostr)
infostr="Create: sqlite -database"
logging.info(infostr)
print(infostr)
sqlitedb.createdb_sqlite()
#check created sqlite-database for read/write access
databasename=sqlitedb.db_sqlite_filename()
if os.access(databasename,os.W_OK and os.R_OK):
    infostr="sqlite-database:'{0}' created and access possible".format(databasename)
else:
    infostr="sqlite-database:'{0}' not available".format(databasename)
print(infostr)
logging.info(infostr)

sqlitedb.close()

infostr="------------------------------------------------"
logging.info(infostr)
print(infostr)
infostr="Create: rrdtool-database (if request is enabled)"
logging.info(infostr)
print(infostr)
rrdtool=db_rrdtool.cdb_rrdtool(configurationfilename, logger=logging)
if not rrdtool.is_rrdtool_db_enabled():
    infostr="rrdtool-database will not be created"
    logging.info(infostr)
    print(infostr)
    infostr="  enable-flag is set to 'False' in configuration"
    logging.info(infostr)
    print(infostr)
else:    
    rrdtool.createdb_rrdtool()
    if rrdtool.is_rrdtool_db_available():
        infostr="rrdtool-databases:'{0}' created and access possible".format(rrdtool.db_rrdtool_filename())
    else:
        infostr="rrdtool-databases:'{0}' not available".format(rrdtool.db_rrdtool_filename())

logging.info(infostr)
print(infostr)

