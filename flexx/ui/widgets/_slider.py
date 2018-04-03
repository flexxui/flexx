"""

Simple example:

.. UIExample:: 50

    s = ui.Slider(min=10, max=20, value=12)


Also see examples: :ref:`sine.py`, :ref:`twente.py`,
:ref:`deep_event_connections.py`.

"""

from ... import event
from .._widget import Widget, create_element


class Slider(Widget):
    """ An input widget to select a value in a certain range (aka HTML
    range input).
    """
    
    CSS = """
    
    .flx-Slider {
        min-height: 20px;
        min-width: 40px;
    }
    .flx-Slider:focus {
        outline: none;
    }
    
    .flx-Slider > .gutter {
        box-sizing: border-box;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        
        margin: 0 5px; /* half width of slider */
        position: absolute;
        top: calc(50% - 2px);
        height: 4px;
        width: calc(100% - 10px);
        border-radius: 6px;
        background: rgba(0, 0, 0, 0.2);
        color: rgba(0,0,0,0);
        text-align: center;
        transition: height 0.2s, top 0.2s;
    }
    .flx-Slider.flx-dragging > .gutter, .flx-Slider:focus > .gutter {
        top: calc(50% - 10px);
        height: 20px;
        color: rgba(0,0,0,1);
    }
    
    .flx-Slider .slider {
        box-sizing: border-box;
        text-align: center;
        border-radius: 3px;
        background: #48c;
        border: 2px solid #48c;
        transition: top 0.2s, height 0.2s, background 0.4s;
        position: absolute;
        top: calc(50% - 8px);
        height: 16px;
        width: 10px;
        }
    .flx-Slider.flx-dragging .slider, .flx-Slider:focus .slider {
        background: none;
        top: calc(50% - 10px);
        height: 20px;
    }
    .flx-Slider > .gutter > .slider.disabled {
        background: #888;
        border: none;
    }
    """
    
    step = event.FloatProp(0.01, settable=True, doc="""
        The step size for the slider.
        """)
    
    min = event.FloatProp(0, settable=True, doc="""
        The minimal slider value.
        """)
    
    max = event.FloatProp(1, settable=True, doc="""
        The maximum slider value.
        """)
    
    value = event.FloatProp(0, settable=True, doc="""
        The current slider value.
        """)
    
    text = event.StringProp('{value}', settable=True, doc="""
        The label to display on the slider during dragging. Occurances of
        "{percent}" are replaced with the current percentage, and
        "{value}" with the current value. Default "{value}".
        """)
    
    disabled = event.BoolProp(False, settable=True, doc="""
        Whether the slider is disabled.
        """)
    
    def init(self):
        self._dragging = None
    
    @event.emitter
    def user_value(self, value):
        """ Event emitted when the user manipulates the slider.
        Has ``old_value`` and ``new_value`` attributes.
        """
        d = {'old_value': self.value, 'new_value': value}
        self.set_value(value)
        return d
    
    @event.emitter
    def user_done(self):
        """ Event emitted when the user stops manipulating the slider. Has
        ``old_value`` and ``new_value`` attributes (which have the same value).
        """
        d = {'old_value': self.value, 'new_value': self.value}
        return d
    
    @event.action
    def set_value(self, value):
        global Math
        value = max(self.min, value)
        value = min(self.max, value)
        value = Math.round(value / self.step) * self.step
        self._mutate_value(value)
    
    @event.reaction('min', 'max', 'step')
    def __keep_value_constrained(self, *events):
        self.set_value(self.value)
    
    def _render_dom(self):
        global Math
        value = self.value
        mi, ma = self.min, self.max
        perc = 100 * (value - mi) / (ma - mi)
        valuestr = str(value)
        if '.' in valuestr and valuestr[-4:-1] == '000':
            valuestr = valuestr[:-1].rstrip('0')
        label = self.text
        label = label.replace('{value}', valuestr)
        label = label.replace('{percent}', Math.round(perc) + '%')
        
        attr = {'className': 'slider disabled' if self.disabled else 'slider',
                'style__left': 'calc(' + perc + '% - 5px)'
                }
        return [create_element('div', {'className': 'gutter'},
                    create_element('span', {}, label),
                    create_element('div', attr),
                    )
                ]
    
    # Use the Flexx mouse event system, so we can make use of capturing ...
    
    @event.emitter
    def mouse_down(self, e):
        if not self.disabled:
            e.stopPropagation()
            x1 = e.clientX
            if not e.target.classList.contains("slider"):
                x1 = (self.node.getBoundingClientRect().x +
                      self.node.children[0].children[1].offsetLeft)
            self._dragging = self.value, x1
            self.outernode.classList.add('flx-dragging')
        else:
            return super().mouse_down(e)
    
    @event.emitter
    def mouse_up(self, e):
        if self._dragging is not None and len(self._dragging) == 3:
            self.outernode.blur()
        self._dragging = None
        self.outernode.classList.remove('flx-dragging')
        self.user_done()
        return super().mouse_down(e)
    
    @event.emitter
    def mouse_move(self, e):
        if self._dragging is not None:
            e.stopPropagation()
            ref_value, x1 = self._dragging[0], self._dragging[1]
            self._dragging = ref_value, x1, True  # mark as moved
            x2 = e.clientX
            mi, ma = self.min, self.max
            value_diff = (x2 - x1) / self.outernode.clientWidth * (ma - mi)
            self.user_value(ref_value + value_diff)
        else:
            return super().mouse_move(e)
    
    @event.reaction('key_down')
    def __on_key(self, *events):
        for ev in events:
            if ev.key == 'Escape':
                self.outernode.blur()
                self.user_done()
            elif ev.key == 'ArrowRight':
                self.user_value(self.value + self.step)
            elif ev.key == 'ArrowLeft':
                self.user_value(self.value - self.step)
