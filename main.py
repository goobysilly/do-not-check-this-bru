import discord
from discord.ext import commands
import aiohttp
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_ID = int(os.getenv("ROLE_ID"))
GAMEPASS_ID = int(os.getenv("GAMEPASS_ID"))

async def get_user_id(username):
    url = f"https://api.roblox.com/users/get-by-username?username={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get("Id", None)

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
    print(f"Ok {bot.user}")

@bot.command()
async def link(ctx, roblox_username: str):
    await ctx.send("Checking if ur not scamming")
    user_id = await get_user_id(roblox_username)
    if not user_id:
        await ctx.send("Can't get username recheck.")
        return

    has_gamepass = await owns_gamepass(user_id, GAMEPASS_ID)
    if has_gamepass:
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(ctx.author.id)
        role = guild.get_role(ROLE_ID)
        if role and member:
            await member.add_roles(role)
            await ctx.send(f" {ctx.author.mention}, you got yo role btw")
        else:
            await ctx.send("i can't give role for some reason so if ur seeing this something bad happened")
    else:
        await ctx.send("u don't got the gamepass brodie")

bot.run(TOKEN)


