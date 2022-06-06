import socket
import paramiko
import os
from typing import Tuple
import binascii

from lib.exceptions import AuthenticationError, CommandTimeoutError
from lib.connection import Connection

class SSHConnection(Connection):

    client: paramiko.SSHClient

    # CompletelyIgnore is a custom policy to ignore missing keys in
    # paramiko. It will do nothing if keys aren't found
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

        h = self.get_hostname(self.connection)
        p = self.get_port(self.connection)
        usr, pwd = self.get_credentials(self.connection)

        # We need to generalize the exception for every connection type
        try:
            if "/" in pwd:
                self.client.connect(hostname=h, port=p, username=usr, pkey=paramiko.RSAKey.from_private_key_file(pwd))
            else:
                self.client.connect(hostname=h, port=p, username=usr, password=pwd)
        except paramiko.AuthenticationException:
            raise AuthenticationError(usr, pwd)
            

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
