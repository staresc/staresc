from typing import Tuple

from staresc.exceptions import StarescPluginError

# parent class of matcher and extractor
# it represents a parser with its rule
class Parser:
    """Parser is the class handling the content of the plugin's tests

    High level object that represents a parser that implements the method parse() used to parse the result of a Command (see the class Test).
    This class is extended when a new type of parser is implemented
    """

    ALLOWED_PARTS = [ "stdout", "stderr" ]
    """Allowed Parts 

    list of valid values for the field Parts 
    """
    ALLOWED_RULES = [ "regex", "word" ]
    """Allowed Rules

    list of valid values for the field Rules 
    """
    ALLOWED_CONDS = [ "and", "or" ]
    """Allowed Conditions 

    list of valid values for the field Condition
    """

    ALLOWED_INV_MATCH = [True, False]
    """Allowed Invert Match 

    list of valid values for the field Invert Match 
    """

    rule_type: str
    """Rule Type 

    type of rule applied by the parser, current supported rule types are defined in Allowed Rules
    """
    rules: list[str]
    """Rules 

    list of rules that the parser checks
    """
    parts: list[str]
    """Parts 

    list of parts of the result on which the parser checks the given rules, current supported parts are defined in Allowed Parts
    """
    condition: str
    """Condition 

    condition applied to join the results of the checks of the rules.
    An "and" value implies that all the rules checks have to return true meanwhile,
    with an "or" value, just one rules TODO finish
    """
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