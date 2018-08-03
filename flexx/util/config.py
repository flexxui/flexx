from __future__ import print_function, absolute_import

import re
import os
import sys
import logging

if sys.version_info[0] == 2:  # pragma: no cover
    from ConfigParser import ConfigParser as _ConfigParser
    from StringIO import StringIO

    class ConfigParser(_ConfigParser):
        def read_string(self, string, source):
            return self.readfp(StringIO(string), source)

else:
    from configparser import ConfigParser


def as_bool(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, basestring) and value.lower() in BOOLEAN_STATES:
        return BOOLEAN_STATES[value.lower()]
    else:
        raise ValueError('Cannot make a bool of %r' % value)

def get_tuple_validator(subvalidator):
    def validator(value):
        if isinstance(value, (tuple, list)):
            value2 = tuple(value)
        elif isinstance(value, basestring):
            value2 = tuple([s.strip() for s in value.strip('()[]').split(',')])
        else:
            raise ValueError('Cannot make a tuple of %r' % value)
        return tuple([subvalidator(x) for x in value2])
    return validator

def stack_sorter(key):
    # Implement ordering, files and strings go at spot 1
    return dict(default=0, environ=2, argv=3, set=4).get(key[0], 1)


BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                  '0': False, 'no': False, 'false': False, 'off': False}

TYPEMAP = {float: float, int: int, bool: as_bool}
if sys.version_info[0] == 2:  # pragma: no cover
    TYPEMAP[basestring] = unicode  # noqa
    TYPEMAP[str] = unicode  # noqa
else:
    basestring = str
    TYPEMAP[str] = str

INSTANCE_DOCS = """ Configuration object for {name}

    The options below can be set from different sources, and are
    evaluated in the following order:

    * From the default value.
    * From .cfg or .ini file, or a string in cfg format.
    * From environment variables, e.g. ``{NAME}_FOO=3``.
    * From command-line arguments, e.g. ``--{name}-foo=3``.
    * From setting the config option directly, e.g. ``config.foo = 3``.

    Use ``print(config)`` to get a summary of the current values and
    from which sources they were set.

    Parameters:
    """


