from lib.exporter.exporter import Exporter
from lib.output import Output
from lib.log import StarescLogger


class StdoutExporter(Exporter):

    logger: StarescLogger

    def __init__(self, filename: str = ''):
        self.logger = StarescLogger()
        super().__init__(filename)


    def add_output(self, output: Output) -> None:
        self.logger.print_if_vuln(output)

