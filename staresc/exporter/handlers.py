import csv

import xlsxwriter
import json
from tabulate import tabulate

from staresc.log import Logger
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

COLUMNS_TO_FUNC = {
    "Host IP"            : lambda x: (Connection)(x.target.connection).hostname,
    "Port"               : lambda x: (Connection)(x.target.connection).port,
    "Scheme"             : lambda x: (Connection)(x.target.connection).scheme,
    "Vulnerable"         : lambda x : x.is_vuln_found(),
    "Any timeout"        : lambda x : any(x.get_timeouts()),
    "CVSS score"         : lambda x : getattr(x.plugin, 'cvss', 0.0),
    "Vulnerability name" : lambda x : getattr(x.plugin, 'name'),
    "Description"        : lambda x : getattr(x.plugin, 'description'),
    "Technical details"  : technical_details,
    "Remediation"        : lambda x : getattr(x.plugin, 'remediation', ''),
    "CVE"                : lambda x : getattr(x.plugin, 'CVE', ''),
    "CVSS vector"        : lambda x : getattr(x.plugin, 'cvss_vector', ''),
    "Complete log"       : complete_log,
}


class CSVHandler(Handler):

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


class StdoutHandler(Handler):

    logger: Logger = Logger()
    scan_summary: dict

    def __init__(self, out: str) -> None:
        self.scan_summary = {}
        super().__init__(out)

    def import_handler(self, o: Output):
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


class XLSXHandler(Handler):

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


class JSONHandler(Handler):

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


class RawHandler(Handler):

    def import_handler(self, o: Output):
        pass

    def export_handler(self, outputs: list[Output], outfile: str):
        from datetime import datetime
        import os
        
        for output in outputs:
            output_dir = outfile
            if not output_dir:
                output_dir = f"staresc_{output.target.hostname}"
            os.makedirs(output_dir, exist_ok=True)

            base_filename = f"{output.target.hostname}_{datetime.now().strftime('%m-%d_%H.%M.%S')}"

            outstream = "\n\n".join(["$ " + r['stdin'] + "\n" + r['stdout'] for r in output.test_results])
            errstream = "\n\n".join([r['stderr'] for r in output.test_results])
            with open(os.path.join(output_dir, base_filename + '.out.log'), 'a+') as f:
                f.write(outstream)
            if len(errstream.strip()) > 0:
                with open(os.path.join(output_dir, base_filename + '.err.log'), 'a+') as f:
                    f.write(errstream)