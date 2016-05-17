from flexx import app, ui, event

TEXT = """
hallo dit is wat text als test.

lorum epsilum blabla

        yield renderer


class Editor(ui.CanvasWidget):
    
    @event.prop(both=True)
    def font_size(self, v):
        return int(v)
    
    class JS:
        
        text = TEXT
        
        def init(self):
            self.ctx = self.node.getContext('2d')#, {alpha: false})
        
        @event.connect('mouse_wheel')
        def _change_font_size(self, *events):
            s = self.font_size
            for ev in events:
                if ev.vscroll > 0:
                    s += 1
                else:
                    s -= 1
            self.font_size = max(5, min(s, 30))

""" * 100

class Editor(ui.CanvasWidget):
    
    @event.prop(both=True)
    def font_size(self, v):
        return int(v)
    
    class JS:
        
        text = TEXT
        
        def init(self):
            self.ctx = self.node.getContext('2d')#, {'alpha': False})
            
            # Use trick to get HiDPI text:
            # http://www.html5rocks.com/en/tutorials/canvas/hidpi/
            self.dpratio = window.devicePixelRatio or 1
            self.bsratio = (self.ctx.webkitBackingStorePixelRatio or
                            self.ctx.mozBackingStorePixelRatio or
                            self.ctx.msBackingStorePixelRatio or
                            self.ctx.oBackingStorePixelRatio or
                            self.ctx.backingStorePixelRatio or 1)
        
        @event.connect('mouse_wheel')
        def _change_font_size(self, *events):
            s = self.font_size
            for ev in events:
                if ev.vscroll > 0:
                    s += 1
                else:
                    s -= 1
            self.font_size = max(5, min(s, 30))
        
        
        def _measure_text_height(self):
            # Inspired by http://stackoverflow.com/a/1135363/2271927
            # todo: only do this when font_size changes
            
            ctx = self.ctx
            sample = 'gM('
            
            width = int(ctx.measureText(sample).width+1)
            height = 100
            
            ctx.fillText(sample, 0, int(height/2))
            
            data = ctx.getImageData(0, 0, width, height).data
            first = False 
            last = False
            r = height
            
            # Find the last line with a non-white pixel
            while r > 0 and last == False:
                r -= 1
                for c in range(width):
                    if data[r * width * 4 + c * 4 + 3] > 0:
                        last = r
                        break
            # Find first line with a non-white pixel
            while r > 0:
                r -= 1
                for c in range(width):
                    if data[r * width * 4 + c * 4 + 3] > 0:
                        first = r
                        break
            
            return last - first
        
        @event.connect('size', 'font_size')
        def update(self, *events):
            
            ctx = self.ctx
            w, h = self.size
            
            # Enable hidpi
            ratio = self.dpratio / self.bsratio
            self.node.width = w * ratio
            self.node.height = h * ratio
            
            ctx.clearRect(0, 0, w, h)
            ctx.font = "%ipx DejaVu Sans Mono" % self.font_size
            
            cw = ctx.measureText('x').width
            ch = self._measure_text_height()
            
            import time
            t0 = time.time()
            
            ypos = 0
            for line in self.text.splitlines():
                ypos += ch + 2
                ctx.fillText(line, 0, ypos)
            
            ctx.scale(ratio, ratio)
            #print(time.time() - t0)
            

if __name__ == '__main__':
    m = app.launch(Editor, 'xul')
