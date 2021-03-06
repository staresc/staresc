#!/usr/bin/python
""" Class responsible for the connection layer

The main class, treated as an interface, is Connection, every possible
connection type inherits the methods and the constructor of Connection.
"""

from .connection import Connection
from .sshconnection import SSHConnection
from .sshssconnection import SSHSSConnection
from .tntconnection import TNTConnection

SCHEME_TO_CONNECTION = {
    "ssh"    : SSHConnection,
    "telnet" : TNTConnection,
    "sshss"  : SSHSSConnection
}
"""Mapping for supported shemes to relative connection class"""
