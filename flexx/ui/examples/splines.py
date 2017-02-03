# doc-export: Splines
"""
An interactive spline demo.
"""

from flexx import app, event, ui
from flexx.pyscript import window


GENERAL_TEXT = """
The splines in this exampe are used to interpolate a line between
control points. The the range of influence is shown when a control point
is clicked. Move the control points by dragging them. Points can be
added and deleted by holding shift and clicking.
"""

LINEAR_TEXT = """
This is not really a spline, but its included for reference. Linear
interpolation is C0 continuous, and relatively easy to implement.
"""

BASIS_TEXT = """
A B-spline is a C2 continuous non-interpolating spline, used extensively
in (3D) modeling.
"""

CARDINAL_TEXT = """
A Cardinal spline is a specific type of cubic Hermite spline, and is
C1 continous. Its tension parameter makes it very versatile.
"""

CATMULLROM_TEXT = """
The Catmull–Rom spline is a Cardinal spline with a tension of 0. It is 
commonly used in computer graphics to interpolate motion between key frames.
"""

LAGRANGE_TEXT = """
The Lagrange polynomials result in (C0 continous) interpolation
equivalent to Newton a polynomial. It is, however, know to suffer from
Runge's phenomenon (oscilating).
"""

LANCZOS_TEXT = """
Lanczos interpolation (C1 continous) is based on a windowed sinc
function and is usually considered to produced the best result from the
perspective of the fourier domain. It's mainly used in applications
related audio.
"""


