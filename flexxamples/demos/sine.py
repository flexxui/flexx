# doc-export: SineExample
"""
A sine, with sliders to manipulate phase and amplitude.
"""

from flexx import flx

class SineExample(flx.Widget):

    def init(self):
        time = [i/100 for i in range(100)]
        with flx.VBox():
            with flx.HBox():
                flx.Label(text='Frequency:')
                self.slider1 = flx.Slider(min=1, max=10, value=5, flex=1)
                flx.Label(text='Phase:')
                self.slider2 = flx.Slider(min=0, max=6, value=0, flex=1)
            self.plot = flx.PlotWidget(flex=1, xdata=time, xlabel='time',
                                       ylabel='amplitude', title='a sinusoid')

    @flx.reaction
    def __update_amplitude(self, *events):
        global Math
        freq, phase = self.slider1.value, self.slider2.value
        ydata = []
        for x in self.plot.xdata:
            ydata.append(Math.sin(freq*x*2*Math.PI+phase))
        self.plot.set_data(self.plot.xdata, ydata)


if __name__ == '__main__':
    m = flx.launch(SineExample)
    flx.run()
