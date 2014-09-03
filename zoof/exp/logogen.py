"""
Zoof, let's code! 
Zoof, let us code!
Zoof, coding to the people!
Zoof, coding for everyone.

"""
import time
from collections import OrderedDict

from PySide import QtCore, QtGui
from zoof.lib.zson import Dict

Qt = QtCore.Qt

# Default values
PARAMS = Dict()
PARAMS.size = 32
PARAMS.gap = 0.05
PARAMS.inset= 0.25
PARAMS.height = 0.4
PARAMS.width = 0.6
#
PARAMS.bgcolor = '#268bd2'  # '#cb4b16'
PARAMS.bgcolor2 = '#dc322f'
PARAMS.bgcolor3 = '#859900'
PARAMS.edgecolor = '#073642'
PARAMS.mono = False
PARAMS.fullheight = 1.0

    
def create_logo(**kwargs):
    """ Create Zoof logo and return as a QPixmap.
    """
    
    # Get shortnames for params
    params = PARAMS.copy()
    params.update(kwargs)
    L = [params[k] for k in 'size gap inset height width'.split()]
    size, gap, inset, height, width = L
    
    # Create vertices
    inset1 = inset * (1 - height)
    inset2 = inset * (1 - height - gap)
    betweenblocks = width+(1-width)*0.5
    #
    verts1 = [  (0, 0), (width, 0), (width-inset1, 1-height), 
                (width, 1-height), (width, 1), (0, 1), (inset1, height), 
                (0, height), ]
    verts2 = [  (width+gap, 0), (1, 0), (1-inset2, 1-height-gap),
                (width+gap-inset2, 1-height-gap), ]
    verts3 = [  (width+gap, 1-height), (betweenblocks, 1-height),
                (betweenblocks, 1), (width+gap, 1), ]
    verts4 = [  (betweenblocks+gap, 1-height), (1, 1-height),
                (1, 1), (betweenblocks+gap, 1), ]
    
    # Correct for edge
    edgewidth = (size/16)**0.5 / size
    for verts in (verts1, verts2, verts3, verts4):
        for i in range(len(verts)):
            verts[i] = [u*(1-edgewidth) + 0.5*edgewidth for u in verts[i]]
            u = verts[i][1]
            verts[i][1] = u*params.fullheight + 0.5*(1-params.fullheight)
    
    # Prepare to paint
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtGui.QColor(0, 0, 0, 0))
    painter = QtGui.QPainter()
    painter.begin(pixmap)
    painter.setRenderHints(1|2|4|8)
    
    # Paint outlines
    pen = QtGui.QPen(QtGui.QColor(params.edgecolor))
    pen.setWidthF(edgewidth*size)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    for verts in (verts1, verts2, verts3, verts4):
        lines = [QtCore.QPointF(p[0]*size, p[1]*size) for p in verts]
        painter.drawPolygon(lines)
    
    # Paint shape
    painter.setPen(Qt.NoPen)
    painter.setBrush(QtGui.QBrush(QtGui.QColor(params.bgcolor)))
    colors = params.bgcolor, params.bgcolor2, params.bgcolor3, params.bgcolor3
    for verts, clr in zip((verts1, verts2, verts3, verts4), colors):
        if not params.mono:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(clr)))
        lines = [QtCore.QPointF(p[0]*size, p[1]*size) for p in verts]
        painter.drawPolygon(lines)
    
    painter.end()
    return pixmap


class Win(QtGui.QWidget):
    
    def __init__(self):
        QtGui.QWidget.__init__(self, None)
        self.resize(900, 600)
        
        # Create labels to hold the logo pixmap
        self._labels = labels = [QtGui.QLabel(self) for i in range(4)]
        for label in labels:
            label.setAlignment(Qt.AlignCenter)
            label.setAutoFillBackground(True)
        labels[0].setStyleSheet("QLabel {background-color:#0f0; padding: 0px;}")
        labels[1].setStyleSheet("QLabel {background-color:#000; padding: 10px;}")
        labels[2].setStyleSheet("QLabel {background-color:%s; padding: 10px;}" % PARAMS.bgcolor)
        labels[3].setStyleSheet("QLabel {background-color:#fff; padding: 10px;}")
        
        labels[0].setMinimumSize(200, 200)
        labels[0].setMaximumSize(200, 200)
        
        # Lay out the labels
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        layout.addLayout(hbox1, 1)
        layout.addLayout(hbox2, 1)
        #
        controlLayout = QtGui.QVBoxLayout()
        hbox1.addLayout(controlLayout, 2)
        hbox1.addWidget(QtGui.QWidget(self), 1)
        #
        hbox1.addWidget(labels[0], 0)
        hbox2.setSpacing(0)
        for label in labels[1:]:
            hbox2.addWidget(label, 1)
        
        # Create sliders to modify logo params
        self._sliders = []
        self._sliderLabels = []
        for name, min, max, in [('size', 16, 256), 
                                ('gap', 0.0, 0.1),
                                ('inset', 0.0, 0.5),
                                ('height', 0.0, 0.5),
                                ('width', 0.1, 0.8),
                                ('fullheight', 0.5, 1.0),
                                ('mono', 0, 1), ]:
            val = PARAMS[name]
            if not isinstance(val, (float, int)):
                continue
            slider = QtGui.QSlider(Qt.Horizontal, self)
            slider._name = name
            slider._isfloat = False
            if isinstance(val, float):
                slider._isfloat = True
                val, min, max = val*1000, min*1000, max*1000
            slider.setRange(min, max)
            slider.setValue(val)
            slider.valueChanged.connect(self.updateLogo)
            label = QtGui.QLabel(name)
            #
            self._sliders.append(slider)
            self._sliderLabels.append(label)
            #
            hbox = QtGui.QHBoxLayout()
            hbox.addWidget(label, 1)
            hbox.addWidget(slider, 4)
            controlLayout.addLayout(hbox, 1)
        
        # Start
        self.updateLogo()
    
    def updateLogo(self, bla=None):
        # Obtain values from sliders and update slider labels
        names = [slider._name for slider in self._sliders]
        values = [(slider.value()/1000. if slider._isfloat else slider.value())
                  for slider in self._sliders]
        for name, val, label in zip(names, values, self._sliderLabels):
            fmt = '%s: %0.2f' if isinstance(val, float) else '%s: %i'
            label.setText(fmt % (name, val))
        # Generate pixmap
        t0 = time.time()
        pixmap = create_logo(**dict(zip(names, values)))
        #print('Logo took %0.0f ms to generate' % ((time.time() - t0)*1000))
        # Apply it to all display labels
        pixmapL = pixmap.scaled(200, 200, transformMode=Qt.FastTransformation)
        self._labels[0].setPixmap(pixmapL)
        for label in self._labels[1:]:
            label.setPixmap(pixmap)


if __name__ == '__main__':
    w = Win()
    w.show()
    w.raise_()
