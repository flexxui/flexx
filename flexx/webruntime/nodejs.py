""" Web runtime based on Nodejs.

This runtime is special in that it does not provide visual output,
but it can be used to e.g. do computing in JavaScript or PyScript.

It also accepts a code attribute to provide the main "script". The url is
provided to nodejs as the ``location`` variable as it is in a browser.

When hooking this up with the flexx.app systen, nodejs and Python can
communicate via the websocket.
"""

import os
import json
import logging
import subprocess
try:
    from urllib.parse import urlparse
    from urllib.request import urlopen
except ImportError:  # Py2k
    from urlparse import urlparse
    from urllib2 import urlopen

from .common import WebRuntime


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
    if not '.' in last:
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
                    code = open(filename, 'rt').read()
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


class NodejsRuntime(WebRuntime):
    """ Web runtime based on nodejs.
    """
    
    def _launch(self):
        
        # Get code
        code = self._kwargs.get('code', None)
        if not code:
            code = get_js_from_url(self._kwargs['url'])
            # raise ValueError('Nodejs runtime needs "code" attribute.')
        
        # Handle URL
        p = urlparse(self._kwargs['url'])
        loc = json.dumps({'hostname': p.hostname, 
                          'port': str(p.port or 80), 
                          'pathname': p.path.strip('/')})
        code = ('var location = %s;\n' % loc) + code
        
        cmd = [get_node_exe(), '-e', code]
        self._start_subprocess(cmd)
