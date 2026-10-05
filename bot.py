
import os, threading, datetime
from zoneinfo import ZoneInfo
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

ITALIA = ZoneInfo("Europe/Rome")

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        await bot.tree.sync()
        print("Sync OK")
    except Exception as e:
        print(e)

def get_ora_italia():
    # Se mi dici data/ora manualmente per test, la usiamo
    # Altrimenti usa ora reale di Roma
    return datetime.datetime.now(ITALIA)

class CreaEventoModal(discord.ui.Modal, title="Crea Evento"):
    def __init__(self):
        super().__init__()
        adesso = get_ora_italia()
        oggi_giorno = 5  # 05/10/26 come mi hai detto
        ora_attuale = adesso.strftime("%H:%M")

        self.giorno = discord.ui.TextInput(
            label=f"Giorno (da {oggi_giorno} a 31) - Oggi 05/10/26",
            placeholder=f"Es: {oggi_giorno}",
            default=str(oggi_giorno),
            max_length=2,
            required=True
        )
        self.ora = discord.ui.TextInput(
            label=f"Ora (adesso {ora_attuale} del 05/10/26)",
            placeholder="Es: 03:00",
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
            label="Partecipanti (numero libero)",
            placeholder="Es: 1 2 3",
            max_length=10,
            required=True
        )

        self.add_item(self.giorno)
        self.add_item(self.ora)
        self.add_item(self.titolo)
        self.add_item(self.partecipanti)

    async def on_submit(self, interaction: discord.Interaction):
        adesso = get_ora_italia()
        oggi_giorno = 5  # Forzato a 05/10/26 come da tua indicazione
        ora_riferimento = 2 * 60 + 2  # 02:02 in minuti

        try:
            g = int(self.giorno.value)
        except:
            await interaction.response.send_message("Giorno non valido. Usa 1-31.", ephemeral=True)
            return

        if g < oggi_giorno or g > 31:
            await interaction.response.send_message(f"Oggi e' 05/10/26 02:02 - puoi usare solo giorni da 05 a 31.", ephemeral=True)
            return

        ora_str = self.ora.value.strip()
        try:
            if ":" in ora_str:
                h, m = map(int, ora_str.split(":"))
            else:
                h = int(ora_str)
                m = 0
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
        except:
            await interaction.response.send_message("Ora non valida. Usa HH:MM es: 21:00", ephemeral=True)
            return

        # Blocco orario passato SOLO se giorno = 05 (oggi)
        if g == oggi_giorno:
            inserita_minuti = h * 60 + m
            if inserita_minuti <= ora_riferimento:
                await interaction.response.send_message(
                    f"Non puoi creare un evento per oggi 05/10 alle {h:02d}:{m:02d}, e' gia passato! Ora sono le 02:02. Inserisci un orario dopo le 02:02.",
                    ephemeral=True
                )
                return

        # VALIDAZIONE PARTECIPANTI LIBERO - solo minimo 1, no massimo
        try:
            p = int(self.partecipanti.value.strip())
        except:
            await interaction.response.send_message("Partecipanti non valido. Inserisci un numero.", ephemeral=True)
            return
        
        if p < 1:
            await interaction.response.send_message(f"Numero partecipanti non valido: {p}. Minimo 1.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Evento del {g:02d}/10/2026 - {self.titolo.value}",
            color=0x00ff88
        )
        embed.add_field(name="Giorno", value=f"{g:02d}/10/2026", inline=True)
        embed.add_field(name="Ora", value=f"{h:02d}:{m:02d}", inline=True)
        embed.add_field(name="Titolo gioco", value=self.titolo.value, inline=False)
        embed.add_field(name="Partecipanti", value=f"{p} persone", inline=False)
        embed.set_footer(text=f"Creato da {interaction.user.display_name} • Oggi 05/10/26 02:02")

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
