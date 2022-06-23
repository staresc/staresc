import threading, socket

import paramiko

import staresc.test as t


SSH_BANNER = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3"
HOST_KEY = paramiko.RSAKey.generate(2048)


class FakeSshServer(paramiko.ServerInterface):
    """Settings for paramiko server interface"""

    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Accept all passwords as valid by default
        return paramiko.AUTH_SUCCESSFUL if password == "pass" else paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True


def handle_cmd(cmd: str, chan: paramiko.Channel):
    """Branching statements to handle and prepare a response for a command"""
    if cmd in t.GOOD_COMMANDS_WITH_ANSWER.keys():
        chan.send(f"{t.GOOD_COMMANDS_WITH_ANSWER[cmd]}\r\n")

    elif cmd == t.BAD_COMMAND:
        pass


def handle_connection(client, addr):
    """Handle a new ssh connection"""
    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(HOST_KEY)

        # Change banner to appear legit on nmap (or other network) scans
        transport.local_version = SSH_BANNER
        server = FakeSshServer()

        try:
            transport.start_server(server=server)

        except paramiko.SSHException:
            raise Exception("SSH negotiation failed")

        chan = transport.accept(20)
        if chan is None:
            raise Exception("No channel")

        server.event.wait(10)
        if not server.event.is_set():
            raise Exception("No shell request")

        try:
            run = True
            while run:
                chan.send("$ ")
                command = ""
                while not command.endswith("\r"):
                    transport = chan.recv(1024)
                    # Echo input to psuedo-simulate a basic terminal
                    chan.send(transport)
                    command += transport.decode("utf-8")

                chan.send("\r\n")
                command = command.rstrip()
                handle_cmd(command, chan)

        except Exception as err:
            print('!!! Exception: {}: {}'.format(err.__class__, err))
            try:
                transport.close()
            except Exception:
                pass

    except Exception as err:
        print('!!! Exception: {}: {}'.format(err.__class__, err))
        try:
            transport.close()
        except Exception:
            pass


def start_server(port, bind):
    """Init and run the ssh server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind, port))

    except Exception as err:
        print(f"error {err}")
        raise err

    threads = []
    while True:
        try:
            sock.listen(100)
            client, addr = sock.accept()

        except Exception as err:
            print('*** Listen/accept failed: {}'.format(err))

        new_thread = threading.Thread(target=handle_connection, args=(client, addr))
        new_thread.start()
        threads.append(new_thread)

    for thread in threads:
        thread.join()


