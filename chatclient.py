# chatclient.py
import socket
import threading
import sys
from time import time, sleep

class ChatClient:
    def __init__(self, host, port, client_id):
        self.MAX_MESSAGE_LENGTH = 255
        self.MAX_NAME_LENGTH = 8
        self.MAX_MESSAGE_CONTENT_LENGTH = 239
        self.host = host
        self.port = port
        self.client_id = client_id
        self.last_message_time = time() 
        self.alive_interval = 60
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.send(f"Connect {self.client_id}".encode())
        print("You will go offline if you are being inactive for 60 seconds.")
        threading.Thread(target=self.listen_for_messages).start()
        threading.Thread(target=self.conditional_keep_alive).start()

    def listen_for_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode()
                print(message)
                if message.startswith("List"):
                  print("Online clients:", message[5:])
            except OSError as e:
              print("Socket error, shutting down:", e)
              break
            except Exception as e:
              print("An unexpected error occurred:", e)
              break
    
    def ensure_connection(self):
        """Ensure the client is connected before sending a message."""
        try:
            # Attempt to send a small data packet to check connection
            self.socket.send(b'')
        except (BrokenPipeError, OSError):
            print("Reconnecting to the server...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.send(f"Connect {self.client_id}".encode())
            print("Reconnected.")

    def send(self, message):
        self.ensure_connection()
        if message.startswith("("):
            try:
                dest_id, message_content = message[1:].split(') ', 1)
            except ValueError:
                print("Invalid message format. Use '(dest_id) Your message'.")
                return

            if len(dest_id.encode()) > self.MAX_NAME_LENGTH or len(self.client_id.encode()) > self.MAX_NAME_LENGTH:
                print("Error: Destination ID or Client ID exceeds the 8 byte limit.")
                return

            # Padding the destination ID and client ID to ensure they are exactly 8 bytes
            dest_id_padded = dest_id.ljust(self.MAX_NAME_LENGTH)[:self.MAX_NAME_LENGTH]
            client_id_padded = self.client_id.ljust(self.MAX_NAME_LENGTH)[:self.MAX_NAME_LENGTH]

            # Construct the complete message for sending
            complete_message = f"{dest_id_padded}{client_id_padded}{message_content}"

            if len(complete_message.encode()) > self.MAX_MESSAGE_LENGTH:
                print("Error: Complete message exceeds the 255 byte limit.")
                return

            self.socket.send(complete_message.encode())
            self.last_message_time = time()
        else:
            # Handle non-standard messages (e.g., Alive, Quit) without padding
            if len(message.encode()) > self.MAX_MESSAGE_LENGTH:
                print("Error: Message exceeds the 255 byte limit.")
                return
            self.socket.send(message.encode())
            self.last_message_time = time()


    def conditional_keep_alive(self):
        """Checks if an "Alive" message needs to be sent based on client activity."""
        while True:
            sleep(self.alive_interval)  # Wait for the specified interval
            if time() - self.last_message_time <= self.alive_interval:
                self.send(f"Alive {self.client_id}")
            else :
                print("Your session has been marked as inactive due to prolonged inactivity. Please reconnect if you wish to continue")

            

    def close(self):
        self.send(f"@Quit")
        self.socket.close()
        print("Disconnected from the server.")
    
    def keep_alive(self):
        alive_message = f"Alive {self.client_id}"
        self.send(alive_message)
        threading.Timer(60, self.keep_alive).start()

if __name__ == "__main__":
    while True:
        client_id = input("Enter client ID: ")
        if len(client_id.encode()) <= 8:
            client = ChatClient('localhost', 8081, client_id)
            break
        else:
            print("Error: Client ID must be no more than 8 bytes.")
    

    try:
        while True:
            message = input()
            if message == "@Quit":
                client.close()
                break
            elif message.startswith("@"):
                client.send(message)
            else :
                client.send(message)

    except KeyboardInterrupt:
        client.close()
        print("Client shutdown gracefully.")
####