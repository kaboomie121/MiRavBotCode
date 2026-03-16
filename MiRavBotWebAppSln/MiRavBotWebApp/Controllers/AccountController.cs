using AspNet.Security.OAuth.Discord;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Mvc;

namespace MiRavBotWebApp.Controllers;

public class AccountController : Controller
{
    [HttpGet]
    public IActionResult Login()
    {
        // Challenge Discord. After login, Discord redirects to our middleware,
        // then the middleware redirects the user to returnUrl.
        var properties = new AuthenticationProperties
        {
            RedirectUri = Url.Action("Index", "Home")
        };

        return Challenge(properties, DiscordAuthenticationDefaults.AuthenticationScheme);
    }

    [HttpPost]
    [HttpGet]
    public async Task<IActionResult> Logout()
    {
        // Sign out of the Cookie scheme to clear the local session
        await HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        return RedirectToAction("Index", "Home");
    }
}
