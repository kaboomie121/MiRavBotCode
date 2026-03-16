using AspNet.Security.OAuth.Discord;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using System.Security.Claims;

namespace MiRavBotWebApp;

public class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add services to the container.
        builder.Services.AddControllersWithViews();

        builder.Services.AddAuthentication(options =>
        {
            // 1. Once authenticated, store the user info in a Cookie
            options.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;

            // 2. If the user isn't logged in, send them to Discord
            options.DefaultChallengeScheme = DiscordAuthenticationDefaults.AuthenticationScheme;
        })
        .AddCookie(CookieAuthenticationDefaults.AuthenticationScheme) // This was likely missing or misconfigured
        .AddDiscord(DiscordAuthenticationDefaults.AuthenticationScheme, options =>
        {
            if (bool.Parse(builder.Configuration["Config:DevMode"]!) == true)
            {
                options.ClientId = builder.Configuration["DiscordDevMode:ClientId"]!;
                options.ClientSecret = builder.Configuration["DiscordDevMode:ClientSecret"]!;
            }
            else
            {
                options.ClientId = builder.Configuration["Discord:ClientId"]!;
                options.ClientSecret = builder.Configuration["Discord:ClientSecret"]!;
            }
        
            // Crucial: The SignInScheme for Discord MUST be the Cookie scheme
            options.SignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;

            options.SaveTokens = true;

            options.Scope.Add("identify");
            options.Scope.Add("email");
            options.Scope.Add("guilds");


            // Map the avatar so your view doesn't break
            options.ClaimActions.MapJsonKey("urn:discord:avatar:hash", "avatar");
        });

        var app = builder.Build();

        // Configure the HTTP request pipeline.
        if (!app.Environment.IsDevelopment())
        {
            app.UseExceptionHandler("/Home/Error");
            // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
            app.UseHsts();
        }

        app.UseHttpsRedirection();
        app.UseRouting();

        app.UseAuthentication();
        app.UseAuthorization();

        app.MapStaticAssets();
        app.MapControllerRoute(
            name: "default",
            pattern: "{controller=Home}/{action=Index}/{id?}")
            .WithStaticAssets();

        app.Run();
    }
}
