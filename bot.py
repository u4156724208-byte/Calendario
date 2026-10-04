
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
    def __init__(self, giorno: int):
        super().__init__()
        self.giorno = giorno
        self.nome = discord.ui.TextInput(label=f"Nome evento per {giorno}/10", placeholder="Es: Torneo, Serata giochi...", max_length=100, required=True)
        self.orario = discord.ui.TextInput(label="Orario", placeholder="Es: 21:00", required=False, max_length=20)
        self.add_item(self.nome)
        self.add_item(self.orario)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Evento creato per il {self.giorno:02d}/10/2026",
            description=f"**{self.nome.value}**\nOrario: {self.orario.value or 'Da definire'}",
            color=0x00ff88
        )
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

class GiornoSelectFuturo(discord.ui.Select):
    def __init__(self):
        oggi = datetime.date.today().day
        # Solo giorni da oggi in poi - niente passati
        options = [
            discord.SelectOption(label=f"{g:02d}/10/2026", value=str(g), description=f"Crea evento il {g:02d}", emoji="\U0001f4c5")
            for g in range(oggi, 32)
        ]
        # Se oggi > 31 (fine mese) mostra messaggio
        if not options:
            options = [discord.SelectOption(label="Nessun giorno disponibile", value="0")]
        super().__init__(placeholder=f"Scegli giorno (disponibili da {oggi:02d} a 31)", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        giorno = int(self.values[0])
        modal = CreaEventoModal(giorno)
        await interaction.response.send_modal(modal)

class SelectGiornoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(GiornoSelectFuturo())

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")

    async def callback(self, interaction: discord.Interaction):
        oggi = datetime.date.today().day
        view = SelectGiornoView()
        await interaction.response.send_message(
            f"Seleziona un giorno disponibile (dal {oggi:02d} al 31) - i giorni passati sono stati rimossi:",
            view=view,
            ephemeral=True
        )

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())

def build_grid():
    giorni = [""]*3 + [f"{d:02d}" for d in range(1, 32)]
    rows = ["LUN  MAR  MER  GIO  VEN  SAB  DOM"]
    for i in range(0, len(giorni), 7):
        week = giorni[i:i+7]
        line = "".join(f"{d:>4}" if d else "    " for d in week)
        rows.append(line)
    return "```\n" + "\n".join(rows) + "\n```"

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    oggi = datetime.date.today()
    grid = build_grid()
    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"Ottobre {oggi.year}\n{grid}",
        color=0x2f3136
    )
    embed.set_footer(text=f"Solo giorni dal {oggi.day:02d} al 31 selezionabili")
    view = CalendarioView()
    await interaction.response.send_message(embed=embed, view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
