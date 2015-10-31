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
# Ver:0.1.7  / Datum 25.02.2015 first release
# Ver:0.1.7.1/ Datum 04.03.2015 word:'Error;' removed from cportwrite()
#              logging-handling added from ht_utils
# Ver:0.1.7.2/ Datum 31.10.2015 __waitfor_client_register method changed
#              for handling clients which not sending the devicetype
#################################################################

import socketserver, socket, serial
import threading, queue
import ht_utils, logging
import xml.etree.ElementTree as ET
import time, os

__author__  = "Norbert S <junky-zs@gmx.de>"
__status__  = "draft"
__version__ = "0.1.7.1"
__date__    = "04 Maerz 2015"

#---------------------------------------------------------------------------
#   targettype related stuff
#---------------------------------------------------------------------------
#
TT_SERVER="SERVER"
TT_CLIENT="CLIENT"

#---------------------------------------------------------------------------
#   devicetype related stuff
#---------------------------------------------------------------------------
#
# devicetype-definitions used in config.xml and proxy-classes
#  client-registration and com-/tty-port select is done
#  with this stuff
#
INT_DT_SERVER = 30
INT_DT_MODEM  = 20
INT_DT_RX     = 10
INT_DT_NOTSET =  0

DT_SERVER = 'SERVER'
DT_MODEM  = 'MODEM'
DT_RX     = 'RX'
DT_NOTSET = 'NONE'

_devicetypes = {
    DT_SERVER    : INT_DT_SERVER,
    DT_MODEM     : INT_DT_MODEM,
    DT_RX        : INT_DT_RX,
    DT_NOTSET    : INT_DT_NOTSET,
    INT_DT_SERVER: DT_SERVER,
    INT_DT_MODEM : DT_MODEM,
    INT_DT_RX    : DT_RX,
    INT_DT_NOTSET: DT_NOTSET,
}
def _getDeviceType(devicetype):
    """Fkt returns devicetype as string
    """
    return "{0}".format(_devicetypes.get(devicetype))

#---------------------------------------------------------------------------
#   priority-queue related stuff
#---------------------------------------------------------------------------
#
# definitions for using priority-queues
#   lower values are defined as higher priorities
#
#   remark:
#     these values are currently not realy used, but will be in the future
#
INT_PRIO_LOW    = 40
INT_PRIO_MEDIUM = 20
INT_PRIO_HIGH   = 10
INT_PRIO_URGEND =  0


class cportread(threading.Thread):
    """class 'cportread' for reading serial asynchronous data from already
       opened port
    """
    global _ClientHandler

    def __init__(self, port, devicetype):
        threading.Thread.__init__(self)
        self.__threadrun=True
        self.__port=port
        self.__devicetype=devicetype
        self.__queueprio=INT_PRIO_MEDIUM

    def __del__(self):
        self.stop()
        
    def run(self):
        _ClientHandler.log_info("cportread() ;thread start; devicetype:{0}".format(self.__devicetype))
        while self.__threadrun:
            if _ClientHandler.get_clientcounter() > 0:
                try:
                    value=self.__port.read(5)
                except:
                    _ClientHandler.log_critical("cportread();Error;couldn't use/read required port")
                    self.__threadrun=False
                try:
                    for clientQueue in _ClientHandler._txqueue.items():
                        #put comport readvalue in any connected client-queue
                        #  clientQueue[0]:=Client-ID; clientQueue[1]:=queue
                        #    put value into queue
                        clientQueue[1].put(value)
                except:
                    _ClientHandler.log_info("Client-ID:{0};cportread();couldn't write to queue".format(clientQueue[0]))
            else:
                time.sleep(0.5)

        _ClientHandler.log_critical("cportread() ;thread end; devicetype:{0}".format(self.__devicetype))

    def stop(self):
        self.__threadrun=False

