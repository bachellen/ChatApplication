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
        self.check_clients_interval = 5  # Checks for inactive clients every 5 seconds.
        print("Server listening on port", port)

    def broadcast_client_list(self):
        MAX_MESSAGE_LENGTH = 255  # Assuming this is the limit including command/type indicators
        MAX_CLIENT_ID_LENGTH = 8   # Assuming each client ID is up to 8 characters long
        # Additional characters in the message for indicating it's a part of the list and separators
        MESSAGE_OVERHEAD = 10  # This includes characters for indicating list parts, separators, etc.
        MAX_LIST_CONTENT_LENGTH = MAX_MESSAGE_LENGTH - MESSAGE_OVERHEAD

        # # Create a space-separated string of client IDs
        # client_list = " ".join(self.clients.keys())
        # Calculate how many client IDs can fit into one message
        num_ids_per_message = MAX_LIST_CONTENT_LENGTH // (MAX_CLIENT_ID_LENGTH + 1)  # +1 for the space separator
         # Split the client list into chunks
        client_ids = list(self.clients.keys())
        for i in range(0, len(client_ids), num_ids_per_message):
            chunk = client_ids[i:i + num_ids_per_message]
            message_part = " ".join(chunk)
            # Indicate it's a list message and whether more parts will follow
            more_follows = i + num_ids_per_message < len(client_ids)
            message = f"List {message_part}{' More' if more_follows else ''}"

            # Send this part of the list to all clients
            for client in self.clients.values():
                client.send(message.encode())

    def handle_list(self,client_socket ):
        MAX_MESSAGE_LENGTH = 255  # Assuming this is the limit including command/type indicators
        MAX_CLIENT_ID_LENGTH = 8   # Assuming each client ID is up to 8 characters long
        # Additional characters in the message for indicating it's a part of the list and separators
        MESSAGE_OVERHEAD = 10  # This includes characters for indicating list parts, separators, etc.
        MAX_LIST_CONTENT_LENGTH = MAX_MESSAGE_LENGTH - MESSAGE_OVERHEAD

        # # Create a space-separated string of client IDs
        # client_list = " ".join(self.clients.keys())
        # Calculate how many client IDs can fit into one message
        """Send the list of online clients to a requesting client, in parts if necessary."""
        client_list = " ".join(self.clients.keys())
        num_ids_per_message = MAX_LIST_CONTENT_LENGTH // (MAX_CLIENT_ID_LENGTH + 1)

        client_ids = list(self.clients.keys())
        for i in range(0, len(client_ids), num_ids_per_message):
            chunk = client_ids[i:i + num_ids_per_message]
            message_part = " ".join(chunk)
            more_follows = i + num_ids_per_message < len(client_ids)
            message = f"List {message_part}{' More' if more_follows else ''}"
            client_socket.send(message.encode())
   

    def handle_client(self, client_socket, client_address):
        client_id = None
        try:
            client_id = client_socket.recv(1024).decode().split()[1]  # Expecting "Connect clientid"
            self.clients[client_id] = client_socket
            self.last_seen[client_id] = time()  # Record the initial "alive" status
            print("{} connected.".format(client_id))
            self.broadcast_client_list()

            while True:
                try:
                    msg = client_socket.recv(1024).decode()
                    if msg.startswith("Quit"):
                        break
                    elif msg=="List":
                        self.handle_list(client_socket)
                        # client_socket.send(("List " + " ".join(self.clients.keys())).encode())
                    elif msg.startswith("Alive"):
                        alive_client_id = msg.split()[1]
                        if alive_client_id == client_id:  # Ensure the message is from the correct client
                            # self.last_seen[client_id] = time()  # Update last seen time
                            print(f"Received alive signal from {client_id}")
                    elif msg.startswith('.'):
                        dothing= False
                    else :
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
                    
                    self.last_seen[client_id] = time()# Update last seen time
                    if client_id not in self.clients:  # If for any reason the client was removed
                        self.clients[client_id] = client_socket
                        self.broadcast_client_list()  # Update all clients with the new list


                except Exception as e:
                    print(f"Error handling client {client_id}: {e}")
                    break

            client_socket.close()
            del self.clients[client_id]
            del self.last_seen[client_id]  # Clean up last seen entry
            self.broadcast_client_list()
            print(f"{client_id} disconnected.")
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
             if client_id in self.clients:
                client_socket.close()
                del self.clients[client_id]
                del self.last_seen[client_id] 
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
    server = ChatServer(8080)
    try:
        server.run()
    except KeyboardInterrupt:
        print("Server shutdown. Cleaning up...")
        for client in server.clients.values():
            client.close()
        server.server_socket.close()
        print("Server shutdown gracefully.")
    ######
