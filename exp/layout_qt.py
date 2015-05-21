""" Simple example showing layout in Qt.
"""

from PyQt4 import QtGui

class Main(QtGui.QWidget):
    
    def __init__(self):
        super().__init__(None)
        
        b1 = QtGui.QPushButton('hello')
        b2 = QtGui.QPushButton('helloooo world')
        l1 = QtGui.QLabel('foo')
        l2 = QtGui.QLabel('fooo baaar always one line, no wrap')
        l1.setStyleSheet('QLabel{background-color:#f55;}')
        l2.setStyleSheet('QLabel{background-color:#5f5;}')
        l1.resize(100, 100)
        l2.resize(100, 100)
        #l1.setMinimumSize(100, 100)  # results in both l1 and l2 to be big
        
        #l2.setText('fooo baaar' * 20)  # Results in very wide window
        
        layout = QtGui.QHBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(b1, 0)
        layout.addWidget(b2, 1 )
        layout.addWidget(l1, 2)
        layout.addWidget(l2, 3)

a = QtGui.QApplication([])
m = Main()
m.show()
a.exec_()
        