class SplineWidget(ui.CanvasWidget):
    
    class Both:
        
        SPLINES = ['linear', 'basis', 'cardinal', 'catmullrom', 'lagrange', 'lanczos']
        
        @event.prop
        def spline_type(self, v='Cardinal'):
            """ The type of spline.
            """
            v = v.lower().replace(' ', '')
            if v not in self.SPLINES:
                raise ValueError('Invalid spline type')
            return v
        
        @event.prop
        def closed(self, v):
            """ Whether the spline is closed.
            """
            return bool(v)
        
        @event.prop
        def tension(self, v=0.5):
            """ The tension parameter for the Cardinal spline.
            """
            return float(v)
    
    class JS:
        
        def init(self):
            self.ctx = self.node.getContext('2d')
            self.xx = [0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.10, 0.23, 0.61, 0.88]
            self.yy = [0.90, 0.60, 0.90, 0.60, 0.90, 0.70, 0.55, 0.19, 0.11, 0.38]
        
        @event.prop
        def _current_node(self, v=None):
            return v
        
        def factors_linear(self, t):
            return [0, t, (1-t), 0]
        
        def factors_basis(self, t):
            f0 = (1 - t)**3 / 6.0
            f1 = (3 * t**3 - 6 * t**2 + 4) / 6.0
            f2 = (-3 * t**3 + 3 * t**2 + 3 * t + 1) / 6.0
            f3 = t**3 / 6.0
            return f0, f1, f2, f3
        
        def factors_cardinal(self, t):
            tension = self.tension
            tau = 0.5 * (1 - tension)
            f0 = - tau * (t**3 - 2 * t**2 + t)
            f3 = + tau * (t**3 - 1 * t**2)
            f1 = 2 * t**3 - 3 * t**2 + 1 - f3
            f2 = - 2 * t**3 + 3 * t**2 - f0
            return f0, f1, f2, f3
        
        def factors_catmullrom(self, t):
            f0 = - 0.5 * t**3 + 1.0 * t**2 - 0.5 * t
            f1 = + 1.5 * t**3 - 2.5 * t**2 + 1
            f2 = - 1.5 * t**3 + 2.0 * t**2 + 0.5 * t
            f3 = + 0.5 * t**3 - 0.5 * t**2
            return f0, f1, f2, f3
        
        def factors_lagrange(self, t):
            k = -1.0  
            f0 = t / k * (t-1) / (k-1) * (t-2) / (k-2)
            k = 0  
            f1 = (t+1) / (k+1) * (t-1) / (k-1) * (t-2) / (k-2)
            k= 1  
            f2 = (t+1) / (k+1) * t / k * (t-2) / (k-2)
            k = 2  
            f3 = (t + 1) / (k+1) * t / k * (t-1) / (k-1)
            return f0, f1, f2, f3
        
        def factors_lanczos(self, t):
            sin = window.Math.sin
            pi = window.Math.PI
            tt = (1+t)
            f0 = 2*sin(pi*tt)*sin(pi*tt/2) / (pi*pi*tt*tt)
            tt = (2-t)  
            f3 = 2*sin(pi*tt)*sin(pi*tt/2) / (pi*pi*tt*tt)
            if t != 0:
                tt = t
                f1 = 2*sin(pi*tt)*sin(pi*tt/2) / (pi*pi*tt*tt)
            else:  
                f1 =1
            if t != 1:
                tt = (1-t)  
                f2 = 2*sin(pi*tt)*sin(pi*tt/2) / (pi*pi*tt*tt)  
            else:
                f2 = 1
            return f0, f1, f2, f3
        
        @event.connect('mouse_down')
        def _on_mouse_down(self, *events):
            for ev in events:
                w, h = self.size
                # Get closest point
                closest, dist = -1, 999999
                for i in range(len(self.xx)):
                    x, y = self.xx[i] * w, self.yy[i] * h
                    d = ((x - ev.pos[0]) ** 2 + (y - ev.pos[1]) ** 2) ** 0.5
                    if d < dist:
                        closest, dist = i, d
                # Did we touch it or not
                if dist < 9:
                    i = closest
                    if 'Shift' in ev.modifiers:  # Remove point
                        self.xx.pop(i)
                        self.yy.pop(i)
                        self._current_node = None
                        self.update()
                    else:
                        self._current_node = i
                else:
                    if 'Shift' in ev.modifiers:
                        # Add point
                        if not self.xx:
                            i = 0  # There were no points
                        else:
                            # Add in between two points. Compose the vectors
                            # from closest points to neightbour points and to the
                            # cicked point. Check with which vector the latter vector
                            # aligns the best by calculating their angles.
                            #
                            # Get the three points
                            p0 = self.xx[closest+0] * w, self.yy[closest+0] * h
                            if closest == 0:
                                p2 = self.xx[closest+1] * w, self.yy[closest+1] * h
                                p1 = p0[0] - (p2[0] - p0[0]), p0[1] - (p2[1] - p0[1])
                            elif closest == len(self.xx) - 1:
                                p1 = self.xx[closest-1] * w, self.yy[closest-1] * h
                                p2 = p0[0] - (p1[0] - p0[0]), p0[1] - (p1[1] - p0[1])
                            else:
                                p1 = self.xx[closest-1] * w, self.yy[closest-1] * h
                                p2 = self.xx[closest+1] * w, self.yy[closest+1] * h
                            # Calculate vectors, and normalize
                            v1 = p1[0] - p0[0], p1[1] - p0[1]
                            v2 = p2[0] - p0[0], p2[1] - p0[1]
                            v3 = ev.pos[0] - p0[0], ev.pos[1] - p0[1]
                            m1 = (v1[0]**2 + v1[1]**2)**0.5
                            m2 = (v2[0]**2 + v2[1]**2)**0.5
                            m3 = (v3[0]**2 + v3[1]**2)**0.5
                            v1 = v1[0] / m1, v1[1] / m1
                            v2 = v2[0] / m2, v2[1] / m2
                            v3 = v3[0] / m3, v3[1] / m3
                            # Calculate angle
                            a1 = window.Math.acos(v1[0] * v3[0] + v1[1] * v3[1])
                            a2 = window.Math.acos(v2[0] * v3[0] + v2[1] * v3[1])
                            i = closest if a1 < a2 else closest + 1
                        self.xx.insert(i, ev.pos[0] / w)
                        self.yy.insert(i, ev.pos[1] / h)
                        self._current_node = i
        
        @event.connect('mouse_up')
        def _on_mouse_up(self, *events):
            self._current_node = None
        
        @event.connect('mouse_move')
        def _on_mouse_move(self, *events):
            ev = events[-1]
            if self._current_node is not None:
                i = self._current_node
                w, h = self.size
                self.xx[i] = ev.pos[0] / w
                self.yy[i] = ev.pos[1] / h
                self.update()
    
        @event.connect('size', 'spline_type', 'tension', 'closed', '_current_node')
        def update(self, *events):
            
            # Init
            ctx = self.ctx
            w, h = self.size
            ctx.clearRect(0, 0, w, h)
            
            # Get coordinates
            xx = [x * w for x in self.xx]
            yy = [y * h for y in self.yy]
            #
            if self.closed:
                xx = xx[-1:] + xx + xx[:2]
                yy = yy[-1:] + yy + yy[:2]
            else:
                xx = [xx[0] - (xx[1] - xx[0])] + xx + [xx[-1] - (xx[-2] - xx[-1])]
                yy = [yy[0] - (yy[1] - yy[0])] + yy + [yy[-1] - (yy[-2] - yy[-1])]
            
            # Draw grid
            ctx.strokeStyle = '#eee'
            ctx.lineWidth = 1
            for y in range(0, h, 20):
                ctx.beginPath()
                ctx.moveTo(0, y)
                ctx.lineTo(w, y)
                ctx.stroke()
            for x in range(0, w, 20):
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, h)
                ctx.stroke()
            
            # Draw nodes
            ctx.fillStyle = '#acf'
            ctx.strokeStyle = '#000'
            ctx.lineWidth = 2
            for i in range(1, len(xx)-1):
                ctx.beginPath()
                ctx.arc(xx[i], yy[i], 9, 0, 6.2831)
                ctx.fill()
                ctx.stroke()
            
            # Select interpolation function
            fun = self['factors_' + self.spline_type]
            if not fun:
                fun = lambda : (0, 1, 0, 0)
            
            # Draw lines
            
            for i in range(1, len(xx)-2):
                
                ctx.lineCap = "round"
                ctx.lineWidth = 3
                ctx.strokeStyle = '#008'
                support = 1 if self.spline_type == 'linear' else 2
                if self._current_node is not None:
                    if i - (support + 1) < self._current_node < i + support:
                        ctx.strokeStyle = '#08F'
                        ctx.lineWidth = 5
                
                # Get coordinates of the four points
                x0, y0 = xx[i-1], yy[i-1]
                x1, y1 = xx[i+0], yy[i+0]
                x2, y2 = xx[i+1], yy[i+1]
                x3, y3 = xx[i+2], yy[i+2]
                
                # Interpolate
                ctx.beginPath()
                # lineto = ctx.moveTo.bind(ctx)
                lineto = ctx.lineTo.bind(ctx)
                n = 30
                for t in [i/n for i in range(n+1)]:
                    f0, f1, f2, f3 = fun(t)
                    x = x0 * f0 + x1 * f1 + x2 * f2 + x3 * f3
                    y = y0 * f0 + y1 * f1 + y2 * f2 + y3 * f3
                    
                    lineto(x, y)
                    lineto = ctx.lineTo.bind(ctx)
                
                ctx.stroke()