class cportwrite(threading.Thread, ht_utils.cht_utils):
    """class 'cportwrite' for writing serial asynchronous data to already
       opened port
    """
    global _ClientHandler

    def __init__(self, port, devicetype):
        threading.Thread.__init__(self)
        ht_utils.cht_utils.__init__(self)
        self.__threadrun=True
        self.__port=port
        self.__devicetype=devicetype
        self.__queueprio=INT_PRIO_MEDIUM
        

    def __del__(self):
        self.stop()
        
    def run(self):
        """bytes are read from queue, searched for start-tag '#' and length of
            following bytes. Then all bytes are written to comport
            # following queue-message_structur is supported:
            #   tag  length   class   detail  option  databytes.....
            #    #   <size>   ! or ?   d       o       bytes.....
            #      size := amount of databytes including class, detail and option but without starttag
            #
        """
        _ClientHandler.log_info("cportwrite();thread start; devicetype:{0}".format(self.__devicetype))
        while self.__threadrun:
            if _ClientHandler.get_clientcounter() > 0:
                #preset local buffers
                self.__starttag_found=False
                self.__length        =0
                readbuffer=[0,]
                try:
                    # 1. search for start-tag '#'
                    while not self.__starttag_found and self.__threadrun and (_ClientHandler.get_clientcounter() > 0):
                        #get comport writevalues from any connected client-queue
                        for clientQueue in _ClientHandler._rxqueue.items():
                            try:
                                # use get() with timeout
                                readbuffer=clientQueue[1].get(timeout=0.2)
                                clientQueue[1].task_done()
                                if readbuffer[0] == 0x23:
                                    self.__starttag_found=True
                                    break
                            except:
                                # timeout occured-> no exception
                                pass
                            
                    # 2. now get msg-length from stream (over all length including headerbytes but without starttag)
                    if self.__starttag_found and len(readbuffer) > 1:
                        self.__length=readbuffer[1]

                    # 3. now read rest of msg-headerbytes from stream and set resulting payload-length
                    if self.__starttag_found and len(readbuffer) > 4:
                        msg_class =readbuffer[2]
                        msg_detail=readbuffer[3]
                        msg_option=readbuffer[4]
                        if self.__length >= 3:
                            self.__length -= 3
                        else:
                            self.__length = 0
                    else:
                        self.__starttag_found=False
                        
                    self.__msgbytes=[]
                    try:
                        if self.__starttag_found and self.__length > 0:
                            self.__msgbytes.extend(readbuffer[5:self.__length+5])
                    except:
                        raise
                        
                    # 4. send message-class/detail/option and (data-bytes if available) to transceiver_if
                    if self.__starttag_found:
                        try:
                            self.__send_2_transceiver_if(clientQueue[0], self.__msgbytes, msg_class, msg_detail, msg_option)
                        except:
                            _ClientHandler.log_critical("Client-ID:{0};cportwrite();couldn't write to port".format(clientQueue[0]))
                            self.__threadrun=False
                            self.__starttag_found=False
                except:
                    _ClientHandler.log_info("Client-ID:{0};cportwrite();couldn't read from queue".format(clientQueue[0]))
            else:
                time.sleep(0.2)
            
        _ClientHandler.log_critical("cportwrite();thread end; devicetype:{0}".format(self.__devicetype))

    def stop(self):
        self.__threadrun=False

    def __send_2_transceiver_if(self, ClientID, data_in, msg_class=0x21, detail=0x53, option=0):
        # header to be send:  <#  ,  msg_class:=! , detail:=S, option, data-length>
        if len(data_in):
            header = [0x23,msg_class,detail,option,len(data_in)]
            data   = header+data_in
        else:
            header = [0x23,msg_class,detail,option,0]
            data   = header

        #generate crc and add crc-byte
        try:
            crc=self.make_crc(data, len(data))
            data += [crc]
        except:
            _ClientHandler.log_critical("Client-ID:{0};cportwrite().__send_2_transceiver_if;Error;couldn't make crc".format(ClientID))
            raise

        try:
            index=0
            while index < len(data):
                self.__port.write(bytearray([data[index]]))
                self.__port.flushOutput()
                time.sleep(0.005)
                _ClientHandler.log_debug("Client-ID:{0};cportwrite();value:{1:02x}".format(ClientID, data[index]))
                index += 1
        except:
            _ClientHandler.log_critical("Client-ID:{0};cportwrite().__send_2_transceiver_if;Error;couldn't write to port".format(ClientID))


