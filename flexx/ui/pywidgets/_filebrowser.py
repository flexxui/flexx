import os
from ... import event
from .._widget import PyWidget, Widget, create_element


sep = os.path.sep


class _FileBrowserJS(Widget):
    """ JS part of FileBrowserWidget.
    """

    CSS = """
        .flx-_FileBrowserJS {
            display: grid;
            padding: 0.5em;
            overflow-y: scroll;
            grid-template-columns: auto 1fr auto;
            grid-column-gap: 0.5em;
            justify-items: start;
            justify-content: stretch;
            align-content: start;
            -webkit-user-select: none;  /* Chrome all / Safari all */
            -moz-user-select: none;     /* Firefox all */
            -ms-user-select: none;      /* IE 10+ */
            user-select: none;          /* Likely future */
        }
        .flx-_FileBrowserJS > b {
            box-sizing: border-box;
            background: #DDD;
            border-radius: 4px;
            width: 100%;
            padding: 0.3em;
        }
        .flx-_FileBrowserJS > b > a {
            cursor: pointer;
            margin-right: 0.2em;
        }
        .flx-_FileBrowserJS > b > a:hover {
            border-bottom: 2px solid rgba(0, 0, 0, 0.6);
        }
        .flx-_FileBrowserJS > u {
            width: 100%;
            cursor: pointer;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            text-decoration: none;
        }
        .flx-_FileBrowserJS > i {
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            width: 100%;
        }
    """

    _items = event.ListProp(settable=True)
    _dirname = event.StringProp(settable=True)


    def init(self):
        self.node.onclick = self._nav

    def _render_dom(self):
        dirname = self._dirname.rstrip(sep)
        pparts = dirname.split(sep)
        path_els = []
        for i in range(0, len(pparts)):
            el = create_element("a",
                {"dirname": sep.join(pparts[:i+1]) + sep}, pparts[i] + sep)
            path_els.append(el)
        elements = []
        elements.append(create_element("b", {},
                        create_element("a",
                            {"dirname": sep.join(pparts[:-1]) + sep}, "..")))
        elements.append(create_element("b", {}, path_els))
        elements.append(create_element("s", {}, ""))

        for i in range(len(self._items)):
            kind, fname, size = self._items[i]
            elements.append(create_element("span", {}, " ❑■"[kind] or ""))
            if kind == 1:
                elements.append(create_element("u",
                    {"dirname": dirname + sep + fname, "filename": None}, fname))
            else:
                elements.append(create_element("u",
                    {"filename": dirname + sep + fname, "dirname": None}, fname))
            if size >= 1048576:
                elements.append(create_element("i", {},
                    "{:0.1f} MiB".format(size/1048576)))
            elif size >= 1024:
                elements.append(create_element("i", {},
                    "{:0.1f} KiB".format(size/1024)))
            elif size >= 0:
                elements.append(create_element("i", {}, "{} B".format(size)))
            else:
                elements.append(create_element("s", {}, ""))
        return elements

    @event.emitter
    def _nav(self, ev):
        dirname = ev.target.dirname or None
        filename = ev.target.filename or None
        if dirname or filename:
            return {"dirname": dirname, "filename": filename}


class FileBrowserWidget(PyWidget):
    """ A PyWidget to browse the file system. Experimental. This could be the
    basis for a file open/save dialog.
    """

    _WidgetCls = _FileBrowserJS

    path = event.StringProp("~", doc="""
        The currectly shown directory (settable). Defaults to the user directory.
        """)

    @event.action
    def set_path(self, dirname=None):
        """ Set the current path. If an invalid directory is given,
        the path is not changed. The given path can be absolute, or relative
        to the current path.
        """
        if dirname is None or not isinstance(dirname, str):
            dirname = "~"
        if dirname.startswith("~"):
            dirname = os.path.expanduser(dirname)
        if not os.path.isabs(dirname):
            dirname = os.path.abspath(os.path.join(self.path, dirname))
        # Set if valid, otherwise default to home dir
        if os.path.isdir(dirname):
            self._mutate("path", dirname)
        elif not self.path:
            self._mutate("path", os.path.expanduser("~"))

    @event.emitter
    def selected(self, filename):
        """ Emitter that fires when the user selects a file. The emitted event
        has a "filename" attribute.
        """
        return {"filename": filename}

    @event.reaction
    def _on_path(self):
        path = self.path
        if not path:
            return

        # Get directory contents
        items = []
        for fname in os.listdir(path):
            filename = os.path.join(path, fname)
            if os.path.isdir(filename):
                items.append((1, fname, -1))
            elif os.path.isfile(filename):
                items.append((2, fname, os.path.getsize(filename)))

        # Sort, by type, then name
        items.sort()

        # Update real widget
        self._jswidget._set_dirname(path)
        self._jswidget._set_items(items)

    @event.reaction("_jswidget._nav")
    def _on_nav(self, *events):
        dirname = events[-1].dirname
        filename = events[-1].filename
        print(dirname, filename)
        if dirname:
            self.set_path(dirname)
        elif filename:
            self.selected(filename)
