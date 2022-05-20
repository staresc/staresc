import telnetlib
from typing import Tuple
import os,binascii
from .connection import Connection
from lib.exception import CommandTimeoutError


class TNTConnection(Connection):

    client: telnetlib.Telnet

    def __init__(self, connection: str) -> None:
        super().__init__(connection)


    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "telnet"


    def connect(self) -> None:
        host = self.get_hostname(self.connection)
        port = self.get_port(self.connection)
        usr, pwd = self.get_credentials(self.connection)

        self.client = telnetlib.Telnet(host, port)
        self.client.read_until(b"login:")
        self.client.write(usr.encode('ascii') + b"\n")
        self.client.read_until(b"Password: ")
        self.client.write(pwd.encode('ascii') + b"\n")

        delimiter_canary = binascii.b2a_hex(os.urandom(15))
        self.client.write(b'echo ' + delimiter_canary + b'\n')

        # consume output on channel
        self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n', timeout=1)


    def run(self, cmd: str, timeout: float = None) -> Tuple[str, str, str]:
        if not timeout:
            timeout = Connection.COMMAND_TIMEOUT
        try:
            delimiter_canary = binascii.b2a_hex(os.urandom(15))
            self.client.write(cmd.encode('ascii') + b"; echo " + delimiter_canary + b'\n')
            stdout = self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n', timeout=timeout)
        except Exception as e:
            raise e

        if not (b'\r\n' + delimiter_canary + b'\r\n') in stdout:
            # read_until() returned due to timeout
            raise CommandTimeoutError(command = cmd)

        # extract from stdout the output of cmd
        stdout = stdout.split(delimiter_canary + b'\r\n')[-2]
        stdout = stdout.rstrip(b'\r\n').decode('ascii')
        return cmd, stdout, None


    def elevate(self) -> bool:
        root_username, root_passwd = super().get_root_credentials(self.connection)
        if root_username == '' or root_passwd == '':
            return False

        delimiter_canary = binascii.b2a_hex(os.urandom(15)).decode('ascii')
        stdin, stdout, stderr = self.run(f'echo {root_passwd} | su -c "echo {delimiter_canary}" {root_username}')

        # check canary
        if delimiter_canary in stdout:
            return True
        return False