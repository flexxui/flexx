# -*- coding: utf-8 -*-
# Copyright (C) 2014, Almar Klein

""" Simple IPC based on a persistent socket pair.
"""

import os
import sys
import time
import socket
import threading

# Python 2.x and 3.x compatibility
if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,

## Constants

# Use a relatively small buffer size, to keep the channels better in sync
SOCKET_BUFFERS_SIZE = 10*1024

# Minimum timout
TIMEOUT_MIN = 0.5

# For the status
STATUS_CLOSED = 0
STATUS_CLOSING = 1
STATUS_WAITING = 2
STATUS_HOSTING = 3
STATUS_CONNECTED = 4

## Functions and the class


def port_hash(name):
    """ port_hash(name)
    
    Given a string, returns a port number between 49152 and 65535. 
    (2**14 (16384) different posibilities)
    This range is the range for dynamic and/or private ports 
    (ephemeral ports) specified by iana.org.
    The algorithm is deterministic, thus providing a way to map names
    to port numbers.
    
    """
    fac = 0xd2d84a61
    val = 0
    for c in name:
        val += ( val>>3 ) + ( ord(c)*fac )
    val += (val>>3) + (len(name)*fac)
    return 49152 + (val % 2**14)


class Connection(object):
    
    def __init__(self):
        # Timeout value (if no data is received for this long, 
        # the timedout signal is fired). Because we do not know the timeout
        # that the other side uses, we apply a minimum timeout.
        self._timeout = TIMEOUT_MIN
        
        self._set_status(0)
    
    def _get_hostname_and_port(self, address):
        # Check
        if not isinstance(address, string_types):
            raise ValueError("Address should be a string.")
        if not ":" in address:
            raise ValueError("Address should be in format 'host:port'.")
        
        host, port = address.split(':')
        # Process host
        if host.lower() == 'localhost':
            host = '127.0.0.1'
        if host.lower() == 'publichost':
            host = 'publichost' + '0'
        if host.lower().startswith('publichost') and host[10:].isnumeric():
            index = int(host[10:])
            hostname = socket.gethostname()
            tmp = socket.gethostbyname_ex(hostname)
            try:
                host = tmp[2][index]  # This resolves to 127.0.1.1 on some Linuxes
            except IndexError:
                raise ValueError('Invalid index (%i) in public host addresses.' % index)
        # Process port
        try:
            port = int(port)
        except ValueError:
            port = port_hash(port)
        if port > 2**16:
            raise ValueError("The port must be in the range [0, 2^16>.")
        return host, port
    
    def _set_status(self, status, bsd_socket=None):
        """ _connected(status, bsd_socket=None)
        
        This method is called when a connection is made.
        
        Private method to apply the bsd_socket.
        Sets the socket and updates the status. 
        Also instantiates the IO threads.
        
        """
        
        # Update hostname and port number; for hosting connections the port
        # may be different if max_tries > 0. Each client connection will be 
        # assigned a different ephemeral port number.
        # http://www.tcpipguide.com/free/t_TCPPortsConnectionsandConnectionIdentification-2.htm
        # Also get hostname and port for other end
        if bsd_socket is not None:
            if True:
                self._hostname1, self._port1 = bsd_socket.getsockname()
            if status != STATUS_WAITING: 
                self._hostname2, self._port2 = bsd_socket.getpeername()
        
        assert status in (STATUS_CLOSED, STATUS_CLOSING, STATUS_WAITING, 
                          STATUS_HOSTING, STATUS_CONNECTED)
        self._status = status
    
        if status in [STATUS_HOSTING, STATUS_CONNECTED]:
            # Really connected
            
            # Store socket
            self._bsd_socket = bsd_socket
            
            # Set socket to non-blocking mode
            bsd_socket.setblocking(False)
            
#             # Create and start io threads
#             self._sendingThread = SendingThread(self)
#             self._receivingThread = ReceivingThread(self)
#             #
#             self._sendingThread.start()
#             self._receivingThread.start()
        
        if status == STATUS_CLOSED:
            
            # Close bsd socket
            try:
                self._bsd_socket.shutdown() 
            except Exception:
                pass
            try:
                self._bsd_socket.close() 
            except Exception:
                pass
            self._bsd_socket = None
