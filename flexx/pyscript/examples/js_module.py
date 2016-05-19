"""
Example on how to create a JavaScript module using PyScript.

PyScript creates AMD modules that can be used in the browser, in nodejs,
and in combination with browserify and related tools.
"""

# This import is ignored by PyScript, it allows using these variable
# names without triggering pyflakes (a static Python source analysis tool).
from flexx.pyscript import undefined, window  # noqa

class Foo:
    
    a_constant = 1, 2, 3
    
    def ham(self, x):
        self.x = x
    
    def eggs(self, y):
        self.y = self.x * y
        hasattr(y, str)


class Bar(Foo):
    
    def bla(self, z):
        print(z)


if __name__ == '__main__':
    from flexx.pyscript import script2js
    script2js(__file__, 'mymodule')
