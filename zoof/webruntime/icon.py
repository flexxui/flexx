# -*- coding: utf-8 -*-
# Copyright (c) 2015, Almar Klein
# This module is distributed under the terms of the new BSD License.

"""
Pure python module to handle the .ico format. Also support for simple
PNG files. Written for Python 2.7 and Python 3.2+.

* Icon - class to populate an icon stack and export it to ICO or PNG
* read_png() and write_png() - functions to deal with simple PNG files.
"""

import os
import sys
import zlib
import struct

if sys.version_info < (3, ):
    bytes = str
    str = basestring

VALID_SIZES = 16, 32, 48, 64, 128, 256

# Little endian int encoding (for bmp/icon writing)
w1 = lambda x: struct.pack('<B', x)
w2 = lambda x: struct.pack('<H', x)
w4 = lambda x: struct.pack('<I', x)

def intl(x):
    """ little endian int decoding (for bmp/ico reading)
    """
    if len(x) == 1:
        return struct.unpack('<B', x)[0]
    elif len(x) == 2:
        return struct.unpack('<H', x)[0]
    elif len(x) == 4:
        return struct.unpack('<I', x)[0]


def write_png(im, shape):
    """ Write png image
    
    Given an image (as bytes or bytearray) and a shape, return bytes
    that represent the PNG image (can be written to a file as-is).
    """
    # This function is written to be standalone
    
    # Check types
    assert isinstance(im, (bytes, bytearray))
    assert isinstance(shape, tuple)
    
    # Check shape
    if len(shape) != 3:
        raise ValueError('shape must be 3 elements)')
    if shape[2] not in (3, 4):
        raise ValueError('shape[2] must be in (3, 4)')
    if (shape[0] * shape[1] * shape[2]) != len(im):
        raise ValueError('Shape does not match number of elements in image')
    
    def add_chunk(data, name):
        name = name.encode('ASCII')
        crc = zlib.crc32(data, zlib.crc32(name))
        parts.append(struct.pack('>I', len(data)))
        parts.append(name)
        parts.append(data)
        #parts.append(crc.to_bytes(4, 'big'))  # python 3.x +
        parts.append(struct.pack('>I', crc & 0xffffffff))
    
    parts = [b'\x89PNG\x0d\x0a\x1a\x0a']  # header
    
    # First chunk
    w, h = shape[0], shape[1]
    depth = 8
    ctyp = 0b0110 if shape[2] == 4 else 0b0010
    ihdr = struct.pack('>IIBBBBB', w, h, depth, ctyp, 0, 0, 0)
    add_chunk(ihdr, 'IHDR')
    
    # Chunk with pixels. Just one chunk, no fancy filters.
    line_len = w * shape[2]
    lines = [im[i*line_len:(i+1)*line_len] for i in range(h)]
    lines = [b'\x00' + line for line in lines]  # prepend filter byte
    pixels_compressed = zlib.compress(b''.join(lines), 9)
    add_chunk(pixels_compressed, 'IDAT')
    
    # Closing chunk
    add_chunk(b'', 'IEND')
    
    # Combine
    return b''.join(parts)


