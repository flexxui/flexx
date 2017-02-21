""" Web runtime based on NW.js

https://github.com/nwjs/nw.js


Dev notes
---------

Apps must have a way to be "unique", so that if you create 2 apps with Flexx,
they won't group on the taskbar, and are preferably easily discovered in the
process manager.

The "name" in the manifest is one option. Note that an appdata dir is
created for each used name, unless one sets --user-data-dir, as we do.

The "description" in the manifest, not sure where that turns up.

The name of the executable is the main thing to change.

"""

import os.path as op
import os
import sys
import json
import tempfile

from .. import config
from ._common import DesktopRuntime
from ._manage import create_temp_app_dir
from ._manage import open_arch, extract_arch, versionstring


# http://docs.nwjs.io/en/latest/References/Manifest%20Format
def get_manifest_template():
    return {"name": "flexx_nw_app",
            "main": "",
            "nodejs": False,
            # "single-instance": False,  # Deprecated; is always True
            "description": "an app made with Flexx ui",
            "version": "1.0",
            "keywords": [],
            
            "window": {
                "title": "",
                "icon": "",
                "toolbar": False,
                "frame": True,
                "width": 640,
                "height": 480,
                "position": "center",
                "resizable": True,
                "min_width": 10,
                "min_height": 10,
                #"max_width": 800,
                #"max_height": 600,
                "always-on-top": False,
                "fullscreen": False,
                "kiosk": False,
                "transparent": False,
                "show_in_taskbar": True,
                "show": True
                },
            
            "webkit": {
                "plugin": True,
                "java": False
                },
            
            # Tweak chromium: es3 == webgl2, single process makes things
            # more compact, but does not work on OS X.
            "chromium-args": ' '.join(['--enable-unsafe-es3-apis',
                                       # '--single-process',
                                       ]),
            }


def fix_libudef(dest):
    """ Fix the dependency for libudef by making a link to libudef.so.1.
    
    github.com/rogerwang/node-webkit/wiki/The-solution-of-lacking-libudev.so.0 
    """
    
    paths = ["/lib/x86_64-linux-gnu/libudev.so.1",  # Ubuntu, Xubuntu, Mint
             "/usr/lib64/libudev.so.1",  # SUSE, Fedora
             "/usr/lib/libudev.so.1",  # Arch, Fedora 32bit
             "/lib/i386-linux-gnu/libudev.so.1",  # Ubuntu 32bit
             ]
    
    target = op.join(dest, 'libudev.so.0')
    for path in paths:
        if op.isfile(path) and not op.isfile(target):
            os.symlink(path, target)


