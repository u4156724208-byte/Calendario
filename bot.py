
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

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Modal vuoto - dimmi cosa mettere dentro", ephemeral=True)

class SoloBottoneView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())

@bot.tree.command(name="calendario", description="Mostra bottone crea evento")
async def calendario(interaction: discord.Interaction):
    view = SoloBottoneView()
    await interaction.response.send_message(view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
