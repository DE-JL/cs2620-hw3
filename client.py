import argparse
import json
import os
import queue
import random
import socket
import threading
import time

from pydantic import BaseModel
from typing import Optional

from config import SERVER_ADDR, SERVER_PORT
from entity import Header, Message


class Event(BaseModel):
    event_type: str
    system_clock_time: float
    logical_clock_time: int
    message_queue_size: Optional[int] = None
    message: Optional[Message] = None


class Client:
    """
    A networked client implementation that communicates with a server, 
    processes incoming messages, and maintains its own logical clock.
    """

    def __init__(self,
                 client_addr: str,
                 client_port: int,
                 prob_internal: float = 0.7,
                 clock_speed: int = None,
                 exp_name: str = None):
        """
        This class initializes a networked client that connects to a server and operates 
        with a clock-based architecture. It sets up the required networking components,
        and establishes two threads for listening to network messages and performing
        work based on those messages.
        """
        # Clock speed
        if clock_speed:
            self.clock_speed = clock_speed
        else:
            self.clock_speed = random.randint(1, 6)
        self.logical_clock = 0
        self.prob_internal = prob_internal

        # Bind and connect the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.bind((client_addr, client_port))
        self.client_socket.connect((SERVER_ADDR, SERVER_PORT))

        # Determine the client address and port
        addr, port = self.client_socket.getsockname()
        self.addr = f"{addr}:{port}"
        print(f"Client {self.addr} initialized with clock speed: {self.clock_speed} Hz.")

        # Network message queue
        self.network_queue = queue.Queue()

        # Open the client log
        client_log_file_path = f"logs/{exp_name}/client-{client_addr}-{client_port}.json"
        os.makedirs(os.path.dirname(client_log_file_path), exist_ok=True)
        self.client_log = open(client_log_file_path, "w")

        # Initialize listener and worker thread
        self.listener_thread = threading.Thread(target=self.listener)
        self.worker_thread = threading.Thread(target=self.worker)
        self.stop_event = threading.Event()

        # Events list
        self.events: list[Event] = []

    def run(self):
        # Start the threads
        self.listener_thread.start()
        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        self.listener_thread.join()
        self.worker_thread.join()

        # Close the socket
        self.client_socket.close()

        # Take a dump
        json.dump([event.model_dump() for event in self.events],
                  self.client_log,
                  indent=4)
        self.client_log.close()

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
                # Check if the message queue is nonempty
                message: Message = self.network_queue.get_nowait()

                # Update the logical clock with Lamport's rule
                self.logical_clock = max(self.logical_clock, message.logical_clock_time) + 1

                self.log_recv(message)

            except queue.Empty:
                # Increment logical clock
                self.logical_clock += 1

                rand = random.random()
                if rand >= self.prob_internal:
                    choice = random.randint(1, 3)
                    message_types = ["SEND_FIRST", "SEND_SECOND", "BROADCAST"]

                    # Generate a new message and send it to the server
                    message = Message(source=self.addr,
                                      type=message_types[choice - 1],
                                      system_clock_time=time.time(),
                                      logical_clock_time=self.logical_clock)
                    self.client_socket.sendall(message.pack())

                    self.log_send(message)
                else:
                    self.log_internal()

            # Simulate clock speed
            time.sleep(1 / self.clock_speed)

    def log_recv(self, message: Message):
        self.events.append(Event(event_type="RECEIVE",
                                 system_clock_time=time.time(),
                                 logical_clock_time=self.logical_clock,
                                 message_queue_size=self.network_queue.qsize(),
                                 message=message))

    def log_send(self, message: Message):
        self.events.append(Event(event_type="SEND",
                                 system_clock_time=time.time(),
                                 logical_clock_time=self.logical_clock,
                                 message_queue_size=self.network_queue.qsize(),
                                 message=message))

    def log_internal(self):
        self.events.append(Event(event_type="INTERNAL",
                                 system_clock_time=time.time(),
                                 logical_clock_time=self.logical_clock,
                                 message_queue_size=self.network_queue.qsize()))


def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"Invalid clock speed: {value}. Must be a positive integer.")
    return ivalue


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, description="Client")
    parser.add_argument("host", type=str, metavar='host', help="The host on which the server is running")
    parser.add_argument("port", type=int, metavar='port', help="The port at which the server is listening")
    parser.add_argument("--clock-speed",
                        type=positive_int,
                        metavar='clock_speed',
                        default=None,
                        help="The clock speed of the client (default: None)")
    parser.add_argument("--exp-name",
                        type=str,
                        metavar='name',
                        default=None,
                        help="The name of the experiment (default: None)")
    parser.add_argument("--prob-internal",
                        type=float,
                        metavar='prob-internal',
                        default=0.7,
                        help="The probability of sending an internal event (default: 0.1)")
    args = parser.parse_args()

    # Initialize the client
    client = Client(args.host, args.port, args.prob_internal, args.clock_speed, args.exp_name)
    client.run()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received; stopping service...")
        client.stop()


if __name__ == "__main__":
    main()
