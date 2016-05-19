"""
Example that puts BoxPanel and BoxLayout side-by-side. You can see how
BoxLayout takes the natural size of content into account, making it
more suited for low-level layout. For higher level layout (e.g. the two
main panels in this example) the BoxPanel is more appropriate.
"""

from flexx import ui, app


class Example(ui.Widget):
    
    def init(self):
        
        with ui.HBox():
            
            with ui.BoxPanel(flex=1, orientation='vertical'):
                
                with ui.BoxLayout(flex=1, orientation='horizontal'):
                    ui.Button(text='Box A', flex=0)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=0)
                with ui.BoxLayout(flex=0, orientation='horizontal'):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=1)
                    ui.Button(text='Box C is a bit longer', flex=1)
                with ui.BoxLayout(flex=1, orientation='horizontal'):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=2)
                with ui.BoxLayout(flex=2, orientation='horizontal'):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=2)
                    ui.Button(text='Box C is a bit longer', flex=3)
            
            ui.Widget(flex=0, style='min-width:20px')
            
            with ui.BoxPanel(flex=1, orientation='vertical'):
                
                with ui.BoxPanel(flex=1, orientation='horizontal'):
                    ui.Button(text='Box A', flex=0)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=0)
                with ui.BoxPanel(flex=0, orientation='horizontal'):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=1)
                    ui.Button(text='Box C is a bit longer', flex=1)
                with ui.BoxPanel(flex=1, orientation='horizontal'):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=0)
                    ui.Button(text='Box C is a bit longer', flex=2)
                with ui.BoxPanel(flex=2, orientation='horizontal'):
                    ui.Button(text='Box A', flex=1)
                    ui.Button(text='Box B', flex=2)
                    ui.Button(text='Box C is a bit longer', flex=3)


if __name__ == '__main__':
    m = app.launch(Example)
    app.run()
