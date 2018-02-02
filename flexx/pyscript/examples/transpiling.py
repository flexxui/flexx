"""
Example to demonstrate simple transpiling and evaluating.
"""

from flexx.pyscript import py2js, evaljs, evalpy

def foo(a, b=1, *args):
    print(a)
    return b

# Create jscode object
jscode = py2js(foo)

# Print some info that we have on the code
print(jscode.meta['filename'])
print(jscode.meta['pycode'])
print(jscode)

# Convert strings of Python to JS
print(py2js('isinstance(x, str)'))
print(py2js('isinstance(x, Bar)'))

# Evaluate js in nodejs
print(evaljs('10 * 10'))

# Evaluate PyScript in nodejs
print(evalpy('10**10'))
