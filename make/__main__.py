# License: consider this public domain

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(__file__, '..', '..'))

# Import make - clean up to avoid side-effects
sys.path.insert(0, ROOT_DIR)
import make
sys.path.pop(0)
if 'make' in sys.path:
    sys.path.remove('make')

make.main()
