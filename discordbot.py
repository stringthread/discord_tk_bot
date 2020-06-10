import discord
from discord.ext import commands
import os
import traceback
import dataclasses
from typing import ClassVar,Dict
import asyncio
import datetime

N_BOTS=2
bot = [commands.Bot(command_prefix='!') for i in range(N_BOTS)]
token = [os.environ['DISCORD_BOT_TOKEN'],os.environ['DISCORD_BOT_TOKEN_2']]

async def check_priv(ctx):
    return True
    
@dataclasses.dataclass
class Cog(commands.Cog):
    bot: commands.Bot
    bot_id: int
    cat2bot: ClassVar[Dict[int,int]]={} #Category_id->Bot id
    bot2cat: ClassVar[Dict[int,int]]={} #Bot_id->Category_id. (Can use for checking if bot is used)
    v_cl=None
    task=None
    future=None
    flg_call=None
    loop=None

    async def se(self,vc_list,src):
        ch_before=None
        if self.v_cl!=None: ch_before=self.v_cl.channel
        for ch in vc_list:
            if self.v_cl==None:
                self.v_cl=await ch.connect()
            else:
                if self.v_cl.is_playing(): self.v_cl.stop()
                await self.v_cl.move_to(ch)
            if not(self.loop) or self.loop.is_closed():
                self.loop=asyncio.get_event_loop()
            self.future=self.loop.create_self.future()
            self.v_cl.play(discord.FFmpegPCMAudio(src),after=lambda err:self.future.set_result(0))
            await self.future
        if ch_before!=None:
            await self.v_cl.move_to(ch_before)

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        orig_error = getattr(error, "original", error)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        await ctx.send(error_msg)

    @commands.command()
    @commands.check(check_priv)
    async def l(self,ctx):
        if self.v_cl: self.v_cl.disconnect()
        del Cog.cat2bot[Cog.bot2cat[self.bot_id]]
        del Cog.bot2cat[self.bot_id]

    @commands.command()
    @commands.check(check_priv)
    async def s(self,ctx):
        if ctx.channel.id in self.future:
            dt=datetime.timedelta(seconds=self.task.when()-self.loop.time())
            self.future.set_result(False)
            self.task.cancel()
            del self.task
            await ctx.send(f"Timer stopped: {dt.seconds//60} min {dt.seconds%60} sec left.")
            voice_state=ctx.author.voice
            if not((not voice_state) or (not voice_state.channel)):
                flg_self_play=True
                if self.flg_call:
                    ch=ctx.channel
                    if hasattr(ch,"category_id"):
                        cat=ctx.guild.get_channel(ch.category_id)
                        if cat!=None:
                            vc_list=cat.voice_channels
                            flg_self_play=False
                            await self.se(vc_list,"audio/fin.mp3")
                if flg_self_play:
                    flg_vc=not((not voice_state) or (not voice_state.channel))
                    if not flg_vc:
                        await ctx.send("You have to join a voice channnel first.")
                    elif self.v_cl==None:
                        self.v_cl=await voice_state.channel.connect()
                    else:
                        if self.v_cl.is_playing(): self.v_cl.stop()
                        if self.v_cl.channel!=voice_state.channel:
                            await self.v_cl.move_to(voice_state.channel)
                    self.v_cl.play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        else:
            await ctx.send("Timer is not running.")

    @commands.command()
    @commands.check(check_priv)
    async def t(self,ctx,arg_t,arg_b='No'):
        if ctx.channel.category_id in Cog.cat2bot:
            if Cog.cat2bot[ctx.channel.category_id]!=self.bot_id:
                return
        else:
            for i in range(1,self.bot_id):
                if not(i in Cog.bot2cat): return
            Cog.cat2bot[ctx.channel.category_id]=self.bot_id
            Cog.bot2cat[self.bot_id]=ctx.channel.category_id
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
        self.flg_call=(arg_b in ['Y','Yes','y','yes'])
    #    ch=ctx.channel
    #    cat=ctx.guild.get_channel(ch.category_id)
    #    vc_list=cat.voice_channels
    #    await se(vc_list,se_start)
        voice_state=ctx.author.voice
        flg_vc=not((not voice_state) or (not voice_state.channel))
        if not flg_vc:
            await ctx.send("You have to join a voice channel first.")
        elif self.v_cl==None:
            self.v_cl=await voice_state.channel.connect()
        else:
            if self.v_cl.is_playing(): self.v_cl.stop()
            if self.v_cl.channel!=voice_state.channel:
                await self.v_cl.move_to(voice_state.channel)
        if self.v_cl:
            self.v_cl.play(discord.FFmpegPCMAudio("audio/start.mp3"))
        await ctx.send(f"Timer set: {dt.seconds//60} min {dt.seconds%60} sec.")
        self.loop=asyncio.get_event_loop()
        self.future=self.loop.create_self.future()
        self.task=self.loop.call_later(dt.total_seconds(),self.future.set_result,True)
        result_future=await self.future
        if result_future:
            await ctx.send('Finished!')
            if flg_vc:
                flg_self_play=True
                if self.flg_call:
                    ch=ctx.channel
                    if hasattr(ch,"category_id"):
                        cat=ctx.guild.get_channel(ch.category_id)
                        if cat!=None:
                            vc_list=cat.voice_channels
                            flg_self_play=False
                            await self.se(vc_list,"audio/fin.mp3")
                if flg_self_play:
                    if self.v_cl==None:
                        self.v_cl=await voice_state.channel.connect()
                    else:
                        if self.v_cl.is_playing(): self.v_cl.stop()
                        if self.v_cl.channel!=voice_state.channel:
                            await self.v_cl.move_to(voice_state.channel)
                    self.v_cl.play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        if ctx.channel.id in self.future: del self.future
        if ctx.channel.id in self.task: del self.task

loop=asyncio.get_event_loop()
for i in range(N_BOTS):
    bot[i].add_cog(Cog(bot=bot[i],bot_id=i))
    loop.run_until_complete(bot[i].login(token[i]))
    loop.create_task(bot[i].connect())
loop.run_forever()