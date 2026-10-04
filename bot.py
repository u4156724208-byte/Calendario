
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
    return "Blackout404 v27 ALLINEATO - ONLINE!"

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
    # FIX ALLINEAMENTO - ogni colonna 4 caratteri
    days_header = ["LUN","MAR","MER","GIO","VEN","SAB","DOM"]
    header = "".join([f"{d:>4}" for d in days_header])
    lines = [header]
    for week in cal:
        row = ""
        for day in week:
            if day == 0:
                row += "    "  # 4 spazi
            else:
                key = f"{year}-{month:02d}-{day:02d}"
                if key in events_db:
                    # [ 5] o [12] = 4 caratteri
                    row += f"[{day:2d}]"
                else:
                    #   5 o  12 + spazio = 4 caratteri
                    row += f"{day:>3} "
        lines.append(row)
    cal_text = "\n".join(lines)
    event_list = ""
    for date in sorted(events_db.keys()):
        if date.startswith(f"{year}-{month:02d}"):
            d = date.split("-")[2]
            for ev in sorted(events_db[date], key=lambda x: x.get('hour','00:00')):
                game_emoji = GAMES.get(ev.get('game'), {}).get('emoji','🎮')
                players = ev.get('players','?')
                leve = ev.get('leve','?')
                hour = ev.get('hour','?')
                event_list += f"**{d}** {game_emoji} {ev.get('game_name','?')} | 👥{players} | Leve:{leve} | 🕒 {hour}h\n"
    return cal_text, event_list

def create_calendar_embed(cal_text, event_list):
    desc = f"**Ottobre 2026**\n```\n{cal_text}\n```\n"
    desc += event_list if event_list else "*Nessun evento - clicca Crea Evento*"
    if len(desc) > 3500:
        desc = desc[:3500] + "\n..."
    embed = discord.Embed(title="CALENDARIO GIOCHI - Blackout404", description=desc, color=0x2f3136)
    embed.set_footer(text="v27 ALLINEATO • Colonne perfette • /calendario")
    return embed

def get_main_embed(view):
    today = datetime.datetime.now().day
    now_hour = datetime.datetime.now().hour
    game_txt = GAMES[view.game_id]['name'] if view.game_id else "❌ non scelto"
    day_txt = view.day if view.day else "❌ non scelto"
    hour_txt = view.hour if view.hour else "❌ non scelto"
    players_txt = view.players if view.players else "❌"
    leve_txt = view.leve if view.leve else "❌"
    
    if view.day and int(view.day) == today:
        hour_info = f"Solo da {now_hour+1}:00 a 23:00 (precedenti escluse)"
    else:
        hour_info = "00:00-23:00 tutte disponibili"
    
    desc = (
        f"**PANNELLO UNICO - Zero spam!**\n\n"
        f"🎮 **Gioco:** {game_txt}\n"
        f"📅 **Giorno:** {day_txt} (solo da oggi {today} a 31)\n"
        f"🕒 **Ora:** {hour_txt}\n"
        f"   └─ {hour_info}\n"
        f"👥 **Player:** {players_txt}\n"
        f"🔧 **Leve:** {leve_txt}\n\n"
        f"👇 Menu in ordine: Gioco → Giorno → Ora → Player → Leve+Conferma"
    )
    return discord.Embed(title="📅 Crea Evento - Pannello Unico", description=desc, color=0x00ff00)

class CreaEventoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.game_id = None
        self.day = None
        self.hour = None
        self.players = None
        self.leve = None
        self.add_item(GameSelectPanel(self))
        self.add_item(DaySelectPanel(self))
        self.add_item(HourSelectPanel(self))
        self.add_item(PlayersSelectPanel(self))

    async def update_embed(self, interaction):
        embed = get_main_embed(self)
        # ricrea ora se giorno cambia
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except:
            try:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
            except:
                try:
                    await interaction.response.defer()
                except:
                    pass

    @discord.ui.button(label="Leve SI", style=discord.ButtonStyle.primary, emoji="✅", row=4)
    async def leve_si(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.leve = "SI"
        await self.update_embed(interaction)

    @discord.ui.button(label="Leve NO", style=discord.ButtonStyle.secondary, emoji="❌", row=4)
    async def leve_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.leve = "NO"
        await self.update_embed(interaction)

    @discord.ui.button(label="✅ CONFERMA", style=discord.ButtonStyle.success, row=4)
    async def conferma(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not all([self.game_id, self.day, self.hour, self.players, self.leve]):
            missing = []
            if not self.game_id: missing.append("Gioco")
            if not self.day: missing.append("Giorno")
            if not self.hour: missing.append("Ora")
            if not self.players: missing.append("Player")
            if not self.leve: missing.append("Leve")
            embed = get_main_embed(self)
            embed.color = 0xff0000
            embed.add_field(name="❌ Manca", value=", ".join(missing), inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
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
        events_db[date_key] = sorted(events_db[date_key], key=lambda x: x["hour"])
        save_events(events_db)
        await interaction.response.edit_message(embed=discord.Embed(title="✅ Evento Creato!", description=f"**{self.day} Ottobre ore {self.hour}**\n{GAMES[self.game_id]['emoji']} {GAMES[self.game_id]['name']} | 👥{self.players} | Leve:{self.leve}", color=0x00ff00), view=None)

class GameSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = [
            discord.SelectOption(label=GAMES["arc_raiders"]["name"], value="arc_raiders", emoji="⚔️"),
            discord.SelectOption(label="Farming Simulator 25", value="fs25", emoji="🚜"),
            discord.SelectOption(label=GAMES["wardogs"]["name"], value="wardogs", emoji="🐺"),
        ]
        super().__init__(placeholder="🎮 1. Gioco...", options=options, row=0)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.game_id = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class DaySelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        today = datetime.datetime.now().day
        options = [discord.SelectOption(label=f"{d} Ottobre", value=str(d)) for d in range(today, 32)]
        super().__init__(placeholder=f"📅 2. Giorno (da {today} a 31 - solo futuri)", options=options[:25], row=1)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.day = self.values[0]
        self.parent_view_ref.hour = None
        # ricrea menu ore con filtro
        for child in list(self.parent_view_ref.children):
            if isinstance(child, HourSelectPanel):
                self.parent_view_ref.remove_item(child)
                break
        self.parent_view_ref.add_item(HourSelectPanel(self.parent_view_ref))
        await self.parent_view_ref.update_embed(interaction)

class HourSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        today = datetime.datetime.now().day
        now_hour = datetime.datetime.now().hour
        selected_day = int(parent_view.day) if parent_view.day else today
        
        options = []
        if selected_day == today:
            start_h = now_hour + 1
            if start_h >= 24:
                options.append(discord.SelectOption(label="Nessuna ora oggi - scegli domani", value="none", description="Oggi finite"))
            else:
                for h in range(start_h, 24):
                    options.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", description=f"Ore {h:02d}:00 disponibile"))
        else:
            for h in range(24):
                options.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00"))
        
        super().__init__(placeholder="🕒 3. Ora (24h - escluse precedenti)", options=options[:25], row=2)
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ Oggi non ci sono più ore! Scegli un giorno futuro", ephemeral=True)
            return
        self.parent_view_ref.hour = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class PlayersSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = [
            discord.SelectOption(label="1 Player", value="1"),
            discord.SelectOption(label="2 Player", value="2"),
            discord.SelectOption(label="3 Player", value="3"),
            discord.SelectOption(label="4 Player", value="4"),
        ]
        super().__init__(placeholder="👥 4. Player 1-4...", options=options, row=3)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.players = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", custom_id="crea_evento_v27")
    async def crea_evento(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = CreaEventoView()
        embed = get_main_embed(view)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    @discord.ui.button(label="Aggiorna", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="aggiorna_cal_v27")
    async def aggiorna(self, interaction: discord.Interaction, button: discord.ui.Button):
        cal_text, event_list = build_calendar_text()
        embed = create_calendar_embed(cal_text, event_list)
        await interaction.response.edit_message(embed=embed, view=self)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Blackout404 v27 online come {bot.user}")
    bot.add_view(CalendarioView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash: {len(synced)}")
    except Exception as e:
        print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="📅 Calendario Blackout404 v27")
async def calendario_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    cal_text, event_list = build_calendar_text()
    embed = create_calendar_embed(cal_text, event_list)
    await interaction.followup.send(embed=embed, view=CalendarioView())

@bot.tree.command(name="ping", description="Check ONLINE")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🏴 Blackout404 v27 ONLINE!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
