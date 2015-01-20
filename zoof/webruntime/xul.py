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
        paths.append('/usr/lib/iceweasel/iceweasel')
        paths.append('/usr/lib64/iceweasel/iceweasel')
    elif sys.platform.startswith('darwin'):
        paths.append('/Applications/Firefox.app/Contents/MacOS/firefox')
    
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
        if 'Contents/MacOS/' in ff_exe:
            inifile = os.path.join(os.path.dirname(ff_exe), '../Resources/application.ini')
        else:
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
    # On Windows we must copy if we want to change the process name and
    # avoid taskbar grouping with firefox. We do it everwhere for
    # consistency since its only needed once and it is fast. On rasp-pi
    # it takes 8 s though.
    if ff_version:
        if (not dnames) or (dnames[-1] < ff_version):
            if sys.platform.startswith('darwin'):
                os.mkdir(os.path.join(xuldir, ff_version))
                stub_exe = os.path.join(xuldir, ff_version, 'xulrunner')
                os.symlink(ff_exe, stub_exe)
                return stub_exe
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
        the_exe = os.path.join(xuldir, dnames[-1], 'xulrunner')
        the_exe += '.exe' if sys.platform.startswith('win') else ''
        return the_exe
    else:
        return None


def copy_firefox_runtime(dir1, dir2):
    """ Copy the firefox runtime to a new folder, in which we rename
    the firefox exe to xulrunner. This thus creates a xul runtime
    in a location where we have write access, so that we can duplicate
    the exe with a name of our chosing, or create a symlink to it.
    """
    t0 = time.time()
    # Get extension
    ext = '.exe' if sys.platform.startswith('win') else ''
    # On Rasberry Pi, the xul runtime is in a (linked) subdir 
    if os.path.isdir(os.path.join(dir1, 'xulrunner')):
        dir1 = os.path.join(dir1, 'xulrunner')
    # Clear
    if os.path.isdir(dir2):
        shutil.rmtree(dir2)
    os.mkdir(dir2)
    try:
        # Copy all files except dirs 
        for fname in os.listdir(dir1):
            filename1 = os.path.join(dir1, fname)
            filename2 = os.path.join(dir2, fname)
            if os.path.isfile(filename1):
                shutil.copy2(filename1, filename2)
        # Copy firefox exe -> xulrunner
        for exe_name in ('firefox', 'iceweasel', 'xulrunner', 'firefox'):
            exe = os.path.join(dir1, exe_name + ext)
            if os.path.isfile(exe):
                break
        shutil.copy2(exe, os.path.join(dir2, 'xulrunner' + ext))
        print('Copied firefox (in %1.2f s)' % (time.time()-t0))
    except Exception:
        # Clean up
        shutil.rmtree(dir2)
        raise

##

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleExecutable</key>
    <string>xulrunner</string>
    <key>CFBundleName</key>
    <string>{name}</string>
</dict>
</plist>
""".replace('    ', '\t')

def osx_create_app(xul_path, path):
    """ xul_path is the executable for xulrunner
    path is the .app to write
    """
    # Get app of firefox
    if not 'Contents/MacOS' in os.path.realpath(xul_path):
        raise NotImplementedError('Cannot deal with real xulrunner yet')
    xul_app = os.path.dirname(os.path.dirname(os.path.dirname(xul_path)))
    assert xul_app.endswith('.app')
    
    # Clear destination
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)
    
    # Make dir structure
    os.mkdir(os.path.join(path, 'Contents'))
    os.mkdir(os.path.join(path, 'Contents', 'MacOS'))
    os.mkdir(os.path.join(path, 'Contents', 'Resources'))
    
    # Make a link for all the files
    for dirpath, dirnames, filenames in os.walk(xul_app):
        relpath = os.path.relpath(dirpath, xul_app)
        if '.app' in relpath:
            continue
        if relpath.endswith('MacOS') or relpath.endswith('Resources'):
            for fname in filenames:
                filename1 = os.path.join(xul_app, relpath, fname)
                filename2 = os.path.join(path, relpath, fname)
                os.symlink(filename1, filename2)
    # Make xulrunner exe
    os.symlink(os.path.join(xul_app, 'Contents', 'MacOS', 'firefox'),
               os.path.join(path, 'Contents', 'MacOS', 'xulrunner'))
    # Make info.plist
    info = INFO_PLIST.format(name=os.path.basename(path)[:-4])  # todo: or title?
    with open(os.path.join(path, 'Contents', 'info.plist'), 'wb') as f:
        f.write(info.encode('utf-8'))
    # Make icon
    icon = default_icon()  # todo: use given icon
    icon.write(os.path.join(path, 'Contents', 'Resources', 'app.icns'))
    
    
#print(osx_create_app(get_firefox_exe()))
##
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
        if xul_exe:  # todo: and realpath is a file
            # Create link if we can, so that our window is not grouped with
            # ff, and has a more meaningful process name. Using
            # sys.executable also works well when frozen.
            exename, ext = os.path.splitext(os.path.basename(sys.executable))
            newexename = exename + '-ui' + ext
            exe = os.path.join(os.path.dirname(xul_exe), newexename)
            if sys.platform.startswith('darwin'):
                osx_create_app(os.path.realpath(xul_exe), exe + '.app')
                exe += '.app/Contents/MacOS/xulrunner'
            else:
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
