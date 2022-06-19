from tabulate import tabulate
from typing import Tuple

from lib.exporter.exporter import Exporter
from lib.output import Output
from lib.log import StarescLogger


class StdoutExporter(Exporter):

    logger: StarescLogger
    scan_summary: dict

    def __init__(self, filename: str = ''):
        self.logger = StarescLogger()
        self.scan_summary = {}
        super().__init__(filename)


    def add_output(self, output: Output) -> None:
        self.logger.print_if_vuln(output)

        if output.is_vuln_found():
            host = output.target.get_hostname(output.target.connection)
            port = output.target.get_port(output.target.connection)

            if f"{host}:{port}" not in self.scan_summary: 
                self.scan_summary[f"{host}:{port}"] = {}

            
            if output.plugin.severity in self.scan_summary[f"{host}:{port}"]:
                self.scan_summary[f"{host}:{port}"][output.plugin.severity] += 1
            
            else:
                self.scan_summary[f"{host}:{port}"][output.plugin.severity] = 1



    def export(self) -> None:
        headers = ["HOST", "SEVERITY", "VULN FOUND"]
        fmt = "github"

        tab = []
        for host in self.scan_summary.keys():
            first = True
            for sev, count in self.scan_summary[host].items():
                if first:
                    tab.append([host, sev, count])
                    first = False
                else:
                    tab.append(["", sev, count])
            tab.append(["-", "-", "-"])
    
        print(tabulate(tab, headers=headers, tablefmt=fmt))

