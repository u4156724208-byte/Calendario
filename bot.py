import os, discord, uuid, traceback
from discord.ext import commands, tasks
from flask import Flask
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
@app.route('/')
def home(): return "OK - Pulizia 24h dopo data evento"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
events = {}

def calendario_text():
    return "LUN  MAR  MER  GIO  VEN  SAB  DOM\n               01   02   03   04\n05   06   07   08   09   10   11\n12   13   14   15   16   17   18\n19   20   21   22   23   24   25\n26   27   28   29   30   31"

def parse_event_datetime(ev):
    try:
        return datetime.strptime(f"{ev['data']} {ev['ora']}", "%d/%m/%Y %H:%M")
    except:
        try:
            return datetime.strptime(ev['data'], "%d/%m/%Y")
        except:
            return None

class PartecipaView(discord.ui.View):
    def __init__(self, event_id="temp"):
        super().__init__(timeout=None)
        self.event_id = event_id
    def make_embed(self):
        ev = events.get(self.event_id)
        if not ev: return discord.Embed(title="Evento eliminato", description="Pulito dopo 24h", color=0xED4245)
        desc = f"**Titolo**\n{ev['titolo']}\n\n**Partecipanti**\n{len(ev['partecipanti'])}/{ev['max']} persone\n"
        for p in ev['partecipanti']:
            desc += f"• {p}\n"
        desc += f"\nCreato da {ev['creatore']}"
        # mostra quando verra cancellato
        ev_dt = parse_event_datetime(ev)
        if ev_dt:
            canc = ev_dt + timedelta(hours=24)
            desc += f"\n\n🗑️ Auto-cancellazione: {canc.strftime('%d/%m %H:%M')} (24h dopo data evento)"
        return discord.Embed(title=f"Evento del {ev['data']} ore {ev['ora']}", description=desc, color=0x2ECC71)
    @discord.ui.button(label="Partecipa", style=discord.ButtonStyle.green, emoji="✅", custom_id="partecipa_btn_persist")
    async def partecipa(self, interaction: discord.Interaction, button: discord.ui.Button):
        ev = events.get(self.event_id)
        if not ev:
            await interaction.response.send_message("Evento gia pulito dopo 24h", ephemeral=True)
            return
        ev_dt = parse_event_datetime(ev)
        if ev_dt and datetime.now() > ev_dt + timedelta(hours=24):
            await interaction.response.send_message("Evento gia scaduto da 24h e pulito!", ephemeral=True)
            return
        nome = interaction.user.display_name
        if nome not in ev['partecipanti'] and len(ev['partecipanti']) < ev['max']:
            ev['partecipanti'].append(nome)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)
    @discord.ui.button(label="Esci", style=discord.ButtonStyle.red, custom_id="esci_btn_persist")
    async def esci(self, interaction: discord.Interaction, button: discord.ui.Button):
        ev = events.get(self.event_id)
        if ev and interaction.user.display_name in ev['partecipanti']:
            ev['partecipanti'].remove(interaction.user.display_name)
            await interaction.response.edit_message(embed=self.make_embed(), view=self)
        else:
            await interaction.response.defer()

