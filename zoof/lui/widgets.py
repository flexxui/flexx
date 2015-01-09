
from ._coords import glyph_coords


def get_glyph_coords(c):
    try:
        return glyph_coords[c]
    except KeyError:
        return glyph_coords['\x00']


class Label(object):
    
    def __init__(self, text):
        self._text = text
    
    def generate_data(self, size):
        
        w, h = size
        chars_on_line = size[0] // 16
        
        ix, iy = 0, 0
        
        # Generate tex coords
        tcoords = []
        vcoords = []
        for i, c in enumerate(self._text):
            if c in '\r\n':
                ix, iy = 0, iy + 1
                continue
            # Store texture coord
            tcoords.extend(get_glyph_coords(c))
            # Define raster position
            ix += 1
            if ix >= chars_on_line:
                ix, iy = 0, iy + 1
            # Define quad corner positions
            x1, x2 = + 2 * ix * 16 / w - 1, +2 * (ix+1) * 16 / w - 1
            y1, y2 = - 2 * iy * 16 / h + 1, -2 * (iy+1) * 16 / h + 1
            # Store vertex coord
            vc = x1, y1, x2, y1, x1, y2,  x1, y2, x2, y1, x2, y2
            vcoords.extend(vc)
        
        return vcoords, tcoords
