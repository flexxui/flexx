""" Web runtime based on a chrome app

In contrast to running in the chrome browser, this makes the app have
more the look and feel of a desktop app.
"""

import os
import sys

from .common import WebRuntime

# todo: icon, sizing, etc.

def get_chrome_exe():
    """ Get the path of the Chrome executable
    
    If the path could not be found, returns None.
    """
    paths = []
    
    # Collect possible locations
    if sys.platform.startswith('win'):
        paths.append("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        paths.append("C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe")
        paths.append(os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\chrome.exe"))
        paths.append(os.path.expanduser("~\\Local Settings\\Application Data\\Google\\Chrome\\chrome.exe"))  # xp
    elif sys.platform.startswith('linux'):
        paths.append('/usr/lib/google-chrome/google-chrome')
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
    
    # Collect possible locations
    if sys.platform.startswith('win'):
        paths.append("C:\\Program Files\\Chromium\\Application\\chrome.exe")
        paths.append("C:\\Program Files (x86)\\Chromium\\Application\\chrome.exe")
        paths.append(os.path.expanduser("~\\AppData\\Local\\Chromium\\chrome.exe"))
        paths.append(os.path.expanduser("~\\Local Settings\\Application Data\\Chromium\\chrome.exe"))  # xp
       
    elif sys.platform.startswith('linux'):
        paths.append('/usr/lib/chromium-browser/chromium-browser')
    elif sys.platform.startswith('darwin'):
        paths.append('/Applications/Chromium.app')
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


class ChromeAppRuntime(WebRuntime):
    """ Web runtime based on chrome app.
    """
    
    def _launch(self):
        # Get chrome executable
        exe = get_chrome_exe() or get_chromium_exe()
        if exe is None:
            raise RuntimeError('Chrome or Chromium browser was not detected.')
        # Launch url
        url = self._kwargs['url']
        self._start_subprocess([exe, '--incognito', '--app=%s' % url])
