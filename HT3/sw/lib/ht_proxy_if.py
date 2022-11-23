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
# Ver:0.1.7.3/ Datum 03.12.2019 Issue:'Deprecated property InterCharTimeout #7'
#                                port.setInterCharTimeout() removed
# Ver:0.1.8    2021-02-19 Portnumber changed to 48088
# Ver:0.2      2022-11-22 ip_address() added.
#                           redesign of exception-handling
#                           modifications for issue:#23
#################################################################

import socketserver, socket, serial
import threading, queue 
import ht_utils, logging
import xml.etree.ElementTree as ET
import time, os
from threading import Condition

__author__  = "junky-zs"
__status__  = "draft"
__version__ = "0.2"
__date__    = "2022-11-22"

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

class cthread_info(object):
    """ class 'cthread_info' used to write thread-trace infos to file.
    """
    counter = 0
    thread_lock = threading.Lock()
    # flag for:
    ## logging to file := True or
    ## print on stdout := False
    log2file_flag = True
    
    def __init__(self):
        self.__threadrun=True
        self.__queue = queue.Queue()
        cthread_info.counter = 0
        self.__logfileObj = None
        if cthread_info.log2file_flag:
            # create logfile
            logfilename = "ht_proxy_thread_debug.log"
            try:
                self.__logfileObj = open("./../var/log/{}".format(logfilename), "a")
            except:
                self.__logfileObj = open("./var/log/{}".format(logfilename), "a")

    def __del__(self):
        if self.__logfileObj != None:
            self.__logfileObj.close()
        self.stop()

    def stop(self):
        """ stop of currently running thread.
        """
        self.__threadrun=False

    def add(self, thread_handle):
        """ (thread-info with it's id-value) send with queue to the
            'thread_debug' - thread as 'added'-thread info.
        """
        self.__inc_counter()
        info_tuple = (id(thread_handle), "   add", thread_handle, self._countervalue(), threading.active_count())
        self.__queue.put(info_tuple)

    def remove(self, thread_handle):
        """ (thread-info with it's id-value) send with queue to the
            'thread_debug' - thread as 'removed'-thread info.
        """
        self.__dec_counter()
        info_tuple = (id(thread_handle), "remove", thread_handle, self._countervalue(), threading.active_count())
        self.__queue.put(info_tuple)

    def show_forever(self, loglevel):
        """ method to write/show that currently traced threading-informations
            endless.
        """
        header_print_counter = 0
        current_loglevel = loglevel

        if current_loglevel == logging.DEBUG:
            self.__write_debug_stream("-"*35 + " Thread-Debug start "+ "-"*35)
        header_str = "--- {:11}; {:^15}; {:6}; {:^50}; {:>3}; {:>3} ---".format("Time","ID","action","detail","registered","active_threads")
        while self.__threadrun:
            try:
                thread_actions = self.__queue.get()
                self.__queue.task_done()
                # display only on debugging-level
                if current_loglevel == logging.DEBUG:
                    (identifier ,action, thread_info, registered, thread_amount) = thread_actions
                    timestamp = str(time.time())[:15]
                    debug_str  = "{:15}; {}; {}; {}; {}; {}".format(timestamp, identifier, action, thread_info, registered, thread_amount)
                    if not (header_print_counter % 20):
                        self.__write_debug_stream(header_str)
                    header_print_counter += 1
                    self.__write_debug_stream(debug_str)
            except:
                time.sleep(1)
                
    def _countervalue(self):
        """ returns currently registered threads.
        """
        rtnvalue = 0
        try:
            cthread_info.thread_lock.acquire()
            rtnvalue = cthread_info.counter
        finally:
            cthread_info.thread_lock.release()
        return rtnvalue

    def __write_debug_stream(self, debug_str):
        """ writes that thread-informations to:
            1. file, if that flag: log2file_flag is True
            else
            2. print on screen.
        """
        if cthread_info.log2file_flag:
            try:
                self.__logfileObj.write(debug_str+"\n")
                self.__logfileObj.flush()
            except Exception("File write error"):
                self.__logfileObj.close()
                cthread_info.log2file_flag = False
        else:
            print(debug_str)

    def __inc_counter(self):
        """ increments currently registered thread-number.
        """
        try:
            cthread_info.thread_lock.acquire()
            cthread_info.counter += 1
        finally:
            cthread_info.thread_lock.release()

    def __dec_counter(self):
        """ decrements currently registered thread-number.
        """
        try:
            cthread_info.thread_lock.acquire()
            if cthread_info.counter > 0:
                cthread_info.counter -= 1
            else:
                raise Exception(ValueError("_dec_counter();value already zero"))
        finally:
            cthread_info.thread_lock.release()

_thread_info = cthread_info()

class cthread(threading.Thread):
    """ class 'cthread' using threading.Thread to trace start- and end-
        time of threads to global _thread_info instance for debug-reasons.
    """
    global _thread_info

    def __init__(self, name=None):
        threading.Thread.__init__(self, name=name)
        _thread_info.add(self)

    def __del__(self):
        _thread_info.remove(self)

