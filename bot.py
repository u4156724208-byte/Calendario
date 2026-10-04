import discord
from discord.ext import commands
import calendar
from datetime import datetime

class CalendarioGiochi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # I tuoi eventi salvati (esempio)
        self.eventi = {
            5: {"ora": "02:00", "gioco": "WarDogs", "partecipanti": "1/3", "live": "SI"},
            6: {"ora": "02:00", "gioco": "WarDogs", "partecipanti": "1/3", "live": "NO"},
        }

    @discord.app_commands.command(name="calendario", description="Mostra il calendario giochi")
    async def calendario(self, interaction: discord.Interaction):
        now = datetime.now()
        year = 2026
        month = 10
        
        # Costruisce la griglia
        cal_str = "```
"
        cal_str += "LUN  MAR  MER  GIO  VEN  SAB  DOM
"
        # Logica per allineare i giorni (ottobre 2026 inizia di gio)
        cal_str += "               01   02   03   04
"
        cal_str += "[05] [06]  07   08   09   10   11
"
        cal_str += " 12   13   14   15   16   17   18
"
        cal_str += " 19   20   21   22   23   24   25
"
        cal_str += " 26   27   28   29   30   31
"
        cal_str += "```"

        embed = discord.Embed(
            title="CALENDARIO GIOCHI",
            description=f"Ottobre {year}
{cal_str}",
            color=0x2F3136
        )
        
        # --- PARTE RIMOSSA ---
        # Prima qui c'era questo loop che creava le righe che vuoi togliere:
        # lista_eventi = ""
        # for giorno, dati in self.eventi.items():
        #     lista_eventi += f"Giorno {giorno:02d} ore {dati['ora']} | {dati['gioco']} | {dati['partecipanti']} | Live:{dati['live']}\n"
        # embed.add_field(name="\u200b", value=lista_eventi, inline=False)
        # ----------------------

        view = CreaEventoView()
        await interaction.response.send_message(embed=embed, view=view)

class CreaEventoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.green, emoji="📅")
    async def crea_evento(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoModal())

class CreaEventoModal(discord.ui.Modal, title="Crea Nuovo Evento"):
    giorno = discord.ui.TextInput(label="Giorno", placeholder="05")
    ora = discord.ui.TextInput(label="Ora", placeholder="21:00")
    gioco = discord.ui.TextInput(label="Gioco", placeholder="WarDogs")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Evento creato per giorno {self.giorno}!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CalendarioGiochi(bot))
