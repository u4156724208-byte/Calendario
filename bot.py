
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
    return "Blackout404 v40 SENZA NUMERI 1 2 3 4 - ONLINE!"

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
    days_header = ["LUN","MAR","MER","GIO","VEN","SAB","DOM"]
    header = "".join([f"{d:^4}" for d in days_header])
    lines = [header]
    for week in cal:
        row_cells = []
        for day in week:
            if day == 0:
                row_cells.append("    ")
            else:
                key = f"{year}-{month:02d}-{day:02d}"
                if key in events_db and len(events_db[key])>0:
                    row_cells.append(f"\u001b[0;32m{day:^3}\u001b[0m ")
                else:
                    row_cells.append(f"{day:^4}")
        row = "".join(row_cells)
        lines.append(row)
    cal_text = "\n".join(lines)
    event_list = ""
    for date in sorted(events_db.keys()):
        if date.startswith(f"{year}-{month:02d}"):
            d = date.split("-")[2]
            for ev in sorted(events_db[date], key=lambda x: x.get('hour','00:00')):
                game_emoji = GAMES.get(ev.get('game'), {}).get('emoji','🎮')
                players_max = ev.get('players','?')
                hour = ev.get('hour','?')
                partecipanti = ev.get('partecipanti', [])
                count = len(partecipanti) if partecipanti else 1
                event_list += f"🟩 **{d}** {game_emoji} {ev.get('game_name','?')} | {hour} | {count}/{players_max}\n"
    return cal_text, event_list

def create_calendar_embed(cal_text, event_list):
    desc = f"**Ottobre 2026**\n```ansi\n{cal_text}\n```\n"
    desc += event_list if event_list else ""
    if len(desc) > 3500:
        desc = desc[:3500] + "\n..."
    embed = discord.Embed(title="CALENDARIO GIOCHI - Blackout404", description=desc, color=0x00FF7F)
    embed.set_footer(text="")
    return embed

def get_main_embed(view):
    today = datetime.datetime.now().day
    now_hour = datetime.datetime.now().hour
    game_txt = GAMES[view.game_id]['name'] if view.game_id else "❌"
    day_txt = view.day if view.day else "❌"
    hour_txt = view.hour if view.hour else "❌"
    players_txt = view.players if view.players else "❌"
    live_txt = view.leve if view.leve else "❌"
    if view.day and int(view.day) == today:
        hour_info = f"da {now_hour+1}:00 a 23:00"
    else:
        hour_info = "00:00-23:00"
    desc = f"Gioco: {game_txt}\nGiorno: {day_txt} (da {today} a 31)\nOra: {hour_txt} ({hour_info})\nPlayer: {players_txt}\nLive: {live_txt}"
    return discord.Embed(title="Crea Evento - 5 punti", description=desc, color=0x00FF7F)

class CreaEventoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.game_id = None
        self.day = None
        self.hour = None
        self.players = None
        self.leve = None
        self.refresh_items()

    def refresh_items(self):
        self.clear_items()
        self.add_item(GameSelectPanel(self))
        self.add_item(DaySelectPanel(self))
        self.add_item(HourSelectPanel(self))
        self.add_item(PlayersSelectPanel(self))
        self.add_item(LiveSelectPanel(self))
        self.add_item(ConfermaButton(self))

    async def update_embed(self, interaction):
        self.refresh_items()
        embed = get_main_embed(self)
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.errors.InteractionResponded:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
        except Exception as e:
            print(f"update error: {e}")

class PlayersSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        opts = []
        for i in range(1,5):
            is_def = parent_view.players == str(i)
            opts.append(discord.SelectOption(label=f"{i} Player", value=str(i), default=is_def))
        super().__init__(placeholder="4. Player 1-4...", options=opts, row=3)
    async def callback(self, interaction):
        self.parent_view_ref.players = self.values[0]
        await self.parent_view_ref.update_embed(interaction)
    @property
    def parent_view_ref(self):
        return self.view
    @parent_view_ref.setter
    def parent_view_ref(self, v):
        self._parent = v
        self.view = v