class cthread_debug(threading.Thread):
    """ class 'cthread_debug' used for debug-purposes on thread lifetime.
        Debug-outputs are only written in debug-mode logging-level.
    """
    global _thread_info

    def __init__(self, loglevel):
        threading.Thread.__init__(self, name = "thread_debug")
        self._loglevel = loglevel

    def run(self):
        """ shows that thread_infos in endlessloop.
            has to be called with: start().
        """
        _thread_info.show_forever(self._loglevel)
       
class cportread(cthread):
    """class 'cportread' for reading serial asynchronous data from already
       open port and send received datastream to '_txqueue'
    """
    global _ClientHandler

    def __init__(self, port, devicetype):
        cthread.__init__(self, "portread_Thread")
        self.__threadrun=True
        self.__stopcalled=False
        self.__port=port
        self.__devicetype=devicetype
        self.__queueprio=INT_PRIO_MEDIUM
        self.__thread_infostr = "{}; ID:{}".format(self.getName(), id(self))

    def __del__(self):
        self.stop()
        cthread.__del__(self)

    def run(self):
        """ reading data from already open serial port and writes that data
            to all currently available client-queues.
            has to be called with: start().
        """
        _ClientHandler.log_debug("{}; start; devicetype:{}".format(self.__thread_infostr, self.__devicetype))
        _raise_condition = False
        value = 0
        while self.__threadrun:
            if _ClientHandler.get_clientcounter() > 0:
                try:
                    value = self.__port.read(5)
                except:
                    _ClientHandler.log_critical("{}; Error; couldn't read serial-port".format(self.__thread_infostr))
                    _raise_condition = True
                    self.stop()
                    break
                else:
                    if len(value) > 0:
                        for clientQueue in _ClientHandler._txqueue.items():
                            if self.__threadrun:
                                try:
                                    #put comport readvalue in any connected client-queue
                                    #  clientQueue[0]:=Client-ID; clientQueue[1]:=queue
                                    #    put value into queue
                                    clientQueue[1].put(value)
                                except:
                                    _ClientHandler.log_info("{}; Error; Client-ID:{}; couldn't write to queue".format(self.__thread_infostr, clientQueue[0]))
                                    break;
                            else:
                                break;
            else:
                time.sleep(0.5)
                try:
                    self.__port.reset_input_buffer()
                except:
                    _ClientHandler.log_critical("{}; Error; serial-port not open".format(self.__thread_infostr))
                    _raise_condition = True
                    self.stop()
                    break
        end_str = "{}; end; devicetype:{}".format(self.__thread_infostr, self.__devicetype)
        execption_str = "{}; unexpected end; devicetype:{}".format(self.__thread_infostr, self.__devicetype)
        _ClientHandler.log_debug(end_str)
        if _raise_condition and not self.__stopcalled:
            _ClientHandler.log_critical(execption_str)
            self.__port.close()
            raise portNotOpenError

    def stop(self):
        """ stop the running 'cportread'-thread and send all startet
            socketsendThreads one 'None'-info as termination-tag.
        """
        _ClientHandler.log_debug("{}; stop() called".format(self.__thread_infostr))
        # stop all running socketsendThreads with dummy-data: None
        for clientQueue in _ClientHandler._txqueue.items():
            clientQueue[1].put_nowait(None)
        self.__threadrun=False
        self.__stopcalled=True

