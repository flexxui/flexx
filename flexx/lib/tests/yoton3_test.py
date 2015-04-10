from zoof.lib.yoton3 import Connection

c1 = Connection()
c2 = Connection()

c1.bind('localhost:yoton3test')

c2.connect('localhost:yoton3test')