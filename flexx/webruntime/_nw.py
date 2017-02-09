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
import re
import sys
import json
import struct
import shutil
from urllib.request import urlopen

from .. import config
from ._common import DesktopRuntime
from ._manage import RUNTIME_DIR, download_runtime, create_temp_app_dir


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
    """ Desktop runtime based on NW.js (http://nwjs.io/, formerly
    node-webkit), which uses the Chromium engine. Flexx takes
    care of downloading (and updating) the runtime when needed.
    
    This runtime is visible in the task manager under a custom process name
    (``sys.executable + '-ui'``), making it easy to spot in the task manager,
    and avoids task-bar grouping. Compared to the Firefox app runtime,
    this runtime uses more processes and memory, but is generally faster.
    """
    
    def _get_name(self):
        return 'nw'
    
    def _get_exe_name(self, dir):
        if sys.platform.startswith('win'):
            return op.join(dir, 'nw.exe')
        elif sys.platform.startswith('darwin'):
            return op.join(dir, 'nwjs.app', 'Contents', 'MacOS', 'nwjs')
        else:
            return op.join(dir, 'nw')
    
    def _get_exe(self):
        cur_version = self.get_current_version() or ''
        if cur_version:
            dir = op.join(RUNTIME_DIR, self.get_name() + '_' + cur_version)
            exe = op.realpath(self._get_exe_name(dir))
            if op.isfile(exe):
                return exe
    
    # todo: if not installedm is_available is false, giving not chance to install
    
    def _get_version(self):
        return self.get_current_version()  # todo: rename to _get_chached_version or something
    
    def _get_latest_version(self):
        """" Get latest version of the NW runtime.
        """
        text = urlopen('https://dl.nwjs.io/').read().decode('utf-8', 'ignore')
        versions = re.findall('href\=\"v(.+?)\"', text)
        versions_int = []
        for v in versions:
            v = v.strip('/')
            try:
                versions_int.append(tuple([int(i) for i in v.split('.')]))
            except Exception:
                pass
        versions_int.sort()
        return '.'.join([str(i) for i in versions_int[-1]])
    
    def _get_download_url(self, version, platform=None):
        """ Given a version, get the url where it can be downloaded.
        """
        platform = platform or sys.platform
        if platform.startswith('win'):
            plat, ext = '-win', '.zip'
        elif platform.startswith('linux'):
            plat, ext = '-linux', '.tar.gz'
        elif platform.startswith('darwin'):
            plat, ext = '-osx', '.zip'
        else:
            raise RuntimeError('Unsupported platform')
        plat += '-x64' if (struct.calcsize('P') == 8) else '-x64'
        return 'https://dl.nwjs.io/v' + version + '/nwjs-v' + version + plat + ext
    
    def _install_runtime(self):
        latest_version = self._get_latest_version()
        url = self._get_download_url(latest_version)
        download_runtime(self.get_name(), latest_version, url)
    
    def _test_platform(self):
        if not (sys.platform.startswith('win') or
                sys.platform.startswith('linux') or
                sys.platform.startswith('darwin')):
            raise RuntimeError('NW.js runtime is not supported on platform ' +
                               sys.platform)
            # todo: show GUI? that wont work either, but if dialite has a nice fallback, we might as well use that to notify the user
    
    def _launch_tab(self, url):
        raise RuntimeError('NW runtime cannot launch tabs.')
    
    def _launch_app(self, url):
        
        self._test_platform()
        
        # Get dir to store app definition
        app_path = create_temp_app_dir('nw')
        id = op.basename(app_path).split('_', 1)[1].replace('~', '_')
        
        # Get runtime exe
        if config.nw_exe:
            # User specifies the executable, we're not going to worry about version
            exe = flexx.config.nw_exe
        else:
            # We install the runtime, based on a minimal required version
            exe = self._get_exe_name(self.get_runtime(config.nw_min_version))
            
            # Change exe to avoid grouping + easier recognition in task manager
            if exe and op.isfile(op.realpath(exe)):
                exe = self._get_app_exe(exe, app_path)
        
        # Populate app definition
        # name must be a unique, lowercase alpha-numeric name without spaces.
        # It may include "." or "_" or "-" characters. Normally, NW.js stores
        # the app's profile data under the directory named name, but we
        # overload user-data-dir.
        D = get_manifest_template()
        D['name'] = self._kwargs['name'] + '_' + id
        D['description'] += ' (%s)' % id
        D['main'] = url
        D['window']['title'] = self._kwargs['title']  # ensured by DesktopRuntime
        
        # Set size (position can be null, center, mouse)
        size = self._kwargs['size']
        D['window']['width'], D['window']['height'] = size[0], size[1]
        
        # Icon (note that icon is "overloaded" if nw is wrapped in a runtime.app)
        icon = self._kwargs['icon']
        icon.write(op.join(app_path, 'app.png'))  # ico does not work
        size = [i for i in icon.image_sizes() if i <= 64][-1]
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
        cmd = [exe, app_path, '--user-data-dir=' + profile_dir]
        self._start_subprocess(cmd, LD_LIBRARY_PATH=llp)