class cportwrite(cthread, ht_utils.cht_utils):
    """class 'cportwrite' for writing serial asynchronous data to already
       open port with received datastream from '_rxqueue'
    """
    global _ClientHandler

    def __init__(self, port, devicetype):
        cthread.__init__(self, "portwrite_Thread")
        ht_utils.cht_utils.__init__(self)
        self.__threadrun=True
        self.__stopcalled=False
        self.__port=port
        self.__devicetype=devicetype
        self.__queueprio=INT_PRIO_MEDIUM
        self.__thread_infostr = "{}; ID:{}".format(self.getName(), id(self))


    def __del__(self):
        self.stop()
        cthread.__del__(self)

    def run(self):
        """bytes are read from queue, searched for start-tag '#' and length of
            following bytes. Then all bytes are written to comport
            # following queue-message_structur is supported:
            #   tag  length   class   detail  option  databytes.....
            #    #   <size>   ! or ?   d       o       bytes.....
            #      size := amount of databytes including class, detail and option but without starttag
            #
        """
        _ClientHandler.log_debug("{}; start; devicetype:{}".format(self.__thread_infostr, self.__devicetype))
        while self.__threadrun:
            if _ClientHandler.get_clientcounter() > 0:
                # preset local buffers
                self.__starttag_found=False
                self.__length        =0
                readbuffer=[0,]
                # 1. search for start-tag '#'
                while not self.__starttag_found and self.__threadrun and (_ClientHandler.get_clientcounter() > 0):
                    try:
                        # get comport writevalues from any connected client-queue
                        for clientQueue in _ClientHandler._rxqueue.items():
                            try:
                                # use get() with timeout
                                readbuffer=clientQueue[1].get(timeout=0.2)
                                clientQueue[1].task_done()
                            except queue.Empty:
                                # timeout occured-> no exception
                                pass
                            else:
                                if readbuffer[0] == 0x23:
                                    self.__starttag_found=True
                                    break
                    except Exception as e:
                        # _ClientHandler.log_warning("{}; Client-ID:{}; Info; {}".format(self.__thread_infostr, clientQueue[0], e))
                        pass

                    try:
                        # check for open serial port.
                        #  if not open terminate the thread
                        if not self.__port.is_open:
                            _ClientHandler.log_critical("{}; Error; Client-ID:{}; serial port not open".format(self.__thread_infostr, clientQueue[0]))
                            self.stop()
                            break
                    except Exception as e :
                        _ClientHandler.log_critical("{}; Error; Client-ID:{}; {}".format(self.__thread_infostr, clientQueue[0], e))
                        self.stop()
                        break

                if self.__threadrun and self.__starttag_found:
                    # 2. now get msg-length from stream (over all length including headerbytes but without starttag)
                    if len(readbuffer) > 1:
                        self.__length=readbuffer[1]

                    # 3. now read rest of msg-headerbytes from stream and set resulting payload-length
                    if len(readbuffer) > 4:
                        msg_class =readbuffer[2]
                        msg_detail=readbuffer[3]
                        msg_option=readbuffer[4]
                        if self.__length >= 3:
                            self.__length -= 3
                        else:
                            self.__length = 0
                    else:
                        self.__starttag_found=False

                if self.__threadrun and self.__starttag_found:
                    self.__msgbytes=[]
                    try:
                        if self.__length > 0:
                            self.__msgbytes.extend(readbuffer[5:self.__length+5])
                    except Exception as e:
                        _ClientHandler.log_critical("{}; Error; Client-ID:{}; {}".format(self.__thread_infostr, clientQueue[0], e))
                        break

                    # 4. send message-class/detail/option and (data-bytes if available) to transceiver_if
                    try:
                        self.__send_2_transceiver_if(clientQueue[0], self.__msgbytes, msg_class, msg_detail, msg_option)
                    except  Exception as e:
                        _ClientHandler.log_critical("{}; Error; Client-ID:{}; {}".format(self.__thread_infostr, clientQueue[0], e))
                        self.stop()
                        break
            else:
                time.sleep(0.2)
                try:
                    self.__port.reset_output_buffer()
                except Exception as e:
                    _ClientHandler.log_critical("{}; Error; {}".format(self.__thread_infostr, e))
                    self.stop()
                    break

        end_str = "{}; end; devicetype:{}".format(self.__thread_infostr, self.__devicetype)
        _ClientHandler.log_debug(end_str)

    def stop(self):
        """ stop the running 'cportwrite'-thread.
        """
        _ClientHandler.log_debug("{}; stop() called".format(self.__thread_infostr))
        self.__threadrun=False
        self.__stopcalled=True

    def __send_2_transceiver_if(self, ClientID, data_in, msg_class=0x21, detail=0x53, option=0):
        """ creates the transceiver-required datastream:
            1. header <#  ,  msg_class:=! , detail:=S, option, data-length>
            2. + payload: 'data_in'
            3. + crc
            and send it with serial port to the transceiver.
        """
        # header to be send:  <#  ,  msg_class:=! , detail:=S, option, data-length>
        if len(data_in):
            header = [0x23,msg_class,detail,option,len(data_in)]
            data   = header+data_in
        else:
            header = [0x23,msg_class,detail,option,0]
            data   = header

        # generate crc and add crc-byte
        try:
            crc=self.make_crc(data, len(data))
            data += [crc]
        except:
            _ClientHandler.log_critical("{}.send_2_transceiver_if(); Error; Client-ID:{}; couldn't make crc".format(self.getName(), ClientID))
            raise

        try:
            index=0
            transmit_str=""
            while index < len(data):
                self.__port.write(bytearray([data[index]]))
                self.__port.flushOutput()
                time.sleep(0.005)
                transmit_str += format(data[index], "02x") + " "
                index += 1
            _ClientHandler.log_debug("{}; Client-ID:{}; tx to transceiver:{}".format(self.getName(), ClientID, transmit_str))
        except:
            _ClientHandler.log_critical("{}.send_2_transceiver_if(); Error; Client-ID:{}; serial-port not open".format(self.getName(), ClientID))
            raise ConnectionError

