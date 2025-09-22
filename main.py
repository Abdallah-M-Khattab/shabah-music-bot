import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# إعدادات البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='-', intents=intents)

# إعدادات الصوت
# إعدادات yt-dlp المعدلة
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,  # ✅ أهم إضافة
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'verbose': False,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

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

# قائمة الانتظار
queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} جاهز للعمل على Railway!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="-play"))

@bot.command()
async def play(ctx, *, query):
    """تشغيل أغنية"""
    if not ctx.author.voice:
        return await ctx.send("❌ يجب ان تدخل روم صوتي اولاً!")
    
    voice_channel = ctx.author.voice.channel
    
    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)
    
    await ctx.send("🔍 **جاري البحث...**")
    
    try:
        player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
        queue = get_queue(ctx.guild.id)
        queue.append(player)
        
        if not ctx.voice_client.is_playing():
            await play_next(ctx)
        else:
            await ctx.send(f"✅ **تمت الإضافة:** {player.title}")
            
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)}")

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if queue:
        player = queue.pop(0)
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"🎶 **الآن يعزف:** {player.title}")

@bot.command()
async def skip(ctx):
    """تخطي الأغنية"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ **تم التخطي**")

@bot.command()
async def queue(ctx):
    """عرض قائمة الانتظار"""
    queue = get_queue(ctx.guild.id)
    if not queue:
        return await ctx.send("📭 **القائمة فارغة**")
    
    embed = discord.Embed(title="📋 قائمة الانتظار", color=0x00ff00)
    for i, player in enumerate(queue[:10], 1):
        embed.add_field(name=f"{i}. {player.title}", value="", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
    """إيقاف مؤقت"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ **متوقف مؤقتاً**")

@bot.command()
async def resume(ctx):
    """استئناف التشغيل"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ **يعود التشغيل**")

@bot.command()
async def stop(ctx):
    """إيقاف البوت"""
    if ctx.voice_client:
        queue = get_queue(ctx.guild.id)
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 **تم الإيقاف**")

@bot.command()
async def ping(ctx):
    """فحص سرعة البوت"""
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

if __name__ == "__main__":
    TOKEN = os.environ['TOKEN']

    bot.run(TOKEN)
