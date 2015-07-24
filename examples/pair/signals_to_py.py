"""
Example demonstrating how signals in Py can connect to signals in JS.
"""

from flexx import react
from flexx import pair


@pair.app
class Clock(pair.Pair):
    
    @react.act('time')
    def show_time(t):
        print(t)
    
    class JS:
        
        def _init(this):
            that = this
            def _set_time():
                that.time._set(perf_counter())  # perf_counter() is a PyScript feature
            
            setInterval(_set_time, 200)
        
        @react.source
        def time(t):
            return float(t)

clock = Clock.launch('nodejs')
pair.run()
