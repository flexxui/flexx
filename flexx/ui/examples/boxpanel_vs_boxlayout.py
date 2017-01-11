# doc-export: DifferentBoxes
"""
Example to explain the differences between the BoxPanel and BoxLayout.
"""

T1 = """
BoxLayout (HBox, VBox) - note how in the bottom row, the natural size
of the buttons is taken into account. Also in the top row the natural
size is used as a starting point, and extra space is equally divided.
<br /><br />
Similarly, see how this explanation text takes exactly the space that's needed.
"""

T2 = """BoxPanel (HBoxPanel, VBoxPanel) - note how in the top two rows the
buttons have equal width; the layout is not aware of their natural size,
but uses the base_size. This is stressed in the bottom row, where the
buttons collapse. Therefore, avoid using a flex of 0 with BoxPanel, or
set appropriate base_size values.
<br /><br />
The label for the explanation text has the same size as the other rows; we
made it scrollable to ensure all text can be read ...
<br /><br />
These examples make this layout look bad though. The layout used to split
this app in a left and right part is an excelent use of the BoxPanel; it needs
a "top-dow" layout, without any of the natural sizes affecting the layout.
""" 


from flexx import app, ui


class DifferentBoxes(ui.Widget):
    
    def init(self):
        
        with ui.HBoxPanel():
            
            # BoxPanel stuff
            with ui.VBoxPanel(flex=1, style='background:#6ff'):
                
                ui.Label(text=T2, flex=2, wrap=True, style='overflow-y:scroll')
                
                ui.Label(text='-- Buttons have flex 1 and base_size 100',
                         flex=0, base_size=(16, 16))
                with ui.HBoxPanel(flex=1):
                    ui.Widget(flex=1)
                    ui.Button(text='Hello', base_size=(100, 10), flex=1)
                    ui.Button(text='Beeeeeeeeeeeeeeeh', base_size=(100, 10), flex=1)
                    ui.Widget(flex=1)
                
                ui.Label(text='-- Buttons have flex 0 and base_size 100',
                         flex=0, base_size=(16, 16))
                with ui.HBoxPanel(flex=1):
                    ui.Widget(flex=1)
                    ui.Button(text='Hello', base_size=(100, 10), flex=0)
                    ui.Button(text='Beeeeeeeeeeeeeeeh', base_size=(100, 10), flex=0)
                    ui.Widget(flex=1)
                
                ui.Label(text='-- Buttons have flex 0 and base_size 0',
                         flex=0, base_size=(16, 16))
                with ui.HBoxPanel(flex=1):
                    ui.Widget(flex=1)
                    ui.Button(text='Hello', base_size=(0, 0), flex=0)
                    ui.Button(text='Beeeeeeeeeeeeeeeh', base_size=(0, 0), flex=0)
                    ui.Widget(flex=1)
            
            # BoxLayout stuff
            with ui.VBox(flex=1, style='background:#ff6'):
                
                ui.Label(text=T1, wrap=True, flex=0)
                
                ui.Label(text='-- Buttons have flex 1', flex=0)
                with ui.HBox(flex=1):
                    ui.Widget(flex=1)
                    ui.Button(text='Hello', flex=1)
                    ui.Button(text='Beeeeeeeeeeeeeeeh', flex=1)
                    ui.Widget(flex=1)
                
                ui.Label(text='-- Buttons have flex 0', flex=0)
                with ui.HBox(flex=1):
                    ui.Widget(flex=1)
                    ui.Button(text='Hello', flex=0)
                    ui.Button(text='Beeeeeeeeeeeeeeeh', flex=0)
                    ui.Widget(flex=1)


if __name__ == '__main__':
    m = app.launch(DifferentBoxes, 'browser')
    app.run()
