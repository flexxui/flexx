"""
Some names that users may want to import to fool pyflakes
"""

import sys

root = '<<JS-ROOT>>'  # noqa
window = '<<JS-WINDOW>>'  # noqa

console = '<<JS-CONSOLE>>'  # noqa
document = '<<JS-DOCUMENT>>'  # noqa
module = '<<JS-MODULE>>'  # noqa
phosphor = '<<JS-PHOSPHOR>>'  # noqa
flexx = '<<JS-FLEXX>>'  # noqa

require = '<<JS-REQUIRE>>'  # noqa
typeof = '<<JS-TYPEOF>>'  # noqa

Object = '<<JS-OBJECT>>'  # noqa
Math = '<<JS-MATH>>'  # noqa
Date = '<<JS-DATE>>'  # noqa
RegExp = '<<JS-REGEXP>>'  # noqa
Infinity = float('inf')  # noqa
NaN = float('nan')  # noqa

# We'll be using "undefined" in flexx.react as well, and want to use
# the same exact object, without having dependencies.
class undefined:
    def __repr__(self):  # pragma: no cover
        return 'undefined'
undefined = sys._undefined = getattr(sys, '_undefined', undefined())  # noqa
