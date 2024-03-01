import socket
import threading
import time

class ChatServer:
    def __init__(self, host, port, alive_interval):
        self.host = host
        self.port = port
        self.clients = {}  # Dictionary to store connected clients {client_id: (client_socket, last_alive)}
        self.alive_interval = alive_interval
        self.lock = threading.Lock()  # Lock to synchronize access to clients dictionary

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Chat server started on {}:{}".format(self.host, self.port))

        threading.Thread(target=self.check_inactive_clients).start()

        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        try:
            message = client_socket.recv(1024).decode().strip()
            if not message.startswith("Connect"):
                client_socket.sendall(b"Invalid connection request\n")
                client_socket.close()
                return

            client_id = message.split()[1]
            self.add_client(client_id, client_socket)

            # Send alive interval to client
            client_socket.sendall(f"AliveInterval {self.alive_interval}".encode())

            while True:
                message = client_socket.recv(256).decode().strip()
                if not message:
                    break

                if message.startswith("Alive"):
                    self.update_client_alive(client_id)
                elif message.startswith("(") and ")" in message:
                    target_client_id, msg = message.split(")", 1)
                    self.send_message(target_client_id[1:], client_id, msg[1:])
                elif target_client_id == "-SERVER-":
                    self.handle_server_message(client_id, message)
                else:
                    client_socket.sendall(b"Invalid command\n")
        except Exception as e:
            print("Error handling client:", e)
        finally:
            self.remove_client(client_id)

    def add_client(self, client_id, client_socket):
        with self.lock:
            self.clients[client_id] = (client_socket, time.time())

    def remove_client(self, client_id):
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
                self.broadcast_online_clients()

    def update_client_alive(self, client_id):
        with self.lock:
            if client_id in self.clients:
                _, last_alive = self.clients[client_id]
                self.clients[client_id] = (self.clients[client_id][0], time.time())

    def check_inactive_clients(self):
        while True:
            inactive_clients = []
            current_time = time.time()
            with self.lock:
                for client_id, (_, last_alive) in self.clients.items():
                    if current_time - last_alive > self.alive_interval:
                        inactive_clients.append(client_id)

            for client_id in inactive_clients:
                self.remove_client(client_id)
                print("Client {} disconnected due to inactivity".format(client_id))

            time.sleep(self.alive_interval)

    def send_message(self, target_client_id, source_client_id, message):
        with self.lock:
            if target_client_id in self.clients:
                target_socket, _ = self.clients[target_client_id]
                target_socket.sendall(f"({source_client_id}) {message}".encode())
            else:
                self.clients[source_client_id][0].sendall(b"Target client is not online\n")

    def handle_server_message(self, client_id, message):
        # Handle messages from the server if necessary
        pass

    def get_online_clients(self):
        with self.lock:
            return ", ".join(self.clients.keys())

    def broadcast_online_clients(self):
        online_clients = self.get_online_clients()
        with self.lock:
            for client_socket, _ in self.clients.values():
                client_socket.sendall(("Online clients: {}\n".format(online_clients)).encode())


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8080
    ALIVE_INTERVAL = 60  # seconds
    server = ChatServer(HOST, PORT, ALIVE_INTERVAL)
    server.start()
