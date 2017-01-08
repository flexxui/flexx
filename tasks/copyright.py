import os

from ._config import ROOT_DIR

from invoke import task


@task
def copyright(ctx):
    """ list usage of copyright notices
    
    The use of copyright notices should be limited to files that are likely
    to be used in other projects, or to make appropriate attributions for code
    taken from other projects. Other than that, git geeps track of what person
    wrote what.
    """
    
    # Processing the whole root directory
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # Check if we should skip this directory
        reldirpath = os.path.relpath(dirpath, ROOT_DIR)
        if reldirpath[0] in '._' or reldirpath.endswith('__pycache__'):
            continue
        if os.path.split(reldirpath)[0] in ('build', 'dist'):
            continue
        # Process files
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            # Open and check
            filename = os.path.join(dirpath, fname)
            text = open(filename, 'rt', encoding='utf-8').read()
            if 'copyright' in text[:200].lower():
                print(
                    'Copyright in %s%s%s' % (reldirpath, os.path.sep, fname))
                for i, line in enumerate(text[:200].splitlines()):
                    if 'copyright' in line.lower():
                        print('  line %i: %s' % (i+1, line))
