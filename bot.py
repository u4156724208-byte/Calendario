
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
intents.message_content = True
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

    # Forza nickname a solo "Calendario" in tutti i server
    for guild in bot.guilds:
        try:
            me = guild.me
            if me.display_name != "Calendario":
                await me.edit(nick="Calendario")
                print(f"Nick cambiato in Calendario su {guild.name}")
        except Exception as e:
            print(f"Non posso cambiare nick su {guild.name}: {e}")

def get_ora_italia():
    return datetime.datetime.now(ITALIA)

# VIEW CON BOTTONE PARTECIPA
class EventoPartecipaView(discord.ui.View):
    def __init__(self, max_partecipanti: int, titolo_evento: str, data_str: str, creatore: str):
        super().__init__(timeout=None)
        self.max_p = max_partecipanti
        self.titolo_evento = titolo_evento
        self.data_str = data_str
        self.creatore = creatore
        self.partecipanti = []  # lista di dict {id, name}

    @discord.ui.button(label="Partecipa", style=discord.ButtonStyle.green, emoji="✅", custom_id="partecipa_btn")
    async def partecipa(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id

        # gia partecipa?
        if any(p["id"] == user_id for p in self.partecipanti):
            await interaction.response.send_message("Hai gia cliccato Partecipa!", ephemeral=True)
            return

        # pieno?
        if len(self.partecipanti) >= self.max_p:
            await interaction.response.send_message(f"Evento pieno! Massimo {self.max_p} persone.", ephemeral=True)
            return

        self.partecipanti.append({"id": user_id, "name": interaction.user.display_name})

        # aggiorna embed
        embed = discord.Embed(
            title=f"Evento del {self.data_str}",
            color=0x00ff88
        )
        embed.add_field(name="Titolo", value=self.titolo_evento, inline=False)

        if self.partecipanti:
            lista_nomi = "\n".join([f"• {p['name']}" for p in self.partecipanti])
            valore = f"{len(self.partecipanti)}/{self.max_p} persone\n{lista_nomi}"
        else:
            valore = f"0/{self.max_p} persone"

        embed.add_field(name="Partecipanti", value=valore, inline=False)
        embed.set_footer(text=f"Creato da {self.creatore}")

        # se pieno disabilita bottone
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

        embed = discord.Embed(
            title=f"Evento del {self.data_str}",
            color=0x00ff88
        )
        embed.add_field(name="Titolo", value=self.titolo_evento, inline=False)
        if self.partecipanti:
            lista_nomi = "\n".join([f"• {p['name']}" for p in self.partecipanti])
            valore = f"{len(self.partecipanti)}/{self.max_p} persone\n{lista_nomi}"
        else:
            valore = f"0/{self.max_p} persone"
        embed.add_field(name="Partecipanti", value=valore, inline=False)
        embed.set_footer(text=f"Creato da {self.creatore}")

        # riabilita bottone partecipa se era pieno
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
        oggi_giorno = 5
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
            label="Titolo",
            placeholder="Es: Game Film JustChatting",
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
        oggi_giorno = 5
        ora_riferimento = 2 * 60 + 2

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

        if g == oggi_giorno:
            inserita_minuti = h * 60 + m
            if inserita_minuti <= ora_riferimento:
                await interaction.response.send_message(
                    f"Non puoi creare un evento per oggi 05/10 alle {h:02d}:{m:02d}, e' gia passato! Ora sono le 02:02. Inserisci un orario dopo le 02:02.",
                    ephemeral=True
                )
                return

        try:
            p = int(self.partecipanti.value.strip())
        except:
            await interaction.response.send_message("Partecipanti non valido. Inserisci un numero.", ephemeral=True)
            return
        
        if p < 1:
            await interaction.response.send_message(f"Numero partecipanti non valido: {p}. Minimo 1.", ephemeral=True)
            return

        data_str = f"{g:02d}/10/2026 ore {h:02d}:{m:02d}"

        embed = discord.Embed(
            title=f"Evento del {data_str}",
            color=0x00ff88
        )
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
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())

@bot.tree.command(name="calendario", description="Mostra bottone crea evento")
async def calendario(interaction: discord.Interaction):
    view = SoloBottoneView()
    # Risposta effimera + messaggio normale: cosi' il "Clicca per vedere il comando" resta solo sopra il messaggio effimero, non sopra l'embed
    await interaction.response.send_message("✅ Calendario inviato qui sotto!", ephemeral=True)
    await interaction.channel.send(view=view)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    view = SoloBottoneView()
    await ctx.send(view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
