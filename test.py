#!/usr/bin/python3 -W ignore::DeprecationWarning

import unittest
import paramiko

from lib.connection.sshconnection import SSHConnection

PLUGINDIR = "./plugins/"
SSH_REACHABLETARGETS = [
    "ssh://user:pass@127.0.0.1:10022/",
    "ssh://user:pass@127.0.0.1:10024/",
]
TNT_REACHABLETARGETS = [
    "tnt://user:pass@127.0.0.1:10023/",
    "tnt://user:pass@127.0.0.1:10025/",
]
UNREACHABLE_TARGET = "ssh://u:p@127.0.0.1:10032/not:existent"


class TestConnection(unittest.TestCase):

    def test_ssh_connection(self):
        c1 = SSHConnection(SSH_REACHABLETARGETS[0])
        c1.connect()
        stdin1, stdout1, stderr1  = c1.run("echo test")
        self.assertEqual(stdin1, "echo test", "Should be 'echo test'")
        self.assertEqual(stdout1, "test", "Should echo 'test'")
        self.assertEqual(stderr1, "", "Should be empty")
        
        c2 = SSHConnection(SSH_REACHABLETARGETS[1])
        c2.connect()
        stdin2, stdout2, stderr2  = c2.run("echo test")
        self.assertEqual(stdin2, "echo test", "Should be 'echo test'")
        self.assertEqual(stdout2, "test", "Should echo 'test'")
        self.assertEqual(stderr2, "", "Should be empty")

    
    def test_unreachable(self):
        try:
            c = SSHConnection(UNREACHABLE_TARGET)
            c.connect()
        except Exception as e:
            self.assertTrue(isinstance(e, paramiko.ssh_exception.NoValidConnectionsError))


if __name__ == "__main__":
    unittest.main()
