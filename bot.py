import os, discord, uuid, traceback
from discord.ext import commands
from flask import Flask
import threading
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "OK - Bot online"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
events = {}

def calendario_text():
    return "LUN  MAR  MER  GIO  VEN  SAB  DOM\n               01   02   03   04\n05   06   07   08   09   10   11\n12   13   14   15   16   17   18\n19   20   21   22   23   24   25\n26   27   28   29   30   31"

class PartecipaView(discord.ui.View):
    def __init__(self, event_id="temp"):
        super().__init__(timeout=None)
        self.event_id = event_id
    def make_embed(self):
        ev = events.get(self.event_id)
        if not ev: return discord.Embed(title="Evento non trovato")
        desc = f"**Titolo**\n{ev['titolo']}\n\n**Partecipanti**\n{len(ev['partecipanti'])}/{ev['max']} persone\n"
        for p in ev['partecipanti']:
            desc += f"• {p}\n"
        desc += f"\nCreato da {ev['creatore']}"
        return discord.Embed(title=f"Evento del {ev['data']} ore {ev['ora']}", description=desc, color=0x2ECC71)
    @discord.ui.button(label="Partecipa", style=discord.ButtonStyle.green, emoji="✅", custom_id="partecipa_btn_persist")
    async def partecipa(self, interaction: discord.Interaction, button: discord.ui.Button):
        ev = events.get(self.event_id)
        if not ev:
            await interaction.response.send_message("Evento scaduto o bot riavviato, ricrealo", ephemeral=True)
            return
        nome = interaction.user.display_name
        if nome not in ev['partecipanti'] and (len(ev['partecipanti']) < ev['max'] or ev['max']==0):
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

class CreaEventoModal(discord.ui.Modal, title="Crea Evento - scegli data completa"):
    data_in = discord.ui.TextInput(label="Data (GG/MM/AAAA)", placeholder="07/10/2026", default="07/10/2026")
    ora_in = discord.ui.TextInput(label="Ora (HH:MM)", placeholder="18:00", default="18:00")
    titolo_in = discord.ui.TextInput(label="Titolo evento", placeholder="Es: Game Film JustChatting")
    max_in = discord.ui.TextInput(label="Max partecipanti (1-99) - Esempio 1 2 3", placeholder="Esempio: 1, 2, 3... lascia 0", default="0", max_length=2)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            now = datetime.now()
            data_val = self.data_in.value or now.strftime("%d/%m/%Y")
            ora_val = self.ora_in.value or now.strftime("%H:%M")
            max_v = int(self.max_in.value) if self.max_in.value.isdigit() else 0
            max_display = 99 if max_v == 0 else max_v
            eid = str(uuid.uuid4())[:8]
            events[eid] = {'data': data_val, 'ora': ora_val, 'titolo': self.titolo_in.value, 'max': max_display, 'partecipanti': [], 'creatore': interaction.user.display_name}
            view = PartecipaView(eid)
            await interaction.response.send_message(embed=view.make_embed(), view=view)
        except Exception as e:
            print(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Errore creazione: {e}", ephemeral=True)

class CalendarioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅", custom_id="crea_evento_cal_persist")
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            modal = CreaEventoModal()
            # aggiorna default con data/ora attuale
            now = datetime.now()
            modal.data_in.default = now.strftime("%d/%m/%Y")
            modal.ora_in.default = now.strftime("%H:%M")
            # ricrea labels con Oggi / Ora
            modal.data_in.label = f"Data (GG/MM/AAAA) - Oggi {modal.data_in.default}"
            modal.ora_in.label = f"Ora (HH:MM) - Ora {modal.ora_in.default}"
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Errore bottone: {e}", ephemeral=True)

@bot.tree.command(name="calendario", description="Mostra calendario")
async def calendario_slash(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="Ottobre 2026", description=f"```\n{calendario_text()}\n```", color=0x2b2d31)
        await interaction.response.send_message(embed=embed, view=CalendarioView())
    except Exception as e:
        print(traceback.format_exc())
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    embed = discord.Embed(title="Ottobre 2026", description=f"```\n{calendario_text()}\n```", color=0x2b2d31)
    await ctx.send(embed=embed, view=CalendarioView())

@bot.event
async def on_ready():
    bot.add_view(CalendarioView())
    bot.add_view(PartecipaView())
    try:
        await bot.tree.sync()
        print(f"SYNC OK - {bot.user} - Views persistenti registrate")
    except Exception as e:
        print(f"SYNC FAIL {e}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
