from enum import IntEnum
import struct

class CommandType(IntEnum):
    CANCEL = 0
    EXIT = 1

class Command:
    def __init__(self, ct: CommandType):
        self.type = ct
    def to_bytes(self):
        return struct.pack('!B', self.type.value)
    def __str__(self) -> str:
        return "CANCEL" if self.type == CommandType.CANCEL else "EXIT"

class DirectCommand(Command):
    def __init__(self, ct: CommandType, target: str):
        Command.__init__(self, ct)
        self.target = target

    def __str__(self) -> str:
        return super().__str__() + f" for {self.target}"