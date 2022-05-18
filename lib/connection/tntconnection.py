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

        # consume output on channel
        time.sleep(1)
        self.client.read_very_eager()


    def run(self, cmd: str) -> Tuple[str, str, str]:
        try:
            delimiter_canary = binascii.b2a_hex(os.urandom(15))
            self.client.write(cmd.encode('ascii') + b"; echo " + delimiter_canary + b"\n")
            stdout = b''
            while stdout == b'' or not (b'\r\n' + delimiter_canary + b'\r\n' )  in stdout:
                time.sleep(1)
                stdout += self.client.read_very_eager()
        except Exception as e:
            raise e

        # extract from stdout the output of cmd
        stdout = stdout.split(b'\r\n' + delimiter_canary + b'\r\n')[-2]
        if (delimiter_canary + b'\r\n') in stdout:
            stdout = stdout.split(delimiter_canary + b'\r\n')[1]
        stdout += b'\r\n'
        stdout = stdout.decode('ascii')
        return cmd, stdout, None


    def elevate(self) -> bool:
        root_username, root_passwd = super().get_root_credentials(self.connection)
        if root_username == '' or root_passwd == '':
            return False

        self.client.write(f'su -c "whoami" {root_username}\n'.encode('ascii'))
        time.sleep(0.5)
        passwd_prompt = self.client.read_very_eager()
        if not b"Password: " in passwd_prompt:
            return False
        self.client.write(root_passwd.encode('ascii') + b'\n')
        time.sleep(0.5)
        stdout = self.client.read_very_eager()
        # extract username
        stdout = stdout.split(b'\r\n')[1]
        if stdout.decode('ascii') == root_username:
            return True
        return False
