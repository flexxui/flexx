# -*- coding: utf-8 -*-
# Copyright (c) 2016, Almar Klein
# This module is distributed under the terms of the new BSD License.

"""
Pure python module to handle for reading and writing png files. Written
for Python 2.7 and Python 3.2+. Can only read PNG's that are not
interlaced, have a bit depth of 8, and are either RGB or RGBA.
"""

from __future__ import print_function, division, absolute_import

import io
import struct
import zlib


def write_png(im, shape=None, file=None):
    """
    Write a png image. The written image is in RGB or RGBA format, with
    8 bit precision, and without interlacing.
    
    Parameters:
        im (bytes, bytearray, numpy-array): the image data to write.
        shape (tuple): the shape of the image. If ``im`` is a numpy array,
            the shape can be omitted. The shape can be ``(H, W)`` for
            grayscale, ``(H, W, 3)`` for RGB and ``(H, W, 4)`` for RGBA.
            Note that grayscale images are converted to RGB.
        file (file-like object, None): where to write the resulting
            image. If omitted or None, the result is returned as bytes.
    """
    
    # Check types
    if hasattr(im, 'shape') and hasattr(im, 'dtype'):
        if shape and tuple(shape) != im.shape:
            raise ValueError('write_png got mismatch in im.shape and shape')
        if im.dtype != 'uint8':
            raise TypeError('Image data to write to PNG must be uint8')
        shape = im.shape
        im = im.tobytes()
    elif isinstance(im, (bytes, bytearray)):
        if not isinstance(shape, (tuple, list)):
            raise ValueError('write_png needs a shape unless ndarray is given')
        shape = tuple(shape)
    else:
        raise ValueError('Invalid type for im, '
                         'need ndarray, bytearray or bytes, got %r' % type(im))
    
    # Allow grayscale: convert to RGB
    if len(shape) == 2 or (len(shape) == 3 and shape[2] == 1):
        im3 = bytearray(shape[0] * shape[1] * 3)
        im3[0::3] = im
        im3[1::3] = im
        im3[2::3] = im
        im = im3
        shape = shape[0], shape[1], 3
    
    # Check shape
    if len(shape) != 3:
        raise ValueError('shape must be 3 elements)')
    if shape[2] not in (3, 4):
        raise ValueError('shape[2] must be in (3, 4)')
    if (shape[0] * shape[1] * shape[2]) != len(im):
        raise ValueError('Shape does not match number of elements in image')
    
    # Get file object
    f = io.BytesIO() if file is None else file
    
    def add_chunk(data, name):
        name = name.encode('ASCII')
        crc = zlib.crc32(data, zlib.crc32(name))
        f.write(struct.pack('>I', len(data)))
        f.write(name)
        f.write(data)
        #f.write(crc.to_bytes(4, 'big'))  # python 3.x +
        f.write(struct.pack('>I', crc & 0xffffffff))
    
    f.write(b'\x89PNG\x0d\x0a\x1a\x0a')  # header
    
    # First chunk
    w, h = shape[1], shape[0]
    depth = 8
    ctyp = 0b0110 if shape[2] == 4 else 0b0010
    ihdr = struct.pack('>IIBBBBB', w, h, depth, ctyp, 0, 0, 0)
    add_chunk(ihdr, 'IHDR')
    
    # Chunk with pixels. Just one chunk, no fancy filters.
    line_len = w * shape[2]
    lines = [im[i*line_len:(i+1)*line_len] for i in range(h)]
    lines = [b'\x00' + bytes(line) for line in lines]  # prepend filter byt
    pixels_compressed = zlib.compress(b''.join(lines), 9)
    add_chunk(pixels_compressed, 'IDAT')
    
    # Closing chunk
    add_chunk(b'', 'IEND')
    
    if file is None:
        return f.getvalue()


def read_png(f, return_ndarray=False):
    """
    Read a png image. This is a simple implementation; can only read
    PNG's that are not interlaced, have a bit depth of 8, and are either
    RGB or RGBA.
    
    Parameters:
        f (file-object, bytes): the source to read the png data from.
        return_ndarray (bool): whether to return the result as a numpy array.
            Default False. If False, returns ``(pixel_array, shape)``,
            with ``pixel_array`` a bytearray object and shape being
            ``(H, W, 3)`` or ``(H, W, 4)``, for RGB and RGBA, respectively.
    """
    # http://en.wikipedia.org/wiki/Portable_Network_Graphics
    # http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html
    
    asint_map = {1: '>B', 2: '>H', 4: '>I'}
    asint = lambda x: struct.unpack(asint_map[len(x)], x)[0]
    
    # Get bytes
    if isinstance(f, (bytes, bytearray)):
        bb = f
    elif hasattr(f, 'read'):
        bb = f.read()
    else:
        raise TypeError('read_png() needs file object or bytes, not %r' % f)
    
    # Read header
    if not (bb[0:1] == b'\x89' and bb[1:4] == b'PNG'):
        raise RuntimeError('Image data does not appear to have a PNG '
                           'header: %r' % bb[:10])
    chunk_pointer = 8
    
    # Read first chunk
    chunk1 = bb[chunk_pointer:]
    chunk_length = asint(chunk1[0:4])
    chunk_pointer += 12 + chunk_length  # size, type, crc, data
    if not (chunk1[4:8] == b'IHDR' and chunk_length == 13):  # noqa
        raise RuntimeError('Unable to read PNG data, maybe its corrupt?')
    
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
    if filter_method != 0:
        raise RuntimeError('Can only deal with unfiltered data.')
    if compression_method != 0:
        # this should be the case for any PNG
        raise RuntimeError('Expected PNG compression param to be 0.')
    
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
        if not len(line) == line_len:  # noqa
            raise RuntimeError('Line length mismatch while reading png.')
        im[i:i+line_len] = line
        i += line_len
    
    shape = height, width, bytes_per_pixel
    
    # Done
    if return_ndarray:
        import numpy as np
        return np.frombuffer(im, 'uint8').reshape(shape)
    else:
        return im, shape


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
