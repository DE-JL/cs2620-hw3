import argparse
import os
import queue
import random
import socket
import threading
import time

from config import SERVER_ADDR, SERVER_PORT
from entity import Header, Message, MessageType


class Client:
    """
    A networked client implementation that communicates with a server, 
    processes incoming messages, and maintains its own logical clock.
    """

    def __init__(self, client_addr: str, client_port: int):
        """
        This class initializes a networked client that connects to a server and operates 
        with a clock-based architecture. It sets up the required networking components,
        and establishes two threads for listening to network messages and performing
        work based on those messages.
        """
        # Clock speed
        self.clock_speed = random.randint(1, 6)
        self.logical_clock = 0

        # Bind and connect the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.bind((client_addr, client_port))
        self.client_socket.connect((SERVER_ADDR, SERVER_PORT))

        # Determine the client address and port
        addr, port = self.client_socket.getsockname()
        self.addr = f"{addr}:{port}"
        print(f"Client {self.addr} initialized with clock speed: {self.clock_speed} Hz.")

        # Network message queue
        self.network_queue = queue.Queue()

        # Open the client log
        client_log_file_path = f"logs/client-{client_addr}-{client_port}.log"
        os.makedirs(os.path.dirname(client_log_file_path), exist_ok=True)
        self.client_log = open(client_log_file_path, "w")

        # Initialize listener and worker thread
        self.listener_thread = threading.Thread(target=self.listener)
        self.worker_thread = threading.Thread(target=self.worker)
        self.stop_event = threading.Event()

    def run(self):
        # Start the threads
        self.listener_thread.start()
        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        self.listener_thread.join()
        self.worker_thread.join()

    def listener(self):
        """
        Listens for incoming messages from a client socket, processes the data to unpack
        the header and the message, and subsequently places the message onto the 
        network queue. This method operates continuously in an infinite loop and is 
        designed for handling network communications in real-time.
        
        :return: None
        """
        while not self.stop_event.is_set():
            # Receive the header
            recvd = self.client_socket.recv(Header.SIZE, socket.MSG_WAITALL)
            if not recvd or len(recvd) != Header.SIZE:
                print(f"Client {self.addr} disconnected from server.")
                break

            # Unpack the header and receive the message
            header = Header.unpack(recvd)
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
        while not self.stop_event.is_set():
            try:
                message: Message = self.network_queue.get_nowait()
                self.log_recv(message)

            except queue.Empty:
                rand = random.randint(1, 10)
                if rand <= 3:
                    message = Message(source=self.addr,
                                      type=MessageType(rand),
                                      system_clock_time=time.time(),
                                      logical_clock_time=self.logical_clock)
                    self.client_socket.sendall(message.pack())

                    self.log_send(message)
                else:
                    self.log_internal()

            # Update the clock
            time.sleep(1 / self.clock_speed)
            self.logical_clock += 1

    def log_recv(self, message: Message):
        self.client_log.write("---------------- RECEIVED MESSAGE ----------------\n")
        self.client_log.write(f"{message}\n\n")
        self.client_log.flush()

    def log_send(self, message: Message):
        self.client_log.write("---------------- SENT MESSAGE ----------------\n")
        self.client_log.write(f"{message}\n\n")
        self.client_log.flush()

    def log_internal(self):
        message = Message(source=self.addr,
                          type=MessageType.INTERNAL,
                          system_clock_time=time.time(),
                          logical_clock_time=self.logical_clock)

        self.client_log.write("---------------- INTERNAL EVENT ----------------\n")
        self.client_log.write(f"{message}\n\n")
        self.client_log.flush()


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, description="Client")
    parser.add_argument("host", type=str, metavar='host', help="The host on which the server is running")
    parser.add_argument("port", type=int, metavar='port', help="The port at which the server is listening")
    args = parser.parse_args()

    # Initialize the client
    client = Client(args.host, args.port)
    client.run()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received; stopping service...")
        client.stop()


if __name__ == "__main__":
    main()
