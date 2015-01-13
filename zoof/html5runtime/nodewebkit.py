""" zoof.gui client based on node-webkit.
"""

import os
import time
import subprocess
import threading


def fix_libudef():
    """ Fix the dependency for libudef by making a link to libudef.so.1.
    
    github.com/rogerwang/node-webkit/wiki/The-solution-of-lacking-libudev.so.0 
    """
    
    paths = [
        "/lib/x86_64-linux-gnu/libudev.so.1",  # Ubuntu, Xubuntu, Mint
        "/usr/lib64/libudev.so.1",  # SUSE, Fedora
        "/usr/lib/libudev.so.1",  # Arch, Fedora 32bit
        "/lib/i386-linux-gnu/libudev.so.1",  # Ubuntu 32bit
        ]
    
    target = '/home/almar/projects/pylib/zoof/zoof/exp/libudev.so.0'
    for path in paths:
        if os.path.isfile(path) and not os.path.isfile(target):
            os.symlink(path, target)
            print('linked to', path)


def launch():
    
    exe = '/home/almar/projects/node-webkit-v0.11.5-linux-x64/nw'
    target = '/home/almar/projects/pylib/zoof/zoof/exp'
    cmd = [exe, target] 
    
    env = os.environ.copy()
    if sys.platform.startswith('linux'):
        llp = env.get('LD_LIBRARY_PATH', '')
        env['LD_LIBRARY_PATH'] = target + os.pathsep + llp
    
    p = subprocess.Popen(cmd, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.reader = StreamReader(p)
    p.reader.start()
    return p


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


if __name__ == '__main__':
    fix_libudef()
    p = launch()
