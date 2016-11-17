"""
Flexx has a command line interface to perform some simple tasks.
Invoke it via ``python -m flexx``. Additional command line arguments
can be provided to configure Flexx, see 
:func:`configuring flexx <flexx.config>`.

.. code-block:: none

"""

import sys

ALIASES = {'-h': 'help', '--help': 'help',
           '--version': 'version',
          }

class CLI:
    """ Command line interface class. Commands are simply defined as methods.
    """
    
    def __init__(self, args=None):
        if args is None:
            return
        
        command = args[0] if args else 'help'
        command = ALIASES.get(command, command)
        
        if command not in self.get_command_names():
            raise RuntimeError('Invalid command %r' % command)
        
        func = getattr(self, 'cmd_' + command)
        func(*args[1:])
    
    def get_command_names(self):
        commands = [d[4:] for d in dir(self) if d.startswith('cmd_')]
        commands.sort()
        return commands
    
    def get_global_help(self):
        lines = []
        lines.append('Flexx command line interface')
        lines.append('  python -m flexx <command> [args]')
        lines.append('')
        for command in self.get_command_names():
            doc = getattr(self, 'cmd_' + command).__doc__
            if doc:
                summary = doc.strip().splitlines()[0]
                lines.append('%s %s' % (command.ljust(15), summary))
        return '\n'.join(lines)
    
    def cmd_help(self, command=None):
        """ show information on how to use this command.
        """
        
        if command:
            if command not in self.get_command_names():
                raise RuntimeError('Invalid command %r' % command)
            doc = getattr(self, 'cmd_' + command).__doc__
            if doc:
                lines = doc.strip().splitlines()
                doc = '\n'.join([lines[0]] + [line[8:] for line in lines[1:]])
                print('%s - %s' % (command, doc))
            else:
                print('%s - no docs' % command)
        else:
            print(self.get_global_help())
    
    def cmd_version(self):
        """ print the version number
        """
        import flexx
        print(flexx.__version__)
    
    def cmd_info(self, port=None):
        """ show info on flexx server process corresponding to given port,
        e.g. flexx info 8080
        The kind of info that is provided is not standardized/documented yet.
        """
        if port is None:
            return self.cmd_help('info')
        port = int(port)
        try:
            print(http_fetch('http://localhost:%i/flexx/cmd/info' % port))
        except FetchError:
            print('There appears to be no local server at port %i' % port)
    
    def cmd_stop(self, port=None):
        """ stop the flexx server process corresponding to the given port.
        """
        if port is None:
            return self.cmd_help('stop')
        port = int(port)
        try:
            print(http_fetch('http://localhost:%i/flexx/cmd/stop' % port))
            print('stopped server at %i' % port)
        except FetchError:
            print('There appears to be no local server at port %i' % port)
    
    def cmd_log(self, port=None, level='info'):
        """ Start listening to log messages from a server process - STUB
        flexx log port level
        """
        if port is None:
            return self.cmd_help('log')
        print('not yet implemented')
        #print(http_fetch('http://localhost:%i/flexx/cmd/log' % int(port)))


class FetchError(Exception):
    pass

def http_fetch(url):
    """ Perform an HTTP request.
    """
    from tornado.httpclient import HTTPClient
    http_client = HTTPClient()
    try:
        response = http_client.fetch(url)
    except Exception as err:
        raise FetchError('http fetch failed: %s' % str(err))
    finally:
        http_client.close()
    return response.body.decode()


# Prepare docss
_cli_docs = CLI().get_global_help().splitlines()
__doc__ += '\n'.join(['    ' + line for line in _cli_docs])


def main():
    # Main entry point (see setup.py)
    CLI(sys.argv[1:])


if __name__ == '__main__':
    main()
