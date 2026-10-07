import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# MODAL con la modifica che hai chiesto
class CreaEventoModal(discord.ui.Modal, title="Crea Evento Calendario"):
    # Qui la modifica: prima era "Max partecipanti (1-99) - Default 10 *"
    # Ora è "Max partecipanti (1-99) - Esempio 1 2 3 *"
    max_partecipanti = discord.ui.TextInput(
        label="Max partecipanti (1-99) - Esempio 1 2 3",
        placeholder="Esempio: 1, 2, 3...",
        default="0",  # prima era 10, ora 0 come da tua richiesta
        min_length=1,
        max_length=2,
        required=True
    )

    nome_evento = discord.ui.TextInput(
        label="Nome evento",
        placeholder="Es: Torneo Ghost",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            num = int(self.max_partecipanti.value)
            if not 0 <= num <= 99:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Inserisci un numero tra 0 e 99 per i partecipanti.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📅 {self.nome_evento.value}",
            description=f"Max partecipanti: **{num}**\nCreatore: {interaction.user.mention}",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

@bot.command()
async def calendario(ctx):
    await ctx.send("Clicca per creare:", view=CreaEventoView())

class CreaEventoView(discord.ui.View):
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.blurple)
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoModal())

@bot.event
async def on_ready():
    print(f"Bot online come {bot.user} - Config: Esempio 1 2 3 / default 0")

# Render usa DISCORD_TOKEN come env var
bot.run(os.getenv("DISCORD_TOKEN")) 
