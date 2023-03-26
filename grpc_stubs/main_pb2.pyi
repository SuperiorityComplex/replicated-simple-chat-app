from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HeartbeatRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class HeartbeatResponse(_message.Message):
    __slots__ = ["leader"]
    LEADER_FIELD_NUMBER: _ClassVar[int]
    leader: int
    def __init__(self, leader: _Optional[int] = ...) -> None: ...

class UpdateRequest(_message.Message):
    __slots__ = ["database"]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    database: str
    def __init__(self, database: _Optional[str] = ...) -> None: ...

class UpdateResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
