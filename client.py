import argparse
import queue
import random
import socket
import threading
import time

from config import DEBUG
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
        self.logical_clock = 0

        # Networking
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((server_host, server_port))

        client_ip, client_port = self.client_socket.getsockname()
        self.addr = f"{client_ip}:{client_port}"

        print(f"Client {self.addr} connected to server at {server_host}:{server_port}.")
        print(f"Client {self.addr} clock speed: {self.clock_speed} Hz")

        # Network message queue
        self.network_queue = queue.Queue()

        # Open the client log
        # self.log_file = open(f"client_{self.addr}.log", "a")

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
                # TODO: process the event?

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
        # TODO
        print("receiving")
        pass

    def log_send(self, message: Message):
        # TODO
        print("sending")
        pass

    def log_internal(self):
        # TODO
        print("internal")
        pass


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