class Config(object):
    """ Class for configuration objects.

    A Config object has a set of options, which can be str, int, float,
    bool, or a tuple of any of the above. Options can be set from
    different sources:

    * Each option has a default value.
    * From .cfg or .ini files.
    * From strings in ini format.
    * From environment variables.
    * From command-line arguments.
    * By setting the config option directly.

    Parameters:
        name (str): the name by which to identify this config. This name
            is used as a prefix in environment variables and command
            line arguments, and optionally as a section header in .cfg files.
        *sources: Sources to initialize the option values with.
            These can be strings in ini format, or .ini or .cfg filenames.
            If a file is given that does not exist, it is simply ignored.
            Special prefixes ``~/`` and ``~appdata/`` are expanded to the
            home dir and appdata dir.
        **options: The options specification: each option consists of
            a 3-element tuple (default, type, docstring).

    Example:

        .. code-block:: Python

            config = Config('myconfig', '~appdata/.myconfig.cfg',
                            foo=(False, bool, 'Whether to foo'),
                            bar=(0.0, float, 'The size of the bar'),
                            spam=('1,2,3', [int], 'A tuple of ints'))

        With this, options can be set:

        * With an entry ``foo = 3`` in "~appdata/.myconfig.cfg".
        * With a string ``"foo = 3"`` passed at initialization.
        * With an environment variable named ``MYCONFIG_FOO``.
        * With a command line argument ``--myconfig-foo=3``.
        * By doing ``config.foo = 3``, or ``config['foo'] = 3`` in Python.

    Notes:
        * Option names are case insensitive, except for attribute access and
          environment variables (the latter must be all uppercase).
        * All values can be set as a Python object or a string; they
          are automatically converted to the correct type.
        * Each instance gets a docstring that lists all options, so it
          can easily be used in e.g. Sphynx docs.
    """

    def __init__(self, name, *sources, **options):

        # The identifier name for this config
        self._name = name
        if not is_valid_name(name):
            raise ValueError('Config name must be an alphanumeric string, '
                             'starting with a letter.')

        # The option names (unmodified case)
        self._options = []

        # Where the values are stored, we keep a stack, lowercase keys
        self._opt_values = {}  # name -> list of (source, value) tuples

        # Map of lowercase option names to validator functions
        self._opt_validators = {}

        # Map of lowercase option names to type names, for better reporting
        self._opt_typenames = {}

        # Map of lowercase option names to docstrings
        self._opt_docs = {}

        # Parse options
        option_docs = ['']
        for name in sorted(options.keys(), key=lambda x: x.lower()):
            lname = name.lower()
            spec = options[name]
            # Checks
            if not is_valid_name(name):
                raise ValueError('Option name must be alphanumeric strings, '
                                 'starting with a letter, and not private.')
            if not len(spec) == 3:
                raise ValueError('Option spec must be (default, type, docs)')
            default, typ, doc = spec
            istuple = False
            if isinstance(typ, (tuple, list)):
                if len(typ) != 1:
                    raise ValueError('Tuple type spec should have one element.')
                istuple, typ = True, typ[0]
            if not (isinstance(typ, type) and issubclass(typ, tuple(TYPEMAP))):
                raise ValueError('Option types can be str, bool, int, float.')
            # Parse
            typename = typ.__name__ + ('-tuple' if istuple else '')
            args = name, typename, doc, default
            option_docs.append(' '*8 + '%s (%s): %s (default %r)' % args)
            self._options.append(name)
            self._opt_typenames[lname] = typename
            self._opt_validators[lname] = (get_tuple_validator(TYPEMAP[typ])
                                           if istuple else TYPEMAP[typ])
            self._opt_docs[lname] = doc
            self._opt_values[lname] = []

        # Overwrite docstring
        self.__doc__ = INSTANCE_DOCS.format(name=self._name,
                                            NAME=self._name.upper())
        self.__doc__ += '\n'.join(option_docs)

        # --- init values

        # Set defaults
        for name, spec in options.items():
            self._set('default', name, spec[0])

        # Load from sources
        for source in sources:
            if not isinstance(source, basestring):
                raise ValueError('Sources should be strings or filenames.')
            if '\n' in source:
                self.load_from_string(source)
            else:
                self.load_from_file(source)

        # Load from environ
        for name in self._opt_values:
            env_name = (self._name + '_' + name).upper()
            value = os.getenv(env_name, None)  # getenv is case insensitive
            if value is not None:
                self._set('environ', name, value)

        # Load from argv
        arg_prefix = '--' + self._name.lower() + '-'
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if arg.lower().startswith(arg_prefix) and '=' in arg:
                name, value = arg[len(arg_prefix):].split('=', 1)
                if name.lower() in self._opt_values:
                    self._set('argv', name, value)

    def __repr__(self):
        t = '<Config %r with %i options at 0x%x>'
        return t % (self._name, len(self._options), id(self))

    def __str__(self):
        # Return a string representing a summary of the options and
        # how they were set from different sources.
        lines = []
        lines.append('Config %r with %i options.' %
                     (self._name, len(self._options)))
        for name in self._options:
            lname = name.lower()
            lines.append('\nOption %s (%s) - %s' % (name,
                                                  self._opt_typenames[lname],
                                                  self._opt_docs[lname]))
            for source, val in self._opt_values[lname]:
                lines.append('    %r from %s' % (val, source))
            lines[-1] = ' -> ' + lines[-1][4:]  # Mark current value
        return '\n'.join(lines)

    def __len__(self):
        return len(self._options)

    def __iter__(self):
        return self._options.__iter__()

    def __dir__(self):
        return self._options

    def __getattr__(self, name):
        # Case sensitive get
        if not name.startswith('_') and name in self._options:
            return self._opt_values[name.lower()][-1][1]
        return super(Config, self).__getattribute__(name)

    def __getitem__(self, name):
        # Case insensitive get
        if not isinstance(name, basestring):
            raise TypeError('Config only allows subscripting by name strings.')
        if name.lower() in self._opt_values:
            return self._opt_values[name.lower()][-1][1]
        else:
            raise IndexError('Config has no option %r' % name)

    def __setattr__(self, name, value):
        # Case sensitive set
        if not name.startswith('_') and name in self._options:
            return self._set('set', name, value)
        return super(Config, self).__setattr__(name, value)

    def __setitem__(self, name, value):
        # Case insensitve set
        if not isinstance(name, basestring):
            raise TypeError('Config only allows subscripting by name strings.')
        if name.lower() in self._opt_values:
            return self._set('set', name, value)
        else:
            raise IndexError('Config has no option %r' % name)

    def _set(self, source, name, value):
        # The actual setter (case insensitive), applies the validator
        validator = self._opt_validators[name.lower()]
        try:
            real_value = validator(value)
        except Exception:
            args = name, self._opt_typenames[name.lower()], value
            raise ValueError('Cannot set option %s (%s) from %r' % args)
        stack = self._opt_values[name.lower()]
        if stack and stack[-1][0] == source:
            stack[-1] = source, real_value
        else:
            stack.append((source, real_value))
            stack.sort(key=stack_sorter)

    def load_from_file(self, filename):
        """ Load config options from a file, as if it was given as a
        source during initialization. This means that options set via
        argv, environ or directly will not be influenced.
        """
        # Expand special prefix
        filename = filename.replace('~appdata/', appdata_dir() + '/')
        filename = filename.replace('~appdata\\', appdata_dir() + '\\')
        filename = os.path.expanduser(filename)
        # Proceed if is an actual file
        if os.path.isfile(filename):
            text = None
            try:
                text = open(filename, 'rb').read().decode()
            except Exception as err:
                logging.warn('Could not read config from %r:\n%s' %
                             (filename, str(err)))
                return
            self.load_from_string(text, filename)

    def load_from_string(self, text, filename='<string>'):
        """ Load config options from a string, as if it was given as a
        source during initialization. This means that options set via
        argv, environ or directly will not be influenced.
        """
        try:
            self._load_from_string(text, filename)
        except Exception as err:
            logging.warn(str(err))

    def _load_from_string(self, s, filename):
        # Create default section, so that users can work with sectionless
        # files (as is common in an .ini file)
        name_section = '[%s]\n' % self._name
        if name_section not in s:
            s = name_section + s
        s += '\n'
        parser = ConfigParser()
        parser.read_string(s, filename)
        if parser.has_section(self._name):
            for name in self._options:
                if parser.has_option(self._name, name):
                    value = parser.get(self._name, name)
                    self._set(filename, name, value)