class cht_transceiver_if(cthread):
    """class 'cht_transceiver_if' as serial asynchronous interface to 'ht_transceiver'
       The used port must be accessable and is used exclusive one time.
       All received serial data are written to queue(s),(unique for every socket-client)
         this is handled with class: cportread
       All transmitted serial data are read from queue(s),(unique for every socket-client)
         this is handled with class: cportwrite
    """
    global _ClientHandler
    def __init__(self, serialdevice="/dev/ttyUSB0", baudrate=19200, devicetype=DT_RX):
        cthread.__init__(self, "transceiver_if_Thread")
        self.__serialdevice = str(serialdevice)
        self.__baudrate     = baudrate
        self.__devicetype   = devicetype
        self.__port = None
        self.__comtx_thread = None
        self.__comrx_thread = None
        self.__thread_infostr = "{}; ID:{}".format(self.getName(), id(self))

    def __del__(self):
        self.stop()
        if self.__port != None:
            self.__port.close()
        cthread.__del__(self)

    def run(self):
        """ open the serial port with parameter: baudrate
            starts threads as daemons:
            1. cportwrite()
            2. cportread()
            and waits for cportread-thread termination.
        """
        try:
            # open serial port with read-timeout for reading HT-data
            self.__port = serial.Serial(self.__serialdevice, self.__baudrate, timeout=0.01)
        except ConnectionError as e:
            _ClientHandler.log_critical("{}; Error; {}".format(self.__thread_infostr, e))
            raise ConnectionError("Can't open serial port")
        else:
            try:
                # start portwrite-thread
                self.__comtx_thread=cportwrite(self.__port, self.__devicetype)
                self.__comtx_thread.setDaemon(True)
                self.__comtx_thread.start()
            except ConnectionError as e:
                _ClientHandler.log_critical("{}; Error; {}".format(self.__thread_infostr, e))
                self.stop()
                raise ConnectionError("serial port for 'write' not available")
            else:
                try:
                    # start portread-thread
                    self.__comrx_thread=cportread(self.__port, self.__devicetype)
                    self.__comrx_thread.setDaemon(True)
                    self.__comrx_thread.start()
                except ConnectionError as e:
                    _ClientHandler.log_critical("{}; Error; {}".format(self.__thread_infostr, e))
                    self.stop()
                    raise ConnectionError("serial port for 'read' not available")

            # check running rx-thread, only at exception all threads are finished
            self.__comrx_thread.join()

            if self.__port is not None:
                self.__port.close()
                self.__port = None

            # check running tx-thread
            self.__comtx_thread.join()

        # should never been reached, only in error-cases
        _ClientHandler.log_critical("{}; Error; unexpected termination".format(self.__thread_infostr))
        
    def stop(self):
        """ stop the running 'cht_transceiver_if' thread.
        """
        _ClientHandler.log_debug("{}; stop() called".format(self.__thread_infostr))
        if self.__comtx_thread is not None:
            self.__comtx_thread.stop()
        if self.__comrx_thread is not None:
            self.__comrx_thread.stop()

class csocketsendThread(cthread):
    """class 'csocketsendThread' used for sending data from tx-queue to
       already connected socket
    """
    def __init__(self, request, queue):
        cthread.__init__(self, "socketsend_Thread")
        self._queue  =queue
        self._request=request
        self.__threadrun=True
        self.__queueprio=INT_PRIO_MEDIUM
        self.__thread_infostr = "{}; ID:{}".format(self.getName(), id(self))

    def __del__(self):
        cthread.__del__(self)

    def run(self):
        """ gets data from queue and send them to connected socket-client.
        """
        _ClientHandler.log_debug("{}; start".format(self.__thread_infostr))
        self._tx=None
        while self.__threadrun:
            try:
                # get queue-value in blocking mode
                self._tx=self._queue.get(True)
            except:
                error_str = "{}; Error; on TXqueue.get()".format(self.__thread_infostr)
                _ClientHandler.log_critical(error_str)
                raise ConnectionError(error_str)
            finally:
                self._queue.task_done()
                if self._tx is None:
                    # terminate thread
                    self.__threadrun=False
                    break

            try:
                if self.__threadrun:
                    self._request.sendall(bytes(self._tx))
                else:
                    break
            except (BrokenPipeError, ConnectionResetError) as e:
##                print("csocketsendThread; Error:{}".format(e))
                pass
            except:
                error_str = "{}; Error; on _request.sendall()".format(self.__thread_infostr)
                _ClientHandler.log_critical(error_str)
                raise ConnectionError(error_str)

        _ClientHandler.log_debug("{}; end".format(self.__thread_infostr))

    def stop(self):
        """ stop the running 'csocketsendThread'-thread.
            send one dummy 'None'-byte to unblock the waiting queue.
        """
        _ClientHandler.log_debug("{}; stop() called".format(self.__thread_infostr))
        self.__threadrun=False
        # put dummy-info in queue to unblock the thread
        self._queue.put_nowait(None)

