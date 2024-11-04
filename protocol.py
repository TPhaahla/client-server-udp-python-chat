from socket import *
from typing import Dict, Optional, List, Union
import logging
from dataclasses import dataclass
import json
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client.log'),
        logging.StreamHandler()
    ]
)


@dataclass
class ServerResponse:
    """Data class for structured server responses"""
    success: bool
    data: Optional[Union[str, List[str], Dict]]
    error: Optional[str] = None
    address: Optional[tuple] = None


class ChatProtocol:
    def __init__(self, server_host: str = 'localhost', server_port: int = 12000):
        self.server_host = server_host
        self.server_port = server_port
        self.buffer_size = 2048
        self.encoding = 'utf-8'
        self.max_retries = 3
        self.timeout = 5.0
        self.socket: Optional[socket] = None
        self.username: Optional[str] = None

    def initialize_socket(self) -> None:
        """Initialize UDP socket with timeout"""
        try:
            self.socket = socket(AF_INET, SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
        except Exception as e:
            logging.error(f"Failed to initialize socket: {str(e)}")
            raise

    def send_with_retry(self, message: str) -> ServerResponse:
        """Send message to server with retry mechanism"""
        if not self.socket:
            self.initialize_socket()

        for attempt in range(self.max_retries):
            try:
                self.socket.sendto(message.encode(self.encoding),
                                   (self.server_host, self.server_port))

                # Wait for acknowledgment
                response, server_address = self.socket.recvfrom(
                    self.buffer_size)
                response_text = response.decode(self.encoding)

                if response_text == "ACK":
                    # Wait for actual response after ACK
                    response, server_address = self.socket.recvfrom(
                        self.buffer_size)
                    response_text = response.decode(self.encoding)

                    # Send acknowledgment back
                    self.socket.sendto("ACK".encode(
                        self.encoding), server_address)

                    if response_text.startswith("ERROR"):
                        _, error_message = response_text.split("|", 1)
                        return ServerResponse(False, None, error_message, server_address)

                    return ServerResponse(True, response_text, None, server_address)

            except timeout:
                logging.warning(
                    f"Attempt {attempt + 1} timed out, retrying...")
                time.sleep(min(2 ** attempt, 10))  # Exponential backoff
            except Exception as e:
                logging.error(f"Error sending message: {str(e)}")

        return ServerResponse(False, None, "Failed to communicate with server after retries")

    def connect(self, username: str, first_name: str) -> ServerResponse:
        """Connect to the chat server"""
        self.username = username
        message = f"CONNECT|{username}|{first_name}"
        response = self.send_with_retry(message)

        if response.success and response.data:
            logging.info(f"Successfully connected user: {username}")
            self._save_session(username)
        return response

    def list_users(self) -> ServerResponse:
        """Get list of online users"""
        if not self.username:
            return ServerResponse(False, None, "Not connected to server")

        message = f"LIST|{self.username}"
        response = self.send_with_retry(message)

        if response.success and response.data:
            try:
                # Parse the LIST response
                _, *users = response.data.split("|")
                return ServerResponse(True, users, None, response.address)
            except Exception as e:
                logging.error(f"Error parsing user list: {str(e)}")
                return ServerResponse(False, None, "Failed to parse user list")
        return response

    def send_message(self, recipient: str, content: str) -> ServerResponse:
        """Send message to specific user"""
        if not self.username:
            return ServerResponse(False, None, "Not connected to server")

        message = f"SEND|{self.username}|{recipient}|{content}"
        return self.send_with_retry(message)

    def retrieve_messages(self, from_user: str) -> ServerResponse:
        """Retrieve messages from specific user"""
        if not self.username:
            return ServerResponse(False, None, "Not connected to server")

        message = f"RETRIEVE|{from_user}|{self.username}"
        response = self.send_with_retry(message)

        if response.success and response.data:
            try:
                # Parse the RETRIEVE response
                parts = response.data.split("|")
                if len(parts) >= 4:
                    _, to_user, from_user, count, *messages = parts
                    return ServerResponse(True, messages, None, response.address)
            except Exception as e:
                logging.error(f"Error parsing retrieved messages: {str(e)}")
                return ServerResponse(False, None, "Failed to parse messages")
        return response

    def _save_session(self, username: str) -> None:
        """Save session information"""
        try:
            session_data = {
                "username": username,
                "last_login": datetime.now().isoformat(),
                "server": f"{self.server_host}:{self.server_port}"
            }
            with open(f"{username}_session.json", "w") as f:
                json.dump(session_data, f)
        except Exception as e:
            logging.warning(f"Failed to save session: {str(e)}")

    def close(self) -> None:
        """Clean up resources"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logging.error(f"Error closing socket: {str(e)}")
