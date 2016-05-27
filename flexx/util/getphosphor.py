""" 
Functionality to ensure an up-to-date version of PhosphorJS on the
system. This depends on the phosphor-all package to provide an on-line
resource of Phosphor.
"""

import os
from .logging import logger
from urllib.request import urlopen

# todo: maybe this should be more generic; download a variety of JS libs (e.g. react)

FNAME = 'phosphor-all.%s.js'
URL = 'http://raw.githubusercontent.com/zoofIO/phosphor-all/%s/phosphor-all.js'


def get_phosphor(commit):
    """ Get the source for the phosphor JS module, corresponding to the
    given commit. Will use cached version if possible. Otherwise will
    download from GitHub and cache.
    """
    
    dest = os.path.abspath(os.path.join(__file__, '..', '..', 'resources'))
    filename = os.path.join(dest, FNAME % commit)
    url = URL % commit
    
    if not os.path.isdir(dest):
        raise ValueError('Phosphor dest dir %r is not a directory.' % dest)
    if not os.path.isfile(filename):
        data = _fetch_file(url)
        with open(filename, 'wb') as f:
            f.write(data)
    
    return open(filename, 'rb').read().decode()


def _fetch_file(url):
    """ Fetches a file from the internet. Retry a few times before
    giving up on failure.
    """
    logger.info('Downloading %s' % url)
    for tries in range(4):
        try:
            return urlopen(url, timeout=5.0).read()
        except Exception as e:
            logger.warn('Error while fetching file: %s' % str(e))
    raise IOError('Unable to download %r. Perhaps there is a no internet '
                  'connection? If there is, please report this problem.' % url)


if __name__ == '__main__':
    # Note that the commit id must be updated in ui/__init__.py
    get_phosphor('xxx')
