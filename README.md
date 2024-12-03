# PyChat: A Simple UDP-Based Chat Application

PyChat is a lightweight chat application designed to facilitate real-time communication between users over a network. Built using the User Datagram Protocol (UDP), PyChat aims to provide a simple yet effective platform for sending and receiving messages. Despite the inherent unreliability of UDP, PyChat implements mechanisms to ensure message delivery and maintain a seamless user experience. The application consists of a server that manages user connections and message exchanges, and a client that allows users to interact with the chat system.

## Running the App Locally

To run PyChat locally, follow these steps:

1. **Clone the Repository**: Clone the project repository to your local machine.

2. **Install Dependencies**: Ensure you have Python installed on your system. No additional libraries are required as the application uses Python's standard library.

3. **Start the Server**: Navigate to the directory containing `udp_server.py` and run the server using the command:

   ```bash
   python3 udp_server.py
   ```

4. **Start the Client**: In a separate terminal, navigate to the directory containing `udp_client.py` and run the client using the command:

   ```bash
   python3 udp_client.py
   ```

5. **Interact with the Application**: Follow the on-screen instructions to connect, list users, send messages, and retrieve messages.

## Features Implemented

- **User Connection**: Users can connect to the server by providing a username and first name.
- **List Online Users**: Users can view a list of currently online users.
- **Send Messages**: Users can send messages to other connected users.
- **Retrieve Messages**: Users can retrieve messages sent to them by other users.
- **Graceful Shutdown**: The client can be gracefully shut down using signal handlers.

## Security Measures

- **Session Management**: User sessions are saved locally to ensure continuity between sessions.
- **Error Handling**: The application includes error handling to manage unexpected situations and provide feedback to users.

## Reliability with UDP

Despite using UDP, which does not guarantee message delivery, PyChat implements several mechanisms to enhance reliability:

- **Acknowledgment System**: Both the client and server use an acknowledgment system to confirm message receipt. If an acknowledgment is not received, the message is resent.
- **Retry Mechanism**: Messages are sent with a retry mechanism, attempting multiple times before reporting a failure.
- **Timeouts**: The application uses timeouts to prevent indefinite waiting for responses, allowing it to retry or handle errors appropriately.

By combining these features, PyChat provides a robust and user-friendly chat experience, even over a protocol that does not inherently ensure reliability.
