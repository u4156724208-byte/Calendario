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
        print(f"Sync error: {e}")

class CreaEventoModal(discord.ui.Modal, title="Crea Evento"):
    def __init__(self, giorno: int):
        super().__init__()
        self.giorno = giorno
        self.nome = discord.ui.TextInput(label=f"Nome evento per {giorno}/10", placeholder="Es: Torneo", max_length=100, required=True)
        self.orario = discord.ui.TextInput(label="Orario", placeholder="Es: 21:00", required=False, max_length=20)
        self.add_item(self.nome)
        self.add_item(self.orario)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title=f"Evento {self.giorno:02d}/10/2026",
                description=f"**{self.nome.value}**\nOrario: {self.orario.value or 'Da definire'}",
                color=0x00ff88
            )
            embed.set_footer(text=f"Creato da {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Modal error: {e}")

class GiornoSelectFuturo(discord.ui.Select):
    def __init__(self, giorni, placeholder):
        options = [
            discord.SelectOption(label=f"{g:02d}/10/2026", value=str(g), emoji="\U0001f4c5")
            for g in giorni
        ]
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            giorno = int(self.values[0])
            modal = CreaEventoModal(giorno)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Select callback error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

class SelectGiornoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        oggi = datetime.date.today().day
        # FIX: max 25 opzioni per select - dividiamo
        futuri = list(range(oggi, 32))
        chunk1 = futuri[:25]
        chunk2 = futuri[25:]

        if chunk1:
            self.add_item(GiornoSelectFuturo(chunk1, f"Giorni {chunk1[0]:02d}-{chunk1[-1]:02d}"))
        if chunk2:
            self.add_item(GiornoSelectFuturo(chunk2, f"Giorni {chunk2[0]:02d}-{chunk2[-1]:02d}"))

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")

    async def callback(self, interaction: discord.Interaction):
        try:
            view = SelectGiornoView()
            await interaction.response.send_message(
                "Scegli il giorno (solo futuri, passati rimossi):",
                view=view,
                ephemeral=True
            )
        except Exception as e:
            print(f"Button error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())

def build_grid():
    cols = ["LUN","MAR","MER","GIO","VEN","SAB","DOM"]
    header = "".join(f"{c:>4}" for c in cols)
    giorni = [""]*3 + [f"{d:02d}" for d in range(1, 32)]
    rows = [header]
    for i in range(0, len(giorni), 7):
        week = giorni[i:i+7]
        line = "".join(f"{d:>4}" if d else "    " for d in week)
        rows.append(line)
    return "```\n" + "\n".join(rows) + "\n```"

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    try:
        grid = build_grid()
        embed = discord.Embed(
            description=f"Ottobre 2026\n{grid}",
            color=0x2f3136
        )
        view = CalendarioView()
        await interaction.response.send_message(embed=embed, view=view)
    except Exception as e:
        print(f"calendario error: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
