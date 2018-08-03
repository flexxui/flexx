# doc-export: Example
"""
Example demonstrating the use of Bootstrap to style element and do layout.
"""

from flexx import flx

# Associate bootstrap CSS with this module
url = "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.3/css/bootstrap.min.css"
flx.assets.associate_asset(__name__, url)


class Example(flx.Widget):

    persons = flx.TupleProp((), doc=""" People to show cards for""")
    first_name = flx.StringProp('', settable=True)
    last_name = flx.StringProp('', settable=True)

    @flx.action
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
            flx.create_element('div',
                {'class': 'form-group mb-2'},
                flx.create_element('input',
                    {'class': 'form-control',
                     'id': 'inputFirstName',
                     'oninput': lambda e: self.set_first_name(e.target.value)
                    },
                    'First name'
                    )
                ),
            flx.create_element('div',
                {'class': 'form-group mx-sm-3 mb-2'},
                flx.create_element('input',
                    {'class': 'form-control',
                     'id': 'inputLastName',
                     'oninput': lambda e: self.set_last_name(e.target.value)
                    },
                    'Last name'
                    )
                ),
            flx.create_element('button',
                {'class': 'btn btn-primary mb-2',
                 'onclick': self._button_clicked
                },
                'Submit'
                ),
            ]

        # Create virtual DOM nodes for all persons. We use bootstrap cards
        card_nodes = []
        for name, info in self.persons:
            person_node = flx.create_element('div', {'class': 'card'},
                flx.create_element('div', {'class': 'card-body'},
                    flx.create_element('h5', {'class': 'card-title'}, name),
                    flx.create_element('p', {'class': 'card-text'}, info),
                    )
                )
            card_nodes.append(person_node)

        # Compose finaly DOM tree
        return flx.create_element('div', {},
                    flx.create_element('div',
                        {'class': 'form-inline'},
                        form_nodes
                        ),
                    *card_nodes)


if __name__ == '__main__':
    m = flx.launch(Example, 'firefox-browser')
    flx.run()
