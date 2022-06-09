
from typing import Tuple


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
        if "part" in d:
            if d["part"] in Parser.ALLOWED_PARTS:
                return [ d["part"] ]
            else:
                raise Exception("Invalid part value!")
        else:
            return Parser.ALLOWED_PARTS

    @staticmethod
    def __get_rule_type(d: dict) -> str:
        if "rule_type" in d:
            if d["rule_type"] in Parser.ALLOWED_RULES:
                return d["rule_type"]
            else:
                raise Exception(f'Unsupported rule_type: {d["rule_type"]}')
        else:
            raise Exception("No rule_type specified in parser definition!")

    @staticmethod
    def __get_condition(d: dict) -> str:
        if "condition" in d:
            if d["condition"] in Parser.ALLOWED_CONDS:
                return d["condition"]
            else:
                raise Exception(f'Invalid condition {d["condition"]}')
        else:
            return "and"

    @staticmethod
    def __get_rules(d: dict) -> list:
        if "rules" in d:
            if isinstance(d["rules"], list) and len(d["rules"]) >= 1:
                return d["rules"]
            else:
                raise Exception("Invalid rules format")
        else:
            raise Exception("No rule specified")

    @staticmethod
    def __get_invert_match(d: dict) -> bool:
        if "invert_match" in d:
            if d["invert_match"] in Parser.ALLOWED_INV_MATCH:
                return d["invert_match"]
            else:
                raise Exception(f'Invalid invert_match {d["invert_match"]}')
        else:
            return False

    def __init__(self, parser_content: dict):

        try:
            # TODO user can specify more parts in yaml file. VERY LOW PRIORITY!!
            self.parts     = self.__get_part(parser_content)
            self.rule_type = self.__get_rule_type(parser_content)
            self.condition = self.__get_condition(parser_content)
            self.rules     = self.__get_rules(parser_content)
            self.invert_match = self.__get_invert_match(parser_content)
        
        except Exception as e:
            raise e

    def parse(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        pass