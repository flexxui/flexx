""" HTML5 runtime based on a common browser

Opens browser via webbrowser module.
"""

import webbrowser
import logging

from .common import HTML5Runtime


BROWSER_MAP = {'chrome': ['google-chrome', 'chrome', 
                          'chromium-browser', 'chromium'],
               'chromium': ['chromium-browser', 'chromium'],
               'default': [],
               }


class BrowserRuntime(HTML5Runtime):
    
    def _launch(self):
        
        # Get url and browser type
        url = self._kwargs['url']
        type = self._kwargs.get('browsertype', '')
        
        # Get alternative types
        types = BROWSER_MAP.get(type, [type])
        types = [t for t in types if t]
        
        # Try to open all possibilities
        errors = []
        for t in types:
            try:
                b = webbrowser.get(t)
            except webbrowser.Error as err:
                errors.append(str(err))
            else:
                b.open(url)
                return
        
        if errors:
            logging.warn('Given browser %r not valid/available;\n'
                         'Falling back to the default browser.' % type)
        
        # Run default
        webbrowser.open(url)
