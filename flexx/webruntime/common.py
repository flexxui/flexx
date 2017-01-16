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
from urllib.request import urlopen, Request

# from . import logger
# from ..util.icon import Icon


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

        logger.info('launching %s' % self.__class__.__name__)
        self._launch()

    def _get_name(self):
        raise NotImplementedError()
    
    def get_name(self):
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
        
        self._runtimedir = op.join(appdata_dir('flexx'), 'webruntimes')
    
    
    def _launch(self, version=None):
        
        self.clean()
        
        versions = self.get_versions()
        # todo: xul does not allow a specific verion
        if version:
            # We need a specific version
            if version in versions:
                pass
            else:
                self._download(version)
        elif versions:
            # Just use the latest that we have, but maybe ask for an update
            version = versions[-1]
            # get age of version
            # if older than X weeks, ask to download newer once
        else:
            # We don't have any runtime yet, we *need* a download
            pass
            
        # Get url to download
        if version is None:
            version = self.get_latest_version()
        url = self.get_url(version)
        
        # Mark used version as used
        # Mark downloaded version as downloaded (so we can establish age later)
        # cleanup
        # launch!
    
    def _download(self, version, now=True):
        url = self.get_url(version)
        d = Downloader(self._runtimedir, self.get_name(), version, url, now)
        if now:
            d.run()  # in main thread
        else:
            d.start()  # download in the background
            self._downloader = d  # keep a ref
    
    def get_versions(self):
        """ Get the versions of the runtime that we currently have.
        """
        versions = []
        for dname in os.listdir(self._runtimedir):
            dirname = os.path.join(self._runtimedir, dname)
            if os.path.isdir(dirname) and dname.startswith(self.get_name() + '_'):
                versions.append(dname.split('_')[-1])
        versions.sort()
        return versions
    
    def get_latest_version(self):
        raise NotImplementedError()
    
    def get_url(self, version):
        raise NotImplementedError()
    
    def clean(self):
        """ Clean up the webruntime dir.
        """
        # todo: where do I make sure that this exists?
        dir = op.join(appdata_dir('flexx'), 'webruntimes')
        pids = get_pid_list()
        
        for name in os.listdir(dir):
            filename = os.path.join(dir, name)
            if '#' in name:
                if name.startswith(_delete_prefix):
                    remove(filename)
                else:
                    try:
                        pid = int(name.split('#')[-1])
                    except ValueError:
                        continue
                    if pid not in pids:
                        remove(filename)
        
    def cleanup(self):
        
        for dname in os.listdir(self._runtimedir):
            dirname = os.path.join(self._runtimedir, dname)
            if os.path.isdir(dirname) and dname.startswith(self.get_name() + '_'):
                version = dname.split('_')[-1]
                testfile = os.path.join(dirname, 'last_access.txt')
                if os.path.isfile(testfile):
                    s = open(testfile, 'rb').read().decode().strip()
                    # dt = datetime ......
                else:
                    self._use_version(version)
    
    def _use_version(self, version):
        pass
        
            
