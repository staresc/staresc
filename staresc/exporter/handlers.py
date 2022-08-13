import csv

import xlsxwriter
import json
from tabulate import tabulate

from staresc.log import StarescLogger
from staresc.output import Output
from staresc.connection import Connection

class StarescHandler:
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

    @staticmethod
    def technical_details(o: Output):
            tech_details = ""
            for i in range(len(o.test_results)):
                tech_details += f"cmd: {o.test_results[i]['stdin']}\n"
                tech_details += f"stdout: {o.test_results_parsed[i]['stdout']}\n"
                tech_details += f"stderr: {o.test_results_parsed[i]['stderr']}\n"
                tech_details += "\n\n\n"
            return tech_details

    @staticmethod
    def complete_log(o: Output):
        ret = []
        for test_res in o.test_results:
            ret.append({
                "stdin": test_res["stdin"],
                "stdout": test_res["stdout"],
                "stderr": test_res["stderr"],
            })
        return str(ret)


COLUMNS_TO_FUNC = {
    "Host IP"            : lambda x: Connection.get_hostname(x.target.connection),
    "Port"               : lambda x: Connection.get_port(x.target.connection),
    "Scheme"             : lambda x: Connection.get_scheme(x.target.connection),
    "Vulnerable"         : lambda x : x.is_vuln_found(),
    "Any timeout"        : lambda x : any(x.get_timeouts()),
    "CVSS score"         : lambda x : getattr(x.plugin, 'cvss', 0.0),
    "Vulnerability name" : lambda x : getattr(x.plugin, 'name'),
    "Description"        : lambda x : getattr(x.plugin, 'description'),
    "Technical details"  : StarescHandler.technical_details,
    "Remediation"        : lambda x : getattr(x.plugin, 'remediation', ''),
    "CVE"                : lambda x : getattr(x.plugin, 'CVE', ''),
    "CVSS vector"        : lambda x : getattr(x.plugin, 'cvss_vector', ''),
    "Complete log"       : StarescHandler.complete_log,
}


class StarescCSVHandler(StarescHandler):

    def import_handler(self, o: Output):
        pass

    def export_handler(self, outputs: list[Output], outfile: str):
        out_rows = [COLUMNS_TO_FUNC.keys()]
        
        # it works only in non multithread environment
        for output in outputs:
            tmp_row = []
            for col in COLUMNS_TO_FUNC.keys():
                tmp_row.append(COLUMNS_TO_FUNC[col](output))
            out_rows.append(tmp_row)

        with open(outfile, 'w') as f:
            csv_writer = csv.writer(f, delimiter=';')
            csv_writer.writerows(out_rows)


class StarescStdoutHandler(StarescHandler):

    logger: StarescLogger = StarescLogger()
    scan_summary: dict

    def __init__(self, out: str) -> None:
        self.scan_summary = {}
        super().__init__(out)

    def import_handler(self, o: Output):
        if o.is_vuln_found():
            self.logger.print_vuln(host = Connection.get_hostname(o.target.connection), port = Connection.get_port(o.target.connection), severity = o.plugin.severity, plugin_name = o.plugin.name)
        self.logger.print_if_vuln(o)

        if o.is_vuln_found():
            host = o.target.get_hostname(o.target.connection)
            port = o.target.get_port(o.target.connection)

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


class StarescXLSXHandler(StarescHandler):

    def import_handler(self, o: Output):
        pass

    def export_handler(self, outputs: list[Output], outfile: str):
        out_rows = [list(COLUMNS_TO_FUNC.keys())]

        # it works only in non multithread environment
        for output in outputs:
            tmp_row = []
            for col in COLUMNS_TO_FUNC.keys():
                tmp_row.append(COLUMNS_TO_FUNC[col](output))
            out_rows.append(tmp_row)

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(outfile)
        worksheet = workbook.add_worksheet()

        # Write tmp_rows as a table to the worksheet, cell after cell.
        for row in range(len(out_rows)):
            for col in range(len(out_rows[row])):
                worksheet.write(row, col, out_rows[row][col])

        workbook.close()


class StarescJSONHandler(StarescHandler):

    def import_handler(self, o: Output):
        pass

    def export_handler(self, outputs: list[Output], outfile: str):
        out_dict = []

        # it works only in non multithread environment
        for output in outputs:
            tmp_row = {}
            for column_name, value_func in COLUMNS_TO_FUNC.items():
                tmp_row[column_name] = value_func(output)
            out_dict.append(tmp_row)

        with open(outfile, 'w') as f:
            json.dump(out_dict, f)
            f.close()
