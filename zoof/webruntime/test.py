from zoof.webruntime import launch

# Define icon
icon = None
#icondir = r'C:\almar\iep\iep\resources\appicons/'
#icondir = '/home/almar/projects/pyapps/iep/default/iep/resources/appicons/'
#icon = icondir + 'ieplogo32.png'


#target = 'file:///home/almar/projects/pylib/zoof/zoof/exp/learn_html5.html'
target = 'http://zoof.io'

rt1 = launch(target, 'xul', title='my xul app', icon=icon)
#rt2 = launch('http://zoof.io')
