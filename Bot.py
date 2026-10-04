import discord
import os
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Blackout404 online come {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏴 Blackout404 è ONLINE!")

@bot.command()
async def blackout(ctx):
    await ctx.send("💀 BLACKOUT 404 - Sistema operativo!")

# Token da Render Environment Variable
bot.run(os.getenv("DISCORD_TOKEN"))
