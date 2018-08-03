""" Test minsize property.
"""

from flexx import flx


class Tester(flx.Widget):

    def init(self):
        super().init()

        with flx.VBox():

            flx.Label(text='You should see 5 pairs of buttons')

            with flx.HFix():  # Use minsize in CSS of button widget
                with flx.GroupWidget(title='asdas'):
                    with flx.HFix():
                        flx.Button(text='foo')
                        flx.Button(text='bar')

            with flx.HFix(minsize=50):  # Set minsize prop on container
                flx.Button(text='foo')
                flx.Button(text='bar')

            with flx.HFix():  # Set minsize prop on widget
                flx.Button(text='foo', minsize=50)
                flx.Button(text='bar')

            with flx.HFix():  # Old school setting of style
                flx.Button(text='foo', style='min-height:50px;')
                flx.Button(text='bar', )

            with flx.Widget():  # Singleton widgets (e.g. custom classes)
                with flx.HFix():
                    flx.Button(text='foo')
                    flx.Button(text='bar')

            flx.Widget(flex=1, style='background:#f99;')  # spacer


if __name__ == '__main__':
    m = flx.launch(Tester, 'firefox')
    flx.run()
