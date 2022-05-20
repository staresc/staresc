class CommandTimeoutError(Exception):
    """Raised when a command requires too much execution time"""
    command: str
    def __init__(self, command: str = ''):
        self.command = command
        super().__init__(f'Command "{self.command}" requires too much execution time')
