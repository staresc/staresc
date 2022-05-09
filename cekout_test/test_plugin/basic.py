# Commands to be executed on the target
COMMANDS = [
    'whoami',
    'uname -a'
]
# Matcher string for distribution/*nix
# https://docs.python.org/3.4/library/re.html
MATCHER = ".*"

def get_commands() -> list:
    return COMMANDS


def get_matcher() -> str:
    return MATCHER


def parse(output: list) -> str:

    # get 'whoami' output
    user = output[0]
    # get 'uname -a' output
    kernel = output[1]

    retVal = f"""
    User is {user}: running kernel {kernel}\n
    It is advised to check kernel flaws using this string:\n
    {output[1]}
    """

    return retVal

