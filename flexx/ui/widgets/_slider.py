"""

Simple example:

.. UIExample:: 70

    with flx.VBox():
        flx.Slider(min=10, max=20, value=12)
        flx.RangeSlider(min=10, max=90, value=(20, 60))

Also see examples: :ref:`sine.py`, :ref:`twente.py`,
:ref:`deep_event_connections.py`.

"""

from ... import event
from .._widget import Widget, create_element


class Slider(Widget):
    """ An input widget to select a value in a certain range.

    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_
    containing a few HTML elements for rendering. It does not use
    a ``<input type='range'>`` because of its different appearance and
    behaviour accross browsers.
    """

    DEFAULT_MIN_SIZE = 40, 20

    CSS = """

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
        transition: top 0.2s, height 0.2s;
    }
    .flx-Slider.flx-dragging > .gutter, .flx-Slider:focus > .gutter {
        top: calc(50% - 10px);
        height: 20px;
        color: rgba(0,0,0,1);
    }

    .flx-Slider .slider, .flx-Slider .range {
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
    .flx-Slider .range {
        border-width: 1px 0px 1px 0px;
        top: calc(50% - 4px);
        height: 8px;
        width: auto;
    }
    .flx-Slider.flx-dragging .slider, .flx-Slider:focus .slider,
    .flx-Slider.flx-dragging .range, .flx-Slider:focus .range {
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
        self._drag_target = 0

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

    # Use the Flexx pointer event system, so we can make use of capturing ...

    def _getgutter(self):
        return self.node.children[0]

    def _snap2handle(self, x):
        # Snap to the slider handle
        gutter = self._getgutter()
        left = gutter.getBoundingClientRect().left + gutter.children[1].offsetLeft
        if left <= x <= left + 10:
            return x
        else:
            return left + 5  # center of the slider handle

    @event.emitter
    def pointer_down(self, e):
        if not self.disabled:
            e.stopPropagation()
            x1 = e.changedTouches[0].clientX if e.changedTouches else e.clientX
            x1 = self._snap2handle(x1)
            self._dragging = self.value, x1
            self.outernode.classList.add('flx-dragging')
        else:
            return super().pointer_down(e)

    @event.emitter
    def pointer_up(self, e):
        if self._dragging is not None and len(self._dragging) == 3:
            self.outernode.blur()
        self._dragging = None
        self._drag_target = 0
        self.outernode.classList.remove('flx-dragging')
        self.user_done()
        return super().pointer_down(e)

    @event.emitter
    def pointer_move(self, e):
        if self._dragging is not None:
            e.stopPropagation()
            ref_value, x1 = self._dragging[0], self._dragging[1]
            self._dragging = ref_value, x1, True  # mark as moved
            x2 = e.changedTouches[0].clientX if e.changedTouches else e.clientX
            mi, ma = self.min, self.max
            value_diff = (x2 - x1) / self._getgutter().clientWidth * (ma - mi)
            self.user_value(ref_value + value_diff)
        else:
            return super().pointer_move(e)

    @event.reaction('key_down')
    def __on_key(self, *events):
        for ev in events:
            value = self.value
            if ev.key == 'Escape':
                self.outernode.blur()
                self.user_done()
            elif ev.key == 'ArrowRight':
                if isinstance(value, float):
                    self.user_value(value + self.step)
                else:
                    self.user_value([v + self.step for v in value])
            elif ev.key == 'ArrowLeft':
                if isinstance(value, float):
                    self.user_value(value - self.step)
                else:
                    self.user_value([v - self.step for v in value])


class RangeSlider(Slider):
    """An input widget to select a range (i.e having two handles instead of one).

    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_
    containing a few HTML elements for rendering.
    """

    value = event.FloatPairProp((0, 1), settable=True, doc="""
        The current slider value as a two-tuple.
        """)

    @event.action
    def set_value(self, *value):
        """ Set the RangeSlider's value. Can be called using
        ``set_value([val1, val2])`` or ``set_value(val1, val2)``.
        """
        global Math
        if len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        assert len(value) == 2, 'RangeSlider value must be a 2-tuple.'
        value = min(value[0], value[1]), max(value[0], value[1])
        for i in range(2):
            value[i] = max(self.min, value[i])
            value[i] = min(self.max, value[i])
            value[i] = Math.round(value[i] / self.step) * self.step
        self._mutate_value(value)

    def _render_dom(self):
        global Math
        value1, value2 = self.value
        mi, ma = self.min, self.max
        perc1 = 100 * (value1 - mi) / (ma - mi)
        perc2 = 100 * (value2 - mi) / (ma - mi)
        valuestr1 = str(value1)
        valuestr2 = str(value2)
        if '.' in valuestr1 and valuestr1[-4:-1] == '000':
            valuestr1 = valuestr1[:-1].rstrip('0')
        elif '.' in valuestr2 and valuestr2[-4:-1] == '000':
            valuestr2 = valuestr2[:-1].rstrip('0')
        label = self.text
        label = label.replace('{value}', valuestr1 + ' - ' + valuestr2)
        label = label.replace('{percent}',
                              Math.round(perc1) + '% - ' + Math.round(perc2) + '%')

        attr0 = {'className': 'range',
                'style__left': perc1 + '%',
                'style__right': (100 - perc2) + '%'
                }
        attr1 = {'className': 'slider disabled' if self.disabled else 'slider',
                'style__left': 'calc(' + perc1 + '% - 5px)'
                }
        attr2 = {'className': 'slider disabled' if self.disabled else 'slider',
                'style__left': 'calc(' + perc2 + '% - 5px)'
                }
        return [create_element('div', {'className': 'gutter'},
                    create_element('span', {}, label),
                    create_element('div', attr0),
                    create_element('div', attr1),
                    create_element('div', attr2),
                    )
                ]

    def _snap2handle(self, x):
        # Snap to a slider handle or the center
        gutter = self._getgutter()
        h1 = gutter.getBoundingClientRect().left + gutter.children[2].offsetLeft + 5
        h2 = gutter.getBoundingClientRect().left + gutter.children[3].offsetLeft + 5
        hc = 0.5 * (h1 + h2)
        # Distances
        d1, d2, dc = abs(x - h1), abs(x - h2), abs(x - hc)
        # Decide
        if dc < d1 and dc < d2:
            self._drag_target = 3
            return x
        elif d1 < d2:
            self._drag_target = 1
            return h1
        else:
            self._drag_target = 2
            return h2

    @event.emitter
    def pointer_move(self, e):
        if self._dragging is not None:
            e.stopPropagation()
            ref_value, x1 = self._dragging[0], self._dragging[1]
            self._dragging = ref_value, x1, True  # mark as moved
            x2 = e.changedTouches[0].clientX if e.changedTouches else e.clientX
            mi, ma = self.min, self.max
            value_diff = (x2 - x1) / self._getgutter().clientWidth * (ma - mi)
            value1, value2 = ref_value
            if 1 & self._drag_target:
                value1 += value_diff
            if 2 & self._drag_target:
                value2 += value_diff
            self.user_value((value1, value2))
        else:
            return super().pointer_move(e)
