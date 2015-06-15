import os
import sys
import subprocess

import flexx
from selenium import webdriver
#from sauceclient import SauceClient

# it's best to remove the hardcoded defaults and always get these values
# from environment variables
credfile = os.path.join(flexx.__file__, '..', '..', '.git', 'sauce')
USERNAME, ACCESS_KEY = open(credfile, 'rt').read().strip().split('\n')

# sauce = SauceClient(USERNAME, ACCESS_KEY)

browsers = [{"platform": "Mac OS X 10.9",
             "browserName": "chrome",
             "version": "31"},
            {"platform": "Windows 8.1",
             "browserName": "internet explorer",
             "version": "11"}]

sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
desired_capabilities = browsers[0]
desired_capabilities['name'] = 'some_id'

driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor=sauce_url % (USERNAME, ACCESS_KEY)
        )
driver.implicitly_wait(30)

##


def open_native(x):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', x))
    elif sys.platform.startswith('win'):
        subprocess.call(('start', x), shell=True)
    elif sys.platform.startswith('linux'):
        # xdg-open is available on all Freedesktop.org compliant distros
        # http://superuser.com/questions/38984/linux-equivalent-command-for-open-command-on-mac-windows
        subprocess.call(('xdg-open', x))

def show():
    png = driver.get_screenshot_as_png()
    filename = 'c:\\Users\\Almar\\sauce.png'
    open(filename, 'wb').write(png)
    open_native(filename)
