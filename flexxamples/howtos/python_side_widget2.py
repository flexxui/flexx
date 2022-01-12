from flexx import flx

class UserInput(flx.PyWidget):

    def init(self):
        with flx.VBox():
            self.edit = flx.LineEdit(placeholder_text='Your name')
            flx.Widget(flex=1)

    @flx.reaction('edit.user_done')
    def update_user(self, *events):
        new_text = self.root.store.username + "\n" + self.edit.text
        self.root.store.set_username(new_text)
        self.edit.set_text("")

class SomeInfoWidget(flx.PyWidget):

    def init(self):
        with flx.FormLayout():
            self.label = flx.Label(title='name:')
            flx.Widget(flex=1)

    @flx.reaction
    def update_label(self):
        self.label.set_text(self.root.store.username)

class Store(flx.PyComponent):

    username = flx.StringProp(settable=True)

class Example(flx.PyWidget):

    store = flx.ComponentProp()

    def init(self):

        # Create our store instance
        self._mutate_store(Store())

        # Imagine this being a large application with many sub-widgets,
        # and the UserInput and SomeInfoWidget being used somewhere inside it.
        with flx.HSplit():
            UserInput()
            flx.Widget(style='background:#eee;')
            SomeInfoWidget()

if __name__ == '__main__':
    m = flx.launch(Example, 'default-browser', backend='flask')
    flx.run()
