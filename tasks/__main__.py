"""
Make this module itself executable as an alias for invoke.
"""

import sys
import subprocess

cmd = ['invoke']
if len(sys.argv) == 1:
    cmd.append('help')
else:
    cmd.extend(sys.argv[1:])

subprocess.check_call(cmd)
