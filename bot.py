import os, discord, calendar
from discord.ext import commands
from flask import Flask
import threading
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "OK"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_calendario_text(year=2026, month=10):
    cal = calendar.Calendar(firstweekday=0)  # Lun = 0
    weeks = cal.monthdayscalendar(year, month)
    header = "LUN  MAR  MER  GIO  VEN  SAB  DOM"
    lines = [header]
    for week in weeks:
        line = ""
        for day in week:
            if day == 0:
                line += "     "
            else:
                line += f"{day:02d}   " if day < 10 else f"{day:02d}   "
                # Fix width: 5 chars per day
                # Better: format with 4 spaces
        # Clean version with fixed width
        row = ""
        for day in week:
            if day == 0:
                row += "     "
            else:
                row += f"{day:02d}   "
        lines.append(row.rstrip())
    return "\n".join(lines)

def get_calendario_embed():
    # versione perfettamente allineata
    text = """LUN  MAR  MER  GIO  VEN  SAB  DOM
               01   02   03   04
05   06   07   08   09   10   11
12   13   14   15   16   17   18
19   20   21   22   23   24   25
26   27   28   29   30   31"""
    # Usa code block con allineamento fisso
    return f"```\n{text}\n```"

class CreaEventoCompletoModal(discord.ui.Modal, title="Crea Evento - scegli data completa"):
    def __init__(self):
        super().__init__()
        now = datetime.now()
        ds = now.strftime("%d/%m/%Y")
        hs = now.strftime("%H:%M")
        self.data_in = discord.ui.TextInput(label=f"Data (GG/MM/AAAA) - Oggi {ds}", default=ds, required=True)
        self.ora_in = discord.ui.TextInput(label=f"Ora (HH:MM) - Ora {hs}", default=hs, required=True)
        self.titolo_in = discord.ui.TextInput(label="Titolo evento", placeholder="Es: Game Film JustChatting", required=True)
        self.max_in = discord.ui.TextInput(label="Max partecipanti (1-99) - Esempio 1 2 3", placeholder="Esempio: 1, 2, 3... lascia 0", default="0", max_length=2, required=True)
        self.add_item(self.data_in)
        self.add_item(self.ora_in)
        self.add_item(self.titolo_in)
        self.add_item(self.max_in)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Creato: **{self.titolo_in.value}** {self.data_in.value} {self.ora_in.value} Max:{self.max_in.value}", ephemeral=True)

class CreaView(discord.ui.View):
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="\U0001f4c5")
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoCompletoModal())

@bot.tree.command(name="calendario", description="Mostra calendario")
async def calendario_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="Ottobre 2026", description=get_calendario_embed(), color=0x2b2d31)
    await interaction.response.send_message(embed=embed, view=CreaView())

@bot.command(name="calendario")
async def calendario_prefix(ctx):
    embed = discord.Embed(title="Ottobre 2026", description=get_calendario_embed(), color=0x2b2d31)
    await ctx.send(embed=embed, view=CreaView())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online {bot.user} - Calendario allineato OK")

def run_flask(): app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
