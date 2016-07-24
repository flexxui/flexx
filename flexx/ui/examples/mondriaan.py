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
    """
    
    def init(self):
        with MyHBox():
            
            with MyVBox(flex=2):
                
                with MyVBox(flex=4, spacing=30):
                    ui.Widget(flex=1, style='background:#fff;')
                    ui.Widget(flex=1, style='background:#fff;')
                
                with MyVBox(flex=2, style='background:#249;'):
                    ui.Widget(flex=1, style='background:none;')
                    ui.Widget(flex=1, style='background:none;')
                
            with MyVBox(flex=6):
                
                with MyVBox(flex=4, spacing=30, style='background:#f23;'):
                    ui.Widget(flex=1, style='background:none;')
                    ui.Widget(flex=1, style='background:none;')
                
                with MyHBox(flex=2):
                    ui.Widget(flex=6, style='background:#fff;')
                    
                    with MyVBox(flex=1):
                        ui.Widget(flex=1, style='background:#fff;')
                        ui.Widget(flex=1, style='background:#ff7;')


if __name__ == '__main__':
    app.launch(Mondriaan)
    app.run()
