""" Make API documentation.
Subcommands:
* html - build html
* show - show the docs in your browser
"""

import os

from make import help, DOC_DIR, DOC_BUILD_DIR
from make._sphinx import sphinx_clean, sphinx_build, sphinx_show

def doc(arg):
    
    # Prepare
    
    if not arg:
        return help('doc')
    # Go
    if 'html' == arg:
        sphinx_clean(DOC_BUILD_DIR)
        sphinx_build(DOC_DIR, DOC_BUILD_DIR)
    elif 'show' == arg:
        sphinx_show(os.path.join(DOC_BUILD_DIR, 'html'))
    else:
        sys.exit('Command "doc" does not have subcommand "%s"' % arg)
