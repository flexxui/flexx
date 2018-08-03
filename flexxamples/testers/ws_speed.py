"""
This little app runs some speed tests by sending binary data over the
websocket (from JS to Py and back), and measuring the time it costs to
do this.

Note that the data is buffered by the websocket (and to some extend in Flexx'
event system), so when multiple messages are send in quick succession, the
last message appears to take a relatively long time.

Also note that when sending singular messages, you also measure the time
of some of Flexx' event loop iterations (on both ends).

Websockets apparently limit the size of messages to somewhere between
5 and 10 MiB. Perhaps Flexx should chunk long messages.

On my machine, with Firefox, it takes about 1.4 seconds to send 100 MiB
messages to Python and back.
"""

from flexx import app, event, ui


class SpeedTest(app.PyComponent):

    def init(self):
        self.widget = SpeedTestWidget(self)

    @event.action
    def echo(self, data):
        self.widget.receive_data(data)


class SpeedTestWidget(ui.Widget):

    def init(self, pycomp):
        self.pycomp = pycomp
        self._start_time = 0
        self._start_times = []

        with ui.VBox():
            with ui.HBox() as self.buttons:
                ui.Button(text='1 x 1 MiB roundtrip')
                ui.Button(text='1 x 5 MiB roundtrip')
                ui.Button(text='10 x 1 MiB roundtrip')
                ui.Button(text='10 x 5 MiB roundtrip')
                ui.Button(text='100 x 1 MiB roundtrip')
                ui.Button(text='100 x 5 MiB roundtrip')
            self.progress = ui.ProgressBar()
            self.status = ui.Label(text='Status: waiting for button press ...',
                                   wrap=1, flex=1, style='overflow-y:scroll;')


    @event.reaction('buttons.children*.pointer_down')
    def run_test(self, *events):
        global window, perf_counter
        self.status.set_text('Test results: ')
        self.progress.set_value(0)

        tests = []
        for ev in events:
            if isinstance(ev.source, ui.Button):
                sze = 5 if '5' in ev.source.text else 1
                n = int(ev.source.text.split(' ')[0])
                for i in range(n):
                    tests.append(sze)

        self.progress.set_max(len(tests))
        self._start_time = perf_counter()
        for n in tests:
            data = window.Uint8Array(n * 1024 * 1024).buffer
            self.send_data(data)

    @event.action
    def send_data(self, data):
        global perf_counter
        self._start_times.append(perf_counter())
        self.pycomp.echo(data)

    @event.action
    def receive_data(self, data):
        global perf_counter
        t = perf_counter() - self._start_times.pop(0)
        mib = data.byteLength / 1024 / 1024
        text = 'Received %i MiB in %s seconds.' % (mib, str(t)[:5])
        self.status.set_html(self.status.html + '  ' + text)
        self.progress.set_value(self.progress.value + 1)

        if len(self._start_times) == 0:
            t = perf_counter() - self._start_time
            text = 'Total time %s.' % str(t)[:5]
            self.status.set_html(self.status.html + '  ' + text)


if __name__ == '__main__':
    m = app.launch(SpeedTest, 'firefox-browser')
    app.run()
