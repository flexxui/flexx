""" Grid layout.

Layout a series of widgets in a grid. The grid has a specified number of columns.
Example:

.. UIExample:: 300

    from flexx import flx

    class Example(flx.Widget):
        def init(self):
            with flx.HSplit():
                with flx.GridLayout(ncolumns=3):
                    flx.Button(text='A')
                    flx.Button(text='B')
                    flx.Button(text='C')
                    flx.Button(text='D')
                    flx.Button(text='E')
                    flx.Button(text='F')

                with flx.GridLayout(ncolumns=2):
                    flx.Button(text='A', flex=(1, 1))  # Set flex for 1st row and col
                    flx.Button(text='B', flex=(2, 1))  # Set flex for 2nd col
                    flx.Button(text='C', flex=(1, 1))  # Set flex for 2nd row
                    flx.Button(text='D')
                    flx.Button(text='E', flex=(1, 2))  # Set flex for 3d row
                    flx.Button(text='F')

"""

from ... import event
from . import Layout


class GridLayout(Layout):
    """ A layout widget that places its children in a grid with a certain number
    of columns. The flex values of the children in the first row determine the
    sizing of the columns. The flex values of the first child of each row
    determine the sizing of the rows.

    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_,
    which lays out it's child widgets and their labels using
    `CSS grid <https://css-tricks.com/snippets/css/complete-guide-grid/>`_.
    """

    CSS = """
    .flx-GridLayout {
        display: grid;
        justify-content: stretch;
        align-content: stretch;
        justify-items: stretch;
        align-items: stretch;
    }
    """

    ncolumns = event.IntProp(2, settable=True, doc="""
        The number of columns of the grid.
    """)

    @event.reaction
    def _on_columns(self):
        ncolumns = self.ncolumns
        children = self.children
        column_templates = []
        row_templates = []
        for i in range(min(ncolumns, len(children))):
            flex = children[i].flex[0]
            column_templates.append(flex + "fr" if flex > 0 else "auto")
        for i in range(0, len(children), ncolumns):
            flex = children[i].flex[1]
            row_templates.append(flex + "fr" if flex > 0 else "auto")

        self.node.style['grid-template-rows'] = " ".join(row_templates)
        self.node.style['grid-template-columns'] = " ".join(column_templates)

    def _query_min_max_size(self):
        """ Overload to also take child limits into account.
        """

        # Collect contributions of child widgets
        mima1 = [0, 1e9, 0, 0]
        for child in self.children:
            mima2 = child._size_limits
            mima1[0] = max(mima1[0], mima2[0])
            mima1[1] = min(mima1[1], mima2[1])
            mima1[2] += mima2[2]
            mima1[3] += mima2[3]

        # Dont forget padding and spacing
        extra_padding = 2
        extra_spacing = 2
        for i in range(4):
            mima1[i] += extra_padding
        mima1[2] += extra_spacing
        mima1[3] += extra_spacing

        # Own limits
        mima3 = super()._query_min_max_size()

        # Combine own limits with limits of children
        return [max(mima1[0], mima3[0]),
                min(mima1[1], mima3[1]),
                max(mima1[2], mima3[2]),
                min(mima1[3], mima3[3])]
