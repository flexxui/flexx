"""
Common code for all runtimes.

Note on app runtimes (i.e. for desktop apps): it is assumed that runtimes
are backward compatible. This is a reasonable assumption since we
use only the web stuff, which browsers generally keep working.

We also don't make a point of always having the latest version, because
some runtimes release almost every week. Having the user confirm a
download such often is way too much a burden, and auto-update too
complex / error-prone. These updates are mostly for security reasons,
which is generally less an issue for us because we only connect them
to known sources which are on localhost for desktop apps anyway.

Therefore, Flexx has a hardcoded minimal version for runtimes where this
makes sense, which is configurable by the user in cases where its needed.

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

from ._manage import RUNTIME_DIR, clean, lock_runtime_dir, versionstring


class BaseRuntime:
    """ Base class for all runtimes.
    """
    
    def __init__(self, **kwargs):
        if 'url' not in kwargs:
            raise KeyError('No url provided for runtime.')
        
        assert self.get_name()
        self._kwargs = kwargs
        self._proc = None
        self._streamreader = None
        atexit.register(self.close)
        
        clean()  # tidy up
        
        logger.info('launching %s' % self.__class__.__name__)
        self._launch()

    def get_name(self):
        """ Get the name of the runtime.
        """
        return self._get_name()
    
    def close(self):
        """ Close the runtime, or kill it if the process does not
        respond. Note that closing does not work when the runtime is a
        browser, because we need a process handle.
        """
        if self._proc is None:
            return
        # Terminate, wait for a bit, kill
        self._proc.we_closed_it = True
        if self._proc.poll() is None:
            if self._proc.stdin:  # pragma: no cover
                self._proc.stdin.close()
            self._proc.terminate()
            timeout = time.time() + 0.25
            while time.time() < timeout:
                time.sleep(0.02)
                if self._proc.poll() is not None:
                    break
            else:  # pragma: no cover
                self._proc.kill()
        # Discart process
        self._proc = None
    
    def _start_subprocess(self, cmd, shell=False, **env):
        """ Start subclasses, store handle, and launch a thread to read
        stdout for the process. Intended for web runtimes that are "bound"
        to this process.
        """
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
    
    ## To implement in subclasses
    
    def _get_name(self):
        """ Just make this return a string name.
        """
        raise NotImplementedError()
    
    def _launch(self):
        """ Function to implement launching the runtime.
        """
        raise NotImplementedError()


class DesktopRuntime(BaseRuntime):
    """ A base class for runtimes that launch a desktop-like app.

    Arguments:
        title (str): Text shown in title bar.
        size (tuple of ints): The size in pixels of the window.
        pos (tuple of ints): The position of the window.
        icon (str | Icon): Icon instance or path to an icon file (png or
            ico). The icon will be automatically converted to
            png/ico/icns, depending on what's needed by the runtime and
            platform.
    """

    def __init__(self, **kwargs):

        icon = kwargs.get('icon', None)
        kwargs['icon'] = iconize(icon)
    
        BaseRuntime.__init__(self, **kwargs)
    
    
    def get_runtime(self, min_version=None):
        """ Get the directory where (our local version of) the runtime is
        located. If necessary, the runtime is installed or updated.
        """
        cur_version = self.get_current_version() or ''
        path = os.path.join(RUNTIME_DIR, self.get_name() + '_' + cur_version)
        
        if not cur_version:
            # Need to install
            path = self._meh_install_runtime(True)
        elif not min_version:
            # No specific version required, e.g. because can assume that we
            # have an up-to-date version, like with Chrome.
            pass
        elif versionstring(cur_version) < versionstring(min_version):
            # Need update
            path = self._meh_install_runtime()
        else:
            # Our version is up to date
            pass
        
        # Prevent the runtime dir from deletion while this process is running
        lock_runtime_dir(path)
        
        return path
    
    def _meh_install_runtime(self, fresh=False):
        
        if fresh:
            print('Installing %s runtime' % self.get_name())
        else:
            print('Updating %s runtime' % self.get_name())
        # todo: this should be a confirmation dialog
        
        try:
            self._install_runtime()
        except Exception:
            # todo: show dialog
            raise
        
        return os.path.join(RUNTIME_DIR, self.get_name() + '_' + self.get_current_version())
        
    
    def get_current_version(self):
        """ Get the (highest) version of this runtime that we currently have.
        """
        versions = []
        for dname in os.listdir(RUNTIME_DIR):
            dirname = os.path.join(RUNTIME_DIR, dname)
            if os.path.isdir(dirname) and dname.startswith(self.get_name() + '_'):
                versions.append(dname.split('_')[-1])
        versions.sort(key=versionstring)
        if versions:
            return versions[-1]
    
    def _get_app_exe(self, runtime_exe, app_path):
        """ Get the executable to run our app. This should take care
        that the runtime process shows up in the task manager with the
        correct exe_name.

        * exe: the location of the runtime executable (can be a symlink)
        * app_path: the location of the temp app (the app.json or whatever)

        """

        if sys.platform.startswith('darwin'):
            # OSX: create an app, the name of the exe does not matter
            # much but the name to give the application does. We set
            # the latter to the title, because title and process name
            # seem the same thing in osx.
            app_exe = op.join(app_path, 'runtime.app')
            title = self._kwargs['title']
            self._osx_create_app(op.realpath(runtime_exe), app_exe, title)
            app_exe += '/Contents/MacOS/runtime'
        else:
            # Define process name, so that our window is not grouped with
            # ff, and has a more meaningful name in the task manager. Using
            # sys.executable also works well when frozen.
            exe_name, ext = op.splitext(op.basename(sys.executable))
            exe_name = exe_name + '-ui' + ext
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


    def _osx_create_app(self, exe, path, title):
        """ Create osx app

        * exe: path to executable of runtime (not the symlink)
        * path: location of the .app directory to create.
        * title: the title of the window *and* the process name
        """

        # Get app of firefox
        if 'Contents/MacOS' not in exe:
            raise NotImplementedError('Need  meeh!')  # todo: h
        xul_app = op.dirname(op.dirname(op.dirname(exe)))
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
                   op.join(path, 'Contents', 'MacOS', 'runtime'))
        # Make info.plist
        info = INFO_PLIST.format(name=title)
        with open(op.join(path, 'Contents', 'info.plist'), 'wb') as f:
            f.write(info.encode())
        # Make icon - ensured by launch function
        if self._kwargs.get('icon'):
            icon = self._kwargs.get('icon')
            icon.write(op.join(path, 'Contents', 'Resources', 'app.icns'))
    
    ## To implenent in subclasses
    
    def _install_runtime(self):
        """ Install a local copy of the latest runtime. Called when needed.
        """
        raise NotImplementedError()


# todo: ditch this? I've never found a use for it
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


_icon_template = """
xx x  xx x x x x
x  x  x  x x x x
xx x  xx  x   x
x  x  x  x x x x
x  xx xx x x x x

 xx   xxx   xxx
x  x  x  x  x  x
xxxx  xxx   xxx
x  x  x     x
"""


def default_icon():
    """ Generate a default icon object.
    """
    im = bytearray(4*16*16)
    for y, line in enumerate(_icon_template.splitlines()):
        y += 5
        if y < 16:
            for x, c in enumerate(line):
                if c == 'x':
                    i = (y * 16 + x) * 4
                    im[i:i+4] = [0, 0, 150, 255]

    icon = Icon()
    icon.add(im)
    return icon


def iconize(icon):
    """ Given a filename Icon object or None, return Icon object.
    """
    if icon is None:
        icon = default_icon()
    elif isinstance(icon, Icon):
        pass
    elif isinstance(icon, str):
        icon = Icon(icon)
    else:
        raise ValueError('Icon must be an Icon, a filename or None, not %r' %
                         type(icon))
    return icon


# Downloader(r'C:\Users\Almar\AppData\Local\flexx\webruntimes', 'nw', '0.19.5', 'https://dl.nwjs.io/v0.19.5/nwjs-v0.19.5-win-x64.zip', force=1).start()
