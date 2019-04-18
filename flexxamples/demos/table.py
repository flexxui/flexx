# doc-export: ReleasesTable
"""
An example of a custom table widget built from stock.

Noticeable features:

 * widget properties,
 * custom DOM rendering with:
   - optional DOM elements,
   - mandatory child widgets type,
   - mandatory parent widget type,
   - `flex` support.

"""

from flexx import flx


class TableWidget(flx.Widget):
    """
    A ``Widget`` that can be used to display information in a table. Its rows are
    represented by its children, which must only be ``TableRow`` objects.
    Cells are created by instantiating ``TableCells`` in the context of a ``TableRow``.

    A `<caption> <https://developer.mozilla.org/docs/Web/HTML/Element/caption>`_ is
    rendered to show the ``title`` of the table if it is not empty.

    The ``outernode`` of this widget is a
    `<table> <https://developer.mozilla.org/docs/Web/HTML/Element/table>`_ with a
    `<thead> <https://developer.mozilla.org/docs/Web/HTML/Element/thead>`_ to hold the
    header row and a
    `<tbody> <https://developer.mozilla.org/docs/Web/HTML/Element/tbody>`_ to contain
    the body rows.

    """

    CSS = """

    /* ----- Table Widget Mechanics ----- */

    .flx-TableWidget {
        height: 100%;
        display: flex;
        flex-flow: column nowrap;

        cursor: default;
    }

    .flx-TableRow, .flx-TableWidget thead tr {
        display: flex;
        flex-flow: row nowrap;
    }

    .flx-TableCell, .flx-TableWidget th {
        display: flex;
        flex-flow: row nowrap;
        flex-grow: 1;
        flex-basis: 0;

        padding: 3px 6px;
    }

    """

    title = flx.StringProp(settable=True, doc="""
        The title which is shown as the caption of this table. If not specified,
        not any caption is rendered.
        """)

    show_header = flx.BoolProp(False, doc="""
        Whether to show the header line.
        """)

    def _create_dom(self):
        return flx.create_element('table')

    def _render_dom(self):
        rows = []
        caption = ''
        header = ''

        for child in self.children:
            if isinstance(child, TableRow):
                rows.append(child)

        if not rows:
            raise RuntimeError("A TableWidget must contain at least one TableRow.")

        if self.title:
            caption = flx.create_element('caption', {}, self.title)

        if self.show_header:
            header = flx.create_element(
                'thead', {}, [
                    flx.create_element(
                        'tr', {}, [
                            flx.create_element(
                                'th',
                                {'style': 'flex-grow: {};'.format(widget.flex[0] + 1)},
                                widget.title
                            )
                            for widget in rows[0].children
                            if isinstance(widget, TableCell)
                        ]
                    )
                ]
            )

        return flx.create_element(
            'table', {}, [
                caption,
                header,
                flx.create_element('tbody', {}, [r.outernode for r in rows])
            ]
        )


class TableRow(flx.Widget):
    """ A row to put in a ``TableWidget``. This widget must only be used inside a
    ``TableWidget``. Its cells are represented by its children, which must only be
    ``TableCell`` objects.

    The ``outernode`` of this widget is a
    `<tr> <https://developer.mozilla.org/docs/Web/HTML/Element/tr>`_.

    """

    @flx.action
    def set_parent(self, parent, pos=None):
        if not (parent is None or
                isinstance(parent, TableWidget)):
            raise RuntimeError("TableRows can only be created in the context of a "
                               "TableWidget.")

        super().set_parent(parent, pos)

    def _create_dom(self):
        return flx.create_element('tr')

    def _render_dom(self):
        for widget in self.children:
            widget.apply_style({
                'flex-grow': widget.flex[0] + 1
            })

        return super()._render_dom(self)


class TableCell(flx.Widget):
    """ A cell to put in a ``TableRow``. This widget must only be used inside a
    ``TableRow``.

    If a ``title`` is specified, it is rendered as the header for this attribute.

    The ``outernode`` of this widget is a
    `<td> <https://developer.mozilla.org/docs/Web/HTML/Element/td>`_.

    """

    text = flx.StringProp(settable=True, doc="""
        The text shown in the cell.
        """)

    title = flx.StringProp(settable=True, doc="""
        The title of the column containing the cell. It is displayed in the header
        if enabled in the parent ``TableWidget``.
        """)

    @flx.action
    def set_parent(self, parent, pos=None):
        if not (parent is None or
                isinstance(parent, TableRow)):
            raise RuntimeError("TableCells can only be created in the context of a "
                               "TableRow.")

        super().set_parent(parent, pos)

    def _create_dom(self):
        return flx.create_element('td', {}, [self.text])

releases = [
    flx.Dict(version='0.7.1',
                commit='38b322c9f521270b1874db150104c094cce508e1'),
    flx.Dict(version='0.7.0',
                commit='74fe76f749f4b033c193a8f8e7b025d42c6f9e70'),
    flx.Dict(version='0.6.2',
                commit='1c3dbb0cedd47b29bae475517302408a53effb4b'),
    flx.Dict(version='0.6.1',
                commit='e54574b3ecd7e5c39c09da68eac33662cc276b78'),
    flx.Dict(version='0.6.0',
                commit='4cff67e57a7b2123bd4d660a79527e3131a494be'),
]

class ReleasesTable(flx.Widget):

    def init(self):
        self.apply_style({
            'width': '100%'
        })

        with TableWidget(title="Flexx Releases", show_header=True):
            for r in releases:
                with TableRow():
                    TableCell(title="Version", text=r.version, flex=0)
                    TableCell(title="Commit", text=r.commit, flex=1)

if __name__ == '__main__':
    m = flx.launch(ReleasesTable, 'app')
    flx.run()
