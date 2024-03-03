# chatclient.py
import socket
import threading
import sys
from time import time, sleep

class ChatClient:
    def __init__(self, host, port, client_id):
        # Initialize client with server address, port, and client's unique ID.
        # Set up socket connection to the server and send initial connect message.
        self.MAX_MESSAGE_LENGTH = 255
        self.MAX_MESSAGE_LENGTH = 255
        self.MAX_NAME_LENGTH = 8
        self.MAX_MESSAGE_CONTENT_LENGTH = 239
        self.host = host
        self.port = port
        self.client_id = client_id
        self.last_message_time = time() 
        self.alive_interval = 60 # Time interval to check alive messages.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.send(f"Connect {self.client_id}".encode())
        print("You will go offline if you are being inactive for 60 seconds.")
        # Start threads for listening to messages and sending alive signals.
        threading.Thread(target=self.listen_for_messages).start()
        threading.Thread(target=self.conditional_keep_alive).start()

    def listen_for_messages(self):
        # Listen for messages from the server and handle them accordingly.
        # This includes handling segmented list of online clients.
        full_client_list = []  # Initialize an empty list to accumulate client IDs
        expecting_more = False  # Flag to track whether more list parts are expected
        while True:
            try:
                message = self.socket.recv(1024).decode()
                if message.startswith("List"):
                    #Extract the client list part from the message
                    parts = message.split(' ', 1)
                    if len(parts) > 1:
                        client_list_part = parts[1]
                        if client_list_part.endswith(' More'):
                            # If the message ends with ' More', remove it and set flag
                            client_list_part = client_list_part[:-5]  # Remove ' More'
                            expecting_more = True
                        else:
                            expecting_more = False
                    # Split the client list part into individual IDs and add them to the full list
                    full_client_list.extend(client_list_part.split())
                    if not expecting_more:
                        # If no more parts are expected, print the full list and reset for next time
                        print("Online clients:", ", ".join(full_client_list))
                        full_client_list = []  # Reset for next list
                else:
                    print(message)
            except OSError as e:
              sys.exit()
              break
            except Exception as e:
              print("An unexpected error occurred:", e)
              break
    
    def ensure_connection(self):
        """Ensure the client is connected before sending a message."""
        try:
            # Attempt to send a small data packet to check connection
            self.socket.send(b'.')
        except (BrokenPipeError, OSError):
            print("Reconnecting to the server...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.send(f"Connect {self.client_id}".encode())
            print("Reconnected.")

    def send(self, message):
    # Send a message to the server, handling different message formats.
        self.ensure_connection()
        if message.startswith("("):
        # Handling direct messages to other clients, including validation.
            try:
                dest_id, message_content = message[1:].split(') ', 1)
            except ValueError:
                print("Invalid message format. Use '(Destination ID) Your message'.")
                return
            # Validate and pad destination and source IDs.
            if len(dest_id.encode()) > self.MAX_NAME_LENGTH :
                print("Error: Destination ID exceeds the 8 byte limit.")
                return            
            if len(message_content.encode()) > self.MAX_MESSAGE_CONTENT_LENGTH:
                print("Error: Message Content exceeds the 239 byte limit.")
                return

            # Padding the destination ID and source ID to ensure they are exactly 8 bytes
            dest_id_padded = dest_id.ljust(self.MAX_NAME_LENGTH)[:self.MAX_NAME_LENGTH]
            src_id_padded = self.client_id.ljust(self.MAX_NAME_LENGTH)[:self.MAX_NAME_LENGTH]

            # Construct the complete message for sending
            complete_message = f"{dest_id_padded}{src_id_padded}{message_content}"

            self.socket.send(complete_message.encode())
            self.last_message_time = time()
        else:
            # Handle non-standard messages (e.g., Alive, Quit,List) without padding
            if len(message.encode()) > self.MAX_MESSAGE_LENGTH:
                print("Error: Message exceeds the 255 byte limit.")
                return
            self.socket.send(message.encode())
            self.last_message_time = time()


    def conditional_keep_alive(self):
        """Checks if an "Alive" message needs to be sent based on client activity."""
        inactive = False
        while True:
            sleep(self.alive_interval)  # Wait for the specified interval
            if time() - self.last_message_time <= self.alive_interval :
                self.send(f"Alive {self.client_id}")
                inactive = False
            elif time() - self.last_message_time > self.alive_interval and not inactive:
                # Mark the session as inactive if no messages have been sent recently.
                print("Your session has been marked as inactive due to prolonged inactivity. Please reconnect if you wish to continue")
                inactive = True

            

    def close(self):
        """Sends the Quit command to the server and shuts down the client application."""
        try:
            self.send(f"Quit {self.client_id}")
            self.socket.close()  # Close the socket connection
            print("Disconnected from the server. Exiting...")
        except Exception as e:
            print(f"Error during disconnection: {e}")
        finally:
            raise SystemExit  # Raise a custom exception to exit the program gracefully    
        
    def keep_alive(self):
        #Send Alive message
        alive_message = f"Alive {self.client_id}"
        self.send(alive_message)
        threading.Timer(60, self.keep_alive).start()

if __name__ == "__main__":
    # Main loop to handle client initialization and user input.
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
            elif message == "@List":
                client.send("List")
            elif message.startswith("("):
                client.send(message)
            else:            
                print("Invalid command or message format. Use one of the following formats:\n"
                "1. @Quit\n"
                "2. @List\n"
                "3. (otherclientid) message-statement")
    except KeyboardInterrupt:
        client.close()
        print("Client shutdown gracefully.")
    except SystemExit:
        sys.exit()
####