class cht_transceiver_if(threading.Thread):
    """class 'cht_transceiver_if' as serial asynchronous interface to 'ht_transceiver'
       The used port must be accessable and is used exclusive one time.
       All received serial data are written to queue(s),(unique for every socket-client)
         this is handled with class: cportread
       All transmitted serial data are read from queue(s),(unique for every socket-client)
         this is handled with class: cportwrite
    """
    global _ClientHandler
    def __init__(self, serialdevice="/dev/ttyUSB0", baudrate=19200, devicetype=DT_RX):
        threading.Thread.__init__(self)
        self.__serialdevice = str(serialdevice)
        self.__baudrate     = baudrate
        self.__devicetype   = devicetype
        self.__port=None
        self.__threadrun=True
    
    def __del__(self):
        self.stop()
        if self.__port != None:
            self.__port.close()

    def run(self):
        #open serial port for reading HT-data
        try:
            self.__port = serial.Serial(self.__serialdevice, self.__baudrate)
            #disabeld, no timeout  self.__port.setInterCharTimeout(0.1) #VTIME; set to 0.1*1sec
        except:
            _ClientHandler.log_critical("cht_transceiver_if();Error;couldn't open requested device:{0}".format(self.__serialdevice))
            self.__threadrun=False
            raise
        
        self.__comtx_thread=cportwrite(self.__port, self.__devicetype)
        self.__comtx_thread.start()
        self.__comrx_thread=cportread(self.__port, self.__devicetype)
        self.__comrx_thread.start()
        
        while self.__threadrun:
            time.sleep(1)

    def stop(self):
        self.__com_txthread.stop()
        self.__com_rxthread.stop()
        self.__threadrun=False
               

class csocketsendThread(threading.Thread):
    """class 'csocketsendThread' used for sending data from queue to
       already connected socket
    """
    def __init__(self, request, queue):
        threading.Thread.__init__(self)
        self._queue  =queue
        self._request=request
        self.__threadrun=True
        self.__queueprio=INT_PRIO_MEDIUM

    def __del__(self):
        self.__threadrun=False
        #clear queue
        while self._queue.qsize() > 0:
            self._queue.get_nowait()

    def run(self):
        _ClientHandler.log_info("csocketsendThread(); socket.send thread start")
        self._tx=None
        while self.__threadrun==True:
            try:
                # get queue-value in blocking mode
                self._tx=self._queue.get(True)
                self._queue.task_done()
            except:
                self.__threadrun=False
                _ClientHandler.log_critical("csocketsendThread();Error on queue.get()")
                raise

            try:
                self._request.sendall(bytes(self._tx))
            except:
                self.__threadrun=False
                _ClientHandler.log_critical("csocketsendThread();Error on socket.send")
                raise
                                        
        _ClientHandler.log_info("csocketsendThread(); socket.send thread terminated")
        
    def stop(self):
        self.__threadrun=False

class cClientHandling(threading.Thread, ht_utils.clog):
    """class 'cClientHandling' used for add and remove clients to / from queues and
       threads. logging-methods are available for different logging-levels.
    """
    def __init__(self, logfilepath="./proxy_if.log", tcp_ip_type=TT_SERVER, loglevel=logging.INFO):
        threading.Thread.__init__(self)
        # init/setup logging-file
        ht_utils.clog.__init__(self)
        self._logging=ht_utils.clog.create_logfile(self, logfilepath=logfilepath, loglevel=loglevel, loggertag=tcp_ip_type)
        
        self._indexcounter=0
        self._clientcounter=0
        self._lock=threading.Lock()
        self._rxqueue={}
        self._txqueue={}
        self._thread={}
        
    def log_critical(self, logmessage):
        self._logging.critical(logmessage)
        
        
    def log_error(self, logmessage):
        self._logging.error(logmessage)
        
    def log_warning(self, logmessage):
        self._logging.warning(logmessage)
        
    def log_info(self, logmessage):
        self._logging.info(logmessage)
        
    def log_debug(self, logmessage):
        self._logging.debug(logmessage)
        
    def inc_indexcounter(self):
        self._lock.acquire()
        self._indexcounter+=1
        self._lock.release()

    def get_indexcounter(self):
        self._lock.acquire()
        counter=self._indexcounter
        self._lock.release()
        return counter

    def inc_clientcounter(self):
        self._lock.acquire()
        self._clientcounter+=1
        self._lock.release()

    def dec_clientcounter(self):
        self._lock.acquire()
        self._clientcounter-=1
        self._lock.release()

    def get_clientcounter(self):
        self._lock.acquire()
        counter=self._clientcounter
        self._lock.release()
        return counter

    def add_client(self, clientID, request):
        self._rxqueue.update({clientID:queue.Queue()})
        self._txqueue.update({clientID:queue.Queue()})
        
        txThread=csocketsendThread(request, self._txqueue.get(clientID))
        self._thread.update({clientID:txThread})
        txThread.start()
        self._logger.info("Client-ID:{0}; added; number of clients:{1}".format(clientID, self._clientcounter))

    def remove_client(self, clientID):
        txThread=self._thread.pop(clientID)
        txThread.stop()
        queue=self._rxqueue.pop(clientID)
        while queue.qsize() > 0:
            queue.get_nowait()
        queue=self._txqueue.pop(clientID)
        while queue.qsize() > 0:
            queue.get_nowait()
        self._logger.info("Client-ID:{0}; removed; number of clients:{1}".format(clientID, self._clientcounter))


