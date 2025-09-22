import discord
from discord.ext import commands
import youtube_dl
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='-', intents=intents)

# إعدادات youtube-dl
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ydl_opts)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} جاهز للعمل!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="-play"))

@bot.command()
async def play(ctx, *, query):
    """تشغيل أغنية من YouTube"""
    if not ctx.author.voice:
        return await ctx.send("❌ يجب ان تدخل روم صوتي اولاً!")
    
    voice_channel = ctx.author.voice.channel
    
    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)
    
    await ctx.send("🔍 **جاري البحث...**")
    
    try:
        # إذا كان رابط YouTube
        if 'youtube.com' in query or 'youtu.be' in query:
            player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
        else:
            # بحث على YouTube
            player = await YTDLSource.from_url(f"ytsearch:{query}", loop=bot.loop, stream=True)
        
        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(player, after=lambda e: print('تم الانتهاء من التشغيل'))
            await ctx.send(f"🎶 **الآن يعزف:** {player.title}")
        else:
            await ctx.send(f"✅ **تمت الإضافة:** {player.title}")
            
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)}")

@bot.command()
async def stop(ctx):
    """إيقاف البوت"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 **تم الإيقاف**")

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

TOKEN = os.environ['TOKEN']
bot.run(TOKEN)
