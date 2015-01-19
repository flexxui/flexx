""" Web runtime based on XUL (i.e. Firefox browser engine)
"""

import os
import sys
import time
import shutil
import subprocess

from .common import WebRuntime, create_temp_app_dir, appdata_dir, default_icon
from .icon import Icon

# todo: title should change with title of web page?
# todo: enable setting position/size at runtime?
# todo: enable fullscreen - does not seem to work on XUL
# todo: test/fix on Windows, OSX, raspberry


defaults = dict(vendor='None',
                name='zoof_ui_app',
                version='1.0',
                buildid='1',
                id='some.app@zoof.io',
                windowid='xx',
                title='XUL app runtime')


APPLICATION_INI = """
[App]
Vendor={vendor}
Name={name}
Version={version}
BuildID={buildid}
ID={id}

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
    windowtype="zoofui:main"
    width="640"
    height="480"
    sizemode="normal"
    >
  <browser type="content" src="{url}" flex="1" disablehistory="true" />
    <keyset>
        <key id="key_fullScreen" keycode="VK_F11" command="View:FullScreen"/>
    </keyset>
</window>
""".lstrip()


MAIN_JS = """
"""
# persist="screenX screenY width height sizemode"


PREFS_JS = """
pref("toolkit.defaultChromeURI", "chrome://{name}/content/main.xul");

pref("toolkit.defaultChromeFeatures", "{windowfeatures}");
 
/* debugging prefs, disable these before you deploy your application! */
pref("browser.dom.window.dump.enabled", false);
pref("javascript.options.showInConsole", false);
pref("javascript.options.strict", false);
pref("nglayout.debug.disable_xul_cache", false);
pref("nglayout.debug.disable_xul_fastload", false);
"""


def create_xul_app(path, id, **kwargs):
    """ Create the files that determine the XUL app to launch
    """
    
    D = defaults.copy()
    D.update(kwargs)
    
    # Create values that need to be unique
    D['windowid'] = 'W' + id
    D['name'] = 'app_' + id
    D['id'] = 'app_' + id + '@zoof.io'
    
    # Fill in arguments in file contents
    manifest = 'content {name} content/'.format(**D)
    application_ini = APPLICATION_INI.format(**D)
    main_xul = MAIN_XUL.format(**D)
    main_js = MAIN_JS.format(**D)
    prefs_js = PREFS_JS.format(**D)
    
    # Clear
    if os.path.isdir(path):
        shutil.rmtree(path)
    
    # Create directory structure
    for subdir in ('',
                   'chrome', 'chrome/content', 
                   'chrome/icons', 'chrome/icons/default',
                   'defaults', 'defaults/preferences',
                   ):
        os.mkdir(os.path.join(path, subdir))
    
    # Create files
    for fname, text in [('chrome.manifest', 'manifest chrome/chrome.manifest'),
                        ('chrome/chrome.manifest', manifest),
                        ('application.ini', application_ini),
                        ('defaults/preferences/prefs.js', prefs_js),
                        ('chrome/content/main.js', main_js),
                        ('chrome/content/main.xul', main_xul),
                        ]:
        open(os.path.join(path, fname), 'wb').write(text.encode('utf-8'))
    
    # Icon - use Icon class to write a png (for Unix) and an ico (for Windows)
    if kwargs.get('icon'):
        icon = Icon(kwargs['icon'])  # accepts ico/png/bmp
    else:
        icon = default_icon()
    icon_name = os.path.join(path, 'chrome/icons/default/' + D['windowid'])
    icon.write(icon_name + '.ico')
    icon.write(icon_name + '.png')



def get_firefox_exe():
    """ Get the path of the Firefox executable
    
    If the path could not be found, returns None. You may still be able
    to launch using "firefox" though.
    """
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
    elif sys.platform.startswith('darwin'):
        paths.append('/Applications/Firefox.app')
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


