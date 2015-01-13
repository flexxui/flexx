""" zoof.ui client based on XUL (i.e. Firefox browser engine)
"""

import os
import sys
import time
import shutil
import subprocess
import threading

# todo: title should change with title of web page
# todo: set position/size at runtime?
# todo: enable fullscreen - does not seem to work on XUL
# todo: test/fix on Windows, OSX, raspberry


APPLICATION_INI = """
[App]
Vendor=XULTest
Name=myapp
Version=1.0
BuildID=20100902
ID=xulapp@xultest.org

[Gecko]
MinVersion=1.8
MaxVersion=200.*
"""

MAIN_XUL = """
<?xml version="1.0"?>
<?xml-stylesheet href="chrome://global/skin/" type="text/css"?>

<window 
    xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"
    id="webapp-window28"
    title="My Web App"
    windowtype="zoofui:main"
    width="800"
    height="600"
    sizemode="normal"
    >
  <browser type="content-primary"
      src="{{SRC}}"
      flex="1"
      disablehistory="true"/>
    <keyset>
        <key id="key_fullScreen" keycode="VK_F11" command="View:FullScreen"/>
    </keyset>
</window>
""".lstrip()


MAIN_JS = """
"""


# persist="screenX screenY width height sizemode"


target = 'file:///home/almar/projects/pylib/zoof/zoof/exp/learn_html5.html'
#target = "http://helloracer.com/webgl/"

# todo: the page seems to be initialized at zero size, so that content like webgl is very tiny

MAIN_XUL = MAIN_XUL.replace('{{SRC}}', target)

PREFS_JS = """
pref("toolkit.defaultChromeURI", "chrome://myapp/content/main.xul");

pref("toolkit.defaultChromeFeatures", "top=100, left=20000");
 
/* debugging prefs, disable these before you deploy your application! */
pref("browser.dom.window.dump.enabled", false);
pref("javascript.options.showInConsole", false);
pref("javascript.options.strict", false);
pref("nglayout.debug.disable_xul_cache", false);
pref("nglayout.debug.disable_xul_fastload", false);
"""




def create_xul_app(path):
    
    # Clear
    if os.path.isdir(path):
        shutil.rmtree(path)
    
    # Create directory structure
    for subdir in ('',
                   'chrome', 'chrome/content', 
                   'chrome/icons', 'chrome/icons/default',
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
    
    # Icon
    shutil.copy('/home/almar/projects/pyapps/iep/default/iep/resources/appicons/ieplogo64.png',
                os.path.join(path, 'chrome/icons/default/webapp-window28.png'))
    
    # Create link, so that our window is not grouped with ff, and has
    # a more meaningful process name.
    # todo: if frozen, call it myapp-ui, otherwise, python-zoof-ui
    os.symlink('/usr/lib/firefox/firefox', os.path.join(path, 'python-zoof-ui'))


def launch():
    
    create_xul_app('/home/almar/projects/pylib/zoof/zoof/exp/xulapp2')
    
    
    cmd = ['/home/almar/projects/pylib/zoof/zoof/exp/xulapp2/python-zoof-ui', 
           '-app', 
           '/home/almar/projects/pylib/zoof/zoof/exp/xulapp2/application.ini']
    
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
    
    
                