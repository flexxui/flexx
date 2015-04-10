"""
Get WebGL to work in QWebkit.
"""

url = 'https://videos.cdn.mozilla.net/uploads/mozhacks/flight-of-the-navigator/'
url = 'http://helloracer.com/webgl/'
#url = 'http://www.3dtin.com'
url = 'https://www.shadertoy.com/view/XsBSRG'
#url = "http://www.webkit.org/blog-files/webgl/SpiritBox.html"

if True:
    from PySide import QtCore, QtGui, QtWebKit
    
    app = QtGui.QApplication([])
    
    settings = QtWebKit.QWebSettings.globalSettings()
    settings.setAttribute(QtWebKit.QWebSettings.WebGLEnabled, True)
    settings.setAttribute(QtWebKit.QWebSettings.AcceleratedCompositingEnabled, True)
    
    m = QtWebKit.QWebView(None)
    
else:
    from PyQt5 import QtCore, QtWebKitWidgets, QtGui, QtWidgets
    
    app = QtWidgets.QApplication([])

    m = QtWebKitWidgets.QWebView()

m.show()
m.setUrl(QtCore.QUrl(url))
app.exec_()
