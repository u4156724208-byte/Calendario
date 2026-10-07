import os
import discord
from discord.ext import commands
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "OK - Calendario Bot Live Slash"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class CreaEventoModal(discord.ui.Modal, title="Crea Evento Calendario"):
    max_partecipanti = discord.ui.TextInput(
        label="Max partecipanti (1-99) - Esempio 1 2 3",
        placeholder="Esempio: 1, 2, 3... lascia 0 per illimitato",
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
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoModal())

@bot.tree.command(name="calendario", description="Mostra calendario Ottobre 2026")
async def calendario_slash(interaction: discord.Interaction):
    embed_desc = "```\nLUN MAR MER GIO VEN SAB DOM\n          01  02  03  04\n05  06  07  08  09  10  11\n12  13  14  15  16  17  18\n19  20  21  22  23  24  25\n26  27  28  29  30  31\n```"
    embed = discord.Embed(title="Ottobre 2026", description=embed_desc, color=0x2b2d31)
    await interaction.response.send_message(embed=embed, view=CreaView())

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sync {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync error: {e}")
    print(f"Bot online {bot.user} - Slash /calendario OK")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
