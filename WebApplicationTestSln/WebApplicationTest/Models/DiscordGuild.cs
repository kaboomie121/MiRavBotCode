namespace WebApplicationTest.Models;

public class DiscordGuild
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string Permissions { get; set; } // Discord returns this as a string-encoded bitwise integer
    public string? Icon { get; set; }
    public bool IsBotPresent { get; set; }

    // Converts the hash to a valid Discord CDN URL
    public string IconUrl => string.IsNullOrEmpty(Icon) 
        ? "https://cdn.discordapp.com/embed/avatars/0.png" // Default placeholder
        : $"https://cdn.discordapp.com/icons/{Id}/{Icon}.{(Icon.StartsWith("a_") ? "gif" : "png")}";
}

public class DashboardViewModel
{
    // The list of all servers the user has permission to manage
    public List<DiscordGuild> UserGuilds { get; set; } = new();

    // The specific server the user is currently looking at
    public DiscordGuild? SelectedGuild { get; set; }

    // ClientId is needed for the bot invite URL
    public string? ClientId { get; set; }
}