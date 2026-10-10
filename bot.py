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
COVER_IMAGE_PATH = "cover_C_corretta_finale.png"
COVER_FILE_NAME = "cover_C_corretta_finale.png"
CANALE_FISSO_ID = 1557509286911807629

def get_cover_file():
    if os.path.exists(COVER_IMAGE_PATH):
        return discord.File(COVER_IMAGE_PATH, filename=COVER_FILE_NAME)
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
        data_oggi = f"{adesso.day:02d}/{adesso.month:02d}/{adesso.year}"
        self.data = discord.ui.TextInput(label=f"Data GG/MM/AAAA - Oggi {data_oggi}", placeholder=f"Es: {data_oggi}", default=data_oggi, max_length=10, required=True)
        self.ora = discord.ui.TextInput(label=f"Ora HH:MM - Ora {adesso.strftime('%H:%M')}", placeholder="Es: 21:00", default=adesso.strftime('%H:%M'), max_length=5, required=True)
        self.titolo = discord.ui.TextInput(label="Titolo evento (scrivi gioco)", placeholder="Es: ARC Raiders LIVE", max_length=100, required=True)
        self.max_p = discord.ui.TextInput(label="Max partecipanti 1-99", placeholder="Es: 3", default="3", max_length=2, required=True)
        self.add_item(self.data)
        self.add_item(self.ora)
        self.add_item(self.titolo)
        self.add_item(self.max_p)

    async def on_submit(self, interaction: discord.Interaction):
        adesso = get_ora_italia()
        data_str_raw = self.data.value.strip()
        m = re.match(r"^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$", data_str_raw)
        if not m:
            await interaction.response.send_message("Data non valida! Usa GG/MM/AAAA", ephemeral=True)
            return
        try:
            g = int(m.group(1)); mese = int(m.group(2)); anno = int(m.group(3))
            max_g = calendar.monthrange(anno, mese)[1]
            if not (1 <= g <= 31 and 1 <= mese <= 12 and g <= max_g): raise ValueError()
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
            await interaction.response.send_message("Ora non valida. Usa HH:MM", ephemeral=True)
            return
        try:
            max_partecipanti = int(self.max_p.value.strip())
            if not (1 <= max_partecipanti <= 99): raise ValueError()
        except:
            await interaction.response.send_message("Max partecipanti non valido!", ephemeral=True)
            return
        data_evento = datetime.datetime(anno, mese, g, h, mm, tzinfo=ITALIA)
        if data_evento <= adesso:
            await interaction.response.send_message(f"Data nel passato! Ora e' {adesso.strftime('%d/%m/%Y %H:%M')}", ephemeral=True)
            return

        data_formattata = f"{g:02d}/{mese:02d}/{anno} ore {h:02d}:{mm:02d}"
        embed = discord.Embed(title=f"Evento del {data_formattata}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo.value, inline=False)
        embed.add_field(name="👤 Creatore", value=f"{interaction.user.display_name} ({interaction.user.mention})", inline=False)
        embed.add_field(name="Partecipanti", value=f"0/{max_partecipanti} persone", inline=False)
        embed.set_footer(text=f"Creato da {interaction.user.display_name} • {data_formattata}")
        view = EventoPartecipaView(max_partecipanti=max_partecipanti, titolo_evento=self.titolo.value, data_str=data_formattata, creatore=interaction.user.display_name)

        try:
            forum = interaction.client.get_channel(CANALE_FISSO_ID)
            if not forum:
                forum = await interaction.client.fetch_channel(CANALE_FISSO_ID)

            if isinstance(forum, discord.ForumChannel):
                titolo_lower = self.titolo.value.lower()
                print(f"[DEBUG TAG] Titolo ricevuto: '{self.titolo.value}' -> lower: '{titolo_lower}'")
                print(f"[DEBUG TAG] Tag disponibili: {[t.name for t in forum.available_tags]}")

                def trova_tag():
                    tags_sorted = sorted(forum.available_tags, key=lambda t: len(t.name), reverse=True)
                    # 1. match esatto nome tag dentro titolo
                    for tag in tags_sorted:
                        nome = tag.name.lower().strip()
                        if "crea evento" in nome:
                            continue
                        if nome in titolo_lower:
                            print(f"[DEBUG TAG] Match diretto: tag '{tag.name}' trovato in titolo")
                            return tag
                    # 2. match per parole chiave
                    parole_titolo = titolo_lower.split()
                    for tag in tags_sorted:
                        nome = tag.name.lower().strip()
                        if "crea evento" in nome:
                            continue
                        # se una parola del tag è nel titolo
                        for parola in nome.split():
                            if len(parola) >= 3 and parola in titolo_lower:
                                print(f"[DEBUG TAG] Match parola: '{parola}' di tag '{tag.name}' in titolo")
                                return tag
                        # se una parola del titolo è nel nome tag
                        for parola in parole_titolo:
                            if len(parola) >= 3 and parola in nome:
                                print(f"[DEBUG TAG] Match inverso: parola titolo '{parola}' in tag '{tag.name}'")
                                return tag
                    # 3. mapping speciale per abbreviazioni
                    mapping_speciale = {
                        "arc": ["arc raiders"],
                        "raiders": ["arc raiders"],
                        "arma": ["arma reforger", "arma"],
                        "reforger": ["arma reforger"],
                        "cod": ["call of duty", "cod"],
                        "warzone": ["call of duty", "warzone"],
                        "dbd": ["dead by daylight"],
                        "ets2": ["euro truck", "ets2"],
                        "farming": ["farming simulator"],
                        "fn": ["fortnite"],
                    }
                    for parola in parole_titolo:
                        if parola in mapping_speciale:
                            for nome_tag_cercato in mapping_speciale[parola]:
                                for tag in forum.available_tags:
                                    if nome_tag_cercato in tag.name.lower():
                                        print(f"[DEBUG TAG] Match mapping: parola '{parola}' -> tag '{tag.name}'")
                                        return tag
                    # 4. fallback Altro
                    for tag in forum.available_tags:
                        if "altro" in tag.name.lower():
                            print(f"[DEBUG TAG] Fallback Altro: {tag.name}")
                            return tag
                    # 5. primo tag utile
                    for tag in forum.available_tags:
                        if "crea evento" not in tag.name.lower():
                            print(f"[DEBUG TAG] Fallback primo utile: {tag.name}")
                            return tag
                    return None

                tag_scelto = trova_tag()
                applied = [tag_scelto] if tag_scelto else []
                
                # IMPORTANTE: niente cover per gli eventi, solo embed + bottoni
                await forum.create_thread(
                    name=f"{self.titolo.value} - {data_formattata}",
                    content=f"**{self.titolo.value}**\n📅 {data_formattata}\n👤 Creato da {interaction.user.mention} - {interaction.user.display_name}",
                    embed=embed,
                    view=view,
                    applied_tags=applied
                )
                tag_nome = tag_scelto.name if tag_scelto else "Altro"
                await interaction.response.send_message(f"✅ Evento creato in <#{CANALE_FISSO_ID}> con tag **{tag_nome}**!\n📅 {data_formattata}\n**Senza cover** come richiesto", ephemeral=True)
            else:
                await interaction.response.send_message(f"✅ Evento creato per {data_formattata}", ephemeral=True)
                await interaction.channel.send(embed=embed, view=view)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[ERRORE EVENTO] {e}")
            await interaction.response.send_message(f"Errore creazione: {e}", ephemeral=True)

class CreaEventoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅", custom_id="crea_evento_persistente")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreaEventoModal())

class SoloBottoneView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreaEventoButton())
    def get_embed(self):
        embed = discord.Embed(description="### Clicca **Crea Evento** qui sotto per creare un evento nel tag giusto", color=0x2b2d31)
        return embed

