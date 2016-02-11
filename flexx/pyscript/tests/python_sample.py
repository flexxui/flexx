"""
This file contains nearly every legal token and grammar in Python.
Taken from https://github.com/erezsh/plyplus (MIT licensed) and
modified for Python 3.3+ and 2.7.
"""

# Python 2 produces different ast for print() if print_function is not imported
from __future__ import print_function, with_statement 

# Might as well try the other imports here
import a
import a.b
import a.b.c
import a.b.c.d.e.f.g.h

import a as A
import a as A, b as B
import a.b as AB, a.b as B, a.b.c

from mod1 import mod2
from mod1.mod2 import mod3

from qmod import *
from qmod.qmod2 import *
from a1 import a1

from a import (xrt,
   yrt,
   zrt,
   zrt2)
from a import (xty,
   yty,
   zty,
   zrt2,)
from qwe import *
from qwe.wer import *
from qwe.wer.ert.rty import *

from .a import y
from ..a import y
from ..a import y as z
#from ...qwe import * This is not allowed
from ...a import (y as z, a as a2, t,)
from .................... import a,b,c  # 20 levels
from ...................... import (a,b,c)  # 22 levels

# Name constants
True
False
None

a = 2
a,b = 1, 222
a, = 1,
a, b, = 1, 234
a, b, c
1;
1;27
1;28;
1;29;3
1;21;33;
a.b
a.b.c
a.b.c.d.e.f

# Different number
0xDEADBEEF
0xDEADBEEFCAFE
0xDeadBeefCafe

1.234
10E-3
1.2e+03
-1.9e+03
9j
9.8j
23.45E-9j


# 'factor' operations
a = -1
a = +1
a = ~1
b ** c
a = + + + + 1

# 'comparison' 'comp_op' expressions
a < b
a > b
a == b
a >= b
a <= b
a != b
a in b
a is b
a not in b
a is not b

# arith_expr
1 + 2
1 + 2 + 3
1 + 2 + 3 + 4
1 - 2
1 - 2 - 3
1 - 2 + 3 - 4 + 5
# 
1 - 2 + - 3 - + 4
1 + + + + + 1

# factors
a * 1
a * 1 * 2
b / 2
b / 2 / 3
c % 9
c % 9 % 7
d // 8
d // 8 // 5

a * 1 / 2 / 3 * 9 % 7 // 2 // 1


truth or dare
war and peace
this and that or that and this
a and b and c and d
x or y or z or w
not a
not not a
not not not a
not a or not b or not c
not a or not b and not c and not d

def yield_function():
    yield
    yield 1
    x = yield

@spam.qwe
def eggs():
    pass

@spam
def eggs():
    pass

@spam.qwe()
def eggs():
    pass

@spam1.qwe()
@spam2.qwe()
@spam3.qwe()
@spam3.qwe()
def eggs():
    pass

@spam(1)
def eggs():
    pass

@spam2\
(\
)
def eggs2():
    pass


@spam3\
(\
this,\
blahblabh\
)
def eggs9():
    pass

@spam\
(
**this
)
def qweqwe():
    pass

@spam.\
and_.\
eggs\
(
**this
)
def qweqwe():
    pass


spam()
spam(1)
spam(1,2)
spam(1,2,3)
spam(1,)
spam(1,2,)
spam(1,2,3,)
spam(*a)
spam(**a)
spam(*a,**b)
spam(1, *a)
spam(1, *a, **b)
spam(1, **b)
def spam(x): pass
def spam(x,): pass
def spam(a, b): pass
def spam(a, b,): pass
def spam(a, b, c): pass
def spam(a, *args): pass
def spam(a, *args, **kwargs): pass
def spam(a, **kwargs): pass
def spam(*args, **kwargs): pass
def spam(**kwargs): pass
def spam(*args): pass

def spam(x=1): pass
def spam(x=1,): pass
def spam(a=1, b=2): pass
def spam(a=1, b=2,): pass
def spam(a=1, *args): pass
def spam(a=9.1, *args, **kwargs): pass
def spam(a="", **kwargs): pass
def spam(a,b=1, *args): pass
def spam(a,b=9.1, *args, **kwargs): pass
def spam(a,b="", **kwargs): pass

def spam(a=1, b=2, *args): pass
def spam(a=1, b=2, *args, **kwargs): pass
def spam(a=1, b=2, **kwargs): pass

def spam(a=1, b=2, c=33, d=4): pass


# This show that the compiler module uses the function name location
# for the ast.Function lineno, and not the "def" reserved word.
def \
 spam \
  ( \
  ) \
  : \
  pass

a += 1
a -= 1
a *= 2
a /= 2
a %= 3
a &= 4
a |= 4
a ^= 5
a <<= 6
a >>= 7
a **= 9
a //= 10

b \
 += \
   3

