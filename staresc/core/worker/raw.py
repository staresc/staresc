import os
from datetime import datetime
from stat import S_ISDIR

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
    tmp:str
    make_temp:bool
    get_tty:bool
    __sftp:SFTPClient|None


    def __init__(self, connection_string:str, make_temp:bool=True, tmp_base:str="/tmp", get_tty:bool=True):
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
        if self.tmp == "":
            return
        
        if self.sftp is None:
            return
        
        def __isdir(path:str, sftp: SFTPClient):
            try:
                mode = sftp.stat(path).st_mode
                return False if mode is None else S_ISDIR(mode)
                
            except IOError:
                return False


        def __rmdir(path:str, sftp: SFTPClient):
            files = sftp.listdir(path)
            for f in files:
                filepath = os.path.join(path, f)
                __rmdir(filepath, sftp) if __isdir(filepath, sftp) else sftp.remove(filepath)
            sftp.rmdir(path)
        

        if self.make_temp == True:
            __rmdir(self.tmp, self.sftp)


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
        if self.sftp is None:
            raise RawModeFileTransferError("sftp not initialized")

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
        if self.sftp is None:
            raise RawModeFileTransferError("sftp not initialized")

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
                stdin, stdout, stderr = self.connection.run(cmd, timeout=3, get_pty=self.get_tty)
                output.add_test_result(stdin, stdout, stderr)
            
            except CommandError:
                output.add_timeout_result(stdin=cmd)

        return output


    def cleanup(self):
        self.__delete_temp_dir()
        if self.__sftp is not None:
            self.__sftp.close()