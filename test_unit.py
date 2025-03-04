import client
import server
import threading
import time

from config import SERVER_ADDR, SERVER_PORT
from entity import Header, Message


def setup():
    # Create a server and connect all the clients to the server
    svr = server.Server("unit_tests")
    server_thread = threading.Thread(target=svr.run, args=(SERVER_ADDR, SERVER_PORT))
    server_thread.start()
    print("Server started.")
    time.sleep(1)

    # Initialize the three clients
    clt1 = client.Client("localhost", 8001, 1, 1, "unit_tests")
    clt2 = client.Client("localhost", 8002, 1, 1, "unit_tests")
    clt3 = client.Client("localhost", 8003, 1, 1, "unit_tests")

    # Start listening
    clt1.listener_thread.start()
    clt2.listener_thread.start()
    clt3.listener_thread.start()

    return svr, clt1, clt2, clt3


def shutdown(svr: server.Server, clt1: client.Client, clt2: client.Client, clt3: client.Client):
    """Stop the server and clients."""
    svr.stop()
    print("Server stopped.")
    time.sleep(1)

    # Stop the client threads
    clt1.listener_thread.join()
    clt2.listener_thread.join()
    clt3.listener_thread.join()

    # Close the client sockets
    clt1.client_socket.close()
    clt2.client_socket.close()
    clt3.client_socket.close()
    print("Clients stopped.")


def test_broadcast():
    """Testing broadcast functionality."""
    svr, clt1, clt2, clt3 = setup()

    # Generate a new message and send it to the server
    msg1 = Message(source="127.0.0.1:8001",
                   type="BROADCAST",
                   system_clock_time=0,
                   logical_clock_time=0)
    clt1.client_socket.sendall(msg1.pack())
    time.sleep(1)

    # Assert the network queue sizes
    assert clt1.network_queue.qsize() == 0
    assert clt2.network_queue.qsize() == 1
    assert clt3.network_queue.qsize() == 1

    # Get the messages
    msg2 = clt2.network_queue.get()
    msg3 = clt3.network_queue.get()
    assert msg1 == msg2
    assert msg1 == msg3

    # Shutdown the server and clients
    shutdown(svr, clt1, clt2, clt3)


def test_send_first():
    """Testing send one functionality."""
    svr, clt1, clt2, clt3 = setup()

    # Generate a new message and send it to the server
    msg1 = Message(source="127.0.0.1:8001",
                   type="SEND_FIRST",
                   system_clock_time=0,
                   logical_clock_time=0)
    clt1.client_socket.sendall(msg1.pack())
    time.sleep(1)

    # Assert the network queue sizes
    assert clt1.network_queue.qsize() == 0
    assert clt2.network_queue.qsize() == 1
    assert clt3.network_queue.qsize() == 0

    # Get the message
    msg2 = clt2.network_queue.get()
    assert msg1 == msg2

    # Shutdown the server and clients
    shutdown(svr, clt1, clt2, clt3)


def test_send_second():
    """Testing send second functionality."""
    svr, clt1, clt2, clt3 = setup()

    # Generate a new message and send it to the server
    msg1 = Message(source="127.0.0.1:8001",
                   type="SEND_SECOND",
                   system_clock_time=0,
                   logical_clock_time=0)
    clt1.client_socket.sendall(msg1.pack())
    time.sleep(1)

    # Assert the network queue sizes
    assert clt1.network_queue.qsize() == 0
    assert clt2.network_queue.qsize() == 0
    assert clt3.network_queue.qsize() == 1

    # Get the message
    msg3 = clt3.network_queue.get()
    assert msg1 == msg3

    # Shutdown the server and clients
    shutdown(svr, clt1, clt2, clt3)


def test_header():
    header1 = Header(message_size=2620)
    header2 = Header(message_size=2621)

    assert header1 == Header.unpack(header1.pack())
    assert header2 == Header.unpack(header2.pack())
    assert header1 != header2


def test_message():
    msg1 = Message(source="host1",
                   type="t1",
                   system_clock_time=0,
                   logical_clock_time=0,
                   payload="hello world")
    msg2 = Message(source="host1",
                   type="t1",
                   system_clock_time=0,
                   logical_clock_time=0,
                   payload="hello world!")

    assert msg1 == Message.unpack(msg1.pack())
    assert msg2 == Message.unpack(msg2.pack())
    assert msg1 != msg2


def main():
    # Client-server unit tests
    test_broadcast()
    test_send_first()
    test_send_second()

    # Entity unit tests
    test_header()
    test_message()


if __name__ == "__main__":
    main()