class cht_RequestHandler(socketserver.BaseRequestHandler):
    """
    """
    global _ClientHandler

    def handle(self):
        self._rx=None
        self._client_devicetype=None
        self.__queueprio=INT_PRIO_HIGH
        try:
            addrc, portc = self.client_address
            addrs, ports = self.server.server_address
            _ClientHandler.log_info("Client-ID:{0}; {1} connected".format(self._myownID, (addrc, portc)))
            _ClientHandler.log_info("Server   :{0}".format((addrs,ports)))
        except:
            addrc, portc = self.client_address
            _ClientHandler.log_critical("Client-ID:{0}; {1} No connection possible".format(self._myownID, (addrc, portc)))
            raise
        # wait for client registration
        self.__waitfor_client_register()
        # add client and start threads
        _ClientHandler.add_client(self._myownID, self.request)
        self._rxqueue=_ClientHandler._rxqueue.get(self._myownID)
        
        _ClientHandler.log_info("Client-ID:{0}; cht_RequestHandler(); socket.receive thread start".format(self._myownID))
        while True:
            try:
                self._rx=self.request.recv(60)
            except:
                _ClientHandler.log_info("Client-ID:{0}; {1} disconnected".format(self._myownID, (addrc, portc)))
                break
            if self._rx:
                # put socket-data in queue
                self._rxqueue.put(self._rx)
                _ClientHandler.log_debug("Client-ID:{0}; recv:{1}".format(self._myownID, self._rx))
            else:
                _ClientHandler.log_info("Client-ID:{0}; {1} disconnected".format(self._myownID, (addrc, portc)))
                break


    def __waitfor_client_register(self):
        self.request.settimeout(5)
        try:
            devicetypetmp=self.request.recv(20)
            self._client_devicetype = devicetypetmp.decode('utf-8')
            _ClientHandler.log_info("Client-ID:{0}; register(); got devicetype:{1}".format(self._myownID,self._client_devicetype))
            #send client-ID to client
            sendtemp=str(self._myownID)
            self.request.sendall(sendtemp.encode("utf-8"))
        except socket.timeout:
            _ClientHandler.log_critical("Client-ID:{0}; Timeout occured, no devicetype was send".format(self._myownID))
            raise
        except socket.error as e:
            # Something else happened, handle error, exit, etc.
            _ClientHandler.log_critical("Client-ID:{0}; error '{1}' on socket.recv or socket.send".format(self._myownID, e))
            raise
        except Exception as e:
            _ClientHandler.log_critical("Client-ID:{0}; unkown error '{1}'".format(self._myownID,e))
            raise
        finally:
            self.request.settimeout(None)
            
        
    def setup(self):
        _ClientHandler.inc_indexcounter()
        _ClientHandler.inc_clientcounter()
        self._myownID=_ClientHandler.get_indexcounter()
        
    def finish(self):
        _ClientHandler.dec_clientcounter()
        _ClientHandler.remove_client(self._myownID)

class cproxyconfig():
    """class 'cproxyconfig', is used for proxy_configuration.
       ip_address, port_number etc. comes from the xml-configuration-file.
        # data-structur: '_configdata':
        #   {target    :[{valuename  :arrayindex},[value1,value2,...]]}
        #
        # data-structur: '_configtransceiver':
        #   {devicename:[{dparam_name:arrayindex},[dvalue1,dvalue2,...]]}
        #
        #    where : target      -> 'SERVER' or 'CLIENT'
        #            valuename   -> as used in configfile
        #            value       -> are from config-file
        #            devicename  -> 'RX' or 'MODEM'
        #            dparam_name -> device-parametername  from config-file
        #            dparam_value-> device-parametervalue from config-file
        #
    """
    global _ClientHandler
    
    _configdata={}
    _configtransceiver={}
    _configtransceiver_devicenames={}
    def __init__(self, config_target=TT_SERVER, devicetype=DT_RX):
        self.__configfilename=None
        self.__root = None
        self.__configtarget  = config_target.upper()
        self.__devicetype    = devicetype
        
    def read_config(self,xmlconfigpathname):
        try:
            self.__configfilename=xmlconfigpathname
            self.__tree = ET.parse(xmlconfigpathname)
        except (NameError,EnvironmentError,IOError) as e:
