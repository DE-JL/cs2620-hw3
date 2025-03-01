import pickle
import struct

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


@dataclass
class Header:
    FORMAT: ClassVar[str] = "!I"
    SIZE: ClassVar[int] = struct.calcsize(FORMAT)

    message_size: int

    def pack(self) -> bytes:
        return struct.pack(Header.FORMAT, self.message_size)

    @staticmethod
    def unpack(data: bytes) -> "Header":
        message_size = struct.unpack_from(Header.FORMAT, data)[0]
        return Header(message_size=message_size)


class MessageType(Enum):
    SEND_FIRST = 1
    SEND_SECOND = 2
    BROADCAST = 3
    INTERNAL = 4


@dataclass
class Message:
    source: str
    type: MessageType
    system_clock_time: float
    logical_clock_time: int
    payload: str = ""

    def __str__(self) -> str:
        return (
            f"Message(\n"
            f"\ttype={self.type}\n"
            f"\tsource={self.source}\n"
            f"\tsystem_clock_time={self.system_clock_time}\n"
            f"\tlogical_clock_time={self.logical_clock_time}\n"
            f"\tpayload={self.payload}\n"
            f")"
        )

    def pack(self) -> bytes:
        data = pickle.dumps(self)
        header = Header(message_size=len(data))
        return header.pack() + data

    @staticmethod
    def unpack(data: bytes) -> "Message":
        header = Header.unpack(data)
        data = data[Header.SIZE:]

        assert len(data) == header.message_size
        return pickle.loads(data)
