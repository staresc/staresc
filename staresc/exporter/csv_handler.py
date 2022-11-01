import csv

from staresc.output import Output
from staresc.exporter.handler import Handler, COLUMNS_TO_FUNC


class CSVHandler(Handler):

    def import_handler(self, o: Output):
        pass

    def export_handler(self, outputs: list[Output], outfile: str):
        out_rows:list[list[str]] = []

        # append headers
        out_rows.append([ col for col in COLUMNS_TO_FUNC.keys() ])
        # append everything else
        for output in outputs:
            out_rows.append([ COLUMNS_TO_FUNC[col](output) for col in COLUMNS_TO_FUNC.keys() ])

        with open(outfile, 'w') as f:
            csv_writer = csv.writer(f, delimiter=';')
            csv_writer.writerows(out_rows)