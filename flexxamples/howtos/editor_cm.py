# doc-export: CodeEditor
"""
This example demonstrates a code editor widget based on CodeMirror.
"""

# todo: Maybe this should be a widget in the library (flexx.ui.CodeMirror) ?

from flexx import flx

# Associate CodeMirror's assets with this module so that Flexx will load
# them when (things from) this module is used.
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/'
flx.assets.associate_asset(__name__, base_url + '5.21.0/codemirror.min.css')
flx.assets.associate_asset(__name__, base_url + '5.21.0/codemirror.min.js')
flx.assets.associate_asset(__name__, base_url + '5.21.0/mode/python/python.js')
flx.assets.associate_asset(__name__, base_url + '5.21.0/theme/solarized.css')
flx.assets.associate_asset(__name__, base_url + '5.21.0/addon/selection/active-line.js')
flx.assets.associate_asset(__name__, base_url + '5.21.0/addon/edit/matchbrackets.js')


class CodeEditor(flx.Widget):
    """ A CodeEditor widget based on CodeMirror.
    """

    CSS = """
    .flx-CodeEditor > .CodeMirror {
        width: 100%;
        height: 100%;
    }
    """

    def init(self):
        global window
        # https://codemirror.net/doc/manual.html
        options = dict(value='import os\n\ndirs = os.walk',
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

    @flx.reaction('size')
    def __on_size(self, *events):
        self.cm.refresh()


if __name__ == '__main__':
    flx.launch(CodeEditor, 'app')
    flx.run()
