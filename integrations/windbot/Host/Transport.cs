using System.IO;
using YGOSharp.Network.Enums;

namespace YGOSharp.Network
{
    public sealed class YGOClient
    {
        public List<byte[]> Output { get; } = new();
        public bool Closed { get; private set; }
        public void Send(BinaryWriter writer) => Output.Add(((MemoryStream)writer.BaseStream).ToArray());
        public void Send(CtosMessage message) => Send(message, Array.Empty<byte>());
        public void Send(CtosMessage message, byte value) => Send(message, new[] { value });
        public void Send(CtosMessage message, int value) => Send(message, BitConverter.GetBytes(value));
        public void Send(CtosMessage message, long value) => Send(message, BitConverter.GetBytes(value));
        private void Send(CtosMessage message, byte[] value)
        {
            byte[] result = new byte[value.Length + 1];
            result[0] = (byte)message;
            value.CopyTo(result, 1);
            Output.Add(result);
        }
        public void Close() => Closed = true;
    }
}

namespace WindBot.Game
{
    public sealed class GameClient
    {
        public YGOSharp.Network.YGOClient Connection { get; } = new();
        public int Hand = 0;
        public bool Debug = false;
        public string Dialog = "default";
        public string Deck;
        public string DeckFile;
        public bool Surrendered { get; private set; }
        public void Chat(string message, bool forced = false) { }
        public void Log(string message, int type) => Logger.WriteLine(message);
        public void Surrender() => Surrendered = true;
    }
}

namespace WindBot
{
    public static class Logger
    {
        public static void WriteLine(string message) { }
        public static void DebugWriteLine(string message) { }
        public static void WriteErrorLine(string message) => Console.Error.WriteLine(message);
    }
}
