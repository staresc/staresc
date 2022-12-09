import argparse
import os

import yaml

from staresc.exporter import Exporter, CSVHandler, XLSXHandler, JSONHandler, Handler
from staresc.exceptions import ParseError
from staresc.log import Logger
from staresc.plugin_parser.plugin import Plugin
from staresc import DEFAULT_PLUGIN_DIR

description  = """
Make SSH/TELNET PTs great again!
The connection string format is the following: schema://user:auth@host:port
auth can be either a password or a path to ssh privkey, specified as \\\\path\\\\to\\\\privkey
"""

def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='staresc', description=description, epilog=' ', formatter_class=argparse.RawTextHelpFormatter )    
    parser.add_argument('-d',  '--debug',    action='store_true', default=False, help='increase output verbosity to debug mode')
    parser.add_argument('-nb', '--nobanner', action='store_true', default=False, help='hide banner')
    parser.add_argument('-t', '--timeout', action='store', default=None, help='set timeout for connections')

    maingroup = parser.add_mutually_exclusive_group(required=True)
    maingroup.add_argument('-f',  '--file',       metavar='F', action='store', default='', help='input file containing 1 connection string per line' )
    maingroup.add_argument('-cs', '--connection', metavar='CS', action='store', default='', help='connection string' )
    maingroup.add_argument('--test', action='store_true', default=False, help='test staresc integrity')
    maingroup.add_argument('-v',  '--version',  action='store_true', default=False, help='print version and exit')

    mode_subparser = parser.add_subparsers(dest='mode', help='Staresc execution mode')

    scanmode = mode_subparser.add_parser(name='scan', help='Scan mode: execute plugins on target')
    scanmode.add_argument('-p', '--plugins', metavar='dir', action='store', default=DEFAULT_PLUGIN_DIR, help='path to plugins directory')

    rawmode = mode_subparser.add_parser(name='raw', help='Raw mode: execute custom commands', formatter_class=argparse.RawTextHelpFormatter)
    rawmode.add_argument('--command', metavar='command',  action='append', default=[], help='command to run on the targers')
    rawmode.add_argument('--push',    metavar='filename', action='append', default=[], help='push files to the target')
    rawmode.add_argument('--pull',    metavar='filename', action='append', default=[], help='pull files from the target')
    rawmode.add_argument('--exec',    metavar='filename', action='store',  default='', help='equivalent to "--push file --command ./file"')
    rawmode.add_argument('--no-tmp',  default=False, action='store_true', help='skip creating temp folder and cd-ing into it')
    rawmode.add_argument('--show',    default=False, action='store_true', help='show commands output in the terminal')
    rawmode.add_argument('--notty',   default=False, action='store_true', help='SSH only: don\'t request a TTY')
    rawmode.add_argument('--no-sftp', default=False, action='store_true', help='disable the SFTP subsystem; implies --no-tmp')

    checkmode = mode_subparser.add_parser(name='check', help='Check mode: check reachability')
    checkmode.add_argument('--ping', default=False, action='store_true', help='ping hosts if they do not respond at ssh port')

    outputs = parser.add_argument_group()
    outputs.add_argument('-o',  '--output', metavar='pattern', action='store', default='', help='export results in specified format')
    outputs.add_argument('-of', '--output-format', metavar='FMT', action='append', default=[], help='format of results')    
    args = parser.parse_args()
    
    # Default timeout values
    if args.timeout:
        args.timeout = float(args.timeout)
    elif args.mode == 'raw':
        args.timeout = float(0)
    else:
        args.timeout = float(2)
    return args

def get_targets(fname:str, single_target:str ) -> list[str]:
    """get_targets parses file or arg to get a list of targets
    
    raises:
        -- ParseError if targets are not parsed
    """
    logger = Logger()
    if fname != "":
        with open(fname, 'r') as f:
            logger.debug(f"Loading file: {fname}")
            return [t.strip() for t in f.readlines()]
    
    elif single_target != "":
        logger.debug(f"Loading connection: {single_target}")
        return [ str(single_target) ]
    
    else:
        raise ParseError("no valid target provided")


def __parsepath(p:str) -> str:
    logger = Logger()
    full_path = os.path.join(os.getcwd(), p)

    # Create directory if doesn't exist
    if not os.path.isdir(os.path.dirname(full_path)):
        logger.debug(f"Created directory: {full_path}")
        os.makedirs(full_path)

    # Choose file name "results" if patter does not provide it
    if not os.path.basename(full_path):
        logger.debug(f"Choosing default filename: results")
        full_path = os.path.join(full_path, "results")

    return full_path


def handle_output(fname:str, formats:list[str]) -> None:
    if fname == "":
        return

    if len(formats) == 0:
        formats.append('csv')

    full_path = __parsepath(fname)
    for fmt in formats:
        if fmt == 'csv':
            Exporter.register_handler(CSVHandler(os.path.join(full_path + ".csv")))
        elif fmt == 'xlsx':
            Exporter.register_handler(XLSXHandler(os.path.join(full_path + ".xlsx")))
        elif fmt == 'json':
            Exporter.register_handler(JSONHandler(os.path.join(full_path + ".json")))
        else:
            raise ParseError(f"Unknown output format {fmt}")


def parse_plugins(plugins_dir: str = "") -> list[Plugin]:
    """Static method to parse plugins"""
    if plugins_dir == "":
        return []
    elif not plugins_dir.startswith('/'):
        plugins_dir = os.path.join(os.getcwd(), plugins_dir)

    plugins = []
    for plugin_filename in os.listdir(plugins_dir):
        if plugin_filename.endswith('.yaml'):
            plugin_filename_long = os.path.join(plugins_dir, plugin_filename)
            with open(plugin_filename_long, "r") as f: 
                plugin_content = yaml.load(f.read(), Loader=yaml.Loader)
            tmp_plugin = Plugin(plugin_content)
            plugins.append(tmp_plugin)
    return plugins