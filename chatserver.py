# chatserver.py
import socket
import threading
import sys
from time import time
class ChatServer:
    def __init__(self, port):
        self.host = 'localhost'
        self.port = port
        self.clients = {}
        self.last_seen = {}  # Keep track of when we last saw a client alive
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.check_clients_interval = 30  # Interval for checking inactive clients in seconds
        print("Server listening on port", port)

    def broadcast_client_list(self):
        client_list = " ".join(self.clients.keys())
        for client in self.clients.values():
            client.send(("List " + client_list).encode())

    def handle_client(self, client_socket, client_address):
        client_id = client_socket.recv(1024).decode().split()[1]  # Expecting "Connect clientid"
        self.clients[client_id] = client_socket
        self.last_seen[client_id] = time()  # Record the initial "alive" status
        print("{} connected.".format(client_id))
        self.broadcast_client_list()

        while True:
            try:
                msg = client_socket.recv(1024).decode()
                if msg.startswith("@Quit"):
                    break
                elif msg.startswith("@List"):
                    client_socket.send(("List " + " ".join(self.clients.keys())).encode())
                elif msg.startswith("Alive "):
                    alive_client_id = msg.split()[1]
                    if alive_client_id == client_id:  # Ensure the message is from the correct client
                        self.last_seen[client_id] = time()  # Update last seen time
                        print(f"Received alive signal from {client_id}")
                else:
                    # Assuming the first 16 bytes are dest_id (8 bytes) and src_id (8 bytes), both padded
                    dest_id_padded = msg[:8].strip()
                    src_id_padded = msg[8:16].strip()
                    message_content = msg[16:]  # The actual message content starts after the first 16 bytes

                    if dest_id_padded in self.clients:
                        # Forward the message, now including the source ID for context
                        formatted_message = f"From {src_id_padded}: {message_content}"
                        self.clients[dest_id_padded].send(formatted_message.encode())
                    else:
                        client_socket.send(f"{dest_id_padded} is offline.".encode())
                
                self.last_seen[client_id] = time()
                if client_id not in self.clients:  # If for any reason the client was removed
                    self.clients[client_id] = client_socket
                    self.broadcast_client_list()  # Update all clients with the new list


            except Exception as e:
                print(f"Error with client {client_id}: {e}")
                break

        client_socket.close()
        del self.clients[client_id]
        del self.last_seen[client_id]  # Clean up last seen entry

        self.broadcast_client_list()
        print(f"{client_id} disconnected.")

    def start_periodic_client_check(self):
        threading.Timer(self.check_clients_interval, self.start_periodic_client_check).start()
        self.remove_inactive_clients()

    def remove_inactive_clients(self):
        current_time = time()
        inactive_clients = [client_id for client_id, last_seen in self.last_seen.items() if current_time - last_seen > 60]
        
        for client_id in inactive_clients:
            print(f"Removing inactive client: {client_id}")
            del self.clients[client_id]
            del self.last_seen[client_id]
        
        if inactive_clients:
            self.broadcast_client_list()

    def run(self):
        self.start_periodic_client_check()
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
        except KeyboardInterrupt:
            print("Server shutting down.")
            self.server_socket.close()
            sys.exit()

if __name__ == "__main__":
    ChatServer(8081).run()
    ######
