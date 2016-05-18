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


een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn een superlange regel sdfksbd fkjsdbf ksdfbn 

""" * 100

class Editor(ui.CanvasWidget):
    
    @event.prop(both=True)
    def font_size(self, v=12):
        return int(v)
    
    class JS:
        
        lines = TEXT.splitlines()
        
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
            
            self._nsublines1 = 1
            self._nsublines2 = 1
        
        @event.prop
        def vscroll(self, v=0):
            """ Indicates the line number for the start of the viewport.
            """
            return int(v)
        
        @event.prop
        def _sub_vscroll(self, v=0):
            # The additional steps in case the current line is split over
            # multiple lines
            return int(v)
        
        @event.connect('mouse_wheel')
        def _handle_wheel(self, *events):
            for ev in events:
                if 'Ctrl' in ev.modifiers:
                    s = self.font_size
                    s += 1 if ev.vscroll < 0 else -1
                    self.font_size = max(5, min(s, 30))
                elif not ev.modifiers:
                    v1 = self.vscroll
                    v2 = self._sub_vscroll
                    v2 += 1 if ev.vscroll > 0 else -1
                    if v2 >= self._nsublines2:
                        self._sub_vscroll = 0
                        v1 += 1
                    elif v2 < 0:
                        v1 -= 1
                        self._sub_vscroll = self._nsublines1 - 1
                    else:
                        self._sub_vscroll = v2
                    self.vscroll = min(len(self.lines), max(0, v1))
        
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
        
        @event.connect('size', 'font_size', 'vscroll', '_sub_vscroll')
        def update(self, *events):
            
            ctx = self.ctx
            w, h = self.size
            
            # Enable hidpi
            ratio = self.dpratio / self.bsratio
            self.node.width = w * ratio
            self.node.height = h * ratio
            
            ctx.clearRect(0, 0, w*ratio, h*ratio)
            ctx.font = "%ipx DejaVu Sans Mono" % self.font_size
            
            cw = ctx.measureText('x').width
            ch = self._measure_text_height()
            line_delta = ch + 2
            
            # Hoe many chars fit  in the viewport?
            nw = int(w*ratio / cw) - 3
            nh = int(h*ratio / ch)
            
            ctx.fillStyle = '#eef'
            ctx.fillRect(0, 0, w*ratio, h*ratio)
            
            import time
            t0 = time.time()
            
            ctx.fillStyle = '#000'
            linenr_start = self.vscroll
            linenr_end = min(len(self.lines), linenr_start + nh)
            
            # Set scroll info
            print('scroll', self.vscroll)
            self._nsublines1 = self._nsublines2 = 1
            if linenr_start < len(self.lines):
                self._nsublines2 = max(1, int(len(self.lines[linenr_start]) / nw))
                if linenr_start > 0:
                    self._nsublines1 = max(1, int(len(self.lines[linenr_start-1]) / nw))
            
            ypos = - self._sub_vscroll * line_delta
            xpos = 3 * cw
            for linenr in range(linenr_start, linenr_end):
                ctx.fillText(linenr + '', 0, ypos)
                line = self.lines[linenr]
                nsublines = 0
                if len(line) == 0:
                    ypos += line_delta
                while len(line) > 0:
                    part, line = line[:nw], line[nw:]
                    ypos += line_delta
                    ctx.fillText(part, xpos, ypos)
                if ypos > h*ratio:
                    break  # we may break earlier if we had multi-line bocks
            
            ctx.scale(ratio, ratio)
            #print(time.time() - t0)
            

if __name__ == '__main__':
    m = app.launch(Editor, 'xul')
