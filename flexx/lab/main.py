# -*- coding: utf-8 -*-
# Copyright (c) 2014, Zoof Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""
This module provides the main window and the main function to run Zoof Lab.
"""

from zoof.qt import QtCore, QtGui

from zoof.lab.condapage import CondaPage

def main():
    """ The function that starts the Zoof Lab.
    """
    app = QtGui.QApplication([])
    m = MainWindow()
    m.show()
    app.exec_()


class MainWindow(QtGui.QMainWindow):
    """ The main window for the Zoof Lab.
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('Zoof Lab - '
                            'The interactive IDE for dynamic languages')
        self.setCentralWidget(CondaPage(self))
        


if __name__ == '__main__':
    main()
