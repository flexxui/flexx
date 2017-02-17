""" Web runtime based on a common browser

Opens browser via webbrowser module.
"""

import webbrowser

from . import logger
from ._common import BaseRuntime


BROWSER_MAP = {'chrome': ['google-chrome', 'chrome', 
                          'chromium-browser', 'chromium'],
               'chromium': ['chromium-browser', 'chromium'],
               'default': [],
               }


class BrowserRuntime(BaseRuntime):
    """ Runtime based on the Python webbrowser module. This runtime is used
    to open a url in the system default browser, and to attempt to handle a
    given browser name that is unknown to Flexx (maybe the webbrowser module
    knows it).
    """
    
    def __init__(self, type=None, **kwargs):
        self._type = type or ''
        super().__init__(**kwargs)
    
    def _get_install_instuctions(self):
        return ''  # we know nothing of the browsers
    
    def _get_name(self):
        return 'browser'
    
    def _get_exe(self):
        b, errors = self._get_openers(self._type)
        if not self._type:
            return 'stub_exe_default_browser'
        elif b:
            return 'stub_exe_%s_browser' % self._type
    
    def _get_version(self):
        return None
    
    def _launch_tab(self, url):
        
        b, errors = self._get_openers(self._type)
        if b:
            b.open(url)
        else:
            if errors:
                logger.warn('Given browser %r not valid/available;\n'
                            'Falling back to the default browser.' % type)
            # Run default
            webbrowser.open(url)
    
    def _launch_app(self, url):
        raise RuntimeError('Browser runtime cannot run as an app.')
    
    def _get_openers(self, type):
        # Get alternative types
        types = BROWSER_MAP.get(type, [type])
        types = [t for t in types if t]
        
        # Use default browser
        if not types:
            return webbrowser, []
        
        # Try to open all possibilities
        errors = []
        b = None
        for t in types:
            try:
                b = webbrowser.get(t)
                break
            except webbrowser.Error as err:
                errors.append(str(err))
        return b, errors
