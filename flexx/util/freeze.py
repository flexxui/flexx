""" Utilities for freezing apps that use Flexx.
"""

import os
import sys
import shutil
import importlib


def copydir(path1, path2):
    # like shutil.copytree, but ...
    # * ignores __pycache__directories
    # * ignores hg, svn and git directories
    # Ensure destination directory does exist
    if not os.path.isdir(path2):
        os.makedirs(path2)
    # Itereate over elements
    count = 0
    for sub in os.listdir(path1):
        fullsub1 = os.path.join(path1, sub)
        fullsub2 = os.path.join(path2, sub)
        if sub in ['__pycache__', '.hg', '.svn', '.git']:
            continue
        elif sub.endswith('.pyc') and os.path.isfile(fullsub1[:-1]):
            continue
        elif os.path.isdir(fullsub1):
            count += copydir(fullsub1, fullsub2)
        elif os.path.isfile(fullsub1):
            shutil.copy(fullsub1, fullsub2)
            count += 1
    # Return number of copies files
    return count


def copy_module(module, app_dir):
    """ Copy the source of the given module to the given application directory.
    """
    if isinstance(module, str):
        module = importlib.import_module(module)
    filename = module.__file__
    if filename.endswith("__init__.py"):
        copydir(os.path.dirname(filename),
                os.path.join(app_dir, "source", module.__name__))
    elif filename.endswith(".py"):
        shutil.copy(filename,
                    os.path.join(app_dir, "source", module.__name__ + ".py"))


class SourceImporter:

    def __init__(self, dir):
        self.module_names = set()
        for name in os.listdir(dir):
            if name.endswith(".py"):
                self.module_names.add(name[:-3])
            elif "." not in name:
                self.module_names.add(name)

    def find_spec(self, fullname, path, target=None):
        if fullname.split(".")[0] in self.module_names:
            for x in sys.meta_path:
                if getattr(x, "__name__", "") == "PathFinder":
                    return x.find_spec(fullname, path, target)
        return None


def install():
    """ Install the imported to allow importing from source.
    """
    if getattr(sys, 'frozen', False):
        print(sys.meta_path)
        source_dir= os.path.join(sys._MEIPASS, 'source')
        sys.path.insert(0, source_dir)
        sys.meta_path.insert(0, SourceImporter(source_dir))
    for key in [x for x in sys.modules if x.startswith("flexx")]:
        sys.modules.pop(key)
