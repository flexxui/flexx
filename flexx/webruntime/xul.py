""" Web runtime based on XUL (i.e. Mozilla's Firefox browser engine)

This is the best developed runtime, with tested good behavior on
Windows, OSX, Linux and Raspberry Pi.

Developer notes
---------------

We keep track of runtimes in appdata/flexx/webruntimes, Xul runtimes
have a 'xul_' prefix. In principle we have just one, the one that is
most up to date. We can use firefox as a runtime, in case we symlink to
it (or on Windows copy the whole runtime). Later we may also download
the xulrunner runtime automatically.

After selecting the runtime, we create an executable to run it in a way
that avoids taskbar grouping (e.g. with firefox), and provides a more
meaningful process name in the task manager. Handling of this bit differs
per platform. On Linux we make a symlink, and on Windows a copy of the
xulrunner/firefox executable. On OSX we make a new xulrunner.app that
mimics the entire runtime via symlinks.

Xul wants a specific directory structure with a few files that define
the app. We write this on the fly to appdata/flexx/temp_apps. We create
a new app for each time we launch an application. We also take good
care to clean up the old ones. On Linux and OSX the runtime app
(symlink) is also stored in this directory.

"""

import os
import sys
import time
import shutil
import subprocess
import os.path as op

from . import logger
from .common import DesktopRuntime, create_temp_app_dir, appdata_dir

# todo: title should change with title of web page?
# todo: enable setting position/size at runtime?
# todo: enable fullscreen - does not seem to work on XUL


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
    sizemode="normal"
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
window.addEventListener("load", startup, false);
window.addEventListener("resize", resizefunc, false);

var thebrowser;

function startup() {
    //thebrowser = document.createElement("browser");
    //window.document.body.appendChild(thebrowser);

    document.getElementById("content").open = function() {
    window.alert('haha open ' + arguments[0]);
        //window.open(arguments[0], arguments[1], "chrome," + arguments[2]);
    };
    //document.getElementById("thebrowser").open = window.open;
    //window.open("http://python.org", "hello", "chrome,width=400,height=300");
}

var resizefunc = function(ev) {
    window.resizeTo(100, 100);
    window.alert("resize");
};


"""
# persist="screenX screenY width height sizemode"


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


INFO_PLIST = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" NONL
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
""".lstrip().replace('    ', '\t').replace('NONL\n', '')


## Functions


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
        osx_user_apps = op.expanduser('~/Applications')
        osx_root_apps = '/Applications'
        paths.append(op.join(osx_user_apps, 'Firefox.app/Contents/MacOS/firefox'))
        paths.append(op.join(osx_root_apps, 'Firefox.app/Contents/MacOS/firefox'))
        if not any([op.isfile(path) for path in paths]):
            # Try harder - use app-id to get the .app path
            try:
                osx_search_arg='kMDItemCFBundleIdentifier==org.mozilla.firefox'
                basepath = subprocess.check_output(['mdfind', osx_search_arg]).rstrip()
                if basepath:
                    paths.append(op.join(basepath, 'Contents/MacOS/firefox'))
            except (OSError, subprocess.CalledProcessError):
                pass

    # Try location until we find one that exists
    for path in paths:
        if op.isfile(path):
            return path
    else:
        return None


def has_firefox():
    """ Get whether firefox is installed.
    """
    if get_firefox_exe() is not None:
        return True

    try:
        subprocess.check_output(['firefox', '--version'])
        return True
    except Exception:
        return False


def copy_xul_runtime(dir1, dir2):
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
        logger.info('Copied firefox (in %1.2f s)' % (time.time()-t0))
    except Exception:
        # Clean up
        shutil.rmtree(dir2)
        raise


