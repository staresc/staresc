from queue import Queue
from lib.output import *

class Exporter():

    runs_results: Queue[Output]

    def __init__(self):
        self.runs_results = Queue()


    def add_output(self, output) -> None:
        self.runs_results.put(output)


    def export(self, filename: str) -> None:
        pass