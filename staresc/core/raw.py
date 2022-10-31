import concurrent.futures
import argparse

from staresc.log import Logger
from staresc.exporter import Exporter
from staresc.core.worker import RawWorker
from staresc.exceptions import RawModeFileTransferError

class Raw:
    targets: list[str]
    logger:  Logger

    def __init__(self, args: argparse.Namespace, exec: str) -> None:
        self.logger  = Logger()
        self.commands = args.command
        self.pull = args.pull
        self.push = args.push
        self.show = args.show
        self.get_tty = not(args.notty)

        # If the you want to just push/pull files, disable the temp dir creation
        if len(self.commands) == 0:
            self.make_temp = False
        else:
            self.make_temp = not(args.no_tmp)


    def launch(self, connection_string: str) -> None:
        """Launch the commands"""
        try:
            worker = RawWorker(connection_string, self.make_temp, get_tty=self.get_tty)
            self.logger.raw(
                target=worker.connection.hostname,
                port=str(worker.connection.port),
                msg="Job Started"
            )
            worker.prepare()

            try:
                # Push needed files
                for filename in self.push:
                    worker.push(filename)

                # Execute commands
                output = worker.exec(self.commands)
                Exporter.import_output(output)
                if self.show:
                    self.logger.raw(
                        target=worker.connection.hostname,
                        port=str(worker.connection.port),
                        msg='\n'.join(e['stdout'] for e in output.test_results)
                    )

                # Pull resulting files
                for filename in self.pull:
                    worker.pull(filename)
                
                # Cleanup
                worker.cleanup()
                self.logger.raw(
                    target=worker.connection.hostname,
                    port=str(worker.connection.port),
                    msg="Job Done"
                )
            
            except KeyboardInterrupt:
                # Cleanup before exiting
                worker.cleanup()
                self.logger.error(f"[{worker.connection.hostname}] Job interrupted")


        except RawModeFileTransferError as e:
            self.logger.error(str(e))


        except Exception as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            return


    def run(self, targets: list[str]) -> int:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                if not target.startswith("ssh://"):
                    self.logger.error(f"Target skipped because it's not SSH: {target}")
                    continue
                futures.append(executor.submit(Raw.launch, self, target))
                self.logger.debug(f"Started scan on target {target}")

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan on target {target}")
        return 0
