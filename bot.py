
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
        self.giorno = discord.ui.TextInput(label="Giorno", placeholder="Es: 12", max_length=2, required=True)
        self.nome = discord.ui.TextInput(label="Nome evento", placeholder="Es: Torneo", max_length=100, required=True)
        self.orario = discord.ui.TextInput(label="Orario", placeholder="Es: 21:00", required=False, max_length=20)
        self.add_item(self.giorno)
        self.add_item(self.nome)
        self.add_item(self.orario)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            g = int(self.giorno.value)
            if not 1 <= g <= 31:
                raise ValueError()
        except:
            await interaction.response.send_message("Giorno non valido (1-31).", ephemeral=True)
            return

        oggi = datetime.date.today().day
        if g < oggi:
            await interaction.response.send_message(f"Il giorno {g:02d} e' gia' passato, non puoi creare eventi.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Evento creato per il {g:02d}/10/2026",
            description=f"**{self.nome.value}**\nOrario: {self.orario.value or 'Da definire'}",
            color=0x00ff88
        )
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreaEventoModal())

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())

def build_grid():
    # Ottobre 2026: 1 = giovedi
    giorni = [""]*3 + [f"{d:02d}" for d in range(1, 32)]
    rows = ["LUN  MAR  MER  GIO  VEN  SAB  DOM"]
    for i in range(0, len(giorni), 7):
        week = giorni[i:i+7]
        line = "".join(f"{d:>4}" if d else "    " for d in week)
        rows.append(line)
    return "```\n" + "\n".join(rows) + "\n```"

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    try:
        oggi = datetime.date.today()
        grid = build_grid()
        embed = discord.Embed(
            title="CALENDARIO GIOCHI",
            description=f"Ottobre {oggi.year}\n{grid}",
            color=0x2f3136
        )
        embed.set_footer(text=f"I giorni prima del {oggi.day:02d} non sono selezionabili")
        view = CalendarioView()
        await interaction.response.send_message(embed=embed, view=view)
    except Exception as e:
        print(e)
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
