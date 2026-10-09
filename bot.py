import os, threading, datetime, calendar, re
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

# MODAL UNICO: data + ora + max partecipanti + titolo
class CreaEventoModal(discord.ui.Modal, title="Crea Evento - scegli data completa"):
    def __init__(self):
        super().__init__()
        adesso = get_ora_italia()
        data_oggi = f"{adesso.day:02d}/{adesso.month:02d}/{adesso.year}"
        self.data = discord.ui.TextInput(label=f"Data (GG/MM/AAAA) - Oggi {data_oggi}", placeholder=f"Es: {data_oggi}", default=data_oggi, max_length=10, required=True)
        self.ora = discord.ui.TextInput(label=f"Ora (HH:MM) - Ora {adesso.strftime('%H:%M')}", placeholder="Es: 21:00", default=adesso.strftime('%H:%M'), max_length=5, required=True)
        self.titolo = discord.ui.TextInput(label="Titolo evento", placeholder="Es: Game Film JustChatting", max_length=100, required=True)
        self.max_p = discord.ui.TextInput(label="Max partecipanti (1-99) - Esempio 1 2 3", placeholder="Es: 1, 2, 3", default="", max_length=2, required=True)
        self.add_item(self.data)
        self.add_item(self.ora)
        self.add_item(self.titolo)
        self.add_item(self.max_p)

    async def on_submit(self, interaction: discord.Interaction):
        adesso = get_ora_italia()
        import re as re_mod
        data_str_raw = self.data.value.strip()
        m = re_mod.match(r"^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$", data_str_raw)
        if not m:
            await interaction.response.send_message("Data non valida! Usa GG/MM/AAAA es: 07/10/2026", ephemeral=True)
            return
        try:
            g = int(m.group(1)); mese = int(m.group(2)); anno = int(m.group(3))
            if not (1 <= g <= 31 and 1 <= mese <= 12 and 2024 <= anno <= 2030): raise ValueError()
            max_g = __import__('calendar').monthrange(anno, mese)[1]
            if g > max_g: raise ValueError(f"Il mese {mese} ha solo {max_g} giorni")
        except Exception as e:
            await interaction.response.send_message(f"Data non valida: {e}", ephemeral=True)
            return
        ora_str = self.ora.value.strip()
        try:
            if ":" in ora_str:
                h,mm = map(int, ora_str.split(":"))
            else:
                h = int(ora_str); mm = 0
            if not (0 <= h <= 23 and 0 <= mm <= 59): raise ValueError()
        except:
            await interaction.response.send_message("Ora non valida. Usa HH:MM es: 21:00", ephemeral=True)
            return
        try:
            max_partecipanti = int(self.max_p.value.strip())
            if not (1 <= max_partecipanti <= 99): raise ValueError()
        except:
            await interaction.response.send_message("Max partecipanti non valido! Metti un numero da 1 a 99", ephemeral=True)
            return
        data_evento = __import__('datetime').datetime(anno, mese, g, h, mm, tzinfo=ITALIA)
        if data_evento <= adesso:
            await interaction.response.send_message(f"Non puoi creare evento nel passato! Hai messo {g:02d}/{mese:02d}/{anno} {h:02d}:{mm:02d} ma ora e' {adesso.strftime('%d/%m/%Y %H:%M')}", ephemeral=True)
            return

        data_formattata = f"{g:02d}/{mese:02d}/{anno} ore {h:02d}:{mm:02d}"
        embed = __import__('discord').Embed(title=f"Evento del {data_formattata}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo.value, inline=False)
        embed.add_field(name="Partecipanti", value=f"0/{max_partecipanti} persone", inline=False)
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        view = EventoPartecipaView(max_partecipanti=max_partecipanti, titolo_evento=self.titolo.value, data_str=data_formattata, creatore=interaction.user.display_name)

        try:
            forum = interaction.client.get_channel(CANALE_FISSO_ID)
            if not forum:
                forum = await interaction.client.fetch_channel(CANALE_FISSO_ID)
            if isinstance(forum, __import__('discord').ForumChannel):
                titolo_lower = self.titolo.value.lower()
                def trova_tag():
                    tags_sorted = sorted(forum.available_tags, key=lambda t: len(t.name), reverse=True)
                    for tag in tags_sorted:
                        nome = tag.name.lower()
                        if "crea evento" in nome:
                            continue
                        if nome in titolo_lower:
                            if len(nome) >= 3:
                                return tag
                    mapping = {
                        "arc raiders": ["arc", "raiders"],
                        "arma reforger": ["arma", "reforger"],
                        "call of duty": ["cod", "call of duty", "warzone", "mw", "black ops"],
                        "dead by daylight": ["dead by daylight", "dbd", "dead by dayligh"],
                        "euro truck": ["euro truck", "ets2", "eurotruck"],
                        "farming simulator": ["farming", "fs22", "fs25"],
                        "fortnite": ["fortnite", "fn"],
                    }
                    for tag in forum.available_tags:
                        chiavi = mapping.get(tag.name.lower(), [tag.name.lower()])
                        for k in chiavi:
                            if k in titolo_lower:
                                return tag
                    for tag in forum.available_tags:
                        if "altro" in tag.name.lower():
                            return tag
                    for tag in forum.available_tags:
                        if "crea evento" not in tag.name.lower():
                            return tag
                    return None
                tag_scelto = trova_tag()
                applied = [tag_scelto] if tag_scelto else []
                thread_with_msg = await forum.create_thread(
                    name=f"{self.titolo.value} - {data_formattata}",
                    content=f"**{self.titolo.value}**\n📅 {data_formattata} - Creato da {interaction.user.mention}",
                    embed=embed,
                    view=view,
                    applied_tags=applied
                )
                tag_nome = tag_scelto.name if tag_scelto else "Altro"
                await interaction.response.send_message(f"✅ Evento creato in <#{CANALE_FISSO_ID}> con tag **{tag_nome}**!", ephemeral=True)
            else:
                await interaction.response.send_message(f"✅ Evento creato per {data_formattata}", ephemeral=True)
                await interaction.channel.send(embed=embed, view=view)
        except Exception as e:
            import traceback; traceback.print_exc()
            try:
                await interaction.response.send_message(f"✅ Evento creato per {data_formattata} (errore tag: {e})", ephemeral=True)
                await interaction.channel.send(embed=embed, view=view)
            except:
                pass


class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreaEventoModal())

