"""
Code related to managing runtimes and temporary app directories.

We follow a convetion by which files and dirs can be associated with a
certain process by giving it a suffix "~pid". That way, we can detect
when dirs are not in use and have them removed. We also rename files/dirs
that ought to be removed, so that if deletion fails, we can try again later.
"""

import os.path as op
import os
import sys
import time
import shutil
import subprocess
from urllib.request import urlopen, Request

from . import logger


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
    userDir = op.expanduser('~')

    # Get system app data dir
    path = None
    if sys.platform.startswith('win'):
        path1, path2 = os.getenv('LOCALAPPDATA'), os.getenv('APPDATA')
        path = (path2 or path1) if roaming else (path1 or path2)
    elif sys.platform.startswith('darwin') and not macAsLinux:
        path = op.join(userDir, 'Library', 'Application Support')
    # On Linux and as fallback
    if not (path and op.isdir(path)):
        path = userDir

    # Maybe we should store things local to the executable (in case of a
    # portable distro or a frozen application that wants to be portable)
    prefix = sys.prefix
    if getattr(sys, 'frozen', None):  # See application_dir() function
        prefix = op.abspath(op.dirname(sys.executable))
    for reldir in ('settings', '../settings'):
        localpath = op.abspath(op.join(prefix, reldir))
        if op.isdir(localpath):  # pragma: no cover
            try:
                open(op.join(localpath, 'test.write'), 'wb').close()
                os.remove(op.join(localpath, 'test.write'))
            except IOError:
                pass  # We cannot write in this directory
            else:
                path = localpath
                break

    # Get path specific for this app
    if appname:
        if path == userDir:
            appname = '.' + appname.lstrip('.')  # Make it a hidden directory
        path = op.join(path, appname)
        if not op.isdir(path):  # pragma: no cover
            os.mkdir(path)

    # Done
    return path


APPDATA_DIR = appdata_dir('flexx')
RUNTIME_DIR = op.join(APPDATA_DIR, 'webruntimes')
TEMP_APP_DIR = op.join(APPDATA_DIR, 'temp_apps')
DELETE_PREFIX = 'todelete~'


# maybe a bit overkill, but hey, it works!
def versionstring(version):
    """ Given a version string or tuple, produce a version string that looks
    a bit funny but can be string-compared to order versions. Works with
    semver. The only restriction is that any part (between two dots) may not
    be more than 9 chars long.
    """
    if isinstance(version, (tuple, list)):
        version = '.'.join(version)
    if not isinstance(version, str):
        raise TypeError('Version must be a tuple or string.')
    version = version.strip().lower()
    version = version.replace(' ', '').replace('\t', '').replace('~', '')
    
    if version == 'latest':
        return '~~'
    
    isnumeric = True
    anchor = 0
    parts = []
    
    def add_part(i):
        part = version[anchor:i]
        if len(part) > 9:
            raise ValueError('Version parts can be at most 9 chars')
        elif part.isnumeric():
            parts.append('~' + part.rjust(9, ' '))
        elif part:
            parts.append(' ' + part.rjust(9, ' '))
    
    for i in range(len(version)):
        c = version[i]
        if i == anchor:
            isnumeric = c.isnumeric()
        if c == '.':
            add_part(i)
            anchor = i + 1
        elif isnumeric and not c.isnumeric():
            add_part(i)
            anchor = i
            isnumeric = False
    
    add_part(len(version))
    return '.'.join(parts) + '.~'


def get_pid_list():
    """ Get list of pids (on Windows, OS X and Linux)
    """
    if sys.platform.startswith('win'):
        cmd = ['tasklist']
    else:  # Posix
        cmd = ['ps', 'aux']  # Not "-u root -N" cause -N does not work on OS X
    
    out = subprocess.check_output(cmd).decode()
    pids = []
    for line in out.splitlines():
        parts = [i.strip() for i in line.replace('\t', ' ').split(' ') if i]
        if len(parts) >= 2 and parts[0] != 'root':
            try:
                pids.append(int(parts[1]))
            except ValueError:
                pass
    pids.sort()  # helps in debugging
    if not pids:
        logger.warn('get_pid_list() found zero pids.')
    return pids


def remove(path1, nowarn=False):
    """ Mark a file or directory for removal (by renaming it) and try
    to remove it. If it fails, that's ok; we'll remove it later.
    """
    if not op.exists(path1):
        return
    dirname, name = op.split(path1)
    
    # Rename if we must/can
    if name.startswith(DELETE_PREFIX):
        path2 = path1
    else:
        for i in range(100):
            path2 = op.join(dirname, DELETE_PREFIX + str(i) + name)
            if not op.exists(path2):
                break
        try:
            os.rename(path1, path2)
        except Exception:
            if not nowarn:
                logger.warn('could not clean up %r' % path1)
            return  # if we cannot rename, we cannot delete
    
    # Delete if we can
    try:
        if op.isfile(path2):
            os.remove(path2)
        elif op.isdir(path2):
            shutil.rmtree(path2)
    except Exception:
        pass


