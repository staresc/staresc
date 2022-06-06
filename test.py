#!/usr/bin/python3 -Wignore

import unittest
import paramiko
import os

from lib.connection.sshconnection import SSHConnection
from lib.connection.tntconnection import TNTConnection
from lib.core.staresc import Staresc
from lib.exceptions import AuthenticationError

PLUGINDIR = "./test/plugins/"

SSH_REACHABLETARGETS = [
    "ssh://user:pass@127.0.0.1:10022/",
    "ssh://user:pass@127.0.0.1:10024/",
]

TNT_REACHABLETARGETS = [
    "telnet://user:pass@127.0.0.1:10023/",
    "telnet://user:pass@127.0.0.1:10025/",
]

UNREACHABLE_TARGETS = [ 
    "ssh://u:p@127.0.0.1:10032/",
    "telnet://u:p@127.0.0.1:10032/",
]

WRONG_CREDENTIALS_LIST = [
    "ssh://user:pass@127.0.0.1:10022/",
    "telnet://user:pass@127.0.0.1:10023/",
]


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


    def test_telnet_connection(self):
        c1 = TNTConnection(TNT_REACHABLETARGETS[0])
        c1.connect()
        stdin1, stdout1, stderr1  = c1.run("echo test")
        self.assertEqual(stdin1, "echo test", "Should be 'echo test'")
        self.assertEqual(stdout1, "test", "Should echo 'test'")
        self.assertEqual(stderr1, None, "Should be empty")

        c2 = TNTConnection(TNT_REACHABLETARGETS[1])
        c2.connect()
        stdin2, stdout2, stderr2  = c2.run("echo test")
        self.assertEqual(stdin2, "echo test", "Should be 'echo test'")
        self.assertEqual(stdout2, "test", "Should echo 'test'")
        self.assertEqual(stderr2, None, "Should be empty")
    

    def test_unreachable(self):
        try:
            c1 = SSHConnection(UNREACHABLE_TARGETS[0])
            c1.connect()
        except Exception as e:
            self.assertTrue(isinstance(e, paramiko.ssh_exception.NoValidConnectionsError))

        try:
            c2 = TNTConnection(UNREACHABLE_TARGETS[1])
            c2.connect()
        # Exception during telnetlib OSError during write() and EOFError during read()
        except Exception as e:
            self.assertTrue(
                isinstance(e, OSError) or isinstance(e, EOFError)
            )


class TestStaresc(unittest.TestCase):


    def test_CVE20213156_plugin_execution_on_vulnerable(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[0])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "CVE-2021-3156.yaml")        
        out = se.do_check(plugin, True)
        
        # Assert result is not empty
        self.assertTrue(out != None)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertTrue(
            "plugin" in out.keys() and "parse_results" in out.keys(),
            f"Key(s) not found in staresc's output:\n\n{out}\n\n"
        )
        self.assertTrue(
            len(out["parse_results"]) == 2 and len(out["parse_results"][0]) == 2, 
            f"Incorrect output in parse_results:\n\n{out['parse_results']}\n\n"
        )
        self.assertTrue(
            isinstance(out["parse_results"][0][0], bool) and isinstance(out["parse_results"][1][0], bool), 
            f"Arrays of results should have a boolean in index 0:\n\n{out['parse_results'][0]}\n{out['parse_results'][1]}\n\n"
        )

        self.assertEqual(out["plugin"], "CVE-2021-3156.yaml", "Wrong plugin field")
        sudoedit_vulnerable = out["parse_results"][0][0]
        sudo_vulnerable_version = out["parse_results"][1][0]
        self.assertTrue(sudoedit_vulnerable and sudo_vulnerable_version, "Parse result should report the presence of the vulnerability")
        

    def test_lxc_plugin_execution_on_vulnerable(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[0])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "lxc.yaml")        
        out = se.do_check(plugin, True)
        
        # Assert result is not empty
        self.assertTrue(out != None)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertTrue(
            "plugin" in out.keys() and "parse_results" in out.keys(),
            f"Key(s) not found in staresc's output:\n\n{out}\n\n"
        )
        self.assertTrue(
            len(out["parse_results"]) == 1 and len(out["parse_results"][0]) == 2, 
            f"Incorrect output in parse_results:\n\n{out['parse_results']}\n\n"
        )
        self.assertTrue(
            isinstance(out["parse_results"][0][0], bool), 
            f"Arrays of results should have a boolean in index 0:\n\n{out['parse_results'][0]}\n\n"
        )

        self.assertEqual(out["plugin"], "lxc.yaml", "Wrong plugin field")
        vulnerable = out["parse_results"][0][0]
        self.assertTrue(vulnerable, "Parse result should report the presence of the vulnerability")

    
    def test_CVE20213156_plugin_execution_on_patched(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[1])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "CVE-2021-3156.yaml")        
        out = se.do_check(plugin, True)
        
        # Assert result is not empty
        self.assertTrue(out != None)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertTrue(
            "plugin" in out.keys() and "parse_results" in out.keys(),
            f"Key(s) not found in staresc's output:\n\n{out}\n\n"
        )
        self.assertTrue(
            len(out["parse_results"]) == 2 and len(out["parse_results"][0]) == 2, 
            f"Incorrect output in parse_results:\n\n{out['parse_results']}\n\n"
        )
        self.assertTrue(
            isinstance(out["parse_results"][0][0], bool) and isinstance(out["parse_results"][1][0], bool), 
            f"Arrays of results should have a boolean in index 0:\n\n{out['parse_results'][0]}\n{out['parse_results'][1]}\n\n"
        )

        self.assertEqual(out["plugin"], "CVE-2021-3156.yaml", "Wrong plugin field")
        sudoedit_vulnerable = out["parse_results"][0][0]
        sudo_vulnerable_version = out["parse_results"][1][0]
        self.assertTrue(not sudoedit_vulnerable and not sudo_vulnerable_version, "Parse result should report the absence of the vulnerability")
        

    def test_lxc_plugin_execution_on_patched(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[1])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "lxc.yaml")        
        out = se.do_check(plugin, True)
        
        # Assert result is not empty
        self.assertTrue(out != None)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertTrue(
            "plugin" in out.keys() and "parse_results" in out.keys(),
            f"Key(s) not found in staresc's output:\n\n{out}\n\n"
        )
        self.assertTrue(
            len(out["parse_results"]) == 1 and len(out["parse_results"][0]) == 2, 
            f"Incorrect output in parse_results:\n\n{out['parse_results']}\n\n"
        )
        self.assertTrue(
            isinstance(out["parse_results"][0][0], bool), 
            f"Arrays of results should have a boolean in index 0:\n\n{out['parse_results'][0]}\n\n"
        )

        self.assertEqual(out["plugin"], "lxc.yaml", "Wrong plugin field")
        vulnerable = out["parse_results"][0][0]
        self.assertTrue(not vulnerable, "Parse result should report the presence of the vulnerability")


class TestCredentials(unittest.TestCase):

    def test_wrong_credentials(self):
        c1 = SSHConnection(WRONG_CREDENTIALS_LIST[0]) 
        try:
            c1.connect()
        except Exception as e:
            self.assertRaises(AuthenticationError,e)

        c2 = TNTConnection(WRONG_CREDENTIALS_LIST[1])
        try:
            c2.connect()
        except Exception as e:
            self.assertRaises(AuthenticationError,e)
        

if __name__ == "__main__":
    unittest.main()
