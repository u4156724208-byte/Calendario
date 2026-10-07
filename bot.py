import os, discord
from discord.ext import commands
from flask import Flask
import threading
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "OK"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class CreaEventoCompletoModal(discord.ui.Modal, title="Crea Evento - scegli data completa"):
    def __init__(self):
        super().__init__()
        now = datetime.now()
        data_str = now.strftime("%d/%m/%Y")
        ora_str = now.strftime("%H:%M")
        self.data_input = discord.ui.TextInput(label=f"Data (GG/MM/AAAA) - Oggi {data_str}", default=data_str, required=True)
        self.ora_input = discord.ui.TextInput(label=f"Ora (HH:MM) - Ora {ora_str}", default=ora_str, required=True)
        self.titolo_input = discord.ui.TextInput(label="Titolo evento", placeholder="Es: Game Film JustChatting", required=True)
        self.max_input = discord.ui.TextInput(label="Max partecipanti (1-99) - Esempio 1 2 3", placeholder="Esempio: 1, 2, 3... lascia 0 per illimitato", default="0", max_length=2, required=True)
        # Ordine: Data, Ora, Titolo, Max sotto
        self.add_item(self.data_input)
        self.add_item(self.ora_input)
        self.add_item(self.titolo_input)
        self.add_item(self.max_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Evento: **{self.titolo_input.value}** {self.data_input.value} {self.ora_input.value} Max {self.max_input.value}", ephemeral=True)

class CreaView(discord.ui.View):
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoCompletoModal())

@bot.tree.command(name="calendario", description="Mostra calendario")
async def calendario_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="Ottobre 2026", description="```\nLUN MAR MER GIO VEN SAB DOM\n          01 02 03 04\n05 06 07 08 09 10 11\n12 13 14 15 16 17 18\n19 20 21 22 23 24 25\n26 27 28 29 30 31\n```", color=0x2b2d31)
    await interaction.response.send_message(embed=embed, view=CreaView())

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    embed = discord.Embed(title="Ottobre 2026", description="```\nLUN MAR MER GIO VEN SAB DOM\n          01 02 03 04\n05 06 07 08 09 10 11\n12 13 14 15 16 17 18\n19 20 21 22 23 24 25\n26 27 28 29 30 31\n```", color=0x2b2d31)
    await ctx.send(embed=embed, view=CreaView())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online {bot.user} - Max sotto con Esempio 1 2 3")

def run_flask(): app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