def clean():
    """ Clean up the webruntime dir and temp app dir.
    """
    
    # Ensure that directories exist
    if not op.isdir(APPDATA_DIR):
        os.mkdir(APPDATA_DIR)
    if not op.isdir(RUNTIME_DIR):
        os.mkdir(RUNTIME_DIR)
    if not op.isdir(TEMP_APP_DIR):
        os.mkdir(TEMP_APP_DIR)
    
    # Collect dirs/files and lockfiles
    items = []
    lockfiles = []
    for dir in (RUNTIME_DIR, TEMP_APP_DIR):
        for name in os.listdir(dir):
            path = op.join(dir, name)
            items.append((name, path))
            
            if dir == RUNTIME_DIR and '_' in path and op.isdir(path):
                for lockfilename in os.listdir(path):
                    if lockfilename.startswith('lock~'):
                        try:
                            pid = int(lockfilename.split('~')[-1])
                        except ValueError:
                            continue
                        lockfiles.append((pid, path, lockfilename))
    
    # Get pids, after collecting items, so that we don't remove items for pids
    # that instantiate after getting our list of pids.
    pids = get_pid_list()
    
    # Remove files/dirs that are marked for deletion or associated with a pid
    # that does not exist.
    for name, path in items:
        if '~' in name:
            if name.startswith(DELETE_PREFIX):
                remove(path)
            else:
                try:
                    pid = int(name.split('~')[-1])
                except ValueError:
                    continue  # we probably did not make this
                if pid not in pids:
                    remove(path)
    
    # Remove lockfiles in runtime dirs
    dirs_with_lockfiles = set()
    for pid, dir, fname in lockfiles:
        if pid not in pids:
            try:
                os.remove(op.join(dir, fname))
                continue  # i.e. dont mark dir
            except Exception:
                pass
        dirs_with_lockfiles.add(dir)
    
    # Removing old runtimes that are not used (i.e. have no lock files).
    # In theory, a new process could have spawned since we collected the
    # lock files, but because we always use the latest version of a runtime,
    # this should not be a problem.
    runtimes = {}
    for dname in os.listdir(RUNTIME_DIR):
        name, _, version = dname.partition('_')
        if version:
            runtimes.setdefault(name, []).append(version)
    for name in runtimes:
        versions = runtimes[name]
        versions.sort(key=versionstring)
        for version in versions[:-1]:
            dir = op.join(RUNTIME_DIR, name + '_' + version)
            if dir not in dirs_with_lockfiles:
                remove(dir, True)


def lock_runtime_dir(path):
    """ Lock a runtime dir for this process.
    """
    assert path.startswith(RUNTIME_DIR)
    lockfile = op.join(path, 'lock~%i' % os.getpid())
    if not op.isfile(lockfile):
        with open(lockfile, 'wb'):
            pass


_app_count = 0

def create_temp_app_dir(prefix, cleanup=60):
    """ Create a temporary direrctory and return its path.

    The directory will be named "<prefix>_<timestamp>_<pid>_<suffix>".
    Will clean up directories with the same prefix which are older than
    cleanup seconds.
    """
    global _app_count
    _app_count += 1
    
    prefix = prefix.strip(' _-')
    name = '%s_%i_%i~%i' % (prefix, time.time(), _app_count, os.getpid())
    path = op.join(TEMP_APP_DIR, name)
    os.mkdir(path)
    return path


def download_runtime(runtime_name, version, url):
    """
    Function for downloading a runtime.
    
    * Download archive as xxx.zip~pid
    * On download complete, rename to xxx.zip
    * Extract to yyy~pid
    * When extract is done, rename to yyy
    
    For downloading, we compare the pid to current list of pids to see
    if perhaps another process is already downloading it (though its no
    guarantee, as pids are reused). If there is an archive in progress,
    which has "stalled", we rename the archive and continue downloading.
    """

    # Calculate file system locations
    fname = url.split('?')[0].split('~')[0].split('/')[-1].lower()
    archive_name = op.join(RUNTIME_DIR, fname)
    dir_name = op.join(RUNTIME_DIR, runtime_name + '_' + version)
    
    # Get func to open archive
    import tarfile
    import zipfile
    if fname.endswith(('.tar', '.tar.gz', '.tar.bz2')):
        arch_func = tarfile.open
    elif fname.endswith('.zip'):
        arch_func = zipfile.ZipFile
    else:
        raise ValueError('Dont know how to extract from %s' % fname)
    
    # Go!
    if op.isdir(dir_name):
        return
    if _download(url, archive_name):
        _extract(archive_name, dir_name, arch_func)
    
    # Remove archive
    remove(archive_name)
    
    # Note, if for some reason the runtime is corrupt, the user can goto
    # flexx.webruntime.RUNTIME_DIR and delete it. This solution works for
    # devs but less so for end-users. So frozen apps should either ship the
    # runtime along, or use the xul runtime.