def is_valid_name(n):
    return isidentifier(n) and not n.startswith('_')


def isidentifier(s):
    # http://stackoverflow.com/questions/2544972/
    if not isinstance(s, basestring):  # noqa
        return False
    return re.match(r'^\w+$', s, re.UNICODE) and re.match(r'^[0-9]', s) is None


# From pyzolib/paths.py (https://bitbucket.org/pyzo/pyzolib/src/tip/paths.py)
def appdata_dir(appname=None, roaming=False):
    """ Get the path to the application directory, where applications
    are allowed to write user specific files (e.g. configurations).
    """
    # Define default user directory
    userDir = os.path.expanduser('~')
    # Get system app data dir
    path = None
    if sys.platform.startswith('win'):
        path1, path2 = os.getenv('LOCALAPPDATA'), os.getenv('APPDATA')
        path = (path2 or path1) if roaming else (path1 or path2)
    elif sys.platform.startswith('darwin'):
        path = os.path.join(userDir, 'Library', 'Application Support')
    # On Linux and as fallback
    if not (path and os.path.isdir(path)):  # pragma: no cover
        path = os.environ.get(
            "XDG_CONFIG_HOME",
            os.path.expanduser(os.path.join("~", ".config")))
    # Maybe we should store things local to the executable (in case of a
    # portable distro or a frozen application that wants to be portable)
    prefix = sys.prefix
    if getattr(sys, 'frozen', None):  # See application_dir() function
        prefix = os.path.abspath(os.path.dirname(sys.executable))
    for reldir in ('settings', '../settings'):
        localpath = os.path.abspath(os.path.join(prefix, reldir))
        if os.path.isdir(localpath):  # pragma: no cover
            try:
                open(os.path.join(localpath, 'test.write'), 'wb').close()
                os.remove(os.path.join(localpath, 'test.write'))
            except IOError:
                pass  # We cannot write in this directory
            else:
                path = localpath
                break
    # Get path specific for this app
    if appname:  # pragma: no cover
        if path == userDir:
            appname = '.' + appname.lstrip('.')  # Make it a hidden directory
        path = os.path.join(path, appname)
        if not os.path.isdir(path):  # pragma: no cover
            os.mkdir(path)
    # Done
    return path


if __name__ == '__main__':

    sys.argv.append('--test-foo=8')
    c = Config('test',
               foo=(3, int, 'foo yeah'),
               spam=(2.1, float, 'a float!'))