class cClientHandling(cthread, ht_utils.clog):
    """class 'cClientHandling' used for add and remove clients to/from queues and
       threads. logging-methods are available for different logging-levels.
    """
    def __init__(self, logfilepath="./ht_proxy_if.log", tcp_ip_type=TT_SERVER, loglevel=logging.INFO):
        cthread.__init__(self, "ClientHandling_Thread")
        # init/setup logging-file
        ht_utils.clog.__init__(self)
        self._logging=ht_utils.clog.create_logfile(self, logfilepath=logfilepath, loglevel=loglevel, loggertag=tcp_ip_type)

        self._indexcounter=0
        self._clientcounter=0
        self._lock=threading.Lock()
        self._rxqueue={}
        self._txqueue={}
        self._thread={}
        self.__thread_infostr = "{}".format(self.getName())

    def __del__(self):
        cthread.__del__(self)

    def log_critical(self, logmessage):
        """ log message with CRITICAL-tag.
        """
        self._logging.critical(logmessage)

    def log_error(self, logmessage):
        """ log message with ERROR-tag.
        """
        self._logging.error(logmessage)

    def log_warning(self, logmessage):
        """ log message with WARNING-tag.
        """
        self._logging.warning(logmessage)

    def log_info(self, logmessage):
        """ log message with INFO-tag.
        """
        self._logging.info(logmessage)

    def log_debug(self, logmessage):
        """ log message with DEBUG-tag.
        """
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
        """ increments that currently registered client amount
        """
        self._lock.acquire()
        self._clientcounter+=1
        self._lock.release()

    def dec_clientcounter(self):
        """ decrements that currently registered client amount
        """
        self._lock.acquire()
        self._clientcounter-=1
        self._lock.release()

    def get_clientcounter(self):
        """ returns the currently registered clients
        """
        self._lock.acquire()
        counter=self._clientcounter
        self._lock.release()
        return counter

    def add_client(self, clientID, request):
        """ adds a new client with:
            1. rxqueue and txqueue attached to this client-ID
            2. starting new csocketsendThread() thread as daemon
                attached to this client-ID
        """
        self._lock.acquire()
        self._rxqueue.update({clientID:queue.Queue()})
        self._txqueue.update({clientID:queue.Queue()})

        txThread=csocketsendThread(request, self._txqueue.get(clientID))
        txThread.setDaemon(True)
        self._thread.update({clientID:txThread})
        txThread.start()
        self._lock.release()
        self._logger.info("{}; Client-ID:{} added; number of clients:{}".format(self.__thread_infostr, clientID, self._clientcounter))

    def remove_client(self, clientID):
        """ removes a client from:
            1. rxqueue and txqueue owned by this client-ID
            2. stopping csocketsendThread() thread owned by this client-ID
        """
        self._lock.acquire()
        if len(self._thread) > 0:
            txThread=self._thread.pop(clientID)
            if txThread is not None:
                txThread.stop()
        if len(self._rxqueue) > 0:
            self._rxqueue.pop(clientID)
        if len(self._txqueue) > 0:
            self._txqueue.pop(clientID)
        self._lock.release()
        self._logger.info("{}; Client-ID:{} removed; number of clients:{}".format(self.__thread_infostr, clientID, self._clientcounter))

class cht_RequestHandler(socketserver.BaseRequestHandler):
    """ class used for every new client-request
         handling-sequence:
         1. waiting for client-devicetype response
         2. add new client with it's unique ID and request
         3. get queue-handle attached on this unique ID
         4. start loop for receiving client.data (request.recv())
         5. put received client-data to queue
         6. stop loop if no more data available
              loop(True): client.request.data -> put.rxqueue (-> cportwrite)
    """
    global _ClientHandler
    threadrun = True

    def handle(self):
        """ handles a new client-request
        """
        self._request_rx=None
        self._client_devicetype=None
        self.__queueprio=INT_PRIO_HIGH
        try:
            addrc, portc = self.client_address
            addrs, ports = self.server.server_address
            _ClientHandler.log_info("RequestHandler; Client-ID:{}; {} connected".format(self._myownID, (addrc, portc)))
            _ClientHandler.log_info("RequestHandler; Server   :{}".format((addrs,ports)))
        except:
            addrc, portc = self.client_address
            _ClientHandler.log_critical("RequestHandler; Client-ID:{}; {} No connection possible".format(self._myownID, (addrc, portc)))
            raise
        # wait for client registration
        self.__waitfor_client_register()
        # add client to handler
        _ClientHandler.add_client(self._myownID, self.request)
        self._rxqueue=_ClientHandler._rxqueue.get(self._myownID)

        _ClientHandler.log_debug("RequestHandler; Client-ID:{}; socket.receive thread start".format(self._myownID))
        # run thread-loop
        while cht_RequestHandler.threadrun:
            try:
                self._request_rx=self.request.recv(60)
            except Exception as e:
                # closed by peer
                _ClientHandler.log_info("RequestHandler; Client-ID:{}; {} disconnected".format(self._myownID, (addrc, portc)))
                # terminate the thread
                break
            if len(self._request_rx) > 0:
                try:
                    # put socket-data in queue
                    self._rxqueue.put(self._request_rx)
                    request_rxstr=""
                    for index in range(len(self._request_rx)):
                        request_rxstr += format(self._request_rx[index], "02x") + " "
                    _ClientHandler.log_debug("RequestHandler; Client-ID:{}; recv:{}".format(self._myownID, request_rxstr))
                except Exception as e:
                    _ClientHandler.log_critical("RequestHandler; Client-ID:{}; _rxqueue.put():{}".format(self._myownID, e))
                    break
            else:
                _ClientHandler.log_info("RequestHandler; Client-ID:{}; {} disconnected".format(self._myownID, (addrc, portc)))
                break

        _ClientHandler.log_debug("RequestHandler; Client-ID:{}; socket.receive thread end".format(self._myownID))

    def __waitfor_client_register(self):
        """ waits for client-information ('RX or 'MODEM')  and sends current internal ID
            back to server.
        """
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
        """ setup a new client-request and set the thread run-flag used
            in 'handle' method.
        """
        _ClientHandler.inc_indexcounter()
        _ClientHandler.inc_clientcounter()
        self._myownID=_ClientHandler.get_indexcounter()
        cht_RequestHandler.threadrun = True

    def finish(self):
        """ removes a registered client and set the thread-temination-flag.
        """
        _ClientHandler.dec_clientcounter()
        _ClientHandler.remove_client(self._myownID)
        cht_RequestHandler.threadrun = False

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
        """ reads the XML- configurationfile and extracs the data.
        """
        try:
            self.__configfilename=xmlconfigpathname
            self.__tree = ET.parse(xmlconfigpathname)
        except (NameError,EnvironmentError,IOError) as e:
            errorstr = "CRITICAL;cproxyconfig().read_config();Error;{0} on file:'{1}'\n".format(e.args[0], self.__configfilename)
            logfilepath = "./var/log/ht_proxy.log"
            try:
                fobj = open(logfilepath, "a")
                fobj.write(errorstr)
                fobj.flush()
                fobj.close()
            except:
                print(errorstr)
            raise Exception(EnvironmentError(errorstr))
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
                    portnumber = int(proxy_part.find(item).text)
                    cproxyconfig._configdata[storetarget][0].update({str(item).upper():proxy_part.find(item).text})
                    item='logfilepath'
                    logfilepath = proxy_part.find(item).text
                    cproxyconfig._configdata[storetarget][0].update({str(item).upper():proxy_part.find(item).text})
                    # check values and raise on error
                    if portnumber < 0 or portnumber > 65535:
                        errorstr = "CRITICAL;cproxyconfig();portnumber must be in range:0-65535.\n"
                        try:
                            fobj = open(logfilepath, "a")
                            fobj.write(errorstr)
                            fobj.flush()
                            fobj.close()
                        except:
                            print(errorstr)
                        raise Exception(ValueError(errorstr))

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
        if initflag is not None:
            cproxyconfig._configtransceiver_devicenames.update({key:initflag})
        return cproxyconfig._configtransceiver_devicenames.get(key)

    def clear_initflags(self):
        """ resets all initialisiation-flags for all devicenames
        """
        for key in self.devicename_keys():
            cproxyconfig._configtransceiver_devicenames.update({key:0})

