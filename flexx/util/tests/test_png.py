"""
Test png module
"""

import os
import sys
import tempfile
from flexx.util.testing import run_tests_if_main, raises, skip

#from flexx.util.png import read_png, write_png
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from util.png import read_png, write_png


try:
    import numpy as np
except ImportError:
    np = None


tempdir = tempfile.gettempdir()

shape0 = 100, 100
im0 = b'\x77' * 10000

shape1 = 5, 5
im1 = b''
im1 += b'\x00\x00\x99\x00\x00'
im1 += b'\x00\x00\xff\x00\x00'
im1 += b'\x99\xff\xff\xff\x99'
im1 += b'\x00\x00\xff\x00\x00'
im1 += b'\x00\x00\x99\x00\x00'

shape2 = 6, 6
im2 = b''
im2 += b'\x00\x00\x00\x88\x88\x88'
im2 += b'\x00\x00\x00\x88\x88\x88'
im2 += b'\x00\x00\x00\x88\x88\x88'
im2 += b'\x44\x44\x44\xbb\xbb\xbb'
im2 += b'\x44\x44\x44\xbb\xbb\xbb'
im2 += b'\x44\x44\x44\xbb\xbb\xbb'

shape3 = 5, 5, 3
im3 = bytearray(5*5*3)
im3[0::3] = im0[:25]
im3[1::3] = im1[:25]
im3[2::3] = im2[:25]

shape4 = 5, 5, 4
im4 = bytearray(5*5*4)
im4[0::4] = im0[:25]
im4[1::4] = im1[:25]
im4[2::4] = im2[:25]
im4[3::4] = im0[:25]

ims = im0, im1, im2, im3, im4
shapes = shape0, shape1, shape2, shape3, shape4


def test_writing():
    
    # Get bytes
    b0 = write_png(im0, shape0)
    b1 = write_png(im1, shape1)
    b2 = write_png(im2, shape2)
    b3 = write_png(im3, shape3)
    b4 = write_png(im4, shape4)
    
    blobs = b0, b1, b2, b3, b4
    
    # Write to disk (also for visual inspection)
    for i in range(5):
        filename = os.path.join(tempdir, 'test%i.png' % i)
        with open(filename, 'wb') as f:
            f.write(blobs[i])
    print('wrote PNG test images to', tempdir)
    
    assert len(b1) < len(b4)  # because all zeros are easier to compress
    
    # Check that providing file object yields same result
    with open(filename+'.check', 'wb') as f:
        write_png(im4, shape4, f)
    bb1 = open(filename, 'rb').read()
    bb2 = open(filename+'.check', 'rb').read()
    assert len(bb1) == len(bb2)
    assert bb1 == bb2

    # Check bytesarray
    b4_check = write_png(bytearray(im4), shape4)
    assert b4_check == b4
    
    # Test shape with singleton dim
    b1_check = write_png(im1, (shape1[0], shape1[1], 1))
    assert b1_check == b1


def test_writing_failures():
        
    with raises(ValueError):
        write_png([1, 2, 3, 4], (2, 2))
    
    with raises(ValueError):
        write_png(b'x'*10)
        
    with raises(ValueError):
        write_png(b'x'*10, (3, 3))
    
    write_png(b'x'*12, (2, 2, 3))
    
    with raises(ValueError):
        write_png(b'x'*8, (2, 2, 2))
    
    with raises(ValueError):
        write_png(b'x'*20, (2, 2, 5))
    
    with raises(ValueError):
        write_png(b'x'*13, (2, 2, 3))


def test_reading():
    
    # # Read using filename (also as unicode)
    # for i in range(5):
    #     filename = os.path.join(tempdir, 'test%i.png' % i)
    #     if sys.version_info[0] == 2 and i > 2:
    #         filename = unicode(filename)
    #     im, shape = read_png(filename)
    #     assert isinstance(im, bytearray)
    #     assert shape[:len(shapes[i])] == shapes[i]
    #     assert im == ims[i]
    
    # Read using file object
    for i in range(5):
        filename = os.path.join(tempdir, 'test%i.png' % i)
        with open(filename, 'rb') as f:
            im, shape = read_png(f)
        assert isinstance(im, bytearray)
        if len(shapes[i]) == 2:
            assert shape == shapes[i] + (3, )
            assert im[::3] == ims[i]
        else:
            assert shape == shapes[i]
            assert im == ims[i]
    
    # Read using binary blob
    for i in range(5):
        filename = os.path.join(tempdir, 'test%i.png' % i)
        with open(filename, 'rb') as f:
            blob = f.read()
            im, shape = read_png(blob)
        if len(shapes[i]) == 2:
            assert shape == shapes[i] + (3, )
            assert im[::3] == ims[i]
        else:
            assert shape == shapes[i]
            assert im == ims[i]
    
    with raises((RuntimeError, TypeError)):  # RuntimeError on legacy py
        read_png('not_a_png_blob.png')
    with raises(TypeError):
        read_png([])
    with raises(RuntimeError):
        read_png(b'xxxxxxxxxxxxxxxxxxxx\x0axx')
    with raises(RuntimeError):
        read_png(b'\x00')
    
    if sys.version_info > (3, ):
        # seen as filenames on legacy py
        with raises(RuntimeError):
            read_png(b'')
        with raises(RuntimeError):
            read_png(b'xxxxxxxxxxxxxxxxxxxx')


def test_with_numpy():
    
    if np is None:
        skip('Numpy not available')
    
    im = np.random.normal(100, 50, (100, 100, 1)).astype(np.float32)
    with raises(TypeError):  # need uint8
        write_png(im)
    
    im = np.ones((100, 100, 1), np.uint8) * (7*16+7)
    blob = write_png(im)
    assert blob == write_png(im0, shape0)
    
    im = np.random.normal(100, 50, (100, 100)).astype(np.uint8)
    blob = write_png(im)
    
    im_bytes, shape = read_png(blob)
    assert isinstance(im_bytes, (bytearray, bytes))
    im_check = np.frombuffer(im_bytes, 'uint8').reshape(shape)
    assert im_check.shape == im.shape + (3, )
    for i in range(3):
        assert (im_check[:,:,i] == im).all()


run_tests_if_main()
