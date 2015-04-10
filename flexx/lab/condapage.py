# -*- coding: utf-8 -*-
# Copyright (c) 2014, Zoof Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""
This module provides a Zoof page to manage conda envs.
"""

from zoof.lib import condaapi
from zoof.qt import QtCore, QtGui

translate = lambda x:x

class CondaPage(QtGui.QWidget):
    """ The main window for the Zoof Lab.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._list = QtGui.QListWidget(self)
        
        self._choice_label = QtGui.QLabel(
            translate('Select language and packages'))
        self._choice_lang = QtGui.QComboBox(self)
        for name in ('Python 2.6', 'Python 2.7', 'Python 3.3', 'Python 3.4',
                     'Pypy2', 'Pypy3', 'Julia'):
            self._choice_lang.addItem(name)
        self._choice_lang.setCurrentIndex(3)
        
        self._choice_stack = QtGui.QComboBox(self)
        for name in ('Minimal', 'Scipy stack', 'Scipy stack++', 'Web?'):
            self._choice_stack.addItem(name)
        self._choice_stack.setCurrentIndex(2)
        
        self._create_but = QtGui.QPushButton(translate('Create env'))
        self._create_but.clicked.connect(self._createEnv)
        
        # Layout
        layoutA1 = QtGui.QHBoxLayout(self)
        self.setLayout(layoutA1)
        layoutB2 = QtGui.QVBoxLayout()
        #
        layoutA1.addWidget(self._list)
        layoutA1.addLayout(layoutB2)
        #
        layoutB2.addStretch(1)
        layoutB2.addWidget(self._choice_label)
        layoutB2.addWidget(self._choice_lang)
        layoutB2.addWidget(self._choice_stack)
        layoutB2.addWidget(self._create_but)
        layoutB2.addStretch(1)
    
    def _createEnv(self):
        lang = self._choice_lang.currentText()
        stack = self._choice_stack.currentText()
        # todo: maybe a hook in qt so that any exception causes a popup
        # or a text in the tip window.
        if not 'python' in lang.lower():
            raise NotImplementedError('Only Python supported for now')
        
        # Build command
        pyver = lang[-3:]#.replace('.', '')
        command = ['create', '-n', 'foo', 'python=%s' % pyver]
        if 'scipy' in stack.lower():
            command.extend(['numpy', 'scipy'])
            if '++' in stack:
                command.extend(['scikit-image'])
        
        # Run command
        condaapi.condacmd(*command)


if __name__ == '__main__':
    m = CondaPage()
    m.show()
