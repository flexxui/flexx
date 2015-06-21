""" Web runtime based on Selenium.

Selenium is a Python library to automate browsers. 

"""

import os
import logging

from .common import WebRuntime


class SeleniumRuntime(WebRuntime):
    """ Web runtime based on Selenium.
    """
    
    def _launch(self):
        
        # Get url and browser type
        url = self._kwargs['url']
        type = self._kwargs.get('browsertype', '')
        
        # Import here; selenium is an optional dependency
        from selenium import webdriver
        
        # If that did not work, maybe we should try harder
        # In particular on Windows, the exes may simply not be on the path
        if type.lower() == 'firefox':
            # from .xul import get_firefox_exe
            # exe = get_firefox_exe()
            # if exe:
            #     os.environ['PATH'] += os.pathsep + os.path.dirname(exe)
            self._driver = webdriver.Firefox()
        
        elif type.lower() == 'chrome':
            # from .chromeapp import get_chrome_exe
            # exe = get_chrome_exe() or 'google-chrome'
            # if exe:
            #     os.environ['PATH'] += os.pathsep + os.path.dirname(exe)
            self._driver = webdriver.Chrome()
        
        elif type.lower() == 'ie':
            from .mshtml import get_ie_exe
            # exe = get_ie_exe()
            # if exe:
            #     os.environ['PATH'] += os.pathsep + exe
            self._driver = webdriver.Ie()
        
        elif type:
            classname = None
            type2 = type[0].upper() + type[1:]
            if hasattr(webdriver, type):
                classname = type
            elif hasattr(webdriver, type2):
                classname = type2
            
            if classname:
                self._driver = getattr(webdriver, classname)()
            else:
                raise ValueError('Unknown Selenium browser type %r' % type)
            
        else:
            raise ValueError('Selenium runtime needs to know "browsertype".')
    
    @property
    def driver(self):
        """ The Selenium webdriver object. Use this to control the browser.
        """
        return self._driver
