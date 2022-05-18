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

        canary = binascii.b2a_hex(os.urandom(15))
        _cmd = f"{cmd}; echo {canary.decode('utf-8')}"
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, get_pty=True, timeout=25)
            if u != "" and p != "":
                stdout.channel.recv(1024)
                stdin.write(f"{p}\n")
                stdin.flush()

            o_stdin = cmd
            o_stdout = self.__read_until(stdout.channel, canary).strip("\r\n")
            o_stderr = self.__read_until(stderr.channel, None).strip("\r\n")

        except Exception as e:
            raise e

        return o_stdin, o_stdout, o_stderr


    @staticmethod
    def __read_all(channel: paramiko.Channel) -> bytes:
        data = b''
        if channel.recv_ready():
            data = channel.recv(1024)
            prevdata = b" "
            while prevdata:
                prevdata = channel.recv(1024)
                data += prevdata
        return data

    @staticmethod
    def __read_until(channel: paramiko.Channel, token) -> str:
        data = b''
        # This is stdout
        if token:
            while not channel.exit_status_ready() and token not in data:
                data += SSHConnection.__read_all(channel)
            return data.split(token)[0].decode('utf-8')
        # This is stderr
        while not channel.exit_status_ready():
            data += SSHConnection.__read_all(channel)
        return data.decode('utf-8')

