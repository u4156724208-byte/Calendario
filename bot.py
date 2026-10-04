import os, threading
from flask import Flask
import discord
from discord.ext import commands

app = Flask(__name__)
@app.route("/")
def home(): return "OK"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    grid = (
        "```\n"
        "LUN  MAR  MER  GIO  VEN  SAB  DOM\n"
        "                 01   02   03\n"
        " 04  [05] [06]  07   08   09   10\n"
        " 11   12   13   14   15   16   17\n"
        " 18   19   20   21   22   23   24\n"
        " 25   26   27   28   29   30   31\n"
        "```"
    )
    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"Ottobre 2026\n{grid}",
        color=0x2f3136
    )
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