class cht_TCPserver(cthread):
    """class 'cht_TCPserver', TCP server-class running as thread.
    """
    global _ClientHandler
    # preset global Flags for 'reuse_address' on server.bind() and
    #  not blocking on server.close() call
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingMixIn.block_on_close = False

    def __init__(self, ip_adr_and_port_t):
        cthread.__init__(self, "TCPserver_Thread")
        (self._ip_address, self._port_number) = ip_adr_and_port_t
        self._server = None
    
    def __del__(self):
        """ delete all used instances
        """
        cthread.__del__(self)

    def shutdown_server(self):
        """ shutdown the running TCPserver
        """
        if self._server is not None:
            _ClientHandler.info("{}; shutdown_server() called".format(self.getName()))
            try:
                self._server.shutdown()
            except:
                pass

    def server_close(self):
        """ close the running server.
        """
        self._server.server_close()
        self._server = None
        
    def run(self):
        """ create Threading TCP server-object and run this endless
        """

        try:
            self._server = socketserver.ThreadingTCPServer((self._ip_address, self._port_number), cht_RequestHandler)
        except ConnectionError as e:
            error_str = "{}; error; {}".format(self.getName(), e)
            _ClientHandler.log_critical(error_str)
        else:
            _ClientHandler.log_debug("{}; start".format(self.getName()))
            # running loop forever, until external 'shutdown'
            self._server.serve_forever()

        _ClientHandler.log_critical("{}; unexpected termination".format(self.getName()))

