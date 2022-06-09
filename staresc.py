#!/usr/bin/env python3

"""
staresc-ng is based on an internal tool developed by @brn1337 on GitLab.
This is my attempt to make the penetration tests over ssh great again :)

I'm @5amu, welcome!
"""

import argparse
import logging
import os
import json
import concurrent.futures
from datetime import datetime

# debug
import traceback

from lib.connection import Connection
from lib.core import Staresc
from lib.exceptions import *


# Configure logger
logging.basicConfig(format='[STARESC]:[%(asctime)s]:[%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


##################################### CLI #######################################

def cliparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser( prog='staresc', description='Make SSH/TELNET PTs great again!', epilog=' ', formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument( '-v', '--verbose', action='count', default=0, help='increase output verbosity (-vv for debug)' )
    parser.add_argument( '-d', '--dontparse', action='store_true', default=False, help='do not parse as soon as the commands are executed' )
    parser.add_argument( '-P', '--pubkey', action='store_true', default=False, help='specify if a pubkey is provided' )
    parser.add_argument( '-c', '--config', metavar='C', action='store', default='', help='path to plugins directory' )
    parser.add_argument( '-r', '--results', action='store', metavar='R', default='', help='results to be parsed (if already existing)' )
    parser.add_argument( '-t', '--timeout', metavar='T', action='store', type=int, help=f'timeout for each command execution on target, default: {Connection.COMMAND_TIMEOUT}s')
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument( '-f', '--file', metavar='F', default='', action='store', help='input file: 1 connection string per line' )

    connection_help  = "schema://user:auth@host:port/root_usr:root_passwd\n"
    connection_help += "auth can be either a password or a path to ssh\n"
    connection_help += "privkey, specified as \\\\path\\\\to\\\\privkey"
    targets.add_argument('connection', nargs='?', action='store', default=None, help=connection_help )
    return parser.parse_args()


def scan(connection_string: str, plugindir: str, to_parse: bool, elevate: bool) -> dict:
    staresc = Staresc(connection_string)
    
    try:
        staresc.prepare()
    except (StarescCommandError, StarescAuthenticationError, Exception) as e:
        logger.error(f"Initialization of {connection_string} raised Exception {type(e)} => {e}")
        return {}

    elevate = staresc.elevate()

    history = []
    for plugin in os.listdir(plugindir):
        if plugin.endswith('.yaml'):
            if not plugindir.startswith('/'):
                plugindir = os.path.join(os.getcwd(), plugindir)

            pluginfile = os.path.join(plugindir, plugin)
            logger.debug(f"Scanning {connection_string} with plugin {pluginfile} (Will be parsed: {to_parse})")
            try:
                to_happend = staresc.do_check(pluginfile, to_parse)
            except Exception as e:
                logger.error(e)
                to_happend = None
            if to_happend != None:
                history.append(to_happend)

    return { 'staresc' : history, 'connection_string' : connection_string, 'elevated' : elevate }


def justparse(outputfile: str, plugindir: str) -> dict:
    
    f = open(outputfile, 'r')
    to_parse = json.load(f)
    logger.debug(f"Loaded result file: {outputfile}")

    conn = to_parse['connection_string']
    hist = to_parse['staresc']

    staresc = Staresc(conn)

    new_history = []
    for result in hist:
        for plugin in os.listdir(plugindir):
            if plugin.endswith('.py') and result['plugin'] == plugin and not plugindir.startswith('/'):
                plugindir = os.path.join(os.getcwd(), plugindir)
                    
            pluginfile = os.path.join(plugindir, plugin)
            logger.debug(f"Analyzing {result} with plugin {pluginfile}")
            parsed = staresc.do_offline_parsing(pluginfile, result)
            new_history.append(parsed)
        
    return { 'staresc' : new_history, 'connection_string' : conn, 'elevated' : to_parse['elevated']}


def write(results: dict, outfile: str) -> None:
    with open(outfile, 'x') as f:
        json.dump(results, f)


if __name__ == '__main__':
    
    args = cliparse()

    if args.verbose == 1:
        logger.setLevel(logging.DEBUG)
        logger.debug("Logger set to debug mode")
    else:
        logger.setLevel(logging.INFO)
        logger.info("Logger set to info mode")

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

    if args.results:
        outfile = f"{args.results}-parsed.json"
        results = justparse(args.results, plugins_dir)
        write(results, outfile)
        logger.info(f"Wrote parsed file to {outfile}")
        exit(0)
    if args.timeout:
        Connection.COMMAND_TIMEOUT = args.timeout

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for target in targets:
            futures.append(executor.submit(scan, target, plugins_dir, (not args.dontparse), args.pubkey))
            logger.info(f"Started scan on target {target}")

        for future in concurrent.futures.as_completed(futures):
            target = targets[futures.index(future)]
            try:
                dump = future.result()
                logger.info(f"Finished scan on target {target}")
            except Exception as e:
                traceback.print_exc()
                print(f"{target} generated an exception: {e}")
            else:
                now = datetime.now()
                outfile = f"{now.year}-{now.month}-{now.day}-{now.hour}:{now.minute}:{now.second}-{Connection.get_hostname(target)}:{Connection.get_port(target)}.json"
                write(dump, outfile)
                logger.info(f"Results written: {outfile}")
             
        