"""
Common code for all runtimes.
"""

import os
import sys
import time
import threading
import subprocess


class HTML5Runtime(object):
    def __init__(self, url, **kwargs):
        self._url = url
        self._kwargs = kwargs
        self._proc = None
        self._streamreader = None
        self._launch()
    
    def close(self):
        """ Close the runtime
        
        If it won't close in a nice way, it is killed.
        """
    
    def _start_subprocess(self, command, **env):
        environ = os.environ.copy()
        environ.update(env)
        self._proc = subprocess.Popen(command, env=environ,
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.STDOUT)
        self._streamreader = StreamReader(self._proc)
        self._streamreader.start()
    
    def _launch(self):
        raise NotImplementedError()
    
    #def set_title
    #def set_size
    #def set_icon
    #def set_pos


class StreamReader(threading.Thread):
    """ Reads stdout of process and print
    
    This needs to be done in a separate thread because reading from a
    PYPE blocks.
    """
    def __init__(self, process):
        threading.Thread.__init__(self)
        
        self._process = process
        self.deamon = True
        self._exit = False
    
    def stop(self, timeout=1.0):
        self._exit = True
        self.join(timeout)
    
    def run(self):
        while not self._exit:
            time.sleep(0.001)
            msg = self._process.stdout.readline()  # <-- Blocks here
            if not msg:
                break  # Process dead  
            if not isinstance(msg, str):
                msg = msg.decode('utf-8', 'ignore')
            print('UI: ' + msg)
        
        # Poll to get return code. Polling also helps to really
        # clean the process up
        while self._process.poll() is None:
            time.sleep(0.05)
        print('process stopped (%i)' % self._process.poll())
