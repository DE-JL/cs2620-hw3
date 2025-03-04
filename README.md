# CS 2620: Scale Models and Logical Clocks

> [!NOTE]
> **Authors:** Daniel Li, Rajiv Swamy
>
> **Date:** 3/5/25

## Overview

This is a client-server application that simulates hosts (clients) running at different clock speeds.
Clients will send messages to each other.
The server acts as a central router that forwards messages from clients to other clients.
Clients send messages of the form:

```python
class MessageType(Enum):
    SEND_FIRST = 1
    SEND_SECOND = 2
    BROADCAST = 3


class Message:
    source: str
    type: MessageType
    system_clock_time: float
    logical_clock_time: int
    payload: str = ""
```

In our application, there will be _three clients_ communicating with each other.
Upon receiving a message, the server will examine the message type.

1. `SEND_FIRST`: the server will forward the message to the first of the other clients.
2. `SEND_SECOND`: the server will forward the message to the second of the other clients.
3. `BROADCAST`: the server will broadcast the message to both of the other clients.

Clients operate at randomly chosen clock speeds.
At the end of each clock cycle, a client will attempt to take a message off of its received messages queue.
If the queue is nonempty, the client will update its logical clock with the logical clock rules.
If the queue is empty, it will either send a message or log an internal event.
At the end of each event, the client will log to a file:

1. The event type.
2. The system clock time.
3. The logical clock time.

The goal of this application is to observe how clocks drift in distributed systems.
We will be looking for discrepancies (large jumps) in the system clock time and the logical clock time.


## Usage Instructions

To run the application, open a new terminal and running `python run.py`.
This will:

1. Start a server subprocess hosted at `<localhost>:8000`.
2. Start three client subprocesses hosted at `<localhost>:800{i + 1}` where `i` is the index of the client.

All logs are written to a `./logs/` directory.
Alternatively, you can run the server and clients manually (see the instructions below).

### Running the Server

To start the server, open a new terminal and run `python server.py`.
By default, the server is hosted at `<localhost>:8000`.
This can be configured in `config/config.yaml`.

### Running the Client

To start a client, open a new terminal and run `python client.py [CLIENT ADDRESS] [CLIENT PORT]`.
This will start a client process at `<CLIENT ADDRESS>:<CLIENT PORT>`.
The client will connect to the server and begin sending messages.


## Experiments

To run the experiment script, open a new terminal and run:
> `python experiment.py --exp-name [EXPERIMENT NAME] --run-time [RUN TIME]`

The experiment script will start a server process and three client processes and run it for the alloted time in seconds based on the command line arguments fed to the script. The logs will be written to the `./logs/[EXPERIMENT NAME]` directory. The clock speeds can be manually set using the `--clock-speeds` argument (e.g., `--clock-speeds 1 2 3`), by default these are manually generated . One can also dictate the probability of internal events for all the clients using the `--prob-internal` argument. The logs for each client contain a list  of event objects 

### Explanation of Logs
Inside a logs subfolder inside the `logs/` directory, one can see five files: three json files are for each of the client logs. We also write a `args.json` file which contains the command line arguments used to run the experiment. The `server.log` file contains the server logs.


## Testing
Unit tests can be found in `test_unit.py`.
To run the tests, open a new terminal and run `python -m pytest test_unit.py`.

This script runs three client-server test cases: one for each type of message that gets sent across processes.
The test then examines what got sent to the message queue(s) of the receiving client(s) and asserts that the message integrity was preserved.
We also added unit tests for verifying the correctness of our serialization methods for each of the message objects that we send over the network.
