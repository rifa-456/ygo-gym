using System.Text.Json;
using WindBot.Game;
using YGOSharp.Network.Enums;
using YGOSharp.OCGWrapper;

namespace WindBot
{
    public static class Program
    {
        public static string AssetPath;
        internal static Random Rand = new(0);
        internal static int Seed;
        private static GameClient Client;
        private static GameBehavior Behavior;

        public static void Main()
        {
            Console.InputEncoding = new System.Text.UTF8Encoding(false);
            Console.OutputEncoding = new System.Text.UTF8Encoding(false);
            string line;
            while((line = Console.ReadLine()) != null)
            {
                try
                {
                    using var document = JsonDocument.Parse(line);
                    var request = document.RootElement;
                    var result = Dispatch(request);
                    Console.WriteLine(JsonSerializer.Serialize(new { ok = true, result }));
                }
                catch(Exception error)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { ok = false, error = error.ToString() }));
                }
            }
        }

        private static object Dispatch(JsonElement request)
        {
            switch(request.GetProperty("op").GetString())
            {
                case "catalog":
                    return DecksManager.Entries.Select(row => new { id = row.Id, file = row.File, level = row.Level }).ToArray();
                case "reset":
                    AssetPath = request.GetProperty("assets").GetString();
                    Seed = request.GetProperty("seed").GetInt32();
                    Rand = new Random(Seed);
                    NamedCardsManager.Load(request.GetProperty("cards"));
                    Client = new GameClient {
                        Deck = request.GetProperty("deck").GetString(),
                        DeckFile = request.GetProperty("deck_file").GetString()
                    };
                    Behavior = new GameBehavior(Client);
                    if(Behavior.Deck == null) throw new InvalidOperationException("WindBot could not load the selected deck");
                    return true;
                case "first":
                    if(Behavior == null) throw new InvalidOperationException("Worker has not been reset");
                    Client.Connection.Output.Clear();
                    using(var stream = new MemoryStream(new byte[] { (byte)StocMessage.SelectTp }))
                    using(var reader = new BinaryReader(stream)) Behavior.OnPacket(reader);
                    return Client.Connection.Output.Single(bytes => bytes[0] == (byte)CtosMessage.TpResult)[1] != 0;
                case "feed":
                    if(Behavior == null) throw new InvalidOperationException("Worker has not been reset");
                    Client.Connection.Output.Clear();
                    foreach(var encoded in request.GetProperty("packets").EnumerateArray())
                    {
                        var bytes = encoded.GetBytesFromBase64();
                        using var stream = new MemoryStream(bytes, false);
                        using var reader = new BinaryReader(stream);
                        Behavior.OnPacket(reader);
                    }
                    var responses = Client.Connection.Output.Where(bytes => bytes.Length > 0 && bytes[0] == (byte)CtosMessage.Response)
                        .Select(bytes => Convert.ToBase64String(bytes.AsSpan(1))).ToArray();
                    return new { responses, surrendered = Client.Surrendered, closed = Client.Connection.Closed };
                default: throw new ArgumentException("Unknown worker operation");
            }
        }
    }
}