class cht_proxy_daemon(cthread, cproxyconfig):
    """class 'cht_proxy_daemon' runs as server-daemon.
       ip_address and port_number comes from configuration-file.
    """
    global _ClientHandler

    def __init__(self, configfile="./etc/config/ht_proxy_cfg.xml", loglevel=logging.INFO):
        cthread.__init__(self, "proxy_daemon")
        tcp_ip_type=TT_SERVER
        cproxyconfig.__init__(self, tcp_ip_type, devicetype=DT_SERVER)
        self._configfile =configfile
        self._logfile    ="default_proxy.log"
        self._ip_address="localhost"
        self._port_number=48088
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
            _ClientHandler.log_info("---------------------------")
            _ClientHandler.log_info("{}; logfile:'{}'".format(self.getName(), self._logfile))
            _ClientHandler.log_info("{}; Rev:{}".format(self.getName(), __version__))
            _ClientHandler.log_info("{}; init".format(self.getName()))
           
            if not self.servername() == None:
                self._ip_address=self.servername()
            else:
                if not self.serveraddress() == None:
                    self._ip_address=self.serveraddress()
                else:
                    _ClientHandler.log_info("{}; using common serveraddress".format(self.getName()))
                    self._ip_address=""
        except:
            _ClientHandler=cClientHandling(self._logfile, loglevel=loglevel)
            _ClientHandler.log_critical("{}; error; can't get/set configurationvalues".format(self.getName()))
            raise

    def __del__(self):
        while len(self._ht_transceiver_if):
            self._ht_transceiver_if.pop().stop()
        cthread.__del__(self)

    def run(self):
        """ starts the proxy-server with:
            1. limited repeating loop (triggered on errors)
            2. starting cthread_debug() thread
            3. starting transceiver_if for every configured serial port
            4. starting one TCP-server waiting for client-requests
            has to be called with: cht_proxy_daemon.start()
        """
        _serialdevice_initialised=[]
        _first_call = True
        _restart = True
        _restart_loop = 50

        # start debug_thread with current loglevel
        thread_debug= cthread_debug(_ClientHandler.loglevel())
        thread_debug.start()
        
        while _restart_loop > 0 and _restart:
            if _first_call:
                _ClientHandler.log_info("{}; start as proxy-server:'{}';port:'{}'".format(self.getName(), self._ip_address, self._port_number))
                _first_call = False
            else:
                _serialdevice_initialised=[]
                self._ht_transceiver_if=[]
                _ClientHandler.log_info("{}; restart as proxy-server:'{}';port:'{}'".format(self.getName(), self._ip_address, self._port_number))
                
            for devicename in self.devicename_keys():
                if self.devicename_initflag(devicename) == 0:
                    # check for already initialised serial device, if not then start transceiver_if for this device
                    serialdevice   = self.transceiver_serialdevice(devicename)
                    if not serialdevice in (_serialdevice_initialised):
                        baudrate       = self.transceiver_baudrate(devicename)
                        devicetype     = self.transceiver_devicetype(devicename)
                        if self._IsPortAvailable(serialdevice, baudrate):
                            try:
                                _ClientHandler.log_info("{}; using serial device:'{}'; baudrate:'{}'".format(self.getName(), serialdevice, baudrate))
                                # create object 'transceiver-if' for that 'serial device'
                                transceiver_if = cht_transceiver_if(serialdevice, baudrate, devicetype)
                                # start 'transceiver-if'-thread
                                transceiver_if.start()
                            except:
                                transceiver_if.stop()
                                _ClientHandler.log_critical("{}; Error; can't open serial device:'{}'; baudrate:'{}'".format(self.getName(), serialdevice, baudrate))
                                break
                            else:
                                time.sleep(1.0)
                                if transceiver_if.is_alive():
                                    # add transceiver to list
                                    self._ht_transceiver_if.append(transceiver_if)
                                    # add used serial-device to list
                                    _serialdevice_initialised.append(serialdevice)

                                    # set initialise-flag for devicename
                                    self.devicename_initflag(devicename, 1)
                                    _restart_loop = 50
                                else:
                                    _ClientHandler.log_critical("{}; Error; transceiver_if:'{}'; not alive".format(self.getName(), id(transceiver_if)))
                                    break
                        else:
                            _ClientHandler.log_critical("{}; Error; serial device:'{}' not available; baudrate:'{}'".format(self.getName(), serialdevice, baudrate))
                            break

            if len(_serialdevice_initialised) > 0 and transceiver_if.is_alive():
                try:
                    # check if TCP-server is still running
                    if self._server is not None:
                        if self._server.is_alive():
                            # shutdown that TCPserver and wait for terminating thread.
                            self._server.shutdown_server()
                            self._server.join()
                            self._server.server_close()
                        self._server = None
                            
                    # create TCP-server object and start it
                    self._server = cht_TCPserver((self._ip_address, self._port_number))
                    self._server.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
                    self._server.start()
                    time.sleep(1.0)
                    if not self._server.is_alive():
                        _ClientHandler.log_critical("{}; Error; TCPserver Thread Not alive".format(self.getName()))
                        _restart = False
                except:
                    _ClientHandler.log_critical("{}; Error; TCPserver not startable".format(self.getName()))
                    _restart = False

                if _restart:
                    # waiting endless if no errors received from 'tranceiver_if'-threads (read/write)
                    for t in self._ht_transceiver_if:
                        t.join()

                if self._server is not None:
                    # shutdown that TCPserver and wait for terminating thread.
                    self._server.shutdown_server()
                    self._server.join()
                    self._server.server_close()

            if _restart and _restart_loop > 0:
                # clear all devicename_initflags
                self.clear_initflags()
                time.sleep(2.0)
                _restart_loop -= 1

        _ClientHandler.log_critical("{}; terminated".format(self.getName()))
        _ClientHandler.log_critical("---------------------------")

    def get_indexcounter(self):
        global _ClientHandler
        return _ClientHandler.get_indexcounter()

    def get_clientcounter(self):
        global _ClientHandler
        return _ClientHandler.get_clientcounter()

    def _IsPortAvailable(self, serialdevice, baudrate):
        """ returns True if serial-port can be created, else False
        """
        rtnvalue = False
        try:
            # open serial port for testpurposes
            porthandle = serial.Serial(serialdevice, baudrate)
            porthandle.close()
            rtnvalue = True
        except:
            rtnvalue = False
        return rtnvalue

