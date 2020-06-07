import discord
from discord.ext import commands
import os
import traceback
import asyncio
import datetime

bot = commands.Bot(command_prefix='!')
token = os.environ['DISCORD_BOT_TOKEN']
v_cl=None
tasks={}
future={}

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
async def s(ctx):
    global tasks,future
    if ctx.channel.id in future:
        await ctx.send("Timer stopped.")
        future[ctx.channel.id].set_result(False)
        tasks[ctx.channel.id].cancel()
        del tasks[ctx.channel.id]

@bot.command()
async def t(ctx,arg):
    global v_cl,tasks,future
    if not(arg.isdecimal()):
        await ctx.send('Error: invalid time.')
        return
    sec=int(arg)
    if len(arg)>=3:
        sec=sec//100*60+sec%100
    else:
        sec*=60
#    ch=ctx.channel
#    cat=ctx.guild.get_channel(ch.category_id)
#    vc_list=cat.voice_channels
#    await se(vc_list,se_start)
    voice_state=ctx.author.voice
    flg_vc=not((not voice_state) or (not voice_state.channel))
    if not flg_vc:
        await ctx.send("You have to join a voice channnel first.")
    elif v_cl==None:
        v_cl=await voice_state.channel.connect()
    elif v_cl.channel!=voice_state.channel:
        await v_cl.move_to(voice_state.channel)
    if v_cl:
        v_cl.play(discord.FFmpegPCMAudio("audio/start.mp3"))
    await ctx.send(f"Timer set: {sec}")
    loop=asyncio.get_event_loop()
    future[ctx.channel.id]=loop.create_future()
    tasks[ctx.channel.id]=loop.call_later(sec,future[ctx.channel.id].set_result,True)
    await future[ctx.channel.id]
    if future[ctx.channel.id].result():
        await ctx.send('Finished!')
#        await se(vc_list,se_fin)
        if flg_vc:
            v_cl.play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        del future[ctx.channel.id]
        if ctx.channel.id in tasks:
            del tasks[ctx.channel.id]
    else:
        await ctx.send('timer finished')


bot.run(token)
