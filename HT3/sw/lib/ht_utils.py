#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2015 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.6  / Datum 10.01.2015 first release
# Ver:0.1.7.1/ Datum 04.03.2015 'crc_check' added
#                               'make_crc' buffer-length corrected
#                               logging-class added
# Ver:0.1.9  / Datum 26.04.2016 'Is_TransceiverHaeder',
#                               'Transceiver_msg_size' and
#                               'Payload_msg_size'     added
# Ver:0.2    / Datum 28.08.2016 minor text-adjustments after Pylint
#                               'Absfilepathname()' added
# Ver:0.3    / Datum 11.06.2017 'MakeAbsPath2FileName()' added.
# Ver:0.3.1  / Datum 29.11.2018 'Extract_HT3_path_from_AbsPath()' added.
#
#################################################################

import os
import logging
import logging.handlers


class cht_utils(object):
    """
    Class: cht_utils.
     Common used for crc-check and more.
    """
    def __init__(self):
        """
        """
        self.__crc_table = [
            0x00, 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E, 0x10, 0x12, 0x14, 0x16, 0x18,
            0x1A, 0x1C, 0x1E, 0x20, 0x22, 0x24, 0x26, 0x28, 0x2A, 0x2C, 0x2E, 0x30, 0x32,
            0x34, 0x36, 0x38, 0x3A, 0x3C, 0x3E, 0x40, 0x42, 0x44, 0x46, 0x48, 0x4A, 0x4C,
            0x4E, 0x50, 0x52, 0x54, 0x56, 0x58, 0x5A, 0x5C, 0x5E, 0x60, 0x62, 0x64, 0x66,
            0x68, 0x6A, 0x6C, 0x6E, 0x70, 0x72, 0x74, 0x76, 0x78, 0x7A, 0x7C, 0x7E, 0x80,
            0x82, 0x84, 0x86, 0x88, 0x8A, 0x8C, 0x8E, 0x90, 0x92, 0x94, 0x96, 0x98, 0x9A,
            0x9C, 0x9E, 0xA0, 0xA2, 0xA4, 0xA6, 0xA8, 0xAA, 0xAC, 0xAE, 0xB0, 0xB2, 0xB4,
            0xB6, 0xB8, 0xBA, 0xBC, 0xBE, 0xC0, 0xC2, 0xC4, 0xC6, 0xC8, 0xCA, 0xCC, 0xCE,
            0xD0, 0xD2, 0xD4, 0xD6, 0xD8, 0xDA, 0xDC, 0xDE, 0xE0, 0xE2, 0xE4, 0xE6, 0xE8,
            0xEA, 0xEC, 0xEE, 0xF0, 0xF2, 0xF4, 0xF6, 0xF8, 0xFA, 0xFC, 0xFE, 0x19, 0x1B,
            0x1D, 0x1F, 0x11, 0x13, 0x15, 0x17, 0x09, 0x0B, 0x0D, 0x0F, 0x01, 0x03, 0x05,
            0x07, 0x39, 0x3B, 0x3D, 0x3F, 0x31, 0x33, 0x35, 0x37, 0x29, 0x2B, 0x2D, 0x2F,
            0x21, 0x23, 0x25, 0x27, 0x59, 0x5B, 0x5D, 0x5F, 0x51, 0x53, 0x55, 0x57, 0x49,
            0x4B, 0x4D, 0x4F, 0x41, 0x43, 0x45, 0x47, 0x79, 0x7B, 0x7D, 0x7F, 0x71, 0x73,
            0x75, 0x77, 0x69, 0x6B, 0x6D, 0x6F, 0x61, 0x63, 0x65, 0x67, 0x99, 0x9B, 0x9D,
            0x9F, 0x91, 0x93, 0x95, 0x97, 0x89, 0x8B, 0x8D, 0x8F, 0x81, 0x83, 0x85, 0x87,
            0xB9, 0xBB, 0xBD, 0xBF, 0xB1, 0xB3, 0xB5, 0xB7, 0xA9, 0xAB, 0xAD, 0xAF, 0xA1,
            0xA3, 0xA5, 0xA7, 0xD9, 0xDB, 0xDD, 0xDF, 0xD1, 0xD3, 0xD5, 0xD7, 0xC9, 0xCB,
            0xCD, 0xCF, 0xC1, 0xC3, 0xC5, 0xC7, 0xF9, 0xFB, 0xFD, 0xFF, 0xF1, 0xF3, 0xF5,
            0xF7, 0xE9, 0xEB, 0xED, 0xEF, 0xE1, 0xE3, 0xE5, 0xE7]

        self.__payloadlength = 0

    def crc_check(self, buffer, bufferlength):
        """
        returns True/False if CRC is OK or not.
        """
        return self.crc_testen(buffer, bufferlength)

    def crc_testen(self, buffer, bufferlength):
        """
        returns True/False if CRC is OK or not.
        """
        crc = 0
        if bufferlength < 3:
            return False
        try:
            for i in range(0, bufferlength - 2):
                crc = self.__crc_table[crc]
                crc ^= buffer[i]
            else:
                if crc == buffer[bufferlength-2]:
                    return True
                else:
                    return False
        except (IndexError) as e:
            print("HT3_decode.__crc_testen();Error;{0}", e.args[0])
            return False

    def make_crc(self, buffer, bufferlength):
        """
        returns crc-value if valid else False.
        """
        crc = 0
        if bufferlength < 3:
            return False
        try:
            for i in range(0, bufferlength):
                crc = self.__crc_table[crc]
                crc ^= buffer[i]
            return crc

        except (IndexError) as e:
            print("HT3_decode.__crc_testen();Error;{0}", e.args[0])
            return False

    def IsTempInRange(self, tempvalue, maxvalue=300.0, minvalue=-50.0):
        """
        returns True/False if tempvalue is in range or not.
        """
        return True if (float(tempvalue) < maxvalue and float(tempvalue) > minvalue) else False

    ## is ht_transceiver header ?
    def Is_TransceiverHeader(self, msgbuffer):
        """
        returns True/False if message starts with 'Transceiver-header' or not.
        """
        rtn_flag = False
        if len(msgbuffer) < 5:
            return False
        try:
            # start-tag '#'
            if (msgbuffer[0] == 0x23):
                # looking for 'H' and 'R'
                if (msgbuffer[1] == 0x48 and msgbuffer[2] == 0x52):
                    self.__payloadlength = msgbuffer[4]
                    rtn_flag = True
                else:
                    rtn_flag = False
                    self.__payloadlength = 0
        except:
            self.__payloadlength = 0

        return rtn_flag

    def Transceiver_msg_size(self):
        """
        returns the size of: payload + crc-byte
        """
        rtn_value = 0
        # plus 1 for CRC-byte
        if self.__payloadlength > 0:
            rtn_value = self.__payloadlength + 1
        return rtn_value

    def Payload_msg_size(self):
        """
        returns the size of: payload
        """
        return self.__payloadlength

    def Absfilepathname(self, filepathname):
        """
        return a tuple of absolute-path and filename as: (abspath, filename).
         This is independent from OS.
        """
        (path, filename) = os.path.split(filepathname)
        abspath = os.path.abspath(os.path.normcase(path))
        return (abspath, filename)

    def MakeAbsPath2FileName(self, tpl_path_and_filename, find_separator='/sw'):
        """returns the absolut path attached with filename.
            is searching for separator in path and cutting the rest of path.
            if separator is not found then the complete path is used.
        """
        (path, filename) = tpl_path_and_filename
        abs_filepathname = ""
        if os.path.isabs(path):
            my_abspath = path
        else:
            current_path = os.path.abspath('.')
            find_index = current_path.find(find_separator)
            sliced_path = current_path[0:find_index]
            if find_index > 0 and len(current_path) > 2:
                sliced_path = current_path[0:find_index + len(find_separator)]
            my_abspath = os.path.abspath(os.path.join(sliced_path, path))

        abs_filepathname = os.path.join(my_abspath, filename)
        return abs_filepathname

    def Extract_HT3_path_from_AbsPath(self, inpath):
        """extract the HT3 path from 'inpath' if available."""
        rtnpath = os.path.normcase(inpath)
        searchpath = os.path.normcase('HT3/sw')
        # check path and remove 'HT3/..' if any entry is found
        if searchpath in (rtnpath):
            rtnpath = rtnpath[: rtnpath.rfind(searchpath)]
        return os.path.abspath(rtnpath)

