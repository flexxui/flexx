# -*- coding: utf-8 -*-

"""
Flexx setup script.
"""

import os
import sys
import shutil

try:
    import setuptools  # noqa, analysis:ignore
except ImportError:
    pass  # setuptools allows for "develop", but it's not essential

from distutils.core import setup


## Function we need

def get_version_and_doc(filename):
    NS = dict(__version__='', __doc__='')
    docStatus = 0  # Not started, in progress, done
    for line in open(filename, 'rb').read().decode().splitlines():
        if line.startswith('__version__'):
            exec(line.strip(), NS, NS)
        elif line.startswith('"""'):
            if docStatus == 0:
                docStatus = 1
                line = line.lstrip('"')
            elif docStatus == 1:
                docStatus = 2
        if docStatus == 1:
            NS['__doc__'] += line.rstrip() + '\n'
    if not NS['__version__']:
        raise RuntimeError('Could not find __version__')
    return NS['__version__'], NS['__doc__']


def get_readme_as_rst(filename):
    lines = []
    for line in open(filename, 'rb').read().decode().splitlines():
        lines.append(line)
        # Convert links, images, and images with links
        i1, i2 = line.find('['), line.find(']')
        i3, i4 = line.find('(', i2), line.find(')', i2)
        i5, i6 = line.find('(', i4), line.find(')', i4+1)
        if '[Documentation Status' in line:
            line.find('x')
        if i1 >=0 and i2 > i1 and i3 == i2 + 1 and i4 > i3:
            text, link = line[i1+1:i2], line[i3+1:i4]
            if i1 == 1 and line[0] == '!':
                # Image
                lines[-1] = '\n.. image:: %s\n' % link
            elif i1 == 0 and line.startswith('[![') and i5 == i4 + 2 and i6 > i5:
                # Image with link
                link2 = line[i5+1:i6]
                lines[-1] = '\n.. image:: %s\n    :target: %s\n' % (link, link2)
            else:
                # RST link: `link text </the/link>`_
                lines[-1] = '%s`%s <%s>`_%s' % (line[:i1], text, link, line[i4+1:])
    return '\n'.join(lines)


def package_tree(pkgroot):
    subdirs = [os.path.relpath(i[0], THIS_DIR).replace(os.path.sep, '.')
               for i in os.walk(os.path.join(THIS_DIR, pkgroot))
               if '__init__.py' in i[2]]
    return subdirs


def get_all_resources():
    import logging  # noqa - prevent mixup with logging module inside flexx.util
    sys.path.insert(0, os.path.join(THIS_DIR, 'flexx', 'util'))
    from getresource import RESOURCES, get_resoure_path
    for name in RESOURCES.keys():
        get_resoure_path(name)
    sys.path.pop(0)


## Collect info for setup()

THIS_DIR = os.path.dirname(__file__)

# Define name and description
name = 'flexx'
description = "Write desktop and web apps in pure Python."

# Get version and docstring (i.e. long description)
version, doc = get_version_and_doc(os.path.join(THIS_DIR, name, '__init__.py'))
if os.path.isfile(os.path.join(THIS_DIR, 'README.md')):
    doc = get_readme_as_rst(os.path.join(THIS_DIR, 'README.md'))

# Install resources (e.g. phosphor.js)
get_all_resources()


## Setup

setup(
    name=name,
    version=version,
    author='Flexx contributors',
    author_email='almar.klein@gmail.com',
    license='(new) BSD',
    url='http://flexx.readthedocs.io',
    download_url='https://pypi.python.org/pypi/flexx',
    keywords="ui design, GUI, web, runtime, pyscript, events, properties",
    description=description,
    long_description=doc,
    platforms='any',
    provides=[name],
    python_requires='>=3.5',
    install_requires=['tornado', 'pscript>=0.7.1', 'webruntime>=0.5.6', 'dialite>=0.5.2'],
    packages=package_tree('flexx') + package_tree('flexxamples'),
    package_dir={'flexx': 'flexx', 'flexxamples': 'flexxamples'},
    package_data={name: ['resources/*']},
    entry_points={'console_scripts': ['flexx = flexx.__main__:main'], },
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
