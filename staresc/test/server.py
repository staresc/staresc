import threading
import socket

import paramiko
import paramiko.server


class StarescTestSSHServer(paramiko.server.ServerInterface):

    def __init__(self) -> None:
        self.event = threading.Event()
        super().__init__()

    def get_allowed_auths(self, username):
        return "password"
    
    def check_auth_password(self, username, password):
        if username == "user" and password == "pass":
            return paramiko.AUTH_SUCCESSFUL  # type: ignore
        else:
            return paramiko.AUTH_FAILED  # type: ignore

    def check_channel_request(self, kind, channelID):
        return paramiko.OPEN_SUCCEEDED  # type: ignore

    def get_banner(self):
        return ("Staresc Test SSH Server\n\r", "EN")

    def check_channel_exec_request(self, channel, command):
        if command == b"whoami":
            channel.send(b"user")
            channel.send_exit_status(0)

        self.event.set()
        return True
    
    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, c, t, w, h, p, ph, m):
        return True


# threading.Thread(target=start_server, args=("127.0.0.1", 9001), daemon=True).start()
def start_server(bind: str, port: int):
    host_key = paramiko.RSAKey.generate(2048)
    # create ServerInterface context object
    ctx = StarescTestSSHServer()
    # Create socket object
    sock = socket.socket()
    # bind socket to specific Port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind, port))
    # Listen for TCP connections
    sock.listen(100)

    while True:
        # accept TCP socket connection
        client, _ = sock.accept()
        server = paramiko.Transport(client)
        # Setup key
        server.add_server_key(host_key)
        # SSH start_server
        server.start_server(server=ctx)
        # Accept Auth requests
        channel = server.accept(30)
        if channel:
            # But I'm not sure what it does actually
            channel.event.wait(1)
            channel.close()


if __name__ == "__main__":
    start_server("127.0.0.1", 9001)