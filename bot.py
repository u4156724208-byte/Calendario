import os
import calendar
import discord
from discord.ext import commands
from flask import Flask
import threading

# --- Web server per Render (per non andare in pausa) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Blackout404Bot online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Bot Discord ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# DATABASE EVENTI - qui metti i tuoi eventi
# Formato: giorno: {ora, vs, slot, live}
eventi_db = {
    5: {"ora": "02:00", "vs": "WarDogs", "slot": "1/3", "live": "SI"},
    6: {"ora": "02:00", "vs": "WarDogs", "slot": "1/3", "live": "NO"},
}

def genera_embed_calendario():
    anno, mese = 2026, 10
    cal = calendar.Calendar(firstweekday=0) # Lunedì = 0
    settimane = cal.monthdayscalendar(anno, mese)

    header = "LUN  MAR  MER  GIO  VEN  SAB  DOM\n"
    corpo = ""
    for sett in settimane:
        riga = ""
        for g in sett:
            if g == 0:
                riga += "     "
            elif g in eventi_db:
                riga += f"[{g:02d}]  "  # giorno con evento evidenziato
            else:
                riga += f" {g:02d}   "
        corpo += riga.rstrip() + "\n"

    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"Ottobre {anno}\n```\n{header}{corpo}```",
        color=0x2b2d31
    )

    # Lista sotto come nella tua foto
    lista_eventi = ""
    for giorno in sorted(eventi_db.keys()):
        info = eventi_db[giorno]
        lista_eventi += f"Giorno {giorno:02d} ore {info['ora']} | {info['vs']} | {info['slot']} | Live:{info['live']}\n"
    
    if lista_eventi:
        embed.add_field(name="", value=lista_eventi, inline=False)
    
    return embed

class EventoModal(discord.ui.Modal, title="Crea Nuovo Evento"):
    giorno = discord.ui.TextInput(label="Giorno (es. 12)", placeholder="12", max_length=2)
    ora = discord.ui.TextInput(label="Ora (es. 21:00)", placeholder="02:00")
    avversario = discord.ui.TextInput(label="Avversario", placeholder="WarDogs")
    slot = discord.ui.TextInput(label="Slot", placeholder="1/3", required=False, default="1/3")
    live = discord.ui.TextInput(label="Live? SI/NO", placeholder="SI", required=False, default="NO")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            g = int(self.giorno.value)
            eventi_db[g] = {
                "ora": self.ora.value, 
                "vs": self.avversario.value, 
                "slot": self.slot.value or "1/3", 
                "live": self.live.value or "NO"
            }
            await interaction.response.send_message(f"✅ Evento del giorno {g} aggiunto!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Giorno non valido", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Loggato come {bot.user}")
    try:
        await bot.tree.sync()
        print("Comandi sincronizzati - /calendario pronto")
    except Exception as e:
        print(e)

@bot.tree.command(name="calendario", description="Mostra il calendario giochi")
async def calendario(interaction: discord.Interaction):
    # FIX ANTI "L'applicazione non ha risposto" - risposta in <0.5s
    embed = genera_embed_calendario()
    
    view = discord.ui.View(timeout=None)
    btn_crea = discord.ui.Button(label="Crea Evento", style=discord.ButtonStyle.success, emoji="📅")
    
    async def crea_callback(inter: discord.Interaction):
        await inter.response.send_modal(EventoModal())
    
    btn_crea.callback = crea_callback
    view.add_item(btn_crea)

    await interaction.response.send_message(embed=embed, view=view)

if __name__ == "__main__":
    # Avvia web server in background
    threading.Thread(target=run_web, daemon=True).start()
    # Avvia bot
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("ERRORE: Manca DISCORD_TOKEN nelle Environment Variables di Render!")
    else:
        bot.run(TOKEN)
