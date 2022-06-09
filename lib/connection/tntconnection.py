import telnetlib
from typing import Tuple
import os,binascii

from lib.exceptions import StarescAuthenticationError, StarescCommandError, StarescConnectionError
from lib.connection import Connection


class TNTConnection(Connection):

    client: telnetlib.Telnet

    def __init__(self, connection: str) -> None:
        super().__init__(connection)


    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "telnet"


    def connect(self) -> None:
        telnet_args = {
            'host'    : self.get_hostname(self.connection),
            'port'    : self.get_port(self.connection),
            'timeout' : Connection.COMMAND_TIMEOUT
        }

        try:
            self.client = telnetlib.Telnet(**telnet_args)
            
            usr, pwd = self.get_credentials(self.connection)
            self.client.read_until(b"login:")
            self.client.write(usr.encode('ascii') + b"\n")
            self.client.read_until(b"Password: ")
            self.client.write(pwd.encode('ascii') + b"\n")
        
        except (OSError,EOFError):
            msg = f"connection to {telnet_args['host']} failed"
            raise StarescConnectionError(msg)
        
        delimiter_canary = binascii.b2a_hex(os.urandom(15))
        try:
            self.client.write(b'echo ' + delimiter_canary + b'\n')
            self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n')

        except (OSError,EOFError):
            msg = f"Authentication failed for {usr} with password {pwd}"
            raise StarescAuthenticationError(msg)


    def run(self, cmd: str, timeout: float = Connection.COMMAND_TIMEOUT) -> Tuple[str, str, str]:

        try:
            delimiter_canary = binascii.b2a_hex(os.urandom(15))
            self.client.write(cmd.encode('ascii') + b"; echo " + delimiter_canary + b'\n')
            stdout = self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n', timeout=timeout)

        except (OSError,EOFError):
            msg = f"connection dropped while executing command: {cmd}"
            raise StarescCommandError

        if (b'\r\n' + delimiter_canary + b'\r\n') not in stdout:
            # read_until() returned due to timeout
            msg = f"command {cmd} timed out"
            raise StarescCommandError(msg)

        # extract from stdout the output of cmd
        stdout = stdout.split(delimiter_canary + b'\r\n')[-2]
        stdout = stdout.rstrip(b'\r\n').decode('ascii')
        return cmd, stdout, None
