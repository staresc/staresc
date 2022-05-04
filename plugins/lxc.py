lxc_commands = [
    "lxc-attach",
    "lxc-checkpoint",
    "lxc-create",
    "lxc-freeze",
    "lxc-snapshot",
    "lxc-unfreeze",
    "lxc-wait",
    "lxc-autostart",
    "lxc-config",
    "lxc-destroy",
    "lxc-info",
    "lxc-start",
    "lxc-unshare",
    "lxc-cgroup",
    "lxc-console",
    "lxc-device",
    "lxc-ls",
    "lxc-stop",
    "lxc-update-config",
    "lxc-checkconfig",
    "lxc-copy",
    "lxc-execute",
    "lxc-monitor",
    "lxc-top",
    "lxc-usernsexec"
]

# Commands to be executed on the target
COMMANDS = [
    f'command -v {" ".join(lxc_commands)}',
    'lxc-ls'
]
# Matcher string for distribution/*nix
# https://docs.python.org/3.4/library/re.html
MATCHER = ".*"

def get_commands() -> list:
    return COMMANDS


def get_matcher() -> str:
    return MATCHER


def parse(output: list) -> str:

    retVal = "LXC is not installed"
    if output[0]:
        retVal = f"LXC is installed: {output[0]}\n"
        if output[1]:
            retVal += f"\n... running containers are: {output[1]}\n"
        return retVal

    return retVal

