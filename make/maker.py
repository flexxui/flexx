#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014, Zoof Development Team
# Distributed under the (new) BSD License. 

# Originally developed under the Vispy project.

"""
Convenience tools for Zoof developers

    python make command [arg]

"""

from __future__ import division, print_function

import sys
import os
from os import path as op
import time
import shutil
import subprocess
import re
import webbrowser
import traceback


# Save where we came frome and where this module lives
START_DIR = op.abspath(os.getcwd())
THIS_DIR = op.abspath(op.dirname(__file__))

# Get root directory of the package, by looking for setup.py
for subdir in ['.', '..']:
    ROOT_DIR = op.abspath(op.join(THIS_DIR, subdir))
    if op.isfile(op.join(ROOT_DIR, 'setup.py')):
        break
else:
    sys.exit('Cannot find root dir')


# Define directories and repos of interest
DOC_DIR = op.join(ROOT_DIR, 'doc')
#
WEBSITE_DIR = op.join(ROOT_DIR, '_website')
WEBSITE_REPO = 'git@github.com:zoofIO/zoof-website'
#
PAGES_DIR = op.join(ROOT_DIR, '_gh-pages')
PAGES_REPO = 'git@github.com:zoofIO/zoofIO.github.io.git'


class Maker:
    """ Collection of make commands.

    To create a new command, create a method with a short name, give it
    a docstring, and make it do something useful :)

    """

    def __init__(self, argv):
        """ Parse command line arguments. """
        # Get function to call
        if len(argv) == 1:
            func, arg = self.help, ''
        else:
            command = argv[1].strip()
            arg = ' '.join(argv[2:]).strip()
            func = getattr(self, command, None)
        # Call it if we can
        if func is not None:
            func(arg)
        else:
            sys.exit('Invalid command: "%s"' % command)

    def coverage_html(self, arg):
        """Generate html report from .coverage and launch"""
        print('Generating HTML...')
        from coverage import coverage
        cov = coverage(auto_data=False, branch=True, data_suffix=None,
                       source=['zoof'])  # should match testing/_coverage.py
        cov.load()
        cov.html_report()
        print('Done, launching browser.')
        fname = op.join(os.getcwd(), 'htmlcov', 'index.html')
        if not op.isfile(fname):
            raise IOError('Generated file not found: %s' % fname)
        webbrowser.open_new_tab(fname)

    def help(self, arg):
        """ Show help message. Use 'help X' to get more help on command X. """
        if arg:
            command = arg
            func = getattr(self, command, None)
            if func is not None:
                doc = getattr(self, command).__doc__.strip()
                print('make %s [arg]\n\n        %s' % (command, doc))
                print()
            else:
                sys.exit('Cannot show help on unknown command: "%s"' % command)

        else:
            print(__doc__.strip() + '\n\nCommands:\n')
            for command in sorted(dir(self)):
                if command.startswith('_'):
                    continue
                preamble = command.ljust(11)  # longest command is 9 or 10
                # doc = getattr(self, command).__doc__.splitlines()[0].strip()
                doc = getattr(self, command).__doc__.strip()
                print(' %s  %s' % (preamble, doc))
            print()

    def _doc(self, arg):
        """ Make API documentation. Subcommands:
                * html - build html
                * show - show the docs in your browser
        """
        # Prepare
        build_dir = op.join(DOC_DIR, '_build')
        if not arg:
            return self.help('doc')
        # Go
        if 'html' == arg:
            sphinx_clean(build_dir)
            sphinx_build(DOC_DIR, build_dir)
        elif 'show' == arg:
            sphinx_show(op.join(build_dir, 'html'))
        else:
            sys.exit('Command "doc" does not have subcommand "%s"' % arg)

    def website(self, arg):
        """ Build website. Website source is put in '_website'. Subcommands:
                * html - build html
                * show - show the website in a util that allows quick rebuild
                * browser - show the website in your browser
                * upload - upload (commit+push) the resulting html to github
        """
        # Prepare
        build_dir = op.join(WEBSITE_DIR, '_build')
        html_dir = op.join(build_dir, 'html')

        # Clone repo for website if needed, make up-to-date otherwise
        if not op.isdir(WEBSITE_DIR):
            os.chdir(ROOT_DIR)
            sh("git clone %s %s" % (WEBSITE_REPO, WEBSITE_DIR))
        else:
            print('Updating website repo')
            os.chdir(WEBSITE_DIR)
            sh('git pull')

        if not arg:
            return self.help('website')

        # Go
        if 'html' == arg:
            sphinx_clean(build_dir)
            sphinx_build(WEBSITE_DIR, build_dir)
            sphinx_copy_pages(html_dir, PAGES_DIR, PAGES_REPO)
        elif 'show' == arg:
            from make import showwebsite
            showwebsite.main()
        elif 'browser' == arg:
            sphinx_show(PAGES_DIR)
        elif 'upload' == arg:
            sphinx_upload(PAGES_DIR)
            print()
            print(
                "Do not forget to also commit+push your changes to '_website'")
        else:
            sys.exit('Command "website" does not have subcommand "%s"' % arg)

    def _test(self, arg):
        """ Run tests:
                * unit - run unit tests
                * style - flake style testing (PEP8 and more)
        """
        if not arg:
            return self.help('test')
        from zoof import test
        try:
            args = arg.split(' ')
            test(args[0], ' '.join(args[1:]))
        except Exception as err:
            print(err)
            if not isinstance(err, RuntimeError):
                type_, value, tb = sys.exc_info()
                traceback.print_exception(type, value, tb)
            raise SystemExit(1)
    
    def copyright(self, arg):
        """ Update all copyright notices to the current year.
        """
        # Initialize
        TEMPLATE = "# Copyright (c) %i, Zoof Development Team."
        CURYEAR = int(time.strftime('%Y'))
        OLDTEXT = TEMPLATE % (CURYEAR - 1)
        NEWTEXT = TEMPLATE % CURYEAR
        # Initialize counts
        count_ok, count_replaced = 0, 0

        # Processing the whole root directory
        for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
            # Check if we should skip this directory
            reldirpath = op.relpath(dirpath, ROOT_DIR)
            if reldirpath[0] in '._' or reldirpath.endswith('__pycache__'):
                continue
            if op.split(reldirpath)[0] in ('build', 'dist'):
                continue
            # Process files
            for fname in filenames:
                if not fname.endswith('.py'):
                    continue
                # Open and check
                filename = op.join(dirpath, fname)
                text = open(filename, 'rt').read()
                if NEWTEXT in text:
                    count_ok += 1
                elif OLDTEXT in text:
                    text = text.replace(OLDTEXT, NEWTEXT)
                    open(filename, 'wt').write(text)
                    print(
                        '  Update copyright year in %s/%s' %
                        (reldirpath, fname))
                    count_replaced += 1
                elif 'copyright' in text[:200].lower():
                    print(
                        '  Unknown copyright mentioned in %s/%s' %
                        (reldirpath, fname))
        # Report
        print('Replaced %i copyright statements' % count_replaced)
        print('Found %i copyright statements up to date' % count_ok)


