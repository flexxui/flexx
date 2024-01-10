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


m = flx.launch(Example)
flx.run()