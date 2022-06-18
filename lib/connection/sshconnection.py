import paramiko
from typing import Tuple
import logging

from lib.exceptions import StarescAuthenticationError, StarescCommandError, StarescConnectionError
from lib.connection import Connection

logger = logging.getLogger(__name__)

class SSHConnection(Connection):

    client: paramiko.SSHClient

    # CompletelyIgnore is a custom policy to ignore missing keys 
    # in paramiko. It will do nothing if keys aren't found
    class CompletelyIgnore(paramiko.MissingHostKeyPolicy):
        def missing_host_key(self, client, hostname, key):
            pass

    def __init__(self, connection: str) -> None:
        super().__init__(connection)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(self.CompletelyIgnore)

    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "ssh"


    def connect(self):

        paramiko_args = {
            'hostname' : self.get_hostname(self.connection),
            'port'     : self.get_port(self.connection),
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

        except paramiko.SSHException:
            msg = f"An error occured when trying to connect"
            raise StarescConnectionError(msg)
            

    def run(self, cmd: str, timeout: float = Connection.COMMAND_TIMEOUT, bufsize: int = 4096) -> Tuple[str, str, str]:

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
