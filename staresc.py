#!/usr/bin/env python3

"""
staresc-ng is based on an internal tool developed by @brn1337 on GitLab.
This is my attempt to make the penetration tests over ssh great again :)

I'm @5amu, welcome!
"""

import sys
from traceback import print_exc

import staresc.cli as cli
from staresc.core import Scanner, Checker, Raw, Tester
from staresc.exceptions import ParseError
from staresc.exporter import Exporter, ScanHandler, RawHandler
from staresc.log import Logger
from staresc import BANNER, VERSION


def main() -> int:
    args = cli.parse()
    
    # Print version if -v is specified and return
    if args.version:
        print(f"Staresc Version: {VERSION}")
        return 0

    # if -hb|--nobanner is not passed, show the banner
    if not args.nobanner:
        print(f"\033[1m\033[1;31m" + BANNER + "\033[0m")

    # if -d|--debug is set, then start printing logger's debug messages
    logger = Logger()
    if args.debug:
        logger.setLevelDebug()
        logger.debug("Logger set to debug mode")
    else:
        logger.setLevelInfo()

    try:     
        # get targets if any, it is useful in every mode
        targets = cli.get_targets(args.file, args.connection)

        # determine output and output formats
        cli.handle_output(args.output, args.output_format)
    
    except ParseError as e:
        logger.error(str(e))
        return 255

    # switch to subcommands
    # subcommand scan handles the plugin run on various targets. this is the
    # only mode that needs the plugins. which can be made specifically for a
    # particular vulnerability.
    if args.mode == 'scan':
        Exporter.register_handler(ScanHandler(""))        
        exit_code = Scanner(timeout=args.timeout).scan(targets, cli.parse_plugins(args.plugins))

    # subcommand raw handles the command parallel command execution and file
    # transfers on the targets. 
    elif args.mode == 'raw':
        Exporter.register_handler(RawHandler(""))
        exit_code = Raw(
            commands=args.command,
            pull=args.pull,
            push=args.push,
            exec=args.exec,
            show=args.show,
            no_tmp=args.no_tmp,
            no_tty=args.notty,
            no_sftp=args.no_sftp,
            timeout=args.timeout,
        ).run(targets)

    # subcommand check handles the reachability and authentication checks on
    # the targets in scope. This mode should produce a csv output for easy 
    # sharing and readability.
    elif args.mode == 'check':
        exit_code = Checker(timeout=args.timeout).run(targets=targets)
    
    # not a subcommand, but test staresc integrity by spawning an SSH server
    # and launching pre-determined commands against it to test how staresc
    # would deal with it.
    elif args.test: 
        return Tester().test()

    # unreachable code, written to warn if a dafuq moment happens. Worry only
    # if that error is ever printed, but should never be.
    else:
        logger.error("We should never reach this code... dafuq happened?")
        return 255

    Exporter.export()
    return exit_code
    

if __name__ == '__main__':
    try:
        sys.exit(main())        

    except Exception:
        print_exc()