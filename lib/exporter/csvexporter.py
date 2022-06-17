import csv
import os
from .exporter import Exporter
from lib.output import *

class CSVExporter(Exporter):

    COLUMNS = ["Host IP", "Port", "Scheme","Vulnerable", "Any timeout", "CVSS score", "Vulnerability name", "Description", "Technical details", "Remediation", "CVE","CVSS vector", "Complete log"]

    def export(self) -> None:
        MATCHER_TO_FUNC = {
            "Host IP" : self.__parse_host_ip,
            "Port" : self.__parse_port,
            "Scheme" : self.__parse_scheme,
            "Vulnerable": self.__parse_vuln_found,
            "Any timeout": self.__parse_any_timeout,
            "CVSS score"  : self.__parse_cvss_score,
            "Vulnerability name"  : self.__parse_vulnerability_name,
            "Description"  : self.__parse_description,
            "Technical details"  : self.__parse_technical_details,
            "Remediation"  : self.__parse_remediation,
            "CVSS vector"  : self.__parse_cvss_vector,
            "Complete log"  : self.__parse_complete_log,
        }

        out_rows = [self.COLUMNS]
        i = 0
        for output in self.runs_results.queue:      # it works only in non multithread environment
            tmp_row = []
            for col in self.COLUMNS:
                try:
                    tmp_row.append(MATCHER_TO_FUNC[col](output))
                except AttributeError as e:
                    tmp_row.append('-')
            out_rows.append(tmp_row)

        f_out = open(self.filename, 'w')
        csv_writer = csv.writer(f_out, delimiter=';')
        csv_writer.writerows(out_rows)
        f_out.close()


    @staticmethod
    def format_filename(filename: str, default_name: str = '') -> str:
        name, extension = os.path.splitext(filename)
        # Use default_name if filename not specified
        if filename == '':
            filename = default_name
        # Add extension if not specified
        if extension == '':
            extension = '.csv'
        # Use absolute path
        if not name.startswith('/'):
            name = os.path.join(os.getcwd(), name)
        return os.path.abspath(name + extension)

    @staticmethod
    def __parse_host_ip(output: Output) -> str:
        return Connection.get_hostname(output.target.connection)

    @staticmethod
    def __parse_port(output: Output) -> int:
        return Connection.get_port(output.target.connection)


    @staticmethod
    def __parse_scheme(output: Output) -> str:
        return Connection.get_scheme(output.target.connection)


    @staticmethod
    def __parse_cvss_score(output: Output) -> float:
        return getattr(output.plugin, 'cvss')


    @staticmethod
    def __parse_vulnerability_name(output: Output) -> str:
        return getattr(output.plugin, 'name')


    @staticmethod
    def __parse_description(output: Output) -> str:
        return getattr(output.plugin, 'description')


    @staticmethod
    def __parse_remediation(output: Output) -> str:
        return getattr(output.plugin, 'remediation')


    @staticmethod
    def __parse_cvss_vector(output: Output) -> str:
        return getattr(output.plugin, 'cvss_vector')


    @staticmethod
    def __parse_technical_details(output: Output) -> str:
        tech_details = ""
        for i in range(len(output.test_results)):
            tech_details += f"cmd: {output.test_results[i]['stdin']}\n"
            tech_details += f"stdout: {output.test_results_parsed[i]['stdout']}\n"
            tech_details += f"stderr: {output.test_results_parsed[i]['stderr']}\n"
            tech_details += "\n\n\n"
        return tech_details


    @staticmethod
    def __parse_vuln_found(output: Output) -> bool:
        return output.is_vuln_found()


    @staticmethod
    def __parse_any_timeout(output: Output) -> bool:
        return any(output.get_timeouts())


    @staticmethod
    def __parse_complete_log(output: Output) -> str:
        ret = []
        for test_res in output.test_results:
            ret.append({
                "stdin": test_res["stdin"],
                "stdout": test_res["stdout"],
                "stderr": test_res["stderr"],
            })
        return str(ret)




