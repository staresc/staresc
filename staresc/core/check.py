import concurrent.futures


from staresc.log import StarescLogger
from staresc.exceptions import StarescAuthenticationError, StarescConnectionError, StarescConnectionStringError
from staresc.core import Staresc


class Checker:

    def __init__(self, logger: StarescLogger) -> None:
        self.logger = logger


    def check(self, target: str):
        try:
            s = Staresc(target)
            s.prepare()

        except StarescAuthenticationError:
            self.logger.check(target=s.connection.hostname,port=s.connection.port,msg="Wrong credentials")
            return

        except StarescConnectionError:
            self.logger.check(target=s.connection.hostname,port=s.connection.port,msg="Not reachable")
            return

        except StarescConnectionStringError:
            self.logger.check(target=s.connection.hostname,port=s.connection.port,msg="Incorrect connection string")
            return

        self.logger.check(target=s.connection.hostname, port=s.connection.port, msg="OK")


    def run(self, targets: list[str]):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                futures.append(executor.submit(Checker.check, self, target))
                self.logger.debug(f"Started scan on target {target}")

            for future in concurrent.futures.as_completed(futures):
                target = targets[futures.index(future)]
                self.logger.debug(f"Finished scan on target {target}")
    

    

