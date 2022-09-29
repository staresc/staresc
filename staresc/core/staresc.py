import re
from functools import lru_cache

from staresc.connection import Connection, SCHEME_TO_CONNECTION
from staresc.plugin_parser import Plugin
from staresc.output import Output
from staresc.exceptions import StarescCommandError, StarescConnectionStringError

class Staresc():
    """Main component
    
    This is the main component, it is responsible for running scans on a single 
    target returning an output
    """

    connection: Connection
    distro: str
    binpath: list

    def __init__(self, connection_string: str) -> None:
        """Init the component

        Attributes:
            connection_string -- The connection string

        Raises:
            StarescConnectionStringError -- when connection string is not valid
        """

        # Check if connection schema is valid
        if not Connection.is_connection_string(connection_string):
            msg = f"invalid connection string: {connection_string}"
            raise StarescConnectionStringError(msg)

        scheme = Connection.get_scheme(connection_string)
        
        try:
            self.connection = SCHEME_TO_CONNECTION[scheme](connection_string)

        except KeyError:
            msg = f"scheme is not valid: allowed schemes are {SCHEME_TO_CONNECTION.keys()}"
            raise StarescConnectionStringError(msg)            

    def prepare(self) -> None:
        """Prepare the execution 
        
        It connects to the client, gets os info and caches all the binaries 
        in the system PATH.
        """
        self.connection.connect()
        self.__populate_binpath()
        self.__get_os_info()


    def __populate_binpath(self):
        cmd = f"""for p in $( echo $PATH | tr ':' ' ' ); do find "$p" -type f; done"""
        stdin, stdout, stderr = self.connection.run(cmd)

        if not stdin or not stdout or stderr:
            self.binpath = []
        else:
            self.binpath = stdout.split("\r\n")
        

    @lru_cache(maxsize=100)
    def __which(self, s) -> str:
        for b in self.binpath:
            if b.lower().endswith(f'/{s}'):
                return b
        return s

    def __get_os_info(self) -> None:
        commands = [
                "uname -a",
                "lsb_release -d",
                "cat /etc/*release*",
                "cat /proc/version"
            ]
        results = []
        for cmd in commands:
            _, s, _ = self.connection.run(cmd)
            results.append(s)
        
        self.osinfo = ' '.join(results)

    @lru_cache
    def _get_absolute_cmd(self, cmd) -> str:
        # Try to use absolute paths for the command
        bin  = cmd.split(' ')[0]
        args = ' '.join(cmd.split(' ')[1:])
        cmd  = f"{self.__which(bin)} {args}" 
        return cmd

    def do_check(self, plugin: Plugin) -> Output:
        """Performs the actual chercks"""
        if not re.findall(plugin.get_distribution_matcher(), self.osinfo):      #check distro matcher
            return None

        plugin_output = Output(target=self.connection, plugin=plugin)
        # Run all commands and return the output

        if plugin.match_condition == 'and':
            plugin_output.set_vuln_found(True)
        elif plugin.match_condition == 'or':
            plugin_output.set_vuln_found(False)

        for idx, test in enumerate(plugin.get_tests()):
            cmd = self.__get_absolute_cmd(test.get_command())
            try:
                stdin, stdout, stderr = self.connection.run(cmd)
                plugin_output.add_test_result(stdin=stdin, stdout=stdout, stderr=stderr)
                positive_test, parsed_result = plugin.get_tests()[idx].parse({
                    "stdout": stdout or '',
                    "stderr": stderr or ''
                })      # parse test results

                plugin_output.add_test_success(positive_test)
                plugin_output.add_test_result_parsed(stdout=parsed_result["stdout"], stderr=parsed_result["stderr"] )
                plugin_output.set_parsed(True)
                if positive_test and plugin.match_condition == 'or':
                    plugin_output.set_vuln_found(True)
                    break
                elif not positive_test and plugin.match_condition == 'and':
                    plugin_output.set_vuln_found(False)
                    break

            except StarescCommandError as e:
                plugin_output.add_timeout_result(stdin=cmd)
        return plugin_output