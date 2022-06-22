import re
from typing import Tuple

from staresc.plugin_parser import Parser

# class that represents a matcher, it is a parser that implements the method match
class Matcher(Parser):

    def __init__(self, parser_content: dict):
        super().__init__(parser_content)


    def __match_regex(self, parts_to_check: list[str], result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        
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

    # Method that return true if the given word or regex 
    # (saved during construction, see Parser constructor) is found
    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        # Not global and centralized enough
        MATCHER_TO_FUNC = {
            "regex" : self.__match_regex,
            "word"  : self.__match_word
        }
        # TODO static centralized way to save possible values for parts
        # VALE: didn't understand, but "all" logic implemented in parent class
        # parts_to_check = self.parts
        is_matched, tmp_res = MATCHER_TO_FUNC[self.rule_type](self.parts, result)
        is_matched ^= self.invert_match         # is_matched = invert_match ? !is_matched : is_matched
        return (is_matched, tmp_res)

