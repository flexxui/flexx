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

asd1
asd2
""".strip() * 2

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
            """ Indicates the block number for the start of the
            viewport. The fractional portion of this number indicates
            the amount of scrolling to the next block, relative to the
            height of the current block.
            """
            return float(v)
        
        # @event.prop
        # def _sub_vscroll(self, v=0):
        #     # The additional steps in case the current block is split over
        #     # multiple lines
        #     return int(v)
        
        def _get_height_of_block(self, blocknr):
            # todo: calculate on the fly?
            return max(self._line_height, self.blocks[blocknr].height)
        
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
                    v2_delta = self._line_height / self._get_height_of_block(v1)
                    v2 += v2_delta if ev.vscroll > 0 else -v2_delta
                    if v2 >= 1:
                        v1 += 1
                        v2 = 0
                    elif v2 < 0 and v1 > 0:
                        v2_delta = self._line_height / self._get_height_of_block(v1-1)
                        v1 -= 1
                        v2 = 1 - v2_delta
                    self.vscroll = min(len(self.blocks)-v2_delta, max(0, v1+v2))
        
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
            
            scroll_bar_width = 10
            
            # Hoe many chars fit  in the viewport?
            nw = int((w-scroll_bar_width) / cw) - 3
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
            ypos = line_height - subscroll * self.blocks[blocknr_start].height
            xpos = 3 * cw
            
            # Draw blocks ...
            for blocknr in range(blocknr_start, blocknr_end):
                block = self.blocks[blocknr].text
                ctx.fillText(blocknr + 1 + '', 0, ypos)
                if len(block) == 0:
                    ypos += line_height
                part = ''
                while len(block) > 0:
                    part, block = block[:nw], block[nw:]
                    ctx.fillText(part, xpos, ypos)
                    ypos += line_height
                # show lf ctx.fillRect(xpos+len(part)*cw + 2, ypos-line_height*1.5, 3, 3)
                if ypos > h:
                    break  # we may break earlier if we had multi-line bocks
            
            self._draw_scrollbar(scroll_bar_width)
            #print(time.time() - t0)
        
        def _draw_scrollbar(self, width):
            ctx = self.ctx
            w, h = self.size
            
            # todo: ensure len(blocks) is always >= 1
            #height = h * h / (self._line_height * len(self.blocks))
            height = h / len(self.blocks) ** 0.5
            height = max(5, height)
            start = (self.vscroll / len(self.blocks)) * (h - height)
            
            ctx.fillStyle = '#afa'
            ctx.fillRect(w-width, 0, width, h)
            
            ctx.fillStyle = '#4f4'
            ctx.fillRect(w-width, start, width, height)
            
            

if __name__ == '__main__':
    m = app.launch(Editor, 'xul')
