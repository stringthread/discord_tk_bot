import discord
from discord.ext import commands
import os
import traceback
import dataclasses
import asyncio
import datetime

bot = commands.Bot(command_prefix='!')
token = os.environ['DISCORD_BOT_TOKEN']
v_cl=None
tasks={}
future={}
flg_call={}
loop=None

@dataclasses.dataclass
class Cog(commands.Cog):
    @classmethod
    async def se(self,vc_list,src):
        global v_cl,loop
        ch_before=None
        if v_cl!=None: ch_before=v_cl.channel
        for ch in vc_list:
            if v_cl==None:
                v_cl=await ch.connect()
            else:
                if v_cl.is_playing(): v_cl.stop()
                await v_cl.move_to(ch)
            if not(loop) or loop.is_closed():
                loop=asyncio.get_event_loop()
            future=loop.create_future()
            v_cl.play(discord.FFmpegPCMAudio(src),after=lambda err:future.set_result(0))
            await future
        if ch_before!=None:
            await v_cl.move_to(ch_before)

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        orig_error = getattr(error, "original", error)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        await ctx.send(error_msg)

    @commands.command()
    async def s(self,ctx):
        global v_cl,tasks,future,flg_call
        if ctx.channel.id in future:
            dt=datetime.timedelta(seconds=tasks[ctx.channel.id].when()-loop.time())
            future[ctx.channel.id].set_result(False)
            tasks[ctx.channel.id].cancel()
            del tasks[ctx.channel.id]
            await ctx.send(f"Timer stopped: {dt.seconds//60} min {dt.seconds%60} sec left.")
            voice_state=ctx.author.voice
            if not((not voice_state) or (not voice_state.channel)):
                flg_self_play=True
                if flg_call[ctx.channel.id]:
                    ch=ctx.channel
                    if hasattr(ch,"category_id"):
                        cat=ctx.guild.get_channel(ch.category_id)
                        if cat!=None:
                            vc_list=cat.voice_channels
                            flg_self_play=False
                            await Cog.se(vc_list,"audio/fin.mp3")
                if flg_self_play:
                    flg_vc=not((not voice_state) or (not voice_state.channel))
                    if not flg_vc:
                        await ctx.send("You have to join a voice channnel first.")
                    elif v_cl==None:
                        v_cl=await voice_state.channel.connect()
                    else:
                        if v_cl.is_playing(): v_cl.stop()
                        if v_cl.channel!=voice_state.channel:
                            await v_cl.move_to(voice_state.channel)
                    v_cl.play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        else:
            await ctx.send("Timer is not running.")

    @commands.command()
    async def t(self,ctx,arg_t,arg_b='No'):
        global v_cl,tasks,future,loop,flg_call
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
        flg_call[ctx.channel.id]=(arg_b in ['Y','Yes','y','yes'])
    #    ch=ctx.channel
    #    cat=ctx.guild.get_channel(ch.category_id)
    #    vc_list=cat.voice_channels
    #    await se(vc_list,se_start)
        voice_state=ctx.author.voice
        flg_vc=not((not voice_state) or (not voice_state.channel))
        if not flg_vc:
            await ctx.send("You have to join a voice channel first.")
        elif v_cl==None:
            v_cl=await voice_state.channel.connect()
        else:
            if v_cl.is_playing(): v_cl.stop()
            if v_cl.channel!=voice_state.channel:
                await v_cl.move_to(voice_state.channel)
        if v_cl:
            v_cl.play(discord.FFmpegPCMAudio("audio/start.mp3"))
        await ctx.send(f"Timer set: {dt.seconds//60} min {dt.seconds%60} sec.")
        loop=asyncio.get_event_loop()
        future[ctx.channel.id]=loop.create_future()
        tasks[ctx.channel.id]=loop.call_later(dt.total_seconds(),future[ctx.channel.id].set_result,True)
        result_future=await future[ctx.channel.id]
        if result_future:
            await ctx.send('Finished!')
            if flg_vc:
                flg_self_play=True
                if flg_call[ctx.channel.id]:
                    ch=ctx.channel
                    if hasattr(ch,"category_id"):
                        cat=ctx.guild.get_channel(ch.category_id)
                        if cat!=None:
                            vc_list=cat.voice_channels
                            flg_self_play=False
                            await Cog.se(vc_list,"audio/fin.mp3")
                if flg_self_play:
                    if v_cl==None:
                        v_cl=await voice_state.channel.connect()
                    else:
                        if v_cl.is_playing(): v_cl.stop()
                        if v_cl.channel!=voice_state.channel:
                            await v_cl.move_to(voice_state.channel)
                    v_cl.play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        if ctx.channel.id in future: del future[ctx.channel.id]
        if ctx.channel.id in tasks: del tasks[ctx.channel.id]

bot.add_cog(Cog())
bot.run(token)
