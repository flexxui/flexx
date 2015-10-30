"""
For lexing of Python code (i.e. converting Python code to a series of
tokens, the Python std has a buildin pure Python module called
tokenize.py. Alternatives would be e.g. using the lexer from Pygments.
However, tokenize is used is several places, for example in lib2to3.
"""


TEST = """
def foo(a, b, *c):
    return None

foo(a, b, c, d, *e)

""".lstrip()

import tokenize


def readline_for(text):
    x = text.splitlines()
    i = [-1]
    def func():
        i[0] += 1
        ii = i[0]
        if ii >= len(x):
            return b''
        line = x[ii].encode()
        if not line.strip():
            line = b'#EMPTYLINE'  # get rid of these later
        return line
    return func

for t in tokenize.tokenize(readline_for(TEST)):
    if t.type == tokenize.COMMENT and t.string == '#EMPTYLINE':
        continue
    print(t)
