# doc-export: AppLayoutExample
"""
An example demonstrating when to use what kind of HV layout in an app.
"""

from flexx import flx


class AppLayoutExample(flx.Widget):

    def init(self):

        with flx.VBox():

            flx.Label(style='background:#cfc;', wrap=1,
                    text='Here is some content at the top for which we want to '
                        'use minimal size. Thus the use of a VBox. '
                        'Below is a splitter, with a box layout on the left '
                        'and a fix layout on the right.')

            with flx.HSplit(flex=1):
                with flx.VBox(style='border:1px solid #777;'):

                    flx.Label(text='Flex 0 0 0')
                    with flx.HBox(flex=0):
                        self.b1 = flx.Button(text='Hi')
                        self.b2 = flx.Button(text='Helloooo world!')
                        self.b3 = flx.Button(text='Foo bar')

                    flx.Label(text='Flex 1 1 1')
                    with flx.HBox(flex=0):
                        self.b1 = flx.Button(flex=1, text='Hi')
                        self.b2 = flx.Button(flex=1, text='Helloooo world!')
                        self.b3 = flx.Button(flex=1, text='Foo bar')

                    flx.Label(text='Flex 1 0 3')
                    with flx.HBox(flex=0):
                        self.b1 = flx.Button(flex=1, text='Hi')
                        self.b2 = flx.Button(flex=0, text='Helloooo world!')
                        self.b3 = flx.Button(flex=3, text='Foo bar')

                    # flx.Widget(flex=1)  # spacer widget

                with flx.VFix(style='border:1px solid #777;'):

                    flx.Label(text='Flex 0 0 0 (space divided equally)', style='')
                    with flx.HFix():
                        self.b1 = flx.Button(text='Hi')
                        self.b2 = flx.Button(text='Helloooo world!')
                        self.b3 = flx.Button(text='Foo bar')

                    flx.Label(text='Flex 1 1 1', style='')
                    with flx.HFix():
                        self.b1 = flx.Button(flex=1, text='Hi')
                        self.b2 = flx.Button(flex=1, text='Helloooo world!')
                        self.b3 = flx.Button(flex=1, text='Foo bar')

                    flx.Label(text='Flex 1 0 3 (the widget with zero collapses')
                    with flx.HFix():
                        self.b1 = flx.Button(flex=1, text='Hi')
                        self.b2 = flx.Button(flex=0, text='Helloooo world!')
                        self.b3 = flx.Button(flex=3, text='Foo bar')

                    # If we would put a spacer widget with flex 1 here, the
                    # above widgets would collapse due to their zero flex value.


if __name__ == '__main__':
    m = flx.launch(AppLayoutExample)
    flx.run()
