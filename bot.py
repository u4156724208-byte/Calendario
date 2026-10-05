
import os, threading, datetime, calendar
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
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ITALIA = ZoneInfo("Europe/Rome")
MESI_ITA = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno","Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]

def get_ora_italia():
    return datetime.datetime.now(ITALIA)

def genera_calendario_mese(anno, mese):
    cal = calendar.Calendar(firstweekday=0)
    giorni = list(cal.itermonthdays(anno, mese))
    header = "LUN  MAR  MER  GIO  VEN  SAB  DOM"
    righe = []
    for i in range(0, len(giorni), 7):
        sett = giorni[i:i+7]
        riga = ""
        for g in sett:
            if g == 0:
                riga += "     "
            else:
                riga += f"{g:02d}   "
        righe.append(riga.rstrip())
    testo = "```\n" + header + "\n" + "\n".join(righe) + "\n```"
    return testo

# VIEW PARTECIPA
class EventoPartecipaView(discord.ui.View):
    def __init__(self, max_partecipanti: int, titolo_evento: str, data_str: str, creatore: str):
        super().__init__(timeout=None)
        self.max_p = max_partecipanti
        self.titolo_evento = titolo_evento
        self.data_str = data_str
        self.creatore = creatore
        self.partecipanti = []

    @discord.ui.button(label="Partecipa", style=discord.ButtonStyle.green, emoji="✅", custom_id="partecipa_btn")
    async def partecipa(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if any(p["id"] == user_id for p in self.partecipanti):
            await interaction.response.send_message("Hai gia cliccato Partecipa!", ephemeral=True)
            return
        if len(self.partecipanti) >= self.max_p:
            await interaction.response.send_message(f"Evento pieno! Massimo {self.max_p} persone.", ephemeral=True)
            return
        self.partecipanti.append({"id": user_id, "name": interaction.user.display_name})
        embed = discord.Embed(title=f"Evento del {self.data_str}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo_evento, inline=False)
        lista_nomi = "\n".join([f"• {p['name']}" for p in self.partecipanti])
        valore = f"{len(self.partecipanti)}/{self.max_p} persone\n{lista_nomi}" if self.partecipanti else f"0/{self.max_p} persone"
        embed.add_field(name="Partecipanti", value=valore, inline=False)
        embed.set_footer(text=f"Creato da {self.creatore}")
        if len(self.partecipanti) >= self.max_p:
            button.disabled = True
            button.label = "Evento Pieno"
            button.style = discord.ButtonStyle.gray
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Esci", style=discord.ButtonStyle.red, emoji="❌", custom_id="esci_btn")
    async def esci(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        trovato = next((p for p in self.partecipanti if p["id"] == user_id), None)
        if not trovato:
            await interaction.response.send_message("Non stai partecipando.", ephemeral=True)
            return
        self.partecipanti = [p for p in self.partecipanti if p["id"] != user_id]
        embed = discord.Embed(title=f"Evento del {self.data_str}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo_evento, inline=False)
        if self.partecipanti:
            lista_nomi = "\n".join([f"• {p['name']}" for p in self.partecipanti])
            valore = f"{len(self.partecipanti)}/{self.max_p} persone\n{lista_nomi}"
        else:
            valore = f"0/{self.max_p} persone"
        embed.add_field(name="Partecipanti", value=valore, inline=False)
        embed.set_footer(text=f"Creato da {self.creatore}")
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "partecipa_btn":
                child.disabled = False
                child.label = "Partecipa"
                child.style = discord.ButtonStyle.green
        await interaction.response.edit_message(embed=embed, view=self)

class CreaEventoModal(discord.ui.Modal, title="Crea Evento"):
    def __init__(self):
        super().__init__()
        adesso = get_ora_italia()
        self.giorno = discord.ui.TextInput(label=f"Giorno (1-31) Oggi {adesso.day:02d}/10", placeholder=f"Es: {adesso.day}", default=str(adesso.day), max_length=2, required=True)
        self.ora = discord.ui.TextInput(label=f"Ora (adesso {adesso.strftime('%H:%M')})", placeholder="Es: 03:00", max_length=5, required=True)
        self.titolo = discord.ui.TextInput(label="Titolo", placeholder="Es: Game Film", max_length=100, required=True)
        self.partecipanti = discord.ui.TextInput(label="Partecipanti (numero)", placeholder="Es: 4", max_length=10, required=True)
        self.add_item(self.giorno)
        self.add_item(self.ora)
        self.add_item(self.titolo)
        self.add_item(self.partecipanti)

    async def on_submit(self, interaction: discord.Interaction):
        oggi = get_ora_italia().day
        try:
            g = int(self.giorno.value)
            if not (1 <= g <= 31): raise ValueError()
        except:
            await interaction.response.send_message("Giorno non valido.", ephemeral=True)
            return
        ora_str = self.ora.value.strip()
        try:
            if ":" in ora_str:
                h,m = map(int, ora_str.split(":"))
            else:
                h = int(ora_str); m = 0
            if not (0 <= h <= 23 and 0 <= m <= 59): raise ValueError()
        except:
            await interaction.response.send_message("Ora non valida.", ephemeral=True)
            return
        try:
            p = int(self.partecipanti.value.strip())
            if p < 1: raise ValueError()
        except:
            await interaction.response.send_message("Partecipanti non valido.", ephemeral=True)
            return
        data_str = f"{g:02d}/10/2026 ore {h:02d}:{m:02d}"
        embed = discord.Embed(title=f"Evento del {data_str}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo.value, inline=False)
        embed.add_field(name="Partecipanti", value=f"0/{p} persone", inline=False)
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        view = EventoPartecipaView(max_partecipanti=p, titolo_evento=self.titolo.value, data_str=data_str, creatore=interaction.user.display_name)
        await interaction.response.send_message(embed=embed, view=view)

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreaEventoModal())

class SoloBottoneView(discord.ui.View):
    def __init__(self, anno=None, mese=None):
        super().__init__(timeout=None)
        adesso = get_ora_italia()
        self.anno = anno or adesso.year
        self.mese = mese or adesso.month
        self.add_item(CreaEventoButton())
        btn_prev = discord.ui.Button(label="◀️", style=discord.ButtonStyle.gray, row=0)
        btn_next = discord.ui.Button(label="▶️", style=discord.ButtonStyle.gray, row=0)
        async def prev_cb(interaction: discord.Interaction):
            self.mese -= 1
            if self.mese < 1:
                self.mese = 12
                self.anno -= 1
            embed = discord.Embed(title=f"{MESI_ITA[self.mese-1]} {self.anno}", description=genera_calendario_mese(self.anno, self.mese), color=0x2b2d31)
            await interaction.response.edit_message(embed=embed, view=self)
        async def next_cb(interaction: discord.Interaction):
            self.mese += 1
            if self.mese > 12:
                self.mese = 1
                self.anno += 1
            embed = discord.Embed(title=f"{MESI_ITA[self.mese-1]} {self.anno}", description=genera_calendario_mese(self.anno, self.mese), color=0x2b2d31)
            await interaction.response.edit_message(embed=embed, view=self)
        btn_prev.callback = prev_cb
        btn_next.callback = next_cb
        self.add_item(btn_prev)
        self.add_item(btn_next)

    def get_embed(self):
        return discord.Embed(title=f"{MESI_ITA[self.mese-1]} {self.anno}", description=genera_calendario_mese(self.anno, self.mese), color=0x2b2d31)

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        await bot.tree.sync()
        print("Sync OK")
    except Exception as e:
        print(e)
    for guild in bot.guilds:
        try:
            if guild.me.display_name != "Calendario":
                await guild.me.edit(nick="Calendario")
        except:
            pass

@bot.tree.command(name="calendario", description="Mostra calendario + bottone crea evento")
async def calendario(interaction: discord.Interaction):
    adesso = get_ora_italia()
    view = SoloBottoneView(anno=adesso.year, mese=adesso.month)
    await interaction.response.send_message("✅ Calendario inviato qui sotto!", ephemeral=True)
    await interaction.channel.send(embed=view.get_embed(), view=view)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    adesso = get_ora_italia()
    view = SoloBottoneView(anno=adesso.year, mese=adesso.month)
    await ctx.send(embed=view.get_embed(), view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
