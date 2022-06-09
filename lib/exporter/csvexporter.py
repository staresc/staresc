import csv

from .exporter import Exporter
from lib.output import *

class CSVExporter(Exporter):

    COLUMNS = ["Host IP", "Vulnerable", "Any timeout", "CVSS score", "Vulnerability name", "Description", "Technical details", "Remediation", "CVSS vector"]
    #TODO should we need CVE field?

    def export(self, filename: str) -> None:
        MATCHER_TO_FUNC = {
            "Host IP" : self.__parse_host_ip,
            "Vulnerable": self.__parse_vuln_found,
            "Any timeout": self.__parse_any_timeout,
            "CVSS score"  : self.__parse_cvss_score,
            "Vulnerability name"  : self.__parse_vulnerability_name,
            "Description"  : self.__parse_description,
            "Technical details"  : self.__parse_technical_details,
            "Remediation"  : self.__parse_remediation,
            "CVSS vector"  : self.__parse_cvss_vector,
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

        f_out = open(filename, 'w')
        csv_writer = csv.writer(f_out, delimiter=';')
        csv_writer.writerows(out_rows)
        f_out.close()


    @staticmethod
    def __parse_host_ip(output: Output) -> str:
        return Connection.get_hostname(output.target.connection)


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
        tech_details = []
        for t_res in output.test_results:
            tech_details.append({
                "stdin": t_res["stdin"],
                "stdout": t_res["stdout"],
                "stderr": t_res["stderr"]
            })
        #TODO understand how to pick a valid and minimal poc, TODO check a way to extract info without directly read object field (use some interface method)
        return str(tech_details)


    @staticmethod
    def __parse_vuln_found(output: Output) -> bool:
        return output.is_vuln_found()


    @staticmethod
    def __parse_any_timeout(output: Output) -> bool:
        return any(output.get_timeouts())




