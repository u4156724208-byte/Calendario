import discord
from discord import app_commands
import asyncio
import os
import json
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    try:
        with open('auto_channels.json','r') as f:
            count = len(json.load(f))
    except:
        count = 0
    deepl = "ON" if os.getenv("DEEPL_KEY") else "OFF"
    return f"BLACKOUT Translator Online - DeepL={deepl} - {count} canali - OK"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_flask, daemon=True).start()

def chunk_smart(text, max_len=380):
    chunks = []
    while len(text) > max_len:
        cut = text.rfind(' ', 0, max_len)
        if cut == -1:
            cut = text.rfind('\n', 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks

def deepl_translate(text, target='IT'):
    """DeepL Free API - 500k chars/mese gratis, non bloccato su Render"""
    key = os.getenv("DEEPL_KEY")
    if not key:
        return None
    try:
        # Usa api-free per chiavi free
        url = "https://api-free.deepl.com/v2/translate"
        data = {
            "auth_key": key,
            "text": text[:4000],
            "target_lang": target,
            "source_lang": "EN"
        }
        r = requests.post(url, data=data, timeout=15)
        if r.status_code == 200:
            j = r.json()
            trans = j.get("translations", [{}])[0].get("text")
            if trans:
                return trans
        elif r.status_code == 403:
            # Prova con api.deepl.com (chiave pro)
            url = "https://api.deepl.com/v2/translate"
            r = requests.post(url, data=data, timeout=15)
            if r.status_code == 200:
                j = r.json()
                return j.get("translations", [{}])[0].get("text")
        print(f"[DeepL status {r.status_code}] {r.text[:200]}")
    except Exception as e:
        print(f"[DeepL fail] {e}")
    return None

def mymemory_translate(text):
    try:
        r = requests.get("https://api.mymemory.translated.net/get",
                         params={"q": text[:380], "langpair": "en|it", "de": "blackout@translator.com"},
                         timeout=15)
        if r.status_code == 200:
            j = r.json()
            t = j.get("responseData", {}).get("translatedText")
            if t and "QUERY LENGTH" not in t.upper() and "MYMEMORY WARNING" not in t.upper():
                return t
    except Exception as e:
        print(f"[MyMemory fail] {e}")
    return None

def google_free_translate(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "en", "tl": "it", "dt": "t", "q": text}
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data[0], list):
                translated = "".join([item[0] for item in data[0] if item and len(item)>0 and item[0]])
                if translated:
                    return translated
    except:
        pass
    return None

def traduci_sync(text: str) -> str:
    if not text or not text.strip():
        return text
    low = text.strip().lower()
    # Emergenza
    if low in {"hello world":"ciao mondo","hello":"ciao","hi":"ciao","thanks":"grazie","thank you":"grazie"}:
        return {"hello world":"ciao mondo","hello":"ciao","hi":"ciao","thanks":"grazie","thank you":"grazie"}[low]

    # 1. DeepL (migliore, non bloccato)
    res = deepl_translate(text[:4000], 'IT')
    if res and res.lower().strip() != low:
        print(f"[DeepL OK] {text[:40]} -> {res[:40]}")
        return res

    # 2. Google diretto
    res = google_free_translate(text[:4000])
    if res and res.lower().strip() != low and res.lower().strip() != text.lower().strip():
        return res

    # 3. MyMemory
    res = mymemory_translate(text[:380])
    if res and res.lower().strip() != low and res.lower().strip() != text.lower().strip():
        return res

    return text

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

AUTO_FILE = "auto_channels.json"
# Leggi canali fissi da env var per persistenza su Render (es: "123,456,789")
ENV_CHANNELS = os.getenv("AUTO_CHANNELS", "")

def load_auto():
    channels = set()
    # 1. Da file (se esiste)
    try:
        with open(AUTO_FILE,'r') as f:
            channels.update(set(json.load(f)))
    except:
        pass
    # 2. Da env var (persistente su Render)
    if ENV_CHANNELS:
        try:
            for cid in ENV_CHANNELS.split(","):
                cid = cid.strip()
                if cid.isdigit():
                    channels.add(int(cid))
        except Exception as e:
            print(f"ENV_CHANNELS parse error {e}")
    return channels

def save_auto(ch):
    try:
        with open(AUTO_FILE,'w') as f:
            json.dump(list(ch), f)
        # Log per aiutare a creare ENV var
        if ch:
            print(f"💾 Canali salvati: {','.join(map(str,ch))} -> Metti questo in ENV AUTO_CHANNELS su Render per renderlo permanente!")
    except Exception as e:
        print(f"Save error {e}")

auto_channels = load_auto()

