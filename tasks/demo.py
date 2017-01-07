from invoke import task

@task
def demo(ctx):
    """show a quick Flexx demo
    """
    from flexx.ui.examples.demo import Demo
    from flexx import app
    app.launch(Demo)
    app.run()
