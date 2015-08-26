"""
Simple web app to monitor the CPU usage of the server process.

Requires psutil
"""

import time
import psutil

from flexx import app, ui, react

nsamples = 16


@react.source
def global_cpu_usage(usage):
    return float(usage)
    
def refresh():
    global_cpu_usage._set(psutil.cpu_percent())
    app.call_later(1, refresh)

refresh()


@app.serve
class CPUMonitor(ui.Widget):
    
    def init(self):
        with ui.HBox():
            with ui.VBox():
                ui.Label(text='<h3>Server monitor</h3>')
                self.info = ui.Label(text='...')
                self.button = ui.Button(text='Do some work')
                
                self.plot = ui.PlotWidget(size=(640, 480), xdata=[0], 
                                          yrange=(0, 100), ylabel='CPU usage (%)')
                ui.Widget(flex=1)
    
    @react.connect('global_cpu_usage')
    def cpu_usage(self, v):
        return float(v)
    
    @react.connect('button.mouse_down')
    def _do_work(self, down):
        if down:
            etime = time.time() + 1.0
            while time.time() < etime:
                pass
    
    @react.connect('app.manager.connections_changed')
    def number_of_connections(name):
        n = 0
        for name in app.manager.get_app_names():
            proxies = app.manager.get_connections(name)
            n += len(proxies)
        return n
    
    class JS:
        cpu_count = psutil.cpu_count()
        nsamples = nsamples
        start_time = time.time()
        
        @react.connect('number_of_connections')
        def _update_info(self, n):
            self.info.text('There are %i connected clients.<br />' % n)
        
        @react.connect('cpu_usage')
        def _update_usage(self, v):
            times = self.plot.xdata()
            usage = self.plot.ydata()
            times.append(time.time() - self.start_time)
            usage.append(v)
            times = times[-self.nsamples:]
            usage = usage[-self.nsamples:]
            self.plot.xdata(times)
            self.plot.ydata(usage)


if __name__ == '__main__':
    # m = app.launch(CPUMonitor)  # for use during development
    app.start()
