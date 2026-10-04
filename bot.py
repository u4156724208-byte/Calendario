import discord
from discord import app_commands
import os
import threading
from flask import Flask
from datetime import datetime

# --- Mini web server per far contento Render Web Service ---
app = Flask(__name__)
@app.route("/")
def home():
    return "Calendario Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
# -----------------------------------------------------------

intents = discord.Intents.default()
bot = discord.ext.commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizzati {len(synced)} comandi")
    except Exception as e:
        print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    grid = "```\nLUN  MAR  MER  GIO  VEN  SAB  DOM\n"
    grid += "               01   02   03   04\n"
    grid += "[05] [06]  07   08   09   10   11\n"
    grid += " 12   13   14   15   16   17   18\n"
    grid += " 19   20   21   22   23   24   25\n"
    grid += " 26   27   28   29   30   31\n```"
    
    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"Ottobre 2026\n{grid}",
        color=0x2f3136
    )
    # Lista Giorno XX rimossa come richiesto

    view = discord.ui.View(timeout=None)
    btn = discord.ui.Button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅")
    async def cb(inter: discord.Interaction):
        await inter.response.send_message("Usa /creaevento giorno:05 ora:21:00 gioco:WarDogs", ephemeral=True)
    btn.callback = cb
    view.add_item(btn)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="creaevento", description="Crea evento calendario")
@app_commands.describe(giorno="Giorno", ora="Ora", gioco="Gioco")
async def creaevento(interaction: discord.Interaction, giorno: int, ora: str, gioco: str):
    await interaction.response.send_message(f"Evento creato: Giorno {giorno} ore {ora} | {gioco}", ephemeral=True)

token = os.getenv("DISCORD_TOKEN")
if not token:
    print("ERRORE: DISCORD_TOKEN non impostato")
else:
    bot.run(token)
