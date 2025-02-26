# Design Exercise 3: Scale Model and Logical Clocks

> [!NOTE]
>
> **Authors: Daniel Li, Rajiv Swamy**

## 2/25

### Process Structuring

- Star topology vs. $K_3$?
    - Star would be simpler, but communication would be constrained to central node.
    - $K_3$ would allow direct messaging between hosts, but more complex for each host to maintain.
        - It is more **P2P**, not entirely sure how they would "discover" each other.
    - Star should be fine because we don't care that much about network throughput in this design exercise.

### Implementation

- Have one main server handle the connections.
- Use the given starter code with Python `selector`, `accept_connection()` and `service_connection()`.
- Server needs to maintain a `hostaddr -> socket` map.
    - Actually we can just go from `hostaddr -> context` because `context.outbound` is the outgoing data buffer.

## 2/26

### Message Type

- Using `dataclass` to represent our messages.
- Messages need at the very least a few things:
    - Source address (I think we can just use `<ip_address>:<port>` here)
    - Message type (there are three)
        - Send to one host
        - Send to other host
        - Broadcast
    - Timestamp (logical clock).
- Payload is unnecessary but we can include it.

### Client Structure

- Have the client use a `queue.Queue()` network queue to store received messages.
- Listener thread will receive any messages and place them on the network queue.
- Worker thread will sleep for $\frac{1}{\text{clock speed}}$ seconds before polling the queue again.

### Server Routing

- Created an `enum` for the message type.
- Server will receive message type.
- Upon receiving a message, it will determine the host(s) to route the message to.
- The list of possible host destinations is determined by **removing** the source address from the set of addresses.
    - `SEND_ONE`: Send to the first (alphabetically sorted) host
    - `SEND_SECOND`: send to the second host
    - `BROADCAST`: sent to both hosts
