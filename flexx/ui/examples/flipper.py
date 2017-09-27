"""
This app demonstrates a phenomenon in the current implementation of Flexx
that we've referred to as "property flickering" (flipperen in Dutch). This
occurs when a synced property is repeatedly set from Python. The effect gets
stronger as Python and/or JS are busier.

In the examples below, pushing the button will add an element to a list
property. When "one-way mode" is turned on, Python will instead send
an event to JS, and the adding to the list happens there, causing the
traffic to be one-directional. This emulates the behavior after the Flexx
refactoring (actions can be invoked from Python, but mutations only happen in
JS).

"""

from time import time, sleep

from flexx import app, ui, event



class FlipperTester(ui.Widget):
    """ Widget to test the two flipper tests in a single app, and allow switching
    one-way mode.
    """
    
    def init(self):
        
        with ui.VBox():
            with ui.HBox():
                ui.Widget(flex=1)
                self._one_way_check = ui.CheckBox(text='One-way mode', checked=False)
                ui.Widget(flex=1)
            
            ui.Label(text=__doc__.replace('\n\n', '<br><br>'), wrap=1)
            
            with ui.HBoxPanel(flex=1, spacing=20):
                self.flipper1 = FlipperTest1()
                self.flipper2 = FlipperTest2()
            
    @event.connect('_one_way_check.checked')
    def set_one_way(self, *events):
        one_way = self._one_way_check.checked
        self.flipper1.one_way_mode = one_way
        self.flipper2.one_way_mode = one_way


class BaseFlipper(ui.Widget):
    """ Base flipper widget class.
    """
    
    def init(self):
        
        self._counter = 0
        
        with ui.FormLayout():
            ui.Label(text=self.__class__.__doc__, wrap=1)
            with ui.HBox(title=''):
                self._reset_but = ui.Button(flex=1, text='Reset')
                self._add_but = ui.Button(flex=1, text='Add item')
                self._add8_but = ui.Button(flex=1, text='Simulate 8 fast clicks')
            with ui.HBox(title='Py&nbsp;busyness'):
                self._slider = ui.Slider(flex=1, min=0, max=2, value=0.5)
                self._slider_label = ui.Label(flex=0)
            self._status_py = ui.Label(title='status py')
            # self._status_js = ui.Label(title='status js')
            self._items_py = ui.Label(title='items, seen from Py', wrap=1)
            self._items_js = ui.Label(title='items, seen from JS', wrap=1)
            
            ui.Widget(flex=1)  # spacer
    
    @event.connect('_slider.value')
    def on_slider_change(self, *events):
        self._slider_label.text = f'{self._slider.value} s'
    
    @event.connect('_reset_but.mouse_click')
    def on_reset_items(self, *events):
        self._counter = 0
        self.items = []
    
    @event.connect('_add_but.mouse_click')
    def on_add_item_py(self, *events):
        for ev in events:
            self._counter += 1
            item = f'{self._counter}'
            if self.one_way_mode:
                self.emit('add_an_item', dict(item=item))
            else:
                self.items = list(self.items) + [item]
    
    @event.prop
    def one_way_mode(self, v=False):
        return bool(v)
    
    class Both:
        
        @event.prop
        def items(self, items=[]):
            return tuple(items)
    
    class JS:
        
        @event.connect('!add_an_item')
        def add_item_in_js(self, *events):
            for ev in events:
                self.items = list(self.items) + [ev.item]
        
        @event.connect('_add8_but.mouse_click')
        def on_add8_items(self, *events):
            for ev in events:
                for i in range(8):
                    etime = time() + 0.1
                    while time() < etime:
                        pass
                    self._add_but.emit('mouse_click', {})


class FlipperTest1(BaseFlipper):
    """ This example updates the text of the string for each event.
    The flickering is very apparent here.
    """
    
    @event.connect('items')
    def on_items_py(self, *events):
        
        for ev in events:
            self._status_py.text = 'working ...'
            sleep(self._slider.value)
            self._status_py.text = ''
            self._items_py.text = ', '.join(ev.new_value)
    
    class JS:
        
        @event.connect('items')
        def on_items(self, *events):
            etime = time() + self._slider.value
            while time() < etime:
                pass
            for ev in events:
                self._items_js.text = ', '.join(ev.new_value)


class FlipperTest2(BaseFlipper):
    """ This example updates the text of the string in batches, i.e. only
    for the last element in *events. The effect is less apparent, but still
    visible, especially if the app is busier.
    """
    
    @event.connect('items')
    def on_items_py(self, *events):
        
        self._status_py.text = 'working ...'
        sleep(self._slider.value)
        self._status_py.text = ''
        self._items_py.text = ', '.join(self.items)
    
    class JS:
        
        @event.connect('items')
        def on_items(self, *events):
            etime = time() + self._slider.value
            while time() < etime:
                pass
            self._items_js.text = ', '.join(self.items)


m = app.App(FlipperTester).launch(size=(1000, 500))