class Splines(ui.Widget):
   
    def init(self):
        
        with ui.HBox():
            
            with ui.VBox(flex=0):
                self.b1 = ui.RadioButton(text='Linear')
                self.b2 = ui.RadioButton(text='Basis')
                self.b3 = ui.RadioButton(text='Cardinal', checked=True)
                self.b4 = ui.RadioButton(text='Catmull Rom')
                self.b5 = ui.RadioButton(text='Lagrange')
                self.b6 = ui.RadioButton(text='Lanczos')
                ui.Widget(style='min-height:10px')
                self.closed = ui.CheckBox(text='Closed')
                ui.Widget(style='min-height:10px')
                self.tension_label = ui.Label(text='Tension: 0.5')
                self.tension = ui.Slider(min=-0.5, max=1, value=0.5)
                ui.Widget(flex=1)
            
            with ui.VBox(flex=1):
                ui.Label(text=GENERAL_TEXT, wrap=True, style='font-size: 12px;')
                self.explanation = ui.Label(text=CARDINAL_TEXT, wrap=True,
                                            style='font-size: 12px;')
                
                self.spline = SplineWidget(flex=1)
    
    class JS:
        
        LINEAR_TEXT = LINEAR_TEXT
        BASIS_TEXT = BASIS_TEXT
        CARDINAL_TEXT = CARDINAL_TEXT
        CATMULLROM_TEXT = CATMULLROM_TEXT
        LAGRANGE_TEXT = LAGRANGE_TEXT
        LANCZOS_TEXT = LANCZOS_TEXT
        
        @event.connect('b1.checked', 'b2.checked', 'b3.checked', 'b4.checked',
                       'b5.checked', 'b6.checked')
        def _set_spline_type(self, *events):
            ev = events[-1]
            self.spline.spline_type = ev.source.text
            type = self.spline.spline_type
            self.explanation.text = self[type.upper() + '_TEXT']
            if type == 'cardinal':
                self.tension.style = self.tension_label.style = 'visibility: visible'
            else:
                self.tension.style = self.tension_label.style = 'visibility: hidden'
        
        @event.connect('tension.value')
        def _set_tension(self, *events):
            t = self.tension.value
            self.tension_label.text = 'Tension: ' + t
            self.spline.tension = t
        
        @event.connect('closed.checked')
        def _set_closed(self, *events):
            self.spline.closed = self.closed.checked


if __name__ == '__main__':
    m = app.launch(Splines)
    app.start()
