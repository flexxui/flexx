import time
import os
import threading
import cProfile as profile

from flexx.lib import yoton2

class HelpThread(threading.Thread):
    
    def __init__(self, fun):
        threading.Thread.__init__(self)
        self._fun = fun
        
    def run(self):
        iter = 0
        while True:
            iter += 1
            try:
                msg = self._fun(iter)
            except StopIteration:
                break


w1, r1 = yoton2.bind()#'/tmp/zoof_speed_test')
w2, r2 = yoton2.connect(w1._m.filename)#'/tmp/zoof_speed_test')

msg_size = 100
niters = 1000

# w1._m.file.close()
# w2._m.file.close()
# os.remove(w1._m.filename)

##
themsg = 'a'*msg_size
def _writer(i):
    if i > niters: raise StopIteration()
    w1.write(themsg, True)

t = HelpThread(_writer)

profiler = profile.Profile()
profiler.enable()
t0 = time.time()
t.start()

for i in range(niters):
    msg = r2.read(True)
    assert msg

assert r2.read() is None
t1 = time.time()
profiler.disable()
ms = 1000 * (t1-t0) / niters
print('Message size %i: %1.2f ms' % (msg_size, ms))
profiler.print_stats(sort='tottime')  # ncalls, tottime, cumtime (incl subcalls)
