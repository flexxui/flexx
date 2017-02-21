"""
Common code for all runtimes.

Desktop runtimes provide a way to load a page as desktop application. To do
so, we may cache or link to an existing runtime (like Firefox) or even
keep a local copy of a runtime (like NW.js). Some runtimes (e.g. Firefox)
needs a whole directory structure as its app definition. Others need just
one manifest file (NW.js) and perhaps some icons. Others need nothing (Chrome).
In all cases we improve the app experience by making use of a custom named
executable to control task bar grouping, and on OS X we build an actual
application (xx.app directory).

It is assumed that desktop runtimes are backward compatible. This is a
reasonable assumption since we use only the web stuff, which browsers
generally keep working.

We also don't make a point of always having the latest version, because
some runtimes release almost every week. Having the user confirm a
download such often is way too much a burden, and auto-update too
complex / error-prone. These updates are mostly for security reasons,
which is generally less an issue for us because we only connect them
to known sources which are on localhost for desktop apps anyway.

Therefore, Flexx has a hardcoded minimal version for runtimes where this
makes sense, which is configurable by the user in cases where its needed.

For deskop runtimes we have the following important attributes:

* icon: the application icon for the app. This will usually come from the
  main widget's icon property (as a string), and is converted to an Icon
  object here, so that each runtime can export the required .ico, .icns or .png
  files.
* title: the title to display on the apps title bar. This will usually come from
  the main widget's title property.
* exe_name: the name of the executable of the runtime, chosing this helps
  find the process in the task manager, but more importantly, avoids task
  grouping, or helps wanted grouping.
* id: a unique application id, generated and used internally to creat unique
  temporary app dirs and application manifests.

"""

import os.path as op
import os
import sys
import time
import atexit
import shutil
import threading
import subprocess

from . import logger
from ..util.icon import Icon

from ._manage import RUNTIME_DIR
from ._manage import init_dirs, clean_dirs, lock_runtime_dir, versionstring


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
    <string>{exe}</string>
    <key>CFBundleName</key>
    <string>{name}</string>
