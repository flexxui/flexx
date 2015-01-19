"""
Common code for all runtimes.
"""

import os
import sys
import time
import shutil
import atexit
import threading
import subprocess

from zoof.html5runtime.icon import Icon


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
    
    def _start_subprocess(self, cmd, **env):
        environ = os.environ.copy()
        environ.update(env)
        try:
            self._proc = subprocess.Popen(cmd, env=environ,
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.STDOUT)
        except OSError:
            raise RuntimeError('Invalid command to start runtime: %r' % cmd[0])
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
    maindir = os.path.join(appdata_dir('zoof'), 'temp_apps')
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
                    except (OSError, IOError):
                        pass
    
    # Return new dir
    id = '%i_%i' % (time.time(), os.getpid())
    path = os.path.join(maindir, prefix + id + suffix)
    os.mkdir(path)
    return path


# From pyzolib/paths.py (https://bitbucket.org/pyzo/pyzolib/src/tip/paths.py)
def appdata_dir(appname=None, roaming=False, macAsLinux=False):
    """ appdata_dir(appname=None, roaming=False,  macAsLinux=False)
    Get the path to the application directory, where applications are allowed
    to write user specific files (e.g. configurations). For non-user specific
    data, consider using common_appdata_dir().
    If appname is given, a subdir is appended (and created if necessary). 
    If roaming is True, will prefer a roaming directory (Windows Vista/7).
    If macAsLinux is True, will return the Linux-like location on Mac.
    """
    
    # Define default user directory
    userDir = os.path.expanduser('~')
    
    # Get system app data dir
    path = None
    if sys.platform.startswith('win'):
        path1, path2 = os.getenv('LOCALAPPDATA'), os.getenv('APPDATA')
        path = (path2 or path1) if roaming else (path1 or path2)
    elif sys.platform.startswith('darwin') and not macAsLinux:
        path = os.path.join(userDir, 'Library', 'Application Support')
    # On Linux and as fallback
    if not (path and os.path.isdir(path)):
        path = userDir
    
    # Maybe we should store things local to the executable (in case of a 
    # portable distro or a frozen application that wants to be portable)
    prefix = sys.prefix
    if getattr(sys, 'frozen', None): # See application_dir() function
        prefix = os.path.abspath(os.path.dirname(sys.path[0]))
    for reldir in ('settings', '../settings'):
        localpath = os.path.abspath(os.path.join(prefix, reldir))
        if os.path.isdir(localpath):
            try:
                open(os.path.join(localpath, 'test.write'), 'wb').close()
                os.remove(os.path.join(localpath, 'test.write'))
            except IOError:
                pass # We cannot write in this directory
            else:
                path = localpath
                break
    
    # Get path specific for this app
    if appname:
        if path == userDir:
            appname = '.' + appname.lstrip('.') # Make it a hidden directory
        path = os.path.join(path, appname)
        if not os.path.isdir(path):
            os.mkdir(path)
    
    # Done
    return path


_icon_template = """
xxxx  x   x  xxx
  x  x x x x x
 x   x x x x xxx
xxxx  x   x  x

 xx   xxx   xxx
x  x  x  x  x  x
xxxx  xxx   xxx 
x  x  x     x
"""


def default_icon():
    """ Generate a default icon object.
    """
    im = bytearray(4*16*16)
    for y, line in enumerate(_icon_template.splitlines()):
        y += 5
        if y < 16:
            for x, c in enumerate(line):
                if c == 'x':
                    i = (y * 16 + x) * 4
                    im[i:i+4] = [0, 0, 150, 255]
        
    icon = Icon()
    icon.add(im)
    return icon
