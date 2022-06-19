#!/usr/bin/env python3

"""
staresc-ng is based on an internal tool developed by @brn1337 on GitLab.
This is my attempt to make the penetration tests over ssh great again :)

I'm @5amu, welcome!
"""

import argparse
import os

from lib.connection import Connection
from lib.exceptions import *
from lib.exporter import *
from lib.log import StarescLogger
from lib.runner import StarescRunner

##################################### CLI #######################################

def cliparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser( prog='staresc', description='Make SSH/TELNET PTs great again!', epilog=' ', formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument( '-v', '--verbose', action='count', default=0, help='increase output verbosity (-vv for debug)' )
    parser.add_argument( '-P', '--pubkey', action='store_true', default=False, help='specify if a pubkey is provided' )
    parser.add_argument( '-c', '--config', metavar='C', action='store', default='', help='path to plugins directory' )
    parser.add_argument( '-t', '--timeout', metavar='T', action='store', type=int, help=f'timeout for each command execution on target, default: {Connection.COMMAND_TIMEOUT}s')
    
    outputs = parser.add_mutually_exclusive_group(required=False)
    outputs.add_argument('-ocsv', '--output-csv', metavar='filename', action='store', default='', help='export results on a csv file')
    outputs.add_argument('-oall', '--output-all', metavar='pattern', action='store', default='', help='export results in all possible formats')
    
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument( '-f', '--file', metavar='F', default='', action='store', help='input file: 1 connection string per line' )

    connection_help  = "schema://user:auth@host:port/root_usr:root_passwd\n"
    connection_help += "auth can be either a password or a path to ssh\n"
    connection_help += "privkey, specified as \\\\path\\\\to\\\\privkey"
    targets.add_argument('connection', nargs='?', action='store', default=None, help=connection_help )
    return parser.parse_args()


if __name__ == '__main__':

    # Configure logger
    logger = StarescLogger()
    
    args = cliparse()

    if args.verbose == 1:
        logger.setLevelDebug()
        logger.debug("Logger set to debug mode")
    else:
        logger.setLevelInfo()

    if args.file:
        f = open(args.file, 'r')
        targets = f.readlines()
        logger.debug(f"Loaded file: {args.file}")
    else:
        targets = [ str(args.connection) ]
        logger.debug(f"Loaded connection: {args.connection}")

    if not args.config:
        plugins_dir = os.path.dirname(os.path.realpath(__file__))
        plugins_dir = os.path.join(plugins_dir, "plugins/")
    else:
        plugins_dir = args.config

    exporters = []
    exporters.append(StdoutExporter())

    if args.output_all:
        exporters.append(CSVExporter(args.output_all))

    if args.output_csv:
        exporters.append(CSVExporter(args.output_csv))

    # TODO: banner dor staresc
    sr = StarescRunner(logger)
    
    plugins = sr.parse_plugins(plugins_dir)
    sr.run(targets, plugins, args.pubkey, exporters)
