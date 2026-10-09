import os, threading, datetime, calendar, re
from zoneinfo import ZoneInfo
from flask import Flask
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

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

# GENERATORE IMMAGINE CALENDARIO AUTO - si aggiorna col mese corrente
def create_calendar_image(year, month, output_path="/tmp/calendario_auto.png"):
    # Crea cover completa con logo + titolo + calendario dinamico
    W, H = 1200, 750
    bg_color = (13, 16, 28)
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Sfondo con leggera vignettatura blu
    try:
        font_title_big = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 62)
        font_sub = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 28)
        font_header = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 22)
        font_days = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 32)
        font_month = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font_title_big = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_days = ImageFont.load_default()
        font_month = ImageFont.load_default()

    # Logo Blackout - cerchio con B (se hai cover originale prova a incollare)
    # Disegna logo stilizzato
    logo_x, logo_y = 40, 35
    logo_r = 75
    # cerchio esterno ciano
    draw.ellipse([logo_x, logo_y, logo_x+logo_r*2, logo_y+logo_r*2], outline=(80, 220, 255), width=3)
    draw.ellipse([logo_x+8, logo_y+8, logo_x+logo_r*2-8, logo_y+logo_r*2-8], outline=(30, 80, 120), width=1)
    # B
    try:
        font_b = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 68)
    except:
        font_b = font_title_big
    draw.text((logo_x+42, logo_y+28), "B", fill=(120, 255, 230), font=font_b, anchor="mm")
    draw.text((logo_x+75, logo_y+150), "BLACKOUT", fill=(255,255,255), font=ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 12) if 'truetype' in str(type(font_title_big)) else font_month, anchor="mm")
    draw.text((logo_x+75, logo_y+168), "404", fill=(120, 180, 255), font=font_month, anchor="mm")

    # Titolo
    titolo1 = "Crea il tuo "
    titolo2 = "Evento Qui"
    # Misura
    x_title = 220
    y_title = 45
    draw.text((x_title, y_title), titolo1, fill=(255,255,255), font=font_title_big)
    w1 = draw.textbbox((0,0), titolo1, font=font_title_big)[2]
    draw.text((x_title + w1, y_title), titolo2, fill=(120, 255, 220), font=font_title_big)
    
    # Sottotitolo mese anno
    sub = f"{MESI_ITA[month-1]} {year} - Calendario Eventi"
    draw.text((x_title, y_title+75), sub, fill=(140, 160, 255), font=font_sub)

    # Calendario grid - stile come tua foto
    cell_w = 145
    cell_h = 68
    gap_x = 12
    gap_y = 10
    start_x = 60
    start_y = 180
    giorni_sett = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]
    
    # Header
    for i, g in enumerate(giorni_sett):
        x = start_x + i*(cell_w+gap_x)
        y = start_y
        draw.rounded_rectangle([x, y, x+cell_w, y+cell_h-8], radius=14, fill=(22, 38, 58), outline=(60, 100, 120))
        bbox = draw.textbbox((0,0), g, font=font_header)
        tw = bbox[2]-bbox[0]
        draw.text((x + (cell_w-tw)/2, y+14), g, fill=(110, 250, 220), font=font_header)

    # Giorni
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdays(year, month))
    start_y_days = start_y + cell_h + 12
    
    for idx, day in enumerate(month_days):
        if day == 0:
            continue
        col = idx % 7
        row = idx // 7
        x = start_x + col*(cell_w+gap_x)
        y = start_y_days + row*(cell_h+gap_y)
        draw.rounded_rectangle([x, y, x+cell_w, y+cell_h], radius=14, fill=(20, 28, 48), outline=(45, 65, 95))
        txt = str(day)
        bbox = draw.textbbox((0,0), txt, font=font_days)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        # Evidenzia oggi se è questo mese
        adesso = get_ora_italia()
        if day == adesso.day and month == adesso.month and year == adesso.year:
            draw.rounded_rectangle([x, y, x+cell_w, y+cell_h], radius=14, fill=(35, 90, 95), outline=(120, 255, 220), width=2)
            draw.text((x + (cell_w-tw)/2, y + (cell_h-th)/2), txt, fill=(120, 255, 220), font=font_days)
        else:
            draw.text((x + (cell_w-tw)/2, y + (cell_h-th)/2), txt, fill=(255,255,255), font=font_days)

    # Icone bottom
    draw.text((60, H-50), "🎮  🎧  ✨", fill=(80, 120, 200), font=font_sub)
    # Pill Nuovo Evento
    pill_x = W-260
    pill_y = H-60
    draw.rounded_rectangle([pill_x, pill_y, W-30, H-15], radius=20, fill=(45, 75, 180), outline=(120, 180, 255))
    draw.text((pill_x+28, pill_y+8), "+ Nuovo Evento", fill=(255,255,255), font=font_month)

    img.save(output_path)
    return output_path

