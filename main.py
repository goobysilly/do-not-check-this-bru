import discord
from discord.ext import commands
import aiohttp
import os
import json

# Replit-safe logging
print("🟢 Starting the bot...")

# Setup Discord intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load .env values from Replit secrets
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    raise ValueError("Missing BOT_TOKEN environment variable")

GUILD_ID = int(os.getenv("GUILD_ID", "0"))  # Default to 0 if not set
ROLE_ID = int(os.getenv("ROLE_ID", "0"))
GAMEPASS_ID = int(os.getenv("GAMEPASS_ID", "0"))

# Fail-fast check for secrets
if not TOKEN or GUILD_ID == 0 or ROLE_ID == 0 or GAMEPASS_ID == 0:
    raise RuntimeError(
        "❌ One or more environment variables are missing in Replit Secrets.")


# Ensure the JSON file exists and is valid
def load_links():
    if not os.path.exists(DATA_FILE):
        print("📁 usernames.json not found, creating new.")
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

    try:
        with open(DATA_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                print("⚠️ usernames.json was empty. Starting with empty data.")
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in usernames.json: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error loading usernames.json: {e}")
        return {}


def save_links(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("💾 usernames.json saved successfully.")
    except Exception as e:
        print(f"❌ Failed to save usernames.json: {e}")


# Load usernames
linked_usernames = load_links()


async def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                print(f"⚠️ Roblox API error (status {resp.status})")
                return None
            data = await resp.json()
            try:
                return str(data["data"][0]["id"])
            except (KeyError, IndexError):
                return None


async def get_roblox_display_name(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("name")
            return None


async def owns_gamepass(user_id, gamepass_id):
    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/GamePass/{gamepass_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return len(data.get("data", [])) > 0
            return False


@bot.event
async def on_ready():
    print(f"✅ Bot is ready: {bot.user}")


@bot.command()
async def link(ctx, roblox_username: str):
    await ctx.send("Checking if you're not scamming...")

    user_id = await get_user_id(roblox_username)
    if not user_id:
        await ctx.send("Can't find that username. Check your spelling.")
        return

    # Check if already linked
    if user_id in linked_usernames and linked_usernames[
            user_id] != ctx.author.id:
        await ctx.send("That Roblox account is already linked to someone else."
                       )
        return

    has_gamepass = await owns_gamepass(user_id, GAMEPASS_ID)
    if has_gamepass:
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(ctx.author.id)
        role = guild.get_role(ROLE_ID)

        if role and member:
            await member.add_roles(role)
            linked_usernames[user_id] = ctx.author.id
            save_links(linked_usernames)
            await ctx.send(
                f"{ctx.author.mention}, you're verified and have been given the role."
            )
        else:
            await ctx.send("Couldn't assign your role. Something went wrong.")
    else:
        await ctx.send("You don't own the required gamepass.")


@bot.command()
@commands.has_permissions(administrator=True)
async def unlink(ctx, roblox_username: str):
    user_id = await get_user_id(roblox_username)
    if not user_id:
        await ctx.send("Invalid Roblox username.")
        return

    if user_id not in linked_usernames:
        await ctx.send("This Roblox account is not linked to anyone.")
        return

    del linked_usernames[user_id]
    save_links(linked_usernames)
    await ctx.send(f"{roblox_username} has been unlinked.")


@bot.command()
async def whois(ctx, roblox_username: str):
    user_id = await get_user_id(roblox_username)
    if not user_id:
        await ctx.send("Invalid Roblox username.")
        return

    if user_id in linked_usernames:
        discord_id = linked_usernames[user_id]
        user = await bot.fetch_user(discord_id)
        await ctx.send(
            f"Roblox user `{roblox_username}` is linked to Discord user {user.mention}"
        )
    else:
        await ctx.send(f"{roblox_username} is not linked to any Discord user.")


# Run the bot safely
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ Bot failed to start: {e}")

