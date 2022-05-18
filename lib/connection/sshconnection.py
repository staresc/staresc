import paramiko
from typing import Tuple

from .connection import Connection


class SSHConnection(Connection):
    
    def __init__(self, connection: str) -> None:
        super().__init__(connection)


    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "ssh"


    def connect(self) -> None:
        host = self.get_hostname(self.connection)
        port = self.get_port(self.connection)
        usr, pwd = self.get_credentials(self.connection)

        self.client = paramiko.SSHClient()
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
        try:
            #print(f'cmd: {cmd}') #debug
            stdin, stdout, stderr = self.client.exec_command(cmd, get_pty=True, timeout=25)

            o_stdin  = cmd
            o_stdout = self.__get_string_from_channel(stdout).strip("\r\n")
            o_stderr = self.__get_string_from_channel(stderr).strip("\r\n")

        except Exception as e:
            raise e

        return o_stdin, o_stdout, o_stderr

    def elevate(self) -> bool:
        root_username, root_passwd = super().get_root_credentials(self.connection)
        if root_username == '' or root_passwd == '':
            return False

        stdin, stdout, stderr = self.client.exec_command(f'su -c "whoami" {root_username}', get_pty=True, timeout=25)
        if stdout.channel.recv(1024) != b'Password: ':
            # Wrong username
            return False
        stdin.channel.send(root_passwd + '\r\n')
        if stdout.read(1024).strip().decode("utf-8") == root_username:
            return True
        else:
            return False


    def __get_string_from_channel(self, channel):
        data = b''
        while not channel.channel.exit_status_ready():
            if channel.channel.recv_ready():
                data =  channel.channel.recv(1024)
                prevdata = b" "
                while prevdata:
                    prevdata = channel.channel.recv(1024)
                    data += prevdata
        return data.decode('utf-8')

