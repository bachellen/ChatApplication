import socket
import threading

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}  # Dictionary to store connected clients {client_id: client_socket}
        self.lock = threading.Lock()  # Lock to synchronize access to clients dictionary

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Chat server started on {}:{}".format(self.host, self.port))

        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        try:
            while True:
                message = client_socket.recv(1024).decode().strip()
                if not message:
                    break

                if message.startswith("Connect"):
                    client_id = message.split()[1]
                    self.add_client(client_id, client_socket)
                elif message == "@Quit":
                    self.remove_client_by_socket(client_socket)
                    break
                elif message.startswith("Quit"):
                    client_id = message.split()[1]
                    self.remove_client(client_id)
                    break
                elif message == "@List" or message == "List":
                    client_socket.sendall(self.get_online_clients().encode())
                elif message.startswith("(") and ")" in message:
                    target_client_id, msg = message.split(")", 1)
                    self.send_message(target_client_id[1:], client_socket, msg[1:])
                else:
                    client_socket.sendall(b"Invalid command\n")
        except Exception as e:
            print("Error handling client:", e)
        finally:
            client_socket.close()

    def add_client(self, client_id, client_socket):
        with self.lock:
            self.clients[client_id] = client_socket
            print("Client {} joined".format(client_id))
            self.broadcast_online_clients()

    def remove_client(self, client_id):
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
                print("Client {} left".format(client_id))
                self.broadcast_online_clients()

    def remove_client_by_socket(self, client_socket):
        with self.lock:
            for client_id, socket in self.clients.items():
                if socket == client_socket:
                    del self.clients[client_id]
                    print("Client {} left".format(client_id))
                    self.broadcast_online_clients()
                    break

    def send_message(self, target_client_id, source_client_socket, message):
        with self.lock:
            if target_client_id in self.clients:
                target_socket = self.clients[target_client_id]
                target_socket.sendall("[{}] {}: {}".format(source_client_socket.getpeername(), source_client_socket.getpeername(), message).encode())
            else:
                source_client_socket.sendall(b"Target client is not online\n")

    def get_online_clients(self):
        with self.lock:
            return ", ".join(self.clients.keys())

    def broadcast_online_clients(self):
        online_clients = self.get_online_clients()
        with self.lock:
            for client_socket in self.clients.values():
                client_socket.sendall(("Online clients: {}\n".format(online_clients)).encode())


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8080
    server = ChatServer(HOST, PORT)
    server.start()