@client.event
async def on_ready():
    deepl_status = "ON" if os.getenv("DEEPL_KEY") else "OFF (metti DEEPL_KEY su Render!)"
    print(f"Bot ONLINE {client.user} | {len(auto_channels)} canali | DeepL={deepl_status}")
    try:
        await tree.sync()
    except Exception as e:
        print(f"Sync error {e}")

@client.event
async def on_message(message):
    try:
        if client.user and message.author.id == client.user.id:
            return
    except:
        pass
    if "Translated from" in (message.content or ""):
        return
    if message.embeds:
        for em in message.embeds:
            if em.footer and em.footer.text and "BLACKOUT" in em.footer.text:
                return
    # AUTO-RECOVERY: se è PatchBot o webhook e il canale non è in lista, riattiva automaticamente
    # Questo fixa il problema "dopo un po non traduce piu" di Render
    if message.channel.id not in auto_channels:
        is_patchbot = False
        try:
            # PatchBot, webhook, o embed con WARDOGS / patch notes
            if message.author.bot:
                is_patchbot = True
            if message.embeds:
                for em in message.embeds:
                    title = (em.title or "").lower()
                    desc = (em.description or "").lower()
                    if "wardogs" in title or "wardogs" in desc or "hotfix" in title or "hotfix" in desc or "balance" in desc or "dead by daylight" in title.lower():
                        is_patchbot = True
        except:
            pass
        
        if is_patchbot:
            print(f"🔄 Auto-recovery: riattivo auto in #{message.channel.name} ({message.channel.id}) dopo restart Render")
            auto_channels.add(message.channel.id)
            save_auto(auto_channels)
        else:
            return

    parts = []
    if message.content and message.content.strip():
        txt = message.content.strip()
        if "will now receive notifications for" not in txt and "will no longer receive" not in txt:
            parts.append(txt)
    if message.embeds:
        for emb in message.embeds:
            if emb.title:
                parts.append(emb.title)
            if emb.description:
                parts.append(emb.description)
            for f in emb.fields:
                if f.value:
                    parts.append(f.value)
    
    orig = "\n".join(parts).strip()
    if not orig or len(orig) < 3:
        return
    if "will now receive notifications for" in orig.lower() and len(orig) < 300:
        embed_only = []
        for emb in message.embeds:
            if emb.title:
                embed_only.append(emb.title)
            if emb.description:
                embed_only.append(emb.description)
        if embed_only:
            orig = "\n".join(embed_only).strip()
        else:
            return

    try:
        if len(orig) > 380:
            chunks = chunk_smart(orig, 380)
            trad_parts = [traduci_sync(c) for c in chunks]
            trad = "\n".join(trad_parts)
        else:
            trad = await asyncio.to_thread(traduci_sync, orig)
        
        if trad and trad.strip() and trad.lower().strip() != orig.lower().strip():
            if len(trad) > 3500:
                trad = trad[:3500] + "..."
            emb = discord.Embed(description=f"**{trad}**", color=0x00ffcc)
            emb.set_footer(text=f"Translated from #{message.channel.name} by BLACKOUT | /traduci_stop per fermare")
            await message.channel.send(embed=emb)
    except Exception as e:
        print(f"[AUTO] Errore: {e}")

@tree.command(name="traduci", description="Traduci EN->IT o attiva auto")
@app_commands.describe(testo="Testo da tradurre (vuoto=attiva auto)")
async def traduci(interaction: discord.Interaction, testo: str = None):
    await interaction.response.defer(thinking=True)
    try:
        if not testo:
            auto_channels.add(interaction.channel.id)
            save_auto(auto_channels)
            await interaction.followup.send(f"✅ Auto ATTIVATA in <#{interaction.channel.id}>! Usa /traduci_stop per fermare.", ephemeral=True)
            return
        if len(testo) > 380:
            chunks = chunk_smart(testo, 380)
            finale = "\n".join([await asyncio.to_thread(traduci_sync, c) for c in chunks])
        else:
            finale = await asyncio.to_thread(traduci_sync, testo)
        await interaction.followup.send(f"**{finale[:3500]}**")
    except Exception as e:
        print(e)
        await interaction.followup.send(f"Errore {e}", ephemeral=True)

@tree.command(name="traduci_stop", description="Ferma auto")
async def traduci_stop(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    auto_channels.discard(interaction.channel.id)
    save_auto(auto_channels)
    await interaction.followup.send(f"🛑 Auto DISATTIVATA in <#{interaction.channel.id}>", ephemeral=True)

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ Manca DISCORD_TOKEN!")
    import time
    while True:
        time.sleep(3600)
else:
    client.run(TOKEN)
