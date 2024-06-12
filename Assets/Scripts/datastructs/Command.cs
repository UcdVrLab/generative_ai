using System.Linq;

public enum CommandType : byte {
    CANCEL = 0,
    EXIT = 1,
}

public class Command {
    public CommandType type;

    public Command(CommandType ct) {
        type = ct;
    }

    public byte[] ToBytes() {
        return new byte[] { (byte)type };
    }

    public override string ToString() {
        return $"Command: {type}";
    }
}

public class DirectCommand : Command {
    public string target;

    public DirectCommand(CommandType ct, string target) : base(ct) {
        this.target = target;
    }

    public override string ToString() {
        return $"DirectCommand: {type} for {target}";
    }
}
