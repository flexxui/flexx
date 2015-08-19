""" flexx.ui

GUI toolkit based on web technology with a Pythonic API.
"""

# We follow the convention of having one module per widget class (or a
# small set of closely related classes). In order not to pollute this
# namespace, we prefix the module names with an underscrore.

from ._widget import Widget

from ._layout import Layout
from ._box import Box, HBox, VBox
from ._splitter import Splitter, HSplitter, VSplitter
from ._formlayout import BaseTableLayout, FormLayout, GridLayout
from ._pinboardlayout import PinboardLayout

from ._button import Button
from ._slider import Slider
from ._lineedit import LineEdit

from ._label import Label
from ._panel import Panel
from ._progressbar import ProgressBar

from ._plotwidget import PlotWidget
from ._plotlayout import PlotLayout
