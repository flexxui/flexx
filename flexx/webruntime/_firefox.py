"""
Web runtime based on Mozilla's Firefox browser engine

This is a well-developed runtime, with tested good behavior on
Windows, OSX, Linux and Raspberry Pi.

Developer notes
---------------

For this runtime we symlink to the Firefox application on Unix, and copy
the Firefox directory on Windows. That way we can make a symlink/copy of the
executable with a name of our chosing, so that we can avoid taskbar grouping.

"""

import os.path as op
import os
import sys
import time
import shutil
import subprocess

from .. import config
from . import logger
from ._common import DesktopRuntime
from ._manage import create_temp_app_dir


## File templates

# The Profile setting makes all apps use the same dummy profile (see issue #150)

APPLICATION_INI = """
[App]
Vendor={vendor}
Name={name}
Version={version}
BuildID={buildid}
ID={id}
Profile=flexx_xul_stub_profile

[Gecko]
MinVersion=1.8
MaxVersion=200.*
"""

MAIN_XUL = """
<?xml version="1.0"?>
<?xml-stylesheet href="chrome://global/skin/" type="text/css"?>

<window
    xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"
    id="{windowid}"
    title="{title}"
    windowtype="flexxui:main"
    width="640"
    height="480"
    sizemode="{sizemode}"
    >
    <script type="application/javascript"
            src="chrome://{name}/content/main.js" />
    <!-- content or content-primary ? -->
    <browser src="{url}"
             id="content"
             type="content"
             flex="1"
             disablehistory="true" />
</window>
""".lstrip()

MAIN_JS = """
"""

# todo: persist="screenX screenY width height sizemode"


PREFS_JS = """
// This tells xulrunner what xul file to use
pref("toolkit.defaultChromeURI", "chrome://{name}/content/main.xul");

// This line is needed to let window.open work
pref("browser.chromeURL", "chrome://{name}/content/main.xul");

// Set features - setting width, height, maximized, etc. here
pref("toolkit.defaultChromeFeatures", "{windowfeatures}");

// debugging prefs, disable these before you deploy your application!
pref("browser.dom.window.dump.enabled", false);
pref("javascript.options.showInConsole", false);
pref("javascript.options.strict", false);
pref("nglayout.debug.disable_xul_cache", false);
pref("nglayout.debug.disable_xul_fastload", false);
"""


# Keep this just in case
def get_firefox_version_unused(exe):
    """Get the version of the given Firefox executable, or None, if the given
    exe does not represent a valid filename.
    """
    version = None
    if exe and op.isfile(exe):
        if 'Contents/MacOS/' in exe:
            inifile = op.join(op.dirname(exe),
                                '../Resources/application.ini')
        else:
            inifile = op.join(op.dirname(exe), 'application.ini')
        for line in open(inifile, 'rb').read().decode().splitlines():
            if line.lower().startswith('version'):
                version = line.split('=')[1].strip()
                break
    return version


