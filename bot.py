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
        oggi_giorno = datetime.date.today().day
        ora_attuale = datetime.datetime.now().strftime("%H:%M")

        self.giorno = discord.ui.TextInput(
            label=f"Giorno (da {oggi_giorno} a 31)",
            placeholder=f"Es: {oggi_giorno}",
            max_length=2,
            required=True
        )
        self.ora = discord.ui.TextInput(
            label=f"Ora (ora attuale {ora_attuale})",
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
            await interaction.response.send_message("Giorno non valido. Usa 1-31.", ephemeral=True)
            return

        oggi = datetime.date.today().day
        if g < oggi or g > 31:
            await interaction.response.send_message(f"Puoi usare solo giorni da {oggi} a 31.", ephemeral=True)
            return

        # VALIDAZIONE ORARIO
        ora_str = self.ora.value.strip()
        try:
            # Supporta HH:MM o HH
            if ":" in ora_str:
                h, m = map(int, ora_str.split(":"))
            else:
                h = int(ora_str)
                m = 0
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
            ora_inserita = datetime.time(h, m)
        except:
            await interaction.response.send_message("Ora non valida. Usa formato HH:MM es: 21:00", ephemeral=True)
            return

        # Se giorno = oggi, blocca orario passato
        if g == oggi:
            ora_adesso = datetime.datetime.now().time()
            # confronto ore e minuti
            adesso_minuti = ora_adesso.hour * 60 + ora_adesso.minute
            inserita_minuti = h * 60 + m
            if inserita_minuti <= adesso_minuti:
                await interaction.response.send_message(
                    f"Non puoi creare un evento per oggi alle {h:02d}:{m:02d}, e' gia passato! Ora sono le {ora_adesso.strftime('%H:%M')}. Inserisci un orario futuro.",
                    ephemeral=True
                )
                return

        embed = discord.Embed(
            title=f"Evento del {g:02d}/10/2026 - {self.titolo.value}",
            color=0x00ff88
        )
        embed.add_field(name="Giorno", value=f"{g:02d}/10/2026", inline=True)
        embed.add_field(name="Ora", value=f"{h:02d}:{m:02d}", inline=True)
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
