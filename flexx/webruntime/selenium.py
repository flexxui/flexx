""" Web runtime based on Selenium.

Selenium is a Python library to automate browsers. 

"""

import os
import logging

from .common import BaseRuntime


class SeleniumRuntime(BaseRuntime):
    """ Runtime based on Selenium (http://www.seleniumhq.org/), a tool
    to automate browsers, e.g. for testing. Requires the Python package
    "selenium" to be installed.
    """
    
    def _launch(self):
        
        # Get url and browser type
        url = self._kwargs['url']
        type = self._kwargs.get('type', '')
        
        # Import here; selenium is an optional dependency
        from selenium import webdriver
        
        if type.lower() == 'firefox':
            self._driver = webdriver.Firefox()
        elif type.lower() == 'chrome':
            self._driver = webdriver.Chrome()
        elif type.lower() == 'ie':
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
