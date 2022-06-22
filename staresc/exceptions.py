class StarescConnectionStringError(Exception):
    """
    Exception raised if the connection string is invalid
    
    Atributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class StarescCommandError(Exception):
    """Exception raised when a command fails

    Attributes:
        msg -- meesage to be displayed
    """

    command: str
    def __init__(self, msg: str):
        super().__init__(msg)


class StarescAuthenticationError(Exception):
    """Exception raised when the authentication fails

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class StarescConnectionError(Exception):
    """Exception raised when the connection fails

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class StarescPluginError(Exception):
    """Exception raised when the plugin syntax is wrong

    Attributes:
        msg -- meesage to be displayed
    """

    def __init__(self, msg: str):
        super().__init__(msg)