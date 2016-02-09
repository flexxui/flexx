""" Web runtime based on Nodejs.

This runtime is special in that it does not provide visual output,
but it can be used to e.g. do computing in JavaScript or PyScript.

It also accepts a code attribute to provide the main "script". The url is
provided to nodejs as the ``location`` variable as it is in a browser.

When hooking this up with the flexx app systen, nodejs and Python can
communicate via the websocket.
"""

import os
import sys
import json
import subprocess
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen

from .common import BaseRuntime


NODE_EXE = None
def get_node_exe():
    """ Small utility that provides the node exe. The first time this
    is called both 'nodejs' and 'node' are tried. To override the
    executable path, set the ``FLEXX_NODE_EXE`` environment variable.
    """
    # This makes things work on Ubuntu's nodejs as well as other node
    # implementations, and allows users to set the node exe if necessary
    global NODE_EXE
    NODE_EXE = os.getenv('FLEXX_NODE_EXE') or NODE_EXE
    if NODE_EXE is None:
        NODE_EXE = 'nodejs'
        try:
            subprocess.check_output([NODE_EXE, '-v'])
        except Exception:
            NODE_EXE = 'node'
    return NODE_EXE



def get_js_from_url(url):
    """ Given an url, extract the JavaScript. This abviously does not
    work when this process/thread is the actually serving that url.
    """
    html = urlopen(url, timeout=5.0).read().decode()
    root, last = url.rsplit('/', 1)
    if '.' not in last:
        root += '/' + last
    return get_js_from_html(html, root)


def get_js_from_html(html, root):
    """ Given an html document provided as a string, extract the
    JavaScript.
    """
    parts = []
    i = 0
    while True:
        i = html.find('<script', i)
        if i < 0 or i > len(html) - 5:
            break
        i_end1 = html.find('>', i+6)
        i_end2 = html.find('/>', i+6)
        i_end3 = html.find('</script>', i+6)
        i_src = html.find('src=', i+6)
        ends = [j for j in (i_end2, i_end3) if j > 0]
        if not ends:
            break
        i_end = min(ends)
        i = i_end  # prepare for next round
        
        if i_src > 0 and i_src < i_end1:
            # Get filename
            i1 = i_src + 5
            quote = html[i1-1]
            if quote not in '"\'':
                continue
            i2 = html.find(quote, i1)
            fname = html[i1:i2]
            # Get JS
            for filename in (fname, root + '/' + fname):
                if filename.startswith('http'):
                    code = urlopen(filename, timeout=5.0).read().decode()
                    break
                elif os.path.isfile(filename):
                    code = open(filename, 'rb').read().decode()
                    break
            else:
                raise IOError('Could not get JS for file %r' % fname)
            parts.append(code)
        elif i_end == i_end3 and i_end > i_end1:
            i1 = i_end1 + 1
            i2 = i_end
            parts.append(html[i1:i2])
        else:
            pass  # malformed tags or empty script tag
    
    return '\n'.join(parts)


class NodejsRuntime(BaseRuntime):
    """ Runtime for nodejs ((http://nodejs.org), which is based on
    Chrome's V8 JavaScript engine. No UI, for computations and testing
    only. Requires nodejs to be installed .
    
    The uri argument is not used in the same way as in the other
    runtimes, because nodejs does not deal with HTML. The uri is only
    used to create a ``location`` object for compatibility with
    browsers.
    
    Arguments:
      code (str): The code to run.
    """
    
    def _launch(self):
        
        # Get code
        code = self._kwargs.get('code', None)
        if not code:
            code = get_js_from_url(self._kwargs['url'])
            # raise ValueError('Nodejs runtime needs "code" attribute.')
        
        # Handle URL
        url = self._kwargs['url']
        if url.startswith('file://'):
            loc = json.dumps({'hostname': '', 'port': '',
                              'pathname': url.split('//', 1)[1]})
        else:
            p = urlparse(url)
            loc = json.dumps({'hostname': p.hostname, 
                              'port': str(p.port or 80), 
                              'pathname': p.path.strip('/')})
        code = ('var location = %s;\n' % loc) + code
        
        # Fix for Windows - by default global modules are searched in wrong place
        NODE_PATH = b'NODE_PATH' if sys.version_info[0] == 2 else 'NODE_PATH'
        if sys.platform.startswith('win') and os.getenv(NODE_PATH) is None:
            os.environ[NODE_PATH] = os.getenv('APPDATA') + '\\npm\\node_modules'
        elif sys.platform.startswith('linux') and not os.getenv(NODE_PATH):
            path = os.path.expanduser('/usr/local/lib/node_modules')
            if os.path.isdir(path):
                os.environ[NODE_PATH] = path
        if sys.version_info[0] == 2 and os.getenv(NODE_PATH):  # str lits are uni
            os.environ[NODE_PATH] = os.environ[NODE_PATH].encode()
        
        # Write code to tempfile
        f = tempfile.NamedTemporaryFile('wt', prefix='flexx_nodejs_', suffix='.js')
        f.file.write(code)
        f.file.flush()
        self._code_file = f  # keep a reference to prevent deletion too soon
        
        # Launch
        cmd = [get_node_exe(), f.name]
        self._start_subprocess(cmd)