class FirefoxRuntime(DesktopRuntime):
    """ Runtime based on Mozilla Firefox. Can be used to open an app in
    Firefox, as well as launch desktop-like apps via Mozilla's XUL framework.
    Available if Firefox is installed.
    
    This runtime is visible in the task manager under a custom process name
    (``sys.executable + '-ui'``), making it easy to spot in the task manager,
    and avoids task-bar grouping. Compared to the NW runtime, this runtime
    is leaner in terms of memory and number of processes.
    """
    
    def _get_name(self):
        return 'firefox'
    
    def _get_install_instuctions(self):
        m = 'Install Mozilla Firefox from http://firefox.com'
        if sys.platform.startswith('linux'):
            m += ', or use your package manager.'
        return m
    
    def _get_exe(self):
        
        # Return user-specified version?
        if config.firefox_exe and self._get_version(config.firefox_exe):
            return config.firefox_exe
        
        paths = []
        
        # Collect possible locations
        if sys.platform.startswith('win'):
            for basepath in ('C:\\Program Files\\', 'C:\\Program Files (x86)\\'):
                paths.append(basepath + 'Mozilla Firefox\\firefox.exe')
                paths.append(basepath + 'Mozilla\\Firefox\\firefox.exe')
                paths.append(basepath + 'Firefox\\firefox.exe')
        elif sys.platform.startswith('linux'):
            paths.append('/usr/lib/firefox/firefox')
            paths.append('/usr/lib64/firefox/firefox')
            paths.append('/usr/lib/iceweasel/iceweasel')
            paths.append('/usr/lib64/iceweasel/iceweasel')
        elif sys.platform.startswith('darwin'):
            osx_user_apps = op.expanduser('~/Applications')
            osx_root_apps = '/Applications'
            paths.append(op.join(osx_user_apps, 'Firefox.app/Contents/MacOS/firefox'))
            paths.append(op.join(osx_root_apps, 'Firefox.app/Contents/MacOS/firefox'))
            if not any([op.isfile(path) for path in paths]):
                # Try harder - use app-id to get the .app path
                try:
                    osx_search_arg='kMDItemCFBundleIdentifier==org.mozilla.firefox'
                    basepath = subprocess.check_output(['mdfind', osx_search_arg])
                    basepath = basepath.rstrip()
                    if basepath:
                        paths.append(op.join(basepath, 'Contents/MacOS/firefox'))
                except (OSError, subprocess.CalledProcessError):
                    pass
    
        # Try location until we find one that exists
        for path in paths:
            if op.isfile(path):
                return path
        
        # Getting desperate ...
        for path in os.getenv('PATH', '').split(os.pathsep):
            if 'firefox' in path.lower() or 'moz' in path.lower():
                for name in ('firefox.exe', 'firefox', 'iceweasel'):
                    if op.isfile(op.join(path, name)):
                        return op.join(path, name)
        
        # Maybe just ... firefox as a command?
        if self._get_version('firefox'):
            return 'firefox'
        
        # We cannot find it
        return None
    
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
        """ Make a local "copy" of the firefox runtime. This should put
        a 'xulrunner' executable in the given path.

        On Windows we must make a copy, so that we can make a copy of
        the runtime exe with the name of our choice, to thereby change
        the process name and avoid taskbar grouping with firefox. On
        other systems we use symlinks. On Windows, when symlinks are
        supported (Python 3.2+, Vista+) they hardly ever work because
        the process has no sufficient privileges.

        On OSX we will create an application "X.app", that symlinks all
        files in the firefox runtime. The symlink that we create here
        is only for reference, and does not actually work.
        """
        if sys.platform.startswith('win'):
            # Windows: copy the whole tuntime
            self._copy_xul_runtime(op.dirname(exe), path)
        else:
            # OSX / Linux: create a symlink to xul runtime exe
            os.mkdir(path)
            os.symlink(exe, op.join(path, 'xulrunner'))
    
    def _launch_app(self, url):
        
        self._check_compat()

        # Get dir to store app definition
        app_path = create_temp_app_dir('firefox')
        id = op.basename(app_path).split('_', 1)[1].replace('~', '_')
        
        # Set size and position
        # Maybe interesting window features: alwaysRaised
        windowfeatures = 'resizable=1,minimizable=1,dialog=0,'
        if self._windowmode == 'normal':
            windowfeatures += 'width=%i,height=%i' % self._size
            if self._pos:
                windowfeatures += ',left=%i,top=%i' % self._pos

        # Create files for app
        self._create_xul_app(app_path, id, url, windowfeatures)

        # Get executable for xul runtime (may be None)
        ff_exe = self.get_exe()
        if not ff_exe:
            raise RuntimeError('Firefox is not available on this system.')
        elif not op.isfile(ff_exe):
            # We have no way to wrap things up in a custom app
            exe = ff_exe
        else:
            # We make sure the runtime is "installed" and mangle the name
            xul_exe = op.join(self.get_runtime_dir(), 'xulrunner')
            xul_exe += '.exe' * sys.platform.startswith('win')
            exe = self._get_app_exe(xul_exe, app_path)
        
        # Prepare profile dir for Xul to let -profile dir point to.
        # This dir is unique for each instance of the app, but because it is
        # inside the app_path, it gets automatically cleaned up.
        profile_dir = op.join(app_path, 'stub_profile')
        if not op.isdir(profile_dir):
            os.mkdir(profile_dir)
        
        # Launch
        cmd = [exe, '-app', op.join(app_path, 'application.ini'),
               '-profile', profile_dir]
        self._start_subprocess(cmd)
    
    def _launch_tab(self, url):
        self._spawn_subprocess([self.get_exe(), url])
    
    def _check_compat(self):
        qts = 'PySide', 'PyQt4', 'PyQt5'
        if any([name+'.QtCore' in sys.modules for name in qts]):
            logger.warn("Using Flexx' Firefox runtime and Qt (PySide/PyQt4/PyQt5) "
                        "together may cause problems.")

    def _create_xul_app(self, path, id, url, windowfeatures):
        """ Create the files that determine the XUL app to launch.
        """
        
        modemap = {'kiosk': 'fullscreen'}
        
        # Dict with all values that are injected in the file templates
        D = dict(vendor='Flexx',
                 name='flexx_ui_app',
                 version='1.0',
                 buildid='1',
                 id='some.app@flexx.io',
                 windowid='xx',
                 title=self._title,
                 url=url,
                 sizemode=modemap.get(self._windowmode, self._windowmode),
                 windowfeatures=windowfeatures)
        
        # Create values that need to be unique
        # Looks like name does not have to be unique, perhapse because we use
        # a custom profile dir. If possible, use static name to avoid XUL from
        # spamming profile dirs (NW did this, so let's be on safe side).
        D['name'] = 'flexx_stub_xul_profile'
        D['windowid'] = 'W' + id
        D['id'] = 'app_' + id + '@flexx.io'
        
        # Fill in arguments in file contents
        manifest_link = 'manifest chrome/chrome.manifest'
        manifest = 'content {name} content/'.format(**D)
        application_ini = APPLICATION_INI.format(**D)
        main_xul = MAIN_XUL.format(**D)
        main_js = MAIN_JS  # No format (also problematic due to braces)
        prefs_js = PREFS_JS.format(**D)

        # Clear
        if op.isdir(path):
            shutil.rmtree(path)

        # Create directory structure
        for subdir in ('',
                       'chrome', 'chrome/content',
                       'chrome/icons', 'chrome/icons/default',
                       'defaults', 'defaults/preferences',
                       ):
            os.mkdir(op.join(path, subdir))

        # Create files
        for fname, text in [('chrome.manifest', manifest_link),
                            ('chrome/chrome.manifest', manifest),
                            ('application.ini', application_ini),
                            ('defaults/preferences/prefs.js', prefs_js),
                            ('chrome/content/main.js', main_js),
                            ('chrome/content/main.xul', main_xul),
                            ]:
            with open(op.join(path, fname), 'wb') as f:
                f.write(text.encode())

        # Icon - use Icon class to write a png (Unix) and an ico (Windows)
        # The DesktopRuntime ensures that there always is an icon
        icon_name = op.join(path, 'chrome/icons/default/' + D['windowid'])
        self._icon.write(icon_name + '.ico')
        self._icon.write(icon_name + '.png')
    
    def _copy_xul_runtime(self, dir1, dir2):
        """ Copy the firefox/xulrunner runtime to a new folder, in which
        we rename the firefox exe to xulrunner. This thus creates a xul
        runtime in a location where we have write access. Used to be able
        to set the process name on Windows, and maybe used to distribute
        apps *with* the runtime.
        """
        t0 = time.time()
        # Get extension
        ext = '.exe' if sys.platform.startswith('win') else ''
        # On Rasberry Pi, the xul runtime is in a (linked) subdir
        if op.isdir(op.join(dir1, 'xulrunner')):
            dir1 = op.join(dir1, 'xulrunner')
        # Clear
        if op.isdir(dir2):
            shutil.rmtree(dir2)
        os.mkdir(dir2)
        try:
            # Copy all files except dirs
            for fname in os.listdir(dir1):
                filename1 = op.join(dir1, fname)
                filename2 = op.join(dir2, fname)
                if op.isfile(filename1):
                    shutil.copy2(filename1, filename2)
            # Copy firefox exe -> xulrunner
            for exe_name in ('firefox', 'iceweasel', 'xulrunner', 'firefox'):
                exe = op.join(dir1, exe_name + ext)
                if op.isfile(exe):
                    break
            shutil.copy2(exe, op.join(dir2, 'xulrunner' + ext))
            logger.info('Copied firefox in %1.1f s' % (time.time()-t0))
        except Exception:
            # Clean up
            shutil.rmtree(dir2)
            raise
