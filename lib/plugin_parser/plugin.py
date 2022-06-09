from lib.plugin_parser import Test

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
    cvss: float
    severity: str
    remediation: str
    # TODO tags?



    def __init__(self, plugin_content: dict):
        if not "id" in plugin_content:
            raise Exception("no id specified!")
        self.id = plugin_content["id"]

        if not "distr_matcher" in plugin_content:
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
        for info in ["name", "cve", "cvss", "author", "description", "severity", "reference", "remediation"]:
            if info in plugin_content:
                setattr(self, info, plugin_content[info])

    def get_distribution_matcher(self) -> str:
        return self.distribution_matcher

    def get_tests(self) -> list[Test]:
        return self.tests