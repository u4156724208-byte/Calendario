
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
        print("Slash syncati")
    except Exception as e:
        print(e)

# --- MODAL CREAZIONE EVENTO ---
class CreaEventoModal(discord.ui.Modal, title="Crea Evento"):
    def __init__(self, giorno: int):
        super().__init__()
        self.giorno = giorno
        self.nome = discord.ui.TextInput(label=f"Evento per il {giorno}/10/2026", placeholder="Es: Torneo, Serata giochi...", max_length=100)
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

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        oggi = datetime.date.today().day
        # Se vuoi forzare ottobre 2026, usa oggi = 5 per test, altrimenti datetime.date.today()
        # Per prod con mese corrente: blocca < oggi
        for giorno in range(1, 32):
            disabilitato = giorno < oggi  # <--- esclude giorni precedenti a oggi
            btn = discord.ui.Button(
                label=f"{giorno:02d}",
                style=discord.ButtonStyle.secondary if disabilitato else discord.ButtonStyle.primary,
                disabled=disabilitato,
                row=(giorno-1)//5,
                custom_id=f"giorno_{giorno}"
            )
            btn.callback = self.make_callback(giorno)
            self.add_item(btn)

    def make_callback(self, giorno: int):
        async def callback(interaction: discord.Interaction):
            modal = CreaEventoModal(giorno)
            await interaction.response.send_modal(modal)
        return callback

@bot.tree.command(name="calendario", description="Mostra calendario giochi cliccabile")
async def calendario(interaction: discord.Interaction):
    oggi = datetime.date.today()
    descrizione = f"Ottobre {oggi.year}\nClicca un giorno per creare un evento.\nGiorni prima di oggi ({oggi.day:02d}) non cliccabili."
    
    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=descrizione,
        color=0x2f3136
    )
    embed.set_footer(text="Seleziona un giorno dal calendario qui sotto")
    
    view = CalendarioView()
    await interaction.response.send_message(embed=embed, view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
