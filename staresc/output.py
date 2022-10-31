from staresc.plugin_parser import Plugin
from staresc.connection import Connection

class Output():
    target: Connection
    plugin: Plugin|None
    test_results: list[dict[str, str]]
    test_results_parsed: list[dict[str, str]]
    test_success: list[bool]
    test_timeout: list[bool]
    parsed: bool
    vuln_found: bool
    message: str

    def __init__(self, target: Connection, plugin: Plugin|None, test_results: list = [], test_results_parsed: list = [], test_success: list[bool] = [], test_timeout: list[bool] = [], parsed = False, vuln_found: bool = False, message:str = ""):
        self.target = target
        self.plugin = plugin
        self.test_results = test_results
        self.test_results_parsed = test_results_parsed
        self.test_success = test_success
        self.test_timeout = test_timeout
        self.parsed = parsed
        self.vuln_found = vuln_found
        self.message = message


    def add_test_result(self, stdin: str, stdout :str, stderr: str) -> None:
        self.test_results.append({
            "stdin": stdin,
            "stdout": stdout,
            "stderr": stderr
        })
        self.test_timeout.append(False)


    def add_test_result_parsed(self, stdout :str, stderr: str) -> None:
        self.test_results_parsed.append({
            "stdout": stdout,
            "stderr": stderr
        })


    def add_test_success(self, is_success: bool) -> None:
        self.test_success.append(is_success)


    def add_timeout_result(self, stdin: str) -> None:
        self.add_test_result(stdin=stdin, stdout='', stderr='')
        self.add_test_result_parsed(stdout='', stderr='')
        self.test_timeout.append(True)


    def is_parsed(self) -> bool:
        return self.parsed


    def set_parsed(self, parsed: bool) -> None:
        self.parsed = parsed


    def set_vuln_found(self, vuln_found: bool) -> None:
        self.vuln_found = vuln_found


    def is_vuln_found(self) -> bool:
        return self.vuln_found


    def get_timeouts(self) -> list[bool]:
        return self.test_timeout