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
#          "stdin": "/usr/bin/whoami ",
#          "stdout": "cekout",
#          "stderr": ""
#        },
#        {
#          "stdin": "/usr/bin/uname -a",
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
            "stdin": "",
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
    regexes: [str]
    words: [str]
    part: str     #stdout or stderr or all
    condition: str #and/or


    def __init__(self, parser_content: dict):
        if not "part" in parser_content:      # TODO user can specify more parts in yaml file
            self.part = "all"
        else:
            self.part = parser_content["part"]

        if not self.__class__.__check_part(self.part):        #pythonic? clean?
            raise Exception("unvalid part value!")

        if not "rule" in parser_content:
            raise Exception("no rule specified in parser definition!")
        if not "type" in parser_content["rule"]:
            raise Exception("no type specified for the parser rule!")

        self.condition = "and"
        if "condition" in parser_content and parser_content["condition"] != "and" and parser_content["condition"] != "or":
            raise Exception(f'Invalid condition {parser_content["condition"]}')


        self.rule_type = parser_content["rule"]["type"]
        if self.rule_type == "regex":
            if not "regex" in parser_content["rule"]:
                raise Exception("regex type but regex field not present!")
            self.regex = parser_content["rule"]["regex"]
        elif self.rule_type == "word":
            if not "word" in parser_content["rule"]:
                raise Exception("word type but word field not present!")
            self.word = parser_content["rule"]["word"]
        else:
            raise Exception("Invalid rule type")


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
            is_matched = "true"
        elif self.condition == "or":
            is_matched = "false"
        #TODO implement matching multiple regex/word
        for regex in self.regexes:
            for p in parts_to_check:
                if re.search(regex, result[p]):
                    if self.condition == "or":          #one regex that matches is enough
                        return True
            if self.condition == "and":         #all regexes must match
                return False
        return is_matched

    def __match_word(self, parts_to_check: [str], result: dict[str, str]) -> (bool, dict[str, str]):
        for p in parts_to_check:
            if self.word in result[p]:
                return True
        return False

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
        extracted_regex = {"stdin": "", "stdout": "", "stderr": "" }                       # TODO return whole text or only the part that matches the regex
        for p in parts_to_check:
            tmp_ext = re.findall(self.regex, result[p])
            if len(tmp_ext) > 1:                                                            # TODO how to handle multiple matches?
                extracted_regex[p] += tmp_ext[0] #pick only the first match
        return extracted_regex

    def __extract_word(self, parts_to_check, result: dict[str, str]) -> dict[str, str]:    # TODO do we need this method?
        extracted_words = {"stdin": "", "stdout": "", "stderr": "" }
        for p in parts_to_check:
            if self.word in result[p]:
                extracted_words[p] += self.word
        return extracted_words


# class that represents a single test (command and relative parsers)
class Test:
    command: str
    parsers: [Parser]                   # TODO maybe distro matcher can be saved here

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

    # method that, given a result of the command, runs all the parsers (matcher/extractor) on it
    def parse(self, result: dict[str, str]) -> dict[str, str]:          #TODO implement support for matchers and mixed (pipe of matcher and extractors) parsing, problem: matchers return boolean, not dict[str, str]
        piped_result: dict[str, str] = result


        if isinstance(self.parsers[0], Extractor):
            parse_mod = "Extractor"
        elif isinstance(self.parsers[0], Matcher):
            parse_mod = "Matcher"
            if
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
                    pass
                else:
                     raise Exception("Mixed parsing Extractor/Matcher not supported yet")
            else:
                raise Exception("Unknown parser type")

        return piped_result

#class that represents the plugin
# it contains info about the plugin (eg: id) and the list of tests to performs
# methods get_matcher(), get_command() and parse() implemented for backward compatibility
class Plugin:
    tests: [Test]
    id: str
    distribution_matcher: str               # TODO change name, now "matcher" is preserved for retro-compatibility


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


    def get_matcher(self) -> str:
        return self.distribution_matcher


    def get_commands(self) -> list:
        command_list: [str] = []
        for t in self.tests:
            command_list.append(t.command)
        return command_list

    # during parsing, results of the command execution are passed to the pipeline of parser (see above)
    def parse(self, results: list) -> str:
        ret_str = ""
        for idx in range(len(results)):
            stdout = results[idx]
        #for idx, stdout in results:
            ret_str += str(self.tests[idx].parse({
                "stdin": "",                #TODO do we really need to pass stdin?
                "stdout": stdout,
                "stderr": ""
            })) + "\n\n"
        return ret_str

# during get_matcher call I initialize a Plugin obj that act as a python plugin module but is constructed using yaml file
# for the moment I keep these methods to make this plugin compatible with old python plugin modules
# TODO delete global var basic_plugin let the plugin object be garbage collected
def get_matcher() -> str:
    global basic_plugin
    f = open("cekout_test/test_yaml_plugin/basic.yaml", "r")
    plugin_content = yaml.load(f.read(), Loader=Loader)
    f.close()
    basic_plugin = Plugin(plugin_content)
    return basic_plugin.get_matcher()


def get_commands() -> list:
    return basic_plugin.get_commands()


def parse(output: list) -> str:
    return basic_plugin.parse(output)





def parse_plugin(plugin_path):
    f = open(plugin_path, "r")
    plugin_content = yaml.load(f.read(), Loader=Loader)
    print(plugin_content)
    f.close()




def main():
    parse_plugin("basic.yaml")


if __name__ == "__main__":
    main()