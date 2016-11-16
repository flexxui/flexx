"""
Module that can dynamically generate stubs.
"""

import sys


class JSConstant:
    """ Class to represent variables that are used in JS, and are considered
    global or otherwise available in a way that Python cannot know.
    """
    
    def __init__(self, name='jsconstant'):
        self._name = name
    
    def __repr__(self):  # pragma: no cover
        return '<%s %s>' % (self.__class__.__name__, self._name)


class Stub:
    
    def __getattr__(self, name):
        if name == 'JSConstant':
            return JSConstant
        else:
            return JSConstant(name)


# Seems hacky, but is supported: http://stackoverflow.com/a/7668273/2271927
sys.modules[__name__] = Stub()
