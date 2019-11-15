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

def get_version(filename):
    NS = dict(__version__='')
    for line in open(filename, 'rb').read().decode().splitlines():
        if line.startswith('__version__'):
            exec(line.strip(), NS, NS)
    if not NS['__version__']:
        raise RuntimeError('Could not find __version__')
    return NS['__version__']


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
version = get_version(os.path.join(THIS_DIR, name, '__init__.py'))
with open('README.md') as read_me:
    long_description = read_me.read()

# Install resources (e.g. phosphor.js)
get_all_resources()

## Setup

setup(
    name=name,
    version=version,
    author='Flexx contributors',
    author_email='almar.klein@gmail.com',
    license='(new) BSD',
    url='https://github.com/flexxui/flexx',
    project_urls={
        'Documentation': 'https://flexx.readthedocs.io/en/stable/',
    },
    download_url='https://pypi.python.org/pypi/flexx',
    keywords="ui design, GUI, web, runtime, pyscript, events, properties",
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
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
