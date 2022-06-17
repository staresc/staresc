from typing import Tuple
from lib.exceptions import StarescPluginError

from lib.plugin_parser import Parser, Matcher, Extractor

# class that represents a single test (command and relative parsers)
class Test:
    command: str
    parsers: list[Parser]

    def __init__(self, test_content: dict):
        self.parsers = []
        try:
            self.command = test_content["command"]
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
        for parser_content in parsers:
            try:
                p = MAP_PARSER[parser_content["parser_type"]](parser_content)
                self.parsers.append(p)

            except KeyError:
                msg = "invalid parser_type value"
                raise StarescPluginError(msg)


    def get_command(self) -> str:
        return self.command

    # method that, given a result of the command, runs all the parsers (matcher/extractor) on it
    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:          #TODO implement support for matchers and mixed (pipe of matcher and extractors) parsing, problem: matchers return boolean, not dict[str, str]
        piped_result: dict[str, str] = result
        piped_boolean_result: bool = True                           #TODO handle not only and condition in piped matchers

        for parser in self.parsers:
            tmp_bool, piped_result = parser.parse(piped_result)
            piped_boolean_result &= tmp_bool

        return piped_boolean_result, piped_result
