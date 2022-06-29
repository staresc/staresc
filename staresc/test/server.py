import paramiko
import socket
import threading


class StarescTestSSHServer(paramiko.server.ServerInterface):

    def __init__(self) -> None:
        self.event = threading.Event()
        super().__init__()

    def get_allowed_auths(self, username):
        return "password"
    
    def check_auth_password(self, username, password):
        if username == "user" and password == "pass":
            return paramiko.AUTH_SUCCESSFUL
        else:
            return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, channelID):
        return paramiko.OPEN_SUCCEEDED

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
    print("server started")
    host_key = paramiko.RSAKey.generate(2048)
    ctx = StarescTestSSHServer()  # create ServerInterface context object
    sock = socket.socket()  # Create socket object
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind, port))  # bind socket to specific Port
    sock.listen(100)  # Listen for TCP connections

    while True:
        client, _ = sock.accept()  # accept TCP socket connection
        server = paramiko.Transport(client)
        server.add_server_key(host_key)  # Setup key
        server.start_server(server=ctx)  # SSH start_server
        channel = server.accept(30)  # Accept Auth requests
        if channel:
            channel.event.wait(1)  # but I'm not sure what it does actually
            channel.close()
