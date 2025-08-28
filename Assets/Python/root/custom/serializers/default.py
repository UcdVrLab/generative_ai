import struct
from PIL import Image as pim
from PIL.Image import Image

from networking.serializer import ISerializer, Serializer, FloatSerializer, Vector3Serializer
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
    "mesh": Mesh,
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




#MOG Coordinate Map - final output of multiObjectGen pipeline as a class so it can be routed by the handler to our MOGHandler multi transformation - Made by Jeric Antony 20/08/25
class MOGCoordinateMap(dict[str, tuple[float, float, float]]):
    @classmethod
    def to_bytes(cls, self) -> bytes:
        # Serialize the number of items in the dictionary (e.g. 8-byte long)
        num_items_bytes = IntSerializer.to_bytes(len(self)) 

        serialized_entries_bytes = []
        for key, vec3_tuple in self.items():
            # Get raw bytes of the item name key
            encoded_key = key.encode('utf-8')
            # Serialize the length of the key
            key_len_bytes = IntSerializer.to_bytes(len(encoded_key))
            
            # Serialize the Vector3 tuple (fixed 12 bytes)
            serialized_vec3 = Vector3Serializer.to_bytes(vec3_tuple)
            
            # Combine length of key, key bytes, and Vector3 bytes for this entry
            serialized_entries_bytes.append(key_len_bytes + encoded_key + serialized_vec3)
        
        # Combine the total number of items with all serialized entries
        return num_items_bytes + b''.join(serialized_entries_bytes)

    @classmethod
    def from_bytes(cls, b: bytes):
        offset = 0
        
        # Read the number of items
        num_items = IntSerializer.from_bytes(b[offset : offset + 8]) # IntSerializer consumes 8 bytes
        offset += 8

        result_dict: MOGCoordinateMap = MOGCoordinateMap()
        for _ in range(num_items):
            # Read the length of the current key string
            key_len = IntSerializer.from_bytes(b[offset : offset + 8])
            offset += 8
            
            # Read the actual key bytes using the obtained length
            key_bytes = b[offset : offset + key_len]
            # Deserialize the string using StringSerializer 
            key = StringSerializer.from_bytes(key_bytes)
            offset += key_len

            # Read the Vector3 tuple bytes (fixed 12 bytes)
            vec3_bytes = b[offset : offset + 12] 
            # Deserialize the Vector3 tuple
            vec3_tuple = Vector3Serializer.from_bytes(vec3_bytes)
            offset += 12

            result_dict[key] = vec3_tuple
        
        return result_dict
    
#Register MOG map serializer - Jeric Antony 20/08/25
class MOGCoordinatesMapSerializer(ISerializer[MOGCoordinateMap]):
    @classmethod
    def to_bytes(cls, objmap: MOGCoordinateMap):
        return  objmap.to_bytes()
    
    @classmethod
    def from_bytes(cls, b: bytes):
        return MOGCoordinateMap.from_bytes(b)
    
Serializer.serializers.append(MOGCoordinatesMapSerializer)
Serializer.type_dict['mog_coordinate_map'] = MOGCoordinateMap