</dict>
</plist>
""".lstrip().replace('    ', '\t').replace('NONL\n', '')


class BaseRuntime:
    """ Base class for all runtimes.
    """
    
    def __init__(self, **kwargs):
        
        # nomnom, we eat all kwargs, because different runtimes use
        # different kwargs, and we want it to be easy to switch runtimes
        self._leftover_kwargs = kwargs
        
        assert self.get_name()
        atexit.register(self.close)
        
        self._exe = None
        self._version = None
        self._proc = None
        self._streamreader = None
        
        # Tidy up, but don't make us wait for it, also give main thread
        # time to e.g. continue incomplete downloads (e.g. for NW.js runtime)
        init_dirs()
        t = threading.Thread(target=lambda: time.sleep(4) or clean_dirs())
        t.setDaemon(True)
        t.start()  # tidy up
    
    def get_install_instuctions(self):
        """ Get instructions on how a runtime can be installed. Used internally
        to show useful dialogs.
        """
        return self._get_install_instuctions().strip()
    
    def get_name(self):
        """ Get the name of the runtime.
        """
        return self._get_name()
    
    def get_exe(self):
        """ Get the executable corresponding to the runtime. This is usually
        the path to an executable file, but it can also be a command, or even
        a stub. Can be None if the runtime is not (yet) installed.
        """
        if not self._exe:
            self._exe = self._get_exe()
        return self._exe
    
    def get_version(self):
        """ Get the version of the available runtime (as a string). Can be None
        if the version cannot be retrieved (e.g. for Edge and IE), or if the
        runtime is not available on this system.
        """
        if not self._version:
            self._version = self._get_version()
        return self._version
    
    def is_available(self):
        """ Get whether this runtime appears to be available on this machine.
        """
        return self._is_available()
    
    def launch_tab(self, url):
        """ Launch the given url in a new browser tab. Only works for runtimes
        that are browsers (e.g. not NW).
        """
        if not self.is_available():
            t = 'Cannot launch tab, because %s runtime is not available'
            raise RuntimeError(t % self.get_name())
        self._launch_tab(url)
        logger.info('launched in %s tab: %s' % (self.get_name(), url))
    
    def launch_app(self, url):
        """ Launch the given url as a desktop application. Only works for
        runtimes that derive from DeskopRuntime (e.g. not Edge). Apps launched
        this way can usually be terminated using the ``close()`` method.
        """
        if not self.is_available():
            t = 'Cannot launch app, because %s runtime is not available'
            raise RuntimeError(t % self.get_name())
        self._launch_app(url)
        logger.info('launched as %s app: %s' % (self.get_name(), url))
    
    def close(self):
        """ Close the runtime, or kill it if the process does not
        respond. Note that closing only works for runtimes launched as
        an app (using ``launch_app()``).
        """
        if self._proc is None:
            return
        # Terminate, wait for a bit, kill
        self._proc.we_closed_it = True
        if self._proc.poll() is None:
            if self._proc.stdin:  # pragma: no cover
                self._proc.stdin.close()
            self._proc.terminate()
            timeout = time.time() + 0.2
            while time.time() < timeout:
                time.sleep(0.02)
                if self._proc.poll() is not None:
                    break
            else:  # pragma: no cover
                self._proc.kill()
        # Discart process
        self._proc = None
    
    ## Utilities that this class provides for subclasses
    
    def _start_subprocess(self, cmd, shell=False, **env):
        """ Start subclasses, store handle, and launch a thread to read
        stdout for the process. Intended for web runtimes that are "bound"
        to this process.
        """
        if self._proc:
            t = 'Cannot launch %s app twice with same runtime instance.'
            raise RuntimeError(t % self.get_name())
        self._proc = self._spawn_subprocess(cmd, shell, **env)
        self._streamreader = StreamReader(self._proc)
        self._streamreader.start()
    
    def _spawn_subprocess(self, cmd, shell=False, **env):
        """ Spawn a subprocess and return process handle. Intended for
        web runtimes that are "spawned", like browsers.
        """
        environ = os.environ.copy()
        environ.update(env)
        try:
            return subprocess.Popen(cmd, env=environ, shell=shell,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
        except OSError as err:  # pragma: no cover
            raise RuntimeError('Could not start runtime with command %r:\n%s' %
                               (cmd[0], str(err)))
    
    ## Methods to implement in subclasses
    
    def _get_install_instuctions(self):
        """ Subclasses can let know how the user must install the runtime.
        Can return None to indicate that it cannot be installed (like the
        "default browser").
        """
        return "No info on how to install %s" % self.get_name()
    
    def _get_name(self):
        """ Just make this return a string name.
        """
        raise NotImplementedError()
    
    def _get_exe(self):
        """ String executable name, preferably an absolute path. Should return
        something if the runtime appears to be available.
        """
        raise NotImplementedError()
    
    def _is_available(self):
        """ Alias of get_exe(), unless overloaded.
        """
        return self.get_exe()
    
    def _get_version(self):
        """ String version of the available runtime, can return None
        if the version cannot be retrieved.
        """
        raise NotImplementedError()
    
    def _launch_tab(self, url):
        """ Function to implement launching the url in a new tab.
        """
        raise NotImplementedError()
    
    def _launch_app(self, url):
        """ Function to implement launching the url as a desktop app.
        """
        raise NotImplementedError()


class DesktopRuntime(BaseRuntime):
    """ A base class for runtimes that launch a desktop-like app.

    Arguments:
        title (str): Text shown in the title bar.
        icon (str | Icon): Icon instance or path to an icon file (png or ico).
            The icon will automatically be converted to png/ico/icns,
            depending on what's needed by the runtime and platform.
        size (tuple of ints): The size (in pixels) of the window.
        pos (tuple of ints): The position (in pixels) of the window.
        windowmode (str): the initial window mode, e.g. 'normal', 'maximized',
            'fullscreen', 'kiosk'. Note that not all modes are supported by all
            runtimes.
    """

    def __init__(self, icon=None, title=None,
                 size=None, pos=None, windowmode=None, **kwargs):
        
        self._icon = iconize(icon or None)
        assert isinstance(self._icon, Icon)
        
        self._title = title or 'Flexx %s runtime' % self.get_name()
        assert isinstance(self._title, str)
        
        self._size = size or (640, 480)
        assert isinstance(self._size, tuple) and len(self._size) == 2
        
        self._pos = pos
        assert self._pos is None or (isinstance(self._pos, tuple) and
                                     len(self._pos) == 2)
        
        self._windowmode = windowmode or 'normal'
        assert isinstance(self._windowmode, str)
        assert self._windowmode in ('normal', 'maximized', 'fullscreen', 'kiosk')
        
        self._system_version = None
        
        super().__init__(**kwargs)
    
    def _is_available(self):
        cached, _ = self.get_cached_version()
        system, _ = self.get_system_version()
        return bool(cached or system)
    
    def get_runtime_dir(self):
        """ Get the directory of the (up-to-date) local version of the runtime.
        If necessary, the runtime is cached/installed.
        """
        
        # Get info on cached version
        cur_version, path = self.get_cached_version()
        sys_version, sys_path = self.get_system_version()
        
        # Do we need an install?
        install_action = None
        if not (cur_version or sys_version):
            raise RuntimeError('Dont have cached version of runtime %s nor can '
                               'install it.' % self.get_name())
        elif not cur_version:
            install_action = 'install'
        elif not sys_version:
            # No specific version required, e.g. because can assume that we
            # have an up-to-date version.
            pass
        elif versionstring(cur_version) < versionstring(sys_version):
            install_action = 'update'
        
        # Install if necessary and update version
        if install_action:
            logger.info('Performing %s of runtime %s' %
                        (install_action, self.get_name()))
            path = op.join(RUNTIME_DIR, self.get_name() + '_' +sys_version)
            self._install_runtime(sys_path, path)
        
        assert os.path.isdir(path)
        lock_runtime_dir(path)
        return path
    
    def get_system_version(self):
        """ Get (version, path) for the version of the runtime available
        on the system. Can be an application, but also an archive or installer.
        This information is used internally to install or update a runtime.
        """
        if not self._system_version:
            self._system_version = self._get_system_version()
            assert len(self._system_version) == 2
        return self._system_version
    
    def get_cached_version(self):
        """ Get (version, path) for the (highest) version of this runtime that
        we currently have locally installed.
        """
        versions = []
        for dname in os.listdir(RUNTIME_DIR):
            dirname = op.join(RUNTIME_DIR, dname)
            if op.isdir(dirname) and dname.startswith(self.get_name() + '_'):
                versions.append((dname.split('_')[-1], dirname))
        versions.sort(key=lambda x: versionstring(x[0]))
        if versions:
            return versions[-1]
        return None, None
    
    def get_frozen_version(self):
        """ Get (version, path) for the (highest) version of this runtime that
        is shipped along with the executable.
        """
        # todo: put this to use
        basedir = os.path.dirname(sys.executable)
        versions = []
        for dname in os.listdir(basedir):
            dirname = op.join(basedir, dname)
            if op.isdir(dirname) and dname.startswith(self.get_name() + '_'):
                versions.append((dname.split('_')[-1], dirname))
        versions.sort(key=lambda x: versionstring(x[0]))
        if versions:
            return versions[-1]
        return None, None
    
    def _get_app_exe(self, runtime_exe, app_path):
        """ Get the executable to run our app. This should take care
        that the runtime process shows up in the task manager with the
        correct exe_name.

        * runtime_exe: the location of the runtime executable (can be a symlink)
        * app_path: the location of the temp app (the app.json or whatever)

        """
        # Define process name, so that our window is not grouped with
        # Firefox, NW.js or whatever, and has a more meaningful name in the
        # task manager. Using sys.executable also works well when frozen.
        exe_name, ext = op.splitext(op.basename(sys.executable))
        # todo: What kind of exe name? test with freezing on different OS's
        exe_name = exe_name + '-ui' + ext
        # exe_name = exe_name + ext
        
        assert runtime_exe.startswith(RUNTIME_DIR)
        
        if sys.platform.startswith('darwin'):
            # OSX: create an app, the name of the exe does not matter
            # much but the name to give the application does. We set
            # the latter to the title, because title and process name
            # seem the same thing in osx.
            app_exe = op.join(app_path, exe_name + '.app')
            # todo: double check to make sure if title makes the most sense here
            self._osx_create_app(op.realpath(runtime_exe), app_exe, self._title)
            app_exe += '/Contents/MacOS/' + exe_name
        else:
            
            if sys.platform.startswith('win'):
                # Windows: make a copy of the executable
                app_exe = op.join(op.dirname(runtime_exe), exe_name)
                if not op.isfile(app_exe):
                    shutil.copy2(runtime_exe, app_exe)
            else:
                # Linux, create a symlink
                app_exe = op.join(app_path, exe_name)
                if not op.isfile(app_exe):
                    os.symlink(op.realpath(runtime_exe), app_exe)
        
        return app_exe

    def _osx_create_app(self, exe, dst_dir, title):
        """ Create osx app

        * exe: path to executable of runtime (not the symlink)
        * dst_dir: path of the .app directory to create.
        * title: the title of the window *and* the process name
        """

        # Get original app to copy it from
        exe_name_src = op.basename(exe)
        exe_name_dst = op.basename(dst_dir).split('.')[0]
        if 'Contents/MacOS' not in exe:
            raise NotImplementedError('Can only create OS X app from existing app')
        src_dir = op.dirname(op.dirname(op.dirname(exe)))
        if not src_dir.endswith('.app'):
            raise TypeError('The original OS X application must end in .app.')

        # Clear destination
        if op.isdir(dst_dir):
            shutil.rmtree(dst_dir)
        os.mkdir(dst_dir)

        # Make dir structure
        os.mkdir(op.join(dst_dir, 'Contents'))
        os.mkdir(op.join(dst_dir, 'Contents', 'MacOS'))

        # Make a link for all the files
        for dirpath, dirnames, filenames in os.walk(src_dir):
            relpath = op.relpath(dirpath, src_dir)
            if relpath.startswith(('Contents/MacOS', 'Contents/Resources',
                                   'Contents/Versions')):
                if not op.isdir(op.join(dst_dir, relpath)):
                    os.mkdir(op.join(dst_dir, relpath))
                for fname in filenames:
                    os.link(op.join(src_dir, relpath, fname),
                            op.join(dst_dir, relpath, fname))
        # Make runtime exe
        os.link(  # or shutil.copy2(
            op.realpath(op.join(src_dir, 'Contents', 'MacOS', exe_name_src)),
            op.join(dst_dir, 'Contents', 'MacOS', exe_name_dst))
        # Make info.plist
        info = INFO_PLIST.format(name=title, exe=exe_name_dst)
        with open(op.join(dst_dir, 'Contents', 'info.plist'), 'wb') as f:
            f.write(info.encode())
        # Make icon - DesktopRuntime ensures that there is an icon and title
        iconfile = op.join(dst_dir, 'Contents', 'Resources', 'app.icns')
        if op.exists(iconfile):
            os.unlink(iconfile)  # remove first, since its a hard link!
        self._icon.write(iconfile)
    
    ## To implenent in subclasses
    
    def _get_system_version(self):
        """ Provide (tuple, path) info on a system-available version.
        """
        raise NotImplementedError()
    
    def _install_runtime(self, sys_path, dest_path):
        """ Install a local copy of the latest runtime. Called when needed.
        """
        raise NotImplementedError()


# This does not seem to do much, most of the time, but when things break it
# usually does give some usefull output!
class StreamReader(threading.Thread):
    """ Reads stdout of process and log

    This needs to be done in a separate thread because reading from a
    PYPE blocks.
    """
    def __init__(self, process):
        threading.Thread.__init__(self)

        self._process = process
        self._exit = False
        self.setDaemon(True)
        atexit.register(self.stop)

    def stop(self, wait=None):  # pragma: no cover
        self._exit = True
        if wait is not None:
            self.join(wait)

    def run(self):  # pragma: no cover
        msgs = []
        while not self._exit:
            time.sleep(0.001)
            # Get and clean msg
            msg = self._process.stdout.readline()  # <-- Blocks here
            if not msg:
                break  # Process dead
            if not isinstance(msg, str):
                msg = msg.decode('utf-8', 'ignore')
            msg = msg.rstrip()
            # Process the message
            msgs.append(msg)
            msgs[:-32] = []
            logger.debug('from runtime: ' + msg)

        if self._exit:
            return  # might be interpreter shutdown, don't print

        # Poll to get return code. Polling also helps to really
        # clean the process up
        while self._process.poll() is None:
            time.sleep(0.05)

        # Notify
        code = self._process.poll()
        if getattr(self._process, 'we_closed_it', False):
            logger.info('runtime process terminated by us')
        elif not code:
            logger.info('runtime process stopped')
        else:
            logger.error('runtime process stopped (%i), stdout:\n%s' %
                          (code, '\n'.join(msgs)))


def find_osx_exe(app_id):
    """ Find the xxx.app of an application via its app id,
    se.g. 'com.google.Chrome'.
    """
    try:
        osx_search_arg = 'kMDItemCFBundleIdentifier==%s' % app_id
        return subprocess.check_output(['mdfind', osx_search_arg]).rstrip().decode()
    except (OSError, subprocess.CalledProcessError):
        pass


## Icon stuff


THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def iconize(icon):
    """ Given a filename Icon object or None, return Icon object.
    """
    
    # Get default icon?
    if icon is None:
        icon = os.path.join(os.path.dirname(THIS_DIR), 'resources', 'flexx.ico')
    
    if isinstance(icon, Icon):
        pass
    elif isinstance(icon, str):
        if icon.startswith('_data/shared'):
            # Icon as an asset in Flexx' asset store
            from ..app import assets  # noqa
            bb = assets.get_data(icon.split('/', 2)[-1])
            icon = Icon()
            icon.from_bytes('.ico', bb)
        else:
            # Filename, url, base64 string - handled by Icon class
            icon = Icon(icon)
    else:
        raise ValueError('Icon must be an Icon, str, or None, not %r' %
                         type(icon))
    return icon
