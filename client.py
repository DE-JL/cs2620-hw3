import queue
import random
import socket
import threading
import time

from entity import Header, Message, MessageType


class Client:
    """
    A networked client implementation that communicates with a server, 
    processes incoming messages, and maintains its own logical clock.
    """

    def __init__(self, server_host: str, server_port: int):
        """
        This class initializes a networked client that connects to a server and operates 
        with a clock-based architecture. It sets up the required networking components,
        and establishes two threads for listening to network messages and performing
        work based on those messages.
        """
        # Clock speed
        self.clock_speed = random.randint(1, 6)
        self.clock = 0

        # Networking
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((server_host, server_port))

        client_ip, client_port = self.client_socket.getsockname()
        self.addr = f"{client_ip}:{client_port}"

        # Network message queue
        self.network_queue = queue.Queue()

        # Open the client log
        self.log_file = open(f"client_{self.addr}.log", "a")

        # Start the threads
        self.listener_thread = threading.Thread(target=self.listener)
        self.worker_thread = threading.Thread(target=self.worker)
        self.listener_thread.start()
        self.worker_thread.start()

    def listener(self):
        """
        Listens for incoming messages from a client socket, processes the data to unpack
        the header and the message, and subsequently places the message onto the 
        network queue. This method operates continuously in an infinite loop and is 
        designed for handling network communications in real-time.
        
        :return: None
        """
        while True:
            # Receive the header
            recvd = self.client_socket.recv(Header.SIZE)
            header = Header.unpack(recvd)

            # Receive the message
            recvd += self.client_socket.recv(header.message_size)
            message = Message.unpack(recvd)

            # Place it on the network queue
            self.network_queue.put(message)

    def worker(self):
        """
        Processes messages and simulates network activity in a loop.

        The worker function continuously runs in an infinite loop, checking for incoming 
        messages from a shared network queue and processing those messages if available. 
        If the queue is empty, the function randomly determines whether to send a new 
        message or log an internal action, simulating network activity. 

        Additionally, the function updates an internal clock on each iteration, ensuring 
        time progresses in accordance with the defined clock speed.

        :return: None
        """
        while True:
            try:
                message: Message = self.network_queue.get_nowait()
                # TODO: process the event?

                self.log_recv(message)

            except queue.Empty:
                rand = random.randint(1, 10)
                if rand <= 3:
                    message = Message(source=self.addr,
                                      type=MessageType(rand),
                                      timestamp=self.clock)
                    self.client_socket.sendall(message.pack())

                    self.log_send(message)
                else:
                    self.log_internal()

            # Update the clock
            time.sleep(1 / self.clock_speed)
            self.clock += 1

    def log_recv(self, message: Message):
        # TODO
        pass

    def log_send(self, message: Message):
        # TODO
        pass

    def log_internal(self):
        # TODO
        pass


def main():
    pass


if __name__ == "__main__":
    main()
