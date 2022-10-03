from typing import Tuple
from staresc.exceptions import PluginError

from staresc.plugin_parser import Parser, Matcher, Extractor


class Test:
    """Test is the class handling the content of the plugin's tests

    high level object that represents a single test run by the staresc engine using the plugin
    """

    command: str
    """Command 

    string containing the shell command to execute on the target machines
    """
    parsers: list[Parser]
    """Parsers list

    list containing the parsers (matchers/extractors) to run on the Command's results
    """

    def __init__(self, test_content: dict):
        """Class constructor

        Attributes:
           test_content -- dict containing data of the given test parsed from the YAML file
        """
        self.parsers = []
        try:
            self.command = test_content["command"]
            parsers      = test_content["parsers"]

        except KeyError:
            msg = "invalid syntax command/parsers"
            raise PluginError(msg)

        if (not isinstance(parsers, list)) or (len(parsers) < 1):
            msg = "no parser specified or invalid syntax"
            raise PluginError(msg)
        
        MAP_PARSER = {
            "matcher"   : Matcher,
            "extractor" : Extractor,
        }
        for parser_content in parsers:
            try:
                p = MAP_PARSER[parser_content["parser_type"]](parser_content)
                self.parsers.append(p)

            except KeyError:
                msg = "invalid parser_type value"
                raise PluginError(msg)


    def get_command(self) -> str:
        """Get the Command"""
        return self.command

    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:          #TODO implement support for matchers and mixed (pipe of matcher and extractors) parsing, problem: matchers return boolean, not dict[str, str]
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
