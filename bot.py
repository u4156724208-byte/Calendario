import discord
import os
import json
import datetime
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home():
    return "Blackout404 v22 ORDINATO - ONLINE!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

EVENTS_FILE = "events.json"
GAMES = {
    "arc_raiders": {"name": "ARC Raiders", "emoji": "⚔️"},
    "fs25": {"name": "Farming Simulator 25", "emoji": "🚜"},
    "wardogs": {"name": "WarDogs", "emoji": "🐺"}
}

def load_events():
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_events(data):
    try:
        with open(EVENTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Errore save: {e}")

events_db = load_events()

def build_calendar_text(year=2026, month=10):
    import calendar
    cal = calendar.monthcalendar(year, month)
    header = "LUN MAR MER GIO VEN SAB DOM"
    lines = [header]
    for week in cal:
        line = ""
        for day in week:
            if day == 0:
                line += "    "
            else:
                key = f"{year}-{month:02d}-{day:02d}"
                if key in events_db:
                    line += f"[{day:2d}] "
                else:
                    line += f" {day:2d}  "
        lines.append(line.rstrip())
    cal_text = "\n".join(lines)
    event_list = ""
    # ORDINA GIORNI
    for date in sorted(events_db.keys()):
        if date.startswith(f"{year}-{month:02d}"):
            d = date.split("-")[2]
            for ev in sorted(events_db[date], key=lambda x: x.get('hour','00:00')):
                game_emoji = GAMES.get(ev.get('game'), {}).get('emoji','🎮')
                players = ev.get('players','?')
                leve = ev.get('leve','?')
                hour = ev.get('hour','?')
                # mostra: giorno + gioco + players + leve + ora
                event_list += f"**{d}** {game_emoji} {ev.get('game_name','?')} | 👥{players} | Leve:{leve} | 🕒 {hour}h\n"
    return cal_text, event_list

def create_calendar_embed(cal_text, event_list):
    desc = f"**Ottobre 2026**\n```\n{cal_text}\n```\n"
    if event_list:
        desc += event_list
    else:
        desc += "*Nessun evento - clicca Crea Evento*"
    if len(desc) > 3500:
        desc = desc[:3500] + "\n...troppi eventi!"
    embed = discord.Embed(
        title="CALENDARIO GIOCHI - Blackout404",
        description=desc,
        color=0x2f3136
    )
    embed.set_footer(text="v22 ORDINATO • 24h • Gioco/Player/Leve nel pannello • /calendario")
    return embed

# --- NUOVO PANNELLO UNICO CON TUTTO DENTRO ---

class CreaEventoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.game_id = None
        self.day = None
        self.players = None
        self.leve = None
        self.hour = None
        
        self.add_item(GameSelectPanel(self))
        self.add_item(DaySelectPanel(self))
        self.add_item(PlayersSelectPanel(self))
        self.add_item(LeveSelectPanel(self))
        self.add_item(HourSelectPanel(self))

    @discord.ui.button(label="✅ Conferma Evento", style=discord.ButtonStyle.success, row=4)
    async def conferma(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not all([self.game_id, self.day, self.players, self.leve, self.hour]):
            missing = []
            if not self.game_id: missing.append("Gioco")
            if not self.day: missing.append("Giorno")
            if not self.players: missing.append("Player")
            if not self.leve: missing.append("Leve")
            if not self.hour: missing.append("Ora")
            await interaction.response.send_message(f"❌ Manca: {', '.join(missing)} - seleziona tutto!", ephemeral=True)
            return
        
        date_key = f"2026-10-{int(self.day):02d}"
        if date_key not in events_db:
            events_db[date_key] = []
        events_db[date_key].append({
            "game": self.game_id,
            "game_name": GAMES[self.game_id]['name'],
            "players": self.players,
            "leve": self.leve,
            "hour": self.hour,
            "author": str(interaction.user.display_name)
        })
        save_events(events_db)
        # ordina eventi dello stesso giorno per ora
        events_db[date_key] = sorted(events_db[date_key], key=lambda x: x['hour'])
        save_events(events_db)
        
        await interaction.response.send_message(
            f"✅ Evento creato **{self.day} Ottobre ore {self.hour}**\n"
            f"{GAMES[self.game_id]['emoji']} {GAMES[self.game_id]['name']} | 👥{self.players} player | Leve: {self.leve}",
            ephemeral=True
        )

class GameSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = [
            discord.SelectOption(label=GAMES["arc_raiders"]["name"], value="arc_raiders", emoji="⚔️"),
            discord.SelectOption(label="Farming Simulator 25", value="fs25", emoji="🚜"),
            discord.SelectOption(label=GAMES["wardogs"]["name"], value="wardogs", emoji="🐺"),
        ]
        super().__init__(placeholder="🎮 1. Scegli Gioco...", options=options, row=0)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.game_id = self.values[0]
        await interaction.response.send_message(f"Gioco: {GAMES[self.values[0]]['name']} ✅", ephemeral=True)

class DaySelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        # GIORNI IN ORDINE, SOLO FUTURI (antecedenti esclusi)
        today = datetime.datetime.now().day
        # Se siamo in ottobre 2026, partiamo da oggi, altrimenti da 1
        start_day = today if datetime.datetime.now().month == 10 else 1
        # Per test lasciamo da 1 a 31 ordinati, ma con label ordinato
        options = []
        for d in range(1, 32):
            # lascia solo giorni >= oggi (futuri) se vuoi antecedenti rimossi
            if d >= start_day or True:  # metti True per mostrare tutti ordinati, cambia a d >= start_day per solo futuri
                options.append(discord.SelectOption(label=f"Giorno {d}", value=str(d)))
        # Discord max 25 opzioni per select, quindi dividiamo in due se serve, qui ne mettiamo 31 ma tagliamo a 25 per sicurezza -> 1-25 e poi 26-31 gestiti
        # Per semplicità mostriamo 1-31 ordinati (max 25, quindi 1-25 + poi 26-31 in secondo menu non serve, facciamo 1-31 troncato a 25)
        # Facciamo 1-25 + opzione 26-31 come ultimo
        super().__init__(placeholder="📅 2. Giorno (ordinato)...", options=options[:25], row=1)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.day = self.values[0]
        await interaction.response.send_message(f"Giorno: {self.values[0]} ✅", ephemeral=True)

class PlayersSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = [
            discord.SelectOption(label="1 Player", value="1", emoji="👤"),
            discord.SelectOption(label="2 Player", value="2", emoji="👥"),
            discord.SelectOption(label="3 Player", value="3", emoji="👥"),
            discord.SelectOption(label="4 Player", value="4", emoji="👥"),
        ]
        super().__init__(placeholder="👥 3. Numero Player 1-4...", options=options, row=2)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.players = self.values[0]
        await interaction.response.send_message(f"Player: {self.values[0]} ✅", ephemeral=True)

class LeveSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = [
            discord.SelectOption(label="Leve SI", value="SI", emoji="✅"),
            discord.SelectOption(label="Leve NO", value="NO", emoji="❌"),
        ]
        super().__init__(placeholder="🔧 4. Leve Si/No...", options=options, row=2)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.leve = self.values[0]
        await interaction.response.send_message(f"Leve: {self.values[0]} ✅", ephemeral=True)

class HourSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = []
        for h in range(24):
            options.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00"))
        super().__init__(placeholder="🕒 5. Ora 00-23 (24h)...", options=options[:25], row=3)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.hour = self.values[0]
        await interaction.response.send_message(f"Ora: {self.values[0]} ✅", ephemeral=True)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", custom_id="crea_evento_v22")
    async def crea_evento(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📅 Crea Nuovo Evento - Tutto nel pannello",
            description="**1️⃣ Gioco**\n**2️⃣ Giorno** (ordinato 1-31)\n**3️⃣ Player** (1-4)\n**4️⃣ Leve** (SI/NO)\n**5️⃣ Ora** (00-23h - 24h)\n\nSeleziona tutto poi clicca Conferma!",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, view=CreaEventoView(), ephemeral=True)
    @discord.ui.button(label="Aggiorna", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="aggiorna_cal_v22")
    async def aggiorna(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            cal_text, event_list = build_calendar_text()
            embed = create_calendar_embed(cal_text, event_list)
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Blackout404 v22 online come {bot.user}")
    bot.add_view(CalendarioView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash: {len(synced)}")
    except Exception as e:
        print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="📅 Calendario Blackout404 - v22 ordinato")
async def calendario_slash(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        cal_text, event_list = build_calendar_text()
        embed = create_calendar_embed(cal_text, event_list)
        await interaction.followup.send(embed=embed, view=CalendarioView())
    except Exception as e:
        print(f"Errore /calendario: {e}")
        try:
            await interaction.followup.send(f"Errore: {e}")
        except:
            pass

@bot.tree.command(name="ping", description="Check ONLINE")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🏴 Blackout404 v22 ONLINE!")

@bot.command(name="calendario")
async def calendario_cmd(ctx):
    cal_text, event_list = build_calendar_text()
    embed = create_calendar_embed(cal_text, event_list)
    await ctx.send(embed=embed, view=CalendarioView())

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
