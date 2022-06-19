#!/usr/bin/env python3

"""
staresc-ng is based on an internal tool developed by @brn1337 on GitLab.
This is my attempt to make the penetration tests over ssh great again :)

I'm @5amu, welcome!
"""

import argparse
import os
import json
import yaml
import concurrent.futures
from datetime import datetime
from tabulate import tabulate

# debug
# import traceback

from lib.connection import Connection
from lib.core import Staresc
from lib.exceptions import *
from lib.exporter import *
from lib.exporter.stdoutexporter import StdoutExporter
from lib.plugin_parser import Plugin
from lib.log import StarescLogger

# Configure logger
logger = StarescLogger()

##################################### CLI #######################################

def cliparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser( prog='staresc', description='Make SSH/TELNET PTs great again!', epilog=' ', formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument( '-v', '--verbose', action='count', default=0, help='increase output verbosity (-vv for debug)' )
    parser.add_argument( '-d', '--dontparse', action='store_true', default=False, help='do not parse as soon as the commands are executed' )
    parser.add_argument( '-P', '--pubkey', action='store_true', default=False, help='specify if a pubkey is provided' )
    parser.add_argument( '-c', '--config', metavar='C', action='store', default='', help='path to plugins directory' )
    parser.add_argument( '-r', '--results', action='store', metavar='R', default='', help='results to be parsed (if already existing)' )
    parser.add_argument( '-t', '--timeout', metavar='T', action='store', type=int, help=f'timeout for each command execution on target, default: {Connection.COMMAND_TIMEOUT}s')
    parser.add_argument('-ocsv', '--output-csv', metavar='filename', action='store', default='', help='export results on a csv file')
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument( '-f', '--file', metavar='F', default='', action='store', help='input file: 1 connection string per line' )

    connection_help  = "schema://user:auth@host:port/root_usr:root_passwd\n"
    connection_help += "auth can be either a password or a path to ssh\n"
    connection_help += "privkey, specified as \\\\path\\\\to\\\\privkey"
    targets.add_argument('connection', nargs='?', action='store', default=None, help=connection_help )
    return parser.parse_args()


def parse_plugins(plugins_dir: str) -> list[Plugin]:
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

def scan(connection_string: str, plugins: list[Plugin], to_parse: bool, elevate: bool, exporters: list[Exporter]) -> dict:
    vulns_severity = {}
    staresc = Staresc(connection_string)
    
    try:
        staresc.prepare()
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")
        return {}

    # For future reference
    # elevate = staresc.elevate()
    
    for plugin in plugins:
        logger.debug(f"Scanning {connection_string} with plugin {plugin.id} (Will be parsed: {to_parse})")
        to_append = None
        try:
            to_append = staresc.do_check(plugin, to_parse)

        except Exception as e:
            logger.error(f"{type(e).__name__}: {e}")
            #print(e.__traceback__)
        if to_append:
            # Add output to exporters
            for exp in exporters:
                exp.add_output(to_append)
            # Keep tracks of vulns found in this target
            if to_append.is_vuln_found():
                to_append_severity = plugin.severity
                if to_append_severity in vulns_severity:
                    vulns_severity[to_append_severity] += 1
                else:
                    vulns_severity[to_append_severity] = 1
    return vulns_severity


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
        logger.setLevelDebug()
        logger.debug("Logger set to debug mode")
    else:
        logger.setLevelInfo()
        logger.info("Logger set to info mode")

    if args.file:
        f = open(args.file, 'r')
        targets = f.readlines()
        logger.debug(f"Loaded file: {args.file}")
    else:
        targets = [ str(args.connection) ]
        logger.debug(f"Loaded connection: {args.connection}")

    if args.timeout:
        Connection.COMMAND_TIMEOUT = args.timeout

    exporters = []
    now = datetime.now()
    default_output_filename = f"staresc__{now.year}-{now.month}-{now.day}-{now.hour}:{now.minute}:{now.second}"

    if args.output_csv:
        filename = CSVExporter.format_filename(args.output_csv, default_name = default_output_filename)
        exporters.append(CSVExporter(filename))

    exporters.append(StdoutExporter())

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

    plugins = parse_plugins(plugins_dir)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for target in targets:
            futures.append(executor.submit(scan, target, plugins, (not args.dontparse), args.pubkey, exporters))
            logger.debug(f"Started scan on target {target}")

        for future in concurrent.futures.as_completed(futures):
            target = targets[futures.index(future)]
            try:
                scan_summary = future.result()
                logger.debug(f"Finished scan on target {target}")
                if len(scan_summary) == 0:
                    logger.info(f"Scan summary for {Connection.get_hostname(target)}\nNO VULN FOUND")
                else:
                    scan_summary_table = []
                    for sev, freq in scan_summary.items():
                        scan_summary_table.append([sev, freq])
                    logger.info(f"Scan summary for {Connection.get_hostname(target)}\n" + tabulate(scan_summary_table, headers=["SEVERITY", "VULN FOUND"], tablefmt="github"))
            except Exception as e:
                logger.error(f"{type(e).__name__}: {e}")
                #traceback.print_exc()

    # export results on file
    for exp in exporters:
        exp.export()
        logger.info(f"Report exported in file: {exp.filename}")

             
        