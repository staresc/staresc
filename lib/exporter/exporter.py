from queue import Queue
from lib.output import *

class Exporter():

    filename: str
    runs_results: Queue[Output] = Queue()

    def __init__(self, filename: str = ''):
        self.runs_results = Queue()
        self.filename = filename


    def add_output(self, output: Output) -> None:
        self.runs_results.put(output)


    def export(self) -> None:
        pass

    @staticmethod
    def format_filename(filename: str, default_name: str = ''):
        pass