#--- class cht_utils end ---#


class clog(object):
    """
    Class: clog.
     Common used for logging.
    """
    def __init__(self):
        """
        Initialisation of logging.
        """
        self._created = False
        self._loglevel = logging.INFO
        self._fileonly = ""
        self._pathonly = ""

    def create_logfile(self, logfilepath="./default_logfile.log", loglevel=logging.INFO, loggertag="default"):
        """
        Create logfile with default-values (overwrite-able).
        """
        self._logfilepath = logfilepath
        self._loglevel = loglevel
        self._loggertag = loggertag
        self._pathonly = ""
        self._fileonly = ""
        (path, filename) = os.path.split(logfilepath)
        if len(path) > 0:
            self._pathonly = os.path.normcase(path)
        if len(filename) > 0:
            self._fileonly = filename

        try:
            self._handler = logging.handlers.RotatingFileHandler(self._logfilepath, maxBytes=1000000)
            _frm = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%d.%m.%Y %H:%M:%S")
            self._handler.setFormatter(_frm)
            self._logger = logging.getLogger(self._loggertag)
            self._logger.addHandler(self._handler)
            self._logger.setLevel(self._loglevel)
            self._created = True
            return self._logger
        except:
            raise EnvironmentError("clog.create_logfile();Error; could not create logging")

    def critical(self, logmessage):
        """
        Log in critical error-level.
        """
        if not self._created:
            raise EnvironmentError("clog.critical();Error; logging not created, call clog.create_logfile() at first")
        self._logger.critical(logmessage)

    def error(self, logmessage):
        """
        Log in standard error-level.
        """
        if not self._created:
            raise EnvironmentError("clog.error();Error; logging not created, call clog.create_logfile() at first")
        self._logger.error(logmessage)

    def warning(self, logmessage):
        """
        Log in warning-level.
        """
        if not self._created:
            raise EnvironmentError("clog.warning();Error; logging not created, call clog.create_logfile() at first")
        self._logger.warning(logmessage)

    def info(self, logmessage):
        """
        Log in info-level.
        """
        if not self._created:
            raise EnvironmentError("clog.info();Error; logging not created, call clog.create_logfile() at first")
        self._logger.info(logmessage)

    def debug(self, logmessage):
        """
        Log in debug-level.
        """
        if not self._created:
            raise EnvironmentError("clog.debug();Error; logging not created, call clog.create_logfile() at first")
        self._logger.debug(logmessage)

    def logfilepathname(self, logfilepath=None):
        """
        returns the currently defined 'logpath'.
         Value is set in configuration-file.
        """
        if logfilepath != None:
            self._logfilepath = logfilepath
        return self._logfilepath

    def logfilename(self, logfilename=None):
        """
        returns the currently defined 'logfilename'.
         Value is set in configuration-file.
        """
        if logfilename != None:
            self._fileonly = logfilename
            self._logfilepath = os.path.normcase(os.path.join(self._pathonly, self._fileonly))
        return self._fileonly

    def logpathname(self, logpathname=None):
        """
        returns the currently defined 'logfilename joined with 'logpath'.
         Values are set in configuration-file.
        """
        if logpathname != None:
            self._pathonly = logpathname
            self._logfilepath = os.path.normcase(os.path.join(self._pathonly, self._fileonly))
        return self._pathonly

    def loglevel(self, loglevel=None):
        """
        returns the currently defined 'loglevel' as defined in logging.py.
         Value is set in configuration-file.
        """
        if loglevel != None:
            tmp_loglevel = loglevel.upper()
            #check first possible parameters
            if tmp_loglevel in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
                if tmp_loglevel in ('CRITICAL'):
                    loglevel = logging.CRITICAL
                if tmp_loglevel in ('ERROR'):
                    loglevel = logging.ERROR
                if tmp_loglevel in ('WARNING'):
                    loglevel = logging.WARNING
                if tmp_loglevel in ('INFO'):
                    loglevel = logging.INFO
                if tmp_loglevel in ('DEBUG'):
                    loglevel = logging.DEBUG
                self._loglevel = loglevel
            else:
                self._loglevel = logging.INFO
