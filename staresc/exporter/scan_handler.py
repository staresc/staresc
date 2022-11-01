from tabulate import tabulate

from staresc.log import Logger
from staresc.output import Output
from staresc.exporter.handler import Handler, COLUMNS_TO_FUNC

class ScanHandler(Handler):
    logger:Logger
    scan_summary: dict

    def __init__(self, out: str) -> None:
        self.logger = Logger()
        self.scan_summary = {}
        super().__init__(out)


    def import_handler(self, o: Output):
        self.logger.print_if_vuln(o)

        if o.is_vuln_found() and o.plugin is not None:
            host = o.target.hostname
            port = o.target.port

            if f"{host}:{port}" not in self.scan_summary:
                self.scan_summary[f"{host}:{port}"] = {}

            if o.plugin.severity in self.scan_summary[f"{host}:{port}"]:
                self.scan_summary[f"{host}:{port}"][o.plugin.severity] += 1
            else:
                self.scan_summary[f"{host}:{port}"][o.plugin.severity] = 1


    def export_handler(self, outputs: list[Output], outfile: str):
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