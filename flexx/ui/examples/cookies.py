"""
Mmmm, cookies ...
Small example for using cookies to (securely) store user data accross sessions.
"""

from flexx import app, ui, event


class Cookies(app.PyComponent):
    
    def init(self):
        
        with ui.Widget():
            ui.Label(text='Refreshing the page should maintain the value of the line edit.')
            self.edit = ui.LineEdit(placeholder_text='username',
                                    text=self.session.get_cookie('username', ''))
        
    @event.reaction('edit.text')
    def _update_cookie(self, *events):
        self.session.set_cookie('username', self.edit.text)


if __name__ == '__main__':
    m = app.launch(Cookies, 'browser')
    app.run()