a = b = c
a = b = c = d
# Shows that the ast.Assign gets the lineno from the first '='
a \
 = \
  b \
   = \
     c

a < b < c < d < e
a == b == c != d != e

a | b | c | d
a & b & c & d
a | b | c & d & e
a ^ b
a ^ b ^ c ^ d

a << 1
a << 1 << 2
a << c() << d[1]
a >> 3
a >> 6 >> 5
a >> 6 >> 5 >> 4 >> 3
a << 1 >> 2 << 3 >> 4

del a
del a,
del a, b
del a, b,
del a, b, c
del a, b, c,
del a.b
del a.b,
del a.b.c.d.e.f
del a[0]
del a[0].b
del (a, b)
del a[:5]
del a[:5,1,2,...]
del [a,b,[c,d]]


x = ()
x = (0)
x = (a,)
# x\
#  \
# =\
# (\   <-- I put the Assign line number here
# a\
# ,\   <-- Python puts the Assign line number here
# )

def spam():
    a = (yield x)

s = "this " "is "   "string " "concatenation"
s = "so " \
   "is "  \
   "this."

#for x, in ((1,),):
#    print x

for i in range(10):
    continue
for a,b in x:
    continue
for (a,b) in x:
    break

# p_trailer_3 : LSQB subscriptlist RSQB
x[0]
x[0,]
x[0:1]
x[0:1:2]
x[:3:4]
x[::6]
x[8::9]

