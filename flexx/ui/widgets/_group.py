"""
Simple example:

.. UIExample:: 100
    
    with ui.GroupWidget(title='This is a panel'):
        with ui.VBox():
            ui.ProgressBar(value=0.2)
            ui.Button(text='click me')


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, react
    
    class Example(ui.GroupWidget):
        def init(self):
            self.title('A silly panel')
            with ui.VBox():
                ui.ProgressBar(value=0.2)
                self.but = ui.Button(text='click me')
        
        class JS:
            @react.connect('but.mouse_down')
            def _change_group_title(self, down):
                if down:
                    self.title(self.title() + '-')

"""

from ... import react
from ...pyscript import window
from . import Widget


class GroupWidget(Widget):
    """ Widget to collect widgets in a named group. 
    
    It does not provide a layout. This is similar to a QGroupBox or an
    HTML fieldset.
    """
    
    class JS:
        
        def _create_node(self):
            # class FieldsetPanel(phosphor.widget.Panel):
            #     def createNode():
            #         return document.createElement('fieldset')
            # self.p = FieldsetPanel()
            
            # todo: make a createPanel function in phosphor all
            ori = window.phosphor.widget.Panel.createNode
            def _():
                return document.createElement('fieldset')
            window.phosphor.widget.Panel.createNode = _
            self.p = phosphor.widget.Panel()
            window.phosphor.widget.Panel.createNode = ori
            
            #self.p = phosphor.createWidget('fieldset')
            self._legend = document.createElement('legend')
            self.p.node.appendChild(self._legend)
        
        @react.connect('title')
        def _title_changed(self, title):
            self._legend.innerHTML = title
