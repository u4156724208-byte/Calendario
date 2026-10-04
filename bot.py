
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
        self.nome = discord.ui.TextInput(label=f"Evento per {giorno}/10/2026", placeholder="Es: Torneo, Serata giochi...", max_length=100)
        self.orario = discord.ui.TextInput(label="Orario", placeholder="Es: 21:00", required=False, max_length=20)
        self.add_item(self.nome)
        self.add_item(self.orario)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Evento creato per il {self.giorno}/10/2026",
            description=f"**{self.nome.value}**\nOrario: {self.orario.value or 'Da definire'}",
            color=0x00ff88
        )
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

class GiornoSelect(discord.ui.Select):
    def __init__(self, giorni):
        oggi = datetime.date.today().day
        options = []
        for g in giorni:
            dis = g < oggi
            options.append(
                discord.SelectOption(
                    label=f"{g:02d}/10/2026",
                    description="Non disponibile" if dis else f"Crea evento per il {g:02d}",
                    value=str(g),
                    emoji="❌" if dis else "📅"
                )
            )
        super().__init__(placeholder="Seleziona un giorno per creare evento", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        giorno = int(self.values[0])
        oggi = datetime.date.today().day
        if giorno < oggi:
            await interaction.response.send_message(f"Il giorno {giorno:02d} e' passato, non puoi creare eventi.", ephemeral=True)
            return
        modal = CreaEventoModal(giorno)
        await interaction.response.send_modal(modal)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        oggi = datetime.date.today().day
        # Giorni futuri 05-31 = 27 giorni -> li dividiamo in 2 menu per rispettare limite 25
        futuri = [g for g in range(1, 32) if g >= oggi]
        # Per mostrare anche i passati come disabilitati nel menu, includiamo tutti ma disabilitiamo descrizione
        # Dividiamo in chunk da 25
        chunk1 = list(range(1, 26))  # 01-25
        chunk2 = list(range(26, 32)) # 26-31
        self.add_item(GiornoSelect(chunk1))
        if len(chunk2) > 0:
            self.add_item(GiornoSelect(chunk2))

@bot.tree.command(name="calendario", description="Mostra calendario giochi cliccabile")
async def calendario(interaction: discord.Interaction):
    try:
        oggi = datetime.date.today()
        embed = discord.Embed(
            title="CALENDARIO GIOCHI",
            description=f"Ottobre {oggi.year}\nSeleziona un giorno dal menu qui sotto.\nI giorni prima di oggi ({oggi.day:02d}) non sono cliccabili.",
            color=0x2f3136
        )
        # Griglia visiva dritta
        giorni = [""]*3 + [f"{d:02d}" for d in range(1, 32)]
        rows = ["LUN  MAR  MER  GIO  VEN  SAB  DOM"]
        for i in range(0, len(giorni), 7):
            week = giorni[i:i+7]
            line = "".join(f"{d:>4}" if d else "    " for d in week)
            rows.append(line)
        grid = "```\n" + "\n".join(rows) + "\n```"
        embed.add_field(name="Calendario", value=grid, inline=False)
        embed.set_footer(text="Usa i menu sotto per creare evento")

        view = CalendarioView()
        await interaction.response.send_message(embed=embed, view=view)
    except Exception as e:
        print(f"Errore calendario: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
