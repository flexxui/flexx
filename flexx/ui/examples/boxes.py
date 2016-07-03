# doc-export: Boxes
"""
Example that puts BoxPanel and BoxLayout side-by-side. You can see how
BoxLayout takes the natural size of content into account, making it
more suited for low-level layout. For higher level layout (e.g. the two
main panels in this example) the BoxPanel is more appropriate.
"""

from flexx import ui, app

class Panel(ui.Label):
    CSS = '.flx-Panel {background: #44aaaa; color: #FFF; padding: 1px;}'

class Boxes(ui.Widget):
    
    def init(self):
        
        with ui.HBox():
            
            with ui.VBox(flex=1, orientation='vertical'):
                
                ui.Label(text='<b>BoxLayout</b> (aware of natural size)')
                ui.Label(text='flex: 1, sub-flexes: 0, 0, 0')
                with ui.BoxLayout(flex=1, orientation='horizontal'):
                    Panel(text='A', flex=0)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=0)
                ui.Label(text='flex: 0, sub-flexes: 1, 1, 1')
                with ui.BoxLayout(flex=0, orientation='horizontal'):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=1)
                    Panel(text='C is a bit longer', flex=1)
                ui.Label(text='flex: 1, sub-flexes: 1, 0, 2')
                with ui.BoxLayout(flex=1, orientation='horizontal'):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=2)
                ui.Label(text='flex: 2, sub-flexes: 1, 2, 3')
                with ui.BoxLayout(flex=2, orientation='horizontal'):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=2)
                    Panel(text='C is a bit longer', flex=3)
            
            ui.Widget(flex=0, style='min-width:20px')
            
            with ui.VBox(flex=1, orientation='vertical'):
                
                ui.Label(text='<b>BoxPanel</b> (high level layout)')
                ui.Label(text='flex: 1, sub-flexes: 0, 0, 0')
                with ui.BoxPanel(flex=1, orientation='horizontal'):
                    Panel(text='A', flex=0)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=0)
                ui.Label(text='flex: 0 (collapses), sub-flexes: 1, 1, 1')
                with ui.BoxPanel(flex=0, orientation='horizontal'):
                    Panel(text='A', flex=1, style='min-height:5px;')
                    Panel(text='B', flex=1)
                    Panel(text='C is a bit longer', flex=1)
                ui.Label(text='flex: 1, sub-flexes: 1, 0, 2')
                with ui.BoxPanel(flex=1, orientation='horizontal'):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=0)
                    Panel(text='C is a bit longer', flex=2)
                ui.Label(text='flex: 2, sub-flexes: 1, 2, 3')
                with ui.BoxPanel(flex=2, orientation='horizontal'):
                    Panel(text='A', flex=1)
                    Panel(text='B', flex=2)
                    Panel(text='C is a bit longer', flex=3)


if __name__ == '__main__':
    m = app.launch(Boxes)
    app.run()
