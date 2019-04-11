""" TableWidget

A ``TableWidget`` can contain ``TableEntry`` objects, which in turn can contain
``TableEntryAttr`` objects to construct a table.

.. UIExample:: 180

    from flexx import flx

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

    class Example(flx.Widget):

        def init(self):
            with flx.TableWidget(show_header=True):
                for r in releases:
                    with flx.TableEntry():
                        flx.TableEntryAttr(title="Version", text=r.version)
                        flx.TableEntryAttr(title="Commit", text=r.commit)

"""

from ... import event
from .._widget import Widget, create_element

# todo: automatically generate MDN links in the documentation


class TableWidget(Widget):
    """
    A ``Widget`` that can be used to display information in a table. Its entries
    are represented by its children, which must only be ``TableEntry`` objects.
    Entry attributes are created by instantiating ``TableEntryAttributes`` in the
    context of a ``TableEntry``.

    A `<caption> <https://developer.mozilla.org/docs/Web/HTML/Element/caption>`_ is
    rendered to show the ``title`` of the table if it is not empty.

    The ``outernode`` of this widget is a
    `<table> <https://developer.mozilla.org/docs/Web/HTML/Element/table>`_ with a
    `<thead> <https://developer.mozilla.org/docs/Web/HTML/Element/thead>`_ to hold the
    header row and a
    `<tbody> <https://developer.mozilla.org/docs/Web/HTML/Element/tbody>`_ to contain
    the entries.

    """

    CSS = """

    /* ----- Table Widget Mechanics ----- */

    .flx-TableWidget {
        overflow: scroll;
        cursor: default;
    }

    .flx-TableWidget .cell {
        padding: 3px 6px;
    }

    """

    title = event.StringProp(settable=True, doc="""
        The title which is shown as the caption of this table. If not specified,
        not any caption is rendered.
        """)

    show_header = event.BoolProp(False, doc="""
        Whether to show the header line.
        """)

    def _create_dom(self):
        return create_element('table')

    def _render_dom(self):
        entries = []
        caption = ''
        header = ''

        for child in self.children:
            if child.__name__ == 'TableEntry':
                entries.append(child)

        if not entries:
            raise RuntimeError("A TableWidget must contain at least one TableEntry.")

        if self.title:
            caption = create_element('caption', {}, self.title)

        if self.show_header:
            header = create_element(
                'thead', {}, [
                    create_element(
                        'tr', {}, [
                            create_element('th', {'class': 'cell'}, widget.title)
                            for widget in entries[0].children
                            if widget.__name__ == 'TableEntryAttr'
                        ]
                    )
                ]
            )

        return create_element(
            'table', {}, [
                caption,
                header,
                create_element('tbody', {}, [entry.outernode for entry in entries])
            ]
        )


class TableEntry(Widget):
    """ An entry to put in a ``TableWidget``. This widget must only be used inside a
    ``TableWidget``.

    The ``outernode`` of this widget is a
    `<tr> <https://developer.mozilla.org/docs/Web/HTML/Element/tr>`_.

    """

    # todo: remove `set_parent` from documentation as its usage is internal, here
    @event.action
    def set_parent(self, parent, pos=None):
        if not (parent is None or
                isinstance(parent, TableWidget)):
            raise RuntimeError("TableEntry objects can only be created in the context "
                               "of a TableWidget.")
        super().set_parent(parent, pos)

    def _create_dom(self):
        return create_element('tr')


class TableEntryAttr(Widget):
    """ An attribute to put in a ``TableEntry``. This widget must only be used inside a
    ``TableEntry``.

    If a ``title`` is specified, it is rendered as the header for this attribute.

    The ``outernode`` of this widget is a
    `<td> <https://developer.mozilla.org/docs/Web/HTML/Element/td>`_.

    """

    text = event.StringProp(settable=True, doc="""
        The text shown for this attribute.
        """)

    title = event.StringProp(settable=True, doc="""
        The title of this attribute that is displayed in the header.
        """)

    @event.action
    def set_parent(self, parent, pos=None):
        if not (parent is None or
                isinstance(parent, TableEntry)):
            raise RuntimeError("TableEntryAttr objects can only be created in the "
                               "context of a TableEntry.")
        super().set_parent(parent, pos)

    def _create_dom(self):
        return create_element('td', {'class': 'cell'}, [self.text])
