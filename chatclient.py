# chatclient.py
import socket
import threading
import sys
from time import time, sleep

class ChatClient:
    def __init__(self, host, port, client_id):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.last_message_time = time() 
        self.alive_interval = 60
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.send(f"Connect {self.client_id}".encode())
        threading.Thread(target=self.listen_for_messages).start()
        threading.Thread(target=self.conditional_keep_alive).start()

    def listen_for_messages(self):
        while True:
            message = self.socket.recv(1024).decode()
            print(message)
            if message.startswith("List"):
                print("Online clients:", message[5:])

    def send(self, message):
            # Assuming the message is already formatted with destination and source names
        if len(message.encode()) > 255:  # Check the byte length, not just character count
           print("Error: Message exceeds the 255 byte limit and was not sent.")
        else:
            self.socket.send(message.encode())
            self.last_message_time = time()  # Update the last message time

    def conditional_keep_alive(self):
        """Checks if an "Alive" message needs to be sent based on client activity."""
        while True:
            sleep(self.alive_interval)  # Wait for the specified interval
            if time() - self.last_message_time <= self.alive_interval:
                self.send(f"Alive {self.client_id}")
            else :
                print("Your session inactive")
                self.close()

            

    def close(self):
        self.send(f"@Quit")
        self.socket.close()
        print("Disconnected from the server.")
    
    def keep_alive(self):
        """Send alive signal every 60 seconds."""
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
            else:
                client.send(f"({message[:8]}) {message[9:]}")
    except KeyboardInterrupt:
        client.close()
