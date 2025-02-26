# Design Exercise 3: Scale Model and Logical Clocks

> [!NOTE]
>
> **Authors: Daniel Li, Rajiv Swamy**

## 2/25

### Process Structuring

- Star topology vs. $K_3$?
    - Star would be much simpler, but communication would be constrained to central node.
    - $K_3$ would low direct messaging between hosts, but more complex for each host to maintain.
        - It is more **P2P**, not entirely sure how they would "discover" each other.
    - Star should be fine because we don't care that much about network throughput in this design exercise.

### Implementation

- Have one main server handle the connections.
- Use the given starter code with Python `selector`, `accept_connection()` and `service_connection()`.
- Server needs to maintain a `hostaddr -> socket` map.
    - Actually we can just go from `hostaddr -> context` because `context.outbound` is the outgoing data buffer.

## 2/26

### Implementation

- Using `dataclass` to represent our messages.
- Messages need at the very least a few things:
    - Source address (I think we can just use `<ip_address>:<port>` here)
    - Message type (there are three)
        - Send to one host
        - Send to other host
        - Broadcast
    - Timestamp (logical clock).
- Payload is unnecessary but we can include it.
