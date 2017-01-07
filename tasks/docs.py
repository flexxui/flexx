import os
import sys
import os.path as op
import shutil

from invoke import task
from ._config import DOC_DIR, DOC_BUILD_DIR


@task(help=dict(clean='clear the doc output; start fresh',
                build='build html docs',
                show='show the docs in the browser.'))
def docs(ctx, clean=False, build=False, show=False, **kwargs):
    """ make API documentation
    """
    # Prepare
    
    if not (clean or build or show):
        sys.exit('Task "docs" must be called with --clean, --build or --show')
    
    if clean:
        sphinx_clean(DOC_BUILD_DIR)
    
    if build:
        sphinx_build(DOC_DIR, DOC_BUILD_DIR)
    
    if show:
        sphinx_show(os.path.join(DOC_BUILD_DIR, 'html'))


def sphinx_clean(build_dir):
    if op.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.mkdir(build_dir)
    print('Cleared build directory.')


def sphinx_build(src_dir, build_dir):
    import sphinx
    ret = sphinx.build_main(['sphinx-build',  # Dummy
                             '-b', 'html',
                             '-d', op.join(build_dir, 'doctrees'),
                             src_dir,  # Source
                             op.join(build_dir, 'html'),  # Dest
                             ])
    if ret != 0:
        raise RuntimeError('Sphinx error: %s' % ret)
    print("Build finished. The HTML pages are in %s/html." % build_dir)


def sphinx_show(html_dir):
    index_html = op.join(html_dir, 'index.html')
    if not op.isfile(index_html):
        sys.exit('Cannot show pages, build the html first.')
    import webbrowser
    webbrowser.open_new_tab(index_html)
