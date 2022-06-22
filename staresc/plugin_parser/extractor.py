import re
from typing import Tuple

from staresc.plugin_parser import Parser

# class that represents an extractor, it is a parser that implements the method extract
class Extractor(Parser):

    def __init__(self, parser_content: dict):
        super().__init__(parser_content)


    def __extract_regex(self, parts_to_check, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        # TODO return whole text or only the part that matches the regex
        extracted_regex = {"stdout": "", "stderr": "" }
        is_extracted: bool = False
        for p in parts_to_check:
            tmp_ext = re.search(self.rules[0], result[p])
            # TODO how to handle multiple matches?
            if tmp_ext:
                is_extracted = True
                # extract the part that matches the regex (the first one)
                extracted_regex[p] += tmp_ext.group()
        return (is_extracted, extracted_regex)


    # TODO do we need this method?
    def __extract_word(self, parts_to_check, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        extracted_words = {"stdout": "", "stderr": "" }
        is_extracted: bool = False
        for p in parts_to_check:
            if self.rules[0] in result[p]:
                is_extracted = True
                extracted_words[p] += self.rules[0]
        return (is_extracted, extracted_words)
    
    # Method that return a dict with the same shape of result one (see 'result of the command' )
    # it search the given word or regex on result (stdin, stdout and stderr) and return a result with the content it found
    # eg: result: {stdin: "hello", stdout: "hello how", stderr: "who is "}, regex to match: ".ho" --> ret: {stdin: "", stdout: " ho", stderr: "who"}
    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        # Not global and centralized enough
        MATCHER_TO_FUNC = {
            "regex" : self.__extract_regex,
            "word"  : self.__extract_word
        }
        # TODO static centralized way to save possible values for parts
        # VALE: didn't understand, but "all" logic implemented in parent class
        # parts_to_check = self.parts
        return MATCHER_TO_FUNC[self.rule_type](self.parts, result)