##            print("cproxyconfig().read_config();Error;{0} on file:'{1}'".format(e.args[0], self.__configfilename))
            _ClientHandler.log_critical("cproxyconfig().read_config();Error;{0} on file:'{1}'".format(e, self.__configfilename))
            raise
        else:            
            try:
                self.__root = self.__tree.getroot()
                self.__transceiver_numbers=int(self.__root.find('transceiver_numbers').text)
                # currently limited to 1
                if self.__transceiver_numbers > 1:
                    self.__transceiver_numbers = 1
                    
                # find server-/client-configuration values
                if self.__configtarget in (TT_SERVER):
                    searchtarget='proxy_server'
                    storetarget =self.__configtarget
                    cproxyconfig._configdata.update({storetarget:[{}]})
                else:
                    searchtarget='proxy_client'
                    storetarget = DT_RX

                for proxy_part in self.__root.findall(searchtarget):
                    # add new item and value, index is the current array-length
                    # and is set to dir{itemname:index}
                    if self.__configtarget in (TT_CLIENT):
                        item='devicetype'
                        devicetype=proxy_part.find(item).text.upper()
                        if devicetype in (DT_MODEM):
                            storetarget=DT_MODEM
                        else:
                            storetarget=DT_RX
                            
                        cproxyconfig._configdata.update({storetarget:[{}]})
                        cproxyconfig._configdata[storetarget][0].update({str(item).upper():devicetype})
                        
                        
                    item='serveraddress'
                    cproxyconfig._configdata[storetarget][0].update({str(item).upper():proxy_part.find(item).text})
                    item='servername'
                    cproxyconfig._configdata[storetarget][0].update({str(item).upper():proxy_part.find(item).text})
                    item='portnumber'
                    cproxyconfig._configdata[storetarget][0].update({str(item).upper():proxy_part.find(item).text})
                    item='logfilepath'
                    cproxyconfig._configdata[storetarget][0].update({str(item).upper():proxy_part.find(item).text})

                if self.__configtarget in (TT_SERVER):
                    for ht_transceiver in proxy_part.findall('ht_transceiver_if'):
                        devicename=ht_transceiver.attrib['devicename']
                        if not devicename in cproxyconfig._configtransceiver_devicenames.keys():
                            # setup 'devicename' and 'init.flag:=0'
                            cproxyconfig._configtransceiver_devicenames.update({devicename:0})
                        #initialise 'devicename'-dictionary
                        cproxyconfig._configtransceiver.update({devicename:[{}]})
                        #fill in parameters in dictionary
                        for parameter in ht_transceiver.findall('parameter'):
                            item='serialdevice'
                            cproxyconfig._configtransceiver[devicename][0].update({str(item).upper():parameter.find(item).text})
                            item='baudrate'
                            cproxyconfig._configtransceiver[devicename][0].update({str(item).upper():parameter.find(item).text})
                            item='config'
                            cproxyconfig._configtransceiver[devicename][0].update({str(item).upper():parameter.find(item).text})
                            
                        item='devicetype'
                        cproxyconfig._configtransceiver[devicename][0].update({str(item).upper():ht_transceiver.find(item).text})

                        item='deviceaddress_hex'
                        if devicename.upper() != 'RX':
                            cproxyconfig._configtransceiver[devicename][0].update({str(item).upper():ht_transceiver.find(item).text})
                        else:                                    
                            cproxyconfig._configtransceiver[devicename][0].update({str(item).upper():'None'})
            except:
                raise
            
    def serveraddress(self):
        try:
            rtn=cproxyconfig._configdata[self.__devicetype][0].get('SERVERADDRESS')
        except:
            rtn=None
        return rtn
    
    def servername(self):
        try:
            rtn=cproxyconfig._configdata[self.__devicetype][0].get('SERVERNAME')
        except:
            rtn=None
        return rtn

    def portnumber(self):
        try:
            rtn=cproxyconfig._configdata[self.__devicetype][0].get('PORTNUMBER')
        except:
            rtn=0
        return int(rtn)

    def logfilepath(self):
        try:
            rtn=cproxyconfig._configdata[self.__devicetype][0].get('LOGFILEPATH')
        except:
            rtn=None
        return os.path.normcase(rtn)

    def transceiver_serialdevice(self, devicename=None):
        try:
            if devicename==None:
                rtn=cproxyconfig._configtransceiver[self.__devicetype][0].get('SERIALDEVICE')
            else:
                rtn=cproxyconfig._configtransceiver[devicename][0].get('SERIALDEVICE')
        except:
            rtn=None
            raise
        return rtn

    def transceiver_baudrate(self, devicename=None):
        try:
            if devicename==None:
                rtn=cproxyconfig._configtransceiver[self.__devicetype][0].get('BAUDRATE')
            else:
                rtn=cproxyconfig._configtransceiver[devicename][0].get('BAUDRATE')
        except:
            rtn=None
        return int(rtn)

    def transceiver_config(self, devicename=None):
        try:
            if devicename==None:
                rtn=cproxyconfig._configtransceiver[self.__devicetype][0].get('CONFIG')
            else:
                rtn=cproxyconfig._configtransceiver[devicename][0].get('CONFIG')
        except:
            rtn=None
        return rtn

    def transceiver_devicetype(self, devicename=None):
        try:
            if devicename==None:
                rtn=cproxyconfig._configtransceiver[self.__devicetype][0].get('DEVICETYPE')
            else:
                rtn=cproxyconfig._configtransceiver[devicename][0].get('DEVICETYPE')
        except:
            rtn=None
        return rtn
    
    def transceiver_deviceaddress(self, devicename=None):
        try:
            if devicename==None:
                rtn=cproxyconfig._configtransceiver[self.__devicetype][0].get('DEVICEADDRESS_HEX')
            else:
                rtn=cproxyconfig._configtransceiver[devicename][0].get('DEVICEADDRESS_HEX')
        except:
            rtn=None
        return rtn

    def devicename_keys(self):
        return list(cproxyconfig._configtransceiver_devicenames.keys())

    def devicename_initflag(self, key, initflag=None ):
        if initflag != None:
            cproxyconfig._configtransceiver_devicenames.update({key:initflag})
        return cproxyconfig._configtransceiver_devicenames.get(key)

