import discord
from discord.ext import commands
import os
import traceback
from typing import ClassVar,Dict
import asyncio
import datetime

N_BOTS=2
bot = [commands.Bot(command_prefix='!') for i in range(N_BOTS)]
token = [os.environ['DISCORD_BOT_TOKEN_'+str(i)] for i in range(1,N_BOTS+1)]

async def check_priv(ctx):
    return True

class Cog(commands.Cog):
    cat2bot: ClassVar[Dict[int,Dict[int,int]]]={} #Guild_id->[Category_id->Bot id]
    bot2cat: ClassVar[Dict[int,Dict[int,int]]]={} #Guild_id->[Bot_id->Category_id] (Can use for checking if bot is used)
    def __init__(self,bot,bot_id):
        self.bot: commands.Bot=bot
        self.bot_id: int=bot_id
        self.v_cl: Dict[int,discord.VoiceClient]={}
        self.task: Dict[int,asyncio.Task]={}
        self.future: Dict[int,asyncio.Future]={}
        self.flg_call: Dict[int,bool]={}
        self.loop: Dict[int,asyncio.BaseEventLoop]={}

    async def se(self,ctx,vc_list,src):
        ch_before=None
        if self.v_cl[ctx.guild.id]!=None: ch_before=self.v_cl[ctx.guild.id].channel
        for ch in vc_list:
            if not(ctx.guild.id in self.v_cl) or self.v_cl[ctx.guild.id]==None or not(self.v_cl[ctx.guild.id].is_connected()):
                self.v_cl[ctx.guild.id]=await ch.connect()
            else:
                if self.v_cl[ctx.guild.id].is_playing(): self.v_cl[ctx.guild.id].stop()
                await self.v_cl[ctx.guild.id].move_to(ch)
            if not(ctx.guild.id in self.loop) or not(self.loop[ctx.guild.id]) or self.loop[ctx.guild.id].is_closed():
                self.loop[ctx.guild.id]=asyncio.get_event_loop()
            future=self.loop[ctx.guild.id].create_future()
            self.v_cl[ctx.guild.id].play(discord.FFmpegPCMAudio(src),after=lambda err:future.set_result(0))
            await future
        if ch_before!=None:
            await self.v_cl[ctx.guild.id].move_to(ch_before)

    def sel_bot(self,ctx,flg_connect=False):
        if not(ctx.guild.id in Cog.cat2bot):
            return self.bot_id==0
        if ctx.channel.category_id in Cog.cat2bot[ctx.guild.id]:
            if Cog.cat2bot[ctx.guild.id][ctx.channel.category_id]!=self.bot_id:
                return False
        else:
            if self.bot_id in Cog.bot2cat[ctx.guild.id]:
                return False
            for i in range(self.bot_id):
                if not(i in Cog.bot2cat[ctx.guild.id]): return False
            if flg_connect:
                Cog.cat2bot[ctx.guild.id][ctx.channel.category_id]=self.bot_id
                Cog.bot2cat[ctx.guild.id][self.bot_id]=ctx.channel.category_id
        return True

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        orig_error = getattr(error, "original", error)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        await ctx.send(error_msg)

    @commands.command()
    @commands.check(check_priv)
    async def l(self,ctx):
        if not(self.sel_bot(ctx)): return
        if self.v_cl[ctx.guild.id]: await self.v_cl[ctx.guild.id].disconnect()
        del Cog.cat2bot[ctx.guild.id][Cog.bot2cat[ctx.guild.id][self.bot_id]]
        del Cog.bot2cat[ctx.guild.id][self.bot_id]

    @commands.command()
    @commands.check(check_priv)
    async def s(self,ctx):
        if not(self.sel_bot(ctx)): return
        if ctx.guild.id in self.future and self.future[ctx.guild.id]:
            if not(ctx.guild.id in self.loop) or not(self.loop[ctx.guild.id]) or self.loop[ctx.guild.id].is_closed():
                self.loop[ctx.guild.id]=asyncio.get_event_loop()
            dt=datetime.timedelta(seconds=self.task[ctx.guild.id].when()-self.loop[ctx.guild.id].time())
            self.future[ctx.guild.id].set_result(False)
            self.task[ctx.guild.id].cancel()
            self.task[ctx.guild.id]=None
            await ctx.send(f"Timer stopped: {dt.seconds//60} min {dt.seconds%60} sec left.")
            voice_state=ctx.author.voice
            if not((not voice_state) or (not voice_state.channel)):
                flg_self_play=True
                if ctx.guild.id in self.flg_call and self.flg_call[ctx.guild.id]:
                    ch=ctx.channel
                    if hasattr(ch,"category_id"):
                        cat=ctx.guild.get_channel(ch.category_id)
                        if cat!=None:
                            vc_list=cat.voice_channels
                            flg_self_play=False
                            await self.se(ctx,vc_list,"audio/fin.mp3")
                if flg_self_play:
                    flg_vc=not((not voice_state) or (not voice_state.channel))
                    if not flg_vc:
                        await ctx.send("You have to join a voice channnel first.")
                    elif not(ctx.guild.id in self.v_cl) or self.v_cl[ctx.guild.id]==None or not(self.v_cl[ctx.guild.id].is_connected()):
                        self.v_cl[ctx.guild.id]=await voice_state.channel.connect()
                    else:
                        if self.v_cl[ctx.guild.id].is_playing(): self.v_cl[ctx.guild.id].stop()
                        if self.v_cl[ctx.guild.id].channel!=voice_state.channel:
                            await self.v_cl[ctx.guild.id].move_to(voice_state.channel)
                    self.v_cl[ctx.guild.id].play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        else:
            await ctx.send("Timer is not running.")

    @commands.command()
    @commands.check(check_priv)
    async def t(self,ctx,arg_t=None,arg_b='No'):
        if not(self.sel_bot(ctx,True)): return
        if arg_t==None or not(arg_t.isdecimal()):
            await ctx.send('Error: no time input.')
            return
        if not(arg_t.isdecimal()):
            await ctx.send('Error: invalid time.')
            return
        if len(arg_t)>=3:
            dt=datetime.timedelta(minutes=int(arg_t[0:-2]),seconds=int(arg_t[-2:]))
        else:
            dt=datetime.timedelta(minutes=int(arg_t))
        self.flg_call[ctx.guild.id]=(arg_b in ['Y','Yes','y','yes'])
    #    ch=ctx.channel
    #    cat=ctx.guild.get_channel(ch.category_id)
    #    vc_list=cat.voice_channels
    #    await se(vc_list,se_start)

        voice_state=ctx.author.voice
        flg_vc=not((not voice_state) or (not voice_state.channel))
        if not flg_vc:
            await ctx.send("You have to join a voice channel first.")
        elif not(ctx.guild.id in self.v_cl) or self.v_cl[ctx.guild.id]==None or not(self.v_cl[ctx.guild.id].is_connected()):
            self.v_cl[ctx.guild.id]=await voice_state.channel.connect()
        else:
            if self.v_cl[ctx.guild.id].is_playing(): self.v_cl[ctx.guild.id].stop()
            if self.v_cl[ctx.guild.id].channel!=voice_state.channel:
                await self.v_cl[ctx.guild.id].move_to(voice_state.channel)
        if self.v_cl[ctx.guild.id]:
            self.v_cl[ctx.guild.id].play(discord.FFmpegPCMAudio("audio/start.mp3"))
        await ctx.send(f"Timer set: {dt.seconds//60} min {dt.seconds%60} sec.")
        self.loop[ctx.guild.id]=asyncio.get_event_loop()
        self.future[ctx.guild.id]=self.loop[ctx.guild.id].create_future()
        self.task[ctx.guild.id]=self.loop[ctx.guild.id].call_later(dt.total_seconds(),self.future[ctx.guild.id].set_result,True)
        result_future=await self.future[ctx.guild.id]
        if result_future:
            await ctx.send('Finished!')    
            voice_state=ctx.author.voice
            if not((not voice_state) or (not voice_state.channel)):
                flg_self_play=True
                if ctx.guild.id in self.flg_call and self.flg_call[ctx.guild.id]:
                    ch=ctx.channel
                    if hasattr(ch,"category_id"):
                        cat=ctx.guild.get_channel(ch.category_id)
                        if cat!=None:
                            vc_list=cat.voice_channels
                            flg_self_play=False
                            await self.se(ctx,vc_list,"audio/fin.mp3")
                if flg_self_play:
                    if not(ctx.guild.id in self.v_cl) or self.v_cl[ctx.guild.id]==None or not(self.v_cl[ctx.guild.id].is_connected()):
                        self.v_cl[ctx.guild.id]=await voice_state.channel.connect()
                    else:
                        if self.v_cl[ctx.guild.id].is_playing(): self.v_cl[ctx.guild.id].stop()
                        if self.v_cl[ctx.guild.id].channel!=voice_state.channel:
                            await self.v_cl[ctx.guild.id].move_to(voice_state.channel)
                    self.v_cl[ctx.guild.id].play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        if self.future[ctx.guild.id]: self.future[ctx.guild.id]=None
        if self.task[ctx.guild.id]: self.task[ctx.guild.id]=None

loop=asyncio.get_event_loop()
for i in range(N_BOTS):
    bot[i].add_cog(Cog(bot=bot[i],bot_id=i))
    loop.run_until_complete(bot[i].login(token[i]))
    loop.create_task(bot[i].connect())
loop.run_forever()