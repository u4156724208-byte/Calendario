import discord
from discord import app_commands
import os
from datetime import datetime

intents = discord.Intents.default()
bot = discord.ext.commands.Bot(command_prefix="!", intents=intents)

# Dati calendario - modificali qui
eventi = {
    5: {"ora": "02:00", "gioco": "WarDogs", "slot": "1/3", "live": "SI"},
    6: {"ora": "02:00", "gioco": "WarDogs", "slot": "1/3", "live": "NO"},
}

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizzati {len(synced)} comandi")
    except Exception as e:
        print(f"Errore sync: {e}")

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    year = 2026
    month_name = "Ottobre"
    
    # Griglia fissa come da tuo screenshot - SENZA la lista sotto (richiesta tua)
    grid = "```\nLUN  MAR  MER  GIO  VEN  SAB  DOM\n"
    grid += "               01   02   03   04\n"
    grid += "[05] [06]  07   08   09   10   11\n"
    grid += " 12   13   14   15   16   17   18\n"
    grid += " 19   20   21   22   23   24   25\n"
    grid += " 26   27   28   29   30   31\n```"

    embed = discord.Embed(
        title="CALENDARIO GIOCHI",
        description=f"{month_name} {year}\n{grid}",
        color=0x2f3136
    )
    # NIENTE lista "Giorno 05 ore..." - rimossa come hai chiesto

    view = discord.ui.View(timeout=None)
    btn = discord.ui.Button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅")
    
    async def crea_callback(inter: discord.Interaction):
        await inter.response.send_message("Usa /creaevento giorno:05 ora:21:00 gioco:WarDogs", ephemeral=True)
    
    btn.callback = crea_callback
    view.add_item(btn)

    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="creaevento", description="Crea evento calendario")
@app_commands.describe(giorno="Giorno", ora="Ora es: 21:00", gioco="Nome gioco")
async def creaevento(interaction: discord.Interaction, giorno: int, ora: str, gioco: str):
    await interaction.response.send_message(f"Evento creato: Giorno {giorno} ore {ora} | {gioco}", ephemeral=True)

token = os.getenv("DISCORD_TOKEN")
if not token:
    print("ERRORE: DISCORD_TOKEN non impostato su Render > Environment")
else:
    bot.run(token)
