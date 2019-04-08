"""
Mmmm, cookies ...
Small example for using cookies to (securely) store user data accross sessions.
"""

from flexx import flx


class Cookies(flx.PyWidget):

    def init(self):

        with flx.Widget():
            flx.Label(text='Refreshing the page should '
                           'maintain the value of the line edit.')
            self.edit = flx.LineEdit(placeholder_text='username',
                                     text=self.session.get_cookie('username', ''))

    @flx.reaction('edit.text')
    def _update_cookie(self, *events):
        self.session.set_cookie('username', self.edit.text)


if __name__ == '__main__':
    m = flx.launch(Cookies, 'browser')
    flx.start()
