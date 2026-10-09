BLACKOUT Translator - FIX FINALE
================================
1. Estrai zip
2. Carica bot.py e requirements.txt su GitHub (sovrascrivi)
3. Su Render -> Environment:
   DISCORD_TOKEN = token tuo bot
   DEEPL_KEY = chiave DeepL free (finisce con :fx) -> https://www.deepl.com/it/account/summary
   AUTO_CHANNELS = (lascia vuoto, poi metti ID canale dopo /traduci)
4. Deploy -> Clear build cache & Deploy
5. Discord -> /traduci nel canale WARDOGS
6. Nei log Render vedrai: Bot ONLINE | DeepL=ON

Fix inclusi:
- DeepL come traduttore principale (non bloccato da Render, italiano perfetto)
- chunk_smart che non rompe "6 seconds" in "6 s econds"
- auto-recovery: se Render dorme, al prossimo WARDOGS si riattiva da solo
- Persistenza via ENV AUTO_CHANNELS
