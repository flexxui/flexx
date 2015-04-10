""" Class that contains the OpenGL code to show a texture.

The code is written so that it can run on both old and new systems,
switching between the fixed function and modern pipeline as necessary.
"""

import os
import ctypes

from .gllib import gl

TEX_WIDTH = 512

GL_VERSION = 7938
GL_COLOR_BUFFER_BIT = 16384
GL_TRIANGLES = 4
GL_BLEND = 3042
GL_SRC_ALPHA = 770
GL_ONE_MINUS_SRC_ALPHA = 771

GL_LUMINANCE = 6409
GL_ALPHA = 6406
GL_RGBA = 6408
GL_FLOAT = 5126
GL_UNSIGNED_BYTE = 5121

GL_TEXTURE_2D = 3553
GL_TEXTURE_WRAP_S = 10242
GL_TEXTURE_WRAP_T = 10243
GL_TEXTURE_MAG_FILTER = 10240
GL_TEXTURE_MIN_FILTER = 10241
GL_LINEAR = 9729
GL_REPEAT = 10497

GL_VERTEX_ARRAY = 32884
GL_TEXTURE_COORD_ARRAY = 32888
GL_PROJECTION = 5889
GL_MODELVIEW = 5888
GL_FLAT = 7424

THISDIR = os.path.dirname(os.path.abspath(__file__))


class Tex(object):
    
    _known_errors = {1280: 'invalid enum',
                     1281: 'invalid value',
                     1282: 'invalid operation',
                     }
    
    def __init__(self):
        
        if False:
            import imageio
            im = imageio.imread('astronaut.png')[:,:,1].copy()
            self._tex_size = im.shape[1], im.shape[0]
            self._data = im.tostring()
        else:
            self._data = open(os.path.join(THISDIR, 'glyphs.blob'), 'rb').read()
            self._tex_size = TEX_WIDTH, len(self._data) // TEX_WIDTH
        
        self._use_new_gl = True
        self._bgcolor = 0.8, 0.8, 0.8
        self._color = 0, 0, 0
        self.init_gl()
    
    def set_vertex_data(self, vcoords, tcoords):
        #tc = [0,1, 1,1, 0,0, 0,0, 1,1, 1,0]
        #vc = [-1,-1, +1,-1, -1,+1, -1,+1, +1,-1, +1,+1]
        
        BufferType = ctypes.c_float*len(vcoords)
        self._vcoords = BufferType()
        self._tcoords = BufferType()
        self._vcoords[:] = vcoords
        self._tcoords[:] = tcoords
    
    def _check_error(self, where):
        err = gl.glGetError()
        if err:
            err = self._known_errors.get(err, str(err))
            print('OpenGL error %s (%s)' % (where, err))
    
    def init_gl(self):
        # Load lib if not already done
        gl.activate()  
        
        # Get GL version
        version = gl.glGetString(GL_VERSION).decode('utf-8')
        if not version:
            raise RuntimeError('No context yet')
        elif True:  # version < '2.1':
            self._use_new_gl = False
        print(version)
        
        # Init
        if self._use_new_gl:
            self._create_texture()
            self._create_program()
        else:
            self._create_texture()
    
    def _reshape(self, size):
        gl.glViewport(0, 0, int(size[0]), int(size[1]))
        if self._use_new_gl:
            pass
        else:
            gl.glMatrixMode(GL_PROJECTION)
            gl.glLoadIdentity()
            gl.glMatrixMode(GL_MODELVIEW)
            gl.glLoadIdentity()
        self._check_error('reshaping')
    
    def _create_texture(self):
        # Get texture name
        textures = (ctypes.c_uint*1)()
        gl.glGenTextures(1, textures)
        self._texid = textures[0]
        
        # Bind
        gl.glBindTexture(GL_TEXTURE_2D, self._texid)
        
        # Set properties
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        
        # Upload (GL_ALPHA or GL_LUMINANCE)
        w, h = self._tex_size
        #ptr = self._data
        ptr = ctypes.cast(self._data, ctypes.c_void_p)
        gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, w, h, 0, 
                        GL_ALPHA, GL_UNSIGNED_BYTE, ptr)
        
        self._check_error('creating texture')
    
    def _create_program(self):
        pass
    
    def draw(self):
        
        # Clear
        gl.glClearColor(*(self._bgcolor + (1.0, )))
        gl.glClear(GL_COLOR_BUFFER_BIT)
        
        # Blending
        gl.glEnable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glColor3f(*self._color)
        
        # Enable texture
        gl.glEnable(GL_TEXTURE_2D)
        gl.glBindTexture(GL_TEXTURE_2D, self._texid)
        
        self._check_error('preparing for drawing')
        
        if self._use_new_gl:
            # todo: implement modern OpenGL version for systems that use ES 
            # or have otherwise a disabled fixed function pipeline
            raise NotImplementedError()
        
        else:
            
            # Draw texture
            #import OpenGL.GL as GL
            if True:
                gl.glEnableClientState(GL_VERTEX_ARRAY)
                gl.glEnableClientState(GL_TEXTURE_COORD_ARRAY)
                gl.glVertexPointer(2, GL_FLOAT, 0, self._vcoords)
                gl.glTexCoordPointer(2, GL_FLOAT, 0, self._tcoords)
                gl.glDrawArrays(GL_TRIANGLES, 0, len(self._vcoords)//2)
            else:
                gl._lib.glBegin(GL_TRIANGLES)
                gl.glTexCoord2f(0, 1); gl.glVertex3f(-1, -1, 0)
                gl.glTexCoord2f(1, 1); gl.glVertex3f(+1, -1, 0)
                gl.glTexCoord2f(0, 0); gl.glVertex3f(-1, +1, 0)
                #
                gl.glTexCoord2f(0, 0); gl.glVertex3f(-1, +1, 0)
                gl.glTexCoord2f(1, 1); gl.glVertex3f(+1, -1, 0)
                gl.glTexCoord2f(1, 0); gl.glVertex3f(+1, +1, 0)
                
                gl._lib.glEnd()
        
        # Almost done
        gl.glFlush()
        self._check_error('drawing')
