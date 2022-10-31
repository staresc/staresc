import xlsxwriter

from staresc.output import Output
from staresc.exporter.handler import Handler, COLUMNS_TO_FUNC


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