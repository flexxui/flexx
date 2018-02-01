# doc-export: Example
"""
Example demonstrating the use of Bootstrap to style element and do layout. 
"""

from flexx import app, event, ui

# Associate bootstrap CSS with this module
url = "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.3/css/bootstrap.min.css"
app.assets.associate_asset(__name__, url)


class Example(ui.Widget):

    persons = event.TupleProp((), doc=""" People to show cards for""")
    first_name = event.StringProp('', settable=True)
    last_name = event.StringProp('', settable=True)
    
    @event.action
    def add_person(self, name, info):
        """ Add a person to our stack.
        """
        ppl = list(self.persons)
        ppl.append((name, info))
        self._mutate_persons(ppl)

    def _button_clicked(self, *events):
        self.add_person(self.first_name, self.last_name)

    def _render_dom(self):
        """ This function gets automatically called when needed; Flexx is aware
        of what properties are used here.
        """
        
        # Create form elements
        form_nodes = [
            ui.create_element('div',
                {'class': 'form-group mb-2'},
                ui.create_element('input',
                    {'class': 'form-control',
                     'id': 'inputFirstName',
                     'oninput': lambda e: self.set_first_name(e.target.value)
                    },
                    'First name'
                    )
                ),
            ui.create_element('div',
                {'class': 'form-group mx-sm-3 mb-2'},
                ui.create_element('input',
                    {'class': 'form-control',
                     'id': 'inputLastName',
                     'oninput': lambda e: self.set_last_name(e.target.value)
                    },
                    'Last name'
                    )
                ),
            ui.create_element('button',
                {'class': 'btn btn-primary mb-2',
                 'onclick': self._button_clicked
                },
                'Submit'
                ),
            ]
        
        # Create virtual DOM nodes for all persons. We use bootstrap cards
        card_nodes = []
        for name, info in self.persons:
            person_node = ui.create_element('div', {'class': 'card'},
                ui.create_element('div', {'class': 'card-body'},
                    ui.create_element('h5', {'class': 'card-title'}, name),
                    ui.create_element('p', {'class': 'card-text'}, info),
                    )
                )
            card_nodes.append(person_node)
        
        # Compose finaly DOM tree
        return ui.create_element('div', {},
                    ui.create_element('div',
                        {'class': 'form-inline'},
                        form_nodes
                        ),
                    *card_nodes)


if __name__ == '__main__':
    m = app.launch(Example, 'firefox-browser')
    app.run()
