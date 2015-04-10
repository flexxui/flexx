

#from flexx import lui
import os
import sys

sys.path.insert(0, '..')
import lui

from vispy import app

class Canvas(app.Canvas):
    
    def __init__(self):
        app.Canvas.__init__(self)
        self._label = lui.Label('Hello World!\nThis is some sweet stuff, it looks pretty nice!')
    
    def on_initialize(self, event):
        self._t = lui.Tex()
        
    def on_resize(self, event):
        self._t._reshape(self.size)
    
    
    def on_draw(self, event):
        self._t.set_vertex_data(*self._label.generate_data(self.size))
        self._t.draw()


c = Canvas()
c.show()
