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
        
        TEXT = TEXT
        
        def init(self):
            self.ctx = self.node.getContext('2d')#, {'alpha': False})
            
            # Use trick to get HiDPI text:
            # http://www.html5rocks.com/en/tutorials/canvas/hidpi/
            # todo: this can change at runtime (e.g. browser zoom)
            self.dpratio = window.devicePixelRatio or 1
            self.bsratio = (self.ctx.webkitBackingStorePixelRatio or
                            self.ctx.mozBackingStorePixelRatio or
                            self.ctx.msBackingStorePixelRatio or
                            self.ctx.oBackingStorePixelRatio or
                            self.ctx.backingStorePixelRatio or 1)
            
            
            # Prepare blocks. Normally these would be provided by a document
            blocks = self.TEXT.splitlines()
            self.blocks = []
            for block in blocks:
                self.blocks.append(dict(text=block, height=0, tokens=[]))
        
        @event.prop
        def vscroll(self, v=0):
            """ Indicates the block number for the start of the viewport.
            The fractional portion of this number indicates the amount of
            scrolling to the next 
            """
            return float(v)
        
        # @event.prop
        # def _sub_vscroll(self, v=0):
        #     # The additional steps in case the current block is split over
        #     # multiple lines
        #     return int(v)
        
        @event.connect('mouse_wheel')
        def _handle_wheel(self, *events):
            for ev in events:
                if 'Ctrl' in ev.modifiers:
                    s = self.font_size
                    s += 1 if ev.vscroll < 0 else -1
                    self.font_size = max(5, min(s, 30))
                elif not ev.modifiers:
                    v1 = int(self.vscroll)
                    v2 = self.vscroll % 1
                    v2_delta = self._line_height / self.blocks[v1].height
                    v2 += v2_delta if ev.vscroll > 0 else -v2_delta
                    if v2 >= 1:
                        v1 += 1
                        v2 = 0
                    elif v2 < 0 and v1 > 0:
                        v1 -= 1
                        v2 = 1 - self._line_height / self.blocks[v1].height
                    self.vscroll = min(len(self.blocks)+0.999, max(0, v1+v2))
        
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
            
            # Find the last row with a non-white pixel
            while r > 0 and last == False:
                r -= 1
                for c in range(width):
                    if data[r * width * 4 + c * 4 + 3] > 0:
                        last = r
                        break
            # Find first row with a non-white pixel
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
            ctx.scale(ratio, ratio)
            
            ctx.clearRect(0, 0, w, h)
            ctx.font = "%ipx DejaVu Sans Mono" % self.font_size
            
            cw = ctx.measureText('x').width
            ch = self._measure_text_height()
            self._line_height = line_height = ch + 2
            
            # Hoe many chars fit  in the viewport?
            nw = int(w / cw) - 3
            nh = int(h / ch)
            
            ctx.fillStyle = '#eef'
            ctx.fillRect(0, 0, w, h)
            
            import time
            t0 = time.time()
            
            ctx.fillStyle = '#000'
            blocknr_start = int(self.vscroll)
            blocknr_end = min(len(self.blocks), blocknr_start + nh)
            
            # Set scroll info
            if blocknr_start < len(self.blocks):
                nlines = max(1, int(len(self.blocks[blocknr_start].text) / nw))
                self.blocks[blocknr_start].height = nlines * line_height
            if blocknr_start > 0:
                nlines = max(1, int(len(self.blocks[blocknr_start-1].text) / nw))
                self.blocks[blocknr_start-1].height = nlines * line_height
            
            # Init offset
            subscroll = self.vscroll % 1
            ypos = - subscroll * self.blocks[blocknr_start].height
            xpos = 3 * cw
            
            # Draw blocks ...
            for blocknr in range(blocknr_start, blocknr_end):
                ctx.fillText(blocknr + '', 0, ypos)
                block = self.blocks[blocknr].text
                nsublines = 0
                if len(block) == 0:
                    ypos += line_height
                while len(block) > 0:
                    part, block = block[:nw], block[nw:]
                    ypos += line_height
                    ctx.fillText(part, xpos, ypos)
                if ypos > h:
                    break  # we may break earlier if we had multi-line bocks
            
            #print(time.time() - t0)
            

if __name__ == '__main__':
    m = app.launch(Editor, 'xul')
