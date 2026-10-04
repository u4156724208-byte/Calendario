
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
  return "CALENDARIO Blackout404 v49 SOLO TESTO BIANCO v49 - ARC DBD WARDOGS v49 ONLINE!"

def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)

def keep_alive():
  t = Thread(target=run_web)
  t.daemon = True
  t.start()

EVENTS_FILE = "events.json"
GAMES = {
  "arc_raiders": {"name": "ARC Raiders", "emoji": ""},
  "dbd": {"name": "Dead By Daylight", "emoji": ""},
  "wardogs": {"name": "Wardogs", "emoji": ""}
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
  event_list = ""
  for date in sorted(events_db.keys()):
    if date.startswith(f"{year}-{month:02d}"):
      d = date.split("-")[2]
      for ev in sorted(events_db[date], key=lambda x: x.get('hour','00:00')):
        players_max = ev.get('players','?')
        hour = ev.get('hour','?')
        partecipanti = ev.get('partecipanti', [])
        count = len(partecipanti) if partecipanti else 1
        event_list += f"Giorno {d} ore {hour} | {ev.get('game_name','?')} | {count}/{players_max} | Live:{ev.get('leve','?')}
"
  if not event_list:
    event_list = "Nessun evento. Clicca Crea Evento!"
  return "", event_list

def create_calendar_embed(cal_text, event_list):
  desc = event_list
  if len(desc) > 1900:
    desc = desc[:1900] + "\n..."
  return desc

def create_calendar_embed_old(cal_text, event_list):
  desc = event_list
  if len(desc) > 3500:
    desc = desc[:3500] + "\n..."
  embed = discord.Embed(title="CALENDARIO GIOCHI", description=desc, color=0x2B2D31)
  return embed



def get_main_text(view):
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
  return f"Crea Evento\nGioco: {game_txt}\nGiorno: {day_txt} (da {today} a 31)\nOra: {hour_txt} ({hour_info})\nPlayer: {players_txt}\nLive: {live_txt}"

def get_main_embed(view):
  return discord.Embed(title="Crea Evento", description=get_main_text(view), color=0x2B2D31)


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
    self.add_item(GameSelect(self))
    self.add_item(DaySelect(self))
    self.add_item(HourSelect(self))
    self.add_item(PlayerSelect(self))
    # Row 4: Live SI, Live NO, Crea Evento - 3 bottoni validi, niente numeri 1 2 3 4
    self.add_item(LiveSIButton(self))
    self.add_item(LiveNOButton(self))
    self.add_item(ConfermaButton(self))

  async def update_embed(self, interaction):
    self.refresh_items()
    text = get_main_text(self)
    try:
      await interaction.response.edit_message(content=text, embed=None, view=self)
    except discord.errors.InteractionResponded:
      await interaction.followup.edit_message(interaction.message.id, content=text, embed=None, view=self)
    except Exception as e:
      print(f"update error: {e}")

class GameSelect(discord.ui.Select):
  def __init__(self, pv):
    opts=[discord.SelectOption(label=d["name"], value=k, default=pv.game_id==k) for k,d in GAMES.items()]
    super().__init__(placeholder="1. Gioco", options=opts, row=0)
    self.pv=pv
  async def callback(self, i):
    self.pv.game_id=self.values[0]
    await self.pv.update_embed(i)

class DaySelect(discord.ui.Select):
  def __init__(self, pv):
    today=datetime.datetime.now().day
    opts=[discord.SelectOption(label=f"{d} Ottobre", value=str(d), default=pv.day==str(d)) for d in range(today, 32)]
    super().__init__(placeholder=f"2. Giorno", options=opts[:25], row=1)
    self.pv=pv
  async def callback(self, i):
    self.pv.day=self.values[0]
    self.pv.hour=None
    await self.pv.update_embed(i)

class HourSelect(discord.ui.Select):
  def __init__(self, pv):
    today=datetime.datetime.now().day
    now_hour=datetime.datetime.now().hour
    sel_day=int(pv.day) if pv.day else today
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
    super().__init__(placeholder="3. Ora", options=opts[:25], row=2)
    self.pv=pv
  async def callback(self, i):
    if self.values[0]=="none":
      await i.response.send_message("Nessuna ora oggi, scegli domani", ephemeral=True)
      return
    self.pv.hour=self.values[0]
    await self.pv.update_embed(i)

class PlayerSelect(discord.ui.Select):
  def __init__(self, pv):
    opts=[discord.SelectOption(label=f"{n} Player", value=str(n), default=pv.players==str(n)) for n in range(1,5)]
    super().__init__(placeholder="4. Player", options=opts, row=3)
    self.pv=pv
  async def callback(self, i):
    self.pv.players=self.values[0]
    await self.pv.update_embed(i)

class LiveSIButton(discord.ui.Button):
  def __init__(self, pv):
    style=discord.ButtonStyle.success if pv.leve=="SI" else discord.ButtonStyle.secondary
    super().__init__(label="Live: SI", style=style, row=4)
    self.pv=pv
  async def callback(self, i):
    self.pv.leve="SI"
    await self.pv.update_embed(i)

class LiveNOButton(discord.ui.Button):
  def __init__(self, pv):
    style=discord.ButtonStyle.success if pv.leve=="NO" else discord.ButtonStyle.secondary
    super().__init__(label="Live: NO", style=style, row=4)
    self.pv=pv
  async def callback(self, i):
    self.pv.leve="NO"
    await self.pv.update_embed(i)

class ConfermaButton(discord.ui.Button):
  def __init__(self, pv):
    super().__init__(label="Crea Evento", style=discord.ButtonStyle.success, row=4)
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
    text_ok = f"✅ Evento Creato!\nGiorno {v.day} ore {v.hour}\n{GAMES[v.game_id]['name']} | 1/{v.players} | Live:{v.leve}"
    await interaction.response.edit_message(content=text_ok, embed=None, view=None)

class JoinEventButton(discord.ui.Button):
  def __init__(self, date_key, event_idx, event):
    day = date_key.split("-")[2]
    hour = event.get('hour','?')
    partecipanti = event.get('partecipanti', [])
    count = len(partecipanti) if partecipanti else 1
    max_p = event.get('players','?')
    game_emoji = GAMES.get(event.get('game'), {}).get('emoji','🎮')
    label = f"{day} {hour} {count}/{max_p}"
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
    txt=create_calendar_embed(ct,el)
    view=CalendarioViewDynamic()
    try:
      await interaction.message.edit(content=txt, embed=None, view=view)
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
  @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.success, custom_id="crea_evento_v49")
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
  print(f"✅ CALENDARIO v41 online come {bot.user}")
  bot.add_view(CalendarioViewDynamic())
  try:
    synced=await bot.tree.sync()
    print(f"✅ Slash: {len(synced)}")
  except Exception as e:
    print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="Calendario giochi")
async def calendario_slash(interaction):
  await interaction.response.defer()
  ct,el=build_calendar_text()
  txt=create_calendar_embed(ct,el)
  await interaction.followup.send(content=txt, view=CalendarioViewDynamic())

@bot.tree.command(name="ping", description="Check ONLINE")
async def ping_slash(interaction):
  await interaction.response.send_message("Blackout404 v49 CALENDARIO GIOCHI ONLINE!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
