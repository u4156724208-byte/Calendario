
import os, threading, datetime
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
        print("Sync OK")
    except Exception as e:
        print(e)

class CreaEventoModal(discord.ui.Modal, title="Crea Evento"):
    def __init__(self):
        super().__init__()
        oggi = datetime.date.today().day

        self.giorno = discord.ui.TextInput(
            label=f"Giorno (da {oggi} a 31)",
            placeholder=f"Es: {oggi}",
            max_length=2,
            required=True
        )
        self.ora = discord.ui.TextInput(
            label="Ora",
            placeholder="Es: 21:00",
            max_length=5,
            required=True
        )
        self.titolo = discord.ui.TextInput(
            label="Titolo gioco",
            placeholder="Es: Torneo Warzone",
            max_length=100,
            required=True
        )
        self.partecipanti = discord.ui.TextInput(
            label="Partecipanti",
            placeholder="Es: @Mario, @Luigi, @Peppe",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False
        )

        self.add_item(self.giorno)
        self.add_item(self.ora)
        self.add_item(self.titolo)
        self.add_item(self.partecipanti)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            g = int(self.giorno.value)
        except:
            await interaction.response.send_message("Giorno non valido.", ephemeral=True)
            return

        oggi = datetime.date.today().day
        if g < oggi or g > 31:
            await interaction.response.send_message(f"Puoi usare solo giorni da {oggi} a 31.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Evento del {g:02d}/10/2026 - {self.titolo.value}",
            color=0x00ff88
        )
        embed.add_field(name="Giorno", value=f"{g:02d}/10/2026", inline=True)
        embed.add_field(name="Ora", value=self.ora.value, inline=True)
        embed.add_field(name="Titolo gioco", value=self.titolo.value, inline=False)
        if self.partecipanti.value:
            embed.add_field(name="Partecipanti", value=self.partecipanti.value, inline=False)
        
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreaEventoModal())

class SoloBottoneView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())

@bot.tree.command(name="calendario", description="Mostra bottone crea evento")
async def calendario(interaction: discord.Interaction):
    view = SoloBottoneView()
    await interaction.response.send_message(view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
