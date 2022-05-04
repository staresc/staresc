# Commands to be executed on the target
COMMANDS = [
    """
    if netstat -ltunp | grep '^tcp.*ftp' &>/dev/null; then
        port="$( netstat -ltunp | grep '^tcp.*ftp' | grep -o ':[0-9]* ' | tr -d ':' | head -n 1 )"
        netcat=$( command -v nc || command -v ncat || command -v netcat )
        echo -e 'USER anonymous\\nPASS anonymous' | $netcat 127.0.0.1 $port
    fi
    """
]
# Matcher string for distribution/*nix
# https://docs.python.org/3.4/library/re.html
MATCHER = ".*"

def get_commands() -> list:
    return COMMANDS


def get_matcher() -> str:
    return MATCHER


def parse(output: list) -> str:
    
    if output[0]:
        if 'Login incorrect' in output[0]:
            return "Cleartext login is enabled"
        elif 'Login successful' in output[0]:
            return "Cleartext login is enabled, as well as anonymous user"        

    return "Not vulnerable"



