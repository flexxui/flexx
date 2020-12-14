"""
Simple use of a the markdown widget,
using a custom widget that is populated in its ``init()``.
"""

from flexx import app, event, ui, flx


class Example(flx.Widget):

    def init(self):
        content = "# Welcome\n\n" \
            "Hello.  Welcome to my **website**. This is an example of a widget container for markdown content. " \
            "The content can be text or a link.\n\n"
        content += "\n\n".join(["a new line to test long files" for a in range(100)])
        ui.Markdown(content=content, style='background:#EAECFF;height:60%;')


if __name__ == '__main__':
    m = flx.launch(Example, 'default-browser')
    flx.run()
