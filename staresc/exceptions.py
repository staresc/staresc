
class ParseError(Exception):
    """Exception raised when the argument parsing fails

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class ConnectionStringError(Exception):
    """
    Exception raised if the connection string is invalid
    
    Atributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class CommandError(Exception):
    """Exception raised when a command fails

    Attributes:
        msg -- meesage to be displayed
    """

    command: str
    def __init__(self, msg: str):
        super().__init__(msg)


class AuthenticationError(Exception):
    """Exception raised when the authentication fails

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class ConnectionError(Exception):
    """Exception raised when the connection fails

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class PluginError(Exception):
    """Exception raised when the plugin syntax is wrong

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)