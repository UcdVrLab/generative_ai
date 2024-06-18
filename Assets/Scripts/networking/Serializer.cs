using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEngine;
using Debug = UnityEngine.Debug;
using Dummies;
using Mesh = Dummies.Mesh;

interface ISerializer<T> {
    byte[] ToBytes(T obj);
    T FromBytes(byte[] bytes);
}

class BytesSerializer : ISerializer<byte[]> {
    public byte[] ToBytes(byte[] bytes) {
        return bytes;
    }
    public byte[] FromBytes(byte[] bytes) {
        return bytes;
    }
}

class StringSerializer : ISerializer<string> {
    public byte[] ToBytes(string str) {
        return Encoding.UTF8.GetBytes(str.ToCharArray());
    }

    public string FromBytes(byte[] bytes) {
        return new(Encoding.UTF8.GetChars(bytes));
    }
}

class LongSerializer : ISerializer<long> {
    public byte[] ToBytes(long num) {
        byte[] bytes = BitConverter.GetBytes(num);
        Array.Reverse(bytes);
        return bytes;
    }

    public long FromBytes(byte[] bytes) {
        var copy = bytes.ToArray();
        Array.Reverse(copy);
        return BitConverter.ToInt64(copy, 0);
    }
}
class DummySerializer<D> : ISerializer<D> where D : Dummy, new() {
    public D FromBytes(byte[] bytes) {
        var d = new D();
        d.SetBytes(bytes);
        return d;
    }

    public byte[] ToBytes(D d) {
        return d.ToBytes();
    }
}
class CommandSerializer : ISerializer<Command> {
    public byte[] ToBytes(Command command) {
        if (command is DirectCommand dc) 
            return dc.ToBytes().Concat(Serializer.ToBytes(dc.target)).ToArray();
        else
            return command.ToBytes();
    }
    public Command FromBytes(byte[] bytes) {
        var ct = (CommandType)bytes[0];
        return ct switch {
            CommandType.CANCEL or 
            CommandType.EXIT => new DirectCommand(ct, Serializer.FromBytes<string>(bytes.Skip(1).ToArray())),
            _ => new Command(ct),
        };
    }
}

class StateSerializer : ISerializer<State> {
    public State FromBytes(byte[] bytes) {
        var id = (int)Serializer.FromBytes<long>(bytes[0..8]);
        bool complete = bytes[8] == 0x01;
        return new(id, complete);
    }

    public byte[] ToBytes(State state) {
        return Serializer.ToBytes(state.id).Concat(state.complete ? new byte[] { 0x01 } : new byte[] { 0x00 }).ToArray();
    }
}

public class UnSerializableTypeException : Exception {
    public UnSerializableTypeException(string message) : base(message){}
}
public class UnknownSerializationTypeNameException : Exception {
    public UnknownSerializationTypeNameException(string message) : base(message){}
}

public static class Serializer {
    private static readonly Dictionary<string, Type> typeDict = new() {
        { "bytes", typeof(byte[]) },
        { "text", typeof(string) },
        { "int", typeof(long) },
        { "image", typeof(Image) },
        { "audio", typeof(Audio) },
        { "mesh", typeof(Mesh) },
        { "command", typeof(Command)},
        { "state", typeof(State)}
    };
    private static readonly Dictionary<Type, object> serializers = new() {
        { typeof(byte[]), new BytesSerializer() },
        { typeof(string), new StringSerializer() },
        { typeof(int), new LongSerializer() },  //dont like this
        { typeof(long), new LongSerializer() },
        { typeof(Image), new DummySerializer<Image>() },
        { typeof(Audio), new DummySerializer<Audio>() },
        { typeof(Mesh), new DummySerializer<Mesh>() },
        { typeof(Command), new CommandSerializer() },
        { typeof(State), new StateSerializer() },
    };

    public static object TypeToSerializer(Type type) {
        var serializer = serializers.Where(p => p.Key.IsAssignableFrom(type)).Select(p => p.Value).FirstOrDefault() 
        ?? throw new UnSerializableTypeException($"Given type: {type} did not have a defined serializer");
        return serializer;
    }

    public static Type NameToType(string name) {
        if(!typeDict.ContainsKey(name)) throw new UnknownSerializationTypeNameException($"There is no known serializable type corresponding to: {name}");
        return typeDict[name];
    }

    public static string TypeToName(Type type) {
        var typ = typeDict.Where(p => p.Value.IsAssignableFrom(type)).Select(p => p.Key).FirstOrDefault() 
        ?? throw new UnSerializableTypeException($"Given type: {type} is not listed as a serializable type");
        return typ;
    }

    private static object Serialize(object serializer, object obj) {
        MethodInfo toBytesMethod = serializer.GetType().GetMethod("ToBytes");
        return toBytesMethod.Invoke(serializer, new object[] { obj });
    }

    private static object Deserialize(object serializer, byte[] bytes) {
        MethodInfo fromBytesMethod = serializer.GetType().GetMethod("FromBytes");
        return fromBytesMethod.Invoke(serializer, new object[] { bytes });
    }
    //obj to bytes
    public static byte[] ToBytes(object obj) {
        return (byte[])Serialize(TypeToSerializer(obj.GetType()), obj);
    }
    //bytes -> T using a generic type T
    public static T FromBytes<T>(byte[] bytes) {
        return (T)Deserialize(TypeToSerializer(typeof(T)), bytes);
    }
    //bytes -> obj using a type given as a parameter
    public static object FromBytes(Type type, byte[] bytes) {
        return Deserialize(TypeToSerializer(type), bytes);
    }
    //bytes -> obj using a type given as a string
    public static object FromBytes(string type, byte[] bytes) {
        return Deserialize(TypeToSerializer(NameToType(type)), bytes);
    } 
}

