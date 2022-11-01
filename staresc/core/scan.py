import concurrent.futures

from staresc.log import Logger
from staresc.plugin_parser import Plugin
from staresc.exporter import Exporter
from staresc.core.worker import ScanWorker


class Scanner:
    """Scanner is a factory for ScanWorkers objects
    
    This class is responsible for parsing connection strings, parse plugins,
    istance Staresc objects and run concurrent scans on targets (1 thread per 
    target). Finally, it calls the exporters associated with the StarescExporter
    class to produce the requested output. 
    """
    targets:list[str]
    timeout:float
    logger:Logger

    def __init__(self, timeout:float = 2.0) -> None:
        self.logger  = Logger()
        self.timeout = timeout


    def __scan(self, connection_string: str, plugins: list[Plugin]) -> None:
        """Launch the scan

        Istance Staresc with connection string, prepare and run plugins commands
        on targets.
        """
        try:
            worker = ScanWorker(connection_string)
            worker.prepare(timeout=self.timeout)

        except Exception as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            return
        
        for plugin in plugins:
            self.logger.debug(f"Scanning {connection_string} with plugin {plugin.id}")
            try:
                to_append = worker.do_check(plugin)
                if to_append:
                    Exporter.import_output(to_append)
            except Exception as e:
                self.logger.error(f"{type(e).__name__}: {e}")


    def scan(self, targets: list[str], plugins: list[Plugin]) -> int:
        """Actual runner for the whole program using 5 concurrent threads"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                futures.append(executor.submit(Scanner.__scan, self, target, plugins))
                self.logger.debug(f"Started scan on target {target}")

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan on target {target}")
        return 0