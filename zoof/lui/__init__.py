"""
This package is an experiment to create a lightweight, cross-platform,
pure Python, UI toolkit. It is based on GLFW (which is real small), and
uses OpenGL to render glyphs that are stored in a precomputed atlas.
This library should be able to work on Windows, OSX, Linux, Raspberry
Pi, and maybe more.

The motivation is that if we create a sophisticated GUI toolit based
on HTML5, we need a "browser", and shipping that with each app that is
made with it seems stupid. Instead, it should make of e.g. firefox, or
another "runtime". This means, however, that we need a way to
communicate with the user when such a runtime is not (yet) available,
for instance to *tell* the user that a runtime is needed and to aks
him/her whether it should be downloaded now.

In terms of alternatives: Qt/wx/gtk are too big, tk does not work on
OSX, fltk might be an option, but it's still a hard to get by dependency ...



"""

from .gllib import gl
from .tex import Tex
from .widgets import Label
