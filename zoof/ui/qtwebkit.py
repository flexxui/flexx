""" zoof.gui client based on qt-webkit.
"""

import os
import time
import subprocess
import threading


CODE_TO_RUN = """
from zoof.qt import QtGui, QtCore, QtWebKit

url = "%s"

app = QtGui.QApplication([])
m = QtWebKit.QWebView(None)
m.show()
m.setUrl(QtCore.QUrl(url))
app.exec_()
"""


def launch():
    
    target = '/home/almar/projects/pylib/zoof/zoof/exp/learn_html5.html'
    #target = "http://helloracer.com/webgl/"
    code = CODE_TO_RUN % target
    
    cmd = [sys.executable, '-c', code] 
    #cmd = ['chromium-browser', '--incognito', '--app=%s' % target] 
    
    env = os.environ.copy()
    p = subprocess.Popen(cmd, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.reader = StreamReader(p)
    p.reader.start()
    return p


# todo: make this a util
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
    p = launch()
