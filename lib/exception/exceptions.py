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

