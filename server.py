import argparse
import os
import selectors
import socket
import types

from config import SERVER_ADDR, SERVER_PORT
from entity import Header, Message


class Server:
    """Main server class that manages all hosts."""

    MIN_HOSTS = 3

    def __init__(self, exp_name: str):
        # Create server socket
        self.sel = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)

        # Initialize data structures for hosts
        self.host_to_ctx: dict[str, types.SimpleNamespace] = {}

        # Create the log file
        server_log_file_path = f"logs/{exp_name}/server.log"
        os.makedirs(os.path.dirname(server_log_file_path), exist_ok=True)
        self.server_log = open(server_log_file_path, "w")

    def run(self, server_addr: str, server_port: int):
        # Bind and listen on <host:port>
        self.server_socket.bind((server_addr, server_port))
        self.server_socket.listen()
        print(f"Server started at {server_addr}:{server_port}.")

        # Register the socket
        self.sel.register(self.server_socket, selectors.EVENT_READ, None)
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting.")
        finally:
            self.sel.close()
            self.server_socket.close()
            self.server_log.close()

    def accept_wrapper(self, key: selectors.SelectorKey):
        """
        Accept a new client connection and register it for reading.

        :param key: Select key.
        """
        sock = key.fileobj
        assert isinstance(sock, socket.socket)

        # Accept the connection
        conn, addr = sock.accept()
        ip, port = addr
        print(f"Accepted connection from {addr}.")

        # Set the connection to be non-blocking
        conn.setblocking(False)

        # Store a context namespace for this particular connection
        ctx = types.SimpleNamespace(addr=addr, outbound=b"")
        self.sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=ctx)
        self.host_to_ctx[f"{ip}:{port}"] = ctx

    def service_connection(self, key: selectors.SelectorKey, mask: int):
        """
        This function serves a connection.

        :param key: Connection key.
        :param mask: Mask for selecting events.
        """
        sock = key.fileobj
        ctx = key.data

        # Explicit type checking
        assert isinstance(sock, socket.socket)
        assert isinstance(ctx, types.SimpleNamespace)

        # Check if the socket is ready for reading
        if mask & selectors.EVENT_READ:
            # Receive the header
            recvd = sock.recv(Header.SIZE, socket.MSG_WAITALL)

            # Check if the client closed the connection
            if not recvd or len(recvd) != Header.SIZE:
                # Close the connection
                self.sel.unregister(sock)
                sock.close()
                print(f"Closed connection to {ctx.addr}.")
                return

            # Unpack the header and receive the payload
            header = Header.unpack(recvd)
            recvd += sock.recv(header.message_size, socket.MSG_WAITALL)

            # Handle the message
            message = Message.unpack(recvd)
            self.handle_message(message)

        # Send a response if it exists
        if mask & selectors.EVENT_WRITE:
            if ctx.outbound:
                sent = sock.send(ctx.outbound)
                ctx.outbound = ctx.outbound[sent:]

    def handle_message(self, message: Message):
        self.server_log.write("---------------- RECEIVED MESSAGE ----------------\n")
        self.server_log.write(f"{message}\n\n")

        # Order the hosts lexicographically on their addresses
        other_hosts = sorted([host for host in self.host_to_ctx if host != message.source])
        if len(other_hosts) < Server.MIN_HOSTS - 1:
            return

        match message.type:
            case "SEND_FIRST":
                destination = other_hosts[0]
                ctx = self.host_to_ctx[destination]
                ctx.outbound += message.pack()

            case "SEND_SECOND":
                destination = other_hosts[1]
                ctx = self.host_to_ctx[destination]
                ctx.outbound += message.pack()

            case "BROADCAST":
                for host in other_hosts:
                    ctx = self.host_to_ctx[host]
                    ctx.outbound += message.pack()

            case _:
                raise ValueError(f"Invalid message type: {message.type}.")


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, description="Server")
    parser.add_argument("--exp-name", type=str, required=True, metavar='name', help="The name of the experiment")
    args = parser.parse_args()

    server = Server(args.exp_name)
    server.run(SERVER_ADDR, SERVER_PORT)


if __name__ == "__main__":
    main()
