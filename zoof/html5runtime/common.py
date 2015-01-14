"""
Common code for all runtimes.
"""

import os
import sys
import time
import atexit
import threading
import subprocess
import tempfile


class HTML5Runtime(object):
    def __init__(self, **kwargs):
        assert 'url' in kwargs
        self._kwargs = kwargs
        self._proc = None
        self._streamreader = None
        self._launch()
        atexit.register(self.close)
    
    def close(self):
        """ Close the runtime
        
        If it won't close in a nice way, it is killed.
        """
        if self._proc is None:
            return
        # Terminate, wait for a bot, kill
        self._proc.terminate()
        timeout = time.time() + 0.25
        while time.time() > timeout:
            time.sleep(0.02)
            if self._proc.poll() is not None:
                break
        else:
            self._proc.kill()
        # Discart process
        self._proc = None
    
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
        self.setDaemon(True)
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
        print('runtime process stopped (%i)' % self._process.poll())


def create_temp_app_dir(prefix, suffix='', cleanup=60):
    """ Create a temporary direrctory and return path
    
    The directory will be named "<prefix>_<timestamp>_<pid>_<suffix>".
    Will clean up directories with the same prefix which are older than
    cleanup seconds.
    """
    
    # Select main dir
    maindir = os.path.join(tempfile.gettempdir(), 'zoof')
    if not os.path.isdir(maindir):
        os.mkdir(maindir)
    
    prefix = prefix.strip(' _-') + '_'
    suffix = '' if not suffix else '_' + suffix.strip(' _-')
    
    # Clear any old files
    for dname in os.listdir(maindir):
        if dname.startswith(prefix):
            dirname = os.path.join(maindir, dname)
            if os.path.isdir(dirname):
                try:
                    dirtime = int(dname.split('_')[1])
                except Exception:
                    pass
                if (time.time() - dirtime) > cleanup:
                    try:
                        shutil.rmtree(dirname)
                    except Exception:
                        pass
    
    # Return new dir
    id = '%i_%i' % (time.time(), os.getpid())
    path = os.path.join(maindir, prefix + id + suffix)
    os.mkdir(path)
    return path
