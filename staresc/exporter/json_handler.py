import json

from staresc.output import Output
from staresc.exporter.handler import Handler, COLUMNS_TO_FUNC


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