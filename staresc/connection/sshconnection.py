import logging
from typing import Tuple

import paramiko

from staresc.exceptions import StarescAuthenticationError, StarescCommandError, StarescConnectionError
from staresc.connection import Connection

logger = logging.getLogger(__name__)

class SSHConnection(Connection):
    """SSHConnection is the main Connection implementation for SSH

    high level object for the commands and data we're sending to the target host
    """

    client: paramiko.SSHClient

    class CompletelyIgnore(paramiko.MissingHostKeyPolicy):
        
        def __init__(self) -> None:
            """CompletelyIgnore is a custom policy 
        
            It ignores missing keys in paramiko. 
            It will do nothing if keys aren't found
            """
            super().__init__()


        def missing_host_key(self, client, hostname, key):
            """
            Called when an .SSHClient receives a server key for a server that 
            isn't in either the system or local .HostKeys object. To accept the 
            key, simply return. To reject, raised an exception (which will be 
            passed to the calling application).

            This implementation does nothing when receiving the keys.
            """
            pass

    def __init__(self, connection: str) -> None:
        super().__init__(connection)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(self.CompletelyIgnore)


    def connect(self):
        """SSH implementation to connect to the target server

        It uses paramiko to handle SSH communication. 

        Raises:
            StarescAuthenticationError -- raised when login fails
            StarescConnectionError -- raised when the program can't connect to the target 
        """

        paramiko_args = {
            'hostname'      : self.get_hostname(self.connection),
            'port'          : self.get_port(self.connection),
            'allow_agent'   : False,
            'look_for_keys' : False
        }
        paramiko_args['username'], paramiko_args['password'] = self.get_credentials(self.connection)
        if '/' in paramiko_args['password']:
            paramiko_args['pkey']     = paramiko.RSAKey.from_private_key_file(paramiko_args['password'])
            paramiko_args['password'] = None

        try:
            self.client.connect(**paramiko_args)
            self.client.get_transport().set_keepalive(5)

        except paramiko.AuthenticationException:
            msg = f"Authentication failed for {paramiko_args['username']} with password {paramiko_args['password']}"
            raise StarescAuthenticationError(msg)

        except (paramiko.SSHException, paramiko.ssh_exception.NoValidConnectionsError):
            msg = f"An error occured when trying to connect"
            raise StarescConnectionError(msg)
            

    def run(self, cmd: str, timeout: float = Connection.command_timeout, bufsize: int = 4096) -> Tuple[str, str, str]:
        """SSH implementation to run commands on the target
        
        every command opens 2 channels (stdout, stderr), which will be closed 
        (generating an EOF) after command execution, then the output will be red
        and returned as Tuple.

        Raises:
            StarescConnectionError -- Failure in connection establishment
            StarescCommandError -- The provided command timed out
        """
        try:
            chan = self.client.get_transport().open_session()
            chan.settimeout(timeout)

            # Sudo usually requires a pty, but not sure if we will run commands with it, so for now it will be disabled
            # chan.get_pty(term=os.getenv('TERM', 'vt100'), width=int(os.getenv('COLUMNS', 0)), height=int(os.getenv('LINES', 0)))

            chan.exec_command(cmd)

        except paramiko.SSHException:
            msg = f"Couldn't open session when trying to run command: {cmd}"
            raise StarescConnectionError(msg)

        except TimeoutError:
            msg = f"command {cmd} timed out"
            raise StarescCommandError(msg)
         
        return (
            # stdin
            cmd, 
            # stdout
            b''.join(chan.makefile('rb', bufsize)).rstrip(b"\r\n").decode("utf-8"),
            # stderr 
            b''.join(chan.makefile_stderr('rb', bufsize)).rstrip(b"\r\n").decode("utf-8"), 
        )
