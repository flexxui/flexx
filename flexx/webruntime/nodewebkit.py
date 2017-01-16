""" Web runtime based on node-webkit

https://github.com/nwjs/nw.js

"""

# todo: needs more work to discover the nw executable.

import os
import re
import sys
import json
import struct
import shutil
from urllib.request import urlopen

from .common import DesktopRuntime, create_temp_app_dir


def get_template():
    return {"name": "flexx_ui_app",
            "main": "",
            "nodejs": False,
            "single-instance": False,
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
                }
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
    
    target = os.path.join(dest, 'libudev.so.0')
    for path in paths:
        if os.path.isfile(path) and not os.path.isfile(target):
            os.symlink(path, target)


def get_nodewebkit_exe():
    """ Try to find the executable for node-webkit
    
    Return None if it could not be found.
    """
    
    # Get possible locations of nw exe
    dirs = ['/opt', '~/tools', '~/apps', '~/dev']
    
    for dir in dirs:
        dir = os.path.expanduser(dir)
        if not os.path.isdir(dir):
            continue
        subs = os.listdir(dir)
        exes = []
        for sub in subs:
            if sub.startswith('node-webkit'):
                exes.append(os.path.join(dir, sub, 'nw'))
        if exes:
            exes.sort()
            return exes[-1]
    
    return r'C:\dev\tools\nwjs-v0.19.5-win-x64\nw.exe'
    return None


class NodeWebkitRuntime(DesktopRuntime):
    """ Desktop runtime for nw.js (http://nwjs.io/, formerly
    node-webkit), which is based on Chromium and nodejs. Requires nw.js
    to be installed.
    """
    
    _app_count = 0
    
    def _get_name(self):
        return 'nw'
    
    def _launch(self):
        NodeWebkitRuntime._app_count += 1
        
        # Get dir to store app definition
        app_path = create_temp_app_dir('nw', str(NodeWebkitRuntime._app_count))
        id = os.path.basename(app_path).split('_', 1)[1]
        
        # Populate app definition
        D = get_template()
        D['name'] = 'app' + id
        D['main'] = self._kwargs['url']
        D['window']['title'] = self._kwargs.get('title', 'nw.js runtime')
        
        # Set size (position can be null, center, mouse)
        size = self._kwargs.get('size', (640, 480))
        D['window']['width'], D['window']['height'] = size[0], size[1]
        
        # Icon?
        if self._kwargs.get('icon'):
            icon = self._kwargs.get('icon')
            icon_path = os.path.join(app_path, 'app.png')  # nw can handle ico
            icon.write(icon_path)
            D['window']['icon'] = 'app%i.png' % icon.image_sizes()[0]
        
        # Write
        with open(os.path.join(app_path, 'package.json'), 'wb') as f:
            f.write(json.dumps(D, indent=4).encode('utf-8'))
        
        # Fix libudef bug
        fix_libudef(app_path)
        llp = os.getenv('LD_LIBRARY_PATH', '')
        if sys.platform.startswith('linux'):
            llp = app_path + os.pathsep + llp
        
        # Launch
        exe = get_nodewebkit_exe() or 'nw'
        cmd = [exe, app_path, '--enable-unsafe-es3-apis']  # with webgl2!
        self._start_subprocess(cmd, LD_LIBRARY_PATH=llp)
    ##
    def get_latest_version(self):
        # return '0.19.5' ? hardcoded by Flexx?
        
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
    
    def get_url(self, version, platform=None):
        """ Given a version, get the url where it can be downloaded.
        """
        platform = platform or sys.platform
        if platform.startswith('win'):
            plat = '-win'
            ext = '.zip'
        elif platform.startswith('linux'):
            plat = '-linux'
            ext = '.tar.gz'
        elif platform.startswith('darwin'):
            plat = '-osx'
            ext = '.zip'
        else:
            raise RuntimeError('Unsupported platform')  # todo: detect earlier
        if struct.calcsize('P') == 8:
            plat += '-x64'
        else:
            plat += '-ia32'
        return 'https://dl.nwjs.io/v' + version + '/nwjs-v' + version + plat + ext
    ##
    
    
