""" Web runtime based on Nodejs.

This runtime is special in that it does not provide visual output,
but it can be used to e.g. do computing in JavaScript or PyScript.
"""

import logging
import subprocess

from .common import WebRuntime


class NodejsRuntime(WebRuntime):
    """ Web runtime based on nodejs.
    """
    
    def _launch(self):
        
        if self._kwargs['url']:
            logging.info('Ignoring URL for nodejs runtime.')
        
        cmd = ["nodejs", "-i"]
        self._start_subprocess(cmd, stdin=subprocess.PIPE)
    
    def run_code(self, code):
        """ Run code in the Nodejs process.
        """
        self._proc.stdin.write(code.encode())
        self._proc.stdin.write(b'\n')
        self._proc.stdin.flush()
