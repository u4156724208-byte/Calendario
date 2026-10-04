import discord
import os
import json
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home():
    return "Blackout404 is ONLINE!"

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
    with open(EVENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

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
    for date, ev_list in sorted(events_db.items()):
        if date.startswith(f"{year}-{month:02d}"):
            d = date.split("-")[2]
            for ev in ev_list:
                game_emoji = GAMES.get(ev['game'], {}).get('emoji','🎮')
                event_list += f"**{d}** {game_emoji} {ev['game_name']} - {ev['title']} ore {ev['hour']} ({ev['author']})\n"
    return cal_text, event_list

def create_calendar_embed(cal_text, event_list):
    embed = discord.Embed(
        title="CALENDARIO GIOCHI - Blackout404",
        description=f"**Ottobre 2026**\n```\n{cal_text}\n```\n{event_list if event_list else '*Nessun evento - clicca Crea Evento*'}",
        color=0x2f3136
    )
    embed.set_footer(text="v20 SLASH • NUMERO VERDE = evento • /calendario")
    return embed

class EventModal(discord.ui.Modal):
    def __init__(self, game_id):
        super().__init__(title=f"Crea Evento - {GAMES[game_id]['name']}")
        self.game_id = game_id
        self.day = discord.ui.TextInput(label="Giorno (1-31)", placeholder="Es: 15", max_length=2, required=True)
        self.hour = discord.ui.TextInput(label="Ora (es: 21:00)", placeholder="Es: 21:00", max_length=5, required=True)
        self.title_input = discord.ui.TextInput(label="Titolo evento", placeholder="Es: Raid serale", max_length=50, required=True)
        self.add_item(self.day)
        self.add_item(self.hour)
        self.add_item(self.title_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            day = int(self.day.value)
            if not 1 <= day <= 31:
                raise ValueError
        except:
            await interaction.response.send_message("❌ Giorno non valido (1-31)", ephemeral=True)
            return
        date_key = f"2026-10-{day:02d}"
        if date_key not in events_db:
            events_db[date_key] = []
        events_db[date_key].append({
            "game": self.game_id,
            "game_name": GAMES[self.game_id]['name'],
            "title": self.title_input.value,
            "hour": self.hour.value,
            "author": str(interaction.user.display_name)
        })
        save_events(events_db)
        await interaction.response.send_message(f"✅ Evento creato per il **{day} Ottobre** - {GAMES[self.game_id]['emoji']} {GAMES[self.game_id]['name']} - {self.title_input.value} alle {self.hour.value}", ephemeral=True)

class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=GAMES["arc_raiders"]["name"], value="arc_raiders", emoji="⚔️", description="ARC Raiders"),
            discord.SelectOption(label="Farming Simulator 25", value="fs25", emoji="🚜", description="Farming Simulator 2"),
            discord.SelectOption(label=GAMES["wardogs"]["name"], value="wardogs", emoji="🐺", description="WarDogs"),
        ]
        super().__init__(placeholder="Scegli il gioco...", options=options, custom_id="game_select")
    async def callback(self, interaction: discord.Interaction):
        game_id = self.values[0]
        await interaction.response.send_modal(EventModal(game_id))

class GameSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(GameSelect())

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", custom_id="crea_evento_v20")
    async def crea_evento(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎮 Scegli il gioco per l'evento:", view=GameSelectView(), ephemeral=True)
    @discord.ui.button(label="Aggiorna", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="aggiorna_cal_v20")
    async def aggiorna(self, interaction: discord.Interaction, button: discord.ui.Button):
        cal_text, event_list = build_calendar_text()
        embed = create_calendar_embed(cal_text, event_list)
        await interaction.response.edit_message(embed=embed, view=self)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Blackout404 online come {bot.user}")
    bot.add_view(CalendarioView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"Errore sync slash: {e}")

@bot.tree.command(name="calendario", description="📅 Mostra il calendario giochi Blackout404")
async def calendario_slash(interaction: discord.Interaction):
    cal_text, event_list = build_calendar_text()
    embed = create_calendar_embed(cal_text, event_list)
    await interaction.response.send_message(embed=embed, view=CalendarioView())

@bot.tree.command(name="ping", description="🏴 Check se Blackout404 è ONLINE")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🏴 Blackout404 è ONLINE!")

@bot.tree.command(name="blackout", description="💀 BLACKOUT 404")
async def blackout_slash(interaction: discord.Interaction):
    await interaction.response.send_message("💀 BLACKOUT 404 - Sistema operativo!")

@bot.command()
async def ping(ctx):
    await ctx.send("🏴 Blackout404 è ONLINE!")

@bot.command()
async def blackout(ctx):
    await ctx.send("💀 BLACKOUT 404 - Sistema operativo!")

@bot.command(name="calendario")
async def calendario_cmd(ctx):
    cal_text, event_list = build_calendar_text()
    embed = create_calendar_embed(cal_text, event_list)
    await ctx.send(embed=embed, view=CalendarioView())

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
