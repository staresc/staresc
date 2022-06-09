from typing import Tuple

from lib.plugin_parser import Parser, Matcher, Extractor

# class that represents a single test (command and relative parsers)
class Test:
    command: str
    parsers: list[Parser]

    def __init__(self, test_content: dict):
        if not "command" in test_content:
            raise Exception("No command defined!")
        self.command = test_content["command"]

        if (not "parsers" in test_content) or (not isinstance(test_content["parsers"], list)) or len(test_content["parsers"]) < 1:
            raise Exception("no parser specified or invalid syntax!")
        self.parsers = []
        for parser_content in test_content["parsers"]:
            if not "parser_type" in parser_content:
                raise Exception("parser_type field not found!")
            if parser_content["parser_type"] == "matcher":
                self.parsers.append(Matcher(parser_content))
            elif parser_content["parser_type"] == "extractor":
                self.parsers.append(Extractor(parser_content))
            else:
                raise Exception("Invalid parser_type value")

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