class cht_proxy_daemon(threading.Thread, cproxyconfig):
    """class 'cht_proxy_daemon', create object using this as server-daemon.
       ip_address and port_number comes from configuration-file.
    """
    global _ClientHandler
    
    def __init__(self, configfile="./etc/config/ht_proxy_cfg.xml", loglevel=logging.INFO):
        threading.Thread.__init__(self)
        tcp_ip_type=TT_SERVER
        cproxyconfig.__init__(self, tcp_ip_type, devicetype=DT_SERVER)
        self._configfile =configfile
        self._logfile    ="default_proxy.log"
        self._ip_address="localhost"
        self._port_number=8088
        self._server=None
        self._ht_transceiver_if=[]
        
        #read configfile
        try:
            self.read_config(self._configfile)
            self._port_number = self.portnumber()
            self._logfile     = self.logfilepath()
            # check for available/writable folder
            #   if not available, create the folder
            abs_pathonly=os.path.abspath(os.path.dirname(self._logfile))
            if not os.path.exists(abs_pathonly):
                try:
                    os.makedirs(abs_pathonly)
                except:
                    print("Sorry, can't create that folder: {0}".format(abs_pathonly))
                    print(" What can we do now with that bloody folder?")
                    print(" The Best and the Rest I can do -> fire and raise !")
                    raise
            else:
                # check for writability
                if not os.access(abs_pathonly, os.W_OK):
                    print("Houston, we have got a problem")
                    print(" Can't write to that folder: {0}".format(abs_pathonly))
                    print(" The Best and the Rest I can do -> fire and forget !")
                    raise
                    
                    
            global _ClientHandler
            _ClientHandler=cClientHandling(self._logfile, loglevel=loglevel)
            _ClientHandler.log_info("----------------------")
            _ClientHandler.log_info("cht_proxy_daemon init")
            if not self.servername() == None:
                self._ip_address=self.servername()
            else:
                if not self.serveraddress() == None:
                    self._ip_address=self.serveraddress()
                else:
                    _ClientHandler.log_info("cht_proxy_daemon(); common serveraddress used")
                    self._ip_address=""
        except:
            _ClientHandler=cClientHandling(self._logfile, loglevel=loglevel)
            _ClientHandler.log_critical("cht_proxy_daemon();error can't get/set configurationvalues")
            raise

    def __del__(self):
        while len(self._ht_transceiver_if):
            self._ht_transceiver_if.pop().stop()

    def run(self):
        _ClientHandler.log_info("cht_proxy_daemon start as proxy-server:'{0}';port:'{1}'".format(self._ip_address, self._port_number))
        _ClientHandler.log_info("logfile:'{0}'".format(self._logfile))
        _serialdevice_initialised=[]

        for devicename in self.devicename_keys():
            if self.devicename_initflag(devicename) == 0:
                #check for already initialised serial device, if not then start transceiver_if
                serialdevice   = self.transceiver_serialdevice(devicename)
                if not serialdevice in (_serialdevice_initialised):
                    baudrate       = self.transceiver_baudrate(devicename)
                    devicetype     = self.transceiver_devicetype(devicename)
                    #start transceiver-if for that serial device
                    transceiver_if = cht_transceiver_if(serialdevice, baudrate, devicetype)
                    #add used serial-device to list
                    _serialdevice_initialised.append(serialdevice)
                    #add transceiver to list
                    self._ht_transceiver_if.append(transceiver_if)
                    transceiver_if.setDaemon(True)
                    transceiver_if.start()
                    
                #set initialise-flag for devicename
                self.devicename_initflag(devicename, 1)

                
        
        try:
            self._server=socketserver.ThreadingTCPServer((self._ip_address, self._port_number), cht_RequestHandler)
            self._server.serve_forever()
            _ClientHandler.log_critical("cht_proxy_daemon terminated")
            _ClientHandler.log_info("---------------------------")
            raise
        except:
            _ClientHandler.log_critical("cht_proxy_daemon terminated")
            _ClientHandler.log_info("---------------------------")
            raise
        
    def get_indexcounter(self):
        global _ClientHandler
        return _ClientHandler.get_indexcounter()

    def get_clientcounter(self):
        global _ClientHandler
        return _ClientHandler.get_clientcounter()

    

