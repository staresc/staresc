from lib.core.plugins import *
from lib.connection import *

class Output():
    target: Connection
    plugin: Plugin
    test_results: list[dict[str]]        #TODO right type?
    test_results_parsed: list[dict[str]]        #TODO right type?
    test_success: list[bool]
    test_timeout: list[bool]
    parsed: bool
    vuln_found: bool                            #TODO match_case implemetation


    def __init__(self, target: Connection, plugin: Plugin, test_results: list = [], test_results_parsed: list = [], test_success: list[bool] = [], test_timeout: list[bool] = [], parsed = False, vuln_found: bool = False,):  #TODO how to handle parsed
        self.target = target
        self.plugin = plugin
        self.test_results = test_results
        self.test_results_parsed = test_results_parsed
        self.test_success = test_success
        self.test_timeout = test_timeout
        self.parsed = parsed
        self.vuln_found = vuln_found

    def add_test_result(self, stdin: str, stdout :str, stderr: str):
        self.test_results.append({
            "stdin": stdin,
            "stdout": stdout,
            "stderr": stderr
        })
        self.test_timeout.append(False)


    def add_test_result_parsed(self, stdout :str, stderr: str):
        self.test_results_parsed.append({
            "stdout": stdout,
            "stderr": stderr
        })


    def add_test_success(self, is_success: bool):
        self.test_success.append(is_success)


    def add_timeout_result(self, stdin: str):
        self.add_test_result(stdin='', stdout='', stderr='')
        self.add_test_result_parsed(stdout='', stderr='')
        self.test_timeout.append(True)


    def is_parsed(self):
        return self.parsed


    def set_parsed(self, parsed: bool):
        self.parsed = parsed


    def set_vuln_found(self, vuln_found: bool):
        self.vuln_found = vuln_found








