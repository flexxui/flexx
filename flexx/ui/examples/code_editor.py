# doc-export: CodeEditor
"""
This example demonstrates a code editor widget based on CodeMirror.
"""

# todo: Maybe this should be a widget in the library (flexx.ui.CodeMirror) ?

from flexx import ui, app, event
from flexx.pyscript.stubs import window

# Associate CodeMirror's assets with this module so that Flexx will load
# them when (things from) this module is used.
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/'
app.assets.associate_asset(__name__, base_url + '5.21.0/codemirror.min.css')
app.assets.associate_asset(__name__, base_url + '5.21.0/codemirror.min.js')
app.assets.associate_asset(__name__, base_url + '5.21.0/mode/python/python.js')
app.assets.associate_asset(__name__, base_url + '5.21.0/theme/solarized.css')
app.assets.associate_asset(__name__, base_url + '5.21.0/addon/selection/active-line.js')
app.assets.associate_asset(__name__, base_url + '5.21.0/addon/edit/matchbrackets.js')

class CodeEditor(ui.Widget):
    """ A CodeEditor widget based on CodeMirror.
    """
    
    CSS = """
    .flx-CodeEditor > .CodeMirror {
        width: 100%;
        height: 100%;
    }
    """
    
    class JS:
        
        def init(self):
            # https://codemirror.net/doc/manual.html
            options = dict(value='from flexx import ui, app, event',
                           mode='python',
                           theme='solarized dark',
                           autofocus=True,
                           styleActiveLine=True,
                           matchBrackets=True,
                           indentUnit=4,
                           smartIndent=True,
                           lineWrapping=True,
                           lineNumbers=True,
                           firstLineNumber=1,
                           readOnly=False,
                           )
            self.cm = window.CodeMirror(self.node, options)
        
        @event.connect('size')
        def __on_size(self, *events):
            self.cm.refresh()


if __name__ == '__main__':
    app.launch(CodeEditor, 'xul')
    app.run()
