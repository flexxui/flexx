# doc-export: Mondriaan
"""
Piet Mondriaan was a Dutch painter who is famous for his style that looks
a little like this. Best viewed in a square window.
"""

from flexx import app, ui


class MyVBox(ui.BoxLayout):
    
    def __init__(self, **kwargs):
        kwargs['spacing'] = kwargs.get('spacing', 15)
        kwargs['padding'] = 0
        kwargs['orientation'] = 'vertical'
        super().__init__(**kwargs)

class MyHBox(ui.BoxLayout):
    def __init__(self, **kwargs):
        kwargs['spacing'] = kwargs.get('spacing', 15)
        kwargs['padding'] = 0
        super().__init__(**kwargs)


class Mondriaan(ui.Widget):
    
    CSS = """
    .flx-Mondriaan {background: #000;}
    .flx-Mondriaan .edge {background:none;}
    .flx-Mondriaan .white {background:#fff;}
    .flx-Mondriaan .red {background:#f23;}
    .flx-Mondriaan .blue {background:#249;}
    .flx-Mondriaan .yellow {background:#ff7;}
    """
    
    def init(self):
        with MyHBox():
            
            with MyVBox(flex=2):
                
                with MyVBox(flex=4, spacing=30):
                    ui.Widget(flex=1, css_class_name='white')
                    ui.Widget(flex=1, css_class_name='white')
                
                with MyVBox(flex=2, css_class_name='blue'):
                    ui.Widget(flex=1, css_class_name='edge')
                    ui.Widget(flex=1, css_class_name='edge')
                
            with MyVBox(flex=6):
                
                with MyVBox(flex=4, spacing=30, css_class_name='red'):
                    ui.Widget(flex=1, css_class_name='edge')
                    ui.Widget(flex=1, css_class_name='edge')
                
                with MyHBox(flex=2):
                    ui.Widget(flex=6, css_class_name='white')
                    
                    with MyVBox(flex=1):
                        ui.Widget(flex=1, css_class_name='white')
                        ui.Widget(flex=1, css_class_name='yellow')


if __name__ == '__main__':
    app.launch(Mondriaan, 'firefox')
    app.run()
