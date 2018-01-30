# doc-export: BokehExample
""" 
Example demonstrating a Bokeh plot in Flexx. Includes client-side
interaction with sliders.
"""

import numpy as np

from bokeh.plotting import figure

from flexx import app, event, ui
from flexx.pyscript import window

# Plot 1
N = 1000
x = np.random.normal(0, np.pi, N)
y = np.sin(x) + np.random.normal(0, 0.2, N)
TOOLS = "pan,wheel_zoom,box_zoom,reset,box_select"
p1 = figure(tools=TOOLS)
p1.scatter(x, y, alpha=0.1, nonselection_alpha=0.1)

# Plot2
t = np.linspace(0, 6.5, 100)
p2 = figure(tools=TOOLS, sizing_mode='scale_width')
p2.line(t, np.sin(t))
p3 = figure(tools=TOOLS, sizing_mode='scale_width')
p3.line(t, np.cos(t))


class BokehExample(app.PyComponent):
    
    def init(self):
        
        with ui.HSplit(style='min-height:300px') as self.widget:
            self.plot1 = ui.BokehWidget.from_plot(p1, title='Scatter')
            with ui.VFix(title='Sine'):
                Controls()
                with ui.Widget(style='overflow-y:auto;', flex=1):
                    self.plot2 = ui.BokehWidget.from_plot(p2)
                    self.plot3 = ui.BokehWidget.from_plot(p3)
        

class Controls(ui.FormLayout):
    
    def init(self):
        self.amp = ui.Slider(title='Amplitude', max=2, value=1)
        self.freq = ui.Slider(title='Frequency', max=10, value=5)
        self.phase = ui.Slider(title='Phase', max=3, value=1)
        
        
    @event.reaction
    def _update_sine(self):
        amp, freq, phase = self.amp.value, self.freq.value, self.phase.value
        # Get reference to data source
        ds = None
        plot2 = self.parent.children[1].children[0]
        plot = plot2.plot
        if plot:
            for ren in plot.model.renderers.values():
                if ren.data_source:
                    ds = ren.data_source
                    break
        
        # Update
        if ds:
            window.plot = plot
            ds.data.y = [amp*window.Math.sin(x*freq+phase) for x in ds.data.x]
            ds.change.emit()  # or trigger('change') in older versions


if __name__ == '__main__':
    m = app.launch(BokehExample, 'app')
    app.start()
