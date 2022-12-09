import os
from datetime import datetime

from staresc.output import Output
from staresc.exporter.handler import Handler


class RawHandler(Handler):

    def import_handler(self, o: Output):
        pass

    def export_handler(self, outputs: list[Output], outfile: str):       
        for output in outputs:
            output_dir = outfile
            
            if not output_dir:
                output_dir = f"staresc_{output.target.hostname}"
            
            os.makedirs(output_dir, exist_ok=True)

            base_filename = f"{output.target.hostname}_{datetime.now().strftime('%m-%d_%H.%M.%S')}"
            outstream = "\n\n".join(["$ " + r['stdin'] + "\n" + r['stdout'] for r in output.test_results]) + "\n"
            errstream = "\n\n".join([r['stderr'] for r in output.test_results]) + "\n"

            with open(os.path.join(output_dir, base_filename + '.out.log'), 'a+') as f:
                f.write(outstream)

            if len(errstream.strip()) > 0:
                with open(os.path.join(output_dir, base_filename + '.err.log'), 'a+') as f:
                    f.write(errstream)