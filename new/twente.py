from flexx import app, ui

# Raw data obtained from 
# http://www.knmi.nl/klimatologie/maandgegevens/datafiles/mndgeg_290_tg.txt

raw_data = """ ... """

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 
          'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'total']

def parse_data(raw_data):
    years, data = [], [[] for i in range(13)]
    for line in raw_data.splitlines():
        if line.startswith('290'):
            parts = [int(i.strip()) for i in line.split(',')]
            years.append(parts[1])
            for i in range(13):
                data[i].append(parts[i+2]/10.0)
    return years, data

years, data = parse_data(raw_data)


class Twente(app.Model):
    """ This model represents the application state and provides two actions
    to update the state.
    """
    
    class State:
    
        month = app.int_prop(0, settable=int, doc="The selected month.")
        smoothing = app.int_prop(5, settable=int, doc="The amount of smoothing to apply.")
    
    class JS:
        
        def init(self):
            # All this widget stuff only lives in JS, the only thing that the server
            # can touch/see is the state that we expose.
             
            with ui.HBox(title='Temperature app', icon='') as self.view:
                ui.Widget(flex=1)
                with ui.VBox(flex=0):
                    with ui.GroupWidget(title='Plot options'):
                        with ui.VBox():
                            self.month_label = ui.Label(text='Month')
                            ui.Slider(max=12, step=1, value=12,
                                      on_value=lambda ev: self.set_month(ev.new_value))
                            self.smoothing_label = ui.Label(text='Smoothing')
                            ui.Slider(max=20, step=2,
                                      on_value=lambda ev: self.set_smoothing(ev.new_value))
                    ui.Widget(flex=1)
                with ui.VBox(flex=4):
                    self.plot = ui.PlotWidget(flex=1,
                                                xdata=years, yrange=(-5, 20),
                                                title='Average monthly temperature',
                                                xlabel='year', ylabel=u'temperature (°C)')
                    # ui.Widget(flex=0, style='height:30px')
                ui.Widget(flex=1)
            
            # One-line connection
            self.month_slider.connect('value', lambda e: self.root.emit('set_month', dict(value=e.new_value)))
        
        @appp.reaction
        def _update_plot(self):
            
            # This would be the "easy way", in case we'd keep the state local
            #month = self.month_slider.value
            #smoothing = self.smoothing_slider.value
            
            # But we use the "scalabale way", letting the view dispatch actions
            # that update application state, to which we react by updating
            # the view.
            month = self.root.month
            smoothing = self.root.smoothing
            
            # Invoke actions to update labels
            self.month_label.set_text('Month (%s)' % months[month])
            self.smoothing_label.set_text('Smoothing (%i)' % smoothing)
            
            yy1 = data[month]
            yy2 = []
            
            sm2 = int(smoothing / 2)
            for i in range(len(yy1)):
                val = 0
                n = 0
                for j in range(max(0, i-sm2), min(len(yy1), i+sm2+1)):
                    val += yy1[j]
                    n += 1
                if n == 0:
                    yy2.append(yy1[i])
                else:
                    yy2.append(val / n)
            
            self.plot.set_ydata(yy2)


if __name__ == '__main__':
    m = app.launch(Twente, runtime='app', title='Temperature 1951 - 2014',
                   size=(900, 400))
    m.style = 'background:#eee;'  # more desktop-like
    app.run()
