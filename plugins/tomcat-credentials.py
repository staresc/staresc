import xml.etree.ElementTree as ET

# Commands to be executed on the target
COMMANDS = [
    'cat /etc/tomcat/tomcat-users.xml 2>/dev/null'
]
# Matcher string for distribution/*nix
# https://docs.python.org/3.4/library/re.html
MATCHER = ".*"

def get_commands() -> list:
    return COMMANDS


def get_matcher() -> str:
    return MATCHER


def parse(output: list) -> str:

    credentials = []
    if output[0]:
        try:
            root = ET.fromstring(output[0])
            for user in root.iter('user'):
                credentials.append(user.get('username') + ":" + user.get('password'))
        except Exception:
            return "Not Vulnerable"

    if credentials:    
        return f"Tomcat credentials found: {credentials.join(' ')}"
    
    return "Not vulnerable"