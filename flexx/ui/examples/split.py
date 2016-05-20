# doc-export: Split
"""
Splitter widgets are cool!
"""

from flexx import app, ui


class Split(ui.Widget):
    
    def init(self):
        
        with ui.SplitPanel(orientation='horizontal'):
            ui.Widget(style='background:#f00')
            with ui.SplitPanel(orientation='vertical'):
                ui.Widget(style='background:#0f0')
                with ui.SplitPanel(orientation='horizontal'):
                    ui.Widget(style='background:#ff0')
                    with ui.SplitPanel(orientation='vertical'):
                        ui.Widget(style='background:#f0f')
                        with ui.SplitPanel(orientation='horizontal'):
                            ui.Widget(style='background:#0ff')
                            ui.Widget(style='background:#00f')


if __name__ == '__main__':
    m = app.launch(Split)
    app.run()
