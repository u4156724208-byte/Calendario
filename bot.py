
import os
import sys
import threading
import time
from flask import Flask
import discord
from discord.ext import commands

print("[SYSTEM] Avvio script bot.py...", flush=True)

# --- FLASK per Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Calendario Live - 200 OK"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"[WEB] Avvio Flask su porta {port}", flush=True)
    app.run(host="0.0.0.0", port=port)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --- DISCORD BOT ---
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("[ERRORE CRITICO] DISCORD_TOKEN mancante in Environment! Il bot non puo' partire.", flush=True)
    print("[ERRORE CRITICO] Vai su Render > Environment > Add DISCORD_TOKEN", flush=True)
    # Tieni vivo Flask per non far crashare Render
    while True:
        time.sleep(60)
else:
    TOKEN = TOKEN.strip()
    print(f"[SYSTEM] TOKEN trovato, lunghezza {len(TOKEN)}, primi 10 char: {TOKEN[:10]}...", flush=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CANALE_FISSO_ID = 1557509286911807629  # il tuo forum "a"
CATEGORIA_EVENTI_ID = None  # opzionale

@bot.event
async def on_ready():
    print(f"[BOT] Online {bot.user} | ID {bot.user.id}", flush=True)
    try:
        synced = await bot.tree.sync()
        print(f"[BOT] Sync {len(synced)} comandi OK", flush=True)
        for cmd in synced:
            print(f"[BOT] - /{cmd.name}", flush=True)
    except Exception as e:
        print(f"[BOT] Errore sync: {e}", flush=True)

@bot.tree.command(name="setup_calendario", description="Crea il post del calendario nel forum")
async def setup_calendario(interaction: discord.Interaction):
    # FIX DEFINITIVO TIMEOUT - defer immediato
    try:
        await interaction.response.defer(ephemeral=True)
        print(f"[CMD] /setup_calendario da {interaction.user} in {interaction.channel}", flush=True)
    except Exception as e:
        print(f"[CMD] Errore defer: {e}", flush=True)
        return

    try:
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Devi usare il comando in un server.", ephemeral=True)
            return

        # Trova il forum
        forum = guild.get_channel(CANALE_FISSO_ID)
        if not forum:
            # prova a cercare per nome "a" se ID non trovato
            for ch in guild.channels:
                if ch.name == "a" and isinstance(ch, discord.ForumChannel):
                    forum = ch
                    break

        if not forum or not isinstance(forum, discord.ForumChannel):
            await interaction.followup.send(f"Non trovo il forum con ID {CANALE_FISSO_ID}. Controlla CANALE_FISSO_ID.", ephemeral=True)
            return

        # Crea thread
        cover_path = "cover_C_corretta_finale.png"
        file = None
        if os.path.exists(cover_path):
            file = discord.File(cover_path, filename="cover.png")

        # Contenuto del post - puoi personalizzare
        content = (
            "**CALENDARIO EVENTI**\n\n"
            "Reagisci a un post per segnare la partecipazione.\n"
            "Usa /crea_evento per creare un nuovo evento."
        )

        thread_with_message = await forum.create_thread(
            name="Calendario",
            content=content,
            file=file
        )
        # create_thread ritorna Thread con messaggio a seconda della versione
        # in discord.py 2.3 ritorna Thread
        print(f"[CMD] Thread creato: {thread_with_message}", flush=True)

        await interaction.followup.send(f"Post pubblicato in {forum.mention}", ephemeral=True)

    except Exception as e:
        print(f"[CMD] Errore durante setup: {e}", flush=True, file=sys.stderr)
        import traceback
        traceback.print_exc()
        try:
            await interaction.followup.send(f"Errore: {e}", ephemeral=True)
        except:
            pass

# --- AVVIO BOT ---
if TOKEN:
    try:
        print("[SYSTEM] Tento connessione a Discord...", flush=True)
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("[ERRORE CRITICO] LoginFailure: TOKEN non valido! Resetta il token su Discord Developer Portal e rimettilo su Render > Environment", flush=True)
        while True:
            time.sleep(60)
    except Exception as e:
        print(f"[ERRORE CRITICO] Bot crashato: {e}", flush=True)
        import traceback
        traceback.print_exc()
        while True:
            time.sleep(60)
