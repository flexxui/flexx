""" Web runtime based on a chrome app

In contrast to running in the chrome browser, this makes the app have
more the look and feel of a desktop app.

It is possible to make a chrome app with a custom icon on Windows (because
it uses the (initial) favicon of the page) and OS X (because how apps work).
I tried hard to make it work on Linux via a .desktop file, but the problem
is that Chome explicitly sets its icon (Chromium does not). Further, both
Chrome and Chromium reset the process name (arg zero), causing the app to be
grouped with Chrome. This makes Chrome not an ideal runtime for apps; use
the NW runtime to effectively make use of the Chromium runtime.
"""

import os.path as op
import os
import sys
import subprocess

from .common import DesktopRuntime, find_osx_exe
from ._manage import RUNTIME_DIR


# todo: icon,  etc.


def get_chrome_exe():
    """ Get the path of the Chrome executable
    
    If the path could not be found, returns None.
    """
    paths = []
    eu = os.path.expanduser
    
    # Collect possible locations
    if sys.platform.startswith('win'):
        paths.append("C:\\Program Files\\Google\\Chrome\\Application")
        paths.append("C:\\Program Files (x86)\\Google\\Chrome\\Application")
        paths.append(eu("~\\AppData\\Local\\Google\\Chrome\\Application"))
        paths.append(eu("~\\Local Settings\\Application Data\\Google\\Chrome"))  # xp
        paths = [p + '\\chrome.exe' for p in paths]
    elif sys.platform.startswith('linux'):
        paths.append('/usr/bin/google-chrome')
        paths.append('/usr/bin/google-chrome-stable')
        paths.append('/usr/bin/google-chrome-beta')
        paths.append('/usr/bin/google-chrome-dev')
    elif sys.platform.startswith('darwin'):
        app_dirs = ['~/Applications/Chrome', '~/Applications/Google Chrome',
                    '/Applications/Chrome', '/Applications/Google Chrome',
                    find_osx_exe('com.google.Chrome')]
        for dir in app_dirs:
            if dir:
                dir = os.path.expanduser(dir)
                if op.isdir(dir):
                    paths.append(op.join(dir, 'Contents/MacOS/Chrome'))
                    paths.append(op.join(dir, 'Contents/MacOS/Google Chrome'))
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


def get_chromium_exe():
    """ Get the path of the Chromium executable
    
    If the path could not be found, returns None.
    """
    paths = []
    eu = os.path.expanduser
    
    # Collect possible locations
    if sys.platform.startswith('win'):
        paths.append("C:\\Program Files\\Chromium\\Application\\chrome.exe")
        paths.append("C:\\Program Files (x86)\\Chromium\\Application\\chrome.exe")
        paths.append(eu("~\\AppData\\Local\\Chromium\\chrome.exe"))
        paths.append(eu("~\\Local Settings\\Application Data\\Chromium\\chrome.exe"))
       
    elif sys.platform.startswith('linux'):
        paths.append('/usr/bin/chromium')
        paths.append('/usr/bin/chromium-browser')
    elif sys.platform.startswith('darwin'):
        app_dirs = ['~/Applications/Chromium', '~/Applications/Chromium',
                    find_osx_exe('org.chromium.Chromium')]
        for dir in app_dirs:
            if dir:
                dir = os.path.expanduser(dir)
                if op.isdir(dir):
                    paths.append(op.join(dir, 'Contents/MacOS/Chromium'))
                    paths.append(op.join(dir, 'Contents/MacOS/Chromium Browser'))
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


class ChromeAppRuntime(DesktopRuntime):
    """ Desktop runtime based on the Chrome/Chromium browser. This runtime
    is somewhat limited in that it has a Chrome icon on Linux and the app
    tends to group on the taskbar with the Chrome/Chromium browser. 
    
    Note: icon, sizing and title is not yet supported.
    """
    
    def _get_name(self):
        return 'chrome'
    
    def _install_runtime(self):
        version = 'latest'
        path = os.path.join(RUNTIME_DIR, self.get_name() + '_' + version)
        if not os.path.isdir(path):
            os.mkdir(path)
        with open(os.path.join(path, 'stub.txt'), 'wb') as f:
            f.write('Flexx uses the system Chrome'.encode())
    
    def _launch(self):
        # Get chrome executable
        self.get_runtime('latest')
        exe = get_chrome_exe() or get_chromium_exe()
        if exe is None:
            raise RuntimeError('Chrome or Chromium browser was not detected.')
            # todo: dialite
        
        # Options
        size = self._kwargs.get('size', (640, 480))
        pos = self._kwargs.get('pos', None)
        #
        opts = ['--incognito']
        opts.append('--enable-unsafe-es3-apis')  # enable webgl2
        opts.append('--window-size=%i,%i' %  (size[0], size[1]))
        if pos:
            opts.append('--window-position=%i,%i' %  (pos[0], pos[1]))
        
        # Launch url
        url = self._kwargs['url']
        self._start_subprocess([exe, '--app=%s' % url] + opts)
