import os, discord, uuid, traceback
from discord.ext import commands, tasks
from flask import Flask
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
@app.route('/')
def home(): return "OK - Forum mode"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
events = {}

def calendario_text():
    return "LUN  MAR  MER  GIO  VEN  SAB  DOM\n               01   02   03   04\n05   06   07   08   09   10   11\n12   13   14   15   16   17   18\n19   20   21   22   23   24   25\n26   27   28   29   30   31"

def parse_event_datetime(ev):
    try:
        return datetime.strptime(f"{ev['data']} {ev['ora']}", "%d/%m/%Y %H:%M")
    except:
        try:
            if ev['ora'].isdigit():
                return datetime.strptime(f"{ev['data']} {ev['ora']}:00", "%d/%m/%Y %H:%M")
            return datetime.strptime(ev['data'], "%d/%m/%Y")
        except:
            return None

def get_forum_channel(interaction):
    ch = interaction.channel
    if isinstance(ch, discord.ForumChannel):
        return ch
    if isinstance(ch, discord.Thread) and isinstance(ch.parent, discord.ForumChannel):
        return ch.parent
    return None

def find_tags_for_title(forum, titolo):
    if not forum or not forum.available_tags:
        return []
    titolo_low = titolo.lower()
    matched = []
    for tag in forum.available_tags:
        name_low = tag.name.lower()
        # match se nome tag dentro titolo o viceversa
        if name_low in titolo_low or titolo_low in name_low:
            matched.append(tag)
    # se trova Game, Cinema, JustChatting ecc
    # limita a max 5 tags (limite Discord)
    return matched[:5]

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
        ev_dt = parse_event_datetime(ev)
        if ev_dt:
            canc = ev_dt + timedelta(hours=24)
            desc += f"\n\n\U0001f5d1\ufe0f Auto-cancellazione: {canc.strftime('%d/%m %H:%M')} (24h dopo data evento)"
        return discord.Embed(title=f"Evento del {ev['data']} ore {ev['ora']}", description=desc, color=0x2ECC71)
    @discord.ui.button(label="Partecipa", style=discord.ButtonStyle.green, emoji="\u2705", custom_id="partecipa_btn_persist")
    async def partecipa(self, interaction: discord.Interaction, button: discord.ui.Button):
        ev = events.get(self.event_id)
        if not ev:
            await interaction.response.send_message("Evento gia pulito", ephemeral=True)
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

