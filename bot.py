
import os, threading, datetime, calendar, re, time
from zoneinfo import ZoneInfo
from flask import Flask
import discord
from discord.ext import commands

app = Flask(__name__)
@app.route("/")
def home(): return "Calendario Bot OK - UptimeRobot OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    print(f"[WEB] Avvio Flask su porta {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

threading.Thread(target=run_web, daemon=True).start()
time.sleep(2)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ITALIA = ZoneInfo("Europe/Rome")
COVER_IMAGE_PATH = "cover_C_corretta_finale.png"
CANALE_FISSO_ID = 1557509286911807629

def get_cover_file():
    if os.path.exists(COVER_IMAGE_PATH):
        return discord.File(COVER_IMAGE_PATH, filename="cover_C_corretta_finale.png")
    return None

def get_ora_italia():
    return datetime.datetime.now(ITALIA)

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
            await interaction.response.send_message("Hai gia partecipato!", ephemeral=True); return
        if len(self.partecipanti) >= self.max_p:
            await interaction.response.send_message(f"Pieno! Max {self.max_p}", ephemeral=True); return
        self.partecipanti.append({"id": user_id, "name": interaction.user.display_name})
        embed = discord.Embed(title=f"Evento del {self.data_str}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo_evento, inline=False)
        lista = "\n".join([f"• {p['name']}" for p in self.partecipanti])
        embed.add_field(name="Partecipanti", value=f"{len(self.partecipanti)}/{self.max_p}\n{lista}", inline=False)
        embed.set_footer(text=f"Creato da {self.creatore}")
        if len(self.partecipanti) >= self.max_p:
            button.disabled=True; button.label="Pieno"; button.style=discord.ButtonStyle.gray
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Esci", style=discord.ButtonStyle.red, emoji="❌", custom_id="esci_btn")
    async def esci(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not any(p["id"] == user_id for p in self.partecipanti):
            await interaction.response.send_message("Non partecipi", ephemeral=True); return
        self.partecipanti = [p for p in self.partecipanti if p["id"] != user_id]
        embed = discord.Embed(title=f"Evento del {self.data_str}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo_evento, inline=False)
        if self.partecipanti:
            lista = "\n".join([f"• {p['name']}" for p in self.partecipanti])
            val = f"{len(self.partecipanti)}/{self.max_p}\n{lista}"
        else:
            val = f"0/{self.max_p}"
        embed.add_field(name="Partecipanti", value=val, inline=False)
        embed.set_footer(text=f"Creato da {self.creatore}")
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "partecipa_btn":
                child.disabled=False; child.label="Partecipa"; child.style=discord.ButtonStyle.green
        await interaction.response.edit_message(embed=embed, view=self)

class CreaEventoModal(discord.ui.Modal, title="Crea Evento"):
    def __init__(self):
        super().__init__()
        adesso = get_ora_italia()
        data_oggi = f"{adesso.day:02d}/{adesso.month:02d}/{adesso.year}"
        self.data = discord.ui.TextInput(label=f"Data GG/MM/AAAA Oggi {data_oggi}", placeholder=data_oggi, default=data_oggi, max_length=10, required=True)
        self.ora = discord.ui.TextInput(label=f"Ora HH:MM Ora {adesso.strftime('%H:%M')}", placeholder="21:00", default=adesso.strftime('%H:%M'), max_length=5, required=True)
        self.titolo = discord.ui.TextInput(label="Titolo evento (gioco)", placeholder="ARC Raiders LIVE", max_length=100, required=True)
        self.max_p = discord.ui.TextInput(label="Max 1-99", placeholder="3", default="3", max_length=2, required=True)
        self.add_item(self.data); self.add_item(self.ora); self.add_item(self.titolo); self.add_item(self.max_p)

    async def on_submit(self, interaction: discord.Interaction):
        # DEFER IMMEDIATO per evitare timeout
        await interaction.response.defer(ephemeral=True, thinking=True)
        adesso = get_ora_italia()
        data_str_raw = self.data.value.strip()
        m = re.match(r"^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$", data_str_raw)
        if not m:
            await interaction.followup.send("Data non valida GG/MM/AAAA", ephemeral=True); return
        try:
            g=int(m.group(1)); mese=int(m.group(2)); anno=int(m.group(3))
            max_g=calendar.monthrange(anno,mese)[1]
            if not (1<=g<=31 and 1<=mese<=12 and g<=max_g): raise ValueError()
        except:
            await interaction.followup.send("Data non valida", ephemeral=True); return
        ora_str=self.ora.value.strip()
        try:
            if ":" in ora_str: h,mm=map(int,ora_str.split(":"))
            else: h=int(ora_str); mm=0
            if not (0<=h<=23 and 0<=mm<=59): raise ValueError()
        except:
            await interaction.followup.send("Ora non valida HH:MM", ephemeral=True); return
        try:
            max_partecipanti=int(self.max_p.value.strip())
            if not (1<=max_partecipanti<=99): raise ValueError()
        except:
            await interaction.followup.send("Max non valido", ephemeral=True); return
        from datetime import datetime as dt
        try:
            data_evento=dt(anno,mese,g,h,mm,tzinfo=ITALIA)
            if data_evento<=adesso:
                await interaction.followup.send(f"Data nel passato! Ora {adesso.strftime('%d/%m/%Y %H:%M')}", ephemeral=True); return
        except Exception as e:
            await interaction.followup.send(f"Errore data {e}", ephemeral=True); return
        data_formattata=f"{g:02d}/{mese:02d}/{anno} ore {h:02d}:{mm:02d}"
        view=EventoPartecipaView(max_partecipanti=max_partecipanti, titolo_evento=self.titolo.value, data_str=data_formattata, creatore=interaction.user.display_name)
        view.partecipanti.append({"id": interaction.user.id, "name": interaction.user.display_name})
        embed=discord.Embed(title=f"Evento del {data_formattata}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo.value, inline=False)
        embed.add_field(name="Partecipanti", value=f"1/{max_partecipanti}\n• {interaction.user.display_name}", inline=False)
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        try:
            forum=bot.get_channel(CANALE_FISSO_ID)
            if not forum: forum=await bot.fetch_channel(CANALE_FISSO_ID)
            if isinstance(forum, discord.ForumChannel):
                titolo_lower=self.titolo.value.lower()
                def trova_tag():
                    tags_sorted=sorted(forum.available_tags, key=lambda t: len(t.name), reverse=True)
                    for tag in tags_sorted:
                        nome=tag.name.lower().strip()
                        if "crea evento" in nome: continue
                        if nome in titolo_lower: return tag
                    for tag in tags_sorted:
                        nome=tag.name.lower().strip()
                        if "crea evento" in nome: continue
                        for parola in nome.split():
                            if len(parola)>=3 and parola in titolo_lower: return tag
                    for tag in forum.available_tags:
                        if "altro" in tag.name.lower(): return tag
                    for tag in forum.available_tags:
                        if "crea evento" not in tag.name.lower(): return tag
                    return None
                tag_scelto=trova_tag()
                applied=[tag_scelto] if tag_scelto else []
                await forum.create_thread(name=f"{self.titolo.value} - {data_formattata}", content=f"📅 {data_formattata}\n👤 {interaction.user.mention}", embed=embed, view=view, applied_tags=applied)
                tag_nome=tag_scelto.name if tag_scelto else "Altro"
                await interaction.followup.send(f"✅ Evento creato in <#{CANALE_FISSO_ID}> tag **{tag_nome}**! 📅 {data_formattata}", ephemeral=True)
            else:
                await interaction.followup.send(f"✅ Evento creato {data_formattata}", ephemeral=True)
                await interaction.channel.send(embed=embed, view=view)
        except Exception as e:
            import traceback; traceback.print_exc()
            await interaction.followup.send(f"Errore: {e}", ephemeral=True)

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅", custom_id="crea_evento_btn")
    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(CreaEventoModal())
        except Exception as e:
            print(f"send_modal err {e}")

class SoloBottoneView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())
    def get_embed(self):
        return discord.Embed(title="Crea il tuo Evento Qui - Calendario Eventi", description="Clicca **Crea Evento** qui sotto", color=0x2b2d31)

async def invia_post_fisso_calendario():
    await bot.wait_until_ready()
    try:
        canale=bot.get_channel(CANALE_FISSO_ID)
        if not canale: canale=await bot.fetch_channel(CANALE_FISSO_ID)
        if not canale: return
    except: return

@bot.event
async def on_ready():
    print(f"[BOT] Online {bot.user}")
    bot.add_view(SoloBottoneView())
    bot.add_view(EventoPartecipaView(99,"x","x","x"))
    try:
        synced=await bot.tree.sync()
        print(f"[BOT] Sync {len(synced)} comandi OK")
    except Exception as e: print(e)

@bot.tree.command(name="calendario", description="Mostra calendario + crea evento")
async def calendario(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    view=SoloBottoneView()
    embed=view.get_embed()
    file_cover=get_cover_file()
    if file_cover: embed.set_image(url=f"attachment://{file_cover.filename}")
    await interaction.followup.send("Calendario qui sotto", ephemeral=True)
    await interaction.channel.send(embed=embed, view=view, file=file_cover)

@bot.tree.command(name="setup_calendario", description="Pubblica post fisso")
async def setup_calendario(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        canale=bot.get_channel(CANALE_FISSO_ID)
        if not canale: canale=await bot.fetch_channel(CANALE_FISSO_ID)
        view=SoloBottoneView()
        embed=view.get_embed()
        file_cover=get_cover_file()
        if file_cover: embed.set_image(url=f"attachment://{file_cover.filename}")
        if isinstance(canale, discord.ForumChannel):
            tag_crea=None
            for t in canale.available_tags:
                if "Crea Evento" in t.name: tag_crea=t; break
            tags=[tag_crea] if tag_crea else []
            await canale.create_thread(name="Crea il tuo Evento Qui", content="**Crea il tuo Evento Qui**", embed=embed, view=view, applied_tags=tags, file=file_cover)
        else:
            await canale.send(embed=embed, view=view, file=file_cover)
        await interaction.followup.send(f"Post pubblicato in <#{CANALE_FISSO_ID}>", ephemeral=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        await interaction.followup.send(f"Errore: {e}", ephemeral=True)

TOKEN=os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("[ERRORE] DISCORD_TOKEN mancante - web server vivo")
    while True: time.sleep(60)
else:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[BOT] Crash {e}")
        import traceback; traceback.print_exc()
        while True: time.sleep(60)
