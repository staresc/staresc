import os, concurrent.futures
from staresc.log import StarescLogger
from staresc.core import Staresc
from staresc.exporter import StarescExporter
from staresc.output import Output
from staresc.exceptions import StarescCommandError
import argparse
import paramiko
import tqdm
import traceback
from threading import Event, Lock
import encodings.idna # Needed for pyinstaller

class RawWorker:

    def __init__(self, logger, connection_string, make_temp=True, no_sftp=False, tmp_base="/tmp", get_tty=True):
        self.logger = logger
        self.staresc = Staresc(connection_string)
        self.connection = self.staresc.connection
        self.sftp = None
        self.enable_sftp = not(no_sftp)
        self.make_temp = make_temp
        self.tmp_base = tmp_base
        self.tmp = "."
        self.get_tty = get_tty
        self.lock = Lock()

    def __init_sftp(self):
        try:
            self.sftp = paramiko.SFTPClient.from_transport(self.connection.client.get_transport())
        except paramiko.SSHException as e:
            self.logger.error("Failed to initialize the SFTP subsystem. Retry with --no-sftp")
            raise e

    def __make_temp_dir(self) -> str:
        from datetime import datetime
        dirname = f"staresc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        dirpath = os.path.join(self.tmp_base, dirname)
        self.sftp.mkdir(dirpath)
        self.tmp = dirpath
        return dirpath

    def __delete_temp_dir(self):
        from stat import S_ISDIR
        def __isdir(path):
            try:
                return S_ISDIR(self.sftp.stat(path).st_mode)
            except IOError:
                return False

        def __rmdir(path):
            files = self.sftp.listdir(path)
            for f in files:
                filepath = os.path.join(path, f)
                if __isdir(filepath):
                    __rmdir(filepath)
                else:
                    self.sftp.remove(filepath)
            self.sftp.rmdir(path)
        
        if self.make_temp == True:
            __rmdir(self.tmp)

    class ProgressBar:
        def __init__(self, title):
            self.title = title
            self.tqdm = None
            self.last = 0

        def callback(self, progress: int, tot: int):
            if not self.tqdm:
                self.tqdm = tqdm.tqdm(
                    range(tot), 
                    leave=False, 
                    disable=None, 
                    dynamic_ncols=True, 
                    desc=self.title, 
                    unit="B", 
                    unit_scale=True, 
                    unit_divisor=1024, 
                    delay=1,
                    bar_format="{l_bar}{bar}|{n_fmt}"
                )
            self.tqdm.update(progress-self.last)
            self.last = progress
            if progress == tot:
                self.tqdm.close()
            
    def prepare(self):
        self.staresc.prepare()
        if self.enable_sftp and (self.__init_sftp() is not None):
            return False
        if self.make_temp:
            self.__make_temp_dir()
        return True

    def push(self, path):
        filename = os.path.basename(path)
        dest = os.path.join(self.tmp, filename)

        self.logger.raw(
            target=self.connection.hostname,
            port=self.connection.port,
            msg=f"Pushing {filename} to {dest}"
        )

        title = StarescLogger.progress_msg.format(
            f"{self.connection.hostname}:{self.connection.port}",
            f"⏫ {filename}",
        )
        self.sftp.put(path, dest, self.ProgressBar(title).callback)
        self.sftp.chmod(dest, 0o777)

    def pull(self, filename):
        path = os.path.join(self.tmp, filename)
        base_filename = os.path.basename(filename)

        dest_dir = f"staresc_{self.connection.hostname}"
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, base_filename)
        self.logger.raw(
            target=self.connection.hostname,
            port=self.connection.port,
            msg=f"Pulling {filename} to {dest}"
        )
        title = StarescLogger.progress_msg.format(
            f"{self.connection.hostname}:{self.connection.port}",
            f"⏬ {filename}",
        )
        self.sftp.get(path, dest, self.ProgressBar(title).callback)

    def exec(self, cmd_list: list[str]) -> Output:
        output = Output(target=self.connection, plugin=None)

        for cmd in cmd_list:
            try:
                self.logger.raw(
                    target=self.connection.hostname,
                    port=self.connection.port,
                    msg=f"Executing {cmd}"
                )
                cmd = self.staresc._get_absolute_cmd(cmd)
                if self.make_temp:
                    cmd = f"cd {self.tmp} ; " + cmd
                stdin, stdout, stderr = self.connection.run(cmd, timeout=None, get_pty=self.get_tty)
                output.add_test_result(stdin, stdout, stderr)
            except StarescCommandError:
                output.add_timeout_result(stdin=cmd)

        return output

    def cleanup(self):
        with self.lock:
            if self.tmp is not None:
                self.__delete_temp_dir()
                self.tmp = None
            if self.__sftp is not None:
                self.__sftp.close()
                self.__sftp = None

class RawRunner:
    targets: list[str]
    logger:  StarescLogger

    def __init__(self, args: argparse.Namespace, logger: StarescLogger) -> None:
        self.logger  = logger
        self.commands = args.command
        self.pull = args.pull
        self.push = args.push
        self.show = args.show
        self.get_tty = not(args.no_tty)
        self.stop_event = Event()
        self.workers: list[RawWorker] = []
        self.no_sftp = args.no_sftp

        # If the you want to just push/pull files, disable the temp dir creation
        if len(self.commands) == 0:
            self.make_temp = False
        else:
            self.make_temp = not(args.no_tmp)


    def launch(self, connection_string: str) -> None:
        """Launch the commands"""
        try:
            worker = RawWorker(
                logger=self.logger, 
                connection_string=connection_string, 
                make_temp=self.make_temp, 
                no_sftp=self.no_sftp, 
                get_tty=self.get_tty
                )
            self.logger.raw(
                target=worker.connection.hostname,
                port=worker.connection.port,
                msg="Job Started"
            )

            if self.stop_event.is_set(): return
            if not worker.prepare():
                return
            self.workers.append(worker)

            try:
                # Push needed files
                for filename in self.push:
                    if self.stop_event.is_set(): return
                    worker.push(filename)

                # Execute commands
                if self.stop_event.is_set(): return
                output = worker.exec(self.commands)
                StarescExporter.import_output(output)
                if self.show:
                    self.logger.raw(
                        target=worker.connection.hostname,
                        port=worker.connection.port,
                        msg='\n'.join(e['stdout'] for e in output.test_results)
                    )

                # Pull resulting files
                for filename in self.pull:
                    if self.stop_event.is_set(): return
                    worker.pull(filename)
                
                # Cleanup
                if self.stop_event.is_set(): return
                worker.cleanup()
                self.logger.raw(
                    target=worker.connection.hostname,
                    port=worker.connection.port,
                    msg="Job Done"
                )
            
            except KeyboardInterrupt:
                # Cleanup before exiting
                worker.cleanup()
                self.logger.error(f"[{worker.connection.hostname}] Job interrupted")

        except Exception as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            self.logger.debug(traceback.format_exc())
            return

    def run(self, targets: list[str]):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures: list[concurrent.futures.Future] = []
            for target in targets:
                if len(target) == 0: continue
                if not target.startswith("ssh://"):
                    self.logger.error(f"Target skipped because it's not SSH: {target}")
                    continue
                futures.append(executor.submit(RawRunner.launch, self, target))

            try:
                for future in concurrent.futures.as_completed(futures):
                    target = targets[futures.index(future)]
                    self.logger.debug(f"Finished scan on target {target}")
            except KeyboardInterrupt:
                for future in futures:
                    future.cancel()
                    self.stop_event.set()
                    for worker in self.workers:
                        worker.cleanup()
        StarescExporter.export()
