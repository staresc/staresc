import unittest

import staresc.connection as conn
from staresc.exceptions import StarescConnectionError, StarescAuthenticationError

UNREACHABLES = {
    "ssh://u:p@127.0.0.1:9999/"    : conn.SSHConnection,
    "sshss://u:p@127.0.0.1:9999/"  : conn.SSHSSConnection,
    "telnet://u:p@127.0.0.1:9999/" : conn.TNTConnection,
}

REACHABLES = {
    "ssh://user:pass@127.0.0.1:9001/"   : conn.SSHConnection,
    # TODO: implement shell_request/pty into ssh server
    # TODO: implement telnet server 
}

WRONG_CREDS = {
    "ssh://user:wrong@127.0.0.1:9001/" : conn.SSHConnection,
    "ssh://user:wrong@127.0.0.1:9001/" : conn.SSHSSConnection,
    # TODO: implement telnet server
}

COMMAND_ANSWER = [ "whoami" , "user" ]



class StarescTests(unittest.TestCase):

    TESTLIST = [
        "test_unreachable_target",
        "test_connection",
        "test_wrong_credentials",
    ]

    def test_unreachable_target(self):
        for conn_str in UNREACHABLES.keys():
            try:
                c = UNREACHABLES[conn_str](conn_str)
                c.connect()
                c.close()

            except Exception as e:
                self.assertTrue(isinstance(e, StarescConnectionError))

    
    def test_connection(self):
        for conn_str in REACHABLES.keys():
            c = REACHABLES[conn_str](conn_str)
            c.connect() 
            _, stdout, _ = c.run(COMMAND_ANSWER[0])
            self.assertEqual(stdout, COMMAND_ANSWER[1])


    def test_wrong_credentials(self):
        for conn_str in WRONG_CREDS.keys():
            try:
                c = WRONG_CREDS[conn_str](conn_str)
                c.connect()

            except Exception as e:
                self.assertTrue(isinstance(e, StarescAuthenticationError))

