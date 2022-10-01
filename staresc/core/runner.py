import concurrent.futures

from staresc.log import StarescLogger
from staresc.core import Scanner
from staresc.exporter import StarescExporter
from staresc.plugin_parser import Plugin


class StarescRunner:
    """StarescRunner is a factory for Staresc objects
    
    This class is responsible for parsing connection strings, parse plugins,
    istance Staresc objects and run concurrent scans on targets (1 thread per 
    target). Finally, it calls the exporters associated with the StarescExporter
    class to produce the requested output. 
    """

    targets: list[str]
    logger:  StarescLogger

    def __init__(self, logger: StarescLogger) -> None:
        self.logger  = logger


    def __scan(self, connection_string: str, plugins: list[Plugin]) -> None:
        """Launch the scan

        Istance Staresc with connection string, prepare and run plugins commands
        on targets.
        """
        
        try:
            staresc = Scanner(connection_string)
            staresc.prepare()

        except Exception as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            return
        
        for plugin in plugins:
            self.logger.debug(f"Scanning {connection_string} with plugin {plugin.id}")
            try:
                to_append = staresc.do_check(plugin)
                StarescExporter.import_output(to_append)
            except Exception as e:
                self.logger.error(f"{type(e).__name__}: {e}")


    def scan(self, targets: list[str], plugins: list[Plugin]) -> int:
        """Actual runner for the whole program using 5 concurrent threads"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                futures.append(executor.submit(StarescRunner.__scan, self, target, plugins))
                self.logger.debug(f"Started scan on target {target}")

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan on target {target}")
        return 0
    