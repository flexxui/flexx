""" Web runtime based on MSHTML, i.e. Microsofts Trident engine.
"""

import os.path as op
import os
import sys

from ._common import BaseRuntime


class MicrosoftRuntime(BaseRuntime):
    """ Base class for IE and Edge runtimes.
    """
    
    def _get_install_instuctions(self):
        avail = 'available' if sys.platform.startswith('win') else 'only available'
        name = self.get_name()
        win = dict(ie='Windows', edge='modern versions of Windows')[name]
        return 'Runtime %s is %s on %s.' % (name, avail, win)
    
    def _get_version(self):
        return None


class IERuntime(MicrosoftRuntime):
    """ Runtime based on IE (Internet Explorer), only for launching in
    the browser.
    """
    
    def _get_name(self):
        return 'ie'
    
    def _get_exe(self):
        if not sys.platform.startswith('win'):
            return None
        
        # Collect possible locations
        paths = []
        for basepath in ('C:\\Program Files\\', 'C:\\Program Files (x86)\\'):
            paths.append(basepath + 'Internet Explorer\\iexplore.exe')
        
        # Try location until we find one that exists
        for path in paths:
            if op.isfile(path):
                return path
        
        # IE not available
        return None
    
    def _launch_tab(self, url):
        self._spawn_subprocess([self.get_exe(), url])

    def _launch_app(self, url):
        raise RuntimeError('IE runtime cannot run as an app.')


class EdgeRuntime(MicrosoftRuntime):
    """ Runtime based on Edge, only for launching in the browser.
    """
    
    def _get_name(self):
        return 'edge'
    
    def _get_exe(self):
        if not sys.platform.startswith('win'):
            return None
        
        path = op.join(os.environ['windir'], 'SystemApps',
                       'Microsoft.MicrosoftEdge_8wekyb3d8bbwe',
                       'MicrosoftEdge.exe')
    
        if op.isfile(path):
            return path
        
        # Edge not available
        return None
    
    def _launch_tab(self, url):
        self._spawn_subprocess(['start', 'microsoft-edge:'+url], shell=True)

    def _launch_app(self, url):
        raise RuntimeError('Edge runtime cannot run as an app.')
