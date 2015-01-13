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

configurationfilename='./etc/config/HT3_db_cfg.xml'
sqlitedb=db_sqlite.cdb_sqlite(configurationfilename)
sqlitedb.connect()
print("------------------------")
print("Create: sqlite -database")
sqlitedb.createdb_sqlite()
#check created sqlite-database for read/write access
databasename=sqlitedb.db_sqlite_filename()
if os.access(databasename,os.W_OK and os.R_OK):
    print("sqlite-database:'{0}' created and access possible".format(databasename))
else:
    print("sqlite-database:'{0}' not available".format(databasename))

sqlitedb.close()

print("------------------------------------------------")
print("Create: rrdtool-database (if request is enabled)")
rrdtool=db_rrdtool.cdb_rrdtool(configurationfilename)
if not rrdtool.is_rrdtool_db_enabled():
    print("rrdtool-database will not be created")
    print("  enable-flag is set to 'False' in configuration")
else:    
    rrdtool.createdb_rrdtool()
    if rrdtool.is_rrdtool_db_available():
        print("rrdtool-databases:'{0}' created and access possible".format(rrdtool.db_rrdtool_filename()))
    else:
        print("rrdtool-databases:'{0}' not available".format(rrdtool.db_rrdtool_filename()))
