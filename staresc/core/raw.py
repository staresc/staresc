import os
import concurrent.futures
import encodings.idna # Needed for pyinstaller

from threading import Event

from staresc.log import Logger
from staresc.exporter import Exporter
from staresc.core.worker import RawWorker
from staresc.exceptions import RawModeFileTransferError


class Raw:
    logger:Logger
    commands:list[str]
    push:list[str]
    pull:list[str]
    show:bool
    get_tty:bool
    no_tmp:bool
    make_tmp:bool
    no_sftp:bool
    stop_event:Event
    timeout:float

    def __init__(self, timeout = float(0), commands:list[str] = None, push:list[str] = None, pull:list[str] = None, exec:str = '', show:bool = False, no_tty:bool = False, no_tmp:bool = False, no_sftp:bool = False) -> None:
        self.logger     = Logger()
        self.commands   = commands or []
        self.push       = push or []
        self.pull       = pull or []
        self.show       = show
        self.get_tty    = not no_tty
        self.no_sftp    = no_sftp
        self.no_tmp     = no_tmp or no_sftp
        self.timeout    = timeout
        self.stop_event = Event()

        self.workers: list[RawWorker] = []

        if exec and exec != '':
            self.push.append(exec)
            self.commands.append('./' + os.path.basename(exec))

        # If the you want to just push/pull files, disable the temp dir creation
        self.make_temp = len(self.commands) != 0 and not self.no_tmp
        
    def __is_stop_event_set(self) -> bool:
        if self.stop_event.isSet():
            self.logger.debug("event was set")
            return True
        return False


    def launch(self, connection_string: str) -> None:
        """Launch the commands"""
        try:
            worker = RawWorker( 
                connection_string=connection_string, 
                make_temp=self.make_temp, 
                no_sftp=self.no_sftp, 
                get_tty=self.get_tty,
                timeout=self.timeout
                )
            self.logger.raw(
                target=worker.connection.hostname,
                port=str(worker.connection.port),
                msg="Job Started"
            )

            if self.__is_stop_event_set(): return
            worker.prepare()
            self.workers.append(worker) # Appending elements to lists is thread-safe

            try:
                # Push needed files
                for filename in self.push:
                    if self.__is_stop_event_set(): return
                    worker.push(filename)

                # Execute commands
                if self.__is_stop_event_set(): return
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
                    if self.__is_stop_event_set(): return
                    worker.pull(filename)
                
                # Cleanup
                if self.__is_stop_event_set(): return
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
            raise e


    def run(self, targets: list[str]) -> int:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures: list[concurrent.futures.Future] = []
            for target in targets:
                if len(target) == 0: continue
                if not target.startswith("ssh://"):
                    self.logger.error(f"Target skipped because it's not SSH: {target}")
                    continue
                futures.append(executor.submit(Raw.launch, self, target))

            try:
                for future in concurrent.futures.as_completed(futures):
                    target = targets[futures.index(future)]
                    self.logger.debug(f"Finished operations on target {target}")
            
            except KeyboardInterrupt:
                self.stop_event.set()
                self.logger.info(f"Shutting down threads...")
                # Synchronize before cleaning-up to prevent race conditions
                executor.shutdown(wait=True, cancel_futures=True)
                for worker in self.workers:
                    worker.cleanup()

        Exporter.export()
        return 0
