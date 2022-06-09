import os
import re
import sys
import yaml
import logging
from functools import lru_cache

from lib.connection import *
from lib.exceptions import *
from lib.plugin_parser import Plugin 

# Configure logger
logging.basicConfig(format='[STARESC]:[%(asctime)s]:[%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

SUPPORTED_SCHEMAS = [ 'ssh', 'tnt', 'sshss']

class Staresc():

    connection: Connection
    distro: str
    binpath: list

    def __init__(self, connection_string: str) -> None:

        # Check if connection schema is valid
        if not Connection.is_connection_string(connection_string):
            msg = f"invalid connection string: {connection_string}"
            raise StarescConnectionStringError(msg)

        scheme = Connection.get_scheme(connection_string)
        MAP_CONNECTION = {
            "ssh"    : SSHConnection,
            "telnet" : TNTConnection,
            "sshss"  : SSHSSConnection
        }
        try:
            self.connection = MAP_CONNECTION[scheme](connection_string)

        except KeyError:
            msg = f"scheme is not valid: allowed schemes are {SUPPORTED_SCHEMAS}"
            raise StarescConnectionStringError(msg)            


    def prepare(self) -> None:
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


    def elevate(self) -> bool:
        return self.connection.elevate()


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


    def do_check(self, pluginfile: str, to_parse: bool = True) -> dict:        
        # load plugin from directory
        basedir = os.path.dirname(pluginfile)
        if basedir not in sys.path:
            sys.path.append(basedir)

        # load plugin file into object
        with open(pluginfile, "r") as f: 
            plugin_content = yaml.load(f.read(), Loader=yaml.Loader)
            plugin = Plugin(plugin_content)

        # check distro matcher
        if not re.findall(plugin.get_distribution_matcher(), self.osinfo):
            return None

        ret_val: dict            = {}
        # results of the commands
        ret_val['results']       = []
        # results parsed by the parsers
        ret_val['parse_results'] = []

        # assign plugin name/id
        ret_val['plugin'] = os.path.basename(pluginfile)

        # Run all commands and save the results
        test_index = 0
        for test in plugin.get_tests():
            cmd = test.get_command()
            # Try to use absolute paths for the command
            bin  = cmd.split(' ')[0]
            args = ' '.join(cmd.split(' ')[1:])
            cmd  = f"{self.__which(bin)} {args}" 
            try:
                stdin, stdout, stderr = self.connection.run(cmd)

            except StarescCommandError as e:
                logger.warning(e)
                stdin, stdout, stderr 
                ret_val['results'].append( { 'stdin'  : cmd, 'stdout' : '', 'stderr' : '' } )
                ret_val['parsed'] = True
                ret_val['parse_results'].append((False, {"stdout" : "", "stderr" : "", "timeout" : True}))
                test_index += 1
                continue

            # command output to parse
            test_result =  {                
                'stdin'  : stdin,
                'stdout' : stdout,
                'stderr' : stderr
            }
            ret_val['results'].append(test_result)

            if not to_parse:
                ret_val['parsed'] = False
                ret_val['parse_results'].append('')
            else:
                parsed_result = plugin.get_tests()[test_index].parse({
                    "stdout": test_result["stdout"],
                    "stderr": test_result["stderr"]
                }) 
                ret_val['parse_results'].append(parsed_result)
                ret_val['parsed'] = True
            test_index += 1

        # delete plugin obj
        del plugin
        return ret_val


    def do_offline_parsing(self, pluginfile:str, check_results: dict) -> dict:          #TODO adapt this to plugin objects
        basedir = os.path.dirname(pluginfile)
        if basedir not in sys.path:
            sys.path.append(basedir)

        # Load plugin as module
        plugin_basename = os.path.basename(pluginfile)
        plugin_module = os.path.splitext(plugin_basename)[0]
        plugin = __import__(plugin_module)

        if not check_results['results']:
            return { 'parse_results' : "Unable to find results, likely because the checks didn't match the OS" }

        output_list = []
        for output in check_results['results']:
            output_list.append(output['stdout'])
        check_results['parse_results'] = plugin.parse(output_list)
        check_results['parsed'] = True

        del plugin
        return check_results

