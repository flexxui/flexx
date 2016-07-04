"""
Common code for all runtimes.
"""

import os
import sys
import time
import atexit
import shutil
import threading
import subprocess

from . import logger
from ..util.icon import Icon


class BaseRuntime:
    """ Base class for all runtimes.
    """

    def __init__(self, **kwargs):
        if 'url' not in kwargs:
            raise KeyError('No url provided for runtime.')

        self._kwargs = kwargs
        self._proc = None
        self._streamreader = None
        atexit.register(self.close)

        logger.info('launching %s' % self.__class__.__name__)
        self._launch()

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
        """ For subclasses to easily launch the subprocess.
        """
        environ = os.environ.copy()
        environ.update(env)
        try:
            self._proc = subprocess.Popen(cmd, env=environ, shell=shell,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
        except OSError as err:  # pragma: no cover
            raise RuntimeError('Could not start runtime with command %r:\n%s' %
                               (cmd[0], str(err)))
        self._streamreader = StreamReader(self._proc)
        self._streamreader.start()

    def _launch(self):
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
            if msg == '> undefined' or not msg:
                continue  # nodejs stubs
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


def create_temp_app_dir(prefix, suffix='', cleanup=60):
    """ Create a temporary direrctory and return path

    The directory will be named "<prefix>_<timestamp>_<pid>_<suffix>".
    Will clean up directories with the same prefix which are older than
    cleanup seconds.
    """

    # Select main dir
    maindir = os.path.join(appdata_dir('flexx'), 'temp_apps')
    if not os.path.isdir(maindir):  # pragma: no cover
        os.mkdir(maindir)

    prefix = prefix.strip(' _-') + '_'
    suffix = '' if not suffix else '_' + suffix.strip(' _-')

    # Clear any old files
    for dname in os.listdir(maindir):
        if dname.startswith(prefix):
            dirname = os.path.join(maindir, dname)
            if os.path.isdir(dirname):
                try:
                    dirtime = int(dname.split('_')[1])
                except Exception:  # pragma: no cover
                    pass
                if (time.time() - dirtime) > cleanup:  # pragma: no cover
                    try:
                        shutil.rmtree(dirname)
                    except (OSError, IOError):
                        pass

    # Return new dir
    id = '%i_%i' % (time.time(), os.getpid())
    path = os.path.join(maindir, prefix + id + suffix)
    os.mkdir(path)
    return path


# From pyzolib/paths.py (https://bitbucket.org/pyzo/pyzolib/src/tip/paths.py)
def appdata_dir(appname=None, roaming=False, macAsLinux=False):
    """ appdata_dir(appname=None, roaming=False,  macAsLinux=False)
    Get the path to the application directory, where applications are allowed
    to write user specific files (e.g. configurations). For non-user specific
    data, consider using common_appdata_dir().
    If appname is given, a subdir is appended (and created if necessary).
    If roaming is True, will prefer a roaming directory (Windows Vista/7).
    If macAsLinux is True, will return the Linux-like location on Mac.
    """

    # Define default user directory
    userDir = os.path.expanduser('~')

    # Get system app data dir
    path = None
    if sys.platform.startswith('win'):
        path1, path2 = os.getenv('LOCALAPPDATA'), os.getenv('APPDATA')
        path = (path2 or path1) if roaming else (path1 or path2)
    elif sys.platform.startswith('darwin') and not macAsLinux:
        path = os.path.join(userDir, 'Library', 'Application Support')
    # On Linux and as fallback
    if not (path and os.path.isdir(path)):
        path = userDir

    # Maybe we should store things local to the executable (in case of a
    # portable distro or a frozen application that wants to be portable)
    prefix = sys.prefix
    if getattr(sys, 'frozen', None):  # See application_dir() function
        prefix = os.path.abspath(os.path.dirname(sys.path[0]))
    for reldir in ('settings', '../settings'):
        localpath = os.path.abspath(os.path.join(prefix, reldir))
        if os.path.isdir(localpath):  # pragma: no cover
            try:
                open(os.path.join(localpath, 'test.write'), 'wb').close()
                os.remove(os.path.join(localpath, 'test.write'))
            except IOError:
                pass  # We cannot write in this directory
            else:
                path = localpath
                break

    # Get path specific for this app
    if appname:
        if path == userDir:
            appname = '.' + appname.lstrip('.')  # Make it a hidden directory
        path = os.path.join(path, appname)
        if not os.path.isdir(path):  # pragma: no cover
            os.mkdir(path)

    # Done
    return path


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