def get_xul_runtime():
    """ Get path to executable for the xul runtime. The given path is
    in a writable directory; we copy the firefox runtime if necessary.
    Returns None if no XUL runtime could be found.
    """
    # Get location of firefox
    ff_exe = get_firefox_exe()
    ff_version = ''
    if ff_exe:
        # Get version
        inifile = os.path.join(os.path.dirname(ff_exe), 'application.ini')
        for line in open(inifile, 'rb').read().decode('utf-8').splitlines():
            if line.lower().startswith('version'):
                ff_version = 'xul_' + line.split('=')[1].strip()
                break
    
    # Get dir with runtimes and list of subdirs (that represent versions)
    xuldir = os.path.join(appdata_dir('zoof'), 'webruntimes')
    if not os.path.isdir(xuldir):
        os.mkdir(xuldir)
    dnames = [d for d in sorted(os.listdir(xuldir)) if d.startswith('xul_')]
    
    # Must we install ff?
    if ff_version:
        if (not dnames) or (dnames[-1] < ff_version):
            copy_firefox_runtime(os.path.dirname(ff_exe),
                                 os.path.join(xuldir, ff_version))
            dnames.append(ff_version)
    
    # Clean up old runtimes
    for dname in dnames[:-1]:
        print('clearing', dname)
        try:
            shutil.rmtree(os.path.join(xuldir, dname))
        except (OSError, IOError):
            pass
    
    # Get highest version
    if dnames:
        the_exe = os.path.join(xuldir, dnames[-1], 'xulrunner-stub')
        the_exe += '.exe' if sys.platform.startswith('win') else ''
        return the_exe
    else:
        return None


def copy_firefox_runtime(dir1, dir2):
    """ Copy the firefox runtime to a new folder, in which we rename
    the firefox exe to xulrunner-stub. This thus creates a xul runtime
    in a location where we have write access, so that we can duplicate
    the exe with a name of our chosing, or create a symlink to it.
    """
    t0 = time.time()
    # Clear
    if os.path.isdir(dir2):
        shutil.rmtree(dir2)
    os.mkdir(dir2)
    # Get extension
    ext = '.exe' if sys.platform.startswith('win') else ''
    # Copy all files except dirs and exes
    for fname in os.listdir(dir1):
        if os.path.splitext(fname)[1].lower() in ('.exe', ''):
            continue
        filename1 = os.path.join(dir1, fname)
        filename2 = os.path.join(dir2, fname)
        if os.path.isfile(filename1):
            shutil.copy2(filename1, filename2)
    # Copy firefox exe -> xulrunner-stub
    shutil.copy2(os.path.join(dir1, 'firefox' + ext),
                    os.path.join(dir2, 'xulrunner-stub' + ext))
    print('Copied firefox (in %1.2f s)' % (time.time()-t0))


class XulRuntime(WebRuntime):
    """ Web runtime based on Mozilla's XUL framework.
    """
    
    _app_count = 0
    
    def _launch(self):
        XulRuntime._app_count += 1
        
        # Get executable for xul runtime (may be None)
        xul_exe = get_xul_runtime()
        
        # Temp folder to store app files
        app_path = create_temp_app_dir('xul', str(XulRuntime._app_count))
        id = os.path.basename(app_path).split('_', 1)[1]
        
        # Set size and position
        size = self._kwargs.get('size', (640, 480))
        pos = self._kwargs.get('pos', None)
        windowfeatures = 'width=%i, height=%i' % (size[0], size[1])
        if pos:
            windowfeatures += ', top=%i, left=%i' % (pos[0], pos[1])
        
        # More preparing
        self._kwargs['title'] = self._kwargs['title'] or 'XUL runtime'
        
        # Create files for app
        create_xul_app(app_path, id, windowfeatures=windowfeatures, 
                       **self._kwargs)
        
        # Get the command to execute
        exe = None
        if xul_exe:
            # Create link if we can, so that our window is not grouped with
            # ff, and has a more meaningful process name. Using
            # sys.executable also works well when frozen.
            exename, ext = os.path.splitext(os.path.basename(sys.executable))
            newexename = exename + '-ui' + ext
            exe = os.path.join(os.path.dirname(xul_exe), newexename)
            if not os.path.isfile(exe):
                try:
                    os.symlink(xul_exe, exe)
                except Exception:
                    # Windows has symlink in Python 3.2+, Windows Vista+
                    # But often the user has no privilege to symlink
                    shutil.copy2(xul_exe, exe)
        else:
            # See if we can use firefox command, Firefox may be
            # available even though we failed to find it.
            try:
                version = subprocess.check_output(['firefox', '--version'])
                exe = 'firefox'
            except Exception:
                pass
        
        # Final check
        if exe is None:
            raise RuntimeError('Could not find XUL runtime. '
                               'Please install firefox.')
        
        # Launch
        print('launching XUL app')
        cmd = [exe, '-app', os.path.join(app_path, 'application.ini')]
        self._start_subprocess(cmd)