def read_png(f):
    """ Read png image
    
    Input argument f can be a filename, file object, or bytes object.
    Returns (pixel_array, (NxMxC)), with C 3 or 4, depending or whether
    the image is RGB or RGBA. The pixel_array is a bytearray object.
    
    Simple implementation. Can only read PNG's that are not interlaced,
    have a bit depth of 8, and are either RGB or RGBA.
    """
    # This function is written to be standalone, but needs _png_scanline()
    
    # http://en.wikipedia.org/wiki/Portable_Network_Graphics
    # http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html
    
    asint_map = {1: '>B', 2: '>H', 4: '>I'}
    asint = lambda x: struct.unpack(asint_map[len(x)], x)[0]
    
    # Try filename
    if isinstance(f, str):
        if b'\x00' not in f:
            if os.path.isfile(f):
                f = open(f, 'rb').read()
            else:
                raise IOError("File does not exist %r" % f)
    
    # Get bytes
    if isinstance(f, bytes):
        bb = f
    elif hasattr(f, 'read'):
        bb = f.read()
    else:
        raise ValueError('Do not know how to read PNG from %r' % f)
    
    # Read header
    assert bb[0:1] == b'\x89'
    assert bb[1:4] == b'PNG'
    chunk_pointer = 8
    
    # Read first chunk
    chunk1 = bb[chunk_pointer:]
    chunk_length = asint(chunk1[0:4])
    chunk_pointer += 12 + chunk_length  # size, type, crc, data
    assert chunk1[4:8] == b'IHDR'  # First chunk must be this
    assert chunk_length == 13  # Always same size
    
    # Extract info
    width = asint(chunk1[8:12])
    height = asint(chunk1[12:16])
    bit_depth = asint(chunk1[16:17])
    color_type = asint(chunk1[17:18])
    compression_method = asint(chunk1[18:19])
    filter_method = asint(chunk1[19:20])
    interlace_method = asint(chunk1[20:21])
    bytes_per_pixel = 3 + (color_type == 6)
    
    # Check if we can do this ....
    if bit_depth != 8:
        raise RuntimeError('Can only deal with bit-depth of 8.')
    if color_type not in [2, 6]:  # RGB, RGBA
        raise RuntimeError('Can only deal with RGB or RGBA.')
    if interlace_method != 0:
        raise RuntimeError('Can only deal with non-interlaced.')
    
    # If this is the case ... extract pixel info
    lines, prev = [], None
    while True:
        chunk = bb[chunk_pointer:]
        if not chunk:
            break
        chunk_length = asint(chunk[0:4])
        chunk_pointer += 12 + chunk_length
        if chunk[4:8] == b'IEND':
            break
        elif chunk[4:8] == b'IDAT':  # Pixel data
            # Decompress and unfilter
            pixels_compressed = chunk[8:8+chunk_length]
            pixels_raw = zlib.decompress(pixels_compressed)
            s = width * bytes_per_pixel + 1  # stride
            #print(pixels_raw[0::s])  # show filters in use
            for i in range(height):
                prev = _png_scanline(pixels_raw[i*s:i*s+s], prev=prev)
                lines.append(prev)
            
    # Combine scanlines from all chunks
    im = bytearray(sum([len(line) for line in lines]))
    i = 0
    line_len = width * bytes_per_pixel
    for line in lines:
        assert len(line) == line_len
        im[i:i+line_len] = line
        i += line_len
    return im, (width, height, bytes_per_pixel)


def _png_scanline(line_bytes, fu=4, prev=None):
    """ Scanline unfiltering, taken from png.py
    """
    filter = ord(line_bytes[0:1])
    line1 = bytearray(line_bytes[1:])  # copy so that indexing yields ints
    line2 = bytearray(line_bytes[1:])  # output line
    
    if filter == 0:
        pass  # No filter
    elif filter == 1:
        # sub
        ai = 0
        for i in range(fu, len(line2)):
            x = line1[i]
            a = line2[ai]
            line2[i] = (x + a) & 0xff
            ai += 1
    elif filter == 2:
        # up
        for i in range(len(line2)):
            x = line1[i]
            b = prev[i]
            line2[i] = (x + b) & 0xff
    elif filter == 3:
        # average
        ai = -fu
        for i in range(len(line2)):
            x = line1[i]
            if ai < 0:
                a = 0
            else:
                a = line2[ai]
            b = prev[i]
            line2[i] = (x + ((a + b) >> 1)) & 0xff
            ai += 1
    elif filter == 4:
        # paeth
        ai = -fu  # Also used for ci.
        for i in range(len(line2)):
            x = line1[i]
            if ai < 0:
                a = c = 0
            else:
                a = line2[ai]
                c = prev[ai]
            b = prev[i]
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                pr = a
            elif pb <= pc:
                pr = b
            else:
                pr = c
            line2[i] = (x + pr) & 0xff
            ai += 1
    else:
        raise RuntimeError('Invalid filter %r' % filter)
    return line2


