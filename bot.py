
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

def build_grid():
    # Ottobre 2026: 1 = giovedi (indice 3)
    days = [""]*3 + [f"{i:02d}" for i in range(1, 32)]
    rows = []
    rows.append("LUN  MAR  MER  GIO  VEN  SAB  DOM")
    for i in range(0, len(days), 7):
        week = days[i:i+7]
        line = "".join(f"{d:>4}" if d else "    " for d in week).rstrip()
        rows.append(line)
    return "```\n" + "\n".join(rows) + "\n```"

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    grid = build_grid()
    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"Ottobre 2026\n{grid}",
        color=0x2f3136
    )
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
