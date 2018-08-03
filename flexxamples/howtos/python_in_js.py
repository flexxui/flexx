# doc-export: UsingPython
"""
This example demonstrates what things from Python land can be used in JS.

Flexx detects what names are used in the transpiled JS of a JsComponent
(a widget, in this case), and tries to look these up in the module,
converting the used objects if possible.

Check out the source of the generated page to see what Flexx did.

Note that once running, there is no interaction with the Python side, so this
example can be exported to standalone HTML.
"""

from flexx import flx

# Define a value. If used in JS, this value will be included in the definition
# of the JS module that corresponds to this Python module. Therefore, the value
# must be serializable using JSON (None, bool, int, float, str, list, dict).
info = dict(name='John', age=42)

# Import a value from another module. It's still just a value, and there is
# no way for Flexx to tell where it was defined, so on the JS side it is
# defined in *this* module just like info. This means that if you import
# and use a value in different modules, in JS these are different instances.
from sys import version

# Define a function (or a class). Provided that its compatible with PScript,
# you can just use this in the JS. Note that if this function used a value
# or a function, that would be converted too.
def poly(x, *coefs):
    degree = len(coefs) - 1
    y = 0
    for coef in coefs:
        y += coef * x ** degree
        degree -= 1
    return y

# Import a (PScript-compatible) function from another module. In this case
# Flexx can tell where it was defined and put it in its own module. See
# the page source.
from html import escape


class UsingPython(flx.Widget):

    def init(self):

        # A rather boring way to present the info. The point is that
        # we're using all sorts of Python stuff here, that is automatically
        # converted for us.
        lines = []
        lines.append('This JS was generated from Python ' + version)
        lines.append('Person %s is %i years old' % (info['name'], info['age']))
        lines.append('Evaling 4*x**2 + 5*x + 6 with x=4: ' + poly(4, 4, 5, 6))
        lines.append('... and with x=12: ' + poly(12, 4, 5, 6))
        lines.append('String with escaped html: ' + escape('html <tags>!'))
        lines.append('String with escaped html: ' + escape('Woezel & Pip'))

        self.label = flx.Label(wrap=0, html='<br />'.join(lines))


if __name__ == '__main__':
    m = flx.launch(UsingPython, 'browser')
    flx.run()
