zoof.qt
-------

This subpackage is a proxy module to import Qt libraries. It allow
loading the libaries from PyQt5, PyQt4 and PySide, whichever is
available. If either of these is already imported, that one is used.
Otherwise the preference set in qt.conf is used. If there is no qt.conf,
the preference is PyQt5-PyQt4-PySide.
