import discord
from discord.ext import commands
import os

# تحميل opus-library قبل أي شيء
discord.opus.load_opus('libopus.so.0')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='-', intents=intents)

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} جاهز للعمل!')
    print(f'🔊 Opus loaded: {discord.opus.is_loaded()}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="-play"))

@bot.command()
async def play(ctx):
    """الاتصال بالروم الصوتي فقط"""
    if not ctx.author.voice:
        return await ctx.send("❌ يجب ان تدخل روم صوتي اولاً!")
    
    try:
        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        
        # الاتصال مع إعدادات خاصة
        vc = await voice_channel.connect()
        await ctx.send(f"✅ **اتصلت بروم:** {voice_channel.name}")
        
        # اختبار بسيط
        source = discord.FFmpegPCMAudio('https://www.soundjay.com/misc/sounds/bell-ringing-05.wav')
        vc.play(source)
        await ctx.send("🔊 **تشغيل صوت اختباري**")
        
    except Exception as e:
        await ctx.send(f"❌ خطأ في الاتصال: {str(e)}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 **تم الإيقاف**")

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

TOKEN = os.environ['TOKEN']
bot.run(TOKEN)
