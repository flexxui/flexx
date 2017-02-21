""" Web runtime based on a chrome/chromium.

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

from .. import config
from ._common import DesktopRuntime, find_osx_exe


class ChromeRuntime(DesktopRuntime):
    """ Runtime representing either the Google Chrome or Chromium browser.
    This runtime does support desktop-like apps, which works pretty well on
    Windows, but not so much on OS X and Linux:

    * On Linux it has the Chrome/Chromium icon.
    * On OSX and Linux it groups with the Chrome/Chromium browser.
    * Fullscreen mode does not work on OS X.
    """
    
    # Note, this is not an abstract class, but a proxy class for either browser
    
    def _get_name(self):
        return 'chrome'
    
    def _get_install_instuctions(self):
        m = 'Install Chrome from http://chrome.com or https://www.chromium.org'
        if sys.platform.startswith('linux'):
            m += ', or use your package manager.'
        return m
    
    def _get_version(self, exe=None):
        if exe is None:
            exe = self.get_exe()
            if exe is None:
                return
        
        # Get raw version string (as bytes)
        if sys.platform.startswith('win'):
            if not op.isfile(exe):
                return
            version = subprocess.check_output(['wmic', 'datafile', 'where',
                                               'name=%r' % exe,
                                               'get', 'Version', '/value'])
        else:
            version = subprocess.check_output([exe, '--version'])
        
        # Clean up
        parts = version.decode().strip().replace('=', ' ').split(' ')
        for part in parts:
            if part and part[0].isnumeric():
                return part
    
    def _get_system_version(self):
        return self.get_version(), self.get_exe()
    
    def _install_runtime(self, exe, path):
        """ Symlink on Unix. Stub in Windows. In contrast to XUL, exe
        renaming is not needed to avoid grouping on Windows. Plus the
        firewall would asks permission for each new exe that we use
        this way. Ironically, there seems to be nothing we can do to avoid
        grouping on Linux and OS X.
        """
        if sys.platform.startswith('win'):
            os.mkdir(path)
            with open(op.join(path, 'stub.txt'), 'wb') as f:
                f.write('Flexx uses the system Chrome'.encode())
        else:
            # This makes a nice icon on OS X, but it still groups with Chrome!
            os.mkdir(path)
            os.symlink(exe, op.join(path, 'chrome'))
    
    def _launch_tab(self, url):
        self._spawn_subprocess([self.get_exe(), url])
    
    def _launch_app(self, url):
        
        # Don't bother with create_temp_app_dir(); its only advantage would be
        # having an icon on OS X, but since it's grouped with Chrome, leave it.
        
        # Get chrome executable, but don't really use it
        self.get_runtime_dir()
        
        exe = self.get_exe()
        if exe is None:
            raise RuntimeError('Chrome/Chromium is not available on this system.')
        
        # No way to set icon and title. On Windows, Chrome uses document
        # title/icon. On OS X we create an app. On Linux ... tough luck
        # self._title ...
        # self._icon ...
        
        # Options
        opts = ['--incognito']
        opts.append('--enable-unsafe-es3-apis')  # enable webgl2
        opts.append('--window-size=%i,%i' % self._size)
        if self._pos:
            opts.append('--window-position=%i,%i' % self._pos)
        if self._windowmode == 'kiosk':
            opts.append('--kiosk')
        elif self._windowmode == 'fullscreen':
            opts.append('--start-fullscreen')
        elif self._windowmode == 'maximized':
            opts.append('--start-maximized')
        
        # Launch url, important to put opts before --app=xx
        self._start_subprocess([exe] + opts + ['--app=%s' % url])
        # self._spawn_subprocess([exe] + opts + ['--app=%s' % url])
    
    def _get_exe(self):
        return self._get_google_chrome_exe() or self._get_chromium_exe()
    
    def _get_google_chrome_exe(self):
        
        # Return user-specified version?
        # Note that its perfectly fine to specify a chromium exe here 
        if config.chrome_exe and self._get_version(config.chrome_exe):
            return config.chrome_exe
        
        paths = []
        
        # Collect possible locations
        if sys.platform.startswith('win'):
            paths.append(r"C:\Program Files\Google\Chrome\Application")
            paths.append(r"C:\Program Files (x86)\Google\Chrome\Application")
            paths.append(r"~\AppData\Local\Google\Chrome\Application")
            paths.append(r"~\Local Settings\Application Data\Google\Chrome")
            paths = [op.expanduser(p + '\\chrome.exe') for p in paths]
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
                    dir = op.expanduser(dir)
                    if op.isdir(dir):
                        paths.append(op.join(dir, 'Contents/MacOS/Chrome'))
                        paths.append(op.join(dir, 'Contents/MacOS/Google Chrome'))
        
        # Try location until we find one that exists
        for path in paths:
            if op.isfile(path):
                return path
        
        # Getting desperate ...
        for path in os.getenv('PATH', '').split(os.pathsep):
            if 'chrome' in path.lower():
                for name in ('chrome.exe', 'chrome', 'google-chrome', 'Google Chrome'):
                    if op.isfile(op.join(path, name)):
                        return op.join(path, name)
        
        # We cannot find it
        return None

    
    def _get_chromium_exe(self):
        paths = []
        
        # Collect possible locations
        if sys.platform.startswith('win'):
            paths.append(r"C:\Program Files\Chromium\Application")
            paths.append(r"C:\Program Files (x86)\Chromium\Application")
            paths.append(r"~\AppData\Local\Chromium\chrome.exe")
            paths.append(r"~\AppData\Local\Chromium\Application")
            paths.append(r"~\Local Settings\Application Data\Chromium")
            paths = [op.expanduser(p + '\\chrome.exe') for p in paths]
        elif sys.platform.startswith('linux'):
            paths.append('/usr/bin/chromium')
            paths.append('/usr/bin/chromium-browser')
        elif sys.platform.startswith('darwin'):
            app_dirs = ['~/Applications/Chromium', '~/Applications/Chromium',
                        find_osx_exe('org.chromium.Chromium')]
            for dir in app_dirs:
                if dir:
                    dir = op.expanduser(dir)
                    if op.isdir(dir):
                        paths.append(op.join(dir, 'Contents/MacOS/Chromium'))
                        paths.append(op.join(dir, 'Contents/MacOS/Chromium Browser'))
        
        # Try location until we find one that exists
        for path in paths:
            if op.isfile(path):
                return path
        
        # Getting desperate ...
        for path in os.getenv('PATH', '').split(os.pathsep):
            if 'chromium' in path.lower():
                for name in ('chrome.exe', 'chromium',
                             'chromium-browser', 'Chromium Browser'):
                    if op.isfile(op.join(path, name)):
                        return op.join(path, name)
        
        # We cannot find it
        return None


class GoogleChromeRuntime(ChromeRuntime):
    """ Runtime based on the Google Chrome browser. Derives from ChromeRuntime.
    """
    
    def _get_name(self):
        return 'googlechrome'
    
    def _get_exe(self):
        return self._get_google_chrome_exe()
    
    def _get_install_instuctions(self):
        return 'Install Google Chrome from http://chrome.com'


class ChromiumRuntime(ChromeRuntime):
    """ Runtime based on the Chromium browser. Derives from ChromeRuntime.
    """
    
    def _get_name(self):
        return 'chromium'
    
    def _get_exe(self):
        return self._get_chromium_exe()
    
    def _get_install_instuctions(self):
        m = 'Install Chromium from https://www.chromium.org'
        if sys.platform.startswith('linux'):
            m += ', or use your package manager.'
        return m
