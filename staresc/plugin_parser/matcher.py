import re
from typing import Tuple

from staresc.log import StarescLogger
from staresc.plugin_parser import Parser


class Matcher(Parser):
    """Matcher is the class representing a matcher.

    The parse() method of the matcher checks if the given rules match the command result.
    This is a subclass of Parser.
    """

    def __init__(self, parser_content: dict, mode: str, logger: StarescLogger = None, plugin_test_string: str = None):
        """Class constructor

        Attributes:
           parser_content -- dict containing data of the given parser read from the YAML file
        """
        self.mode = mode
        self.logger = logger
        self.plugin_test_string = plugin_test_string
        if self.mode == "test_plugins":
            self.logger.debug(f"parser_type: matcher", self.plugin_test_string)
        super().__init__(parser_content)


    def __match_regex(self, parts_to_check: list[str], result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """Check if the regexes of the rules match on a given part of the command result

        Attributes:
           parts_to_check -- list of strings that identifies which part of the output to check
           result -- output of the command run on the target machine
        """
        # We have "and"/"or", already validated during __init__, so if it is not "and" is "or"
        is_matched = ( self.condition == "and" )
        
        for regex in self.rules:
            if any(re.search(regex, result[p]) for p in parts_to_check):
                # one regex that matches is enough
                if self.condition == "or":
                    return (True, result)
            # all regexes must match
            elif self.condition == "and":
                    return (False, result)
        return (is_matched, result)


    def __match_word(self, parts_to_check: list[str], result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """Check if a given part of the command result contains the strings of the rules

        Attributes:
           parts_to_check -- list of strings that identifies which part of the output to check
           result -- output of the command run on the target machine
        """

        # We have "and"/"or", already validated during __init__, so if it is not "and" is "or"
        is_matched = ( self.condition == "and" )

        for word in self.rules:
            if any(word in result[p] for p in parts_to_check):
                # one regex that matches is enough
                if self.condition == "or":
                    return (True, result)
            elif self.condition == "and":         #all word must match
                return (False, result)
        return (is_matched, result)

    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """Method used to parse the result of a command and to check if the vuln is found.
        In this class, this method checks if the matching rules are satisfied.
        It doesn't modify the content of result.

        Attributes:
            result -- dict containing the result of the command executed on the target machine, it has the following format: {"stdout": command_stdout, "stderr": command_stderr}
        """
        # Not global and centralized enough
        MATCHER_TO_FUNC = {
            "regex" : self.__match_regex,
            "word"  : self.__match_word
        }
        is_matched, tmp_res = MATCHER_TO_FUNC[self.rule_type](self.parts, result)
        is_matched ^= self.invert_match         # is_matched = invert_match ? !is_matched : is_matched
        return (is_matched, tmp_res)

