from protocol import ChatProtocol
import logging
import sys
from typing import Optional
import signal
import time
from datetime import datetime


class ChatClient:
    def __init__(self):
        self.protocol = ChatProtocol()
        self.running = True
        self.setup_signal_handlers()

    def setup_signal_handlers(self) -> None:
        """Setup handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame) -> None:
        """Handle graceful shutdown"""
        print("\nShutting down client...")
        self.running = False
        self.protocol.close()
        sys.exit(0)

    def display_menu(self) -> None:
        """Display main menu options"""
        print("\n============ PyChat Menu ============")
        print("1. List Online Users")
        print("2. Send Message")
        print("3. Check Messages")
        print("4. Exit")
        print("====================================")

    def handle_user_list(self) -> None:
        """Handle listing online users"""
        response = self.protocol.list_users()
        if response.success and response.data:
            print("\nOnline Users:")
            for user in response.data:
                username, status, online = user.split("-")
                status_icon = "🟢" if online.lower() == "true" else "⚪"
                print(f"{status_icon} {username}")
        else:
            print(f"Error: {response.error or 'Failed to retrieve user list'}")

    def handle_send_message(self) -> None:
        """Handle sending a message"""
        recipient = input("Enter recipient username: ").strip()
        if not recipient:
            print("Invalid recipient username")
            return

        print("Enter your message (press Ctrl+D or Ctrl+Z to finish):")
        message_lines = []
        try:
            while True:
                line = input()
                message_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        message = "\n".join(message_lines)
        if message.strip():
            response = self.protocol.send_message(recipient, message)
            if response.success:
                print("Message sent successfully!")
            else:
                print(f"Failed to send message: {response.error}")

    def handle_check_messages(self) -> None:
        """Handle checking messages"""
        print("\n======= Messages =======")
        print("1. Retrieve Messages")
        print("2. Return to Main Menu")
        print("=======================")

        try:
            choice = int(input("Choose an option: "))
            if choice == 1:
                sender = input("Enter sender's username: ").strip()
                if sender:
                    response = self.protocol.retrieve_messages(sender)
                    if response.success and response.data:
                        print(f"\nMessages from {sender}:")
                        for idx, msg in enumerate(response.data, 1):
                            print(f"\n--- Message {idx} ---")
                            print(
                                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"Content: {msg}")
                    else:
                        print(
                            "No new messages" if not response.error else f"Error: {response.error}")
            elif choice != 2:
                print("Invalid option")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def connect(self) -> bool:
        """Handle user connection"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                username = input("Enter username: ").strip()
                if not username:
                    print("Username cannot be empty")
                    continue

                first_name = input("Enter your first name: ").strip()
                if not first_name:
                    print("First name cannot be empty")
                    continue

                response = self.protocol.connect(username, first_name)
                if response.success:
                    print(
                        f"Welcome {first_name}! You are now connected to PyChat.")
                    return True
                else:
                    print(f"Connection failed: {response.error}")
                    if attempt < max_attempts - 1:
                        print(f"Retrying... ({attempt + 1}/{max_attempts})")
                        time.sleep(1)
            except Exception as e:
                logging.error(f"Error during connection: {str(e)}")
                if attempt < max_attempts - 1:
                    print("An error occurred. Retrying...")
                    time.sleep(1)

        print("Failed to connect after multiple attempts")
        return False

    def run(self) -> None:
        """Main client loop"""
        print("============Welcome To PyChat=============")

        if not self.connect():
            return

        while self.running:
            try:
                self.display_menu()
                choice = input("Enter your choice (1-4): ").strip()

                if choice == "1":
                    self.handle_user_list()
                elif choice == "2":
                    self.handle_send_message()
                elif choice == "3":
                    self.handle_check_messages()
                elif choice == "4":
                    print("Thank you for using PyChat!")
                    self.handle_shutdown(None, None)
                else:
                    print("Invalid option. Please try again.")

            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                print("An error occurred. Please try again.")


if __name__ == "__main__":
    client = ChatClient()
    client.run()