class ConfermaButton(discord.ui.Button):
    def __init__(self, parent_view):
        self.parent_view_ref = parent_view
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", row=4)
    async def callback(self, interaction: discord.Interaction):
        v = self.parent_view_ref
        if not all([v.game_id, v.day, v.hour, v.players, v.leve]):
            missing = []
            if not v.game_id: missing.append("Gioco")
            if not v.day: missing.append("Giorno")
            if not v.hour: missing.append("Ora")
            if not v.players: missing.append("Player")
            if not v.leve: missing.append("Live")
            embed = get_main_embed(v)
            embed.add_field(name="Manca", value=", ".join(missing))
            v.refresh_items()
            await interaction.response.edit_message(embed=embed, view=v)
            return
        date_key = f"2026-10-{int(v.day):02d}"
        if date_key not in events_db:
            events_db[date_key] = []
        events_db[date_key].append({
            "game": v.game_id,
            "game_name": GAMES[v.game_id]['name'],
            "players": v.players,
            "leve": v.leve,
            "hour": v.hour,
            "author": str(interaction.user.display_name),
            "partecipanti": [str(interaction.user.display_name)]
        })
        events_db[date_key] = sorted(events_db[date_key], key=lambda x: x["hour"])
        save_events(events_db)
        embed_ok = discord.Embed(title="✅ Evento Creato!", description=f"🟩 Giorno {v.day} ore {v.hour}\n{GAMES[v.game_id]['emoji']} {GAMES[v.game_id]['name']} | 1/{v.players} | Live:{v.leve}", color=0x00FF7F)
        await interaction.response.edit_message(embed=embed_ok, view=None)

class GameSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        opts = []
        for val, data in GAMES.items():
            is_def = parent_view.game_id == val
            opts.append(discord.SelectOption(label=data["name"], value=val, emoji=data["emoji"], default=is_def))
        super().__init__(placeholder="1. Gioco...", options=opts, row=0)
        self.parent_view_ref = parent_view
    async def callback(self, interaction):
        self.parent_view_ref.game_id = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class DaySelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        today = datetime.datetime.now().day
        opts = []
        for d in range(today, 32):
            is_def = parent_view.day == str(d)
            opts.append(discord.SelectOption(label=f"{d} Ottobre", value=str(d), default=is_def))
        super().__init__(placeholder=f"2. Giorno (da {today} a 31)", options=opts[:25], row=1)
        self.parent_view_ref = parent_view
    async def callback(self, interaction):
        self.parent_view_ref.day = self.values[0]
        self.parent_view_ref.hour = None
        await self.parent_view_ref.update_embed(interaction)

class HourSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        today = datetime.datetime.now().day
        now_hour = datetime.datetime.now().hour
        selected_day = int(parent_view.day) if parent_view.day else today
        opts = []
        if selected_day == today:
            start_h = now_hour + 1
            if start_h >= 24:
                opts.append(discord.SelectOption(label="Nessuna ora oggi", value="none"))
            else:
                for h in range(start_h, 24):
                    is_def = parent_view.hour == f"{h:02d}:00"
                    opts.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", default=is_def))
        else:
            for h in range(24):
                is_def = parent_view.hour == f"{h:02d}:00"
                opts.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", default=is_def))
        super().__init__(placeholder="3. Ora (dopo giorno)", options=opts[:25], row=2)
        self.parent_view_ref = parent_view
    async def callback(self, interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Nessuna ora oggi, scegli domani", ephemeral=True)
            return
        self.parent_view_ref.hour = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

class LiveSelectPanel(discord.ui.Select):
    def __init__(self, parent_view):
        opts = [
            discord.SelectOption(label="SI", value="SI", default=parent_view.leve=="SI"),
            discord.SelectOption(label="NO", value="NO", default=parent_view.leve=="NO"),
        ]
        super().__init__(placeholder="5. Live: SI/NO...", options=opts, row=3)
        self.parent_view_ref = parent_view
    async def callback(self, interaction):
        self.parent_view_ref.leve = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

# Fix PlayersSelectPanel parent ref for row 3
class PlayersSelectPanelNew(discord.ui.Select):
    def __init__(self, parent_view):
        opts = []
        for i in range(1,5):
            is_def = parent_view.players == str(i)
            opts.append(discord.SelectOption(label=f"{i} Player", value=str(i), default=is_def))
        super().__init__(placeholder="4. Player 1-4...", options=opts, row=3)
        self.parent_view_ref = parent_view
    async def callback(self, interaction):
        self.parent_view_ref.players = self.values[0]
        await self.parent_view_ref.update_embed(interaction)

# Override to use correct row mapping
# Row mapping finale: 0 Gioco, 1 Giorno, 2 Ora, 3 Player, 3 Live? No, servono 5 righe max
# Soluzione finale: 4 select + 1 bottone = 5 righe

# Re-define CreaEventoView finale corretto con 4 dropdown + 1 dropdown Live + bottone
class CreaEventoViewFinal(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.game_id = None
        self.day = None
        self.hour = None
        self.players = None
        self.leve = None
        self.refresh_items()

    def refresh_items(self):
        self.clear_items()
        self.add_item(GameSelectPanelFinal(self))
        self.add_item(DaySelectPanelFinal(self))
        self.add_item(HourSelectPanelFinal(self))
        self.add_item(PlayerSelectPanelFinal(self))
        self.add_item(LiveSelectPanelFinal(self))
        self.add_item(ConfermaButtonFinal(self))

    async def update_embed(self, interaction):
        self.refresh_items()
        embed = get_main_embed(self)
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.errors.InteractionResponded:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)

class GameSelectPanelFinal(discord.ui.Select):
    def __init__(self, pv):
        opts = [discord.SelectOption(label=d["name"], value=k, emoji=d["emoji"], default=pv.game_id==k) for k,d in GAMES.items()]
        super().__init__(placeholder="1. Gioco...", options=opts, row=0)
        self.pv=pv
    async def callback(self, i):
        self.pv.game_id=self.values[0]
        await self.pv.update_embed(i)

class DaySelectPanelFinal(discord.ui.Select):
    def __init__(self, pv):
        today = datetime.datetime.now().day
        opts = [discord.SelectOption(label=f"{d} Ottobre", value=str(d), default=pv.day==str(d)) for d in range(today, 32)]
        super().__init__(placeholder=f"2. Giorno (da {today} a 31)", options=opts[:25], row=1)
        self.pv=pv
    async def callback(self, i):
        self.pv.day=self.values[0]
        self.pv.hour=None
        await self.pv.update_embed(i)

class HourSelectPanelFinal(discord.ui.Select):
    def __init__(self, pv):
        today = datetime.datetime.now().day
        now_hour = datetime.datetime.now().hour
        sel_day = int(pv.day) if pv.day else today
        opts=[]
        if sel_day==today:
            sh=now_hour+1
            if sh>=24:
                opts.append(discord.SelectOption(label="Nessuna ora oggi", value="none"))
            else:
                for h in range(sh,24):
                    opts.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", default=pv.hour==f"{h:02d}:00"))
        else:
            for h in range(24):
                opts.append(discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", default=pv.hour==f"{h:02d}:00"))
        super().__init__(placeholder="3. Ora (dopo giorno)", options=opts[:25], row=2)
        self.pv=pv
    async def callback(self, i):
        if self.values[0]=="none":
            await i.response.send_message("Nessuna ora oggi, scegli domani", ephemeral=True)
            return
        self.pv.hour=self.values[0]
        await self.pv.update_embed(i)

class PlayerSelectPanelFinal(discord.ui.Select):
    def __init__(self, pv):
        opts=[discord.SelectOption(label=f"{n} Player", value=str(n), default=pv.players==str(n)) for n in range(1,5)]
        super().__init__(placeholder="4. Player 1-4...", options=opts, row=3)
        self.pv=pv
    async def callback(self, i):
        self.pv.players=self.values[0]
        await self.pv.update_embed(i)

class LiveSelectPanelFinal(discord.ui.Select):
    def __init__(self, pv):
        opts=[discord.SelectOption(label="SI", value="SI", default=pv.leve=="SI"), discord.SelectOption(label="NO", value="NO", default=pv.leve=="NO")]
        super().__init__(placeholder="5. Live: SI/NO...", options=opts, row=4)
        self.pv=pv
    async def callback(self, i):
        self.pv.leve=self.values[0]
        await self.pv.update_embed(i)

class ConfermaButtonFinal(discord.ui.Button):
    def __init__(self, pv):
        super().__init__(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", row=4)
        self.pv=pv
    async def callback(self, interaction):
        v=self.pv
        if not all([v.game_id, v.day, v.hour, v.players, v.leve]):
            miss=[]
            if not v.game_id: miss.append("Gioco")
            if not v.day: miss.append("Giorno")
            if not v.hour: miss.append("Ora")
            if not v.players: miss.append("Player")
            if not v.leve: miss.append("Live")
            embed=get_main_embed(v)
            embed.add_field(name="Manca", value=", ".join(miss))
            v.refresh_items()
            await interaction.response.edit_message(embed=embed, view=v)
            return
        key=f"2026-10-{int(v.day):02d}"
        if key not in events_db:
            events_db[key]=[]
        events_db[key].append({"game":v.game_id,"game_name":GAMES[v.game_id]['name'],"players":v.players,"leve":v.leve,"hour":v.hour,"author":str(interaction.user.display_name),"partecipanti":[str(interaction.user.display_name)]})
        events_db[key]=sorted(events_db[key], key=lambda x: x["hour"])
        save_events(events_db)
        embed_ok=discord.Embed(title="✅ Evento Creato!", description=f"🟩 Giorno {v.day} ore {v.hour}\n{GAMES[v.game_id]['emoji']} {GAMES[v.game_id]['name']} | 1/{v.players} | Live:{v.leve}", color=0x00FF7F)
        await interaction.response.edit_message(embed=embed_ok, view=None)

# Usa la versione finale valida
CreaEventoView = CreaEventoViewFinal

class JoinEventButton(discord.ui.Button):
    def __init__(self, date_key, event_idx, event):
        day = date_key.split("-")[2]
        hour = event.get('hour','?')
        partecipanti = event.get('partecipanti', [])
        count = len(partecipanti) if partecipanti else 1
        max_p = event.get('players','?')
        game_emoji = GAMES.get(event.get('game'), {}).get('emoji','🎮')
        label = f"{day} {hour} {game_emoji} {count}/{max_p}"
        super().__init__(label=label, style=discord.ButtonStyle.success)
        self.date_key = date_key
        self.event_idx = event_idx
    async def callback(self, interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass
        date_key=self.date_key
        if date_key not in events_db or self.event_idx>=len(events_db[date_key]):
            await interaction.followup.send("Evento non trovato", ephemeral=True)
            return
        ev=events_db[date_key][self.event_idx]
        part=ev.get('partecipanti',[])
        user=str(interaction.user.display_name)
        if user in part:
            await interaction.followup.send(f"Sei già dentro! {', '.join(part)}", ephemeral=True)
            return
        max_p=int(ev.get('players',4))
        if len(part)>=max_p:
            await interaction.followup.send(f"Pieno! {max_p}/{max_p}", ephemeral=True)
            return
        part.append(user)
        ev['partecipanti']=part
        save_events(events_db)
        ct,el=build_calendar_text()
        emb=create_calendar_embed(ct,el)
        view=CalendarioViewDynamic()
        try:
            await interaction.message.edit(embed=emb, view=view)
        except:
            pass
        await interaction.followup.send(f"Partecipato! {date_key.split('-')[2]} ore {ev.get('hour')} - {len(part)}/{max_p}", ephemeral=True)

class CalendarioViewDynamic(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        count=0
        for date_key in sorted(events_db.keys()):
            if not date_key.startswith("2026-10"):
                continue
            for idx, ev in enumerate(sorted(events_db[date_key], key=lambda x: x.get('hour','00:00'))):
                if count>=20:
                    break
                btn=JoinEventButton(date_key, idx, ev)
                btn.row=1+(count//4)
                if btn.row>4:
                    break
                self.add_item(btn)
                count+=1
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅", custom_id="crea_evento_v40")
    async def crea_evento(self, interaction, button):
        view=CreaEventoView()
        embed=get_main_embed(view)
        try:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            print(f"crea_evento error: {e}")
            try:
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            except:
                pass

intents=discord.Intents.default()
intents.message_content=True
bot=commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Blackout404 v40 online come {bot.user}")
    bot.add_view(CalendarioViewDynamic())
    try:
        synced=await bot.tree.sync()
        print(f"✅ Slash: {len(synced)}")
    except Exception as e:
        print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="Calendario Blackout404 v40")
async def calendario_slash(interaction):
    await interaction.response.defer()
    ct,el=build_calendar_text()
    emb=create_calendar_embed(ct,el)
    await interaction.followup.send(embed=emb, view=CalendarioViewDynamic())

@bot.tree.command(name="ping", description="Check ONLINE")
async def ping_slash(interaction):
    await interaction.response.send_message("Blackout404 v40 SENZA NUMERI ONLINE!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