CANALE_FISSO_ID = 1557509286911807629

class SoloBottoneView(discord.ui.View):
    def __init__(self, anno=None, mese=None):
        super().__init__(timeout=None)
        adesso = get_ora_italia()
        self.anno = anno or adesso.year
        self.mese = mese or adesso.month
        self.add_item(CreaEventoButton())
        # Rimuovi frecce mese - lasciamo solo Crea Evento

    def get_embed(self):
        # Solo embed pulito, senza calendario di testo grigio
        embed = discord.Embed(
            title="Crea il tuo Evento Qui - Calendario Eventi",
            description="Clicca **Crea Evento** qui sotto per creare un evento nel tag giusto",
            color=0x2b2d31
        )
        return embed


async def invia_post_fisso_calendario():
    await bot.wait_until_ready()
    try:
        canale = bot.get_channel(CANALE_FISSO_ID)
        if not canale:
            canale = await bot.fetch_channel(CANALE_FISSO_ID)
        if not canale:
            print(f"Canale {CANALE_FISSO_ID} non trovato")
            return
        # Controlla se c'è già un post del bot nelle ultime 20 msgs per non spammare
        async for msg in canale.history(limit=20):
            if msg.author == bot.user and "Ottobre" in str(msg.embeds[0].title if msg.embeds else ""):
                print("Post fisso già presente, skip")
                return
        adesso = get_ora_italia()
        view = SoloBottoneView(anno=adesso.year, mese=adesso.month)
        embed = view.get_embed()
        await canale.send(content="**Crea il tuo Evento Qui**", embed=embed, view=view)
        print(f"Post fisso inviato in {canale.name}")
    except Exception as e:
        print(f"Errore invio post fisso: {e}")

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
    bot.loop.create_task(invia_post_fisso_calendario())

@bot.tree.command(name="calendario", description="Mostra calendario + crea evento")
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
