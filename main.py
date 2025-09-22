import discord
from discord.ext import commands
import os

# لا تحمل opus يدوياً - دع discord.py يتعامل معه
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='-', intents=intents)

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} جاهز للعمل!')
    # تحقق إذا opus مثبت تلقائياً
    print(f'🔊 Opus متاح: {discord.opus.is_loaded()}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="-play"))

@bot.command()
async def join(ctx):
    """الانضمام إلى الروم الصوتي"""
    if not ctx.author.voice:
        return await ctx.send("❌ يجب ان تدخل روم صوتي اولاً!")
    
    try:
        voice_channel = ctx.author.voice.channel
        
        # إذا كان متصلاً بالفعل، اقطع الاتصال أولاً
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        
        # الاتصال بدون opus يدوي
        vc = await voice_channel.connect()
        await ctx.send(f"✅ **اتصلت بروم:** {voice_channel.name}")
        
    except Exception as e:
        await ctx.send(f"❌ خطأ في الاتصال: {str(e)}")

@bot.command()
async def play(ctx):
    """تشغيل صوت اختباري"""
    if not ctx.voice_client:
        return await ctx.send("❌ البوت غير متصل بالروم الصوتي! استخدم `-join` أولاً")
    
    try:
        # استخدم FFmpeg مباشرة بدون opus
        source = discord.FFmpegPCMAudio(
            'https://www.soundjay.com/misc/sounds/bell-ringing-05.wav',
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        )
        ctx.voice_client.play(source)
        await ctx.send("🔊 **جاري تشغيل الصوت الاختباري**")
    except Exception as e:
        await ctx.send(f"❌ خطأ في التشغيل: {str(e)}")

@bot.command()
async def leave(ctx):
    """مغادرة الروم الصوتي"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 **غادرت الروم الصوتي**")

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

TOKEN = os.environ['TOKEN']
bot.run(TOKEN)
