"""
Example UI with a nested layout. This demonstrates how we could specify
layout at the same time as defining our widgets, with very little
boilerplate code.

By using a context manager, we reduce the specification of the layout
to a single line, and we get indentation as an indication of structure.

The widgets themselves contain the hints needed by the layout (e.g.
flex, pack, halign, valign). In the call of the with-statement, one can
specify parameters for the layout itself. This makes it very concise.

Compare this to equivalent ENAML; I think this is even shorter.

"""

from zoof import ui

class MyApp(ui.App):
    def init(self):
        
        with ui.VBoxLayout():
            with ui.FormLayout(spacing=1):
                ui.Label(self, 'Name')
                self._name = ui.TextInput(self)
                ui.Label(self, 'Age')
                self._age = ui.IntInput(self)
            with ui.HBoxLayout():
                ui.Widget(self, flex=1)  # spacer
                ui.Button(self, 'Cancel', 
                          on_click=self.close, 
                          flex=0)
                ui.Button(self, 'Ok', 
                          on_click=self.process, 
                          flex=0)
        
        # I wonder ... 
        # - we might even be able to get rid of 'self'
        # - what if we force all widgets to be created in a context manager?
        # - is it necessary to dynamically create widgets? It might!
    
    def init_alt(self):
        # Is layout a class or a method?
        
        with self.layout_vbox():
            with self.layout_form(spacing=1):
                pass  # etc...
    
    def init_qt(self):
        # The above would be more or less this code in Qt 
        # (from the top of my head, not tested)
        
        layout0 = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        layout1 = QtGui.QFormLayout()
        layout2 = QtGui.QHBoxLayout()
        
        layout0.addLayout(layout1, 1)
        layout0.addLayout(layout2, 1)
        
        self._name = QtGui.QLineEdit(self)
        self._age = QtGui.QLineEdit(self)
        layout.addItem('Name', self._name)
        layout.addItem('Age', self._age)
        
        self._cancel = QtGui.QPushButton('Cancel')
        self._ok = QtGui.QPushButton('Ok')
        layout2.addStretch(1)
        layout2.addWidget(self._cancel, 0)
        layout2.addWidget(self._ok, 0)

ui.run()
