import subprocess

from invoke import task

from ._config import NAME


@task
def help(ctx):
    """Get info on usage.
    """

    print('Developer tools for project %s\n' % NAME.capitalize())
    print('  invoke <task> [arg] to run a task')
    print('  invoke --help <task> to get info on a task')
    print()
    subprocess.call('invoke --list')
