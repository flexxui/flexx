""" Web runtime based on node-webkit

https://github.com/nwjs/nw.js

"""

# todo: needs more work to discover the nw executable.

import os
import sys
import json
import shutil

from .common import WebRuntime, create_temp_app_dir


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
    
    paths = [
        "/lib/x86_64-linux-gnu/libudev.so.1",  # Ubuntu, Xubuntu, Mint
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
    paths = []
    paths.append('/home/almar/projects/node-webkit-v0.11.5-linux-x64/nw')
    
    # Test each location
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


class NodeWebkitRuntime(WebRuntime):
    """ Web runtime based on node-webkit.
    """
    
    _app_count = 0
    
    def _launch(self):
        NodeWebkitRuntime._app_count += 1
        
        # Get dir to store app definition
        app_path = create_temp_app_dir('nw', str(NodeWebkitRuntime._app_count))
        id = os.path.basename(app_path).split('_', 1)[1]
        
        # Populate app definition
        D = get_template()
        D['name'] = 'app' + id
        D['main'] = self._kwargs['url']
        D['window']['title'] = self._kwargs['title'] or 'node-webkit runtime'
        
        # Set size (position can be null, center, mouse)
        size = self._kwargs.get('size', (640, 480))
        D['window']['width'], D['window']['height'] = size[0], size[1]
        
        # Icon?
        if self._kwargs.get('icon'):
            print(self._kwargs.get('icon'))
            icon = self._kwargs.get('icon')
            icon_path = os.path.join(app_path, 'app.png')  # nw can handle ico
            icon.write(icon_path)
            smallest = '%i.png' % icon.image_sizes()[0]
            D['window']['icon'] = icon_path.rsplit('.', 1)[0] + smallest
        
        # Write
        with open(os.path.join(app_path, 'package.json'), 'wb') as f:
            f.write(json.dumps(D, indent=4).encode('utf-8'))
        
        # Fix libudef bug
        fix_libudef(app_path)
        if sys.platform.startswith('linux'):
            llp = app_path + os.pathsep + os.getenv('LD_LIBRARY_PATH', '')
        
        # Launch
        exe = get_nodewebkit_exe() or 'nw'
        cmd = [exe, app_path] 
        self._start_subprocess(cmd, LD_LIBRARY_PATH=llp)
