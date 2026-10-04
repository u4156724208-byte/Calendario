import os, threading
from flask import Flask
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)
@app.route("/")
def home(): return "OK"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")
    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

def create_calendar_image():
    W, H = 800, 520
    bg = (54, 57, 63)
    fg = (255, 255, 255)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    # usa font di default grande
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
        font_month = ImageFont.truetype("DejaVuSans.ttf", 22)
        font_head = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        font_day = ImageFont.truetype("DejaVuSans.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_month = ImageFont.load_default()
        font_head = ImageFont.load_default()
        font_day = ImageFont.load_default()

    draw.text((30, 18), "CALENDARIO GIOCHI", font=font_title, fill=fg)
    draw.text((30, 62), "Ottobre 2026", font=font_month, fill=(180,180,180))

    # griglia
    cols = ["LUN","MAR","MER","GIO","VEN","SAB","DOM"]
    x_start = 30
    y_start = 120
    col_w = 106
    row_h = 55

    # header giorni
    for i, c in enumerate(cols):
        x = x_start + i*col_w
        draw.text((x+18, y_start), c, font=font_head, fill=fg)

    # giorni: 1 Ott 2026 = Giovedi (indice 3)
    days = [""]*3 + [f"{d:02d}" for d in range(1, 32)]
    y = y_start + row_h
    for week in range(0, len(days), 7):
        for col in range(7):
            idx = week + col
            if idx < len(days) and days[idx]:
                x = x_start + col*col_w + 26
                draw.text((x, y), days[idx], font=font_day, fill=fg)
        y += row_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@bot.tree.command(name="calendario", description="Mostra calendario giochi")
async def calendario(interaction: discord.Interaction):
    await interaction.response.defer()
    buf = create_calendar_image()
    file = discord.File(buf, filename="calendario.png")
    embed = discord.Embed(title="CALENDARIO GIOCHI - Ottobre 2026", color=0x2f3136)
    embed.set_image(url="attachment://calendario.png")
    await interaction.followup.send(embed=embed, file=file)

bot.run(os.getenv("DISCORD_TOKEN"))
