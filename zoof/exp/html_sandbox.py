import os
from PyQt4 import QtCore, QtGui, QtWebKit

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

INIT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>New example</title>

    <style>
    
    body {
        background-color: #fff;
    }
   
    </style>

</head>
<body>

</body>
</html>
""".lstrip()


class TextField(QtGui.QPlainTextEdit):

    def __init__(self, parent):
        QtGui.QPlainTextEdit.__init__(self, parent)
        # Set font to monospaced (TypeWriter)
        font = QtGui.QFont('')
        font.setStyleHint(font.TypeWriter, font.PreferDefault)
        font.setPointSize(8)
        self.setFont(font)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.insertPlainText('    ')
        else:
            super().keyPressEvent(event)


class MainWindow(QtGui.QWidget):
    
    def __init__(self):
        super().__init__(None)
        
        # Create editor
        self._editor = TextField(self)
        self._editor.setMinimumWidth(525)
        
        # Create display
        self._display = QtWebKit.QWebView(self)
        
        # Create example selector
        self._select = QtGui.QComboBox(self)
        
        # Create example *new* button
        self._newBut = QtGui.QPushButton('New example', self)
        
        # Init
        self._current_example = 0
        self._load_examples()
        self._update_select()
        self._editor.setPlainText(self._examples[0])
        self._display.setHtml(self._examples[0])
        
        # Connect
        self._editor.textChanged.connect(self._on_code_update)
        self._select.activated.connect(self._on_select)
        self._newBut.clicked.connect(self._on_new_example)
        
        # Layout
        layout0 = QtGui.QHBoxLayout(self)
        self.setLayout(layout0)
        #
        layout00 = QtGui.QVBoxLayout()
        layout000 = QtGui.QHBoxLayout()
        layout000.addWidget(self._select, 1)
        layout000.addWidget(self._newBut, 0)
        layout00.addLayout(layout000, 0)
        layout00.addWidget(self._editor, 1)
        #
        layout0.addLayout(layout00, 0)
        layout0.addWidget(self._display, 1)
        
        self.resize(1200, 800)
    
    def _on_code_update(self):
        text = self._editor.toPlainText()
        self._display.setHtml(text)
        self._examples[self._current_example] = text
        self._save_examples()
        self._update_select()
    
    def _on_select(self):
        self._current_example = self._select.currentIndex()
        self._update_select()
        text = self._examples[self._current_example]
        self._editor.setPlainText(text)
        self._display.setHtml(text)
    
    def _on_new_example(self):
        self._examples.append(INIT_HTML)
        self._current_example = len(self._examples) - 1
        self._update_select()
        self._on_select()
    
    def _update_select(self):
        self._select.clear()
        for text in self._examples:
            title = self._find_title(text)
            self._select.addItem(title)
        self._select.setCurrentIndex(self._current_example)
    
    def _load_examples(self):
        # Load txt
        fname = os.path.join(THIS_DIR, 'html_examples.txt')
        if not os.path.isfile(fname):
            open(fname, 'wb')
        totaltext = open(fname, 'rb').read().decode('utf-8')
        # Split and turn into dict
        self._examples = []
        for text in totaltext.split('=' * 80):
            text = text.strip()
            if not text:
                continue
            self._examples.append(text + '\n')
        if not self._examples:
            self._examples.append(INIT_HTML)

    def _save_examples(self):
        # Turn examples into text
        devider = '\n\n' + '=' * 80 + '\n\n'
        parts = [text.strip() for text in self._examples]
        totaltext = devider.join(parts)
        # Save
        fname = os.path.join(THIS_DIR, 'html_examples.txt')
        open(fname, 'wb').write(totaltext.encode('utf-8'))
    
    def _find_title(self, text):
        try:
            i1 = text.index('<title>')
            i2 = text.index('</title>')
            return text[i1+7:i2].strip()
        except ValueError:
            return 'Untitled'


if __name__ == '__main__':
    app = QtGui.QApplication([])
    m = MainWindow()
    m.show()
    app.exec_()
