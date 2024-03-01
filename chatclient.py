import socket
import threading
import time
import sys

class ChatClient:
    def __init__(self, server_host, server_port, client_id):
        self.server_host = server_host
        self.server_port = server_port
        self.client_id = client_id
        self.alive_interval = None
        self.socket = None

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))

            # Send connection request with client id
            self.socket.sendall(f"Connect {self.client_id}".encode())

            # Receive alive interval from server
            response = self.socket.recv(1024).decode().strip()
            if response.startswith("AliveInterval"):
                self.alive_interval = int(response.split()[1])

            threading.Thread(target=self.send_alive_messages).start()

            self.receive_messages()
        except ConnectionError:
            print("Disconnected from server.")
            sys.exit(1)

    def send_message(self, target_client_id, message):
        self.socket.sendall(f"(-SERVER-) ({target_client_id}) {message}".encode())

    def send_alive_messages(self):
        while True:
            if self.alive_interval:
                self.socket.sendall("(-SERVER-) Alive".encode())
                time.sleep(self.alive_interval)

    def receive_messages(self):
        while True:
            try:
                message = input("Enter message (format: (target_client_id) message): ")
                if message.lower() == "@quit":
                    self.socket.sendall("@Quit".encode())
                    break
                target_client_id, msg = message.split(maxsplit=1)
                self.send_message(target_client_id, msg)
            except ConnectionError:
                print("Disconnected from server.")
                break

if __name__ == "__main__":
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 8080
    CLIENT_ID = input("Enter client id: ")

    client = ChatClient(SERVER_HOST, SERVER_PORT, CLIENT_ID)
    client.start()
