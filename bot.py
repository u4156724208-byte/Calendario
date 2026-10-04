import os
import calendar
import time
import threading
import discord
from discord.ext import commands
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return "Blackout404Bot online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

eventi_db = {
    5: {"ora": "02:00", "vs": "WarDogs", "slot": "1/3", "live": "SI"},
    6: {"ora": "02:00", "vs": "WarDogs", "slot": "1/3", "live": "NO"},
}

def genera_embed_calendario():
    anno, mese = 2026, 10
    cal = calendar.Calendar(firstweekday=0)
    settimane = cal.monthdayscalendar(anno, mese)
    header = "LUN  MAR  MER  GIO  VEN  SAB  DOM\n"
    corpo = ""
    for sett in settimane:
        riga = ""
        for g in sett:
            if g == 0:
                riga += "     "
            elif g in eventi_db:
                riga += f"[{g:02d}]  "
            else:
                riga += f" {g:02d}   "
        corpo += riga.rstrip() + "\n"
    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"Ottobre {anno}\n```\n{header}{corpo}```",
        color=0x2b2d31
    )
    lista = ""
    for giorno in sorted(eventi_db.keys()):
        info = eventi_db[giorno]
        lista += f"Giorno {giorno:02d} ore {info['ora']} | {info['vs']} | {info['slot']} | Live:{info['live']}\n"
    if lista:
        embed.add_field(name="", value=lista, inline=False)
    return embed

class EventoModal(discord.ui.Modal, title="Crea Evento"):
    giorno = discord.ui.TextInput(label="Giorno", placeholder="12", max_length=2)
    ora = discord.ui.TextInput(label="Ora", placeholder="02:00")
    avversario = discord.ui.TextInput(label="Avversario", placeholder="WarDogs")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            g = int(self.giorno.value)
            eventi_db[g] = {"ora": self.ora.value, "vs": self.avversario.value, "slot": "1/3", "live": "NO"}
            await interaction.response.send_message(f"Evento giorno {g} aggiunto!", ephemeral=True)
        except:
            await interaction.response.send_message("Giorno non valido", ephemeral=True)

@bot.event
async def on_ready():
    print(f"ONLINE come {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="calendario", description="Mostra calendario")
async def calendario(interaction: discord.Interaction):
    embed = genera_embed_calendario()
    view = discord.ui.View(timeout=None)
    btn = discord.ui.Button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="\U0001f4c5")
    async def cb(i: discord.Interaction):
        await i.response.send_modal(EventoModal())
    btn.callback = cb
    view.add_item(btn)
    await interaction.response.send_message(embed=embed, view=view)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    time.sleep(1)
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("ATTENZIONE: DISCORD_TOKEN non impostato su Render! Servizio web resta online per far passare il deploy.")
        while True:
            time.sleep(60)
    else:
        bot.run(TOKEN)
