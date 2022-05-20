import socket

import paramiko
import os
from typing import Tuple
import binascii

from .connection import Connection
from lib.exception import CommandTimeoutError

class SSHConnection(Connection):

    client: paramiko.SSHClient

    def __init__(self, connection: str) -> None:
        super().__init__(connection)
        self.client = paramiko.SSHClient()

    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "ssh"


    def connect(self):
        host = self.get_hostname(self.connection)
        port = self.get_port(self.connection)
        usr, pwd = self.get_credentials(self.connection)

        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if "/" in pwd:
            self.client.connect(
                hostname=host,
                port=port,
                username=usr,
                pkey=paramiko.RSAKey.from_private_key_file(pwd),
            )
        else:
            self.client.connect(
                hostname=host,
                port=port,
                username=usr,
                password=pwd,
            )
            

    def run(self, cmd: str, timeout: float = None) -> Tuple[str, str, str]:
        if not timeout:
            timeout = Connection.COMMAND_TIMEOUT
        bufsize = 4096
        try:

            self.client.get_transport().set_keepalive(5)
            chan = self.client.get_transport().open_session()
            chan.get_pty(
                term=os.getenv('TERM', 'vt100'), 
                width=int(os.getenv('COLUMNS', 0)), 
                height=int(os.getenv('LINES', 0))
                )
            chan.settimeout(timeout)
            chan.exec_command(cmd)

            stdin = cmd
            stdout = b''.join(chan.makefile('rb', bufsize))
            stderr = b''.join(chan.makefile_stderr('rb', bufsize))

        except socket.timeout as e:
            raise CommandTimeoutError(command = cmd)
        except Exception as e:
            raise e
         
        return stdin, stdout.rstrip(b"\r\n").decode("utf-8"), stderr.rstrip(b"\r\n").decode("utf-8")


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
