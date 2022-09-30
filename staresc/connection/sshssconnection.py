import socket, re, os, binascii
from typing import Tuple

import paramiko

from staresc.exceptions import StarescAuthenticationError, StarescCommandError, StarescConnectionError
from staresc.connection import Connection

class SSHSSConnection(Connection):
    """SSHSSConnection is a Connection implementation for SSH

    high level object for the commands and data we're sending to the target host

    The difference between this class and SSHConnection is that this class runs
    commands in a Single Session (hence SSHSS). This connection type was done
    because of some "hardened" systems that allows just one session for each SSH
    client: "no need for terminal multiplexing".
    """

    client: paramiko.SSHClient

    class CompletelyIgnore(paramiko.MissingHostKeyPolicy):
        
        def __init__(self) -> None:
            """CompletelyIgnore is a custom policy 
        
            It ignores missing keys in paramiko. 
            It will do nothing if keys aren't found
            """
            super().__init__()


        def missing_host_key(self, client, hostname, key):
            """
            Called when an .SSHClient receives a server key for a server that 
            isn't in either the system or local .HostKeys object. To accept the 
            key, simply return. To reject, raised an exception (which will be 
            passed to the calling application).

            This implementation does nothing when receiving the keys.
            """
            pass


    def __init__(self, connection: str) -> None:
        super().__init__(connection)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(self.CompletelyIgnore)


    @staticmethod
    def match_scheme(s: str) -> bool:
        return s == "sshss"


    def connect(self):
        """SSHSS implementation to connect to the target server

        It uses paramiko to handle SSH communication. 

        Raises:
            StarescAuthenticationError -- raised when login fails
            StarescConnectionError -- raised when the program can't connect to the target 
        """
        paramiko_args = {
            'hostname'      : self.get_hostname(self.connection),
            'port'          : self.get_port(self.connection),
            'allow_agent'   : False,
            'look_for_keys' : False
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

        except (paramiko.SSHException, paramiko.ssh_exception.NoValidConnectionsError):
            msg = f"An error occured when trying to connect"
            raise StarescConnectionError(msg)
            

    def run(self, cmd: str, timeout: float = Connection.command_timeout) -> Tuple[str, str, str]:
        """SSHSS implementation to run commands on the target
        
        every command reuses a single channel to send commands and receive both
        stdin and stdout, it understands when a command is done executing using
        canary tokens generated for each command, then the output will be red
        and returned as Tuple.

        Raises:
            StarescCommandError -- The provided command timed out
        """
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