def _download(url, archive_name):
    """ Download the archive.
    """
    temp_archive_name = '%s~%i' % (archive_name, os.getpid())
    
    # Clean, just to be sure
    remove(temp_archive_name)
    
    # Maybe the archive is already there ...
    if op.isfile(archive_name):
        return True
    
    # Get whether the downloading is already in progress by another process
    pids = get_pid_list()
    # pids.remove(os.getpid())
    archives = []  # that do not correspond to an existing pid other than us
    for name in os.listdir(RUNTIME_DIR):
        filename = op.join(RUNTIME_DIR, name)
        if filename.startswith(archive_name):
            try:
                pid = int(name.split('~')[-1])
            except ValueError:
                continue  # what is this? not ours, probably
            if pid and pid in pids:
                # another process might be working on it
                if False:  # noqa - maybe we want a silent update at some point?
                    return
            else:
                archives.append(filename)
    
    # Touch file to clear it and tell other processes that we're loading it,
    # or proceed with existing (partial) file.
    if not archives:
        with open(temp_archive_name, 'wb'):
            pass
    else:
        try:
            os.rename(archives[0], temp_archive_name)
        except FileNotFoundError:
            raise  # another process was just a wee bit earlier?
    
    # Open folder in native file explorer for user to see progress
    _open_folder(op.dirname(archive_name))
    
    # Create a file that we keep renaming to indicate progress
    progress_name_t = '%s~ progress %%0.0f %%%% ~%i' % (archive_name, os.getpid())
    progress_name = progress_name_t % 0
    with open(progress_name, 'wb'):
        pass
    
    # Open local file ...
    t0 = time.time()
    with open(temp_archive_name, 'ab') as f_dst:
        tries = 0
        
        while tries < 5:
            tries += 1
            
            try:
                nbytes = f_dst.tell()
                # Open remote resource
                r = Request(url)
                r.headers['Range'] = 'bytes=%i-' % nbytes
                f_src = urlopen(r, timeout=5)
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
                    # Show percentage done in console
                    percentage = 100 * nbytes / file_size
                    print('downloading: %03.1f%%\r' % percentage, end='')
                    # Show percentahe done in FS
                    progress_name2 = progress_name_t % percentage
                    if progress_name2 != progress_name:
                        try:
                            os.rename(progress_name, progress_name2)
                            progress_name = progress_name2
                        except Exception:
                            pass
            
            except (OSError, IOError) as err:
                if tries < 4:
                    logger.warn('%s. Retrying ...' % str(err))
                    time.sleep(0.2)
                    continue
                raise
            break  # retry loop
    
    print('Downloaded %s in %1.f s' % (url, time.time() - t0))
    
    if op.isfile(progress_name):
        try:
            os.remove(progress_name)
        except Exception:
            pass
    
    # Mark archive as done
    if op.isfile(archive_name):
        pass  # another process beat us to it
    else:
        os.rename(temp_archive_name, archive_name)
    return True
    
    
def _extract(archive_name, dir_name, arch_func):
    """ Extract an archive that contains a runtime.
    """
    temp_dir_name = dir_name + '~' + str(os.getpid())
    
    # Maybe the dir is already there ...
    if op.isdir(dir_name):
        return
    
    # Extract it
    try:
        print('Extracting ...', end='')
        with arch_func(archive_name, mode='r') as archive:
            archive.extractall(temp_dir_name)
    except Exception:
        remove(archive_name)  # it might be corrupt
        raise
    
    # Pop out empty dirs
    while True:
        subdirs = os.listdir(temp_dir_name)
        if len(subdirs) != 1 or op.isfile(subdirs[0]) or '.app' in subdirs[0]:
            break
        else:
            pop_dir = subdirs[0] + '~temp'
            os.rename(op.join(temp_dir_name, subdirs[0]),
                      op.join(temp_dir_name, pop_dir))
            for name in os.listdir(op.join(temp_dir_name, pop_dir)):
                os.rename(op.join(temp_dir_name, pop_dir, name),
                          op.join(temp_dir_name, name))
            os.rmdir(op.join(temp_dir_name, pop_dir))
    
    print('done')
    
    # Enable executables for OS X
    import stat
    for dirpath, dirnames, filenames in os.walk(temp_dir_name):
        if dirpath.endswith('/Contents/MacOS'):
            for fname in filenames:
                if '.' not in fname:
                    filename = op.join(dirpath, fname)
                    os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)
    
    # Mark dir as done
    if op.isdir(dir_name):
        pass  # another process beat us to it
    else:
        os.rename(temp_dir_name, dir_name)
    return True


def _open_folder(path):
    """ Open folder in native file explorer, on Windows, OS X and Linux.
    """
    if sys.platform.startswith('win'):
        os.startfile(path)
    elif  sys.platform.startswith('darwin'):
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
