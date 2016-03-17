"""
Implementation of basic event loop object. Can be integrated a real
event loop such as tornado or Qt.
"""


class EventLoop:
    def __init__(self):
        self._pending_calls = []
        
    def call_later(self, func):
        self._pending_calls.append(func)
    
    def iter(self):
        while self._pending_calls:
            func = self._pending_calls.pop(0)
            func()
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.iter()

loop = EventLoop()