#--- class cht_proxy_if end ---#

class cht_socket_client(cproxyconfig, ht_utils.clog):
    """class 'cht_socket_client', create object to connect to server
       using ip_address and port_number from configuration-file.
    """
    def __init__(self, configfile="./etc/config/ht_proxy_cfg.xml", devicetype=DT_RX, loglevel=logging.INFO):
        tcp_ip_type=TT_CLIENT
        self._devicetype =devicetype
        cproxyconfig.__init__(self, tcp_ip_type, self._devicetype)
        self._configfile =configfile
        self._ip_address ="192.168.2.1"
        self._port_number=8088
        self._logfile    ="./ht_client_default.log"
        self._loglevel   = loglevel
        self._loggertag  = tcp_ip_type
        self._clientID   =0
        
        self._socket=None
        #read configfile
        try:
            self.read_config(self._configfile)
        except:
            # setup logging-file only for this exception
            _handler=logging.handlers.RotatingFileHandler(self._logfile, maxBytes=1000000)
            _frm = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%d.%m.%Y %H:%M:%S")
            _handler.setFormatter(_frm)
            self._logging     = logging.getLogger(tcp_ip_type)
            self._logging.addHandler(_handler)
            self._logging.setLevel(loglevel)
            
            self.log_critical("cht_socket_client();error can't get configurationvalues")
            raise
        
        try:
            self._port_number = self.portnumber()
            self._logfile     = self.logfilepath()

            # setup logging-file using class: ht_utils.clog
            ht_utils.clog.__init__(self)
            self._logging=self.create_logfile(self._logfile, self._loglevel, self._loggertag)
            
            self.log_info("----------------------")
            self.log_info("cht_socket_client init")
            if not self.servername() == None:
                self._ip_address=self.servername()
            else:
                if not self.serveraddress() == None:
                    self._ip_address=self.serveraddress()
                else:
                    self.log_critical("cht_socket_client.__init__(); error:no serveraddress defined")
                    raise ValueError("cht_socket_client.__init__(); error:no serveraddress defined")
                
        except:
            self.log_critical("cht_socket_client();error can't set configurationvalues")
            raise

        try:
            self._socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._ip_address, self._port_number))
            self.log_info("connected to server:'{0}';port:'{1}'".format(self._ip_address, self._port_number))
            self.log_info("logfile:'{0}'".format(self._logfile))
        except:
            self.log_critical("cht_socket_client.__init__();error:can't connect to socket")
            raise

        #send registration to proxy-server and receive client-related informations from server
        self.__registration();
        self.log_info("Client-ID:{0}; registered with devicetype:'{1}'".format(self._clientID, self._devicetype))
        
    def __del__(self):
        if self._socket != None:
            self._socket.close()
            self.log_info("Client-ID:{0}; socket closed".format(self._clientID))

    def __registration(self):
        try:
            # send devicetype to server
            devicetype=bytearray(self._devicetype.encode("utf-8"))
            self.write(devicetype)
            
            # read answer from server (client-ID) and store it
            self._clientID=self._socket.recv(10).decode('utf-8')
            ## only for test## print("client got ID:{0}".format(self._clientID))
        except:
            self._socket.close()
            self.log_critical("cht_socket_client.__registration();error:can't register to master")
            raise

    def run(self):
        try:
            self.log_info("Client-ID:{0}; cht_socket_client run".format(self._clientID))
            while True:
                antwort=self._socket.recv(1)
                print("{0}".format(antwort))
        except:
            self._socket.close()
            self.log_critical ("Client-ID:{0} ; cht_socket_client.run(); error on socket.recv".format(self._clientID))
            raise

    def close(self):
        if self._socket != None:
            self._socket.close()
            self._socket = None
            self.log_info("Client-ID:{0}; socket closed".format(self._clientID))

    def read(self, size=1):
        """Read size bytes from the connected socket. It will block
           until the requested number of bytes are read.
        """
        if self._socket==None:
            raise ("Client-ID:{0}; cht_socket_client.read(); error:socket not initialised".format(self._clientID))
        read=bytearray()
        while len(read) < size:
            try:
                buffer=self._socket.recv(size)
            except:
                self._socket.close()
                self.log_critical("Client-ID:{0}; cht_socket_client.read(); error on socket.recv".format(self._clientID))
                raise 
            
            if not buffer:
                self._socket.close()
                self.log_critical("Client-ID:{0}; cht_socket_client.read(); peer closed socket".format(self._clientID))
                raise 
            else:
                read.extend(buffer)
        
        return bytes(read)

    def write(self, data):
        """write data to connected socket. It will block
           until all data is written.
        """
        if self._socket==None:
            self.log_critical("Client-ID:{0}; cht_socket_client.write(); socket not initialised".format(self._clientID))
            raise
        try:
            self._socket.sendall(bytes(data))
        except:
            self.log_critical("Client-ID:{0}; cht_socket_client.write(); error on socket.sendall".format(self._clientID))
            raise
            
    def log_critical(self, logmessage):
        self._logging.critical(logmessage)
        
    def log_error(self, logmessage):
        self._logging.error(logmessage)
        
    def log_warning(self, logmessage):
        self._logging.warning(logmessage)
        
    def log_info(self, logmessage):
        self._logging.info(logmessage)
        
    def log_debug(self, logmessage):
        self._logging.debug(logmessage)
        
