const { Client, GatewayIntentBits, SlashCommandBuilder, REST, Routes } = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus, NoSubscriberBehavior } = require('@discordjs/voice');
const https = require('https');

const TOKEN = process.env.DISCORD_TOKEN;
const CLIENT_ID = '1556323733046693920';
const RADIO_URL = 'https://icecast.unitedradio.it/Radio105.mp3';

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates] });

const commands = [
  new SlashCommandBuilder().setName('party').setDescription('Avvia Radio 105').toJSON(),
  new SlashCommandBuilder().setName('stop').setDescription('Ferma radio').toJSON(),
];

const rest = new REST({ version: '10' }).setToken(TOKEN);
(async () => {
  try {
    console.log('Registrazione comandi...');
    await rest.put(Routes.applicationCommands(CLIENT_ID), { body: commands });
    console.log('✅ Comandi registrati');
  } catch (e) { console.error(e); }
})();

function getStream() {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Icy-MetaData': '1'
      }
    };
    const req = https.get(RADIO_URL, options, res => {
      console.log('Icecast status:', res.statusCode);
      if (res.statusCode !== 200) return reject(new Error('Icecast status ' + res.statusCode));
      resolve(res);
    });
    req.on('error', (err) => {
      console.error('https error:', err.message);
      reject(err);
    });
    req.setTimeout(20000, () => {
      console.error('https timeout');
      req.destroy(new Error('Timeout'));
    });
  });
}

let player = null;
let connection = null;

client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand()) return;
  const vc = interaction.member?.voice?.channel;
  
  if (interaction.commandName === 'party') {
    if (!vc) return interaction.reply({ content: '❌ Entra in vocale prima!', ephemeral: true }).catch(()=>{});
    
    try {
      await interaction.deferReply({ ephemeral: false });
    } catch(e) {
      console.log('defer fallito, continuo');
    }

    try {
      if (connection) { try { connection.destroy(); } catch {} connection = null; }

      console.log('Join', vc.name);
      connection = joinVoiceChannel({
        channelId: vc.id,
        guildId: interaction.guildId,
        adapterCreator: interaction.guild.voiceAdapterCreator,
        selfDeaf: false,
        selfMute: false,
      });

      // NIENTE entersState - era quello che abortiva su Render

      console.log('Get stream...');
      const stream = await getStream();
      console.log('Stream OK, creo resource');
      
      const resource = createAudioResource(stream, {
        inputType: 'arbitrary',
        inlineVolume: false,
      });

      player = createAudioPlayer({
        behaviors: { noSubscriber: NoSubscriberBehavior.Play }
      });

      player.on(AudioPlayerStatus.Idle, async () => {
        console.log('Idle -> riconnessione');
        try {
          const s = await getStream();
          player.play(createAudioResource(s, { inputType: 'arbitrary' }));
        } catch(e){ console.error('reconnect fail', e.message); }
      });
      player.on('error', e => {
        console.error('player error', e.message);
      });

      player.play(resource);
      connection.subscribe(player);

      await interaction.editReply(`📻 **Radio 105 ON** in ${vc.name}`).catch(async () => {
        await interaction.followUp(`📻 **Radio 105 ON** in ${vc.name}`).catch(()=>{});
      });
      console.log('ON in', vc.name);

    } catch (e) {
      console.error('ERRORE PARTY REALE:', e.stack || e.message);
      const msg = `❌ Errore vero: ${e.message} - log su Render`;
      try {
        await interaction.editReply(msg);
      } catch {
        try { await interaction.followUp({ content: msg, ephemeral: true }); } catch {}
      }
      if (connection) { try { connection.destroy(); } catch {} connection = null; }
    }
  }

  if (interaction.commandName === 'stop') {
    if (connection) { try { connection.destroy(); } catch {} connection = null; player = null; }
    await interaction.reply({ content: '⏹️ Fermata', ephemeral: true }).catch(()=>{});
  }
});

client.once('ready', () => console.log(`✅ Ready as ${client.user.tag} - V8 NO-ABORT`));
client.login(TOKEN);

require('http').createServer((req,res)=>res.end('V8 OK')).listen(process.env.PORT||10000);
