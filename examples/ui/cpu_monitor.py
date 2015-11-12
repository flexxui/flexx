"""
Simple web app to monitor the CPU usage of the server process.

Requires psutil
"""

import os
import time
import psutil

from flexx import app, ui, react

nsamples = 16


@react.source
def global_cpu_usage(usage):
    return float(usage)

@react.source
def global_mem_usage(usage):
    return float(usage)

def refresh():
    global_cpu_usage._set(psutil.cpu_percent())
    global_mem_usage._set(psutil.virtual_memory().percent)
    app.call_later(1, refresh)

refresh()


@app.serve
class CPUMonitor(ui.Widget):
    
    def init(self):
        with ui.HBox():
            with ui.VBox():
                ui.Label(text='<h3>Server monitor</h3>')
                self.info = ui.Label(text='...')
                if os.getenv('FLEXX_HOSTNAME', 'localhost') == 'localhost':
                    self.button = ui.Button(text='Do some work')
                
                self.cpu_plot = ui.PlotWidget(style='width: 640px; height: 320px;',
                                              xdata=[], yrange=(0, 100), 
                                              ylabel='CPU usage (%)')
                self.mem_plot = ui.PlotWidget(style='width: 640px; height: 320px;',
                                              xdata=[], yrange=(0, 100), 
                                              ylabel='Mem usage (%)')
                ui.Widget(flex=1)
    
    @react.connect('global_cpu_usage')
    def cpu_usage(self, v):
        return float(v)
    
    @react.connect('global_mem_usage')
    def mem_usage(self, v):
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
        return n, app.manager.total_sessions
    
    class JS:
        cpu_count = psutil.cpu_count()
        nsamples = nsamples
        
        def _init(self):
            super()._init()
            import time
            self.start_time = time.time()
        
        @react.connect('number_of_connections')
        def _update_info(self, n):
            self.info.text('There are %i connected clients.<br />' % n[0] +
                           'And in total we served %i connections.<br />' % n[1])
        
        @react.connect('cpu_usage')
        def _update_cpu_usage(self, v):
            import time
            times = self.cpu_plot.xdata()
            usage = self.cpu_plot.ydata()
            times.append(time.time() - self.start_time)
            usage.append(v)
            times = times[-self.nsamples:]
            usage = usage[-self.nsamples:]
            self.cpu_plot.xdata(times)
            self.cpu_plot.ydata(usage)
        
        @react.connect('mem_usage')
        def _update_mem_usage(self, v):
            import time
            times = self.mem_plot.xdata()
            usage = self.mem_plot.ydata()
            times.append(time.time() - self.start_time)
            usage.append(v)
            times = times[-self.nsamples:]
            usage = usage[-self.nsamples:]
            self.mem_plot.xdata(times)
            self.mem_plot.ydata(usage)


if __name__ == '__main__':
    # m = app.launch(CPUMonitor)  # for use during development
    app.start()