#zs#test# print("loglevel:{0}".format(logging.getLevelName(self._loglevel)))
        return self._loglevel

#--- class clogging end ---#

################################################

if __name__ == "__main__":
    print("-------------------- do some CRC-checks ----------------------------")
    utils = cht_utils()

    print("-- check with valid 'heizgeraet' Message 1 --")
    # Heizgeraet
    # HG: 88 00 18 00 27 01 31 54 00 01 03 20 c0 01 c5 80
    #     00 01 2c ff ff ff 00 00 00 00 00 00 00 e9 00
    length = 31
    heizgeraet = [
       0x88, 0x00, 0x18, 0x00, 0x27, 0x01, 0x31, 0x54,
       0x00, 0x01, 0x03, 0x20, 0xC0, 0x01, 0xC5, 0x80,
       0x00, 0x01, 0x2C, 0xFF, 0xFF, 0xFF, 0x00, 0x00,
       0x00, 0x00, 0x00, 0x00, 0x00, 0xE9, 0x00]
    crc_ok = utils.crc_testen(heizgeraet, length)
    print("+-> OK") if crc_ok else print("+-> Error")

    print("-- check with valid 'heizgeraet' Message 2 --")
    # Heizgeraetmessage 2
    # HK: 88 00 19 00 ff fc 80 00 80 00 ff ff 00 41 00 15
    #     fa 02 97 fd 00 00 00 02 5d 3d 00 0b 51 80 00 d5 00
    length = 33
    heizgeraettestbuffer2 = [
       0x88, 0x00, 0x19, 0x00, 0xFF, 0xFC, 0x80, 0x00,
       0x80, 0x00, 0xFF, 0xFF, 0x00, 0x41, 0x00, 0x15,
       0xFA, 0x02, 0x97, 0xFD, 0x00, 0x00, 0x00, 0x02,
       0x5D, 0x3D, 0x00, 0x0B, 0x51, 0x80, 0x00, 0xD5, 0x00]
    crc_ok = utils.crc_testen(heizgeraettestbuffer2, length)
    print("+-> OK") if crc_ok else print("+-> Error")

    print("-- check with valid 'heizkreis'  Message 3 --")
    # Heizkreismessage
    # HK: 90 00 ff 00 00 6f 03 02 00 d7 00 e1 00 d8 00 23 00
    length = 17
    heizkreistestbuffer = [
       0x90, 0x00, 0xFF, 0x00, 0x00, 0x6F, 0x03, 0x02,
       0x00, 0xD7, 0x00, 0xE1, 0x00, 0xD8, 0x00, 0x23, 0x00]
    crc_ok = utils.crc_testen(heizkreistestbuffer, length)
    print("+-> OK") if crc_ok else print("+-> Error")

    print(" --  -- check with wrong values --  --")

    print(" -- check with wrong bufferlength on 'heizgeraet' Message --")
    length = 30
    crc_ok = utils.crc_testen(heizgeraettestbuffer2, length)
    print("+-> OK") if crc_ok else print("+-> Error seen and so it's OK")

    print("-------------------- do some transceiver-header-checks -------------")
    transceiver_header = [0x23, 0x48, 0x52, 0x11, 1, 0, 4]
    if utils.Is_TransceiverHeader(transceiver_header):
        print("Transceiver_message found; msg-size:{0}".format(utils.Transceiver_msg_size()))
        print("+-> OK")
    else:
        print("No Transceiver_message found!")
        print("+-> Error")
    wrong_transceiver_header = [0x23, 0x23, 0x48, 0x52, 0x11, 1, 0, 4]
    if utils.Is_TransceiverHeader(wrong_transceiver_header):
        print("Transceiver_message found; msg-size:{0}".format(utils.Transceiver_msg_size()))
        print("+-> Error")
    else:
        print("No Transceiver_message found! msg-size:{0}".format(utils.Transceiver_msg_size()))
        print("+-> OK")

    import os
    import time

    print("-------------------- do some logging-checks ------------------------")
    #first default logging
    log = clog()
    log.create_logfile()
    if not os.path.exists(log.logfilepathname()):
        print(" could not create logfile:{0}".format(log.logfilepathname()))
        raise
    else:
        print(" OK; logfile:'{0}' created".format(log.logfilepathname()))
    log.critical("Is critical")
    log.error("Is error")
    log.warning("Is warning")
    log.info("Is info")
    log.debug("debug must not be logged")

    #second debug logging
    logdebug = clog()
    logdebug.create_logfile(logfilepath="./debug_logfile.log", loglevel=logging.DEBUG, loggertag="debug_me")
    if not os.path.exists(logdebug.logfilepathname()):
        print(" could not create logfile:{0}".format(logdebug.logfilepathname()))
        raise
    else:
        print(" OK; logfile:'{0}' created".format(logdebug.logfilepathname()))
    logdebug.critical("Is critical")
    logdebug.error("Is error")
    logdebug.warning("Is warning")
    logdebug.info("Is info")
    logdebug.debug("Is debug-level")

    print("Please check the content of:")
    print(" default-file:{0}".format(log.logfilepathname()))
    print(" debug  -file:{0}".format(logdebug.logfilepathname()))