#--- class cht_socket_client end ---#
            
    
    
################################################

if __name__ == "__main__":
    import time

    configfile="./../etc/config/4test/ht_proxy_cfg_test.xml"
    
    print("----- do some daemon-server-checks with connected client -----")
    print("   -- start socket.server --")
    ht_proxy=cht_proxy_daemon(configfile)
    ht_proxy.start()
    print("   -- start socket.client --")
    client=cht_socket_client(configfile, devicetype=DT_MODEM) 
    time.sleep(1)
    # data-stream send to ht_transceifer_if: '#' ,'!' ,'S',option, length(payload)
    #   data = [0x23,0x21,0x53,0,0]
    # data-stream to be send on socket : '#' , <length> ,'!' ,'S',option
    print("     -- write 5 bytes to proxy-server for test --")
    data = [0x23,3,0x21,0x53,0]
    client.write(data)
    time.sleep(1)
    
    print("     -- cylic send reconfigure-commands to transceiver_if --")
    # data-stream send to ht_transceifer_if: '#' ,'!' ,'M', 0xF0, 0
    #   data = [0x23,0x21,0x53,0xF0,0]
    # data-stream to be send on socket : '#' , <length> ,'!' ,'M',0xF0
    reset_command = [0x23,3,0x21,0x4D,0xF0]
    # data-stream for config Mode 1    : '#' , <length> ,'!' ,'C',1,1
    cfg_nosend_command = [0x23,4,0x21,0x43,1,1]
    # data-stream for config Mode 3    : '#' , <length> ,'!' ,'C',1,3
    cfg_fullsend_command = [0x23,4,0x21,0x43,1,3]

    while True:
        print("     -->  command: config Mode 1 to ht_ransceiver!")
        client.write(cfg_nosend_command)
        time.sleep(1)
        print("     -->  command: reset to ht_transceiver!")
        client.write(reset_command)
        time.sleep(9)
        print("     -->  command: config Mode 3 to ht_ransceiver!")
        client.write(cfg_fullsend_command)
        time.sleep(1)
        print("     -->  command: reset to ht_transceiver!")
        client.write(reset_command)
        time.sleep(9)
