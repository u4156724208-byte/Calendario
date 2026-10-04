import os, threading
import 【entity-discord¦canonical_name=discord】
from 【entity-discord¦canonical_name=discord】.ext import commands
from flask import Flask
from 【entity-discord¦canonical_name=discord】 import app_commands

app = Flask(__name__)
@app.route("/")
def home(): return "OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

intents = 【entity-discord¦canonical_name=discord】.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash syncati")
    except Exception as e:
        print(e)

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: 【entity-discord¦canonical_name=discord】.Interaction):
    grid = "```\nLUN MAR MER GIO VEN SAB DOM\n 01 02 03 04\n[05] [06] 07 08 09 10 11\n 12 13 14 15 16 17 18\n 19 20 21 22 23 24 25\n 26 27 28 29 30 31\n```"
    embed = discord.Embed(title="CALENDARIO GIOCHI", description=f"Ottobre 2026\n{grid}", color=0x2f3136)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅"))
    await interaction.response.send_message(embed=embed, view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
