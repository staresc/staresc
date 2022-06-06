class ConnectionStringError(Exception):
    """
    Exception raised if the connection string is invalid
    
    Atributes:
        conn -- connection string
        schemas -- supported schemas
    """

    def __init__(self, conn: str, schemas: list) -> None:
        message=f"Connection String is invalid: {conn}"
        super().__init__(message)


class SchemeError(Exception):
    """
    Exception raised if the schema is unsupported

    Attributes:
        scheme -- unsupported scheme
    """

    def __init__(self, scheme) -> None:
        message=f"Unsupported schema: {scheme}"
        super().__init__(message=message)


class CommandTimeoutError(Exception):
    """Exception raised when a command requires too much execution time

    Attributes:
        command -- command that triggers timeout
    """

    command: str
    def __init__(self, command: str = ''):
        self.command = command
        super().__init__(f'Command "{self.command}" requires too much execution time')


class AuthenticationError(Exception):
    """Exception raised when the authentication fails

    Attributes:
        username -- username used for authentication
        password -- password used for authentication
    """

    def __init__(self, user: str = '', passwd: str = ''):
        super().__init__(f'Authentication failed with creds: {user}:{passwd}')