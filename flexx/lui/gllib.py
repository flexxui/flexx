""" Load the GL library
"""

import os
import sys
import ctypes.util

# Load the OpenGL library. We more or less follow the same approach
# as Vispy and PyOpenGL do internally

class Gl(object):
    
    def __init__(self):
        self._lib = None
        self._have_get_proc_address = False
    
    def activate(self):
        if self._lib is None:
            self._load_lib()
            self._init_functions()
    
    def _load_lib(self):
        _lib = ''  # os.getenv('XXX', '')
        need_es2 = False
        
        if _lib != '':
            # Force a library
            if sys.platform.startswith('win'):
                _lib = ctypes.windll.LoadLibrary(_lib)
            else:
                _lib = ctypes.cdll.LoadLibrary(_lib)
        
        elif need_es2:
            # ES2 lib
            es2_file = None
            if 'ES2_LIBRARY' in os.environ:  # todo: is this the correct name?
                if os.path.exists(os.environ['ES2_LIBRARY']):
                    es2_file = os.path.realpath(os.environ['ES2_LIBRARY'])
            if es2_file is None:
                es2_file = ctypes.util.find_library('GLESv2')
            if es2_file is None:
                raise OSError('GL ES 2.0 library not found')
            _lib = ctypes.CDLL(es2_file)
        
        elif sys.platform.startswith('win'):
            # Windows
            _lib = ctypes.windll.opengl32
            try:
                wglGetProcAddress = _lib.wglGetProcAddress
                wglGetProcAddress.restype = ctypes.CFUNCTYPE(
                    ctypes.POINTER(ctypes.c_int))
                wglGetProcAddress.argtypes = [ctypes.c_char_p]
                self._have_get_proc_address = True
            except AttributeError:
                pass
        
        else:
            # Unix-ish
            if sys.platform.startswith('darwin'):
                _fname = ctypes.util.find_library('OpenGL')
            else:
                _fname = ctypes.util.find_library('GL')
            if not _fname:
                raise RuntimeError('Could not load OpenGL library.')
            # Load lib
            _lib = ctypes.cdll.LoadLibrary(_fname)
        
        self._lib = _lib
    
    def _get_gl_func(self, name, restype, argtypes):
        # Based on a function in Pyglet
        try:
            # Try using normal ctypes stuff
            func = getattr(self._lib, name)
            func.restype = restype
            func.argtypes = argtypes
            return func
        except AttributeError:
            if sys.platform.startswith('win'):
                # Ask for a pointer to the function, this is the approach
                # for OpenGL extensions on Windows
                fargs = (restype,) + argtypes
                ftype = ctypes.WINFUNCTYPE(*fargs)
                if not self._have_get_proc_address:
                    raise RuntimeError('Function %s not available.' % name)
                if not _have_context():
                    raise RuntimeError('Using %s with no OpenGL context.' % name)
                address = wglGetProcAddress(name.encode('utf-8'))
                if address:
                    return ctypes.cast(address, ftype)
            # If not Windows or if we did not return function object on Windows:
            raise RuntimeError('Function %s not present in context.' % name)
    
    def _init_functions(self):
        """ Get functions that we can actually use.
        """
        self.glGetError = self._get_gl_func("glGetError", ctypes.c_uint, ())
        self.glClearColor = self._get_gl_func("glClearColor", None, (ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,))
        self.glClear = self._get_gl_func("glClear", None, (ctypes.c_uint,))
        self.glViewport = self._get_gl_func("glViewport", None, (ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,))
        self.glEnable = self._get_gl_func("glEnable", None, (ctypes.c_uint,))
        self.glDisable = self._get_gl_func("glDisable", None, (ctypes.c_uint,))
        self.glFlush = self._get_gl_func("glFlush", None, ())
        self.glBlendFunc = self._get_gl_func("glBlendFunc", None, (ctypes.c_uint, ctypes.c_uint,))
        self.glDrawArrays = self._get_gl_func("glDrawArrays", None, (ctypes.c_uint, ctypes.c_int, ctypes.c_int,))
        self.glGetString = self._get_gl_func("glGetString", ctypes.c_char_p, (ctypes.c_uint,))
        
        self.glGenTextures = self._get_gl_func("glGenTextures", None, (ctypes.c_int, ctypes.POINTER(ctypes.c_uint),))
        self.glBindTexture = self._get_gl_func("glBindTexture", None, (ctypes.c_uint, ctypes.c_uint,))
        self.glTexParameteri = self._get_gl_func("glTexParameteri", None, (ctypes.c_uint, ctypes.c_uint, ctypes.c_int,))
        self.glTexImage2D = self._get_gl_func("glTexImage2D", None, (ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,))
        
        # These are for fixed function only
        self.glMatrixMode = self._get_gl_func("glMatrixMode", None, (ctypes.c_uint,))
        self.glLoadIdentity = self._get_gl_func("glLoadIdentity", None, ())
        self.glColor3f = self._get_gl_func("glColor3f", None, (ctypes.c_float, ctypes.c_float, ctypes.c_float, ))
        self.glEnableClientState = self._get_gl_func("glEnableClientState", None, (ctypes.c_uint,))
        self.glVertexPointer = self._get_gl_func("glVertexPointer", None, (ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ))
        self.glTexCoordPointer = self._get_gl_func("glTexCoordPointer", None, (ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ))
        
        # These can be removed soon I think
        self.glTexCoord2f = self._get_gl_func("glTexCoord2f", None, (ctypes.c_float, ctypes.c_float, ))
        self.glVertex3f = self._get_gl_func("glVertex3f", None, (ctypes.c_float, ctypes.c_float, ctypes.c_float, ))
        
# Create instance
gl = Gl()
