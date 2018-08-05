import os

from invoke import task

from ._config import ROOT_DIR, NAME


def trim_py_files(directory):
    for root, dirs, files in os.walk(directory):
        for fname in files:
            filename = os.path.join(root, fname)
            if fname.endswith('.py'):
                with open(filename, 'rb') as f:
                    code = f.read().decode()
                lines = [line.rstrip() for line in code.splitlines()]
                while lines and not lines[-1]:
                    lines.pop(-1)
                lines.append('')  # always end with a newline
                with open(filename, 'wb') as f:
                    f.write('\n'.join(lines).encode())


@task
def ws(ctx):
    """ Remove trailing whitespace from all py files.
    """
    trim_py_files(os.path.join(ROOT_DIR, 'flexx'))
    trim_py_files(os.path.join(ROOT_DIR, 'flexxamples'))
    trim_py_files(os.path.join(ROOT_DIR, 'tasks'))
