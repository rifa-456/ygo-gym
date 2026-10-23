using System.Reflection;
using WindBot.Game.AI;

namespace WindBot.Game
{
    public static class DecksManager
    {
        public record Entry(string Id, string File, string Level, Type Type);
        public static IReadOnlyList<Entry> Entries { get; } = Assembly.GetExecutingAssembly().GetTypes()
            .Where(type => !type.IsAbstract && typeof(Executor).IsAssignableFrom(type))
            .Select(type => (type, attribute: type.GetCustomAttribute<DeckAttribute>()))
            .Where(row => row.attribute != null)
            .Select(row => new Entry(row.attribute.Name, row.attribute.File, row.attribute.Level, row.type))
            .OrderBy(row => row.Id, StringComparer.Ordinal).ToArray();

        public static Executor Instantiate(GameAI ai, Duel duel, string deck)
        {
            var entry = Entries.SingleOrDefault(row => row.Id == deck)
                ?? throw new ArgumentException($"Unknown WindBot executor: {deck}");
            var executor = (Executor)Activator.CreateInstance(entry.Type, ai, duel);
            executor.Rand = new Random(Program.Seed);
            executor.Deck = entry.File;
            return executor;
        }
    }
}
