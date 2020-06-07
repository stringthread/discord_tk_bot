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
loop=None

async def se(vc_list,src):
    global v_cl,loop
    ch_before=None
    if v_cl!=None: ch_before=v_cl.channel
    for ch in vc_list:
        if v_cl==None:
            v_cl=await ch.connect()
        elif v_cl.channel!=ch:
            await v_cl.move_to(ch)
        if not(loop) or loop.is_closed():
            loop=asyncio.get_event_loop()
        future=loop.create_future()
        v_cl.play(src,after=lambda err:future.set_result(0))
        await future
    if ch_before!=None:
        await v_cl.move_to(ch_before)

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

@bot.command()
async def s(ctx):
    global tasks,future
    if ctx.channel.id in future:
        dt=datetime.timedelta(seconds=tasks[ctx.channel.id].when()-loop.time())
        await ctx.send(f"Timer stopped: {dt.seconds//60} min {dt.seconds%60} sec left.")
        future[ctx.channel.id].set_result(False)
        tasks[ctx.channel.id].cancel()
        del tasks[ctx.channel.id]

@bot.command()
async def t(ctx,arg_t,arg_b=False):
    global v_cl,tasks,future,loop
    if arg_t==None:
        await ctx.send('Error: no time input.')
        return
    if not(arg_t.isdecimal()):
        await ctx.send('Error: invalid time.')
        return
    if len(arg_t)>=3:
        dt=datetime.timedelta(minutes=int(arg_t[0:-2]),seconds=int(arg_t[-2:]))
    else:
        dt=datetime.timedelta(minutes=int(arg_t))
    if arg_b: arg_b=(arg_b in ['Y','Yes','y','yes'])
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
    await ctx.send(f"Timer set: {dt.seconds//60} min {dt.seconds%60} sec.")
    loop=asyncio.get_event_loop()
    future[ctx.channel.id]=loop.create_future()
    tasks[ctx.channel.id]=loop.call_later(dt.total_seconds(),future[ctx.channel.id].set_result,True)
    await future[ctx.channel.id]
    if future[ctx.channel.id].result():
        await ctx.send('Finished!')
        if flg_vc:
            flg_self_play=True
            if arg_b:
                ch=ctx.channel
                if hasattr(ch,"category_id"):
                    cat=ctx.guild.get_channel(ch.category_id)
                    if cat!=None:
                        vc_list=cat.voice_channels
                        flg_self_play=False
                        await se(vc_list,discord.FFmpegPCMAudio("audio/fin.mp3"))
            if flg_self_play: v_cl.play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        del future[ctx.channel.id]
        if ctx.channel.id in tasks:
            del tasks[ctx.channel.id]


bot.run(token)
