# -*- coding: utf-8 -*-

""" Flexx setup script.

Release:

* bump __version__
* python setup.py register
* python setup.py sdist bdist_wheel --universal upload
* build conda packages?

"""

import os

try:
    # use setuptools namespace, allows for "develop"
    import setuptools  # noqa, analysis:ignore
except ImportError:
    pass  # it's not essential for installation
from distutils.core import setup

name = 'flexx'
description = "Pure Python toolkit for creating GUI's using web technology."


# Get version and docstring
__version__ = None
__doc__ = ''
docStatus = 0  # Not started, in progress, done
initFile = os.path.join(os.path.dirname(__file__), name, '__init__.py')
for line in open(initFile, 'rt', encoding='utf-8').readlines():
    if (line.startswith('version_info') or line.startswith('__version__')):
        exec(line.strip())
    elif line.startswith('"""'):
        if docStatus == 0:
            docStatus = 1
            line = line.lstrip('"')
        elif docStatus == 1:
            docStatus = 2
    if docStatus == 1:
        __doc__ += line


def package_tree(pkgroot):
    path = os.path.dirname(__file__)
    subdirs = [os.path.relpath(i[0], path).replace(os.path.sep, '.')
               for i in os.walk(os.path.join(path, pkgroot))
               if '__init__.py' in i[2]]
    return subdirs


# Define dependencies per subpackage
extras_require = {'app': ['tornado']}
extras_require['ui'] = extras_require['app']
extras_require['all'] = [i for ii in extras_require.values() for i in ii]


setup(
    name=name,
    version=__version__,
    author='Flexx contributors',
    author_email='almar.klein@gmail.com',
    license='(new) BSD',
    url='http://flexx.readthedocs.org',
    download_url='https://pypi.python.org/pypi/flexx',
    keywords="ui design, web runtime, pyscript, reactive programming, FRP",
    description=description,
    long_description=__doc__,
    platforms='any',
    provides=[name],
    install_requires=[],  # react, pyscript and webruntime require nothing
    extras_require=extras_require,
    packages=package_tree(name),
    package_dir={name: name},
    package_data={'flexx': ['resources/*']},
    entry_points={'console_scripts': ['flexx = flexx.__main__'], },
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        #'Programming Language :: Python :: 2.7',  # not yet supported
        'Programming Language :: Python :: 3.4',
    ],
)
