""" IPC via websockets

Mimic the API of yoton2 (the mmap one) but implementation is via a
websocket. This provides a way for languages that do not support mmap
(like JavaScript) to be used from Zoof.
"""

import websockets

def foo(*args):
    print(args)

s1 = websockets.WebSocketServerProtocol(foo, host='localhost', port=8765)


s2 = websockets.WebSocketClientProtocol(host='localhost', port=8765)

