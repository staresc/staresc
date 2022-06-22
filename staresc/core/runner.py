import os, concurrent.futures

import yaml

from staresc.log import StarescLogger
from staresc.core import Staresc
from staresc.exporter import StarescExporter
from staresc.plugin_parser import Plugin


class StarescRunner:
    """StarescRunner is a factory for Staresc objects
    
    This class is responsible for parsing connection strings
    """

    targets: list[str]
    logger:  StarescLogger

    def __init__(self, logger: StarescLogger) -> None:
        self.logger  = logger


    def scan(self, connection_string: str, plugins: list[Plugin]) -> None:
        
        try:
            staresc = Staresc(connection_string)
            staresc.prepare()

        except Exception as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            return

        # For future reference
        # elevate = staresc.elevate()
        
        for plugin in plugins:
            self.logger.debug(f"Scanning {connection_string} with plugin {plugin.id}")
            to_append = None
            try:
                to_append = staresc.do_check(plugin)

            except Exception as e:
                self.logger.error(f"{type(e).__name__}: {e}")

            if to_append:
                StarescExporter.import_output(to_append)


    def run(self, targets: list[str], plugins: list[Plugin]):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                futures.append(executor.submit(StarescRunner.scan, self, target, plugins))
                self.logger.debug(f"Started scan on target {target}")

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan on target {target}")

        StarescExporter.export()


    @staticmethod
    def parse_plugins(plugins_dir: str = None) -> list[Plugin]:
        plugins = []

        if not plugins_dir.startswith('/'):
            plugins_dir = os.path.join(os.getcwd(), plugins_dir)

        for plugin_filename in os.listdir(plugins_dir):
            if plugin_filename.endswith('.yaml'):
                plugin_filename_long = os.path.join(plugins_dir, plugin_filename)
                f = open(plugin_filename_long, "r")
                plugin_content = yaml.load(f.read(), Loader=yaml.Loader)
                f.close()
                tmp_plugin = Plugin(plugin_content)
                plugins.append(tmp_plugin)

        return plugins