
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
    return "Blackout404 v26 PULITO FIX - ONLINE!"

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
    header = "LUN  MAR  MER  GIO  VEN  SAB  DOM"
    lines = [header]
    for week in cal:
        row = ""
        for day in week:
            if day == 0:
                row += "     "
            else:
                key = f"{year}-{month:02d}-{day:02d}"
                if key in events_db:
                    row += f"[{day:2d}] "
                else:
                    row += f" {day:2d}  "
        lines.append(row.rstrip())
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
    embed.set_footer(text="v26 PULITO • Colonne allineate • Solo futuri • /calendario")
    return embed

def get_main_embed(view):
    today = datetime.datetime.now().day
    now_hour = datetime.datetime.now().hour
    game_txt = GAMES[view.game_id]['name'] if view.game_id else "❌ non scelto"
    day_txt = view.day if view.day else "❌ non scelto"
    players_txt = view.players if view.players else "❌"
    leve_txt = view.leve if view.leve else "❌"
    hour_info = f"Ore: escluse <={now_hour}:00 se oggi" if view.day and int(view.day)==today else "Ore: 00-23 tutte"
    desc = (
        f"**PANNELLO UNICO - Zero spam!**\n\n"
        f"🎮 **Gioco:** {game_txt}\n"
        f"📅 **Giorno:** {day_txt} (solo da oggi {today} a 31)\n"
        f"   └─ {hour_info}\n"
        f"👥 **Player:** {players_txt}\n"
        f"🔧 **Leve:** {leve_txt}\n\n"
        f"Seleziona i 4 menu sotto 👇 - Si aggiorna qui!"
    )
    return discord.Embed(title="📅 Crea Evento - Pannello Unico Pulito", description=desc, color=0x00ff00)

class HourModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Ora 24h - solo future")
        self.parent_view_ref = parent_view
        today = datetime.datetime.now().day
        now_hour = datetime.datetime.now().hour
        sel_day = int(parent_view.day) if parent_view.day else today
        if sel_day == today:
            ph = f"Es: {now_hour+1}:00 a 23:00"
        else:
            ph = "Es: 21:00"
        self.hour_input = discord.ui.TextInput(label="Ora 24h (escluse precedenti se oggi)", placeholder=ph, max_length=5, required=True)
        self.add_item(self.hour_input)

    async def on_submit(self, interaction: discord.Interaction):
        hour_str = self.hour_input.value.strip()
        try:
            parts = hour_str.split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts)>1 else 0
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            today = datetime.datetime.now().day
            now_h = datetime.datetime.now().hour
            if int(self.parent_view_ref.day) == today and h <= now_h:
                await interaction.response.send_message(f"❌ Ora {h:02d}:00 già passata! Scegli da {now_h+1}:00", ephemeral=True)
                return
            hour_fmt = f"{h:02d}:{m:02d}"
        except:
            await interaction.response.send_message("❌ Formato non valido! Usa 14:00", ephemeral=True)
            return
        date_key = f"2026-10-{int(self.parent_view_ref.day):02d}"
        if date_key not in events_db:
            events_db[date_key] = []
        events_db[date_key].append({
            "game": self.parent_view_ref.game_id,
            "game_name": GAMES[self.parent_view_ref.game_id]['name'],
            "players": self.parent_view_ref.players,
            "leve": self.parent_view_ref.leve,
            "hour": hour_fmt,
            "author": str(interaction.user.display_name)
        })
        events_db[date_key] = sorted(events_db[date_key], key=lambda x: x["hour"])
        save_events(events_db)
        await interaction.response.edit_message(embed=discord.Embed(title="✅ Evento Creato!", description=f"**{self.parent_view_ref.day} Ottobre ore {hour_fmt}**\n{GAMES[self.parent_view_ref.game_id]['emoji']} {GAMES[self.parent_view_ref.game_id]['name']} | 👥{self.parent_view_ref.players} | Leve:{self.parent_view_ref.leve}", color=0x00ff00), view=None)

class CreaEventoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.game_id = None
        self.day = None
        self.players = None
        self.leve = None
        self.add_item(GameSelectPanel(self))
        self.add_item(DaySelectPanel(self))
        self.add_item(PlayersSelectPanel(self))
        self.add_item(LeveSelectPanel(self))

    async def update_embed(self, interaction):
        embed = get_main_embed(self)
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except:
            try:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
            except:
                await interaction.response.defer()

    @discord.ui.button(label="🕒 Ora 24h e CONFERMA", style=discord.ButtonStyle.success, row=4)
    async def conferma(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not all([self.game_id, self.day, self.players, self.leve]):
            missing = []
            if not self.game_id: missing.append("Gioco")
            if not self.day: missing.append("Giorno")
            if not self.players: missing.append("Player")
            if not self.leve: missing.append("Leve")
            embed = get_main_embed(self)
            embed.color = 0xff0000
            embed.add_field(name="❌ Manca", value=", ".join(missing), inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
            return
        await interaction.response.send_modal(HourModal(self))

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
        super().__init__(placeholder=f"📅 2. Giorno (da {today} a 31)", options=options[:25], row=1)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.day = self.values[0]
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
        super().__init__(placeholder="👥 3. Player 1-4...", options=options, row=2)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.players = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class LeveSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        options = [
            discord.SelectOption(label="Leve SI", value="SI", emoji="✅"),
            discord.SelectOption(label="Leve NO", value="NO", emoji="❌"),
        ]
        super().__init__(placeholder="🔧 4. Leve SI/NO...", options=options, row=3)
    async def callback(self, interaction: discord.Interaction):
        self.parent_view_ref.leve = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", custom_id="crea_evento_v26")
    async def crea_evento(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = CreaEventoView()
        embed = get_main_embed(view)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    @discord.ui.button(label="Aggiorna", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="aggiorna_cal_v26")
    async def aggiorna(self, interaction: discord.Interaction, button: discord.ui.Button):
        cal_text, event_list = build_calendar_text()
        embed = create_calendar_embed(cal_text, event_list)
        await interaction.response.edit_message(embed=embed, view=self)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Blackout404 v26 online come {bot.user}")
    bot.add_view(CalendarioView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash: {len(synced)}")
    except Exception as e:
        print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="📅 Calendario Blackout404 v26")
async def calendario_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    cal_text, event_list = build_calendar_text()
    embed = create_calendar_embed(cal_text, event_list)
    await interaction.followup.send(embed=embed, view=CalendarioView())

@bot.tree.command(name="ping", description="Check ONLINE")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🏴 Blackout404 v26 ONLINE!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
