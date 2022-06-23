"""Test module for Staresc

this class will be responsible for testing staresc's features. It will spawn a
dummy SSH server, then automatically run some commands on them, expecting unit 
tests to succeed.

What it should check:
    [x] Correct connection to the target
    [x] Correct command execution
    [x] Correct handling of timeouts
    [ ] Correct connection string parsing
    [ ] Correct handling of wrong credentials
"""

from .server import start_server
from .client import StarescTester

# reachable SSH server with good credentials
SSH_SERVER_GOOD = "ssh://user:pass@127.0.0.1:9001/"

# reachable SSH server with bad credentials
SSH_SERVER_WRONG = "ssh://user:wrongpass@127.0.0.1:9001/"

# unreachable SSH server
SSH_SERVER_UNREACHABLE = "ssh://user:pass@127.0.0.1:10000/"

# good commands that should return correct value
GOOD_COMMANDS_WITH_ANSWER = { "whoami": "user" }

# bad commands that should not return 
BAD_COMMAND = "lol"
