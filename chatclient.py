import socket
import threading
import time

class ChatClient:
    def __init__(self, server_host, server_port, client_id):
        self.server_host = server_host
        self.server_port = server_port
        self.client_id = client_id
        self.alive_interval = None
        self.socket = None

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_host, self.server_port))

        # Send connection request with client id
        self.socket.sendall(f"Connect {self.client_id}".encode())

        # Receive alive interval from server
        response = self.socket.recv(1024).decode().strip()
        if response.startswith("AliveInterval"):
            self.alive_interval = int(response.split()[1])

        threading.Thread(target=self.send_alive_messages).start()

    def send_message(self, target_client_id, message):
        self.socket.sendall(f"({target_client_id}) {message}".encode())

    def send_alive_messages(self):
        while True:
            if self.alive_interval:
                self.socket.sendall("Alive".encode())
                time.sleep(self.alive_interval)

if __name__ == "__main__":
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 8080
    CLIENT_ID = input("Enter client id: ")

    client = ChatClient(SERVER_HOST, SERVER_PORT, CLIENT_ID)
    client.start()

    while True:
        message = input("Enter message (format: (target_client_id) message): ")
        if message.lower() == "quit":
            break
        client.send_message(*message.split(maxsplit=1))

    client.socket.close()