# Functions used by the maker

if sys.version_info[0] < 3:
    input = raw_input  # noqa


def sh(cmd):
    """Execute command in a subshell, return status code."""
    return subprocess.check_call(cmd, shell=True)


def sh2(cmd):
    """Execute command in a subshell, return stdout.
    Stderr is unbuffered from the subshell."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out = p.communicate()[0]
    retcode = p.returncode
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd)
    else:
        return out.rstrip().decode('utf-8', 'ignore')


def sphinx_clean(build_dir):
    if op.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.mkdir(build_dir)
    print('Cleared build directory.')


def sphinx_build(src_dir, build_dir):
    import sphinx
    
    try:
        ret = 0
        ret = sphinx.main(('sphinx-build',  # Dummy
                        '-b', 'html',
                        '-d', op.join(build_dir, 'doctrees'),
                        src_dir,  # Source
                        op.join(build_dir, 'html'),  # Dest
                        ))
    except SystemExit:
        pass
    if ret != 0:
        raise RuntimeError('Sphinx error: %s' % ret)
    print("Build finished. The HTML pages are in %s/html." % build_dir)


def sphinx_show(html_dir):
    index_html = op.join(html_dir, 'index.html')
    if not op.isfile(index_html):
        sys.exit('Cannot show pages, build the html first.')
    import webbrowser
    webbrowser.open_new_tab(index_html)


def sphinx_copy_pages(html_dir, pages_dir, pages_repo):
    print('COPYING PAGES')
    # Create the pages repo if needed
    if not op.isdir(pages_dir):
        os.chdir(ROOT_DIR)
        sh("git clone %s %s" % (pages_repo, pages_dir))
    # Ensure that its up to date
    os.chdir(pages_dir)
    sh('git checkout master -q')
    sh('git pull -q')
    os.chdir('..')
    # This is pretty unforgiving: we unconditionally nuke the destination
    # directory, and then copy the html tree in there
    tmp_git_dir = op.join(ROOT_DIR, pages_dir + '_git')
    shutil.move(op.join(pages_dir, '.git'), tmp_git_dir)
    try:
        shutil.rmtree(pages_dir)
        shutil.copytree(html_dir, pages_dir)
        shutil.move(tmp_git_dir, op.join(pages_dir, '.git'))
    finally:
        if op.isdir(tmp_git_dir):
            shutil.rmtree(tmp_git_dir)
    # Copy individual files
    for fname in ['CNAME']:  # 'README.md', 'conf.py', '.nojekyll', 'Makefile'
        if op.isfile(op.join(WEBSITE_DIR, fname)):
            shutil.copyfile(op.join(WEBSITE_DIR, fname),
                            op.join(pages_dir, fname))
    # Messages
    os.chdir(pages_dir)
    sh('git status')
    print()
    print("Website copied to _gh-pages. Above you can see its status:")
    print("  Run 'make website show' to view.")
    print("  Run 'make website upload' to commit and push.")


def sphinx_upload(repo_dir):
    # Check head
    os.chdir(repo_dir)
    status = sh2('git status | head -1')
    branch = re.match('On branch (.*)$', status).group(1)
    if branch != 'master':
        e = 'On %r, git branch is %r, MUST be "master"' % (repo_dir,
                                                           branch)
        raise RuntimeError(e)
    # Show repo and ask confirmation
    print()
    print('You are about to commit to:')
    sh('git config --get remote.origin.url')
    print()
    print('Most recent 3 commits:')
    sys.stdout.flush()
    sh('git --no-pager log --oneline -n 3')
    ok = input('Are you sure you want to commit and push? (y/[n]): ')
    ok = ok or 'n'
    # If ok, add, commit, push
    if ok.lower() == 'y':
        sh('git add .')
        sh('git commit -am"Update (automated commit)"')
        print()
        sh('git push')

if __name__ == '__main__':
    try:
        m = Maker(sys.argv)
    finally:
        os.chdir(START_DIR)
