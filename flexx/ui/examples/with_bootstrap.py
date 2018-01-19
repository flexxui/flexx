"""
Example demonstrating the use of Bootstrap to style element and do layout. 
"""

from flexx import app, event, ui

# Associate bootstrap CSS with this module
url = "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.3/css/bootstrap.min.css"
app.assets.associate_asset(__name__, url)


class Example(ui.Widget):
    
    # A property with (name, info) tuples
    persons = event.TupleProp((), doc=""" People to show cards for""")
    
    def init(self):
        # We use Flexx widgets for our input; easier to wire
        self.name = ui.LineEdit(placeholder_text='name')
        self.info = ui.LineEdit()
        self.but = ui.Button(css_class='btn btn-primary', text='hello')
    
    @event.action
    def add_person(self, name, info):
        """ Add a person to our stack.
        """
        ppl = list(self.persons)
        ppl.append((name, info))
        self._mutate_persons(ppl)
    
    @event.reaction('but.mouse_down')
    def _button_clicked(self, *events):
        self.add_person(self.name.text, self.info.text)
    
    def _render_dom(self):
        """ This function gets automatically called when needed; Flexx is aware
        of what properties are used here.
        """
        # Create virtual DOM nodes for all persons. We use bootstrap cards
        nodes = []
        for name, info in self.persons:
            person_node = ui.create_element('div', {'class': 'card'}, [
                                ui.create_element('h5', {'class': 'card-title'}, name),
                                ui.create_element('p', {'class': 'card-text'}, info),
                                ])
            nodes.append(person_node)
        
        # Define the final layout. Note how the nodes of the input widgets are embedded
        return ui.create_element('div', {'class': 'container'}, [
                    ui.create_element('div', {'class': 'row'}, [
                        ui.create_element('div', {'class': 'col-sm-4'},
                                          [self.name.outernode]),
                        ui.create_element('div', {'class': 'col-sm-4'},
                                          [self.info.outernode]),
                        ui.create_element('div', {'class': 'col-sm-4'},
                                          [self.but.outernode]),
                        ]),
                    ui.create_element('div', {'class': 'row'}, 
                        [ui.create_element('div', {'class': 'col-sm-4'}, [node])
                         for node in nodes]),
                    ])


if __name__ == '__main__':
    m = app.launch(Example)
    app.run()