a[...]
a[:]
b[:9]
c[:9,]
d[-4:]
a[0]**3
c[:9,:1]
q[7:,]
q[::4,]
q[:,]
t[::2]
r[1,2,3]
r[1,2,3,]
r[1,2,3,4]
r[1,2,3,4,]
t[::]
t[::,::]
t[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
  1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
  1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
  1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
  1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
p[1,2:,3:4]
p[1,2:,3:4,5:6:7,::,:9,::2, 1:2:3,
  1,2:,3:4,5:6:7,::,:9,::2, 1:2:3]


x[1] = 1
x[1:2] = 2
x[1:] = 3
x[:1] = 4
x[:] = 5
a[1,2] = 11
a[1:2,3:4] = 12

[a] = [1]
[a] = 1,
[a,b,[c,d]] = 1,2,(3,4)


# this is an 'atom'
{}

# an atom with a dictmaker
{1:2}
{1:2,}
{1:2,3:4}
{1:2,3:4,}
{1:2,3:4,5:6}
{1:2,3:4,5:6,}
{"name": "Andrew", "language": "Python", "dance": "tango"}

# dict comprehensions
{x:x**2 for x in (1,2,3,4)}
{x:x**2 for x in (1,2,3,4) if x > 2}

# Sets
{1}
{1,}
{1,2}
{1,2,}

# Set comprehensions
{x for x in (1,2,1,3)}
{1 for c1 in s1 for c2 in s2}
{1 for c in s if c}

# Some lists
[]
[1]
[1,]
[1,2]
[1,2,]
[1,2,3,4,5,6]
[1,2,3,4,5,6,]

# List comprehensions
[1 for c in s]
[1 for c1 in s1 for c2 in s2]
[1 for c1 in s1 for c2 in s2 for c3 in s3]
[1 for c in s if c]
#TODO [(c,c2) for c in s1 if c != "n" for c2 in s2 if c2 != "a" if c2 != "e"]

[x.y for x.y in "this is legal"]

# Generator comprehensions
(1 for c in s)
(1 for c in s for d in t)

(x.y for x.y in "this is legal")
#TODO (1 for c in s if c if c+1 for d in t for e in u if d*e == c if 1 if 0)

# class definitions
class Spam:
    pass
# This shows that Python gets the line number from the 'NAME'
class \
 Spam:
    pass

class Spam: pass

class Spam(object):
    pass

class \
 Spam \
  (
   object
 ) \
 :
 pass

class Spam(): pass

class \
  Spam\
  ():
  pass

class Spam(A): pass
class Spam(A, B): pass

@dec1
class Foo: pass

@dec1
@dec2(a, b)
class Foo: pass


def a1():
    return

def a2():
    return 1,2

def a3():
    return 1,2,3

try:
    f()
except:
    pass

try:
    f()
finally:
    pass

try:
    f()
except Spam:
    a=2

try:
    f()
except (Spam, Eggs):
    a=2

# This is a Python 2.6-ism
#try:
#    f()
#except Spam as err:
#    p()

try:
    f()
except Spam as err:
    p()


try:
    f()
except Spam:
    g()
except Eggs:
    h()
except (Vikings+Marmalade) as err:
    i()

try:
    a()
except Spam: b()
except Spam2: c()
finally: g()

try:
    a()
except:
    b()
else:
    c()

try: a()
except: b()
else: c()
finally: d()

try:
    raise Fail1
except:
    raise

try:
    raise Fail2("qwer")
except:
    pass

try:
    raise Fail3("qwer", "trw23r")
except:
    pass

try:
    raise AssertionError("raise an instance")
except:
    pass

# with statements

with x1:
  1+2
with x2 as a:
  2+3
with x3 as a.b:
  9
with x4 as a[1]:
  10
with (x5,y6) as a.b[1]:
  3+4
with x7 as (a,b):
  4+5
#with x as (a+b):  # should not work
#  5+6

with x8 as [a,b,[c.x.y,d[0]]]:
  (9).__class__

# Nested
with a, b, c:
    1
with aa as a, bb as b, cc as c:
    1

# make this 'x' and get the error "name 'x' is local and global"
# The compiler module doesn't verify this correctly.  Python does
def spam(xyz):
    global z
    z = z + 1

    global x, y
    x,y=y,z

    global a, b, c
    a,b,c = b,c,a

assert 0
assert f(x)
assert f(x), "this is not right"
assert f(x), "this is not %s" % ["left", "right"][1]

if 1:
    g()

if 1: f()

if (a+1):
    f()
    g()
    h()
    pass
else:
    pass
    a()
    b()

if a:
    z()
elif b():
    y()
elif c():
    x

if a:
    spam()
elif f()//g():
    eggs()
else:
    vikings()


while 1:
    break

while a > 1:
    a -= 1
else:
    raise AssertionError("this is a problem")

for x in s:
    1/0
for (a,b) in s:
    2/0
for (a, b.c, d[1], e[1].d.f) in (p[1], t.r.e):
    f(a)
for a in b:
    break
else:
    print("b was empty")
    print("did you hear me?")

# testlist_safe
[x for x in 1]
#[x for x in 1,]  # This isn't legal
[x for x in (1,2)]
[x for x in (1,2,)]
[x for x in [1,2,3]]
[x for x in [1,2,3,]]

#[x for x in lambda :2]
#[x for x in lambda x:2*x]  # bug in compiler.transfomer prevents
#[x for x in lambda x,y:x*y]  # testing "safe" lambdas with arguments
#[x for x in lambda x,y=2:x*y]

lambda x: 5 if x else 2
#TODO: [ x for x in lambda: True, lambda: False if x() ]
#[ x for x in lambda: True, lambda: False if x else 2 ]


x = 1 if a else 2
y = 1 if a else 2 if b else 3

func = lambda : 1
func2 = lambda x, y: x+y
func3 = lambda x=2, y=3: x*y


f(1)
f(1,)
f(1,2)
f(1,2,)
f(1,2,3)
f(1,2,3,)
f(1,2,3,4)
f(1,2,3,4,)
f(a=1)
f(a=1,)
f(a=1, b=2)
f(a=1, b=2,)
f(a=1, b=2, c=3)
f(a=1, b=2, c=3,)
f(9, a=1)
f(9, a=1,)
f(9, a=1, b=2)
f(9, a=1, b=2,)
f(9, 8, a=1)
f(9, 7, a=1, b=2)

f(c for c in s)
f(x=2)
f(x, y=2)
f(x, *args, **kwargs)

#f(x+y=3)

## check some line number assignments.  Python's compiler module uses
## the first term inside of the bracket/parens/braces.  I prefer the
## line number of the first character (the '[', '(', or '{')

x = [


  "a", "b",
  # comment
  "c", "d", "e", "f"


]

y = (

  c for c in s)

def f():
  welk = (



      yield
      )

d = {


  "a":
 1,
  101: 102,
  103: 104}

# Check all the different ways of escaping and counting line numbers

"""
This text
goes over
various
lines.
"""

# this should have the right line number
x_triple_quoted = 3

'''
blah blah
and
blah
'''

# this should have the right line number
y_triple_quoted = 34

r"""
when shall we three meet again
"""

# this should have the right line number
z_triple_quoted = 3235

r'''
This text
goes over
various
lines.
'''

# this should have the right line number
x_triple_quoted = 373

u"""
When in the
course of human
events
"""

# this should have the right line number
x_triple_quoted = 65

r'''
We hold these truths to be self-evident
'''

# this should have the right line number
y_triple_quoted = 3963


# Check the escaping for the newline
s1 = r'''
  This
has a newline\
and\
a\
few
more

'''

1

s1 = r"""
Some more \
with\
newlines

"""

# Pypy tests fails on these
# str123 = 'single quoted line\
# line with embedded\
# newlines.'
# 
# str367 = "another \
# with \
# embedded\
# newlines."


u"\N{LATIN SMALL LETTER ETH}"
r"\N{LATIN SMALL LETTER ETH}"

f(1
 +
 2)

b'some bytes'
b"some bytes"

# Pypy injects /r/n in multiline strings on Windows, arg
# b'''some
# bytes
# '''
# b"""some
# bytes
# """

# print "The end"
