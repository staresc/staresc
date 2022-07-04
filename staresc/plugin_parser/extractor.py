import re
from typing import Tuple

from staresc.plugin_parser import Parser

class Extractor(Parser):
    """Extractor is the class representing an extractor.

    The parse() method of the extractor extracts part of the command result using the given rules.
    This is a subclass of Parser.
    """

    def __init__(self, parser_content: dict):
        """Class constructor

        Attributes:
           parser_content -- dict containing data of the given parser read from the YAML file
        """
        super().__init__(parser_content)


    def __extract_regex(self, parts_to_check, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """From the given parts of the command result, extract the regexes of the rules

        Attributes:
           parts_to_check -- list of strings that identifies which part of the output to check
           result -- output of the command run on the target machine
        """
        extracted_regex = {"stdout": "", "stderr": "" }
        is_extracted: bool = False
        for p in parts_to_check:
            tmp_ext = re.search(self.rules[0], result[p])
            if tmp_ext:
                is_extracted = True
                # extract the part that matches the regex (the first one)
                extracted_regex[p] += tmp_ext.group()
        return (is_extracted, extracted_regex)


    def __extract_word(self, parts_to_check, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """From the given parts of the command result, extract the strings of the rules

        Attributes:
           parts_to_check -- list of strings that identifies which part of the output to check
           result -- output of the command run on the target machine
        """
        extracted_words = {"stdout": "", "stderr": "" }
        is_extracted: bool = False
        for p in parts_to_check:
            if self.rules[0] in result[p]:
                is_extracted = True
                extracted_words[p] += self.rules[0]
        return (is_extracted, extracted_words)
    
    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        """Method used to parse the result of a command and to check if the vuln is found.
        In this class, this method extract part of the result using the rules and return them.
        The boolean part of the return value is set to true if something is extracted, false otherwise.

        Attributes:
            result -- dict containing the result of the command executed on the target machine, it has the following format: {"stdout": command_stdout, "stderr": command_stderr}
        """
        # Not global and centralized enough
        MATCHER_TO_FUNC = {
            "regex" : self.__extract_regex,
            "word"  : self.__extract_word
        }
        return MATCHER_TO_FUNC[self.rule_type](self.parts, result)