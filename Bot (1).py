import discord
import os
from discord.ext import commands
from flask import Flask
from threading import Thread

# Web server finto per Render (evita lo spin-down)
app = Flask(__name__)
@app.route('/')
def home():
    return "Blackout404 is ONLINE!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

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

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
