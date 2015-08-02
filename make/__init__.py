# License: consider this public domain

"""
Convenience tools for developers

    python make command [arg]

This file defines the project-specific variables.
"""

import os.path as op

# Get root directory of the package
THIS_DIR = op.dirname(op.abspath(__file__))
ROOT_DIR = op.dirname(THIS_DIR)

# Definions - these change per project
NAME = 'flexx'
DOC_DIR = op.join(ROOT_DIR, 'docs')
DOC_BUILD_DIR = op.join(DOC_DIR, '_build')
