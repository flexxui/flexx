"""
Test icon module
"""

import os
import sys
import tempfile
from flexx.util.testing import run_tests_if_main, raises, skip

#from flexx.util.png import write_png
#from flexx.util.icon import Icon
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from util.png import write_png
from util.icon import Icon

tempdir = tempfile.gettempdir()

im1 = b'\x77' * 16*16
im2 = b'\x77' * 32*32
im3 = b'\x77' * 48*48
im4 = b'\x77' * 64*64

im8 = b'\x77' * 16*15
im9 = b'\x77' * 17*16

shapes = (16, 16), (32, 32), (48, 48), (64, 64), (), (), (), (16, 15), (17, 16)
ims = im1, im2, im3, im4, None, None, None, im8, im9


def test_reading_from_png():
    
    # Empty icon
    icon = Icon()
    assert icon.image_sizes() == ()
    assert '0 sizes' in repr(icon)
    
    # Write images
    filenames = [None for x in ims]
    for i in range(len(ims)):
        if ims[i]:
            filename = os.path.join(tempdir, 'ico%i.png' % i)
            with open(filename, 'wb') as f:
                write_png(ims[i], shapes[i], f)
            filenames[i] = filename
    
    # One image in the icon
    icon = Icon(filenames[0])
    assert icon.image_sizes() == (16, )
    assert '1 sizes' in repr(icon)
    
    # Four images in the icon
    icon = Icon(*filenames[:4])
    assert icon.image_sizes() == (16, 32, 48, 64)
    assert '4 sizes' in repr(icon)
    
    # Two image in the icon
    icon = Icon(filenames[1], filenames[3])
    assert icon.image_sizes() == (32, 64)
    assert '2 sizes' in repr(icon)
    
    # Add images
    icon.read(filenames[2])
    assert icon.image_sizes() == (32, 48, 64)
    assert '3 sizes' in repr(icon)


def test_read_wrong():
    with raises(TypeError):
        Icon(4)
    
    with raises(IOError):
        Icon('file does not exist')
    
    with raises(IOError):
        Icon('http://url does not exist')
    
    with raises(TypeError):
        Icon(['no', 'lists'])
    
    if sys.version_info[0] > 2:
        with raises(TypeError):
            Icon(b'not a filename')


def test_reading_from_url():
    
    icon = Icon('https://assets-cdn.github.com/favicon.ico')
    assert len(icon.image_sizes()) > 0
    
    # Write locally
    icon.write(os.path.join(tempdir, 'gh.ico'))
    icon.write(os.path.join(tempdir, 'gh.icns'))


def test_reading_from_base64():
    black_png = ('iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAIUlEQVR42mNgY'
                 'GD4TyEeTAacOHGCKDxqwKgBtDVgaGYmAD/v6XAYiQl7AAAAAElFTkSuQmCC')
    
    icon = Icon('data:image/png;base64,' + black_png)
    assert icon.image_sizes() == (16, )


def test_export():
    
    # Test using some icons over which I have some control
    B = 'https://bitbucket.org/iep-project/iep/raw/tip/iep/resources/appicons/'
    
    for name in ['ieplogo', 'py']:
        icon = Icon(B + name + '.ico')
        assert len(icon.image_sizes()) > 0
        
        # Export png
        filename = os.path.join(tempdir, name + '.png')
        icon.write(filename)
        for i in icon.image_sizes():
            assert os.path.isfile(os.path.join(tempdir, name + '%i.png' % i))
        
        # Export bmp
        filename = os.path.join(tempdir, name + '.bmp')
        icon.write(filename)
        for i in icon.image_sizes():
            assert os.path.isfile(os.path.join(tempdir, name + '%i.bmp' % i))
        
        # Failures ..
        
        with raises(TypeError):
            icon.write(3)
        
        with raises(TypeError):
            icon.write([])
        
        if sys.version_info[0] > 2:
            with raises(TypeError):
                icon.write(filename.encode())
        
        with raises(ValueError):
            icon.write(os.path.join(tempdir, name + '.foo'))


run_tests_if_main()
