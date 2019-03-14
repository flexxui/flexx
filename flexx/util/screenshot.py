""" Make screenshots of windows on Windows and Linux.
We need this to do visual tests.
"""

import sys

if sys.platform.startswith('win'):

    import ctypes
    from ctypes import windll
    from ctypes.wintypes import (BOOL, DOUBLE, DWORD, HBITMAP, HDC, HGDIOBJ,  # noqa
                                 HWND, INT, LPARAM, LONG, UINT, WORD)  # noqa

    SRCCOPY = 13369376
    DIB_RGB_COLORS = BI_RGB = 0

    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long),
                    ('top', ctypes.c_long),
                    ('right', ctypes.c_long),
                    ('bottom', ctypes.c_long)]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', DWORD), ('biWidth', LONG), ('biHeight', LONG),
                    ('biPlanes', WORD), ('biBitCount', WORD),
                    ('biCompression', DWORD), ('biSizeImage', DWORD),
                    ('biXPelsPerMeter', LONG), ('biYPelsPerMeter', LONG),
                    ('biClrUsed', DWORD), ('biClrImportant', DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', DWORD * 3)]

    # Function shorthands
    GetClientRect = windll.user32.GetClientRect
    GetWindowRect = windll.user32.GetWindowRect
    PrintWindow = windll.user32.PrintWindow
    GetWindowThreadProcessId = windll.user32.GetWindowThreadProcessId
    IsWindowVisible = windll.user32.IsWindowVisible
    EnumWindows = windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool,
                                         ctypes.POINTER(ctypes.c_int),
                                         ctypes.POINTER(ctypes.c_int))

    GetWindowDC = windll.user32.GetWindowDC
    CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
    CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
    SelectObject = windll.gdi32.SelectObject
    BitBlt = windll.gdi32.BitBlt
    DeleteObject = windll.gdi32.DeleteObject
    GetDIBits = windll.gdi32.GetDIBits

    # Arg types
    windll.user32.GetWindowDC.argtypes = [HWND]
    windll.gdi32.CreateCompatibleDC.argtypes = [HDC]
    windll.gdi32.CreateCompatibleBitmap.argtypes = [HDC, INT, INT]
    windll.gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
    windll.gdi32.BitBlt.argtypes = [HDC, INT, INT, INT, INT, HDC, INT, INT, DWORD]
    windll.gdi32.DeleteObject.argtypes = [HGDIOBJ]
    windll.gdi32.GetDIBits.argtypes = [HDC, HBITMAP, UINT, UINT, ctypes.c_void_p,
                                        ctypes.POINTER(BITMAPINFO), UINT]
    # Return types
    windll.user32.GetWindowDC.restypes = HDC
    windll.gdi32.CreateCompatibleDC.restypes = HDC
    windll.gdi32.CreateCompatibleBitmap.restypes = HBITMAP
    windll.gdi32.SelectObject.restypes = HGDIOBJ
    windll.gdi32.BitBlt.restypes = BOOL
    windll.gdi32.GetDIBits.restypes = INT
    windll.gdi32.DeleteObject.restypes = BOOL


    def win_for_pid(pid):
        """ Get the windows-handle for the first visible window of the
        process with the given id.
        """
        handles = []

        def called_for_each_win(hwnd, lParam):
            if not IsWindowVisible(hwnd):
                return True
            # get the proccessid from the windowhandle
            p_id = ctypes.c_int()
            #t_id = GetWindowThreadProcessId(hwnd, ctypes.byref(p_id))
            if p_id.value == pid:
                handles.append(hwnd)
                return False
            return True

        EnumWindows(EnumWindowsProc(called_for_each_win), 0)
        if handles:
            return handles[0]
        else:
            return None


    def screenshot(pid, client=True):
        """ Grab a screenshot of the first visible window of the process
        with the given id. If client is True, no Window decoration is shown.

        This code is derived from https://github.com/BoboTiG/python-mss
        """
        # Get handle
        hwnd = win_for_pid(pid)
        # Get window dimensions
        rect = RECT()
        if client:
            GetClientRect(hwnd, ctypes.byref(rect))
        else:
            GetWindowRect(hwnd, ctypes.byref(rect))
        left, right, top, bottom = rect.left, rect.right, rect.top, rect.bottom
        w, h = right - left, bottom - top

        hwndDC = saveDC = bmp = None
        try:
            # Get device contexts
            hwndDC = GetWindowDC(hwnd)
            saveDC = CreateCompatibleDC(hwndDC)
            # Get bitmap
            bmp = CreateCompatibleBitmap(hwndDC, w, h)
            SelectObject(saveDC, bmp)
            if client:
                PrintWindow(hwnd, saveDC, 1)  # todo: result is never used??
            else:
                PrintWindow(hwnd, saveDC, 0)
            # Init bitmap info
            # We grab the image in RGBX mode, so that each word is 32bit and
            # we have no striding, then we transform to RGB
            buffer_len = h * w * 4
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = w
            bmi.bmiHeader.biHeight = -h  # Why minus? See [1]
            bmi.bmiHeader.biPlanes = 1  # Always 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = BI_RGB
            # Blit
            image = ctypes.create_string_buffer(buffer_len)
            bits = windll.gdi32.GetDIBits(saveDC, bmp, 0, h, image, bmi, DIB_RGB_COLORS)
            assert bits == h
            # Replace pixels values: BGRX to RGB
            image2 = ctypes.create_string_buffer(h*w*3)
            image2[0::3] = image[2::4]
            image2[1::3] = image[1::4]
            image2[2::3] = image[0::4]

            return bytes(image2), (w, h, 3)

        finally:
            # Clean up
            if hwndDC:
                DeleteObject(hwndDC)
            if saveDC:
                DeleteObject(saveDC)
            if bmp:
                DeleteObject(bmp)


if __name__ == '__main__':
    im, shape = screenshot(5144, True)

    from flexx.util import icon
    png = icon.write_png(im, shape)
    open('C:\\Users\\Almar\\test.png', 'wb').write(png)
