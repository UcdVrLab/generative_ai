import struct
from PIL import Image as pim
from PIL.Image import Image

from networking.serializer import ISerializer, Serializer
from datastructs.command import Command, CommandType, DirectCommand
from datastructs.states import State
from datastructs.audio import Audio
from datastructs.mesh import Mesh

type_dict = {
    "bytes" : bytes,
    "command": Command,
    "text": str,
    "int": int,
    "state": State,
    "image": Image,
    "audio": Audio,
    "mesh": Mesh
}

class BytesSerializer(ISerializer[bytes]):
    @classmethod
    def to_bytes(cls, b: bytes):
        return b
    @classmethod
    def from_bytes(cls, b: bytes):
        return b

class StringSerializer(ISerializer[str]):
    @classmethod
    def to_bytes(cls, s: str): 
        return s.encode('utf-8')
    @classmethod
    def from_bytes(cls, b: bytes): 
        return b.decode('utf-8')
        
#uses longs
class IntSerializer(ISerializer[int]):
    @classmethod
    def to_bytes(cls, i: int): return struct.pack('!q', i)
    @classmethod
    def from_bytes(cls, b: bytes): 
        return 0 if b == b'' else struct.unpack('!q', b)[0]
         
class CommandSerializer(ISerializer[Command]):
    @classmethod
    def to_bytes(cls, c: Command):
        if isinstance(c, DirectCommand):
            return c.to_bytes() + Serializer.to_bytes(c.target)
        else:
            return c.to_bytes()

    @classmethod
    def from_bytes(cls, b: bytes):
        ct = CommandType(struct.unpack('!B', b[:1])[0])
        if ct is CommandType.CANCEL or ct is CommandType.EXIT:
            return DirectCommand(ct, Serializer.from_bytes_by_name("text", b[1:]))
        else: return Command(ct)

class StateSerializer(ISerializer[State]):
    @classmethod
    def to_bytes(cls, s: State):
        return Serializer.to_bytes(s.id) + (b'\x01' if s.complete else b'\x00')
    @classmethod
    def from_bytes(cls, b: bytes):
        id = Serializer.from_bytes(int, b[:8])
        complete = True if b[8:9] == b'\x01' else False
        return State(id, complete)
    
class ImageSerializer(ISerializer[Image]):
    @classmethod
    def to_bytes(cls, image: Image):
        image_bytes = image.tobytes()
        width_bytes = Serializer.to_bytes(image.width)
        height_bytes = Serializer.to_bytes(image.height)
        return width_bytes + height_bytes + image_bytes
        
    @classmethod
    def from_bytes(cls, bytes):
        width = Serializer.from_bytes(int, bytes[:8])
        height = Serializer.from_bytes(int, bytes[8:16])
        image = pim.frombytes(mode='RGB', size=(width, height), data=bytes[16:])
        return image
    
class AudioSerializer(ISerializer[Audio]):
    @classmethod
    def to_bytes(cls, audio: Audio):
        return audio.to_bytes()
        
    @classmethod
    def from_bytes(cls, b: bytes):
        return Audio(b)

class MeshSerializer(ISerializer[Mesh]):
    @classmethod
    def to_bytes(cls, mesh: Mesh):
        return mesh.to_bytes()

    @classmethod
    def from_bytes(cls, b: bytes):
        return Mesh.from_bytes(b)