async def invia_post_fisso_calendario():
    await bot.wait_until_ready()
    try:
        canale = bot.get_channel(CANALE_FISSO_ID)
        if not canale:
            canale = await bot.fetch_channel(CANALE_FISSO_ID)
        if not canale:
            return
        if isinstance(canale, discord.ForumChannel):
            for thread in canale.threads:
                if "Crea il tuo Evento Qui" in thread.name and thread.owner_id == bot.user.id:
                    print("Guida già presente, skip")
                    return
        else:
            async for msg in canale.history(limit=30):
                if msg.author == bot.user and msg.embeds and any("Crea il tuo Evento Qui" in (e.title or "") for e in msg.embeds):
                    print("Guida già presente")
                    return
        view = SoloBottoneView()
        embed = view.get_embed()
        file_cover = get_cover_file()
        if file_cover:
            embed.set_image(url=f"attachment://{COVER_FILE_NAME}")
        if isinstance(canale, discord.ForumChannel):
            tag_crea = None
            for t in canale.available_tags:
                if "Crea Evento" in t.name:
                    tag_crea = t
                    break
            tags = [tag_crea] if tag_crea else []
            await canale.create_thread(name="Crea il tuo Evento Qui", content="**Crea il tuo Evento Qui - Calendario Eventi**", embed=embed, view=view, applied_tags=tags, file=file_cover)
        else:
            await canale.send(embed=embed, view=view, file=file_cover)
    except Exception as e:
        print(f"Errore guida: {e}")
        import traceback; traceback.print_exc()

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    # FIX TIMEOUT: registra le view persistenti
    bot.add_view(SoloBottoneView())
    try:
        await bot.tree.sync()
        print("Sync OK - view persistenti OK")
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
    view = SoloBottoneView()
    embed = view.get_embed()
    file_cover = get_cover_file()
    if file_cover:
        embed.set_image(url=f"attachment://{file_cover.filename}")
    await interaction.response.send_message("✅ Calendario inviato!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=view, file=file_cover)

@bot.tree.command(name="setup_calendario", description="Pubblica il post fisso")
async def setup_calendario(interaction: discord.Interaction):
    try:
        canale = bot.get_channel(CANALE_FISSO_ID)
        if not canale:
            canale = await bot.fetch_channel(CANALE_FISSO_ID)
        view = SoloBottoneView()
        embed = view.get_embed()
        file_cover = get_cover_file()
        if file_cover:
            embed.set_image(url=f"attachment://{file_cover.filename}")
        if isinstance(canale, discord.ForumChannel):
            tag_crea = None
            for t in canale.available_tags:
                if "Crea Evento" in t.name:
                    tag_crea = t
                    break
            tags = [tag_crea] if tag_crea else []
            await canale.create_thread(name="Crea il tuo Evento Qui", content="**Crea il tuo Evento Qui - Calendario Eventi**", embed=embed, view=view, applied_tags=tags, file=file_cover)
        else:
            await canale.send(embed=embed, view=view, file=file_cover)
        await interaction.response.send_message(f"✅ Post guida pubblicato in <#{CANALE_FISSO_ID}>", ephemeral=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    view = SoloBottoneView()
    embed = view.get_embed()
    file_cover = get_cover_file()
    if file_cover:
        embed.set_image(url=f"attachment://{file_cover.filename}")
    await ctx.send(embed=embed, view=view, file=file_cover)

bot.run(os.getenv("DISCORD_TOKEN"))
