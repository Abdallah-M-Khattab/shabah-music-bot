import discord
from discord.ext import commands
import asyncio
import os
from pytube import YouTube
from pytube.exceptions import PytubeError
import io

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='-', intents=intents)

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} جاهز للعمل!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="-play"))

async def play_audio(ctx, url):
    """تشغيل audio من YouTube باستخدام pytube"""
    try:
        # تحميل معلومات الفيديو
        yt = YouTube(url)
        
        # الحصول على أفضل audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            await ctx.send("❌ لم أستطع العثور على audio")
            return None
            
        await ctx.send(f"🎵 **جاري التشغيل:** {yt.title}")
        
        # تحميل audio إلى memory
        audio_buffer = io.BytesIO()
        audio_stream.stream_to_buffer(audio_buffer)
        audio_buffer.seek(0)
        
        return discord.FFmpegPCMAudio(audio_buffer, pipe=True)
        
    except PytubeError as e:
        await ctx.send(f"❌ خطأ في تحميل الفيديو: {e}")
        return None
    except Exception as e:
        await ctx.send(f"❌ خطأ غير متوقع: {e}")
        return None

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
    
    # إذا كان query رابط YouTube
    if query.startswith('http'):
        url = query
    else:
        # بحث بسيط (سيحتاج تطوير)
        url = f"ytsearch:{query}"
        await ctx.send("⚠️ البحث بالنص يحتاج تطوير إضافي، استخدم رابط YouTube مباشرة")
        return
    
    try:
        audio_source = await play_audio(ctx, url)
        
        if audio_source and not ctx.voice_client.is_playing():
            ctx.voice_client.play(audio_source)
            await ctx.send("✅ **بدأ التشغيل**")
        else:
            await ctx.send("❌ لم أستطع تشغيل الموسيقى")
            
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
