import socket
import paramiko
import os
from typing import Tuple
import binascii
import re

from lib.exceptions import AuthenticationError, CommandTimeoutError
from lib.connection import Connection

class SSHSSConnection(Connection):

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
        return s == "sshss"


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

            self.chan = self.client.invoke_shell()
            self.stdin = self.chan.makefile('wb')
            self.stdout = self.chan.makefile('r')
        except paramiko.AuthenticationException:
            raise AuthenticationError(usr, pwd)
            

    def run(self, cmd: str, timeout: float = None) -> Tuple[str, str, str]:
        if not timeout:
            timeout = Connection.COMMAND_TIMEOUT
        try:
            self.chan.settimeout(timeout)

            # Send cmd and delimiter canary
            delimiter_canary = binascii.b2a_hex(os.urandom(15)).decode('ascii')
            self.stdin.write(cmd + '\n')
            canary_cmd = f'echo {delimiter_canary}'
            self.stdin.write(f'echo {delimiter_canary}' + '\n')
            self.stdin.flush()

            tmpout = []
            for line in self.stdout:
                # get rid of 'coloring and formatting' special characters
                line = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).replace('\b', '').replace('\r', '')

                if str(line).startswith(cmd) or str(line).startswith(canary_cmd):
                    # up for now filled with shell junk from stdin
                    tmpout = []
                elif str(line).startswith(delimiter_canary):
                    # our finish command ends with the exit status
                    break
                else:
                    tmpout.append(line)

            if tmpout and canary_cmd in tmpout[-1]:
                tmpout.pop()
            if tmpout and cmd in tmpout[0]:
                tmpout.pop(0)

        except socket.timeout as e:
            raise CommandTimeoutError(command=cmd)
        except Exception as e:
            raise e

        return cmd, ''.join(tmpout).rstrip(), ''


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
