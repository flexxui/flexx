""" zoof.ui client based on XUL (i.e. Firefox browser engine)
"""

import os
import time
import shutil
import subprocess
import threading


MAIN_JS = """
"""

MAIN_XUL = """<?xml version="1.0"?>

<?xml-stylesheet href="chrome://global/skin/" type="text/css"?>

<window xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"
    title="My Web App"
    id="webapp-window"
    width="800"
    height="600"
    persist="screenX screenY width height sizemode">
  <browser type="content-primary"
      src="{{SRC}}"
      flex="1"
      disablehistory="true"/>
</window>
"""
target = 'file:///home/almar/projects/pylib/zoof/zoof/exp/learn_html5.html'
#target = "http://helloracer.com/webgl/"

# todo: the page seems to be initialized at zero size, so that content like webgl is very tiny

MAIN_XUL = MAIN_XUL.replace('{{SRC}}', target)

PREFS_JS = """
pref("toolkit.defaultChromeURI", "chrome://myapp/content/main.xul");

/* debugging prefs, disable these before you deploy your application! */
pref("browser.dom.window.dump.enabled", true);
pref("javascript.options.showInConsole", true);
pref("javascript.options.strict", false);
pref("nglayout.debug.disable_xul_cache", true);
pref("nglayout.debug.disable_xul_fastload", true);
"""

APPLICATION_INI = """
[App]
Vendor=XULTest
Name=myapp
Version=1.0
BuildID=20100901
ID=xulapp@xultest.org

[Gecko]
MinVersion=1.8
MaxVersion=200.*
"""


def create_xul_app(path):
    
    # Clear
    if os.path.isdir(path):
        shutil.rmtree(path)
    
    # Create directory structure
    for subdir in ('',
                   'chrome', 'chrome/content',
                   'defaults', 'defaults/preferences',
                   ):
        os.mkdir(os.path.join(path, subdir))
    
    # Create files
    for fname, text in [('chrome.manifest', 'manifest chrome/chrome.manifest'),
                        ('chrome/chrome.manifest', 'content myapp content/'),
                        ('application.ini', APPLICATION_INI),
                        ('defaults/preferences/prefs.js', PREFS_JS),
                        ('chrome/content/main.js', MAIN_JS),
                        ('chrome/content/main.xul', MAIN_XUL),
                        ]:
        open(os.path.join(path, fname), 'wb').write(text.encode('utf-8'))


def launch():
    
    create_xul_app('/home/almar/projects/pylib/zoof/zoof/exp/xulapp2')
    
    cmd = ['firefox', '-app', '/home/almar/projects/pylib/zoof/zoof/exp/xulapp2/application.ini']
    
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
        
        # Poll to get return code. Polling also helps to really
        # clean the process up
        while self._process.poll() is None:
            time.sleep(0.05)
        print('process stopped (%i)' % self._process.poll())


if __name__ == '__main__':
    p = launch()
    
    
                