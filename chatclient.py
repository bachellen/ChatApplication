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
        print("You will be offline if you are being inactive for 60 seconds.")
        threading.Thread(target=self.listen_for_messages).start()
        threading.Thread(target=self.conditional_keep_alive).start()

    def listen_for_messages(self):
        while True:
            message = self.socket.recv(1024).decode()
            print(message)
            if message.startswith("List"):
                print("Online clients:", message[5:])

    def send(self, message):
        
        
        if message.startswith("("):
              # Splitting the message into destination and message content
            parts = message.split(' ', 1)

            if len(parts) != 2:
                print("Invalid message format. Please provide a message in the format '(dest_id) message'.")
                return

            dest_id = parts[0].strip("()")  # Extracting the destination ID
            message = parts[1]

            if len(dest_id) > self.MAX_NAME_LENGTH:
                print(f"Invalid destination ID. The destination ID cannot exceed {self.MAX_NAME_LENGTH} characters.")
                return

            if len(message) > self.MAX_MESSAGE_CONTENT_LENGTH:
                print(f"Invalid message. The message content cannot exceed {self.MAX_MESSAGE_CONTENT_LENGTH} characters.")
                return

    # Padding the destination ID if it is less than 8 bytes
            padded_dest_id = dest_id.ljust(self.MAX_NAME_LENGTH)[:self.MAX_NAME_LENGTH]

    # Trimming the message content if it exceeds 239 bytes
            trimmed_message = message[:self.MAX_MESSAGE_CONTENT_LENGTH]

    # Constructing the complete message string
            complete_message = padded_dest_id + self.client_id +" "+ trimmed_message + "\0"
            message= complete_message

    # Sending the message
    # Your implementation to send the message goes here
            print(f"Sending message: {message}")


        self.socket.send(message.encode())
        self.last_message_time = time()  # Update the last message time

    def conditional_keep_alive(self):
        """Checks if an "Alive" message needs to be sent based on client activity."""
        while True:
            sleep(self.alive_interval)  # Wait for the specified interval
            if time() - self.last_message_time <= self.alive_interval:
                self.send(f"Alive {self.client_id}")
            else :
                print("Your session is inactive")
                self.close()

            

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
            client = ChatClient('localhost', 8080, client_id)
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

            # else: 
            #     print ("format")
    except KeyboardInterrupt:
        client.close()
####