class Icon(object):
    """ Icon class
    
    Functionality to read/create icons. Considers only RGBA icons. Can
    deal with images stored raw (BMP) and compressed (PNG).
    
    """
    # Convetions:
    # im -> an image stores as a bytearray array, uint8, NxNx4
    # bb -> bytes, possibly a png/bmp/ico
    
    def __init__(self, *filenames):
        self._ims = {}
        for filename in filenames:
            self.read(filename)
    
    def __repr__(self):
        ss = self.image_sizes()
        return '<Icon with %i sizes: %r at 0x%x>' % (len(ss), ss, id(self))
    
    def image_sizes(self):
        """ Get a tuple of image sizes currently loaded
        """
        return tuple(sorted(self._ims.keys()))
    
    def add(self, data):
        """ Add an image represented as bytes or bytearray.
        """
        assert isinstance(data, (bytes, bytearray))
        self._store_image(data)
    
    def read(self, filename):
        """ Read an image from the given filename and add to collection
        
        Can be an ICO, PNG, or BMP file.  When an RGB image is read,
        it is converted to RGBA. Some restrictions may apply to the
        formats that can be read.
        """
        if not isinstance(filename, str):
            raise ValueError('Icon.read() needs a file name')
        
        if filename.startswith('http'):
            try:
                from urllib.request import urlopen  # Python 3.x
            except ImportError:
                from urllib2 import urlopen  # Python 2.x
            data = urlopen(filename, timeout=2.0).read()
        else:
            data = open(filename, 'rb').read()
        
        if filename.lower().endswith('.ico'):
            self._from_ico(data)
        elif filename.lower().endswith('.png'):
            self._from_png(data)
        elif filename.lower().endswith('.bmp'):
            self._from_bmp(data)
        else:
            raise ValueError('Can only load from png, bmp, or ico')
    
    def write(self, filename):
        """ Write the icon collection to an image with the given filename
        
        Can be an ICO, ICNS, PNG, or BMP file. In case of PNG/BMP,
        multiple images may be generated, the image size is appended
        to the file name.
        """
        if not isinstance(filename, str):
            raise ValueError('Icon.write() needs a file name')
        
        if filename.lower().endswith('.ico'):
            data = self._to_ico()
            open(filename, 'wb').write(data)
        elif filename.lower().endswith('.icns'):
            data = self._to_icns()
            open(filename, 'wb').write(data)    
        elif filename.lower().endswith('.png'):
            for size in sorted(self._ims):
                filename2 = '%s%i%s' % (filename[:-4], size, filename[-4:])
                data = self._to_png(self._ims[size])
                open(filename2, 'wb').write(data)
        elif filename.lower().endswith('.bmp'):
            for size in sorted(self._ims):
                filename2 = '%s%i%s' % (filename[:-4], size, filename[-4:])
                data = self._to_bmp(self._ims[size], file_header=True)
                open(filename2, 'wb').write(data)
        else:
            raise ValueError('Can only export to png, bmp, or ico')
    
    def to_bytes(self):
        """ Return the bytes that represent the .ico image
        
        This function can be used by webservers to serve the ico image
        without needing a physical representation on disk.
        """
        return self._to_ico()
    
    def _image_size(self, im):
        npixels = len(im) // 4
        width = height = int(npixels ** 0.5)
        if width * height * 4 != len(im):
            raise ValueError('Icon must be NxMx4 pixels')
        if width not in VALID_SIZES:
            raise ValueError('Icon must have size in %s' % str(VALID_SIZES))
        return width
    
    def _store_image(self, im):
        self._ims[self._image_size(im)] = im
    
    def _from_ico(self, bb):
        # Windows icon format.
        # http://en.wikipedia.org/wiki/ICO_%28file_format%29
        
        assert intl(bb[0:2]) == 0
        assert intl(bb[2:4]) == 1  # must be ICO (not CUR)
        number_of_images = intl(bb[4:6])
        
        for imnr in range(number_of_images):
            imheader = bb[6+imnr*16:]
            # We don't care about dimensions and bpp, we read that in bmp/png
            width = intl(imheader[0:1]) or 256
            size = intl(imheader[8:12])
            offset = intl(imheader[12:16])
            # Get image
            imdata = bb[offset:offset+size]
            try:
                if imdata[1:4] == b'PNG':
                    self._from_png(imdata)
                else:
                    self._from_bmp(imdata)
            except RuntimeError as err:
                print('Skipping image size %i: %s' % (width, err))
    
    def _to_ico(self):
        
        bb = b''
        imdatas = []
        
        # Header
        bb += w2(0)
        bb += w2(1)  # 1:ICO, 2:CUR
        bb += w2(len(self._ims))
        
        # Put offset right after the last directory entry
        offset = len(bb) + 16 * len(self._ims)
        
        # Directory (header for each image)
        for size in sorted(self._ims):
            im = self._ims[size]
            if size >= 64:
                imdata = self._to_png(im)
            else:
                imdata = self._to_bmp(im)
            imdatas.append(imdata)
            # Prepare dimensions
            w = h = 0 if size == 256 else size
            # Write directory entry
            bb += w1(w)
            bb += w1(h)
            bb += w1(0)  # number of colors in palette, assume no palette (0)
            bb += w1(0)  # reserved (must be 0)
            bb += w2(0)  # color planes
            bb += w2(32)  # bits per pixel
            bb += w4(len(imdata))  # size of image data
            bb += w4(offset)
            # Set offset pointer
            offset += len(imdata)
        
        return b''.join([bb] + imdatas)
    
    def _to_icns(self):
        # OSX icon format. 
        # No formal spec. Any docs is reverse engineered by someone.
        # Which is one reason for not having a from_icns().
        # http://en.wikipedia.org/wiki/Apple_Icon_Image_format
        # http://www.macdisk.com/maciconen.php
        # http://www.ezix.org/project/wiki/MacOSXIcons
        
        imdatas = []
        raw_types = {16: (b'is32', b's8mk'),
                     32: (b'il32', b'l8mk'),
                     48: (b'ih32', b'h8mk'),
                     128: (b'it32', b't8mk'), }
        png_types = {16: b'icp4', 32: b'icp5', 64: b'icp6', 128: b'ic07',
                     256: b'ic08', 512: b'ic09', 1024: b'ic10'}
        
        for size in sorted(self._ims):
            im = self._ims[size]
            if size in raw_types:
                # Raw format - can be compressed with packbits
                type, apha_type = raw_types[size]
                # RGBA to XRGB
                data = bytearray(len(im))
                data[1::4] = im[0::4]
                data[2::4] = im[1::4]
                data[3::4] = im[2::4]
                # Store RGBA
                imdatas.append(type)
                imdatas.append(struct.pack('>I', len(data) + 8))
                imdatas.append(data)
                # RGBA to A
                data = bytearray(len(im)//4)
                data[:] = im[3::4]
                # Store alpha
                imdatas.append(apha_type)
                imdatas.append(struct.pack('>I', len(data) + 8))
                imdatas.append(data)
            elif False:  # size in png_types:
                # Store as png, does not seem to work
                data = self._to_png(im)
                imdatas.append(png_types[size])
                imdatas.append(struct.pack('>I', len(data) + 8))
                imdatas.append(data)
            else:
                print('Skipping export size %i to .icns' % size)
                continue
        
        total_icon_size = sum([len(i) for i in imdatas]) + 8
        bb = b'icns' + struct.pack('>I', total_icon_size)
        return b''.join([bb] + imdatas)
    
    def _from_bmp(self, bb):
        # Bitmap image file format
        # http://en.wikipedia.org/wiki/BMP_file_format
        
        # Skip header it is there
        file_header = False
        if bb[0:2] in (b'BM', b'BA', b'CI', b'CP', b'IC', b'PT'):
            file_header = True
            bb = bb[14:]
        
        # Get and check header size (BMP identifies its many headers by length)    
        head_size = intl(bb[0:4])
        if head_size != 40:
            raise RuntimeError('Need BMP header size 40 (not %r)' % head_size)
        
        # Get info from this header
        width = intl(bb[4:8])
        height = intl(bb[8:12]) // (2 - file_header)  # half if not from file 
        color_planes = intl(bb[12:14])
        bpp = intl(bb[14:16])
        compression = intl(bb[16:20])
        data_length = intl(bb[20:24])
        
        # Check
        if width != height:
            raise RuntimeError('Width and height must be equal in icon')
        if width not in VALID_SIZES:
            raise RuntimeError('Invalid size %r in icon' % width)
        if compression != 0:
            raise RuntimeError('Can only deal with uncompressed BMP')
        
        # Get image data
        im = bb[40:40+data_length]
        
        # Init, ensure we have alpha channel
        if bpp == 32:
            im = im[:width*width*4]  # Discart AND mask
            assert len(im) == width * width * 4
            im2 = bytearray(len(im))
            im2[3::4] = im[3::4]
        elif bpp == 24:
            im = im[width*width*3]  # Discart AND mask
            assert len(im) in width * width * 3
            im2 = bytearray(int(len(im)*1.333333333334))
            im2[3::4] = 255
        else:
            raise RuntimeError('Can only deal with RGB or RGBA BMP')
        
        # BGRA to RGBA
        im2[0::4] = im[2::4]
        im2[1::4] = im[1::4]
        im2[2::4] = im[0::4]
        im = im2
        
        # Flip vertically
        lines = [im[width*4*i:width*4*(i+1)] for i in range(height)]
        im = bytearray().join(reversed(lines))
        
        #return im2
        self._store_image(im)
        
    def _to_bmp(self, im, file_header=False):
        
        # Init
        width = self._image_size(im)
        height = reported_height = width
        if not file_header:
            reported_height *= 2  # This is soo weird, but it needs to be so
        
        # RGBA to BGRA
        im2 = bytearray(len(im))
        im2[0::4] = im[2::4]
        im2[1::4] = im[1::4]
        im2[2::4] = im[0::4]
        im2[3::4] = im[3::4]
        im = im2
        
        # Flip vertically
        lines = [im[width*4*i:width*4*(i+1)] for i in range(height)]
        im = bytearray().join(reversed(lines))
        
        # DIB header
        bb = b''
        bb += w4(40)  # header size
        bb += w4(width)
        bb += w4(reported_height)
        bb += w2(1)  # 1 color plane
        bb += w2(32)
        bb += w4(0)  # no compression
        bb += w4(len(im))
        bb += w4(2835) + w4(2835)  # 2835 pixels/meter, ~ 72 dpi
        bb += w4(0)  # number of colors in palette
        bb += w4(0)  # number of important colors (0->all)
        
        # File header (not when bm is in-memory)
        header = b''
        if file_header:
            header += b'BM'
            header += w4(14 + 40 + len(im))  # file size
            header += b'\x00\x00\x00\x00'
            header += w4(14 + 40)  # pixel data offset
        
        # Add pixels
        # No padding, because we assume power of 2 image sizes
        return header + bb + bytes(im)
    
    def _from_png(self, data):
        im, shape = read_png(data)
        
        if shape[0] != shape[1]:
            raise RuntimeError('Width and height must be equal in icon')
        if shape[0] not in VALID_SIZES:
            raise RuntimeError('Invalid size %r in png' % width)
        
        # Make RGBA if necessary
        if shape[2] == 3:
            im2 = bytearray(int(len(im)*1.333333333334))
            im2[3::4] = 255
            im2[0::4] = im[0::4]
            im2[1::4] = im[1::4]
            im2[2::4] = im[2::4]
        else:
            im2 = im  # already bytearray
        
        #return im2
        self._store_image(im2)
    
    def _to_png(self, im):
        size = self._image_size(im)
        return write_png(bytes(im), (size, size, 4))


if __name__ == '__main__':
    icondir = '/home/almar/projects/pyapps/iep/default/iep/resources/appicons/'
    icondir = '/Users/almar/py/iep/iep/resources/appicons/'
    #print(get_png_info(icondir+'ieplogo32.png'))
    
    
    #icon = Icon(icondir+'test.ico')
#     icon = Icon(icondir+'ieplogo16.png', icondir+'ieplogo32.png', 
#                 icondir+'ieplogo48.png', icondir+'ieplogo64.png', 
#                 icondir+'ieplogo128.png', icondir+'ieplogo256.png')
#     icon = Icon(icondir+'test16.bmp', icondir+'test32.bmp', 
#                 icondir+'test48.bmp', icondir+'test64.bmp', 
#                 icondir+'test128.bmp', icondir+'test256.bmp')
    icon = Icon(icondir + 'ieplogo.ico')
    icon.write(icondir+'test.ico')
    icon.write(icondir+'test.icns')
    icon.write(icondir+'test.png')
