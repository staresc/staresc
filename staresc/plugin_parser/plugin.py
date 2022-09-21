from staresc.exceptions import StarescPluginError
from staresc.plugin_parser import Test

class Plugin:
    """Plugin is the class handling plugins content

    high level object that represents a plugin, with its data and functionalities
    """

    ALLOWED_MATCH_CONDS = [ "and", "or" ]

    # mandatory fields
    tests: list[Test]
    """List of Tests 
    
    Each element of this list represents a test that is run on target machines
    """
    id: str
    """ID

        This is the ID of the plugin, it is used as a unique identifier for the plugin
    """
    # TODO change name, now "matcher" is preserved for retro-compatibility
    distribution_matcher: str
    """Distribution Matcher

        This field contains a regexp that identifies the target OSs supported by the plugin
    """
    match_condition: str
    # optional plugin info
    author: str
    """Author

        This string indentifies the plugin's author
    """
    name: str
    """Name

        This string indentifies the name of the vulnerability checked by the plugin
    """
    description: str
    """Description

        This field contains a decription of the vulnerability discovered by the plugin
    """
    cve: str
    """CVE

        This field contains the CVE ID for the vulnerability checked by the plugin
    """
    reference: str
    """Reference

        This field contains urls for useful references about the plugin and the vulnerability
    """
    cvss: float
    """CVSS

        CVSSv3 score of the vulnerability
    """
    severity: str
    """Vulnerability Severity

        Severity of the given vulnerability, based on CVSSv3 score. 
    """
    remediation: str
    """Possible Remediation

        This field contains advices about remediations options for the given vulnerability. 
    """
    cvss_vector: str

    @staticmethod
    def __get_condition(d: dict) -> str:
        try:
            selected = d["match_condition"]

        except KeyError:
            return "and"

        if selected in Plugin.ALLOWED_MATCH_CONDS:
            return selected
        else:
            msg = f'Invalid condition {selected}'
            raise StarescPluginError(msg)


    def __init__(self, plugin_content: dict):
        """Class constructor

        Attributes:
           plugin_content -- dict containing data parsed from the YAML file
        """
        try:
            self.id   = plugin_content["id"]
            self.match_condition = Plugin.__get_condition(plugin_content)
            test_list = plugin_content["tests"]

        except KeyError:
            msg = "plugin syntax is wrong"
            raise StarescPluginError(msg)

        if (not isinstance(test_list, list))  or len(test_list) < 1:
            msg = "no test specified or invalid syntax"
            raise StarescPluginError(msg)

        if "distr_matcher" in plugin_content:
            self.distribution_matcher = plugin_content["distr_matcher"]
        else:
            self.distribution_matcher = ".*"

        self.tests = []
        for test_content in test_list:
            self.tests.append(Test(test_content))

        self.__intialize_opt_info(plugin_content)


    def __intialize_opt_info(self, plugin_content: dict):
        """Initialize optional informations. If set them only if they are available

        Attributes:
           plugin_content -- dict containing data parsed from the YAML file"""
        for info in ["name", "cve", "cvss", "author", "description", "severity", "reference", "remediation", "cvss_vector"]:
            if info in plugin_content:
                setattr(self, info, plugin_content[info])


    def get_distribution_matcher(self) -> str:
        """Get the Ditribution Matcher"""
        return self.distribution_matcher


    def get_tests(self) -> list[Test]:
        """Get the list of Tests"""
        return self.tests