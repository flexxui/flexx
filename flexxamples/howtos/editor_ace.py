# doc-export: CodeEditor
"""
This example demonstrates a code editor widget based on Ace.
"""

# todo: Maybe this should be a widget in the library (flexx.ui.Ace) ?

from flexx import flx

# Associate Ace's assets with this module so that Flexx will load
# them when (things from) this module is used.
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/'
flx.assets.associate_asset(__name__, base_url + 'ace.js')
flx.assets.associate_asset(__name__, base_url + 'mode-python.js')
flx.assets.associate_asset(__name__, base_url + 'theme-solarized_dark.js')


class CodeEditor(flx.Widget):
    """ A CodeEditor widget based on Ace.
    """

    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """

    def init(self):
        global window
        # https://ace.c9.io/#nav=api
        self.ace = window.ace.edit(self.node, "editor")
        self.ace.setValue("import os\n\ndirs = os.walk")
        self.ace.navigateFileEnd()  # otherwise all lines highlighted
        self.ace.setTheme("ace/theme/solarized_dark")
        self.ace.getSession().setMode("ace/mode/python")

    @flx.reaction('size')
    def __on_size(self, *events):
        self.ace.resize()


if __name__ == '__main__':
    flx.launch(CodeEditor, 'app')
    flx.run()
