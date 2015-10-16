""" 
Example demonstrating a Bokeh plot in Flexx, using a Phosphor dock panel
layout. Includes client-side interaction with sliders.
"""

import numpy as np

from bokeh.plotting import figure, show, output_file
from bokeh.embed import file_html, components

from flexx import app, ui, react

src = 'https://github.com/zoofIO/flexx/blob/master/examples/ui/bokeh_plot.py'

# Plot 1
N = 1000
x = np.random.normal(0, np.pi, N)
y = np.sin(x) + np.random.normal(0, 0.2, N)
TOOLS = "pan,wheel_zoom,box_zoom,reset,box_select"
p1 = figure(tools=TOOLS, webgl=True)
p1.scatter(x,y, alpha=0.1, nonselection_alpha=0.01)

# Plot2
t = np.linspace(0, 6.5, 100)
p2 = figure(tools=TOOLS)
p2.line(t, np.sin(t))
p3 = figure(tools=TOOLS)
p3.line(t, np.cos(t))

class Example(ui.Widget):
    
    def init(self):
        
        with ui.DockPanel():
            self.plot1 = ui.BokehWidget(plot=p1, title='Scatter')
            with ui.VBox(title='Sine'):
                with ui.FormLayout():
                    self.amp = ui.Slider(title='Amplitude', max=2, value=1)
                    self.freq = ui.Slider(title='Frequency', max=10, value=5)
                    self.phase = ui.Slider(title='Phase',max=3, value=1)
                with ui.Widget(style='overflow-y:auto;', flex=1):
                    self.plot2 = ui.BokehWidget(plot=p2)
                    self.plot3 = ui.BokehWidget(plot=p3)
            # Add some colorful panels just for fun
            ui.Label(title='Info', text='Source is <a href="%s">%s</a>' % (src, src))
            ui.Widget(style='background:#0a0;', title='green')
            ui.Widget(style='background:#00a;', title='blue')
    
    class JS:
        
        @react.connect('amp.value', 'freq.value', 'phase.value')
        def _update_sine(self, amp, freq, phase):
            # Get reference to line glyph, can this be done easier?
            glyph = None
            plot = self.plot2.plot()
            if plot:
                for ren in plot.renderers.values():
                    if ren.glyph:
                        glyph = ren.glyph
                        break
            # Update
            if glyph:
                glyph.y = [amp*Math.sin(x*freq+phase) for x in glyph.x]
                plot.render()


if __name__ == '__main__':
    m = app.launch(Example)

