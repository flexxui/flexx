""" Run scripts to generate docs for Flexx
"""

#import examplesgenerator
import genuiclasses
import genexamples
import gencommonast


def init():
    print('GENERATING DOCS ...')
    
    print('  Generating docs for UI classes.')
    genuiclasses.main()
    print('  Generating examples.')
    genexamples.main()


def clean(app, *args):
    genuiclasses.clean()
    genexamples.clean()


def setup(app):
    init()
    app.connect('build-finished', clean)

