# -*- coding: utf-8 -*-

""" Flexx setup script.

Release:

* bump __version__
* python setup.py register
* python setup.py sdist bdist_wheel --universal upload
* build conda packages?

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
    __version__, __doc__ = None, ''
    docStatus = 0  # Not started, in progress, done
    for line in open(filename, 'rb').read().decode().splitlines():
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
    return __version__, __doc__


def package_tree(pkgroot):
    subdirs = [os.path.relpath(i[0], THIS_DIR).replace(os.path.sep, '.')
               for i in os.walk(os.path.join(THIS_DIR, pkgroot))
               if '__init__.py' in i[2]]
    return subdirs


def copy_for_legacy_python(src_dir, dest_dir):
    
    if sys.argv[1:] != ['install']:
        raise RuntimeError('Setup.py can only be used to "install" on Python 2.x')
    
    # todo: usefull error if lib3to2 is not there
    from lib3to2.main import main
    
    ignore_dirs = ['__pycache__']
    ignores = ['pyscript/tests/python_sample.py', 
               'pyscript/tests/python_sample2.py',
               'pyscript/tests/python_sample3.py']
    
    # Make a copy of the flexx package
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir,
                    ignore=lambda src, names: [n for n in names if n in ignore_dirs])
    for fname in ignores:
        os.remove(os.path.join(dest_dir, fname))
    
    # Convert code inplace
    main("lib3to2.fixes", ['--fix', 'all', '--fix', 'printfunction', '--nofix', 'print', '--write', '--nobackups', '--no-diffs', dest_dir])
    
    # Copy originals of the files we wanted to ignore
    for fname in ignores:
        shutil.copy(os.path.join(src_dir, fname), os.path.join(dest_dir, fname))
    
    # Apply some very specific fixes
    fixes = [("react/hassignals.py", "u'temporary_class'", "'temporary_class'"),
            ]
    for fname, needle, rep in fixes:
        filename = os.path.join(dest_dir, fname)
        code = open(filename, 'rb').read().decode()
        code = code.replace(needle, rep)
        with open(filename, 'wb') as f:
            f.write(code.encode())
    
    #sys.exit()


## Collect info for setup()

THIS_DIR = os.path.dirname(__file__)

# Define name and description
name = 'flexx'
description = "Pure Python toolkit for creating GUI's using web technology."

# Get version and docstring (i.e. long description)
version, doc = get_version_and_doc(os.path.join(THIS_DIR, name, '__init__.py'))

# Define dependencies per subpackage
extras_require = {'app': ['tornado']}
extras_require['ui'] = extras_require['app']
extras_require['all'] = [i for ii in extras_require.values() for i in ii]

# Get directory to install
package_dir = name
if sys.version_info[0] == 2:
    package_dir += '_legacy_py'
    copy_for_legacy_python(os.path.join(THIS_DIR, name),
                           os.path.join(THIS_DIR, package_dir))


## Setup

setup(
    name=name,
    version=version,
    author='Flexx contributors',
    author_email='almar.klein@gmail.com',
    license='(new) BSD',
    url='http://flexx.readthedocs.org',
    download_url='https://pypi.python.org/pypi/flexx',
    keywords="ui design, web runtime, pyscript, reactive programming, FRP",
    description=description,
    long_description=doc,
    platforms='any',
    provides=[name],
    install_requires=[],  # react, pyscript and webruntime require nothing
    extras_require=extras_require,
    packages=package_tree(name),
    package_dir={name: package_dir},
    package_data={'flexx': ['resources/*']},
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