class NWRuntime(DesktopRuntime):
    """ Desktop runtime based on NW.js (http://nwjs.io, formerly
    node-webkit), which uses the Chromium engine. Flexx will install/update the
    runtime if it finds a suitable archive in a few common locations like
    the desktop, download dir and temp dir. That way, the end-user only
    has to download the archive to make this runtime work.
    
    This runtime is visible in the task manager under a custom process name
    (``sys.executable + '-ui'``), making it easy to spot in the task manager,
    and avoids task-bar grouping. Compared to the Firefox app runtime,
    this runtime uses more processes and memory, but is generally faster.
    
    The supported ``windowmode`` values are 'normal', 'fullscreen',
    'kiosk' ('maximized' is ignored).
    """
    
    _pending_install = None
    
    def _get_name(self):
        return 'nw'
    
    def _get_install_instuctions(self):
        m = ('Download the NW.js archive for your platform from '
             '"http://nwjs.io". Flexx will find the file if it is placed in '
             'your home dir, desktop, downloads dir (where most browser save '
             'it) or the default temp dir.')
        return m
    
    def _get_exe_name(self, dir):
        if sys.platform.startswith('win'):
            return op.join(dir, 'nw.exe')
        elif sys.platform.startswith('darwin'):
            return op.join(dir, 'nwjs.app', 'Contents', 'MacOS', 'nwjs')
        else:
            return op.join(dir, 'nw')
    
    def _get_exe(self):
        # Get exe to up-to-date locally installed
        # (this does an install/update if necessary)
        exe = op.realpath(self._get_exe_name(self.get_runtime_dir()))
        if op.isfile(exe):
            return exe
    
    def _install_runtime(self, archive, path):
        extract_arch(open_arch(archive), path)
    
    def _get_system_version(self):
        """ Get the version and filename of any valid nwjs archive for this
        platform.
        """
        
        # Where can we look for archives
        dirs = [op.expanduser('~'),
                op.expanduser('~/Desktop'),
                op.expanduser('~/Downloads'),
                tempfile.gettempdir(),
                ]
        
        # What are we looking for?
        exts = '.zip', '.tar', '.tar.gz', '.tar.bz2'
        if sys.platform.startswith('win'):
            plat = '-win'
        elif sys.platform.startswith('linux'):
            plat = '-linux'
        elif sys.platform.startswith('darwin'):
            plat = '-osx'
        
        # Collect archives
        archives = {}  # version -> filename
        for dir in dirs:
            if os.path.isdir(dir):
                for fname in os.listdir(dir):
                    if fname.startswith('nwjs-v') and plat in fname:
                        if fname.lower().endswith(exts):
                            version = fname.split('-v')[1].split('-')[0]
                            archives[version] = os.path.join(dir, fname)
        
        # Avoid having to open archives which we know are not of higher version
        version_th, _ = self.get_cached_version()
        
        # Try - highest version first - whether the archive is ok
        for version in reversed(sorted(archives, key=versionstring)):
            if version_th and versionstring(version) <= versionstring(version_th):
                break
            try:
                with open_arch(archives[version]):
                    pass
            except Exception:
                continue
            else:
                return version, archives[version]
        
        return None, None
    
    def _get_version(self):
        self.get_exe()
        cur_version, _ = self.get_cached_version()
        return cur_version
    
    def _test_platform(self):
        if not (sys.platform.startswith('win') or
                sys.platform.startswith('linux') or
                sys.platform.startswith('darwin')):
            raise RuntimeError('NW.js runtime is not supported on platform ' +
                               sys.platform)
    
    def _launch_tab(self, url):
        raise RuntimeError('NW runtime cannot launch tabs.')
    
    def _launch_app(self, url):
        
        self._test_platform()
        self._clean_nw_dirs()
        
        # Get dir to store app definition
        app_path = create_temp_app_dir('nw')
        id = op.basename(app_path).split('_', 1)[1].replace('~', '_')
        
        # Get runtime exe
        if config.nw_exe:
            # User specifies the executable, we're not going to worry about version
            exe = config.nw_exe
        else:
            # We install the runtime, based on a minimal required version
            exe = self.get_exe()
            
            # Change exe to avoid grouping + easier recognition in task manager
            if exe and op.isfile(op.realpath(exe)):
                exe = self._get_app_exe(exe, app_path)
        
        # Populate app definition
        # name must be a unique, lowercase alpha-numeric name without spaces.
        # It may include "." or "_" or "-" characters. Normally, NW.js stores
        # the app's profile data under the directory named name, but we
        # overload user-data-dir.
        
        # From 0.20.0, even with --user-data-dir, a profile dir with "name" is
        # still created (at least on Windows). Fortunately. the name does not
        # have to be unique, perhaps because we define a custom profile dir.
        D = get_manifest_template()
        D['name'] = 'flexx_stub_nw_profile'
        D['description'] += ' (%s)' % id
        D['main'] = url
        D['window']['title'] = self._title
        
        # Set size (position can be null, center, mouse)
        D['window']['kiosk'] = self._windowmode == 'kiosk'
        D['window']['fullscreen'] = self._windowmode == 'fullscreen'
        D['window']['width'], D['window']['height'] = self._size
        
        # Icon (note that icon is "overloaded" if nw is wrapped in a runtime.app)
        self._icon.write(op.join(app_path, 'app.png'))  # ico does not work
        size = [i for i in self._icon.image_sizes() if i <= 64][-1]
        D['window']['icon'] = 'app%i.png' % size
        
        # Write app manifest
        with open(op.join(app_path, 'package.json'), 'wb') as f:
            f.write(json.dumps(D, indent=4).encode())
        
        # Fix libudef bug
        llp = os.getenv('LD_LIBRARY_PATH', '')
        if sys.platform.startswith('linux'):
            fix_libudef(app_path)
            llp = app_path + os.pathsep + llp
        
        # Prepare profile dir for NW/Chromium to let --user-data-dir point to.
        # This dir is unique for each instance of the app, but because it is
        # inside the app_path, it gets automatically cleaned up.
        profile_dir = op.join(app_path, 'stub_profile')
        if not op.isdir(profile_dir):
            os.mkdir(profile_dir)
        
        # Launch
        cmd = [exe, '--user-data-dir=' + profile_dir, app_path]
        self._start_subprocess(cmd, LD_LIBRARY_PATH=llp)
    
    def _clean_nw_dirs(self):
        """ NW makes empty dirs in temp dir, clean these up.
        """
        if sys.platform.startswith('win'):  # only an issue on Windows
            dir = tempfile.gettempdir()
            for dname in os.listdir(dir):
                if dname.startswith('nw'):
                    dirname = os.path.join(dir, dname)
                    if not os.listdir(dirname):
                        try:
                            os.rmdir(dirname)
                        except Exception:
                            pass
