import math

from flexx import ui


class Circle(ui.Label):
    CSS = """
    .flx-circle {
        background: #f00;
        border-radius: 10px;
        width: 10px;
        height: 10px;
    }
    """

class App(ui.App):
    def init(self):
        self._circles = []
        
        with ui.PinboardLayout():
            for i in range(64):
                x = math.sin(i*0.1)*0.3 + 0.5 
                y = math.cos(i*0.1)*0.3 + 0.5
                w = Circle(pos=(x,y))
                self._circles.append(w)
        
        #ui.call_later(0.2, self.tick)
        # todo: animate in Python!
        # todo: animate in JS!
    
    def tick(self):
        print('tick!')
        

app = App()
ui.run()
