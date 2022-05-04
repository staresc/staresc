# Commands to be executed on the target
COMMANDS = [
    """
    for e in $( find / -type f -name "*python[0-9]*" 2>/dev/null ); do
        if [ -x "$e" ] && ! { echo "$e" | grep "\.so\|/usr/lib" >/dev/null; }; then
            ver=$( $e -c 'import platform; major, minor, patch = platform.python_version_tuple(); print(major)' 2>/dev/null ) 
            [ "$ver" = "2" ] && echo "$e"
        fi
    done 
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
        return f"Python2 found in following path(s): \n{output[0]}"
    
    return "Not vulnerable"


