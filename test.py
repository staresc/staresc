#!/usr/bin/python3 -Wignore

import unittest
import paramiko
import os
import json

from lib.connection.sshconnection import SSHConnection
from lib.connection.tntconnection import TNTConnection
from lib.core.staresc import Staresc

PLUGINDIR = "./test/plugins/"

SSH_REACHABLETARGETS = [
    "ssh://user:pass@127.0.0.1:10022/",
    "ssh://user:pass@127.0.0.1:10024/",
]

TNT_REACHABLETARGETS = [
    "tnt://user:pass@127.0.0.1:10023/",
    "tnt://user:pass@127.0.0.1:10025/",
]

UNREACHABLE_TARGETS = [ 
    "ssh://u:p@127.0.0.1:10032/",
    "tnt://u:p@127.0.0.1:10032/",
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

        # We expect this output:
        expected_str = """{"plugin":"lxc.yaml","results":[{"stdin":"command -v lxc-attach lxc-checkpoint lxc-create lxc-freeze lxc-snapshot lxc-unfreeze lxc-wait lxc-autostart lxc-config lxc-destroy lxc-info lxc-start lxc-unshare lxc-cgroup lxc-console lxc-device lxc-ls lxc-stop lxc-update-config lxc-checkconfig lxc-copy lxc-execute lxc-monitor lxc-top lxc-usernsexec","stdout": "/usr/bin/lxc-attach\\r\\n/usr/bin/lxc-checkpoint\\r\\n/usr/bin/lxc-create\\r\\n/usr/bin/lxc-freeze\\r\\n/usr/bin/lxc-snapshot\\r\\n/usr/bin/lxc-unfreeze\\r\\n/usr/bin/lxc-wait\\r\\n/usr/bin/lxc-autostart\\r\\n/usr/bin/lxc-config\\r\\n/usr/bin/lxc-destroy\\r\\n/usr/bin/lxc-info\\r\\n/usr/bin/lxc-start\\r\\n/usr/bin/lxc-unshare\\r\\n/usr/bin/lxc-cgroup\\r\\n/usr/bin/lxc-console\\r\\n/usr/bin/lxc-device\\r\\n/usr/bin/lxc-ls\\r\\n/usr/bin/lxc-stop\\r\\n/usr/bin/lxc-update-config\\r\\n/usr/bin/lxc-checkconfig\\r\\n/usr/bin/lxc-copy\\r\\n/usr/bin/lxc-execute\\r\\n/usr/bin/lxc-monitor\\r\\n/usr/bin/lxc-top\\r\\n/usr/bin/lxc-usernsexec","stderr": ""}],"parse_results": [[true,{"stdout": "/usr/bin/lxc-attach\\r\\n/usr/bin/lxc-checkpoint\\r\\n/usr/bin/lxc-create\\r\\n/usr/bin/lxc-freeze\\r\\n/usr/bin/lxc-snapshot\\r\\n/usr/bin/lxc-unfreeze\\r\\n/usr/bin/lxc-wait\\r\\n/usr/bin/lxc-autostart\\r\\n/usr/bin/lxc-config\\r\\n/usr/bin/lxc-destroy\\r\\n/usr/bin/lxc-info\\r\\n/usr/bin/lxc-start\\r\\n/usr/bin/lxc-unshare\\r\\n/usr/bin/lxc-cgroup\\r\\n/usr/bin/lxc-console\\r\\n/usr/bin/lxc-device\\r\\n/usr/bin/lxc-ls\\r\\n/usr/bin/lxc-stop\\r\\n/usr/bin/lxc-update-config\\r\\n/usr/bin/lxc-checkconfig\\r\\n/usr/bin/lxc-copy\\r\\n/usr/bin/lxc-execute\\r\\n/usr/bin/lxc-monitor\\r\\n/usr/bin/lxc-top\\r\\n/usr/bin/lxc-usernsexec","stderr": ""}]],"parsed": true}"""
        expected = json.loads(expected_str)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertEqual(expected, out, f"Output should be equals to expected \n\n{out}\n\n{expected}" )

    
    def test_CVE20213156_plugin_execution_on_patched(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[1])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "CVE-2021-3156.yaml")        
        out = se.do_check(plugin, True)
        
        # Assert result is not empty
        self.assertTrue(out != None)

        # We expect this output:
        expected_str = """{"plugin": "CVE-2021-3156.yaml","results": [{"stdin": "sudoedit -s '0123456789\\\\'","stdout": "bash: sudoedit: command not found","stderr": ""},{"stdin": "sudo --version","stdout": "bash: sudo: command not found","stderr": ""}],"parse_results": [[false,{"stdout": "bash: sudoedit: command not found","stderr": ""}],[false,{"stdout": "","stderr": ""}]],"parsed": true}"""
        expected = json.loads(expected_str)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertEqual(expected, out, f"Output should be equals to expected \n\n{out}\n\n{expected}" )


    def test_lxc_plugin_execution_on_patched(self):
        # Prepare object
        se = Staresc(SSH_REACHABLETARGETS[1])
        se.prepare()

        # check for CVE-2021-3156
        plugin = os.path.join(os.getcwd(), PLUGINDIR, "lxc.yaml")        
        out = se.do_check(plugin, True)
        
        # Assert result is not empty
        self.assertTrue(out != None)

        # We expect this output:
        expected_str = """{"plugin": "lxc.yaml","results": [{"stdin": "command -v lxc-attach lxc-checkpoint lxc-create lxc-freeze lxc-snapshot lxc-unfreeze lxc-wait lxc-autostart lxc-config lxc-destroy lxc-info lxc-start lxc-unshare lxc-cgroup lxc-console lxc-device lxc-ls lxc-stop lxc-update-config lxc-checkconfig lxc-copy lxc-execute lxc-monitor lxc-top lxc-usernsexec","stdout": "","stderr": ""}],"parse_results": [[false,{"stdout": "","stderr": ""}]],"parsed": true}"""
        expected = json.loads(expected_str)

        # Adjust for tuples -> list
        sub = []
        for i in out['parse_results']:
            sub.append(list(i))
        out['parse_results'] = sub

        self.assertEqual(expected, out, f"Output should be equals to expected \n\n{out}\n\n{expected}" )



if __name__ == "__main__":
    unittest.main()
