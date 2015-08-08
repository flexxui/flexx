"""
Example demonstrating lazy evaluation.
"""

import time

from flexx import react

class DataProcessor(react.HasSignals):
    
    @react.input
    def raw1(n=0):
        return float(n)
    
    @react.input
    def raw2(n=0):
        return float(n)
    
    @react.lazy('raw1')
    def processed1(data):
        print('processing 1 (slow)')
        time.sleep(1)
        return data + 10
    
    @react.lazy('raw2')
    def processed2(data):
        print('processing 2 (fast)')
        time.sleep(0.1)
        return data + 1
    
    @react.lazy('processed1', 'processed2')
    def result(data1, data2):
        return data1 + data2

p = DataProcessor()

# Get result, first time, we need to wait, next time is instant
print(p.result())
print(p.result())

# We can change the input, but nothing happens until we request a result
p.raw1(10)
p.raw1(50)
p.raw1(100)
print(p.result())

# Dito, but now we change raw2, so getting the result is fast
p.raw2(10)
p.raw2(50)
p.raw2(100)
print(p.result())
