""" flexx.ui

GUI toolkit based on web technology with a Pythonic API.
"""

from ..app import run, stop, call_later, make_app
from ..app import Pair, get_instance_by_id

# We follow the convention of having one module per widget class. In
# order not to pollute this namespace, we prefix the module names with
# an underscrore.

from ._widget import Widget
from ._label import Label
from ._button import Button
from ._layout import Layout, Box, HBox, VBox
from ._layout import BaseTableLayout, FormLayout, GridLayout
from ._layout import Splitter, HSplitter, VSplitter
from ._layout import PinboardLayout
from ._progressbar import ProgressBar
from ._layout2 import Panel, PlotWidget, PlotLayout