def get_cover_file():
    adesso = get_ora_italia()
    path = f"/tmp/calendario_{adesso.year}_{adesso.month}.png"
    create_calendar_image(adesso.year, adesso.month, path)
    return discord.File(path, filename="calendario.png")

# Resta compatibile con vecchio nome
COVER_IMAGE_PATH = "cover_C_corretta_finale.png"
COVER_FILE_NAME = "calendario.png"

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

class CreaEventoModal(discord.ui.Modal, title="Crea Evento - scegli data completa"):
    def __init__(self):
        super().__init__()
        adesso = get_ora_italia()
        data_oggi = f"{adesso.day:02d}/{adesso.month:02d}/{adesso.year}"
        self.data = discord.ui.TextInput(label=f"Data (GG/MM/AAAA) - Oggi {data_oggi}", placeholder=f"Es: {data_oggi}", default=data_oggi, max_length=10, required=True)
        self.ora = discord.ui.TextInput(label=f"Ora (HH:MM) - Ora {adesso.strftime('%H:%M')}", placeholder="Es: 21:00", default=adesso.strftime('%H:%M'), max_length=5, required=True)
        self.titolo = discord.ui.TextInput(label="Titolo evento", placeholder="Es: ARC Raiders LIVE", max_length=100, required=True)
        self.max_p = discord.ui.TextInput(label="Max partecipanti (1-99)", placeholder="Es: 3", default="3", max_length=2, required=True)
        self.add_item(self.data)
        self.add_item(self.ora)
        self.add_item(self.titolo)
        self.add_item(self.max_p)

    async def on_submit(self, interaction: discord.Interaction):
        adesso = get_ora_italia()
        data_str_raw = self.data.value.strip()
        m = re.match(r"^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$", data_str_raw)
        if not m:
            await interaction.response.send_message("Data non valida! Usa GG/MM/AAAA es: 07/10/2026", ephemeral=True)
            return
        try:
            g = int(m.group(1)); mese = int(m.group(2)); anno = int(m.group(3))
            if not (1 <= g <= 31 and 1 <= mese <= 12 and 2024 <= anno <= 2030): raise ValueError()
            max_g = calendar.monthrange(anno, mese)[1]
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
        data_evento = datetime.datetime(anno, mese, g, h, mm, tzinfo=ITALIA)
        if data_evento <= adesso:
            await interaction.response.send_message(f"Non puoi creare evento nel passato! Hai messo {g:02d}/{mese:02d}/{anno} {h:02d}:{mm:02d} ma ora e' {adesso.strftime('%d/%m/%Y %H:%M')}", ephemeral=True)
            return

        data_formattata = f"{g:02d}/{mese:02d}/{anno} ore {h:02d}:{mm:02d}"
        embed = discord.Embed(title=f"Evento del {data_formattata}", color=0x00ff88)
        embed.add_field(name="Titolo", value=self.titolo.value, inline=False)
        embed.add_field(name="Partecipanti", value=f"0/{max_partecipanti} persone", inline=False)
        embed.set_footer(text=f"Creato da {interaction.user.display_name}")
        view = EventoPartecipaView(max_partecipanti=max_partecipanti, titolo_evento=self.titolo.value, data_str=data_formattata, creatore=interaction.user.display_name)

        try:
            forum = interaction.client.get_channel(CANALE_FISSO_ID)
            if not forum:
                forum = await interaction.client.fetch_channel(CANALE_FISSO_ID)
            if isinstance(forum, discord.ForumChannel):
                titolo_lower = self.titolo.value.lower()
                def trova_tag():
                    tags_sorted = sorted(forum.available_tags, key=lambda t: len(t.name), reverse=True)
                    for tag in tags_sorted:
                        nome = tag.name.lower()
                        if "crea evento" in nome:
                            continue
                        if nome in titolo_lower and len(nome) >= 3:
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
                await forum.create_thread(
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
    def get_embed(self):
        embed = discord.Embed(title="Crea il tuo Evento Qui - Calendario Eventi", description="Clicca **Crea Evento** qui sotto per creare un evento nel tag giusto", color=0x2b2d31)
        return embed

async def trova_e_aggiorna_copertina():
    """Trova il post guida del calendario e aggiorna l'immagine con il mese corrente"""
    try:
        canale = bot.get_channel(CANALE_FISSO_ID)
        if not canale:
            canale = await bot.fetch_channel(CANALE_FISSO_ID)
        if not canale:
            return False

        adesso = get_ora_italia()
        nuovo_file = get_cover_file()
        view = SoloBottoneView()
        nuovo_embed = view.get_embed()
        nuovo_embed.title = f"Crea il tuo Evento Qui - {MESI_ITA[adesso.month-1]} {adesso.year}"
        nuovo_embed.set_image(url=f"attachment://{nuovo_file.filename}")

        aggiornati = 0

        if isinstance(canale, discord.ForumChannel):
            # Cerca nei thread attivi
            for thread in canale.threads:
                if "Crea il tuo Evento Qui" in thread.name and thread.owner_id == bot.user.id:
                    try:
                        # Prendi il primo messaggio del thread (quello con l'immagine)
                        async for msg in thread.history(limit=1, oldest_first=True):
                            await msg.edit(embed=nuovo_embed, attachments=[nuovo_file], view=view)
                            aggiornati += 1
                            print(f"Aggiornato thread {thread.name} con mese {adesso.month}/{adesso.year}")
                    except Exception as e:
                        print(f"Errore aggiornamento thread {thread.id}: {e}")
            
            # Cerca anche negli archiviati
            try:
                async for thread in canale.archived_threads(limit=100):
                    if "Crea il tuo Evento Qui" in thread.name and thread.owner_id == bot.user.id:
                        try:
                            async for msg in thread.history(limit=1, oldest_first=True):
                                await msg.edit(embed=nuovo_embed, attachments=[nuovo_file], view=view)
                                aggiornati += 1
                        except:
                            pass
            except:
                pass
        else:
            # Canale testo normale
            async for msg in canale.history(limit=100):
                if msg.author == bot.user and msg.embeds:
                    if any("Crea il tuo Evento Qui" in (e.title or "") for e in msg.embeds):
                        try:
                            await msg.edit(embed=nuovo_embed, attachments=[nuovo_file], view=view)
                            aggiornati += 1
                            print(f"Aggiornato messaggio {msg.id} con mese {adesso.month}/{adesso.year}")
                        except Exception as e:
                            print(f"Errore aggiornamento msg: {e}")

        return aggiornati > 0
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Errore trova_e_aggiorna: {e}")
        return False

async def invia_post_fisso_calendario():
    await bot.wait_until_ready()
    try:
        canale = bot.get_channel(CANALE_FISSO_ID)
        if not canale:
            canale = await bot.fetch_channel(CANALE_FISSO_ID)
        if not canale:
            return
        
        # Se esiste già, non spammare - ma se è del mese scorso, aggiornalo
        async for msg in canale.history(limit=30):
            if msg.author == bot.user and msg.embeds:
                if any("Crea il tuo Evento Qui" in (e.title or "") for e in msg.embeds):
                    print("Post fisso già presente, skip invio")
                    return
        
        # Se siamo in un forum, controlla anche i thread
        if isinstance(canale, discord.ForumChannel):
            for thread in canale.threads:
                if "Crea il tuo Evento Qui" in thread.name and thread.owner_id == bot.user.id:
                    print("Thread guida già presente, skip invio")
                    return

        view = SoloBottoneView()
        embed = view.get_embed()
        adesso = get_ora_italia()
        embed.title = f"Crea il tuo Evento Qui - {MESI_ITA[adesso.month-1]} {adesso.year}"
        file_cover = get_cover_file()
        embed.set_image(url=f"attachment://{file_cover.filename}")

        if isinstance(canale, discord.ForumChannel):
            tag_crea = None
            for t in canale.available_tags:
                if "Crea Evento" in t.name:
                    tag_crea = t
                    break
            tags = [tag_crea] if tag_crea else []
            await canale.create_thread(
                name="Crea il tuo Evento Qui",
                content=f"**Crea il tuo Evento Qui - Calendario Eventi {MESI_ITA[adesso.month-1]} {adesso.year}**",
                embed=embed,
                view=view,
                applied_tags=tags,
                file=file_cover
            )
        else:
            await canale.send(content=f"**Crea il tuo Evento Qui - {MESI_ITA[adesso.month-1]} {adesso.year}**", embed=embed, view=view, file=file_cover)
        print(f"Post fisso inviato con mese {adesso.month}/{adesso.year}")
    except Exception as e:
        print(f"Errore invio post fisso: {e}")
        import traceback; traceback.print_exc()

# TASK AUTOMATICO: ogni ora controlla se è cambiato il mese, se sì aggiorna l'immagine di copertina
async def task_aggiornamento_mensile():
    await bot.wait_until_ready()
    print("Task aggiornamento mensile avviato")
    ultimo_mese = get_ora_italia().month
    ultimo_anno = get_ora_italia().year
    
    while not bot.is_closed():
        try:
            await asyncio.sleep(3600)  # controlla ogni ora
            adesso = get_ora_italia()
            # Se è cambiato mese/anno
            if adesso.month != ultimo_mese or adesso.year != ultimo_anno:
                print(f"Nuovo mese rilevato: {MESI_ITA[adesso.month-1]} {adesso.year} - aggiorno copertina")
                success = await trova_e_aggiorna_copertina()
                if success:
                    print(f"Copertina aggiornata a {MESI_ITA[adesso.month-1]} {adesso.year}")
                else:
                    print("Nessun post da aggiornare trovato, ne creo uno nuovo")
                    await invia_post_fisso_calendario()
                ultimo_mese = adesso.month
                ultimo_anno = adesso.year
            
            # Inoltre, ogni giorno 1 alle 00:05 forza l'aggiornamento (sicurezza)
            if adesso.day == 1 and adesso.hour == 0 and adesso.minute < 60:
                # controlla se l'ultimo aggiornamento era vecchio
                print("E' il primo del mese, forzo aggiornamento copertina")
                await trova_e_aggiorna_copertina()
                
        except Exception as e:
            print(f"Errore task mensile: {e}")
            import traceback; traceback.print_exc()
            await asyncio.sleep(3600)

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
    bot.loop.create_task(task_aggiornamento_mensile())

@bot.tree.command(name="calendario", description="Mostra calendario + crea evento")
async def calendario(interaction: discord.Interaction):
    view = SoloBottoneView()
    embed = view.get_embed()
    file_cover = get_cover_file()
    embed.set_image(url=f"attachment://{file_cover.filename}")
    await interaction.response.send_message("✅ Calendario inviato qui sotto!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=view, file=file_cover)

@bot.tree.command(name="setup_calendario", description="Pubblica il post fisso con calendario nel canale dedicato")
async def setup_calendario(interaction: discord.Interaction):
    try:
        canale = bot.get_channel(CANALE_FISSO_ID)
        if not canale:
            canale = await bot.fetch_channel(CANALE_FISSO_ID)
        view = SoloBottoneView()
        embed = view.get_embed()
        file_cover = get_cover_file()
        embed.set_image(url=f"attachment://{file_cover.filename}")
        if isinstance(canale, discord.ForumChannel):
            tag_crea = None
            for t in canale.available_tags:
                if "Crea Evento" in t.name:
                    tag_crea = t
                    break
            tags = [tag_crea] if tag_crea else []
            await canale.create_thread(
                name="Crea il tuo Evento Qui",
                content="**Crea il tuo Evento Qui - Calendario Eventi**",
                embed=embed,
                view=view,
                applied_tags=tags,
                file=file_cover
            )
        else:
            await canale.send(content="**Crea il tuo Evento Qui**", embed=embed, view=view, file=file_cover)
        await interaction.response.send_message(f"✅ Post pubblicato in <#{CANALE_FISSO_ID}> con calendario auto {get_ora_italia().month}/{get_ora_italia().year}", ephemeral=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    view = SoloBottoneView()
    embed = view.get_embed()
    file_cover = get_cover_file()
    embed.set_image(url=f"attachment://{file_cover.filename}")
    await ctx.send(embed=embed, view=view, file=file_cover)

bot.run(os.getenv("DISCORD_TOKEN"))
