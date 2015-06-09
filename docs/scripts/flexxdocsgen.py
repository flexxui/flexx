""" Run scripts to generate docs for Flexx
"""

#import examplesgenerator
import genuiclasses


def init():
    print('GENERATING DOCS ...')
    
    print('  Generating docs for UI classes.')
    genuiclasses.main()


def clean(app, *args):
    genuiclasses.clean()

def setup(app):
    init()
    app.connect('build-finished', clean)
