""" Namespace for all widgets (that are not layouts).
"""

# flake8: noqa

from .. import Widget

from ._button import BaseButton, Button, ToggleButton, RadioButton, CheckBox
from ._slider import Slider
from ._tree import TreeWidget, TreeItem
from ._dropdown import ComboBox, DropdownContainer
from ._lineedit import LineEdit
from ._label import Label
from ._group import GroupWidget
from ._progressbar import ProgressBar
from ._plotwidget import PlotWidget
from ._iframe import IFrame
from ._bokeh import BokehWidget
from ._canvas import CanvasWidget
from ._color import ColorSelectWidget
from ._media import ImageWidget, VideoWidget, YoutubeWidget
from ._html import Div, html
