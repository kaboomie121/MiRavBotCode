using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Newtonsoft.Json;
using System.Net.Http.Headers;
using WebApplicationTest.Models;

namespace MiRavBotWebApp.Controllers;

[Authorize]
public class DashboardController : Controller
{
    private readonly IConfiguration _configuration;

    public DashboardController(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public async Task<IActionResult> Index(string? guildId)
    {
        var accessToken = await HttpContext.GetTokenAsync("access_token");

        string? botToken, clientId;

        if (bool.Parse(_configuration["Config:DevMode"]!) == true)
        {
            botToken = _configuration["DiscordDevMode:BotToken"];
            clientId = _configuration["DiscordDevMode:ClientId"];
        }
        else
        {
            botToken = _configuration["Discord:BotToken"];
            clientId = _configuration["Discord:ClientId"];
        }

        // Fetch guilds from Discord API for the User
        var allGuilds = await FetchGuildsFromDiscord(accessToken);

        // Fetch guilds from Discord API for the Bot
        var botGuilds = await FetchBotGuildsFromDiscord(botToken);
        var botGuildIds = botGuilds.Select(g => g.Id).ToHashSet();

        // Filter for Manage Server permissions and cross-reference with bot
        var manageableGuilds = allGuilds.Where(g => long.TryParse(g.Permissions, out var p) && (p & 0x20) == 0x20).ToList();

        foreach (var guild in manageableGuilds)
        {
            guild.IsBotPresent = botGuildIds.Contains(guild.Id);
        }

        var viewModel = new DashboardViewModel
        {
            UserGuilds = manageableGuilds,
            SelectedGuild = manageableGuilds.FirstOrDefault(g => g.Id == guildId),
            ClientId = clientId
        };

        return View(viewModel);
    }

    private async Task<List<DiscordGuild>> FetchGuildsFromDiscord(string? token)
    {
        if (string.IsNullOrEmpty(token)) return new List<DiscordGuild>();

        using var client = new HttpClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

        var response = await client.GetAsync("https://discord.com/api/users/@me/guilds");
        if (!response.IsSuccessStatusCode) return new List<DiscordGuild>();

        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<List<DiscordGuild>>(json) ?? new List<DiscordGuild>();
    }

    private async Task<List<DiscordGuild>> FetchBotGuildsFromDiscord(string? botToken)
    {
        if (string.IsNullOrEmpty(botToken)) return new List<DiscordGuild>();

        using var client = new HttpClient();
        // Discord API requires "Bot" prefix for bot tokens, rather than "Bearer"
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bot", botToken);

        var response = await client.GetAsync("https://discord.com/api/users/@me/guilds");
        if (!response.IsSuccessStatusCode) return new List<DiscordGuild>();

        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<List<DiscordGuild>>(json) ?? new List<DiscordGuild>();
    }
}
