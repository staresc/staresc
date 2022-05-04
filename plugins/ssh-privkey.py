# Commands to be executed on the target
COMMANDS = [
    'grep -H "PRIVATE" /home/**/.ssh/*',
    'ls -la /home/**/.ssh/*'
]
# Matcher string for distribution/*nix
# https://docs.python.org/3.4/library/re.html
MATCHER = ".*"

def get_commands() -> list:
    return COMMANDS


def get_matcher() -> str:
    return MATCHER


def parse(output: list) -> str:

    if "PRIVATE" in output[0]:
        retVal = "Found readable private keys in the following locations:"
        retVal += output[0]
        return retVal
    
    return "Not vulnerable"

