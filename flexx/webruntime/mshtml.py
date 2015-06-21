""" Web runtime based on MSHTML, i.e. Microsofts Trident engine.
"""

import os
import sys


def get_ie_exe():
    """ Get the path of the Internet Explorer executable
    
    If the path could not be found, returns None. You may still be able
    to launch using "iexplore" though.
    """
    paths = []
    
    # Collect possible locations
    if sys.platform.startswith('win'):
        for basepath in ('C:\\Program Files\\', 'C:\\Program Files (x86)\\'):
            paths.append(basepath + 'Internet Explorer\\iexplore.exe')
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None
