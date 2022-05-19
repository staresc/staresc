import telnetlib
from typing import Tuple
import os,binascii
import time
from .connection import Connection


class TNTConnection(Connection):
    
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
        output2 = self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n', timeout=1)


    def run(self, cmd: str) -> Tuple[str, str, str]:
        try:
            delimiter_canary = binascii.b2a_hex(os.urandom(15))
            self.client.write(cmd.encode('ascii') + b"; echo " + delimiter_canary + b'\n')
            stdout = self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n')
        except Exception as e:
            raise e

        # extract from stdout the output of cmd
        stdout = stdout.split(delimiter_canary + b'\r\n')[1]
        stdout = stdout.decode('ascii')
        return cmd, stdout, None


    def elevate(self) -> bool:
        root_username, root_passwd = super().get_root_credentials(self.connection)
        if root_username == '' or root_passwd == '':
            return False
        root_username = root_username.encode('ascii')
        root_passwd = root_passwd.encode('ascii')

        delimiter_canary = binascii.b2a_hex(os.urandom(15))
        self.client.write(b'su -c "echo ' + delimiter_canary + b'" ' + root_username + b'\r\n')
        passwd_prompt = self.client.read_until(b'Password: ', timeout=1)
        if not b"Password: " in passwd_prompt:
            return False

        self.client.write(root_passwd + b'\n')
        stdout = self.client.read_until(b'\r\n' + delimiter_canary + b'\r\n', timeout=1)
        # check username
        if (b'\r\n' + delimiter_canary + b'\r\n') in stdout:
            return True
        return False