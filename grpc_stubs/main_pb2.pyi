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

class LeaderRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LeaderResponse(_message.Message):
    __slots__ = ["leader"]
    LEADER_FIELD_NUMBER: _ClassVar[int]
    leader: int
    def __init__(self, leader: _Optional[int] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class UpdateRequest(_message.Message):
    __slots__ = ["active_users", "database"]
    ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    active_users: str
    database: str
    def __init__(self, database: _Optional[str] = ..., active_users: _Optional[str] = ...) -> None: ...

class UpdateResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class UserRequest(_message.Message):
    __slots__ = ["action", "message", "recipient", "username"]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    action: str
    message: str
    recipient: str
    username: str
    def __init__(self, action: _Optional[str] = ..., username: _Optional[str] = ..., recipient: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class Username(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...
