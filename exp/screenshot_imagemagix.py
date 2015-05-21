"""
* Uses imagamagix' import command (nearly always available on Linux
* Uses wmctrl. small utility to obtain via apt-get

Would this work on Travis?
"""
import subprocess

L = subprocess.getoutput(['wmctrl -l -p'])
for line in L.splitlines():
    parts = [part for part in line.split(' ') if part]
    id, _, pid, *rest = parts
    if pid == str(app._runtime._proc.pid):
        theid = id
        break
else:
    raise ValueError('Not found')

subprocess.check_call(['import', '-window', theid, '/home/almar/screen.png'])