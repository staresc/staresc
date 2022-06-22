#!/usr/bin/env python3

"""
staresc-ng is based on an internal tool developed by @brn1337 on GitLab.
This is my attempt to make the penetration tests over ssh great again :)

I'm @5amu, welcome!
"""

import argparse
import os

from staresc.exporter import StarescExporter, StarescCSVHandler, StarescStdoutHandler, StarescXLSXHandler, StarescJSONHandler
from staresc.log import StarescLogger
from staresc.core import StarescRunner

# Configure logger
logger = StarescLogger()

##################################### CLI #######################################

def cliparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser( prog='staresc', description='Make SSH/TELNET PTs great again!', epilog=' ', formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument( '-v', '--verbose', action='count', default=0, help='increase output verbosity (-vv for debug)' )
    parser.add_argument( '-P', '--pubkey', action='store_true', default=False, help='specify if a pubkey is provided' )
    parser.add_argument( '-c', '--config', metavar='C', action='store', default='', help='path to plugins directory' )
    parser.add_argument( '-t', '--timeout', metavar='T', action='store', type=int, help=f'timeout for each command execution on target')
    
    single_outputs = parser.add_argument_group()
    single_outputs.add_argument('-ocsv', '--output-csv', metavar='filename', action='store', default='', help='export results on a csv file')
    single_outputs.add_argument('-oxlsx', '--output-xlsx', metavar='filename', action='store', default='', help='export results on a xlsx (MS Excel) file')
    single_outputs.add_argument('-ojson', '--output-json', metavar='filename', action='store', default='', help='export results on a json file')
    
    outputs = parser.add_mutually_exclusive_group(required=False)
    outputs.add_argument_group(single_outputs)
    outputs.add_argument('-oall', '--output-all', metavar='pattern', action='store', default='', help='export results in all possible formats')
    
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument( '-f', '--file', metavar='F', default='', action='store', help='input file: 1 connection string per line' )

    connection_help  = "schema://user:auth@host:port/root_usr:root_passwd\n"
    connection_help += "auth can be either a password or a path to ssh\n"
    connection_help += "privkey, specified as \\\\path\\\\to\\\\privkey"
    targets.add_argument('connection', nargs='?', action='store', default=None, help=connection_help )
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

    StarescExporter.register_handler(StarescStdoutHandler(""))

    if args.output_all:
        
        full_path = parsepath(args.output_all)
        StarescExporter.register_handler(StarescCSVHandler(os.path.join(full_path + ".csv")))
        StarescExporter.register_handler(StarescXLSXHandler(os.path.join(full_path + ".xlsx")))
        StarescExporter.register_handler(StarescJSONHandler(os.path.join(full_path + ".json")))

    if args.output_csv:
        StarescExporter.register_handler(StarescCSVHandler(args.output_csv))

    if args.output_xlsx:
        StarescExporter.register_handler(StarescXLSXHandler(args.output_xlsx))

    if args.output_json:
        StarescExporter.register_handler(StarescJSONHandler(args.output_json))

    print("\033[1m\033[1;31m" + banner() + "\033[0m")
    sr = StarescRunner(logger)
    
    plugins = sr.parse_plugins(plugins_dir)
    sr.run(targets, plugins, args.pubkey)


if __name__ == '__main__':
    main()
