import pickle
import struct

from pydantic import BaseModel
from typing import ClassVar


class Header(BaseModel):
    FORMAT: ClassVar[str] = "!I"
    SIZE: ClassVar[int] = struct.calcsize(FORMAT)

    message_size: int

    def pack(self) -> bytes:
        return struct.pack(Header.FORMAT, self.message_size)

    @staticmethod
    def unpack(data: bytes) -> "Header":
        message_size = struct.unpack_from(Header.FORMAT, data)[0]
        return Header(message_size=message_size)


class Message(BaseModel):
    source: str
    type: str
    system_clock_time: float
    logical_clock_time: int
    payload: str = ""

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
