# doc-export: Dock
"""
Dock widgets are cool!
"""

from flexx import app, ui


class Dock(ui.DockPanel):
    
    def init(self):
        
        ui.Widget(style='background:#f00', title='red')
        ui.Widget(style='background:#0f0', title='green')
        ui.Widget(style='background:#00f', title='blue')
        ui.Widget(style='background:#ff0', title='yellow')
        ui.Widget(style='background:#f0f', title='purple')
        ui.Widget(style='background:#0ff', title='cyan')


if __name__ == '__main__':
    m = app.launch(Dock)
    app.run()