class CreaEventoModal(discord.ui.Modal):
    def __init__(self, forum_channel=None):
        super().__init__(title="Crea Evento - con tag @")
        now = datetime.now()
        self.forum_channel = forum_channel
        self.data_in = discord.ui.TextInput(
            label=f"Data (GG/MM/AAAA) - Oggi {now.strftime('%d/%m/%Y')}",
            placeholder="07/10/2026",
            default=now.strftime("%d/%m/%Y"),
            max_length=10
        )
        self.ora_in = discord.ui.TextInput(
            label=f"Ora (HH:MM) - Ora {now.strftime('%H:%M')}",
            placeholder="Es: 18:00 o 22",
            default=now.strftime("%H:%M"),
            max_length=5
        )
        self.titolo_in = discord.ui.TextInput(
            label="Titolo evento - usa @ per taggare",
            placeholder="Es: Game Cinema JustChatting",
            style=discord.TextStyle.short,
            max_length=100,
            required=True
        )
        self.max_in = discord.ui.TextInput(
            label="Max partecipanti (1-99)",
            placeholder="Esempio 1 2 3",
            default="1",
            max_length=2,
            required=True
        )
        self.add_item(self.data_in)
        self.add_item(self.ora_in)
        self.add_item(self.titolo_in)
        self.add_item(self.max_in)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            now = datetime.now()
            data_val = self.data_in.value.strip() or now.strftime("%d/%m/%Y")
            ora_val = self.ora_in.value.strip() or now.strftime("%H:%M")
            if ora_val.isdigit():
                ora_val = f"{ora_val}:00"
            try:
                max_v = int(self.max_in.value) if self.max_in.value.isdigit() else 1
            except:
                max_v = 1
            if max_v < 1: max_v = 1
            if max_v > 99: max_v = 99

            titolo_raw = self.titolo_in.value.strip()
            if not titolo_raw:
                await interaction.response.send_message("Titolo obbligatorio!", ephemeral=True)
                return

            eid = str(uuid.uuid4())[:8]
            events[eid] = {'data': data_val, 'ora': ora_val, 'titolo': titolo_raw, 'max': max_v, 'partecipanti': [], 'creatore': interaction.user.display_name, 'created_at': now, 'channel_id': None, 'message_id': None, 'thread_id': None}
            view = PartecipaView(eid)
            embed = view.make_embed()
            content_con_tag = titolo_raw if '@' in titolo_raw else None

            forum = self.forum_channel or get_forum_channel(interaction)

            if forum and isinstance(forum, discord.ForumChannel):
                # FORUM MODE: crea post forum
                tags = find_tags_for_title(forum, titolo_raw)
                thread_name = f"{titolo_raw} - {data_val} {ora_val}"[:100]
                try:
                    thread_with_msg = await forum.create_thread(
                        name=thread_name,
                        content=content_con_tag,
                        embed=embed,
                        view=view,
                        applied_tags=tags,
                        allowed_mentions=discord.AllowedMentions(everyone=True, users=True, roles=True)
                    )
                    # thread_with_msg e' un Thread, oppure tuple (thread, message)
                    thread = thread_with_msg.thread if hasattr(thread_with_msg, 'thread') else thread_with_msg
                    if isinstance(thread_with_msg, tuple):
                        thread = thread_with_msg[0]
                    events[eid]['thread_id'] = thread.id
                    events[eid]['channel_id'] = thread.id
                    events[eid]['forum_id'] = forum.id
                    await interaction.response.send_message(f"Evento creato nel forum: {thread.mention}", ephemeral=True)
                except Exception as e:
                    print(f"Errore create_thread forum: {e}\n{traceback.format_exc()}")
                    # fallback a messaggio normale
                    await interaction.response.send_message(content=content_con_tag, embed=embed, view=view, allowed_mentions=discord.AllowedMentions(everyone=True, users=True, roles=True))
            else:
                # CANALE NORMALE
                await interaction.response.send_message(content=content_con_tag, embed=embed, view=view, allowed_mentions=discord.AllowedMentions(everyone=True, users=True, roles=True))
                try:
                    msg = await interaction.original_response()
                    events[eid]['message_id'] = msg.id
                    events[eid]['channel_id'] = msg.channel.id
                except:
                    pass

        except Exception as e:
            print(f"ERRORE ON_SUBMIT FORUM: {e}\n{traceback.format_exc()}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Errore: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"Errore: {e}", ephemeral=True)
            except:
                pass

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5", custom_id="crea_evento_cal_persist")
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        forum = get_forum_channel(interaction)
        await interaction.response.send_modal(CreaEventoModal(forum_channel=forum))

@tasks.loop(minutes=10)
async def pulizia_24h():
    now = datetime.now()
    to_delete = []
    for eid, ev in list(events.items()):
        ev_dt = parse_event_datetime(ev)
        if not ev_dt: continue
        scadenza = ev_dt + timedelta(hours=24)
        if now >= scadenza:
            to_delete.append(eid)
            try:
                # se e' thread forum, cancella thread
                thread_id = ev.get('thread_id') or ev.get('channel_id')
                if thread_id:
                    ch = bot.get_channel(thread_id)
                    if ch and isinstance(ch, discord.Thread):
                        await ch.delete()
                    else:
                        # prova fetch messaggio
                        if ev.get('channel_id') and ev.get('message_id'):
                            ch2 = bot.get_channel(ev['channel_id'])
                            if ch2:
                                try:
                                    msg = await ch2.fetch_message(ev['message_id'])
                                    await msg.delete()
                                except:
                                    pass
            except Exception as ex:
                print(f"Cancello {eid} fallito: {ex}")
    for eid in to_delete:
        events.pop(eid, None)
    if to_delete:
        print(f"[PULIZIA FORUM 24h] Eliminati {len(to_delete)} post")

@bot.tree.command(name="calendario", description="Mostra calendario (supporta canale forum)")
async def calendario_slash(interaction: discord.Interaction):
    forum = get_forum_channel(interaction)
    embed = discord.Embed(title="Ottobre 2026", description=f"```\n{calendario_text()}\n```", color=0x2b2d31)
    if forum and isinstance(forum, discord.ForumChannel):
        # Se siamo in forum, creiamo un post forum per il calendario
        try:
            await forum.create_thread(
                name="Calendario - Ottobre 2026",
                embed=embed,
                view=CalendarioView()
            )
            await interaction.response.send_message("Calendario creato nel forum!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=embed, view=CalendarioView(), ephemeral=True)
    else:
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
            try:
                thread_id = ev.get('thread_id') or ev.get('channel_id')
                if thread_id:
                    ch = bot.get_channel(thread_id)
                    if ch and isinstance(ch, discord.Thread):
                        await ch.delete()
            except: pass
            events.pop(eid, None)
            count += 1
    await interaction.response.send_message(f"Puliti {count} eventi", ephemeral=True)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    embed = discord.Embed(title="Ottobre 2026", description=f"```\n{calendario_text()}\n```", color=0x2b2d31)
    await ctx.send(embed=embed, view=CalendarioView())

@bot.event
async def on_ready():
    bot.add_view(CalendarioView())
    bot.add_view(PartecipaView())
    await bot.tree.sync()
    print(f"SYNC OK - {bot.user} - Forum mode 24h")
    if not pulizia_24h.is_running():
        pulizia_24h.start()

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
