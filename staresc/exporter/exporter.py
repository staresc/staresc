import os
from queue import Queue

from staresc.exporter.handlers import StarescHandler
from staresc.output import Output

class StarescExporter():

    runs_results: Queue[Output] = Queue()
    handlers: list[StarescHandler] = []

    def __init__(self, dir: str = './export/'):
        self.output_directory = dir
        if not os.path.exists(dir):
            os.makedirs(dir)

    @classmethod
    def register_handler(cls, handler: StarescHandler):
        cls.handlers.append(handler)

    @classmethod
    def import_output(cls, output: Output) -> None:
        cls.runs_results.put(output)
        for h in cls.handlers:
            h.import_handler(output)

    @classmethod
    def export(cls) -> None:
        outputs: list[Output] = []
        for o in list(cls.runs_results.queue):
            outputs.append(o)

        for h in cls.handlers:
            h.export_handler(outputs, h.out)

