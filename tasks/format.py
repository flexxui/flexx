import sys

from invoke import task

from ._config import ROOT_DIR, NAME


@task
def checkformat(ctx):
    """ Check whether the code adheres to the style rules. Use autoformat to fix.
    """
    try:
        import yapf
    except ImportError:
        sys.exit("You need to ``pip install yapf`` to checkformat")

    # YAPF docs: if --diff is supplied, YAPF returns zero when no changes were
    # necessary, non-zero otherwise (including program error).
    cmd = ["yapf", "--recursive", "--diff"]
    cmd += ["flexx", "flexxamples", "tasks", "setup.py"]

    try:
        sys.exit(yapf.main(cmd))
    except yapf.errors.YapfError as e:
        sys.stderr.write('yapf: ' + str(e) + '\n')
        sys.exit(1)


@task
def autoformat(ctx):
    """ Automatically format the code (using yapf).
    """
    try:
        import yapf
    except ImportError:
        sys.exit("You need to ``pip install yapf`` to autoformat")

    cmd = ["yapf", "--recursive", "--in-place"]
    cmd += ["flexx", "flexxamples", "tasks", "setup.py"]

    try:
        sys.exit(yapf.main(cmd))
    except yapf.errors.YapfError as e:
        sys.stderr.write('yapf: ' + str(e) + '\n')
        sys.exit(1)
