""" Web runtime based on a chrome app

In contrast to running in the chrome browser, this makes the app have
more the look and feel of a desktop app.
"""

import os
import sys

from .common import DesktopRuntime

# todo: icon, sizing, etc.

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
        paths.append(eu("~\\AppData\\Local\\Google\\Chrome\\chrome.exe"))
        paths.append(eu("~\\Local Settings\\Application Data\\Google\\Chrome"))  # xp
        paths = [p + '\\chrome.exe' for p in paths]
    elif sys.platform.startswith('linux'):
        paths.append('/usr/bin/google-chrome-stable')
        paths.append('/usr/bin/google-chrome-beta')
        paths.append('/usr/bin/google-chrome-dev')
    elif sys.platform.startswith('darwin'):
        paths.append('/Applications/Chrome.app')
    
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
    elif sys.platform.startswith('darwin'):
        paths.append('/Applications/Chromium.app')
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


class ChromeAppRuntime(DesktopRuntime):
    """ Desktop runtime based on chrome app. Requires the Chrome or
    Chromium browser to be installed.
    
    Note: icon, sizing and title is not yet supported.
    """
    
    def _launch(self):
        # Get chrome executable
        exe = get_chrome_exe() or get_chromium_exe()
        if exe is None:
            raise RuntimeError('Chrome or Chromium browser was not detected.')
        # Launch url
        url = self._kwargs['url']
        self._start_subprocess([exe, '--incognito', '--app=%s' % url])
