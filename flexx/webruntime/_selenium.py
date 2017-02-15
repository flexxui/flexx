""" Web runtime based on Selenium.

Selenium is a Python library to automate browsers. 

"""

from ._common import BaseRuntime


class SeleniumRuntime(BaseRuntime):
    """ Runtime based on Selenium (http://www.seleniumhq.org/), a tool
    to automate browsers, e.g. for testing. Requires the Python package
    "selenium" to be installed. It's possible that this runtime is currently
    broken.
    """
    
    def __init__(self, type=None, **kwargs):
        self._type = type or ''
        super().__init__(**kwargs)
    
    def _get_install_instuctions(self):
        return ('To enable the Selenium runtime, install selenium '
                'in your Python environment.')
    
    def _get_name(self):
        return 'selenium'
    
    def _get_exe(self):
        try:
            import selenium
            return selenium.__file__
        except ImportError:
            return None
    
    def _get_version(self):
        if self._get_exe():
            import selenium
            return selenium.__version__
    
    def _launch_tab(self, url):
        
        # Get url and browser type
        type = self._type
        self._driver = None
        
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
            raise ValueError('To use selenium runtime specify a browser type".')
        
        # Open page
        self._driver.get(url)
    
    def _launch_app(self, url):
        raise RuntimeError('Selenium runtime cannot run as an app.')
    
    def close(self):
        """ Close the Selenium driver.
        """
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def get_driver(self):
        """ Get the Selenium webdriver object. Use this to control the browser.
        """
        return self._driver
