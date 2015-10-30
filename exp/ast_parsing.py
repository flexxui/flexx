"""
Playing with ast parsing via lib2to3. A pure Python implementation of
a Python ast parser is a necesary towards PyScript being able to compile
itself.

There are also some downsides:
* there is no readily available pure Python lib available for ast
  parsing. lib2to3 seems to come close, but will need some processing
  to get the higher level ast tree that the ast module provides
* probably want to copy the relevant bits from libpy2to and tweak them
  to our use-case, but this will add a maintenance burden.
* pure Python ast parsing is significantly slower (about 20-30x). This
  can easily mean the difference between being able to produce JS during import
  time or not.

Decision for now is to use ast module, but convert that to our own ast
tree definition. This means that all the gory details wrt making all
Python versions/implementations compatible are constrained to a single
place, and can all be extensively tested. This approach also keeps the
door open for alternative parsers to produce such an ast tree, and such
parsers can easily be tested for compliance.

An alternative ast parser could be to take tokens and produce ast by
"manually" parsing with if-statements rather than defining a grammar
and using that to generate a parser. But this may also be my naive self
talking.
"""

TEST = """
aap = bar = 2 or 3
aap += 2
def foo(a, b, *c):
    return None

foo(a, b, c, d, *e)
# 1 < a < 3
""" #.lstrip()

import time
import ast

N = 1  # increase this to say 100 for more representative speed tests
TEST = TEST * N

from lib2to3 import pygram, pgen2, pytree

driver = pgen2.driver.Driver(pygram.python_grammar_no_print_statement, convert=pytree.convert)

t0 = time.time()
r1 = driver.parse_string(TEST)
t1 = time.time()-t0


t0 = time.time()
r2 = ast.parse(TEST)
t2 = time.time()-t0

print(repr(r1))
print()
print('Parsing with lib2to3 took', t1)
print('Parsing with ast module took', t2)
print('Parsing in pure Python is %1.1f times slower' % (t1 / t2))


##

from lib2to3 import pygram

symbols = []
for name, nr in pygram.python_symbols.__dict__.items():
    symbols.append((nr, name))
symbols.sort()
for nr, name in symbols:
    print(nr, name)