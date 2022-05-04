import telnetlib
from typing import Tuple

from .connection import Connection


class TNTConnection(Connection):
    
    def __init__(self, connection: str) -> None:
        super().__init__(connection)


    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "tnt"


    def connect(self) -> None:
        host = self.get_hostname(self.connection)
        port = self.get_port(self.connection)
        usr, pwd = self.get_credentials(self.connection)

        self.client = telnetlib.Telnet(host, port)
        self.client.read_until(b"login: ")
        self.client.write(usr.encode('ascii') + b"\n")
        self.client.read_until(b"Password: ")
        self.client.write(pwd.encode('ascii') + b"\n")


    def run(self, cmd: str) -> Tuple[str, str, str]:
        try:
            self.client.write(cmd.encode('ascii') +  b"\n")
            stdout = self.client.read_all().decode('ascii')
        except Exception as e:
            raise e
        
        return cmd.decode('utf-8'), stdout, None


    def elevate(self) -> bool:
        return False
