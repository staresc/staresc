#!/usr/bin/env python3

"""
staresc-ng is based on an internal tool developed by @brn1337 on GitLab.
This is my attempt to make the penetration tests over ssh great again :)

I'm @5amu, welcome!
"""

import argparse
import os

import yaml

from staresc.core import Runner, Checker, Raw, Tester
from staresc.exporter import Exporter, CSVHandler, StdoutHandler, XLSXHandler, JSONHandler, RawHandler
from staresc.log import Logger
from staresc.plugin_parser import Plugin
from staresc import VERSION

# Configure logger
logger = Logger()

##################################### CLI #######################################

description  = """
Make SSH/TELNET PTs great again!
The connection string format is the following: schema://user:auth@host:port
auth can be either a password or a path to ssh privkey, specified as \\\\path\\\\to\\\\privkey
"""

def cliparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='staresc', description=description, epilog=' ', formatter_class=argparse.RawTextHelpFormatter )    
    parser.add_argument('-d',  '--debug',    action='store_true', default=False, help='increase output verbosity to debug mode')
    parser.add_argument('-v',  '--version',  action='store_true', default=False, help='print version and exit')
    parser.add_argument('-nb', '--nobanner', action='store_true', default=False, help='hide banner')

    targets_or_test = parser.add_mutually_exclusive_group(required=True)
    targets_or_test.add_argument('-f',  '--file',       metavar='F', action='store', default='', help='input file containing 1 connection string per line' )
    targets_or_test.add_argument('-cs', '--connection', metavar='CS', action='store', default='', help='connection string' )
    targets_or_test.add_argument('--test', action='store_true', default=False, help='test staresc integrity')

    mode_subparser = parser.add_subparsers(dest='mode', help='Staresc execution mode')

    scanmode = mode_subparser.add_parser(name='scan', help='Scan mode: execute plugins on target')
    scanmode.add_argument('-p', '--plugins', metavar='dir', action='store', default='', help='path to plugins directory')

    rawmode = mode_subparser.add_parser(name='raw', help='Raw mode: execute custom commands', formatter_class=argparse.RawTextHelpFormatter)
    rawmode.add_argument('--command', metavar='command',  action='append', default=[], help='command to run on the targers')
    rawmode.add_argument('--push',    metavar='filename', action='append', default=[], help='push files to the target')
    rawmode.add_argument('--pull',    metavar='filename', action='append', default=[], help='pull files from the target')
    rawmode.add_argument('--exec',    metavar='filename', action='store',  default='', help='equivalent to "--push file --command ./file"')
    rawmode.add_argument('--no-tmp', default=False, action='store_true', help='skip creating temp folder and cd-ing into it')
    rawmode.add_argument('--show',   default=False, action='store_true', help='show commands output in the terminal')
    rawmode.add_argument('--notty',  default=False, action='store_true', help='SSH only: don\'t request a TTY')

    checkmode = mode_subparser.add_parser(name='check', help='Check mode: check reachability')
    checkmode.add_argument('--ping', default=False, action='store_true', help='ping hosts if they do not respond at ssh port')

    outputs = parser.add_mutually_exclusive_group(required=False)
    outputs.add_argument('-o',  '--output', metavar='pattern', action='store', default='', help='export results in specified format')
    outputs.add_argument('-of', '--output-format', metavar='FMT', action='append', default=['csv'], help='format of results')    
    return parser.parse_args()


def parsepath(p:str) -> str:
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
    

def parse_plugins(plugins_dir: str = None) -> list[Plugin]:
    """Static method to parse plugins"""
    if not plugins_dir:
        tmp = os.path.dirname(os.path.realpath(__file__))
        plugins_dir = os.path.join(tmp, "plugins/")
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


def banner() -> str:
    b = " _______ _________ _______  _______  _______  _______  _______ \n"
    b += "(  ____ \\\\__   __/(  ___  )(  ____ )(  ____ \(  ____ \(  ____ \\\n"
    b += "| (    \/   ) (   | (   ) || (    )|| (    \/| (    \/| (    \/\n"
    b += "| (_____    | |   | (___) || (____)|| (__    | (_____ | |      \n"
    b += "(_____  )   | |   |  ___  ||     __)|  __)   (_____  )| |      \n"
    b += "      ) |   | |   | (   ) || (\ (   | (            ) || |      \n"
    b += "/\\____) |   | |   | )   ( || ) \ \__| (____/\\/\\____) || (____/\\\n"
    b += "\_______)   )_(   |/     \||/   \__/(_______/\_______)(_______/\n"
    b += "                                             - by 5amu & cekout\n"
    return b


def main():
    args = cliparse()
    
    # Print version if -v is specified and return
    if args.version:
        print(f"Staresc Version: {VERSION}\n")
        return

    # if -hb|--nobanner is not passed, show the banner
    if not args.nobanner:
        print("\033[1m\033[1;31m" + banner() + "\033[0m")

    # if -d|--debug is set, then start printing logger's debug messages
    if args.debug:
        logger.setLevelDebug()
        logger.debug("Logger set to debug mode")
    else:
        logger.setLevelInfo()
        

    # get targets if any, it is useful in every mode
    if args.file:
        f = open(args.file, 'r')
        targets = [t.strip() for t in f.readlines()]
        logger.debug(f"Loaded file: {args.file}")
    else:
        targets = [ str(args.connection) ]
        logger.debug(f"Loaded connection: {args.connection}")

    # determine output and output formats
    if args.output:
        full_path = parsepath(args.output)
        for fmt in args.output_format:
            if fmt == 'csv':
                Exporter.register_handler(CSVHandler(os.path.join(full_path + ".csv")))
            elif fmt == 'xlsx':
                Exporter.register_handler(XLSXHandler(os.path.join(full_path + ".xlsx")))
            elif fmt == 'json':
                Exporter.register_handler(JSONHandler(os.path.join(full_path + ".json")))

    # switch to subcommands
    # subcommand scan handles the plugin run on various targets. this is the
    # only mode that needs the plugins. which can be made specifically for a
    # particular vulnerability.
    if args.mode == 'scan':
        Exporter.register_handler(StdoutHandler(""))        
        exit_code = Runner(logger).scan(targets, parse_plugins(args.plugins))

    # subcommand raw handles the command parallel command execution and file
    # transfers on the targets. 
    elif args.mode == 'raw':
        Exporter.register_handler(RawHandler(""))
        exit_code = Raw(args, logger, args.exec).run(targets)

    # subcommand check handles the reachability and authentication checks on
    # the targets in scope. This mode should produce a csv output for easy 
    # sharing and readability.
    elif args.mode == 'check':
        exit_code = Checker(logger=logger).run(targets=targets)
    
    # not a subcommand, but test staresc integrity by spawning an SSH server
    # and launching pre-determined commands against it to test how staresc
    # would deal with it.
    elif args.test: 
        exit(Tester(logger=logger).test())

    Exporter.export()
    exit(exit_code)
    

if __name__ == '__main__':
    try:
        main()

    except Exception as e:
        logger.error(e)