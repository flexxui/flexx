""" HTML5 runtime based on XUL (i.e. Firefox browser engine)
"""

import os
import sys
import time
import shutil

from .common import HTML5Runtime, create_temp_app_dir


# todo: title should change with title of web page?
# todo: enable setting position/size at runtime?
# todo: enable fullscreen - does not seem to work on XUL
# todo: test/fix on Windows, OSX, raspberry


defaults = dict(vendor='None',
                name='zoof_ui_app',
                version='1.0',
                buildid='1',
                id='some.app@zoof.io',
                windowid='xx',
                title='XUL app runtime')


APPLICATION_INI = """
[App]
Vendor={vendor}
Name={name}
Version={version}
BuildID={buildid}
ID={id}

[Gecko]
MinVersion=1.8
MaxVersion=200.*
"""

MAIN_XUL = """
<?xml version="1.0"?>
<?xml-stylesheet href="chrome://global/skin/" type="text/css"?>

<window 
    xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"
    id="{windowid}"
    title="{title}"
    windowtype="zoofui:main"
    width="640"
    height="480"
    sizemode="normal"
    >
  <browser type="content" src="{url}" flex="1" disablehistory="true" />
    <keyset>
        <key id="key_fullScreen" keycode="VK_F11" command="View:FullScreen"/>
    </keyset>
</window>
""".lstrip()


MAIN_JS = """
"""
# persist="screenX screenY width height sizemode"


PREFS_JS = """
pref("toolkit.defaultChromeURI", "chrome://{name}/content/main.xul");

pref("toolkit.defaultChromeFeatures", "{windowfeatures}");
 
/* debugging prefs, disable these before you deploy your application! */
pref("browser.dom.window.dump.enabled", false);
pref("javascript.options.showInConsole", false);
pref("javascript.options.strict", false);
pref("nglayout.debug.disable_xul_cache", false);
pref("nglayout.debug.disable_xul_fastload", false);
"""


def create_xul_app(path, id, **kwargs):
    """ Create the files that determine the XUL app to launch
    """
    
    D = defaults.copy()
    D.update(kwargs)
    
    # Create values that need to be unique
    D['windowid'] = 'W' + id
    D['name'] = 'app_' + id
    D['id'] = 'app_' + id + '@zoof.io'
    
    # Fill in arguments in file contents
    manifest = 'content {name} content/'.format(**D)
    application_ini = APPLICATION_INI.format(**D)
    main_xul = MAIN_XUL.format(**D)
    main_js = MAIN_JS.format(**D)
    prefs_js = PREFS_JS.format(**D)
    
    # Clear
    if os.path.isdir(path):
        shutil.rmtree(path)
    
    # Create directory structure
    for subdir in ('',
                   'chrome', 'chrome/content', 
                   'chrome/icons', 'chrome/icons/default',
                   'defaults', 'defaults/preferences',
                   ):
        os.mkdir(os.path.join(path, subdir))
    
    # Create files
    for fname, text in [('chrome.manifest', 'manifest chrome/chrome.manifest'),
                        ('chrome/chrome.manifest', manifest),
                        ('application.ini', application_ini),
                        ('defaults/preferences/prefs.js', prefs_js),
                        ('chrome/content/main.js', main_js),
                        ('chrome/content/main.xul', main_xul),
                        ]:
        open(os.path.join(path, fname), 'wb').write(text.encode('utf-8'))
    
    # Icon
    if kwargs.get('icon'):
        icon = kwargs['icon']
        ext = os.path.splitext(icon)[1]
        icon_name = 'chrome/icons/default/%s%s' % (D['windowid'], ext)
        shutil.copy(icon, os.path.join(path, icon_name))


def get_firefox_exe():
    """ Get the path of the Firefox executable
    
    If the path could not be found, returns None. You may still be able
    to launch using "firefox" though.
    """
    paths = []
    
    # Collect possible locations
    if sys.platform.startswith('win'):
        paths.append('C:\\Program Files\\Mozilla Firefox\\firefox.exe')
        paths.append('C:\\Program Files\\Firefox\\firefox.exe')
        paths.append('C:\\Program Files (x86)\\Firefox\\firefox.exe')
    elif sys.platform.startswith('linux'):
        paths.append('/usr/lib/firefox/firefox')
        paths.append('/usr/lib64/firefox/firefox')
    elif sys.platform.startswith('darwin'):
        paths.append('/Applications/Firefox.app')
    
    # Try location until we find one that exists
    for path in paths:
        if os.path.isfile(path):
            return path
    else:
        return None


class XulRuntime(HTML5Runtime):
    """ HTML5 runtime based on Mozilla's XUL framework.
    """
    
    _app_count = 0
    
    def _launch(self):
        XulRuntime._app_count += 1
        
        # Temp folder to store app files
        app_path = create_temp_app_dir('xul', str(XulRuntime._app_count))
        id = os.path.basename(app_path).split('_', 1)[1]
        
        # Set size and position
        size = self._kwargs.get('size', (640, 480))
        pos = self._kwargs.get('pos', None)
        windowfeatures = 'width=%i, height=%i' % (size[0], size[1])
        if pos:
            windowfeatures += ', top=%i, left=%i' % (pos[0], pos[1])
        
        # More preparing
        self._kwargs['title'] = self._kwargs['title'] or 'XUL runtime'
        
        # Create files for app
        create_xul_app(app_path, id, windowfeatures=windowfeatures, 
                       **self._kwargs)
        
        # Get executable, create link if we can, so that our window is
        # not grouped with ff, and has a more meaningful process name.
        # Using sys.executable also works well when frozen.
        ff_exe = get_firefox_exe()
        if ff_exe:
            exename, ext = os.path.splitext(os.path.basename(sys.executable))
            exe = os.path.join(app_path, exename + '-ui' + ext)
            try:
                os.symlink(ff_exe, exe)
            except Exception:  # e.g. WinXP
                exe = ff_exe
        else:
            exe = 'firefox'
        
        # Launch
        print('launching XUL app')
        cmd = [exe, '-app', os.path.join(app_path, 'application.ini')]
        self._start_subprocess(cmd)
