from socket import *
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)


class ChatServer:
    def __init__(self, port: int = 12000, buffer_size: int = 2048):
        self.port = port
        self.buffer_size = buffer_size
        self.users: List[Dict] = []
        self.messages: List[Dict] = []
        self.socket: Optional[socket] = None

        # Constants
        self.ENCODING = 'utf-8'
        self.MAX_RETRIES = 3
        self.TIMEOUT = 5.0  # seconds

    def initialize_socket(self) -> None:
        """Initialize and bind the UDP socket with timeout"""
        try:
            self.socket = socket(AF_INET, SOCK_DGRAM)
            self.socket.bind(('', self.port))
            self.socket.settimeout(self.TIMEOUT)
            logging.info(f"Server initialized on port {self.port}")
        except Exception as e:
            logging.error(f"Failed to initialize socket: {str(e)}")
            raise

    def load_data(self) -> None:
        """Load users and messages from files with error handling"""
        try:
            with open("users.txt", "r") as f:
                self.users = json.load(f)
        except FileNotFoundError:
            logging.warning(
                "Users file not found. Starting with empty users list.")
        except json.JSONDecodeError:
            logging.error(
                "Users file corrupted. Starting with empty users list.")

        try:
            with open("messages.txt", "r") as f:
                self.messages = json.load(f)
        except FileNotFoundError:
            logging.warning(
                "Messages file not found. Starting with empty messages list.")
        except json.JSONDecodeError:
            logging.error(
                "Messages file corrupted. Starting with empty messages list.")

    def save_data(self) -> None:
        """Save current state to files"""
        try:
            with open("users.txt", "w") as f:
                json.dump(self.users, f, indent=2)
            with open("messages.txt", "w") as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save data: {str(e)}")

    def send_with_ack(self, message: str, address: tuple) -> bool:
        """Send message with acknowledgment mechanism"""
        for attempt in range(self.MAX_RETRIES):
            try:
                if self.socket:
                    self.socket.sendto(message.encode(self.ENCODING), address)
                    # Wait for acknowledgment
                    ack, _ = self.socket.recvfrom(self.buffer_size)
                    if ack.decode(self.ENCODING) == "ACK":
                        return True
            except timeout:
                logging.warning(
                    f"Attempt {attempt + 1} timed out, retrying...")
            except Exception as e:
                logging.error(f"Error sending message: {str(e)}")
        return False

    def handle_connect(self, message: str, address: tuple) -> None:
        """Handle CONNECT command"""
        try:
            _, username, firstname = [part.strip()
                                      for part in message.split("|")]

            user = next(
                (u for u in self.users if u["username"] == username), None)
            if user:
                user.update({
                    "address": address,
                    "online": True,
                    "last_seen": datetime.now().isoformat()
                })
            else:
                self.users.append({
                    "username": username,
                    "firstName": firstname,
                    "address": address,
                    "online": True,
                    "isChatting": False,
                    "last_seen": datetime.now().isoformat()
                })

            response = f"CONNECT|{username}|{firstname}|True"
            self.send_with_ack(response, address)
            self.save_data()
            logging.info(f"User {username} connected successfully")

        except Exception as e:
            logging.error(f"Error handling connect: {str(e)}")
            self.send_with_ack("ERROR|Connection failed", address)

    def handle_list(self, address: tuple) -> None:
        """Handle LIST command"""
        try:
            online_users = [f"{u['username']}-Online-{u['online']}"
                            for u in self.users if u['address'] != address]

            response = "LIST|" + \
                "|".join(
                    online_users) if online_users else "LIST|Currently No Other Users Registered"
            self.send_with_ack(response, address)

        except Exception as e:
            logging.error(f"Error handling list: {str(e)}")
            self.send_with_ack("ERROR|Failed to retrieve user list", address)

    def handle_send(self, message: str, address: tuple) -> None:
        """Handle SEND command"""
        try:
            _, from_user, to_user, content = [
                part.strip() for part in message.split("|")]

            self.messages.append({
                "from": from_user,
                "to": to_user,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "retrieved": False
            })

            self.save_data()
            self.send_with_ack("SUCCESS|Message sent", address)
            logging.info(f"Message sent from {from_user} to {to_user}")

        except Exception as e:
            logging.error(f"Error handling send: {str(e)}")
            self.send_with_ack("ERROR|Failed to send message", address)

    def handle_retrieve(self, message: str, address: tuple) -> None:
        """Handle RETRIEVE command"""
        try:
            _, from_user, to_user = [part.strip()
                                     for part in message.split("|")]

            unretrieved_messages = [
                msg["content"] for msg in self.messages
                if msg["from"] == from_user and msg["to"] == to_user and not msg["retrieved"]
            ]

            # Mark messages as retrieved
            for msg in self.messages:
                if msg["from"] == from_user and msg["to"] == to_user:
                    msg["retrieved"] = True

            response = f"RETRIEVE|{to_user}|{from_user}|{len(unretrieved_messages)}|{'|'.join(unretrieved_messages)}"
            self.send_with_ack(response, address)
            self.save_data()

        except Exception as e:
            logging.error(f"Error handling retrieve: {str(e)}")
            self.send_with_ack("ERROR|Failed to retrieve messages", address)

    def run(self) -> None:
        """Main server loop"""
        self.initialize_socket()
        self.load_data()

        logging.info("Server is ready to receive messages")

        while True:
            try:
                if self.socket:
                    message, client_address = self.socket.recvfrom(
                        self.buffer_size)
                    message = message.decode(self.ENCODING)

                    # Send immediate acknowledgment
                    self.socket.sendto("ACK".encode(
                        self.ENCODING), client_address)

                    command = message.split("|")[0].strip()

                    handlers = {
                        "CONNECT": self.handle_connect,
                        "LIST": self.handle_list,
                        "SEND": self.handle_send,
                        "RETRIEVE": self.handle_retrieve
                    }

                    if command in handlers:
                        handlers[command](message, client_address)
                    else:
                        logging.warning(f"Unknown command received: {command}")
                        self.send_with_ack(
                            "ERROR|Unknown command", client_address)

            except timeout:
                continue
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")


if __name__ == "__main__":
    server = ChatServer()
    server.run()
