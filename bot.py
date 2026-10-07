import os
import discord
from discord.ext import commands
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "OK - Calendario Bot Live"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class CreaEventoModal(discord.ui.Modal, title="Crea Evento Calendario"):
    max_partecipanti = discord.ui.TextInput(
        label="Max partecipanti (1-99) - Esempio 1 2 3",
        placeholder="Esempio: 1, 2, 3...",
        default="0",
        max_length=2,
        required=True
    )
    nome_evento = discord.ui.TextInput(
        label="Nome evento",
        placeholder="Es: Torneo Ghost",
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        try:
            num = int(self.max_partecipanti.value)
        except:
            num = 0
        await interaction.response.send_message(f"Evento {self.nome_evento.value} - Max: {num}", ephemeral=True)

class CreaView(discord.ui.View):
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.blurple)
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoModal())

@bot.command(name="calendario")
async def calendario_cmd(ctx):
    await ctx.send("Crea:", view=CreaView())

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"Sync error: {e}")
    print(f"Bot online {bot.user} - Fix Esempio 1 2 3 / 0 OK")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
