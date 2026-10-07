import os, discord
from discord.ext import commands
from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home():
    return "Calendario Bot Live - Esempio 1 2 3 / 0 OK"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class Modal(discord.ui.Modal, title="Crea Evento"):
    max_part = discord.ui.TextInput(label="Max partecipanti (1-99) - Esempio 1 2 3", default="0", max_length=2, required=True)
    nome = discord.ui.TextInput(label="Nome evento", required=True)
    async def on_submit(self, interaction):
        await interaction.response.send_message(f"{self.nome.value} - {self.max_part.value} max", ephemeral=True)

class View(discord.ui.View):
    @discord.ui.button(label="Crea", style=discord.ButtonStyle.blurple)
    async def crea(self, inter, btn):
        await inter.response.send_modal(Modal())

@bot.command()
async def calendario(ctx):
    await ctx.send("Crea evento:", view=View())

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except: pass
    print(f"Bot ready {bot.user}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

threading.Thread(target=run_flask, daemon=True).start()
bot.run(os.getenv("DISCORD_TOKEN"))
