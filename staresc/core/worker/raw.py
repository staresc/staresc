import os
from datetime import datetime
from stat import S_ISDIR
import posixpath
from threading import Lock

import paramiko
from paramiko import SFTPClient
import tqdm

from staresc.output import Output
from staresc.connection import SSHConnection
from staresc.exceptions import CommandError, RawModeFileTransferError
from staresc.log import Logger


class RawWorker:
    connection:SSHConnection
    logger:Logger
    tmp_base:str
    cwd:str
    make_temp:bool
    get_tty:bool
    lock:Lock
    no_sftp:bool
    __sftp:SFTPClient|None
    timeout:float

    def __init__(self, connection_string:str, make_temp:bool=True, tmp_base:str="/tmp", get_tty:bool=True, no_sftp:bool = False, timeout:float = 0.0):
        self.logger     = Logger()
        self.connection = SSHConnection(connection_string)
        self.make_temp  = make_temp
        self.tmp_base   = tmp_base
        self.cwd        = "."
        self.get_tty    = get_tty
        self.__sftp     = None
        self.lock       = Lock()
        self.no_sftp    = no_sftp
        self.timeout    = timeout

    @property
    def sftp(self) -> SFTPClient|None:
        # Lazy sftp initialization; useful for targets that don't have sftp_server
        # because you can use Raw mode without using sftp features and it never gets initialized
        if self.__sftp is not None:
            return self.__sftp
        
        if self.no_sftp:
            raise RawModeFileTransferError("an SFTP action was requested but --no-sftp was specified.")
        
        try:
            transport = self.connection.client.get_transport()
            if transport:
                self.__sftp = paramiko.SFTPClient.from_transport(transport)
                return self.__sftp
            else:
                raise RawModeFileTransferError("failed to initialize the SFTP subsystem. Retry with --no-sftp")
            
        except paramiko.SSHException as e:
            self.logger.error("failed to initialize the SFTP subsystem. Retry with --no-sftp")
            raise e
    

    def __make_temp_dir(self) -> str:
        if not self.sftp:
            # Terminate execution: let's not risk deleting the user's home directory when __delete_temp_dir
            # is called but the temp dir was not created. This should never happen anyway.
            raise RawModeFileTransferError("trying to create temp directory but SFTP subsystem is uninitialized, something's wrong.")

        dirname = f"staresc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.cwd = posixpath.join(self.tmp_base, dirname)
        self.sftp.mkdir(self.cwd)
        return self.cwd


    def __delete_temp_dir(self):
        if not self.cwd:
            return
        
        if self.sftp is None:
            return
        
        def __isdir(path:str, sftp: SFTPClient):
            try:
                mode = sftp.stat(path).st_mode
                return mode is not None and S_ISDIR(mode)
                
            except IOError:
                return False


        def __rmdir(path:str, sftp: SFTPClient):
            files = sftp.listdir(path)
            for f in files:
                filepath = posixpath.join(path, f)
                __rmdir(filepath, sftp) if __isdir(filepath, sftp) else sftp.remove(filepath)
            sftp.rmdir(path)
        

        if self.make_temp == True:
            __rmdir(self.cwd, self.sftp)


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
        self.connection.connect(timeout=self.timeout)
        if self.make_temp:
            self.__make_temp_dir()


    def push(self, local_path):
        if self.sftp is None:
            raise RawModeFileTransferError("sftp not initialized")

        filename = os.path.basename(local_path)
        remote_path = posixpath.join(self.cwd, filename)

        self.logger.raw(
            target=self.connection.hostname,
            port=str(self.connection.port),
            msg=f"Pushing {filename} to {remote_path}"
        )

        title = Logger.progress_msg.format(
            f"{self.connection.hostname}:{self.connection.port}",
            f"⏫ {filename}",
        )
        self.sftp.put(local_path, remote_path, self.ProgressBar(title).callback)
        self.sftp.chmod(remote_path, 0o777)


    def pull(self, filename):
        if self.sftp is None:
            raise RawModeFileTransferError("sftp not initialized")

        remote_path = posixpath.join(self.cwd, filename)
        base_filename = os.path.basename(filename)

        dest_dir = f"staresc_{self.connection.hostname}"
        os.makedirs(dest_dir, exist_ok=True)
        local_path = os.path.join(dest_dir, base_filename)
        self.logger.raw(
            target=self.connection.hostname,
            port=str(self.connection.port),
            msg=f"Pulling {filename} from {remote_path}"
        )
        title = Logger.progress_msg.format(
            f"{self.connection.hostname}:{self.connection.port}",
            f"⏬ {filename}",
        )
        self.sftp.get(remote_path, local_path, self.ProgressBar(title).callback)


    def exec(self, cmd_list: list[str]) -> Output:
        output = Output(target=self.connection, plugin=None)

        for cmd in cmd_list:
            try:
                self.logger.raw(
                    target=self.connection.hostname,
                    port=str(self.connection.port),
                    msg=f"Executing {cmd}"
                )
                if self.cwd != ".":
                    cmd = f"cd {self.cwd} ; " + cmd
                stdin, stdout, stderr = self.connection.run(cmd, timeout=self.timeout, get_pty=self.get_tty)
                output.add_test_result(stdin, stdout, stderr)
            
            except CommandError:
                output.add_timeout_result(stdin=cmd)

        return output


    def cleanup(self):
        with self.lock:
            if self.make_temp:
                self.__delete_temp_dir()
                self.cwd = None
            if self.__sftp is not None:
                self.__sftp.close()