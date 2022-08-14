from typing import Tuple
from staresc.exceptions import StarescPluginError, StarescModeError
from staresc.log import StarescLogger

from staresc.plugin_parser import Parser, Matcher, Extractor


class Test:
    """Test is the class handling the content of the plugin's tests

    high level object that represents a single test run by the staresc engine using the plugin
    """

    mode: str
    logger: StarescLogger
    plugin_test_string: str
    plugin_tests: list[dict]        #TODO fix the type list[{str: str, str: bool}]

    command: str
    """Command 

    string containing the shell command to execute on the target machines
    """
    parsers: list[Parser]
    """Parsers list

    list containing the parsers (matchers/extractors) to run on the Command's results
    """

    def __init__(self, test_content: dict, mode: str, logger: StarescLogger = None, plugin_test_string: str = None):
        """Class constructor

        Attributes:
           test_content -- dict containing data of the given test parsed from the YAML file
        """
        self.parsers = []
        self.mode = mode
        self.logger = logger
        self.plugin_test_string = plugin_test_string
        self.plugin_tests = None
        try:
            self.command = test_content["command"]
            if self.mode == "test_plugins":
                self.logger.debug(f"command: {self.command}", self.plugin_test_string)
            parsers      = test_content["parsers"]

        except KeyError:
            msg = "invalid syntax command/parsers"
            raise StarescPluginError(msg)

        if (not isinstance(parsers, list)) or (len(parsers) < 1):
            msg = "no parser specified or invalid syntax"
            raise StarescPluginError(msg)
        
        MAP_PARSER = {
            "matcher"   : Matcher,
            "extractor" : Extractor,
        }
        for idx, parser_content in enumerate(parsers):
            try:
                if self.mode == "test_plugins":
                    p = MAP_PARSER[parser_content["parser_type"]](parser_content, self.mode, self.logger, f"{self.plugin_test_string}.Parser_{idx+1}")
                else:
                    p = MAP_PARSER[parser_content["parser_type"]](parser_content, self.mode)
                self.parsers.append(p)

            except KeyError:
                msg = "invalid parser_type value"
                raise StarescPluginError(msg)

        if self.mode == "test_plugins":
            self.plugin_tests = []
            if not "plugin_tests" in test_content:
                self.logger.debug("no plugin test specified", self.plugin_test_string)
            else:
                for plugin_test in test_content["plugin_tests"]:
                    if not "stdout" in plugin_test and not "stderr" in plugin_test:
                        msg = "a plugin_test needs \"stdout\" or \"stderr\" fields"
                        raise StarescPluginError(msg)
                    if "stdout" in plugin_test and not isinstance(plugin_test["stdout"], str):
                        msg = "\"stdout\" field in plugin_test must be a string"
                        raise StarescPluginError(msg)
                    if "stderr" in plugin_test and not isinstance(plugin_test["stderr"], str):
                        msg = "\"stderr\" field in plugin_test must be a string"
                        raise StarescPluginError(msg)
                    if not "expected" in plugin_test or not isinstance(plugin_test["expected"], bool):
                        msg = "\"expected\" field in plugin_test must exist and must be a boolean"
                        raise StarescPluginError(msg)
                    self.plugin_tests.append({
                        "stdout": plugin_test["stdout"] if "stdout" in plugin_test else "",
                        "stderr": plugin_test["stderr"] if "stderr" in plugin_test else "",
                        "expected": plugin_test["expected"]
                    })


    def get_command(self) -> str:
        """Get the Command"""
        return self.command


    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """Run the parsers on the result of the Command
        The parsers are run following a pipeline-like structure:
        the output of the parser N°1 is passed as input to the parser N°2,
        the output of the parser N°2 is passed as input to the parser N°3 and so on.

        A boolean condition is passed from parser to parser together with command result,
        if a parser find that one of his condition is matched, it sets the boolean condition to True.

        The first parser receieves as input the result of the Command and a boolean condition set to True.

        Attributes:
           result -- dict containing the result of the command executed on the target machine, it has the following format: {"stdout": command_stdout, "stderr": command_stderr}"""
        piped_result: dict[str, str] = result
        piped_boolean_result: bool = True                           #TODO handle not only and condition in piped matchers

        for parser in self.parsers:
            tmp_bool, piped_result = parser.parse(piped_result)
            piped_boolean_result &= tmp_bool

        return piped_boolean_result, piped_result


    def test_plugin(self) -> None:
        if not self.mode == "test_plugins":
            msg = "plugin can be tested only in \"test_plugins\" mode"
            raise StarescModeError(msg)
        for idx, plugin_test in enumerate(self.plugin_tests):
            result = {"stdout": plugin_test["stdout"], "stderr": plugin_test["stderr"]}
            piped_result: dict[str, str] = result
            piped_boolean_result: bool = True

            for parser in self.parsers:
                tmp_bool, piped_result = parser.parse(piped_result)
                piped_boolean_result &= tmp_bool
            if piped_boolean_result == plugin_test["expected"]:
                self.logger.debug(f"plugin_test success", f"{self.plugin_test_string}.plugin_test_{idx+1}")
            else:
                self.logger.debug(f"plugin_test failed", f"{self.plugin_test_string}.plugin_test_{idx + 1}")
