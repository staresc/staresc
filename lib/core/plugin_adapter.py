import yaml, re, logging
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

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


'''structure of the yaml file
id: 'CVE-2021-3156'                                         # id of the plugin
author: 'cekout'
name: 'sudoedit -s'
description: 'Check if sudo is vulnerable to sudoedit -s heap-based buffer overflow'
cve: 'CVE-2021-3156'
reference: 'https://nvd.nist.gov/vuln/detail/CVE-2021-3156'
cvssv3: 7.8
cvssv2: 0
severity: 'high'
tests:                                                              # list of the test (commands to check) to perform
  - command: 'sudoedit -s "1234567890123456789012\\"'               # command to test
    parsers:                                                        # list of the parsers (matcher/extractor) to run on the result of the command
      - parser_type: 'matcher'                                      # type of the parser
        part: 'all'                                                 # part of the output of the command to analyze (stdout/stderr)
        rule_type: 'word'                                           # type of rules of the parser
        condition: 'or'                                             # how the matcher evaluate rules, or -> one match is enough, and -> all rules should match
        rules:                                                      # list of rules
          - 'memory'
          - 'Error'
          - 'Backtrace'
  - command: 'sudo --version'
    parsers:
      - parser_type: 'extractor'            
        rule_type: 'regex'      
        rules:
          - 'Sudo version .*\n'                                     # regex to extract, only the text that match the regex is extracted, IMPORTANT: keep regex in a string with single quotes (double quotes could broke yaml parser)
      - parser_type: 'extractor'                                    # output of the first extractor is piped as input for the second extraxtor
        rule_type: 'regex'
        rules:
          - '(\d+\.)(\d+\.)(\.)?(\d)'


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
    @staticmethod
    def __check_part(part):
        return part in ["stdout", "stderr", "all"]

    rule_type: str  #regex or word
    rules: [str]
    part: str     #stdout or stderr or all
    condition: str #and/or


    def __init__(self, parser_content: dict):
        if not "part" in parser_content:      # TODO user can specify more parts in yaml file
            self.part = "all"
        else:
            self.part = parser_content["part"]

        if not self.__class__.__check_part(self.part):        #pythonic? clean?
            raise Exception("unvalid part value!")

        if not "rule_type" in parser_content:
            raise Exception("no rule_type specified in parser definition!")
        if parser_content["rule_type"] != "regex" and parser_content["rule_type"] != "word":         #TODO define function that checks rule_type format
            raise Exception(f'Unsupported rule_type: {parser_content["rule_type"]}')
        self.rule_type = parser_content["rule_type"]


        if "condition" in parser_content and parser_content["condition"] != "and" and parser_content["condition"] != "or":
            raise Exception(f'Invalid condition {parser_content["condition"]}')
        if "condition" in parser_content:
            self.condition = parser_content["condition"]
        else:
            self.condition = "and"

        if (not "rules" in parser_content) or (not isinstance(parser_content["rules"], list)) or (len(parser_content["rules"]) < 1):
            raise Exception("no rule specified or invalid format")
        self.rules = parser_content["rules"]




# class that represents a matcher, it is a parser that implements the method match
class Matcher(Parser):
    #Method that return true if the given word or regex (saved during construction, see Parser constructor) is found
    def match(self, result: dict[str, str]) -> (bool, dict[str, str]):
        parts_to_check: [str] = []
        if self.part == "all":
            parts_to_check += ["stdout", "stderr"]     # TODO static centralized way to save possible values for parts 
        else :
            parts_to_check.append(self.part)
        
        if self.rule_type == "regex":
            return self.__match_regex(parts_to_check, result)
        elif self.rule_type == "word":
            return self.__match_word(parts_to_check, result)


    def __match_regex(self, parts_to_check: [str], result: dict[str, str]) -> (bool, dict[str, str]):
        if self.condition == "and":
            is_matched = True
        elif self.condition == "or":
            is_matched = False
        else:
            raise Exception(f"Unsupported condition {self.condition}")

        for regex in self.rules:
            if any(re.search(regex, result[p]) for p in parts_to_check):
                if self.condition == "or":          #one regex that matches is enough
                    return (True, result)
            elif self.condition == "and":         #all regexes must match
                    return (False, result)
        return (is_matched, result)

    def __match_word(self, parts_to_check: [str], result: dict[str, str]) -> (bool, dict[str, str]):
        if self.condition == "and":
            is_matched = True
        elif self.condition == "or":
            is_matched = False
        else:
            raise Exception(f"Unsupported condition {self.condition}")

        for word in self.rules:
            if any(word in result[p] for p in parts_to_check):
                if self.condition == "or":          #one regex that matches is enough
                    return (True, result)
            elif self.condition == "and":         #all word must match
                return (False, result)
        return (is_matched, result)


# class that represents an extractor, it is a parser that implements the method extract
class Extractor(Parser):
    #Method that return a dict with the same shape of result one (see 'result of the command' )
    # it search the given word or regex on result (stdin, stdout and stderr) and return a result with the content it found
    # eg: result: {stdin: "hello", stdout: "hello how", stderr: "who is "}, regex to match: ".ho" --> ret: {stdin: "", stdout: " ho", stderr: "who"}
    def extract(self, result: dict[str, str]) -> [str]:
        parts_to_check: [str] = []
        if self.part == "all":
            parts_to_check += ["stdout", "stderr"]  # TODO static centralized way to save possible values for parts
        else:
            parts_to_check.append(self.part)

        if self.rule_type == "regex":
            return self.__extract_regex(parts_to_check, result)
        elif self.rule_type == "word":
            return self.__extract_word(parts_to_check, result)


    def __extract_regex(self, parts_to_check, result: dict[str, str]) -> dict[str, str]:
        extracted_regex = {"stdout": "", "stderr": "" }                       # TODO return whole text or only the part that matches the regex
        for p in parts_to_check:
            tmp_ext = re.search(self.rules[0], result[p])
            if tmp_ext:                                                            # TODO how to handle multiple matches?
                extracted_regex[p] += tmp_ext.group()                       # extract the part that matches the regex (the first one)
        return extracted_regex

    def __extract_word(self, parts_to_check, result: dict[str, str]) -> dict[str, str]:    # TODO do we need this method?
        extracted_words = {"stdout": "", "stderr": "" }
        for p in parts_to_check:
            if self.rules[0] in result[p]:
                extracted_words[p] += self.rules[0]
        return extracted_words


# class that represents a single test (command and relative parsers)
class Test:
    command: str
    parsers: [Parser]

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
    def parse(self, result: dict[str, str]) -> (bool, dict[str, str]):          #TODO implement support for matchers and mixed (pipe of matcher and extractors) parsing, problem: matchers return boolean, not dict[str, str]
        piped_result: dict[str, str] = result
        piped_boolean_result: bool = True                           #TODO handle not only and condition in piped matchers

        for parser in self.parsers:
            if isinstance(parser, Extractor):
                if piped_boolean_result:
                    piped_result = parser.extract(piped_result)
            elif isinstance(parser, Matcher):
                if piped_boolean_result:
                    tmp_bool, piped_result = parser.match(piped_result)
                    piped_boolean_result &= tmp_bool
            else:
                raise Exception("Unknown parser type")

        return piped_boolean_result, piped_result

#class that represents the plugin
# it contains info about the plugin (eg: id) and the list of tests to performs
# methods get_matcher(), get_command() and parse() implemented for backward compatibility
class Plugin:
    # mandatory fields
    tests: [Test]
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

    def get_tests(self) -> [Test]:
        return self.tests
