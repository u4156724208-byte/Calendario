const { Client, GatewayIntentBits, SlashCommandBuilder, REST, Routes } = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus, VoiceConnectionStatus, entersState } = require('@discordjs/voice');
const https = require('https');

const TOKEN = process.env.DISCORD_TOKEN;
const CLIENT_ID = '1556323733046693920';
const RADIO_URL = 'https://icecast.unitedradio.it/Radio105.mp3'; // stream diretto, no YouTube, no abort

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates] });

const commands = [
  new SlashCommandBuilder().setName('party').setDescription('Avvia Radio 105 nel tuo canale vocale').toJSON(),
  new SlashCommandBuilder().setName('stop').setDescription('Ferma la radio').toJSON(),
].map(c => { return c; });

const rest = new REST({ version: '10' }).setToken(TOKEN);
(async () => {
  try {
    console.log('Registrazione comandi...');
    await rest.put(Routes.applicationCommands(CLIENT_ID), { body: commands });
    console.log('✅ Comandi registrati: /party, /stop');
  } catch (e) { console.error(e); }
})();

function getStream() {
  return new Promise((resolve, reject) => {
    const req = https.get(RADIO_URL, res => {
      if (res.statusCode !== 200) return reject(new Error('Status ' + res.statusCode));
      resolve(res);
    });
    req.on('error', reject);
    req.setTimeout(15000, () => { req.destroy(); reject(new Error('Timeout stream')); });
  });
}

let player = null;
let connection = null;

client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand()) return;
  
  if (interaction.commandName === 'party') {
    const member = interaction.member;
    const voiceChannel = member?.voice?.channel;
    if (!voiceChannel) return interaction.reply({ content: '❌ Entra prima in un canale vocale!', ephemeral: true });

    await interaction.deferReply();

    try {
      // chiudi vecchia connessione se c'è
      if (connection) { try { connection.destroy(); } catch {} }

      connection = joinVoiceChannel({
        channelId: voiceChannel.id,
        guildId: interaction.guildId,
        adapterCreator: interaction.guild.voiceAdapterCreator,
        selfDeaf: false,
      });

      await entersState(connection, VoiceConnectionStatus.Ready, 10000);

      const stream = await getStream();
      
      // FIX ABORT: nessuna abort controller, stream diretto
      const resource = createAudioResource(stream, {
        inlineVolume: false,
        inputType: 'arbitrary',
      });

      player = createAudioPlayer();
      player.play(resource);
      connection.subscribe(player);

      player.on(AudioPlayerStatus.Idle, async () => {
        try {
          console.log('Stream finito, riconnessione...');
          const newStream = await getStream();
          const newRes = createAudioResource(newStream, { inputType: 'arbitrary' });
          player.play(newRes);
        } catch(e) { console.log('Riconnessione fallita', e.message); }
      });

      player.on('error', async err => {
        console.error('Player error:', err.message);
        try {
          const newStream = await getStream();
          const newRes = createAudioResource(newStream, { inputType: 'arbitrary' });
          player.play(newRes);
        } catch(e) {}
      });

      await interaction.editReply(`📻 **Radio 105 ON** in ${voiceChannel.name} - Buon ascolto!`);
      console.log(`Radio avviata in ${voiceChannel.name}`);

    } catch (e) {
      console.error('Errore party:', e);
      await interaction.editReply(`❌ Errore: ${e.message}. Riprova /party`);
      if (connection) { try { connection.destroy(); } catch {} connection = null; }
    }
  }

  if (interaction.commandName === 'stop') {
    if (connection) { connection.destroy(); connection = null; player = null; }
    await interaction.reply({ content: '⏹️ Radio fermata', ephemeral: true });
  }
});

client.once('ready', () => console.log(`✅ Ready as ${client.user.tag}`));
client.login(TOKEN);

// Keep alive per Render + UptimeRobot
require('http').createServer((req,res)=>res.end('Radio105 BOT OK')).listen(process.env.PORT||10000);
