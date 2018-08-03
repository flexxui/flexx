from invoke import task

# todo: also print meta info like globals etc.

@task(help=dict(code='the Python code to transpile'))
def py2js(ctx, code):
    """transpile given Python code to JavaScript
    """
    from pscript import py2js
    print(py2js(code))
