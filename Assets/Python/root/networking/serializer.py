from typing import TypeVar, Generic, Type
from types import ModuleType
import inspect
import struct

T = TypeVar('T')

class ISerializer(Generic[T]):
    @classmethod
    def to_bytes(cls, t: T) -> bytes: 
        raise NotImplementedError("Serializer must implement to_bytes method")
    
    @classmethod
    def from_bytes(cls, b: bytes) -> T: 
        raise NotImplementedError("Serializer must implement from_bytes method")
    
    @classmethod
    def get_generic_type(cls) -> TypeVar:
        return cls.__orig_bases__[0].__args__[0]

class SerializationException(Exception):
    pass

class Serializer:
    type_dict: dict[str, Type] = {}
    serializers: list[ISerializer] = []

    @classmethod
    def isSerializer(cls, obj) -> bool:
        return inspect.isclass(obj) and issubclass(obj, ISerializer) and obj != ISerializer
    
    @classmethod
    def isTypeDictionary(cls, obj) -> bool:
        return isinstance(obj, dict) and all(isinstance(key, str) and isinstance(val, type) for key, val in obj.items())

    @classmethod
    def load_serializers_from_module(cls, module: ModuleType):
        members = inspect.getmembers(module)
        cls.serializers += [obj for _, obj in members if Serializer.isSerializer(obj)]
        new_type_dict: dict[str, Type] = next((obj for _, obj in members if Serializer.isTypeDictionary(obj)), {})
        cls.type_dict = cls.type_dict | new_type_dict

    @classmethod
    def name_to_type(cls, name: str) -> Type[T]:
        if name in cls.type_dict:
            return cls.type_dict[name]
        else:
            raise SerializationException(f"There is no known serializable type corresponding to: '{name}'")

    @classmethod
    def type_to_name(cls, typ: Type[T]) -> str:
        name = next((k for k, v in cls.type_dict.items() if issubclass(typ, v)), None)
        if name:
            return name
        else:
            raise SerializationException(f"Given type: '{typ}' is not listed as a serializable type")

    @classmethod
    def type_to_serializer(cls, typ: Type[T]) -> ISerializer[T]:
        serializer = next((s for s in cls.serializers if issubclass(typ, s.get_generic_type())), None)
        if serializer:
            return serializer
        else:
            raise SerializationException(f"Given type: '{typ}' did not have a defined serializer")

    @classmethod
    def to_bytes(cls, obj):
        serializer = cls.type_to_serializer(type(obj))
        return serializer.to_bytes(obj)

    @classmethod
    def from_bytes(cls, typ: Type[T], b: bytes) -> T:
        serializer = cls.type_to_serializer(typ)
        return serializer.from_bytes(b)

    @classmethod
    def from_bytes_by_name(cls, type_name: str, b: bytes):
        typ = cls.name_to_type(type_name)
        return cls.from_bytes(typ, b)

# Define serializer for float
class FloatSerializer(ISerializer[float]):
    @classmethod
    def to_bytes(cls, t: float) -> bytes:
        return struct.pack('f', t)  # Pack float into bytes
    
    @classmethod
    def from_bytes(cls, b: bytes) -> float:
        return struct.unpack('f', b)[0]  # Unpack bytes into float

# Register float serializer
Serializer.serializers.append(FloatSerializer)
Serializer.type_dict['float'] = float
