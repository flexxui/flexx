import os
import time

from ._config import ROOT_DIR, NAME

from invoke import task

# todo: it might not be best to always update this to the latest year;
# the earliest year might be better. Or maybe a range.


@task(help=dict(name='the name of the copyright holder (optional)',
                dry='dry run (print changes, but do not apply them)'))
def copyright(ctx, name='', dry=False):
    """ update all copyright notices to the current year
    
    Does a search for a specific copyright notice of last year and replaces
    it with a version for this year. Other copyright mentionings are listed,
    but left unmodified.
    
    If the name argument is given, use that as the name of the copyright holder,
    otherwise use the name specifief in `tasks/_config.py`.
    """

    # Initialize
    if not name:
        name = '%s Development Team' % NAME
    
    TEMPLATE = "# Copyright (c) %i, %s."
    CURYEAR = int(time.strftime('%Y'))
    OLDTEXT = TEMPLATE % (CURYEAR - 1, name)
    NEWTEXT = TEMPLATE % (CURYEAR, name)
    # Initialize counts
    count_ok, count_replaced = 0, 0
    
    print('looking for: ' + OLDTEXT)
    
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
            if NEWTEXT in text:
                count_ok += 1
            elif OLDTEXT in text:
                text = text.replace(OLDTEXT, NEWTEXT)
                if not dry:
                    open(filename, 'wt', encoding='utf-8').write(text)
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