class CreaEventoModal(discord.ui.Modal, title="Crea Evento - con tag @"):
    data_in = discord.ui.TextInput(label="Data (GG/MM/AAAA)", placeholder="07/10/2026", default="07/10/2026")
    ora_in = discord.ui.TextInput(label="Ora (HH:MM)", placeholder="18:00", default="18:00")
    titolo_in = discord.ui.TextInput(label="Titolo evento - usa @ per taggare", placeholder="Es: Game Cinema JustChatting", style=discord.TextStyle.paragraph)
    max_in = discord.ui.TextInput(label="Max partecipanti (1-99)", placeholder="Esempio 1 2 3", default="1", max_length=2)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            now = datetime.now()
            data_val = self.data_in.value or now.strftime("%d/%m/%Y")
            ora_val = self.ora_in.value or now.strftime("%H:%M")
            max_v = int(self.max_in.value) if self.max_in.value.isdigit() else 1
            if max_v < 1: max_v = 1
            if max_v > 99: max_v = 99
            max_display = max_v
            eid = str(uuid.uuid4())[:8]
            titolo_raw = self.titolo_in.value
            events[eid] = {'data': data_val, 'ora': ora_val, 'titolo': titolo_raw, 'max': max_display, 'partecipanti': [], 'creatore': interaction.user.display_name, 'created_at': now, 'channel_id': None, 'message_id': None}
            view = PartecipaView(eid)
            # Se nel titolo c'e' @, mettilo nel contenuto per far pingare
            content_con_tag = None
            if '@' in titolo_raw:
                content_con_tag = titolo_raw  # Discord pinga se @everyone/@here/@ruolo/@utente nel content
            await interaction.response.send_message(content=content_con_tag, embed=view.make_embed(), view=view, allowed_mentions=discord.AllowedMentions(everyone=True, users=True, roles=True))
            try:
                msg = await interaction.original_response()
                events[eid]['message_id'] = msg.id
                events[eid]['channel_id'] = msg.channel.id
            except: pass
        except Exception as e:
            print(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅", custom_id="crea_evento_cal_persist")
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CreaEventoModal()
        now = datetime.now()
        modal.data_in.default = now.strftime("%d/%m/%Y")
        modal.ora_in.default = now.strftime("%H:%M")
        modal.data_in.label = f"Data (GG/MM/AAAA) - Oggi {modal.data_in.default}"
        modal.ora_in.label = f"Ora (HH:MM) - Ora {modal.ora_in.default}"
        await interaction.response.send_modal(modal)

# PULIZIA: data evento + 24 ore
@tasks.loop(minutes=10)
async def pulizia_24h():
    now = datetime.now()
    to_delete = []
    for eid, ev in list(events.items()):
        ev_dt = parse_event_datetime(ev)
        if not ev_dt:
            continue
        # Cancella 24h dopo la data odierna dell'evento (data+ora + 24h)
        scadenza = ev_dt + timedelta(hours=24)
        if now >= scadenza:
            to_delete.append(eid)
            if ev.get('channel_id') and ev.get('message_id'):
                try:
                    ch = bot.get_channel(ev['channel_id'])
                    if ch:
                        msg = await ch.fetch_message(ev['message_id'])
                        await msg.delete()
                except Exception as ex:
                    print(f"Cancello {eid} fallito: {ex}")
    
    for eid in to_delete:
        events.pop(eid, None)
    if to_delete:
        print(f"[PULIZIA 24h] Eliminati {len(to_delete)} eventi - 24h dopo data evento")

@bot.tree.command(name="calendario", description="Mostra calendario")
async def calendario_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="Ottobre 2026", description=f"```\n{calendario_text()}\n```", color=0x2b2d31)
    await interaction.response.send_message(embed=embed, view=CalendarioView())

@bot.tree.command(name="pulisci_eventi", description="[Admin] Pulisci eventi vecchi di 24h")
async def pulisci_eventi_slash(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Serve Gestisci Messaggi", ephemeral=True)
        return
    now = datetime.now()
    count = 0
    for eid, ev in list(events.items()):
        ev_dt = parse_event_datetime(ev)
        if ev_dt and now >= ev_dt + timedelta(hours=24):
            if ev.get('channel_id') and ev.get('message_id'):
                try:
                    ch = bot.get_channel(ev['channel_id'])
                    if ch:
                        m = await ch.fetch_message(ev['message_id'])
                        await m.delete()
                except: pass
            events.pop(eid, None)
            count += 1
    await interaction.response.send_message(f"Puliti {count} eventi con piu di 24h", ephemeral=True)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    embed = discord.Embed(title="Ottobre 2026", description=f"```\n{calendario_text()}\n```", color=0x2b2d31)
    await ctx.send(embed=embed, view=CalendarioView())

@bot.event
async def on_ready():
    bot.add_view(CalendarioView())
    bot.add_view(PartecipaView())
    await bot.tree.sync()
    print(f"SYNC OK - {bot.user} - Pulizia 24h dopo data evento")
    if not pulizia_24h.is_running():
        pulizia_24h.start()

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
