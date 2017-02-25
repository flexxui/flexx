# -*- coding: utf-8 -*-
# Copyright (c) 2015-2017, Almar Klein
# This module is distributed under the terms of the new BSD License.

"""
Pure python module to handle the .ico format. Written for Python 2.7
and Python 3.2+. Depends on png.py.
"""

from __future__ import print_function, division, absolute_import

import sys
import struct

from .png import read_png, write_png

if sys.version_info[0] >= 3:
    basestring = str  # noqa
    from base64 import decodebytes
else:
    from base64 import decodestring as decodebytes


# Note: up to 256 is support by our .ico exporter
VALID_SIZES = 16, 32, 48, 64, 128, 256, 512, 1024

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


class Icon(object):
    """
    Object for reading/creating icons. Considers only RGBA icons. Can
    deal with images stored raw (BMP) and compressed (PNG).
    """
    # Conventions:
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
        """ Get a tuple of image sizes (integers) currently loaded.
        """
        return tuple(sorted(self._ims.keys()))
    
    def add(self, data):
        """ Add an image represented as bytes or bytearray. The size
        of the image is inferred from the number of bytes. The image
        is assumed to be square and in RGBA format.
        """
        if isinstance(data, (bytes, bytearray)):
            self._store_image(data)
        else:
            raise ValueError('Data to add should be bytes or bytearray')
    
    def read(self, filename):
        """ Read an image from the given filename and add to collection.
        Can be an ICO, PNG, or BMP file.  When a grayscale or RGB image
        is read, it is converted to RGBA. Some restrictions may apply
        to the formats that can be read.
        """
        if not isinstance(filename, basestring):
            raise TypeError('Icon.read() needs a file name')
        
        if filename.startswith(('http://', 'https://')):
            # Remote resource
            try:
                from urllib.request import urlopen  # Python 3.x
            except ImportError:
                from urllib2 import urlopen  # Python 2.x
            data = urlopen(filename, timeout=2.0).read()
        elif filename.startswith('data:image/') and 'base64' in filename[:32]:
            # Base64 encoded asset
            data = decodebytes(filename.split(',', 1)[-1].encode())
            filename = '.' + filename.split(';')[0].split('/')[-1]
        else:
            data = open(filename, 'rb').read()
        
        self.from_bytes(filename, data)
    
    def from_bytes(self, ext, data):
        """ Read an image from the raw bytes of the encoded image. The format
        is specified by the extension (or filename).
        """
        if ext.lower().endswith('.ico'):
            self._from_ico(data)
        elif ext.lower().endswith('.png'):
            self._from_png(data)
        elif ext.lower().endswith('.bmp'):
            self._from_bmp(data)
        else:
            raise ValueError('Can only load from png, bmp, or ico')
    
    def write(self, filename):
        """ Write the icon collection to an image with the given filename.
        Can be an ICO, ICNS, PNG, or BMP file. In case of PNG/BMP,
        multiple images may be generated, the image size is appended
        to the file name.
        """
        if not isinstance(filename, basestring):
            raise TypeError('Icon.write() needs a file name')
        
        if filename.lower().endswith('.ico'):
            data = self._to_ico()
            with open(filename, 'wb') as f:
                f.write(data)
        elif filename.lower().endswith('.icns'):
            data = self._to_icns()
            with open(filename, 'wb') as f:
                f.write(data)
        elif filename.lower().endswith('.png'):
            for size in sorted(self._ims):
                filename2 = '%s%i%s' % (filename[:-4], size, filename[-4:])
                data = self._to_png(self._ims[size])
                with open(filename2, 'wb') as f:
                    f.write(data)
        elif filename.lower().endswith('.bmp'):
            for size in sorted(self._ims):
                filename2 = '%s%i%s' % (filename[:-4], size, filename[-4:])
                data = self._to_bmp(self._ims[size], file_header=True)
                with open(filename2, 'wb') as f:
                    f.write(data)
        else:
            raise ValueError('Can only export to png, bmp, or ico')
    
    def to_bytes(self):
        """ Return the bytes that represent the .ico image.
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
            if size > 256:
                continue
            elif size >= 64:
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
        
        if not imdatas:
            raise RuntimeError('Exported icon is empty '
                               '(none of the sizes was supported).')
        
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
                imdatas.append(bytes(data))
                # RGBA to A
                data = bytearray(len(im)//4)
                data[:] = im[3::4]
                # Store alpha
                imdatas.append(apha_type)
                imdatas.append(struct.pack('>I', len(data) + 8))
                imdatas.append(bytes(data))
            elif False:  # size in png_types:
                # Store as png, does not seem to work
                data = self._to_png(im)
                imdatas.append(png_types[size])
                imdatas.append(struct.pack('>I', len(data) + 8))
                imdatas.append(bytes(data))
            else:
                # print('Skipping export size %i to .icns' % size)
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
        #color_planes = intl(bb[12:14])
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
            raise RuntimeError('Invalid size %r in png' % shape[0])
        
        # Make RGBA if necessary
        if shape[2] == 3:
            im2 = bytearray(int(len(im)*1.333333333334))
            im2[3::4] = b'\xff' * (shape[0] * shape[1])
            im2[0::4] = im[0::3]
            im2[1::4] = im[1::3]
            im2[2::4] = im[2::3]
        else:
            im2 = im  # already bytearray
        
        #return im2
        self._store_image(im2)
    
    def _to_png(self, im):
        size = self._image_size(im)
        return write_png(bytes(im), (size, size, 4))
