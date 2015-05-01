from flexx.webruntime import launch

# Define icon
icon = None
#icondir = r'C:\almar\iep\iep\resources\appicons/'
#icondir = '/home/almar/projects/pyapps/iep/default/iep/resources/appicons/'
#icondir = '/Users/almar/py/iep/iep/resources/appicons/'
#icon = icondir + 'ieplogo.ico'


#target = 'file:///home/almar/projects/pylib/flexx/flexx/exp/learn_html5.html'
target = 'http://python.org'

rt1 = launch(target, 'xul', title='my xul app', icon=icon)
#rt2 = launch('http://python.org')
