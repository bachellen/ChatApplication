# Chat Application

This Chat Application enables real-time communication between multiple clients connected to a server. Clients can send messages to each other, request a list of online users, and gracefully handle connections and disconnections.

## Features

- **Real-Time Messaging:** Send and receive messages in real-time to and from other clients.
- **Dynamic User List:** Request the current list of online users.
- **Activity Monitoring:** The server monitors client activity, marking clients as inactive if they do not send messages within a specified timeframe.
- **Graceful Reconnection:** Clients can automatically attempt to reconnect to the server if the connection is lost.
- **Input Validation:** The server validates message formats and informs clients of the correct format if an invalid message is sent.

## Requirements

- Python 3.6 or higher

## Setup

1. **Clone the repository:**
   ```
   git clone https://github.com/bachellen/assignment.git
   ```
2. **Navigate to the project directory:**
   ```
   cd chat-application
   ```

## Running the Application

### Start the Server

1. Open a terminal window.
2. Run the server script with Python:
   ```
   python chatserver.py
   ```
3. The server will start and listen for incoming client connections.

### Connect as a Client

1. Open a new terminal window for each client.
2. Run the client script with Python, providing a unique client ID:
   ```
   python chatclient.py
   ```
3. Follow the on-screen prompts to interact with the chat application.

## Commands

Clients can use the following commands:

- **@Quit:** Disconnects the client from the server.
- **@List:** Requests a list of currently online clients.
- **Sending Messages:** To send a message to another client, use the format:
  ```
  (otherclientid) message-statement
  ```
  Replace `otherclientid` with the recipient's client ID and `message-statement` with your message.
