from typing import Tuple
import re, logging

# Configure logger
logging.basicConfig(format='[STARESC]:[%(asctime)s]:[%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


#results = [
#        {
#          "stdout": "cekout",
#          "stderr": ""
#        },
#        {
#          "stdout": "Linux cekout-virtual-machine 5.15.0-27-generic #28-Ubuntu SMP Thu Apr 14 04:55:28 UTC 2022 x86_64 x86_64 x86_64 GNU/Linux",
#          "stderr": ""
#        }
#]


'''basic structure of the yaml file
{
    'id': 'basic',                                          # id of the plugin
    'tests': [{                                             # list of the test (commands to check) to perform
            'command': 'whoami',                            # command to test
            'parsers': [{                                   # list of the parsers (matcher/extractor) to run on the result of the command
                    'parser_type': 'extractor',             # type of the parser, can be matcher or extractor, matcher is not supported yet
                    'part': 'stdout',
                    'rule': {                               # rule of the parser, can be a regex or a word finder
                        type: 'regex'                       
                        'regex': ['*']
                    
            }]
        },
        {
            'command': 'uname -a',
            'parsers': [{
                    'parser_type': 'extractor',
                    'rule': {
                        type: 'regex'
                        'regex': ['*']
                    
            }]
        }]
}

An extractor use a word or a regex, it finds a portion of text based on its rule and extracts it
The parsers of a test are executed as a pipeline on the result of the executed command
    the result of the command has the following shape: (TODO chose to keep or not stdin)
        { 
            "stdout": "",
            "stderr": ""
        }
'''

# parent class of matcher and extractor
# it represents a parser with its rule
class Parser:

    ALLOWED_PARTS = [ "stdout", "stderr", "all" ]
    ALLOWED_RULES = [ "regex", "word" ]
    ALLOWED_CONDS = [ "and", "or" ]

    # rule_type can be "regex" or "word" for matching the command outputs
    rule_type: str
    # rules
    rules: list[str]
    # stdout or stderr or all
    parts: list
    # and/or conditions
    condition: str
    
    @staticmethod
    def __get_part(d: dict) -> str:
        if "part" in d:
            if d["part"] in Parser.ALLOWED_PARTS:
                return d["part"]
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
            if isinstance(d["rules"]) and len(d["rules"]) >= 1:
                return d["rules"]
            else:
                raise Exception("Invalid rules format")
        else:
            raise Exception("No rule specified")


    def __init__(self, parser_content: dict):

        try:
            # TODO user can specify more parts in yaml file. VERY LOW PRIORITY!!
            self.parts     = self.__get_part(parser_content)
            self.rule_type = self.__get_rule_type(parser_content)
            self.condition = self.__get_condition(parser_content)
            self.rules     = self.__get_rules(parser_content)
        
        except Exception as e:
            raise e


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
    def match(self, result: dict[str, str]) -> Tuple[bool, dict[str, str]]:
        # Not global and centralized enough
        MATCHER_TO_FUNC = {
            "regex" : self.__match_regex,
            "word"  : self.__match_word
        }
        # TODO static centralized way to save possible values for parts
        # VALE: didn't understand, but "all" logic implemented in parent class
        # parts_to_check = self.parts
        return MATCHER_TO_FUNC[self.rule_type](self.parts, result)


# class that represents an extractor, it is a parser that implements the method extract
class Extractor(Parser):

    def __init__(self, parser_content: dict):
        super().__init__(parser_content)


    def __extract_regex(self, parts_to_check, result: dict[str, str]) -> dict[str, str]:
        # TODO return whole text or only the part that matches the regex
        extracted_regex = {"stdout": "", "stderr": "" }
        for p in parts_to_check:
            tmp_ext = re.findall(self.rules[0], result[p])
            # TODO how to handle multiple matches?
            if len(tmp_ext) >= 1:
                extracted_regex[p] += tmp_ext[0] #pick only the first match
        return extracted_regex


    # TODO do we need this method?
    def __extract_word(self, parts_to_check, result: dict[str, str]) -> dict[str, str]:
        extracted_words = {"stdout": "", "stderr": "" }
        for p in parts_to_check:
            if self.rules[0] in result[p]:
                extracted_words[p] += self.rules[0]
        return extracted_words
    
    # Method that return a dict with the same shape of result one (see 'result of the command' )
    # it search the given word or regex on result (stdin, stdout and stderr) and return a result with the content it found
    # eg: result: {stdin: "hello", stdout: "hello how", stderr: "who is "}, regex to match: ".ho" --> ret: {stdin: "", stdout: " ho", stderr: "who"}
    def extract(self, result: dict[str, str]) -> list(str):
        # Not global and centralized enough
        MATCHER_TO_FUNC = {
            "regex" : self.__extract_regex,
            "word"  : self.__extract_word
        }
        # TODO static centralized way to save possible values for parts
        # VALE: didn't understand, but "all" logic implemented in parent class
        # parts_to_check = self.parts
        return MATCHER_TO_FUNC[self.rule_type](self.parts, result)


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

        if isinstance(self.parsers[0], Extractor):
            parse_mod = "Extractor"
        elif isinstance(self.parsers[0], Matcher):
            parse_mod = "Matcher"
        else:
            raise Exception("Unknown parser type")

        for parser in self.parsers:
            if isinstance(parser, Extractor):
                if parse_mod == "Extractor":
                    piped_result = parser.extract(piped_result)
                else:
                    raise Exception("Mixed parsing Matcher/Extractor not supported yet")
            elif isinstance(parser, Matcher):
                if parse_mod == "Matcher":
                    tmp_bool, piped_result = parser.match(piped_result)
                    piped_boolean_result &= tmp_bool
                else:
                     raise Exception("Mixed parsing Extractor/Matcher not supported yet")
            else:
                raise Exception("Unknown parser type")

        return piped_boolean_result, piped_result

# class that represents the plugin
# it contains info about the plugin (eg: id) and the list of tests to performs
# methods get_matcher(), get_command() and parse() implemented for backward compatibility
class Plugin:
    # mandatory fields
    tests: list[Test]
    id: str
    distribution_matcher: str               # TODO change name, now "matcher" is preserved for retro-compatibility

    # optional plugin info
    author: str
    name: str
    description: str
    cve: str
    reference: str
    cvssv3: float
    cvssv2: float
    severity: str
    remediation: str
    # TODO tags?



    def __init__(self, plugin_content: dict):
        if not "id" in plugin_content:
            raise Exception("no id specified!")
        self.id = plugin_content["id"]

        if not "distr_matcher" in plugin_content:
            logger.info("No distr_matcher specified, all distro accepted by default")
            self.distribution_matcher = ".*"
        else:
            self.distribution_matcher = plugin_content["distr_matcher"]

        if (not "tests" in plugin_content) or  (not isinstance(plugin_content["tests"], list))  or len(plugin_content["tests"]) < 1:
            raise Exception("no test specified or invalid syntax!")
        self.tests = []
        for test_content in plugin_content["tests"]:
            self.tests.append(Test(test_content))

        self.__intialize_opt_info(plugin_content)

    def __intialize_opt_info(self, plugin_content: dict):
        for info in ["name", "cve", "cvssv3", "cvssv2", "author", "description", "severity", "reference", "remediation"]:
            if info in plugin_content:
                setattr(self, info, plugin_content[info])

    def get_distribution_matcher(self) -> str:
        return self.distribution_matcher

    def get_tests(self) -> list[Test]:
        return self.tests
