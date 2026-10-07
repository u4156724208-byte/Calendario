import 【entity-discord¦canonical_name=discord】
from 【entity-discord¦canonical_name=discord】.ext import commands
import os
from flask import Flask
import threading

# FIX 1: Mini web server per Render Web Service
app = Flask(__name__)
@app.route('/')
def home(): return "OK - Calendario Bot Esempio 1 2 3"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_flask, daemon=True).start()

# FIX 2: Bot con sync corretto
intents = 【entity-discord¦canonical_name=discord】.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class CreaEventoModal(【entity-discord¦canonical_name=discord】.ui.Modal, title="Crea Evento"):
    max_partecipanti = discord.ui.TextInput(
        label="Max partecipanti (1-99) - Esempio 1 2 3",
        placeholder="0",
        default="0",
        required=True,
        max_length=2
    )
    nome_evento = discord.ui.TextInput(label="Nome evento", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"📅 **{self.nome_evento.value}** - Max: {self.max_partecipanti.value}",
            ephemeral=True
        )

class CreaView(discord.ui.View):
    @discord.ui.button(label="Crea Evento", style=discord.ButtonStyle.blurple)
    async def crea(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreaEventoModal())

@bot.command()
async def calendario(ctx):
    await ctx.send("Crea:", view=CreaView())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Online come {bot.user} - Sync OK")

bot.run(os.getenv("DISCORD_TOKEN"))
