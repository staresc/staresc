import os
import concurrent.futures
import argparse
from datetime import datetime

import paramiko
from paramiko import SFTPClient
import tqdm

from staresc.connection.sshconnection import SSHConnection
from staresc.log import Logger
from staresc.exporter import Exporter
from staresc.output import Output
from staresc.exceptions import CommandError

class RawWorker:
    connection:SSHConnection
    tmp_base:str
    tmp:str
    make_temp:bool
    __sftp:SFTPClient|None

    def __init__(self, connection_string, make_temp=True, tmp_base="/tmp", get_tty=True):
        self.logger = Logger()
        self.connection = SSHConnection(connection_string)
        self.make_temp = make_temp
        self.tmp_base = tmp_base
        self.tmp = "."
        self.get_tty = get_tty

    @property
    def sftp(self) -> SFTPClient|None:
        # Lazy sftp initialization; useful for targets that don't have sftp_server
        # because you can use Raw mode without using sftp features and it never gets initialized
        if self.__sftp is not None:
            return self.__sftp

        transport = self.connection.client.get_transport()
        if transport:
            self.__sftp = paramiko.SFTPClient.from_transport(transport)

        return self.__sftp
    

    def __make_temp_dir(self) -> str:
        if not self.sftp:
            raise Exception

        dirname = f"staresc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.tmp = os.path.join(self.tmp_base, dirname)
        self.sftp.mkdir(self.tmp)
        return self.tmp


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
                    disable=False, 
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
        self.connection.connect()
        if self.make_temp:
            self.__make_temp_dir()

    def push(self, path):
        filename = os.path.basename(path)
        dest = os.path.join(self.tmp, filename)

        self.logger.raw(
            target=self.connection.hostname,
            port=str(self.connection.port),
            msg=f"Pushing {filename} to {dest}"
        )

        title = Logger.progress_msg.format(
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
            port=str(self.connection.port),
            msg=f"Pulling {filename} to {dest}"
        )
        title = Logger.progress_msg.format(
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
                    port=str(self.connection.port),
                    msg=f"Executing {cmd}"
                )
                if self.make_temp:
                    cmd = f"cd {self.tmp} ; " + cmd
                stdin, stdout, stderr = self.connection.run(cmd, timeout=0, get_pty=self.get_tty)
                output.add_test_result(stdin, stdout, stderr)
            except CommandError:
                output.add_timeout_result(stdin=cmd)

        return output

    def cleanup(self):
        if self.tmp is not None:
            self.__delete_temp_dir()
            self.tmp = None
        if self.__sftp is not None:
            self.__sftp.close()

class Raw:
    targets: list[str]
    logger:  Logger

    def __init__(self, args: argparse.Namespace, logger: Logger, exec: str) -> None:
        self.logger  = logger
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
            worker = RawWorker(self.logger, connection_string, self.make_temp, get_tty=self.get_tty)
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
                        port=worker.connection.port,
                        msg='\n'.join(e['stdout'] for e in output.test_results)
                    )

                # Pull resulting files
                for filename in self.pull:
                    worker.pull(filename)
                
                # Cleanup
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
