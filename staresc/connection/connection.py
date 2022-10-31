import re
from telnetlib import Telnet
from typing import Tuple
from functools import cached_property

from paramiko import SSHClient

class Connection():
    """Connection is the class handling connections
    
    high level object for the commands and data we're sending to the target host
    """

    connection: str = ""
    """Connection String

    This is a wrapper for everything we need to know about the connection:

    scheme://user:(passwd|\\path\\pubkey)@host:port

    Attributes:
        scheme -- We support different schemes, such as ssh:// telnet://
        user -- Username for the connection authentication
        passwd -- Password for the connection authentication
        \\path\\pubkey -- Path to the private key for SSH connections
        host -- Host to connect to
        port -- Port to connect to
    """

    # static fields
    __parse_regex = re.compile(
        "^([a-z]+)://" +    # scheme
        "([^:]+)" +         # username
        ":(.*)@" +          # password
        "(" +               # host parse start
        "((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])\.?){4}" + # IP
        "|" +               # or
        "([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])*\.)+[a-zA-Z]{2,}" + # Hostname
        ")" +               # host parse end
        ":([0-9]{1,5})" +   # port
        "/?$"               # optional trailing slash
        )

    command_timeout: float = 60
    """Command timeout

    This field indicates how much a connection should wait for data before it 
    will not. Changing this value might generate false negatives in the result    
    """

    client:Telnet|SSHClient


    def __init__(self, connection: str) -> None:
        """Class constructor

        Attributes:
            connection -- connection string     
        """
        self.connection = connection


    @cached_property
    def scheme(self) -> str:
        return Connection.parse(self.connection)['scheme']


    @cached_property
    def hostname(self) -> str:
        return Connection.parse(self.connection)['hostname']


    @cached_property
    def port(self) -> int:
        return int(Connection.parse(self.connection)['port'])


    @cached_property
    def credentials(self)-> Tuple[str, str]:
        """Get user credentials from connection string"""
        p = Connection.parse(self.connection)
        if "\\" in p['password']:
            return p['username'], p['password'].replace("\\", "/")
        return p['username'], p['password']


    @staticmethod
    def parse(connection: str) -> dict[str, str]:
        match = Connection.__parse_regex.search(connection)
        if not match:
            return {}
        return {
            'scheme':   match.group(1),
            'hostname': match.group(4),
            'port':     match.group(10),
            'username': match.group(2),
            'password': match.group(3)
        }


    @staticmethod
    def is_connection_string(connection: str) -> bool:
        """Check if the provided connection string is properly formatted"""
        tmp = Connection.parse(connection)
        if not tmp:
            return False
        return bool(tmp['hostname'] and tmp['username'] and tmp['password']) 


    def close(self) -> None:
        """Close the connection"""
        self.client.close()


    def connect(self, ispubkey: bool) -> None:
        """Interface to make the connection connect to the target"""
        pass


    def run(self, cmd: str) -> Tuple[str, str, str]:
        """Interface to run a command on the target machine 
        
        it uses the underlying connection and enforces the return values in the
        form of a tuple composed by stdin, stdout and stderr
        """
        return '','',''

