import os
from queue import Queue

from staresc.exporter.handlers import StarescHandler
from staresc.output import Output

class StarescExporter():
    """Handle Staresc output

    This class is never istanciated, has class methods and an output queue
    which is handled by a list of handlers objects both when an output is added 
    to the queue and when an output is taken from the queue
    """

    runs_results: Queue[Output] = Queue()
    handlers: list[StarescHandler] = []

    def __init__(self, dir: str = './export/'):
        self.output_directory = dir
        if not os.path.exists(dir):
            os.makedirs(dir)

    @classmethod
    def register_handler(cls, handler: StarescHandler):
        """Called to add an handler to the class"""
        cls.handlers.append(handler)

    @classmethod
    def import_output(cls, output: Output) -> None:
        """Called when an output has to be added to the queue"""
        cls.runs_results.put(output)
        for h in cls.handlers:
            h.import_handler(output)

    @classmethod
    def export(cls) -> None:
        """Called at the end of execution to produce results"""
        outputs: list[Output] = []
        for o in list(cls.runs_results.queue):
            outputs.append(o)

        for h in cls.handlers:
            h.export_handler(outputs, h.out)

