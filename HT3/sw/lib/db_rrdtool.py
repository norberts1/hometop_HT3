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
# Ver:0.1.8  / Datum 16.09.2015 repeat call 'os.system()'on error
# Ver:0.1.10 / Datum 28.08.2016 code-adjustment after pylint
# Ver:0.2    / Datum 29.08.2016 added info-text
# Ver:0.3    / Datum 18.01.2019 create_draw() added
#################################################################
#

import os
import tempfile
import xml.etree.ElementTree as ET
import time
import ht_utils
import logging
import ht_const


class cdb_rrdtool(ht_utils.clog):
    """ Class 'cdb_rrdtool' for creating and writing data to rrdtool-database
    """
    __rrdtool_syspartnames = {}
    __rrdtool_dbname_mapping = {}

    def __init__(self, configurationfilename, PerlIF=True, logger=None):
        """
        constructor of class 'cdb_rrdtool'
         mandatory: parameter 'configurationfilename' (Path and name)
         optional : PerlIF (default must be set to 'True')
         perl is used to handle the interface to rrdtool
        """
        # init/setup logging-file
        if logger == None:
            ht_utils.clog.__init__(self)
            self._logging = ht_utils.clog.create_logfile(self, logfilepath="./cdb_rrdtool.log", loggertag="cdb_rrdtool")
        else:
            self._logging = logger

        self.__databasefiles = []
        self.__rrdtoolh = None
        self.__rrdfileh = None
        self.__rrdtool_enable = False
        self.__rrdtool_stepseconds = 60
        self.__rrdtool_starttime_utc = 0

        # flag used to activate perl rrdtool-handling,
        #  it is not yet available for Python3 and debian
        self.__PerlIF = PerlIF
        try:
            if not isinstance(configurationfilename, str):
                errorstr = "cdb_rrdtool();TypeError;Parameter: configurationfilename"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)

            #get database-name from configuration
            tree = ET.parse(configurationfilename)
            self.__root = tree.getroot()
            self.__dbname = self.__root.find('dbname_rrd').text
            if not len(self.__dbname):
                errorstr = "cdb_rrdtool();NameError;'dbname_rrd' not found in configuration"
                self._logging.critical(errorstr)
                raise NameError(errorstr)

            self.__path = os.path.dirname(self.__dbname)
            self.__basename = os.path.basename(self.__dbname)
            if not os.path.isabs(self.__dbname):
                abspath = os.path.abspath(".")
                self.__fullpathname = os.path.join(abspath, os.path.abspath(self.__dbname))
            else:
                self.__fullpathname = self.__dbname

            self.__Perl_dbcreateFile = os.path.normcase("/tmp/rrdtool_dbcreate.pl")
            self.__fillup_mapping()

            for rrdtool_part in self.__root.findall('rrdtool-db'):
                self.__rrdtool_enable = rrdtool_part.find('enable').text.upper()
                if self.__rrdtool_enable == 'ON' or self.__rrdtool_enable == '1':
                    self.__rrdtool_enable = True
                else:
                    self.__rrdtool_enable = False

                self.__rrdtool_stepseconds = int(rrdtool_part.find('step_seconds').text)
                if self.__rrdtool_stepseconds < 60:
                    self.__rrdtool_stepseconds = 60

                self.__rrdtool_starttime_utc = int(rrdtool_part.find('starttime_utc').text)
                if self.__rrdtool_starttime_utc < 1344000000 or self.__rrdtool_starttime_utc > 1999999999:
                    self.__rrdtool_starttime_utc = 1344000000

        except (OSError, EnvironmentError, TypeError, NameError) as e:
            errorstr = """cdb_rrdtool();Error;<{0}>""".format(str(e.args))
            print(errorstr)
            self._logging.critical(errorstr)
            raise e

    def __del__(self):
        """
        """
        pass

    def __fillup_mapping(self):
        """
        """
        for syspart in self.__root.findall('systempart'):
            syspartname = syspart.attrib["name"]
            shortnameinpart = syspart.find('shortname')
            shortname = shortnameinpart.attrib["name"]
            Filename = self.__fullpathname + "_" + str(syspartname) + ".rrd"
            cdb_rrdtool.__rrdtool_syspartnames.update({shortname: syspartname})
            cdb_rrdtool.__rrdtool_dbname_mapping.update({shortname: Filename})

    def syspartnames(self):
        """
        returns the 'syspartnames' from configuration as directory
         structur : {shortname:syspartname}
         mandatory: none
        """
        return cdb_rrdtool.__rrdtool_syspartnames

    def dbfilenames(self, syspartname=None):
        """
        returns the 'database-filenames' from configuration as:
         1. directory     <- 'syspartname' := None
         2. folder-string <- 'syspartname' := valid nickname e.g. 'HK'
         structur : {shortname:Filename}
         mandatory: none
         optional : Syspartshortname (default is 'None')
        """
        if not syspartname == None:
            return cdb_rrdtool.__rrdtool_dbname_mapping[syspartname]
        else:
            return cdb_rrdtool.__rrdtool_dbname_mapping

    def isavailable(self):
        """
        returns True/False if database is available/not available.
         mandatory: none
        """
        #find database-files in directory
        dircontent = os.listdir(self.__path)
        filefound = 0
        for content in dircontent:
            if self.__basename in content:
                self.__databasefiles.append(content)
                filefound += 1
        return bool(filefound)

    def update(self, syspartname, values, timestamp=None):
        """
        updates the rrdtool-database entry 'syspartname' with value(s)
         mandatory: syspartname <- syspart-longname (not nickname!)
         values      <- array of tuples [(n1,v1),(n2,v2),...]
         optional : timestamp        (default is current UTC-time)
        """
        try:
            if not self.isavailable():
                errorstr = "db_rrdtool.update();Error;database not yet created"
                self._logging.critical(errorstr)
                raise EnvironmentError(errorstr)

            if timestamp == None:
                itimestamp = int(time.time())
            else:
                itimestamp = int(timestamp)
            rrdfile = tempfile.NamedTemporaryFile()
            filename = rrdfile.name + "_"+syspartname + ".pl"
            self.__rrdfileh = open("{0}".format(filename), "w")
            self.__define_rrd_update_fileheader()
            self.__define_rrd_update_filehandle(syspartname, itimestamp)
            self.__define_rrd_update_details(syspartname, values)
            self.__rrdfileh.close()

            #setup executemode for file to: 'rwxr-xr-x'
            os.chmod(filename, 0o755)
            #execute perl-script for updating 'rrdtool' database
            error = os.system(filename)
            if error:
                #  repeat the call if any error occured, perhaps it works the second time
                #  see: https://www.mikrocontroller.net/topic/324673#4239986
                error = os.system(filename)
                if error:
                    self.__rrdfileh = open("{0}".format(filename), "a")
                    self.__rrdfileh.write('# ---- error occured: -------\n')
                    self.__rrdfileh.write('# {0}, syspart:{1}, timestamp:{2}\n'.format(error, syspartname, itimestamp))
                    self.__rrdfileh.flush()
                    self.__rrdfileh.close()
                    errorstr = "db_rrdtool.update();ValueError;script failed, syspart:{0}, timestamp:{1}".format(syspartname, itimestamp)
                    self._logging.critical(errorstr)
                    raise ValueError(errorstr)
            else:
                os.remove(filename)

            return bool(error)

        except (ValueError, EnvironmentError, NameError, TypeError) as e:
            if not self.__rrdfileh == None:
                self.__rrdfileh.close()
            errorstr = 'cdb_rrdtool.update();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            return True

    def __define_rrd_update_fileheader(self):
        """
        """
        try:
            self.__rrdfileh.write("#!/usr/bin/perl\n#\nuse strict;\nuse warnings;\nuse RRDTool::OO;\n\n")
            self.__rrdfileh.flush()
        except (EnvironmentError) as e:
            errorstr = 'cdb_rrdtool.__define_rrd_update_fileheader();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def __define_rrd_update_filehandle(self, syspartname, timestamp):
        """
        """
        try:
            Filename = self.__fullpathname + "_" + str(syspartname) + ".rrd"
            self.__rrdfileh.write('my $DB_{0}  = "{1}";\n'.format(syspartname, Filename))
            self.__rrdfileh.write('my ${0}_rrdh = RRDTool::OO->new(file => $DB_{0});\n'.format(syspartname))
            self.__rrdfileh.write('#\n')
            self.__rrdfileh.write('${0}_rrdh->update (\n'.format(syspartname))
            self.__rrdfileh.write('  time   => {0},\n'.format(timestamp))
            self.__rrdfileh.write('  values => {\n')
            self.__rrdfileh.flush()
        except (EnvironmentError) as e:
            errorstr = 'cdb_rrdtool.__define_rrd_update_filehandle();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def __define_rrd_update_details(self, syspartname, values):
        """
        """
        try:
            if not (isinstance(values, list) and isinstance(values[0], tuple)):
                errorstr = "cdb_rrdtool.__define_rrd_update_details;TypeError;only a list of tuples allowed for 'values'"
                self._logging.critical(errorstr)
                raise TypeError(errorstr)
            for (logitem, value) in values:
                if len(str(logitem)) > 18:
                    errorstr = "cdb_rrdtool.__define_rrd_update_details;Error;logitem-length must be less then 19 chars"
                    self._logging.critical(errorstr)
                    raise TypeError(errorstr)
                self.__rrdfileh.write('   {0}=>{1},\n'.format(logitem, value))
            self.__rrdfileh.write('   }\n')
            self.__rrdfileh.write(');\n')
            self.__rrdfileh.flush()

        except (EnvironmentError) as e:
            errorstr = 'cdb_rrdtool.update();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def createdb_rrdtool(self, timestamp=None, step_seconds=None):
        """
            creating database 'rrdtool'
             The db-structur is taken from xml-configurefile
             mandatory: Perl 'RRDTool::OO' is installed
             optional : timestamp    (default is value from configuration)
             step_seconds (default is value from configuration)
        """
        if self.is_rrdtool_db_available():
            infostr = "cdb_rrdtool.createdb_rrdtool();INFO;Database:'{0}' already created".format(self.__dbname)
            print(infostr)
            self._logging.info(infostr)
        else:
            if not self.__PerlIF:
                errorstr = "cdb_rrdtool.createdb_rrdtool();Error;rrdtool database-creation must be done with perl-scripts"
                self._logging.critical(errorstr)
                raise EnvironmentError(errorstr)
            try:
                infostr = "cdb_rrdtool.createdb_rrdtool();INFO;Database:'{0}' will be created".format(self.__dbname)
                print(infostr)
                self._logging.info(infostr)
                # set starttime and step-seconds for rrdtool-db
                if timestamp == None:
                    itimestamp = int(self.__rrdtool_starttime_utc)
                else:
                    itimestamp = int(timestamp)

                if step_seconds == None:
                    istep_seconds = int(self.__rrdtool_stepseconds)
                else:
                    istep_seconds = int(step_seconds)

                # create file to fillup this as perlscript with dbcreate-informations
                self.__rrdtoolh = open("{0}".format(self.__Perl_dbcreateFile), "w")
                # first fillup fileheader
                self.__define_rrd_fileheader()

                # then fillup filehandles
                for syspart in self.__root.findall('systempart'):
                    syspartname = syspart.attrib["name"]
                    self.__define_rrd_filehandle(syspartname)

                # then fillup startuptime and step-seconds
                self.__define_rrd_starttime(itimestamp, istep_seconds)

                for syspart in self.__root.findall('systempart'):
                    syspartname = syspart.attrib["name"]
                    #write detail-header
                    self.__define_rrd_details(syspartname, "", "", "", True)

                    for logitem in syspart.findall('logitem'):
                        name = logitem.attrib["name"]
                        datause = logitem.find('datause').text.upper()
                        maxvalue = logitem.find('maxvalue').text
                        default = logitem.find('default').text
                        if datause in ['GAUGE', 'COUNTER', 'DERIVE', 'ABSOLUTE', 'COMPUTE']:
                            # fillup database-details for logitems
                            self.__define_rrd_details(syspartname, name, datause, default)
                    #write trailer
                    self.__define_rrd_details(syspartname, "", "", "", False, True)
                self.__rrdtoolh.close()

                #setup executemode for file to: 'rwxr-xr-x'
                os.chmod(self.__Perl_dbcreateFile, 0o755)

                #execute perl-script to create 'rrdtool' database
                os.system(self.__Perl_dbcreateFile)

                #check rrdtool-db for availability, if not raise exception
                if not self.is_rrdtool_db_available():
                    errorstr = "db_rrdtool.createdb_rrdtool();Error;rrdtool-database:'{0}' not created".format(self.__dbname)
                    self._logging.critical(errorstr)
                    raise EnvironmentError(errorstr)
                else:
                    infostr = "cdb_rrdtool.createdb_rrdtool();INFO;Database:'{0}' is created".format(self.__dbname)
                    print(infostr)
                    self._logging.info(infostr)

            except (EnvironmentError, TypeError) as e:
                if not self.__rrdtoolh == None: self.__rrdtoolh.close()
                errorstr = 'db_rrdtool.createdb_rrdtool();Error;<{0}>'.format(e.args[0])
                self._logging.critical(errorstr)
                print(errorstr)

    def create_draw(self, path_2_db, path_2_draw,
                    hc_count=1,
                    controller_type_nr=ht_const.CONTROLLER_TYPE_NR_Fxyz,
                    mixer_flags=[0, 0, 0, 0],
                    hydsw=0,
                    solar_flag=1,
                    second_source_flag=0
                    ):
        """calling the rrdtool-draw script to create rrdtool-drawings"""
        [hc1_mixer, hc2_mixer, hc3_mixer, hc4_mixer] = mixer_flags
        debugstr = """cdb_rrdtool.create_draw();\n
                    path2db  :{0};\n
                    path2draw:{1};\n
                    hc_count:{2};\n
                    Contr.type:{3};\n
                    mixer_flags:{4};\n
                    hydrlic_sw:{5};\n
                    solar_flag:{6};\n
                    second_source:{7}\n""".format(path_2_db, path_2_draw, hc_count, controller_type_nr, mixer_flags, hydsw, solar_flag, second_source_flag)
        self._logging.debug(debugstr)
        AbsPathandFilename = os.path.abspath(os.path.normcase('./etc/rrdtool_draw.pl'))
        Abspath2_db = ht_utils.cht_utils.Extract_HT3_path_from_AbsPath(self, path_2_db)
        Abspath_2_draw = ht_utils.cht_utils.Extract_HT3_path_from_AbsPath(self, path_2_draw)


        strsystemcmd1 = AbsPathandFilename+' '+Abspath2_db+' '+Abspath_2_draw+' '+str(hc_count)+' '
        strsystemcmd2 = str(controller_type_nr)+' '+str(hc1_mixer)+' '+str(hc2_mixer)+' '+str(hc3_mixer)+' '+str(hc4_mixer)
        strsystemcmd = strsystemcmd1 + strsystemcmd2 +' '+str(hydsw) +' '+str(solar_flag)+' '+str(second_source_flag)
        self._logging.debug(strsystemcmd)
        try:
            #execute perl-script for drawing 'rrdtool' dbinfos
            error = os.system(strsystemcmd)
            if error:
                errorstr = "cdb_rrdtool.create_draw();Error:{0}; cmd:{1}".format(error, strsystemcmd)
                self._logging.critical(errorstr)
        except:
            errorstr = "cdb_rrdtool.create_draw();Error; os.system-call"
            self._logging.critical(errorstr)

    def __define_rrd_fileheader(self):
        """
        """
        try:
            self.__rrdtoolh.write("#!/usr/bin/perl\n#\nuse strict;\nuse warnings;\nuse RRDTool::OO;\n\n")
            self.__rrdtoolh.write('my $rc = 0;\n')
            self.__rrdtoolh.flush()
        except (EnvironmentError) as e:
            errorstr = 'db_rrdtool.__define_rrd_fileheader();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def __define_rrd_filehandle(self, syspartname):
        """
        """
        try:
            Filename = self.__fullpathname + "_" + str(syspartname) + ".rrd"
            self.__rrdtoolh.write('my $DB_{0}  = "{1}";\n'.format(syspartname, Filename))
            self.__rrdtoolh.write('my ${0}_rrdh = RRDTool::OO->new(file => $DB_{0});\n'.format(syspartname))
            self.__rrdtoolh.flush()
        except (EnvironmentError) as e:
            errorstr = 'db_rrdtool.__define_rrd_filehandle();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def __define_rrd_starttime(self, starttime=None, iterations="100"):
        """
        """
        try:
            if starttime == None:
                istarttime = int(time.time())
            else:
                istarttime = int(starttime)

            self.__rrdtoolh.write('# \n')
            self.__rrdtoolh.write('# Set Starttime\n')
            self.__rrdtoolh.write('my $start_time     = {0};\n'.format(istarttime))
            self.__rrdtoolh.write('my $step           = {0};\n'.format(iterations))
            self.__rrdtoolh.write('# \n')
            self.__rrdtoolh.write('# Define the RRD\n')
            self.__rrdtoolh.write("# RRA's consolidation function must be one of the following:\n")
            self.__rrdtoolh.write("#  ['AVERAGE', 'MIN', 'MAX', 'LAST', 'HWPREDICT', 'SEASONAL',\n")
            self.__rrdtoolh.write("#   'DEVSEASONAL', 'DEVPREDICT', 'FAILURES']\n")
            self.__rrdtoolh.write('# \n')
            self.__rrdtoolh.write("# Define the archiv\n")
            self.__rrdtoolh.write("# 'LAST    saved every 5 min, kept for 10years back\n")
            self.__rrdtoolh.write("# 'AVERAGE saved every 1 min, kept for  1year  back\n")
            self.__rrdtoolh.write("# 'MAX  saved every 5 min, kept for 1year back\n")
            self.__rrdtoolh.write("# 'MIN  saved every 5 min, kept for 1year back\n")
            self.__rrdtoolh.write('# \n')
            self.__rrdtoolh.flush()
        except (EnvironmentError) as e:
            errorstr = 'db_rrdtool.__define_rrd_starttime();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def __define_rrd_details(self, syspartname, logitem, datause, default, heading=False, tail=False):
        """
        """
        try:
            if heading:
                rrd_handlename = syspartname + "_rrdh"
                self.__rrdtoolh.write('$rc = ${0}->create(\n'.format(rrd_handlename))
                self.__rrdtoolh.write('    start       => $start_time - 600,\n')
                self.__rrdtoolh.write('    step        => $step,\n')
            elif tail:
                self.__rrdtoolh.write('        archive     => { \n')
                self.__rrdtoolh.write('            rows     => 1051200,\n')
                self.__rrdtoolh.write('            cpoints  => 5,\n')
                self.__rrdtoolh.write("            cfunc    => 'LAST',\n")
                self.__rrdtoolh.write('        },\n')
                self.__rrdtoolh.write('        archive     => { \n')
                self.__rrdtoolh.write('            rows     => 525600,\n')
                self.__rrdtoolh.write('            cpoints  => 1,\n')
                self.__rrdtoolh.write("            cfunc    => 'AVERAGE',\n")
                self.__rrdtoolh.write('        },\n')
                self.__rrdtoolh.write('        archive     => { \n')
                self.__rrdtoolh.write('            rows     => 105120,\n')
                self.__rrdtoolh.write('            cpoints  => 5,\n')
                self.__rrdtoolh.write("            cfunc    => 'MAX',\n")
                self.__rrdtoolh.write('        },\n')
                self.__rrdtoolh.write('        archive     => { \n')
                self.__rrdtoolh.write('            rows     => 105120,\n')
                self.__rrdtoolh.write('            cpoints  => 5,\n')
                self.__rrdtoolh.write("            cfunc    => 'MIN',\n")
                self.__rrdtoolh.write('        }\n')
                self.__rrdtoolh.write(');\n')
                self.__rrdtoolh.flush()
            else:
                self.__rrdtoolh.write('        data_source => { \n')
                self.__rrdtoolh.write("            name    => '{0}',\n".format(logitem))
                self.__rrdtoolh.write("            type    => '{0}',\n".format(datause))
                self.__rrdtoolh.write("        },\n")

            self.__rrdtoolh.flush()
        except (EnvironmentError) as e:
            self.__rrdtoolh.flush()
            errorstr='db_rrdtool.__define_rrd_details();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            raise e

    def is_rrdtool_db_available(self, dbname=""):
        """
        returns True/False on status rrdtool-db available/not available
         mandatory: none
         optional : db-name      (default is value from configuration)
        """
        syspartname = ""
        syspartcount = 0
        dbfilescount = 0
        rtnvalue = False
        try:
            if len(dbname):
                # check the file 'dbname' with it's naming for availability
                if os.access(dbname, os.W_OK and os.R_OK):
                    rtnvalue = True
            else:
                for syspart in self.__root.findall('systempart'):
                        syspartname = syspart.attrib["name"]
                        Filename = self.__dbname + "_" + str(syspartname) + ".rrd"
                        #check of dbfile-available
                        if os.access(Filename, os.W_OK and os.R_OK):
                            dbfilescount += 1
                        syspartcount += 1
                if dbfilescount > 0 and dbfilescount == syspartcount:
                    rtnvalue = True

            return rtnvalue
        except (EnvironmentError) as e:
            errorstr = 'create_db.__is_rrdtool_db_available();Error;<{0}>'.format(e.args[0])
            self._logging.critical(errorstr)
            print(errorstr)
            return False

    def db_rrdtool_filename(self):
        """
        return of used rrdtool-db  filename.
         mandatory: none
        """
        # returns the db-basename
        return self.__dbname

    def is_rrdtool_db_enabled(self):
        """
        returns True/False for rrdtool-db config-tag 'enable'
        """
        return self.__rrdtool_enable

    def db_rrdtool_stepseconds(self):
        """
        returns value 'step_seconds' for rrdtool-db
        """
        return self.__rrdtool_stepseconds

    def db_rrdtool_starttime_utc(self):
        """
        returns value 'starttime_utc' for rrdtool-db
        """
        return self.__rrdtool_starttime_utc

