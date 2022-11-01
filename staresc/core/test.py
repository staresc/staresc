import unittest
import threading
import time

from staresc.log import Logger 
import staresc.test as test



class Tester:

    def __init__(self) -> None:
        self.logger = Logger()


    def test(self) -> int:
        suite = unittest.TestSuite()
        [ suite.addTest(test.IntegrityTests(t)) for t in test.IntegrityTests.TESTLIST ]

        t_args = {
            "target" : test.start_server,
            "args"   : ("127.0.0.1", 9001),
            "daemon" : True,
        }
        threading.Thread(**t_args).start()

        self.logger.info("Starting tests")
        time.sleep(1)

        try:
            r = unittest.TextTestRunner().run(suite)
            self.logger.info("End of tests")
            if not r.wasSuccessful():
                return 1

        except Exception as e:
            self.logger.error(str(e))
        
        return 0