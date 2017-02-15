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
        # IE / Edge is installed, or not, but usually there is little choice
        return ''
    
    def _get_version(self):
        return None


class IERuntime(MicrosoftRuntime):
    """ Runtime based on IE (Internet Explorer), only for launching in
    the browser.
    """
    
    def _get_name(self):
        return 'ie'
    
    def _get_exe(self):
        paths = []
        
        # Collect possible locations
        if sys.platform.startswith('win'):
            for basepath in ('C:\\Program Files\\', 'C:\\Program Files (x86)\\'):
                paths.append(basepath + 'Internet Explorer\\iexplore.exe')
        else:
            raise RuntimeError('IE runtime is only available on Windows.')
        
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
