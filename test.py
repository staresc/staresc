#!/usr/bin/python3 -Wignore

import unittest
import os

import paramiko
import yaml

from staresc.core import Staresc
from staresc.connection import SSHConnection, TNTConnection
from staresc.output import Output
from staresc.plugin_parser import Plugin
from staresc.exceptions import StarescAuthenticationError, StarescConnectionError, StarescCommandError

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
            self.assertTrue(isinstance(e, StarescConnectionError))

        try:
            c2 = TNTConnection(UNREACHABLE_TARGETS[1])
            c2.connect()
        # Exception during telnetlib OSError during write() and EOFError during read()
        except Exception as e:
            self.assertTrue(isinstance(e, StarescConnectionError))


class TestStaresc(unittest.TestCase):


    def test_CVE20213156_plugin_execution_on_vulnerable(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[0])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "CVE-2021-3156.yaml")

        out: Plugin = None
        with open(plugin, "r") as f:
            p = Plugin(yaml.load(f.read(), Loader=yaml.Loader))
            out = se.do_check(p)
        
        # Assert result is not empty
        self.assertTrue(out != None)
        self.assertTrue(out.is_vuln_found())        
        

    def test_lxc_plugin_execution_on_vulnerable(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[0])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "lxc.yaml")        
        
        out: Plugin = None
        with open(plugin, "r") as f:
            p = Plugin(yaml.load(f.read(), Loader=yaml.Loader))
            out = se.do_check(p)

        # Assert result is not empty
        self.assertTrue(out != None)
        self.assertTrue(out.is_vuln_found())

    
    def test_CVE20213156_plugin_execution_on_patched(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[1])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "CVE-2021-3156.yaml")        
        
        out: Plugin = None
        with open(plugin, "r") as f:
            p = Plugin(yaml.load(f.read(), Loader=yaml.Loader))
            out = se.do_check(p)

        # Assert result is not empty
        self.assertTrue(out != None)
        self.assertTrue(not out.is_vuln_found())
        

    def test_lxc_plugin_execution_on_patched(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[1])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "lxc.yaml")        
        
        out: Plugin = None
        with open(plugin, "r") as f:
            p = Plugin(yaml.load(f.read(), Loader=yaml.Loader))
            out = se.do_check(p)

        # Assert result is not empty
        self.assertTrue(out != None)
        self.assertTrue(not out.is_vuln_found())


class TestCredentials(unittest.TestCase):

    def test_wrong_credentials(self):
        c1 = SSHConnection(WRONG_CREDENTIALS_LIST[0]) 
        try:
            c1.connect()
        except Exception as e:
            self.assertRaises(StarescAuthenticationError,e)

        c2 = TNTConnection(WRONG_CREDENTIALS_LIST[1])
        try:
            c2.connect()
        except Exception as e:
            self.assertRaises(StarescAuthenticationError,e)
        

if __name__ == "__main__":
    unittest.main()
