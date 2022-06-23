
import unittest, threading

import staresc.test as t
from staresc.exceptions import StarescCommandError, StarescConnectionError
from staresc.connection import SSHConnection

class StarescTester(unittest.TestCase):

    TESTS = [
        "test_unreachable_target",
        "test_correct_command_execution",
        #"test_timeout_error"
    ]     


    def test_unreachable_target(self):
        """Test a target that is not reachable"""
        try:
            c = SSHConnection(t.SSH_SERVER_UNREACHABLE)
            c.connect()
            c.close()

        except Exception as e:
            self.assertTrue(isinstance(e, StarescConnectionError))


    def test_correct_command_execution(self):
        """Test if command gives correct answer"""
        c = SSHConnection(t.SSH_SERVER_GOOD)
        c.connect()

        for k in t.GOOD_COMMANDS_WITH_ANSWER.keys():
            _, o, _ = c.run(k)
            self.assertEqual(o, t.GOOD_COMMANDS_WITH_ANSWER[k])
            
        c.close()


    def test_timeout_error(self):
        """Test behavior when command returns timeout"""
        c = SSHConnection(t.SSH_SERVER_GOOD)
        c.connect()

        try:
            c.run(t.BAD_COMMAND)
            c.close()

        except Exception as e:
            self.assertTrue(isinstance(e, StarescConnectionError))
        
