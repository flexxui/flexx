# doc-export: CodeEditor
"""
This example demonstrates a code editor widget based on Ace.
"""

# todo: Maybe this should be a widget in the library (flexx.ui.Ace) ?

from flexx import ui, app, event
from flexx.pyscript import window

# Associate Ace's assets with this module so that Flexx will load
# them when (things from) this module is used.
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/'
app.assets.associate_asset(__name__, base_url + 'ace.js')
app.assets.associate_asset(__name__, base_url + 'mode-python.js')
app.assets.associate_asset(__name__, base_url + 'theme-solarized_dark.js')

class CodeEditor(ui.Widget):
    """ A CodeEditor widget based on Ace.
    """
    
    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """
    
    class JS:
        def init(self):
            # https://ace.c9.io/#nav=api
            self.ace = window.ace.edit(self.node, "editor")
            self.ace.setValue("import os\n\ndirs = os.walk")
            self.ace.navigateFileEnd()  # otherwise all lines highlighted
            self.ace.setTheme("ace/theme/solarized_dark")
            self.ace.getSession().setMode("ace/mode/python")
            
        @event.connect('size')
        def __on_size(self, *events):
            self.ace.resize()

if __name__ == '__main__':
    app.launch(CodeEditor, 'app')
    app.run()