class XulRuntime(DesktopRuntime):
    """ Desktop runtime based on Mozilla's XUL framework. Xul is
    available wherever Firefox is installed, and uses same engine (Gecko).
    Requires Firefox or the Xul binaries to be installed.

    This runtime is currently the best supported way to create a desktop
    app, with full support for title, window position, icon and custom
    process name.
    """

    _app_count = 0

    def _launch(self):
        XulRuntime._app_count += 1

        self._check_compat()

        # Temp folder to store app files
        app_path = create_temp_app_dir('xul', str(XulRuntime._app_count))
        id = op.basename(app_path).split('_', 1)[1]

        # Set size and position
        size = self._kwargs.get('size', (640, 480))
        pos = self._kwargs.get('pos', None)
        windowfeatures = 'resizable,'
        windowfeatures += 'width=%i, height=%i' % (size[0], size[1])
        if pos:
            windowfeatures += ', top=%i, left=%i' % (pos[0], pos[1])

        # More preparing
        self._kwargs['title'] = self._kwargs.get('title', 'XUL runtime')

        # Create files for app
        self._create_xul_app(app_path, id, windowfeatures=windowfeatures,
                             **self._kwargs)

        # Get executable for xul runtime (may be None)
        xul_exe = self._get_xul_runtime()

        # Get the command to execute
        exe = None
        if xul_exe and op.isfile(op.realpath(xul_exe)):
            exe = self._get_app_exe(xul_exe, app_path)
        else:
            # See if we can use firefox command, Firefox may be
            # available even though we failed to find it.
            try:
                subprocess.check_output(['firefox', '--version'])
                exe = 'firefox'
            except Exception:
                pass

        # Final check
        if exe is None:
            raise RuntimeError('Could not find XUL runtime. '
                               'Please install firefox.')

        # Launch
        cmd = [exe, '-app', op.join(app_path, 'application.ini')]
        #cmd.append('-jsconsole')  # for debugging
        self._start_subprocess(cmd)

    def _check_compat(self):
        qts = 'PySide', 'PyQt4', 'PyQt5'
        if any([name+'.QtCore' in sys.modules for name in qts]):
            logger.warn("Using Flexx' Xul runtime and Qt (PySide/PyQt4/PyQt5) "
                        "together may cause problems.")

    def _create_xul_app(self, path, id, **kwargs):
        """ Create the files that determine the XUL app to launch.
        """

        # Dict with all values that are injected in the file templates
        # All values can be overriden via kwargs
        D = dict(vendor='Flexx',
                 name='flexx_ui_app',
                 version='1.0',
                 buildid='1',
                 id='some.app@flexx.io',
                 windowid='xx',
                 title='XUL app runtime',
                 url='http://example.com',
                 windowfeatures='', )
        D.update(kwargs)

        # Create values that need to be unique
        D['windowid'] = 'W' + id
        D['name'] = 'app_' + id
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
        # The launch function ensures that there always is an icon
        if kwargs.get('icon'):
            icon = kwargs.get('icon')
            icon_name = op.join(path, 'chrome/icons/default/' + D['windowid'])
            icon.write(icon_name + '.ico')
            icon.write(icon_name + '.png')

    def _get_xul_runtime(self):
        """ Get path to executable of a xul runtime. The returned path
        is in a writable directory. On Unix/OSX it may be a symlink,
        on Windows it is a real file. Returns None if no XUL runtime
        could be found.
        """

        # Define name of xul executable
        exe_name = 'xulrunner'
        exe_name += '.exe' if sys.platform.startswith('win') else ''

        # Get location and version of firefox
        ff_exe = get_firefox_exe()
        ff_version = ''
        if ff_exe:
            if 'Contents/MacOS/' in ff_exe:
                inifile = op.join(op.dirname(ff_exe),
                                  '../Resources/application.ini')
            else:
                inifile = op.join(op.dirname(ff_exe), 'application.ini')
            for line in open(inifile, 'rb').read().decode().splitlines():
                if line.lower().startswith('version'):
                    ff_version = 'xul_' + line.split('=')[1].strip()
                    break

        # Get dir with runtimes and list of subdirs (that represent versions)
        xuldir = op.join(appdata_dir('flexx'), 'webruntimes')
        if not op.isdir(xuldir):
            os.mkdir(xuldir)
        dnames = [d for d in sorted(os.listdir(xuldir)) if d.startswith('xul')]

        # Get obsolete versions, and remove them
        obsolete = [d for d in dnames if not
                    op.isfile(op.realpath(op.join(xuldir, d, exe_name)))]
        dnames = [d for d in dnames if d not in obsolete]

        # Clean up old runtimes (do before installing new ff, because
        # we may be "updating" it)
        for dname in (obsolete + dnames[:-1]):
            logger.info('Clearing XUL runtime at %s' % dname)
            try:
                shutil.rmtree(op.join(xuldir, dname))
            except (OSError, IOError):
                pass

        # Must we install ff?
        if ff_version:
            if (not dnames) or (dnames[-1] < ff_version):
                self._install_ff_locally(op.join(xuldir, ff_version), ff_exe)
                dnames.append(ff_version)

        # Return highest version or None
        if dnames:
            return op.join(xuldir, dnames[-1], exe_name)


    def _install_ff_locally(self, path, ff_exe):
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
            copy_xul_runtime(op.dirname(ff_exe), path)
        else:
            # OSX / Linux: create a symlink to xul runtime exe
            os.mkdir(path)
            stub_exe = op.join(path, 'xulrunner')
            os.symlink(ff_exe, stub_exe)
            return stub_exe


    def _get_app_exe(self, xul_exe, app_path):
        """ Get the executable to run our app. This should take care
        that the runtime process shows up in the task manager with the
        correct exe_name.

        * xul_exe: the location of the xul executable (can be a symlink)
        * app_path: the location of the xul app (the application.ini etc.)

        """

        if sys.platform.startswith('darwin'):
            # OSX: create an app, the name of the exe does not matter
            # much but the name to give the application does. We set
            # the latter to the title, because title and process name
            # seem the same thing in osx.
            exe = op.join(app_path, 'xulrunner.app')
            title = self._kwargs['title']
            self._osx_create_app(op.realpath(xul_exe), exe, title)
            exe += '/Contents/MacOS/xulrunner'
        else:
            # Define process name, so that our window is not grouped with
            # ff, and has a more meaningful name in the task manager. Using
            # sys.executable also works well when frozen.
            exe_name, ext = op.splitext(op.basename(sys.executable))
            exe_name = exe_name + '-ui' + ext
            if sys.platform.startswith('win'):
                # Windows: make a copy of the xulrunner executable
                exe = op.join(op.dirname(xul_exe), exe_name)
                if not op.isfile(exe):
                    shutil.copy2(xul_exe, exe)
            else:
                # Linux, create a symlink
                exe = op.join(app_path, exe_name)
                if not op.isfile(exe):
                    os.symlink(op.realpath(xul_exe), exe)

        return exe


    def _osx_create_app(self, xul_path, path, title):
        """ Create osx app

        * xul_path: path to executable of xulrunner (not the symlink)
        * path: location of the .app directory to create.
        * title: the title of the window *and* the process name
        """

        # Get app of firefox
        if 'Contents/MacOS' not in xul_path:
            raise NotImplementedError('Cannot deal with real xulrunner yet')
        xul_app = op.dirname(op.dirname(op.dirname(xul_path)))
        if not xul_app.endswith('.app'):
            raise TypeError('The xulrunner application must end in .app.')

        # Clear destination
        if op.isdir(path):
            shutil.rmtree(path)
        os.mkdir(path)

        # Make dir structure
        os.mkdir(op.join(path, 'Contents'))
        os.mkdir(op.join(path, 'Contents', 'MacOS'))
        os.mkdir(op.join(path, 'Contents', 'Resources'))

        # Make a link for all the files
        for dirpath, dirnames, filenames in os.walk(xul_app):
            relpath = op.relpath(dirpath, xul_app)
            if '.app' in relpath:
                continue
            if relpath.endswith('MacOS') or relpath.endswith('Resources'):
                for fname in filenames:
                    filename1 = op.join(xul_app, relpath, fname)
                    filename2 = op.join(path, relpath, fname)
                    os.symlink(filename1, filename2)
        # Make xulrunner exe
        os.symlink(op.join(xul_app, 'Contents', 'MacOS', 'firefox'),
                   op.join(path, 'Contents', 'MacOS', 'xulrunner'))
        # Make info.plist
        info = INFO_PLIST.format(name=title)
        with open(op.join(path, 'Contents', 'info.plist'), 'wb') as f:
            f.write(info.encode())
        # Make icon - ensured by launch function
        if self._kwargs.get('icon'):
            icon = self._kwargs.get('icon')
            icon.write(op.join(path, 'Contents', 'Resources', 'app.icns'))
