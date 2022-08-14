import os, concurrent.futures

import yaml
from staresc.exceptions import StarescAuthenticationError, StarescCommandError, StarescPluginError

from staresc.log import StarescLogger
from staresc.core import Staresc
from staresc.exporter import StarescExporter
from staresc.plugin_parser import Plugin
from staresc.connection import Connection


class StarescRunner:
    """StarescRunner is a factory for Staresc objects
    
    This class is responsible for parsing connection strings, parse plugins,
    istance Staresc objects and run concurrent scans on targets (1 thread per 
    target). Finally, it calls the exporters associated with the StarescExporter
    class to produce the requested output. 
    """

    targets: list[str]
    logger:  StarescLogger
    mode: str

    def __init__(self, logger: StarescLogger) -> None:
        self.logger  = logger
        self.mode = "regular"


    @staticmethod
    def __hostport(s: str) -> str:
        """Host:Port from connection string"""
        host = Connection.get_hostname(s)
        port = Connection.get_port(s)
        return f"{host}:{port}"


    def scan(self, connection_string: str, plugins: list[Plugin]) -> None:
        """Launch the scan

        Istance Staresc with connection string, prepare and run plugins commands
        on targets.
        """
        try:
            staresc = Staresc(connection_string)

        except Exception as e:
            self.logger.error(f"{type(e).__name__}: {e}", self.__hostport(connection_string))
            return

        # For future reference
        # elevate = staresc.elevate()

        for plugin in plugins:
            self.logger.debug(f"Using plugin {plugin.id}", self.__hostport(connection_string))
            to_append = None
            try:
                to_append = staresc.do_check(plugin)

            except (StarescAuthenticationError, StarescCommandError)  as e:
                self.logger.error(f"{type(e).__name__}: {e}")
            
            except Exception as e:
                import traceback
                traceback.print_exc(e)
            try:
                if to_append:
                    StarescExporter.import_output(to_append)
            except Exception as e:
                self.logger.error(f"{type(e).__name__}: {e}", self.__hostport(connection_string))
                return


    def run(self, targets: list[str], plugins: list[Plugin]):
        """Actual runner for the whole program using 5 concurrent threads"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                futures.append(executor.submit(StarescRunner.scan, self, target, plugins))
                self.logger.debug(f"Started scan", self.__hostport(target))

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan", self.__hostport(target))

        StarescExporter.export()


    def test_plugins(self, plugins: list[Plugin]):
        self.logger.debug("Started plugins test")
        staresc = Staresc("test_plugins", mode="test_plugins")
        for plugin in plugins:
            self.logger.debug(f"testing plugin {plugin.id}")
            try:
                staresc.test_plugin(plugin)
            except Exception as e:
                import traceback
                traceback.print_exc(e)
            self.logger.debug(f"tested plugin {plugin.id}")
        self.logger.debug("Finished plugins test")


    def parse_plugins(self, plugins_dir: str) -> list[Plugin]:
        """Static method to parse plugins"""
        plugins = []

        if not plugins_dir.startswith('/'):
            plugins_dir = os.path.join(os.getcwd(), plugins_dir)

        for plugin_filename in os.listdir(plugins_dir):
            if plugin_filename.endswith('.yaml'):
                plugin_filename_long = os.path.join(plugins_dir, plugin_filename)
                f = open(plugin_filename_long, "r")
                plugin_content = yaml.load(f.read(), Loader=yaml.Loader)
                f.close()
                tmp_plugin = Plugin(plugin_content, self.get_mode(), self.logger)
                plugins.append(tmp_plugin)

        return plugins

    def set_mode(self, new_mode: str) -> None:
        self.mode = new_mode

    def get_mode(self) -> str:
        return self.mode
