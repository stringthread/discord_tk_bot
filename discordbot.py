import discord
from discord.ext import commands
import os
import traceback
import asyncio

bot = commands.Bot(command_prefix='!')
token = os.environ['DISCORD_BOT_TOKEN']
se_start=discord.FFmpegPCMAudio("audio/start.mp3")
se_fin=discord.FFmpegPCMAudio("audio/fin.mp3")

async def se(vc_list,src):
    for ch in vc_list:
        v_client=await ch.connect()
        v_client.play(src)
        await v_client.disconnect()

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def t(ctx,arg):
    global se_start
    global se_fin
    if not(arg.isdecimal()):
        await ctx.send('Error: invalid time.')
        return
    sec=int(arg)
    if len(arg)>=3:
        sec=sec//100*60+sec%100
    else:
        sec*=60
    ch=ctx.channel
    cat=ctx.guild.get_channel(ch.category_id)
    vc_list=cat.voice_channels
    await se(vc_list,se_start)
    await ctx.send(f"Timer set: {sec}")
    await asyncio.sleep(sec)
    await ctx.send('Finished!')
    await se(vc_list,se_fin)


bot.run(token)
