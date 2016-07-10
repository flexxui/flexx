""" 
Functionality to ensure up-to-date versions of resources. This module
must be able to run standalone, since it will be used from setup.py to
pack resources in dist packages.
"""

from __future__ import absolute_import, print_function, division

import os

try:
    from .logging import logger
except Exception:
    import logging
    logger = logging.getLogger('getresource')
    logger.setLevel(logging.INFO)

try:
    from urllib.request import urlopen
except ImportError:
    try:
        from urllib2 import urlopen  # Legacy Python
    except ImportError:
        raise RuntimeError('Could not import urlopen.')


def get_resoure_filename(tagfile):
    """ Get the filename for a resource, corresponding to the given
    tagfile. The tagfile should consist of two line: the url of the
    resource and a tag (used for versioning). Will use cached version
    if available. Otherwise will download and cache.
    """
    # Get location of tag file (i.e. the file that says where the source is)
    dest = os.path.abspath(os.path.join(__file__, '..', '..', 'resources'))
    tagfilename = os.path.join(dest, tagfile)

    if not os.path.isdir(dest):
        raise ValueError('Resource dest dir %r is not a directory.' % dest)
    if not os.path.isfile(tagfilename):
        raise ValueError('Resource tag file %r is not a valid file.' % tagfile)
    
    # Get url
    url = open(tagfilename, 'rb').read().decode('utf-8').strip()
    if not url.count('\n') == 1:
        raise ValueError('The tag file should consists of two lines: a url and a tag.')
    url, tag = [x.strip() for x in url.split('\n')]
    
    # Filename for downloaded file
    baseame, ext, _ = tagfile.rsplit('.', 2)
    filename = os.path.join(dest, baseame + '.' + tag + '.' + ext)
    
    # Download if needed
    if not os.path.isfile(filename):
        data = _fetch_file(url)
        with open(filename, 'wb') as f:
            f.write(data)
    
    return filename


def get_resource(tagfile):
    """ Get the bytes of the resource corresponding to the given
    tagfile.
    """
    return open(get_resoure_filename(tagfile), 'rb').read()


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
    get_resource('phosphor-all.js.tag')
