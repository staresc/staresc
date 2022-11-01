from typing import Any
from staresc.output import Output
from staresc.connection import Connection

class Handler:
    """Generic handler
    
    This is a generic handler for StarescExporter
    """

    out: str

    def __init__(self, out: str) -> None:
        self.out = out

    def import_handler(self, o: Output):
        """Import Handler
        
        This method is called on the hadler when a new output is added to the 
        queue. Each handler can decide to either do nothing or perform special
        operations, such as the StarescStdoutHandler, which prints the 
        vulnerabilities when discovered in the Output
        """
        pass

    def export_handler(self, outputs: list[Output], outfile: str):
        """Export Handler
        
        This method is called on the hadler when the execution is over and the
        whole queue is converted to a list.
        """
        pass


def technical_details(o: Output):
    tech_details = ""
    for i in range(len(o.test_results)):
        tech_details += f"cmd: {o.test_results[i]['stdin']}\n"
        tech_details += f"stdout: {o.test_results_parsed[i]['stdout']}\n"
        tech_details += f"stderr: {o.test_results_parsed[i]['stderr']}\n"
        tech_details += "\n\n\n"
    return tech_details


def complete_log(o: Output):
    ret = []
    for test_res in o.test_results:
        ret.append({
            "stdin": test_res["stdin"],
            "stdout": test_res["stdout"],
            "stderr": test_res["stderr"],
        })
    return str(ret)


COLUMNS_TO_FUNC:dict[str, Any] = {
    "Host IP"            : lambda x : str((Connection)(x.target.connection).hostname),
    "Port"               : lambda x : str((Connection)(x.target.connection).port),
    "Scheme"             : lambda x : str((Connection)(x.target.connection).scheme),
    "Vulnerable"         : lambda x : str(x.is_vuln_found()),
    "Any timeout"        : lambda x : str(any(x.get_timeouts())),
    "CVSS score"         : lambda x : str(getattr(x.plugin, 'cvss', 0.0)),
    "Vulnerability name" : lambda x : str(getattr(x.plugin, 'name')),
    "Description"        : lambda x : str(getattr(x.plugin, 'description')),
    "Technical details"  : technical_details,
    "Remediation"        : lambda x : str(getattr(x.plugin, 'remediation', '')),
    "CVE"                : lambda x : str(getattr(x.plugin, 'CVE', '')),
    "CVSS vector"        : lambda x : str(getattr(x.plugin, 'cvss_vector', '')),
    "Complete log"       : complete_log,
}