#             
#             # Remove references to threads
#             self._sendingThread = None
#             self._receivingThread = None
    
    @property
    def is_waiting(self):
        """ Get whether this connection instance is waiting for a connection. 
        This is the state after using bind() and before another context 
        connects to it.
        """
        return self._status == 2
    
    def bind(self, address, max_tries=1):
        """ Bind the bsd socket. Launches a dedicated thread that waits
        for incoming connections and to do the handshaking procedure.
        """ 
        hostname, port = self._get_hostname_and_port(address)
        
        # Create socket. 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set buffer size to be fairly small (less than 10 packages)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFERS_SIZE)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFERS_SIZE)
        
        # Apply SO_REUSEADDR when binding, so that an improperly closed 
        # socket on the same port will not prevent us from connecting.
        # It also allows a connection to bind at the same port number,
        # but only after the previous binding connection has connected
        # (and has closed the listen-socket).
        # 
        # SO_REUSEADDR means something different on win32 than it does
        # for Linux sockets. To get the intended behavior on Windows,
        # we don't have to do anything. Also see:
        #  * http://msdn.microsoft.com/en-us/library/ms740621%28VS.85%29.aspx
        #  * http://twistedmatrix.com/trac/ticket/1151
        #  * http://www.tcpipguide.com/free/t_TCPPortsConnectionsandConnectionIdentification-2.htm
        if not sys.platform.startswith('win'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Try all ports in the specified range
        for port2 in range(port, port+max_tries):
            try:
                s.bind((hostname,port2))
                break
            except Exception:
                # Raise the socket exception if we were asked to try
                # just one port. Otherwise just try the next
                if max_tries == 1:
                    raise
                continue
        else:
            # We tried all ports without success
            tmp = str(max_tries)
            tmp = "Could not bind to any of the " + tmp + " ports tried."
            raise IOError(tmp)
        
        # Tell the socket it is a host, backlog of zero
        s.listen(0)
        
        # Set connected (status 1: waiting for connection)
        # Will be called with status 2 by the hostThread on success
        self._set_status(STATUS_WAITING, s)
        
        # Start thread to wait for a connection 
        # (keep reference so the thread-object stays alive)
        self._hostThread = HostThread(self, s)
        self._hostThread.start()
    
    
    def connect(self, address, timeout=1.0):
        """ Connect to a bound socket.
        """
        hostname, port = self._get_hostname_and_port(address)
        
        # Create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set buffer size to be fairly small (less than 10 packages)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFERS_SIZE)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFERS_SIZE)
        
        # Refuse rediculously low timeouts
        if timeout<= 0.01:
            timeout = 0.01
        
        # Try to connect
        ok = False
        timestamp = time.time() + timeout
        while not ok and time.time() < timestamp:           
            try:
                s.connect((hostname, port))
                ok = True
            except socket.error:
                pass
            except socket.timeout:
                pass
            time.sleep(timeout / 100.0)
        
        # Did it work?
        if not ok:
            type, value, tb = sys.exc_info()
            del tb
            err = str(value)
            raise IOError("Cannot connect to %s on %i: %s" % (hostname, port, err))
        
        # Shake hands
        h = HandShaker(s)
        success, info = h.shake_hands_as_client()
        
        # Problem?
        if not success:
            self._set_status(0)
            if not info:
                info = 'problem during handshake'
            raise IOError('Could not connect: '+ info)
        
        # Store id
        self._id2, self._pid2 = info
        
        # Set connected (status 3: connected as client)
        self._set_status(STATUS_CONNECTED, s)


class HostThread(threading.Thread):
    """ HostThread(context_connection, bds_socket)
    
    The host thread is used by the ContextConnection when hosting a 
    connection. This thread waits for another context to connect 
    to it, and then performs the handshaking procedure.
    
    When a successful connection is made, the context_connection's 
    _connected() method is called and this thread then exits.
    
    """
    
    def __init__(self, context_connection, bsd_socket):
        threading.Thread.__init__(self)
        
        # Store connection and socket
        self._context_connection = context_connection
        self._bsd_host_socket = bsd_socket
        
        # Make deamon (Python can exit even if this thread is still alive)
        self.setDaemon(True)
    
    
    def run(self):
        """ Run the main loop. Waits for a connection and performs handshaking
        if successfull.
        """
        
        # Try making a connection until success or the context is stopped
        while self._context_connection.is_waiting:
            
            # Wait for connection 
            s = self._wait_for_connection()
            if not s:
                continue
            
            # Check if not closed in the mean time
            if not self._context_connection.is_waiting:
                break
            
            # Do handshaking
            hs = HandShaker(s)
            success, info = hs.shake_hands_as_host()
            if success:
                self._context_connection._id2 = info[0]
                self._context_connection._pid2 = info[1]
            else:
                print('Yoton: Handshake failed: '+info)
                continue
            
            # Success!
            # Close hosting socket, thereby enabling rebinding at the same port
            self._bsd_host_socket.close()
            # Update the status of the connection
            self._context_connection._set_status(STATUS_HOSTING, s)
            # Break out of the loop
            break
        
        # Remove ref
        del self._context_connection
        del self._bsd_host_socket
    
    
    def _wait_for_connection(self):
        """ The thread will wait here until someone connects. When a 
        connections is made, the new socket is returned.
        """
        # Set timeout so that we can check _stop_me from time to time
        self._bsd_host_socket.settimeout(0.25)
        # Wait
        while self._context_connection.is_waiting:
            try:
                s, addr = self._bsd_host_socket.accept()
                return s  # Return the new socket
            except socket.timeout:
                pass
            except socket.error:
                # Skip errors caused by interruptions.
                type, value, tb = sys.exc_info()
                del tb
                if value.errno != EINTR:
                    raise

class HandShaker:
    """ HandShaker(bsd_socket)
    
    Class that performs the handshaking procedure for Tcp connections.
    
    Essentially, the connecting side starts by sending 'YOTON!' 
    followed by its id as a hex string. The hosting side responds
    with the same message (but with a different id).
    
    This process is very similar to a client/server pattern (both 
    messages are also terminated with '\r\n'). This is done such that
    if for example a web client tries to connect, a sensible error
    message can be returned. Or when a ContextConnection tries to connect
    to a web server, it will be able to determine the error gracefully.
    
    """
    
    def __init__(self, bsd_socket):
        
        # Store bsd socket
        self._bsd_socket = bsd_socket
    
    
    def shake_hands_as_host(self):
        """ _shake_hands_as_host(id)
        
        As the host, we wait for the client to ask stuff, so when
        for example a http client connects, we can stop the connection.
        
        Returns (success, info), where info is the id of the context at
        the other end, or the error message in case success is False.
        
        """
        
        # Make our message with id and pid
        message = 'ZOOF says yoton!'
        
        # Get request
        request = self._recv_during_handshaking()
        
        if not request:
            return False, STOP_HANDSHAKE_TIMEOUT
        elif request.strip() == message:
            self._send_during_handshaking(message)
            return True, (0, 0)
        else:
            # Client is not yoton
            self._send_during_handshaking('ERROR: this is Zoof via yoton.')
            return False, STOP_HANDSHAKE_FAILED
    
    
    def shake_hands_as_client(self):
        """ _shake_hands_as_client(id)
        
        As the client, we ask the host whether it is a Yoton context
        and whether the channels we want to support are all right.
        
        Returns (success, info), where info is the id of the context at
        the other end, or the error message in case success is False.
        
        """
        
        # Make our message with id and pif
        # todo: define message as constant
        message = 'ZOOF says yoton!'
        
        # Do request
        error = self._send_during_handshaking(message)
        
        # Get response
        response = self._recv_during_handshaking()
        
        # Process
        if not response:
            return False, STOP_HANDSHAKE_TIMEOUT
        elif response.strip() == message:
            return True, (0, 0)
        else:
            return False, STOP_HANDSHAKE_FAILED
    
    def _send_during_handshaking(self, text, shutdown=False):
        bb = (text + '\r\n').encode('utf-8')
        try:
            n = self._bsd_socket.sendall(bb)
        except socket.error:
            return -1 # Socket closed down badly
        if shutdown:
            try:
                self._bsd_socket.shutdown(socket.SHUT_WR)
            except socket.error:
                pass
    
    def _recv_during_handshaking(self, timeout=2):
        # Init parts (start with one byte, such that len(parts) is always >= 2
        parts = [' '.encode('ascii'),]
        end_bytes = '\r\n'.encode('ascii')
        maxtime = time.time() + timeout
        
        # Receive data
        while True:
            # Get part
            try:
                part = self._bsd_socket.recv(1)
                parts.append(part)
            except socket.error:
                return None # Socket closed down badly
            # Detect end by shutdown (EOF)
            if not part:
                break
            # Detect end by \r\n
            if (parts[-2] + parts[-1]).endswith(end_bytes):
                break
        # Combine parts (discared first (dummy) part)
        bb = bytes().join(parts[1:])
        return bb.decode('utf-8', 'ignore')
