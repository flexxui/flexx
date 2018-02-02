"""
Simple web app to monitor the CPU and memory usage of the server process.
Requires psutil.

This app might be running at the demo server: http://flexx1.zoof.io
"""

from time import time
import psutil
import asyncio

from flexx import app, event, ui

nsamples = 16


class Relay(event.Component):
    
    number_of_connections = event.IntProp(settable=True)
    
    def init(self):
        self.update_number_of_connections()
        self.refresh()
    
    @app.manager.reaction('connections_changed')
    def update_number_of_connections(self, *events):
        n = 0
        for name in app.manager.get_app_names():
            sessions = app.manager.get_connections(name)
            n += len(sessions)
        self.set_number_of_connections(n)
    
    @event.emitter
    def system_info(self):
        return dict(cpu=psutil.cpu_percent(),
                    mem=psutil.virtual_memory().percent,
                    sessions=self.number_of_connections,
                    total_sessions=app.manager.total_sessions,
                    )
        
    def refresh(self):
        self.system_info()
        asyncio.get_event_loop().call_later(1, self.refresh)


# Create global relay
relay = Relay()


class Monitor(app.PyComponent):
    
    cpu_count = psutil.cpu_count()
    nsamples = nsamples
    
    def init(self):
        
        with ui.VBox():
            ui.Label(text='<h3>Server monitor</h3>')
            if app.current_server().serving[0] == 'localhost':
                # Don't do this for a public server
                self.button = ui.Button(text='Do some work')
            self.view = MonitorView(flex=1)
    
    @relay.reaction('system_info')  # note that we connect to relay
    def _push_info(self, *events):
        if not self.session.status:
            return relay.disconnect('system_info:' + self.id)
        for ev in events:
            self.view.update_info(dict(cpu=ev.cpu,
                                       mem=ev.mem,
                                       sessions=ev.sessions,
                                       total_sessions=ev.total_sessions))
    
    @event.reaction('!button.mouse_down')
    def _do_work(self, *events):
        etime = time() + len(events)
        # print('doing work for %i s' % len(events))
        while time() < etime:
            pass


class MonitorView(ui.VBox):
    
    def init(self):
        self.start_time = time()
        
        self.status = ui.Label(text='...')
        self.cpu_plot = ui.PlotWidget(flex=1, style='width: 640px; height: 320px;',
                                      xdata=[], yrange=(0, 100), 
                                      ylabel='CPU usage (%)')
        self.mem_plot = ui.PlotWidget(flex=1, style='width: 640px; height: 320px;',
                                      xdata=[], yrange=(0, 100), 
                                      ylabel='Mem usage (%)')
    
    @event.action
    def update_info(self, info):
        
        # Set connections
        n = info.sessions, info.total_sessions
        self.status.set_text('There are %i connected clients.<br />' % n[0] +
                             'And in total we served %i connections.<br />' % n[1])
        
        # Prepare plots
        times = list(self.cpu_plot.xdata)
        times.append(time() - self.start_time)
        times = times[-self.nsamples:]
        
        # cpu data
        usage = list(self.cpu_plot.ydata)
        usage.append(info.cpu)
        usage = usage[-self.nsamples:]
        self.cpu_plot.set_data(times, usage)
        
        # mem data
        usage = list(self.mem_plot.ydata)
        usage.append(info.mem)
        usage = usage[-self.nsamples:]
        self.mem_plot.set_data(times, usage)


if __name__ == '__main__':
    a = app.App(Monitor)
    a.serve()
    # m = a.launch('browser')  # for use during development
    app.start()