#--- class cht_proxy_if end ---#

class cht_socket_client(cproxyconfig, ht_utils.clog):
    """class 'cht_socket_client' connects to socket.server
       using ip_address and port_number from configuration-file.
    """
    def __init__(self, configfile="./etc/config/ht_proxy_cfg.xml", devicetype=DT_RX, loglevel=logging.INFO):
        """ constructor actions:
            1. reading configurationfile and extract informations
            2. creating logfile - handler
            3. creating socket-instance and connect to server
            4. register to server and get information from answer
        """
        tcp_ip_type=TT_CLIENT
        self._devicetype =devicetype
        cproxyconfig.__init__(self, tcp_ip_type, self._devicetype)
        self._configfile =configfile
        self._ip_address ="192.168.2.1"
        self._port_number=48088
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
            self.log_info("socket_client; init")
            if not self.servername() == None:
                self._ip_address=self.servername()
            else:
                if not self.serveraddress() == None:
                    self._ip_address=self.serveraddress()
                else:
                    error_str = "socket_client.__init__(); Error; no serveraddress defined"
                    self.log_critical(error_str)
                    raise ValueError(error_str)

        except:
            error_str = "socket_client; Error; can't set configurationvalues"
            self.log_critical(error_str)
            raise ValueError(error_str)

        try:
            self._socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._ip_address, self._port_number))
            self.log_info("socket_client; connected to server:'{0}';port:'{1}'".format(self._ip_address, self._port_number))
            self.log_info("socket_client; logfile:'{0}'".format(self._logfile))
        except:
            error_str = "socket_client.__init__(); Error; can't connect to socket"
            self.log_critical(error_str)
            raise ConnectionRefusedError(error_str)

        #send registration to proxy-server and receive client-related informations from server
        self.__registration()
        self.log_info("socket_client; Client-ID:{0}; registered with devicetype:'{1}'".format(self._clientID, self._devicetype))

    def __del__(self):
        if self._socket is not None:
            self.log_info("socket_client; Client-ID:{0}; socket closed".format(self._clientID))

    def __registration(self):
        """ send that config:devicetype-information to the socket.server
            and waiting for server-answer used as Client-ID number.
        """
        try:
            # send devicetype to server
            devicetype=bytearray(self._devicetype.encode("utf-8"))
            self.write(devicetype)

            # read answer from server (client-ID) and store it
            self._clientID=self._socket.recv(10).decode('utf-8')
            ## only for test## print("client got ID:{0}".format(self._clientID))
        except (ConnectionError, SystemExit) as e:
            self.log_critical("socket_client.__registration(); Error; {}".format(e))
            raise SystemExit(e)
        except:
            self.log_critical("socket_client.__registration(); Error; can't register to master")
            raise

    def run(self):
        """ endless running thread for debug-output only of received
            data from the socket.server
            Must not be called, only the constructor __init__ is required
            to connect to the socket.server.
        """
        try:
            self.log_info("socket_client; Client-ID:{0}; run".format(self._clientID))
            while True:
                antwort=self._socket.recv(1)
                print("{0}".format(antwort))
        except:
            self._socket.close()
            self.log_critical ("socket_client; Error; Client-ID:{0}; on socket.recv".format(self._clientID))
            raise

    def close(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None
            self.log_info("socket_client; Client-ID:{0}; socket closed".format(self._clientID))

    def read(self, size=1):
        """Read size bytes from the connected socket. It will block
           until the requested number of bytes are read.
        """
        if self._socket is None:
            error_str = "socket_client.read(); Error; Client-ID:{0}; socket not initialised".format(self._clientID)
            self.log_critical(error_str)
            raise SystemExit(error_str)

        read=bytearray()
        buffer = bytearray()
        while len(read) < size:
            try:
                buffer=self._socket.recv(size)
            except:
                error_str = "socket_client.read(); Error; Client-ID:{0}; error on socket.recv".format(self._clientID)
                self.log_critical(error_str)
                self._socket.close()
                raise ConnectionError(error_str)
            else:
                # check for empty buffer and raise if it is empty -->> socket connection broken
                if len(buffer) == 0:
                    error_str = "socket_client.read(); Error; Client-ID:{0}; peer closed socket".format(self._clientID)
                    self.log_critical(error_str)
                    raise SystemExit(error_str)
                else:
                    read.extend(buffer)

        return bytes(read)

    def write(self, data):
        """write data to connected socket. It will block
           until all data is written.
        """
        if self._socket==None:
            error_str = "socket_client.write(); Error; Client-ID:{0}; socket not initialised".format(self._clientID)
            self.log_critical(error_str)
            raise SystemExit(error_str)
        try:
            self._socket.sendall(bytes(data))
        except:
            error_str = "socket_client.write(); Error; Client-ID:{0}; error on socket.sendall".format(self._clientID)
            self.log_critical(error_str)
            raise ConnectionError(error_str)

    def ip_address(self):
        """
            returns the current ip-address
        """
        return self._ip_address

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
