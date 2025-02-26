import selectors
import socket
import types

from config import DEBUG, LOCALHOST, SERVER_PORT
from entity import Header, Message, MessageType


class Server:
    """Main server class that manages all hosts."""

    MIN_HOSTS = 3

    def __init__(self):
        # Create server socket
        self.sel = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)

        # Initialize data structures for hosts
        self.host_to_ctx: dict[str, types.SimpleNamespace] = {}

    def run(self, host: str, port: int):
        # Bind and listen on <host:port>
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server listening on {host}:{port}")

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

    def accept_wrapper(self, key: selectors.SelectorKey):
        """
        Accept a new client connection and register it for reading.

        :param key: Select key.
        """
        sock = key.fileobj
        assert isinstance(sock, socket.socket)

        # Accept the connection
        conn, addr = sock.accept()
        print(f"Accepted client connection from: {addr}")

        # Set the connection to be non-blocking
        conn.setblocking(False)

        # Store a context namespace for this particular connection
        ctx = types.SimpleNamespace(addr=addr, outbound=b"")
        self.sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=ctx)
        self.host_to_ctx[addr] = ctx

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
                print(f"Closed connection to {ctx.addr}")
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
        if DEBUG:
            print(f"Received message: {message}")

        other_hosts = sorted([host for host in self.host_to_ctx if host != message.source])
        if len(other_hosts) < Server.MIN_HOSTS:
            return

        match message.type:
            case MessageType.SEND_FIRST:
                destination = other_hosts[0]
                ctx = self.host_to_ctx[destination]
                ctx.outbound += message.pack()

            case MessageType.SEND_SECOND:
                destination = other_hosts[1]
                ctx = self.host_to_ctx[destination]
                ctx.outbound += message.pack()

            case MessageType.BROADCAST:
                for host in other_hosts:
                    ctx = self.host_to_ctx[host]
                    ctx.outbound += message.pack()

            case _:
                raise ValueError(f"Invalid message type: {message.type}")

    def log(self):
        """Utility function that logs the state of the server."""
        print("\n-------------------------------- SERVER STATE --------------------------------")
        print(f"HOSTS: {self.host_to_ctx.keys()}")
        print("------------------------------------------------------------------------------\n")


def main():
    server = Server()
    server.run(LOCALHOST, SERVER_PORT)


if __name__ == "__main__":
    main()
