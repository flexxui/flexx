"""
Simple script to generate Flexx' icon for different sizes.
"""

import os
import base64

import numpy as np

import flexx
from flexx.util.icon import Icon


# colors:
# (70, 140, 210) - Python blue
# (240, 80, 80) - a strong red


def create_icon(N=16, COLOR=(240, 80, 80)):

    im = np.zeros((N, N), np.bool)

    row_index = [0, 1, 1, 1, 1, 0, 2, 2, 2, 2, 0, 3, 3, 3, 3, 0]
    col_index1 = [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    col_index2 = [0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    col_index3 = [0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0]
    col_index = None, col_index1, col_index2, col_index3


    # Create template image
    for y in range(N):
        for x in range(N):
            row16 = int(y * 16 / N)
            col16 = int(x * 16 / N)
            inrow = row_index[row16]

            if inrow:
                incol = col_index[inrow][col16]

                if incol:
                    im[y, x] = True

    im = np.flipud(im)  # images have y up

    # Colorize
    rgba = np.zeros((N, N, 4), np.uint8)
    for y in range(N):
        for x in range(N):
            if im[y, x]:
                rgba[y, x, :3] = COLOR
                rgba[y, x, 3] = 255
            elif im[max(0, y-1):y+2, max(0, x-1):x+2].any():
                factor = im[max(0, y-1):y+2, max(0, x-1):x+2].sum()
                rgba[y, x, :3] = COLOR
                rgba[y, x, :3] //= 2
                rgba[y, x, 3] = 64 * (0.66 if factor == 1 else 1)
            # else:
            #     rgba[y, x, :3] = 0, 0, 0
            #     rgba[y, x, 3] = 128

    return rgba


def create_icons():
    icon = Icon()
    for n in (16, 32, 48, 64, 128, 256):
        icon.add(create_icon(n).tobytes())
    icon.write(os.path.join(flexx.__path__[0], 'resources', 'flexx.ico'))


def create_silly_icon():

    im = np.zeros((16, 16, 4), 'uint8')
    im[3:-3, 3:-3] = 200
    im[:, :, 3] = 255

    icon = Icon()
    icon.add(im.tobytes())
    bb = icon._to_png(icon._ims[16])
    print(base64.encodebytes(bb).decode())


if __name__ == '__main__':

    rgba = create_icon(48)

    import visvis as vv
    vv.figure(1)
    vv.clf()
    vv.imshow(rgba)

    create_icons()
