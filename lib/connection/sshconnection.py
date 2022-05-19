from base64 import decode
import paramiko
import os
import binascii
from typing import Tuple

from .connection import Connection


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
                pkey=paramiko.RSAKey.from_private_key_file(pwd)
            )
        else:
            self.client.connect(
                hostname=host,
                port=port,
                username=usr,
                password=pwd
            )


    def run(self, cmd: str) -> Tuple[str, str, str]:
        
        u, p = self.get_root_credentails(self.connection)
        if u != "" and p != "":
            cmd = cmd.replace('\'', '"')
            cmd = f"su {u} -c '{cmd}'"

        bufsize = 4096

        try:
            
            self.client.get_transport().set_keepalive(5)
            chan = self.client.get_transport().open_session()

            chan.get_pty(
                term=os.getenv('TERM', 'vt100'), 
                width=int(os.getenv('COLUMNS', 0)), 
                height=int(os.getenv('LINES', 0))
                )

            chan.exec_command(cmd)

            stdin = cmd
            stdout = b''.join(chan.makefile('rb', bufsize))
            stderr = b''.join(chan.makefile_stderr('rb', bufsize))

        except Exception as e:
            raise e

        return stdin, stdout.rstrip(b"\r\n").decode("utf-8"), stderr.rstrip(b"\r\n").decode("utf-8")

