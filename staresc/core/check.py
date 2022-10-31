import concurrent.futures
import platform
import os


from staresc.log import Logger
from staresc.exceptions import AuthenticationError, ConnectionError, ConnectionStringError
from staresc.core import Scanner


class Checker:

    def __init__(self, logger: Logger) -> None:
        self.logger = logger


    def check(self, connection_string: str):

        try:
            s = Scanner(connection_string)

        except ConnectionStringError:
            try:
                self.logger.debug(f"{connection_string} is a malformed connection string, is it a single host?")
                parameter = "-n" if platform.system().lower() == "windows" else "-c"
                exit_code = os.system(f"ping {parameter} 1 -w1 {connection_string} >/dev/null 2>&1")
                if exit_code == 0:
                    self.logger.check(target=f"{connection_string}",msg="OK")
                else:
                    self.logger.check(target=f"{connection_string}",msg="Not reachable")
                return
        
            except Exception as e:
                print(type(e), e)
                return
        
        try:
            s.prepare(timeout=1)

        except AuthenticationError:
            self.logger.check(target=f"{s.connection.hostname}:{s.connection.port}",msg="Wrong credentials")
            return

        except ConnectionError:
            self.logger.check(target=f"{s.connection.hostname}:{s.connection.port}",msg="Not reachable")
            return

        self.logger.check(target=f"{s.connection.hostname}:{s.connection.port}", msg="OK")


    def run(self, targets: list[str]):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                futures.append(executor.submit(Checker.check, self, target))
                self.logger.debug(f"Started scan on target {target}")

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan on target {target}")
        return 0
    

    

