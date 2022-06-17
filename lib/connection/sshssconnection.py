import socket
import paramiko
import os
from typing import Tuple
import binascii
import re

from lib.exceptions import StarescAuthenticationError, StarescCommandError
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
        paramiko_args = {
            'hostname' : self.get_hostname(self.connection),
            'port'     : self.get_port(self.connection),
        }
        paramiko_args['username'], paramiko_args['password'] = self.get_credentials(self.connection)
        if '/' in paramiko_args['password']:
            paramiko_args['pkey']     = paramiko.RSAKey.from_private_key_file(paramiko_args['password'])
            paramiko_args['password'] = None

        
        try:
            self.client.connect(**paramiko_args)
            self.chan = self.client.invoke_shell()
            self.stdin = self.chan.makefile('wb')
            self.stdout = self.chan.makefile('r')

        except paramiko.AuthenticationException:
            msg = f"Authentication failed for {paramiko_args['username']} with password {paramiko_args['password']}"
            raise StarescAuthenticationError(msg)

        except paramiko.SSHException:
            msg = f"An error occured when trying to connect"
            raise StarescCommandError(msg)
            

    def run(self, cmd: str, timeout: float = Connection.COMMAND_TIMEOUT) -> Tuple[str, str, str]:
        
        self.chan.settimeout(timeout)

        # Send cmd and delimiter canary
        delimiter_canary = binascii.b2a_hex(os.urandom(15)).decode('ascii')
        canary_cmd = f'echo {delimiter_canary}'
        
        self.stdin.write(cmd + '\n')
        self.stdin.write(canary_cmd + '\n')
        self.stdin.flush()

        try:
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
            msg = f"Command {cmd} timed out"
            raise StarescCommandError(msg)

        except IndexError:
            return (
                # stdin
                cmd,
                #stdout
                ''.join(tmpout).rstrip(), 
                #stderr
                ''
            )

        return (
            # stdin
            cmd,
            #stdout
            ''.join(tmpout).rstrip(), 
            #stderr
            ''
        )
