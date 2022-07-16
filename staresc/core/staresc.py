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

        Also connects the client to the server

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
            self.connection: Connection = SCHEME_TO_CONNECTION[scheme](connection_string)
            self.connection.connect()

        except KeyError:
            msg = f"scheme is not valid: allowed schemes are {SCHEME_TO_CONNECTION.keys()}"
            raise StarescConnectionStringError(msg)


    def elevate(self) -> bool:
        """Elevate the connection privileges using the underlying connection"""
        return self.connection.elevate()


    def do_check(self, plugin: Plugin) -> Output:
        """Performs the actual chercks"""
        #if not re.findall(plugin.get_distribution_matcher(), self.osinfo):
        #    return None

        plugin_output = Output(target=self.connection, plugin=plugin)
        # Run all commands and return the output

        if plugin.match_condition == 'and':
            plugin_output.set_vuln_found(True)
        elif plugin.match_condition == 'or':
            plugin_output.set_vuln_found(False)

        # index of the text being run
        idx = 0
        for test in plugin.get_tests():
            try:
                stdin, stdout, stderr = self.connection.run(test.get_command())
                plugin_output.add_test_result(stdin=stdin, stdout=stdout, stderr=stderr)
                positive_test, parsed_result = plugin.get_tests()[idx].parse({
                    "stdout": stdout or '',
                    "stderr": stderr or ''
                })

                plugin_output.add_test_success(positive_test)
                plugin_output.add_test_result_parsed(stdout=parsed_result["stdout"], stderr=parsed_result["stderr"] )
                plugin_output.set_parsed(True)
                if positive_test and plugin.match_condition == 'or':
                    plugin_output.set_vuln_found(True)
                    break
                elif not positive_test and plugin.match_condition == 'and':
                    plugin_output.set_vuln_found(False)
                    break

            except (StarescCommandError, TimeoutError):
                plugin_output.add_timeout_result(stdin=test.get_command())

            idx += 1

        return plugin_output

