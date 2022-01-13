# Following line may be needed for step by step debugging into threads
# from gevent import monkey; monkey.patch_all()  # do it before modules like requests gets imported

from flexx import flx
from flexx import event

import threading
import asyncio


class PyWidget1(flx.PyWidget):
    frame = None

    def init(self, additional_style="width: 100%; height: 100%;"):
        with flx.VFix(flex=1, style=additional_style) as self.frame:
            with flx.VFix(flex=1) as self.page:
                self.custom = flx.VFix(flex=1, style="width: 100%; height: 100%; border: 5px solid green;")
                with flx.HFix(flex=1):
                    self.but = flx.Button(text="Replace by PyWidget2")
                    self.but_close = flx.Button(text="Close")
                self.input = flx.LineEdit(text="input")

    def dispose(self):
        self.frame.dispose()
        self.frame = None
        super().dispose()

    @flx.reaction("but.pointer_click")
    def delete_function(self, *events):
        self.parent.remove(self.dyn_id)
        self.parent.instantiate(PyWidget2)

    @flx.reaction("but_close.pointer_click")
    def close_function(self, *events):
        self.parent.remove(self.dyn_id)


class PyWidget2(flx.PyWidget):
    frame = None

    def init(self, additional_style="width: 100%; height: 100%;"):
        with flx.VFix(flex=1, style=additional_style) as self.frame:
            with flx.VFix(flex=1) as self.page:
                self.custom = flx.VFix(flex=1, style="width: 100%; height: 100%; border: 5px solid blue;")
                self.but = flx.Button(text="Swap back to a PyWidget1")

    def dispose(self):
        self.frame.dispose()
        self.frame = None
        super().dispose()

    @flx.reaction("but.pointer_click")
    def delete_function(self, *events):
        self.parent.remove(self.dyn_id)
        self.parent.instantiate(PyWidget1)


class Example(flx.PyWidget):

    # The CSS is not used by flex in PyWiget but it should be applied to the top div: TODO
    CSS = """
    .flx-DynamicWidgetContainer {
        white-space: nowrap;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        color: #333;
    }
    """

    def init(self):
        with flx.VFix(flex=1) as self.frame_layout:
            self.dynamic = flx.DynamicWidgetContainer(
                style="width: 100%; height: 100%; border: 5px solid black;", flex=1
            )
            self.but = flx.Button(text="Instanciate a PyWidget1 in the dynamic container")

    @flx.reaction("but.pointer_click")
    def click(self, *events):
        self.dynamic.instantiate(PyWidget1)


flexx_app = threading.Event()
flexx_thread = None


def start_flexx_app():
    """
    Starts the flexx thread that manages the flexx asyncio worker loop.
    """

    flexx_loop = asyncio.new_event_loop()  # assign the loop to the manager so it can be accessed later.

    def flexx_run(loop):
        """
        Function to start a thread containing the main loop of flexx.
        """
        global flexx_app
        asyncio.set_event_loop(loop)

        event = flexx_app  # flexx_app was initialized with an Event()
        flexx_app = flx.launch(Example, loop=loop)
        event.set()
        flx.run()

    global flexx_thread
    flexx_thread = threading.Thread(target=flexx_run, args=(flexx_loop,))
    flexx_thread.daemon = True
    flexx_thread.start()


start_flexx_app()
app = flexx_app
if isinstance(app, threading.Event):  # check if app was instanciated
    app.wait()  # wait for instanciation
# At this point flexx_app contains the Example application
pos = flexx_app.dynamic.instantiate(PyWidget1)
instance = flexx_app.dynamic.get_instance(pos)
instance.but.set_text("it worked")
# instance.dyn_stop_event.wait()  # This waits for the instance to be removed
flexx_thread.join()  # Wait for the flexx event loop to terminate.
print(instance.input.text)