#--- class cdb_rrdtool end ---#

### Runs only for test ###########
if __name__ == "__main__":
    configurationfilename = './../etc/config/4test/create_db_test.xml'
    db_rrdtool = cdb_rrdtool(configurationfilename)
    print("------------------------")
    print("Config: get rrdtool-database configuration at first")
    print("configfile            :'{0}'".format(configurationfilename))
    print("rrdtool db-file       :'{0}'".format(db_rrdtool.db_rrdtool_filename()))
    print("rrdtool db_enabled    :{0}".format(db_rrdtool.is_rrdtool_db_enabled()))
    print("rrdtool db_stepseconds:{0}".format(db_rrdtool.db_rrdtool_stepseconds()))
    print("rrdtool db_starttime  :{0}".format(db_rrdtool.db_rrdtool_starttime_utc()))

    print("------------------------")
    print("Create: rrdtool-database next (independent from 'db_enabled' flag)")
    db_rrdtool.createdb_rrdtool()

    print("------------------------")
    print("Update: rrdtool-database")
    values = [("T_ist_HK", 22.3), ("T_soll_HK", 21.0)]
    error = db_rrdtool.update("heizkreis1", values)
    if error:
        print("Update rrdtool database Failed")
    else:
        print("Update rrdtool database OK")
    for syspartshortname in db_rrdtool.syspartnames():
        syspart = db_rrdtool.syspartnames()[syspartshortname]
        print("Shortname: {0:2}, syspartname: {1}\n +-> rrdtool_file: {2}\n".format(syspartshortname,
                                                                                syspart,
                                                                                db_rrdtool.dbfilenames()[syspartshortname]))
