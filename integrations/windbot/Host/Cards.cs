using System.Data;
using System.Text.Json;

namespace YGOSharp.OCGWrapper
{
    public static class NamedCardsManager
    {
        private static readonly Dictionary<long, NamedCard> Cards = new();
        internal static NamedCard GetCard(long id) => Cards.GetValueOrDefault(id);
        public static IList<NamedCard> GetAllCards() => Cards.Values.ToList();
        public static void Load(JsonElement rows)
        {
            Cards.Clear();
            using var table = new DataTable();
            for(int i = 0; i < 12; i++)
                table.Columns.Add($"c{i}", i >= 10 ? typeof(string) : i is 0 or 1 or 2 or 8 or 9 ? typeof(int) : typeof(long));
            foreach(var row in rows.EnumerateArray())
            {
                object[] values = new object[12];
                for(int i = 0; i < values.Length; i++)
                    values[i] = i >= 10 ? row[i].GetString() ?? "" : i is 0 or 1 or 2 or 8 or 9 ? (object)row[i].GetInt32() : row[i].GetInt64();
                table.Rows.Add(values);
            }
            using var reader = table.CreateDataReader();
            while(reader.Read())
            {
                var card = new NamedCard(reader);
                Cards[card.Id] = card;
            }
        }
    }
    internal static class CardsManager
    {
        internal static Card GetCard(int id) => NamedCardsManager.GetCard(id);
    }
}