##
class Downloader(threading.Thread):
    """
    Helper class for downloading a runtime.
    
    * Download archive as xxx.zip#pid
    * On download complete, rename to xxx.zip
    * Extract to yyy#pid
    * When extract is done, rename to yyy
    
    For downloading, we compare the pid to current list of pids to see
    if perhaps another process is already downloading it (though its no
    guarantee, as pids are reused). If there is an archive in progess,
    which has "stalled", we rename the archive and continue downloading.
    
    Files to delete are first renamed todelete#... and an attempt is made
    to delete them. If that fails, we can delete them at a later time.
    """
    
    def __init__(self, dir, prefix, version, url, force=False):
        super().__init__()
        self._dir = dir
        self._prefix = prefix
        self._version = version
        self._url = url
        self._force = force
        self.isDaemon = True
        
        # Calculate file system locations
        fname = url.split('?')[0].split('#')[0].split('/')[-1].lower()
        self._archive_name = os.path.join(self._dir, fname)
        self._dir_name = os.path.join(self._dir, prefix + '_' + version)
        
        # Get func to open archive
        import tarfile
        import zipfile
        if fname.endswith(('.tar', '.tar.gz', '.tar.bz2')):
            self._arch_func = tarfile.open
        elif fname.endswith('.zip'):
            self._arch_func = zipfile.ZipFile
        else:
            raise ValueError('Dont know how to extract from %s' % fname)
    
    def run(self):
        """ Main function of thread, or call this directly from main thread.
        """
        # Get names
        archive_name = self._archive_name
        dir_name = self._dir_name
        
        # Our own special names
        temp_archive_name = archive_name + '#' + str(os.getpid())
        temp_dir_name = dir_name + '#' + str(os.getpid())
        
        # Go!
        if os.path.isdir(dir_name):
            return
        if self.download(temp_archive_name, archive_name):
            self.extract(archive_name, temp_dir_name, dir_name)
        
        # Remove archive
        remove(archive_name)
        
        # todo: delete version if it seems corrupt?
    
    def download(self, temp_archive_name, archive_name):
        """ Download the archive.
        """
        # Clean, just to be sure
        remove(temp_archive_name)
        
        # Maybe the archive is already there ...
        if os.path.isfile(archive_name):
            return True
        
        # Get whether the downloading is already in progress by another process
        pids = get_pid_list()
        archives = []  # that do not correspond to an existing pid
        for name in os.listdir(self._dir):
            filename = os.path.join(self._dir, name)
            if filename.startswith(archive_name):
                try:
                    pid = int(name.split('#')[-1])
                except ValueError:
                    continue  # what is this? not ours, probably
                if pid and pid in pids:
                    # another process might be working on it
                    if not self._force:
                        return
                else:
                    archives.append(filename)
        
        # Touch file to clear it and tell other processes that we're loading it,
        # or proceed with existing (partial) file.
        print(archives)
        if not archives:
            with open(temp_archive_name, 'wb'):
                pass
        else:
            try:
                shutil.move(archives[0], temp_archive_name)
            except FileNotFoundError:
                return  # another process was just a wee bit earlier?
        
        # Open local file ...
        t0 = time.time()
        with open(temp_archive_name, 'ab') as f_dst:
            nbytes = f_dst.tell()
            
            # Open remote resource
            try:
                r = Request(self._url)
                r.headers['Range'] = 'bytes=%i-' % f_dst.tell()
                f_src = urlopen(r, timeout=5)
            except Exception:
                if self._force:
                    raise
                return
            file_size = nbytes + int(f_src.headers['Content-Length'].strip())
            chunksize = 64 * 1024
            # Download in chunks
            while True:
                chunk = f_src.read(chunksize)
                if not chunk:
                    break
                nbytes += len(chunk)
                f_dst.write(chunk)
                f_dst.flush()
                print('downloading: %03.1f%%\r' % (100 * nbytes / file_size), end='')
        print('Downloaded %s in %1.f s' % (self._url, time.time() - t0))
        
        # Mark archive as done
        if os.path.isfile(archive_name):
            pass  # another process beat us to it
        else:
            shutil.move(temp_archive_name, archive_name)
        return True
    
    def extract(self, archive_name, temp_dir_name, dir_name):
        """Extract the archive.
        """
        # Maybe the dir is already there ...
        if os.path.isdir(dir_name):
            return
        
        # Extract it
        try:
            print('Extracting ...', end='')
            with self._arch_func(archive_name, mode='r') as archive:
                archive.extractall(temp_dir_name)
        except Exception:
            remove(archive_name)  # it might be corrupt
            raise
        
        # Pop out empty dirs
        while len(os.listdir(temp_dir_name)) == 1:
            pop_dir = os.listdir(temp_dir_name)[0]
            for name in os.listdir(os.path.join(temp_dir_name, pop_dir)):
                shutil.move(os.path.join(temp_dir_name, pop_dir, name),
                            os.path.join(temp_dir_name, name))
            os.rmdir(os.path.join(temp_dir_name, pop_dir))
        
        print('done')
        
        # Mark dir as done
        if os.path.isdir(dir_name):
            pass  # another process beat us to it
        else:
            shutil.move(temp_dir_name, dir_name)
        return True


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


#

def get_pid_list():
    """ Get list of pids.
    """
    if sys.platform.startswith('win'):
        cmd = ['tasklist']
        index = 1
    else:  # Posix
        cmd = ['ps', '-U', 0]
        index = 0
    
    out = subprocess.check_output(cmd).decode()
    pids = []
    for line in out.splitlines():
        parts = [i.strip() for i in line.replace('\t', ' ').split(' ') if i]
        if len(parts) >= index:
            try:
                pids.append(int(parts[1]))
            except ValueError:
                pass
    pids.sort()
    return pids


_delete_prefix = 'todelete#'

def remove(path1):
    """ Mark a file or directory for removal and try to remove it.
    If it fails, that's ok; we'll remove it later.
    """
    if not os.path.exists(path1):
        return
    # Rename if we must/can
    if path1.startswith(_delete_prefix):
        path2 = path1
    else:
        for i in range(100):
            path2 = _delete_prefix + str(i) + path1
            try:
                shutil.move(path1, path2)
                break
            except Exception:
                pass
        else:
            path2 = path1
    # Delete if we can
    try:
        if os.path.isfile(path2):
            os.remove(path2)
        elif os.path.isdir(path2):
            shutil.rmtree(path2)
    except Exception:
        pass


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
        prefix = os.path.abspath(os.path.dirname(sys.executable))
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


Downloader(r'C:\Users\Almar\AppData\Local\flexx\webruntimes', 'nw', '0.19.5', 'https://dl.nwjs.io/v0.19.5/nwjs-v0.19.5-win-x64.zip', force=1).start()
