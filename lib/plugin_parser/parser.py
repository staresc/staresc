
from typing import Tuple

from lib.exceptions import StarescPluginError


# parent class of matcher and extractor
# it represents a parser with its rule
class Parser:

    ALLOWED_PARTS = [ "stdout", "stderr" ]
    ALLOWED_RULES = [ "regex", "word" ]
    ALLOWED_CONDS = [ "and", "or" ]
    ALLOWED_INV_MATCH = [True, False]

    # rule_type can be "regex" or "word" for matching the command outputs
    rule_type: str
    # rules
    rules: list[str]
    # stdout or stderr or all
    parts: list[str]
    # and/or conditions
    condition: str
    # True: invert the result of matcher, False: don't invert
    invert_match: bool
    
    @staticmethod
    def __get_part(d: dict) -> list[str]:
        try:
            selected = d["part"]

        except KeyError:
            return Parser.ALLOWED_PARTS

        if selected in Parser.ALLOWED_PARTS:
            return [ selected ]
        else:
            msg = "Invalid part value"
            raise StarescPluginError(msg)
            

    @staticmethod
    def __get_rule_type(d: dict) -> str:
        try:
            selected = d["rule_type"]
        
        except KeyError:
            msg = "No rule_type specified in parser definition"
            raise StarescPluginError(msg)

        if selected in Parser.ALLOWED_RULES:
            return selected
        else:
            msg = f"Unsupported rule_type: {selected}"
            raise StarescPluginError(msg)


    @staticmethod
    def __get_condition(d: dict) -> str:
        try:
            selected = d["condition"]

        except KeyError:
            return "and"

        if selected in Parser.ALLOWED_CONDS:
            return selected
        else:
            msg = f'Invalid condition {selected}'
            raise StarescPluginError(msg)


    @staticmethod
    def __get_rules(d: dict) -> list:
        try:
            selected = d["rules"]
        
        except KeyError:
            msg = "No rule_type specified in parser definition"
            raise StarescPluginError(msg)

        if (isinstance(selected, list)) and (len(selected) > 0):
            return selected
        else:
            msg = "No rule specified"
            raise StarescPluginError(msg)


    @staticmethod
    def __get_invert_match(d: dict) -> bool:
        try:
            selected = d["invert_match"]
        
        except KeyError:
            return False

        if selected in Parser.ALLOWED_INV_MATCH:
            return selected
        else:
            msg = f"Invalid invert_match {d['invert_match']}"
            raise StarescPluginError(msg)
            

    def __init__(self, parser_content: dict):
        # TODO user can specify more parts in yaml file. VERY LOW PRIORITY!!
        self.parts        = self.__get_part(parser_content)
        self.rule_type    = self.__get_rule_type(parser_content)
        self.condition    = self.__get_condition(parser_content)
        self.rules        = self.__get_rules(parser_content)
        self.invert_match = self.__get_invert_match(parser_content)


    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        pass