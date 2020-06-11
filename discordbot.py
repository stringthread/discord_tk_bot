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
    return check_priv_user(ctx.author)

def check_priv_user(user):
    return True

class Cog(commands.Cog):
    cat2bot: ClassVar[Dict[int,Dict[int,int]]]={} #Guild_id->[Category_id->Bot id]
    bot2cat: ClassVar[Dict[int,Dict[int,int]]]={} #Guild_id->[Bot_id->Category_id] (Can use for checking if bot is used)
    prefix_ui: str='>Discord TK Bot UI:'
    def __init__(self,bot,bot_id):
        self.bot: commands.Bot=bot
        self.bot_id: int=bot_id
        self.v_cl: Dict[int,discord.VoiceClient]={}
        self.task: Dict[int,asyncio.Task]={}
        self.future: Dict[int,asyncio.Future]={}
        self.flg_call: Dict[int,bool]={}
        self.loop: Dict[int,asyncio.BaseEventLoop]={}
        self.emoji_func={}

    async def se(self,guild_id,vc_list,src):
        ch_before=None
        if self.v_cl[guild_id]!=None: ch_before=self.v_cl[guild_id].channel
        for ch in vc_list:
            if not(guild_id in self.v_cl) or self.v_cl[guild_id]==None or not(self.v_cl[guild_id].is_connected()):
                self.v_cl[guild_id]=await ch.connect()
            else:
                if self.v_cl[guild_id].is_playing(): self.v_cl[guild_id].stop()
                await self.v_cl[guild_id].move_to(ch)
            if not(guild_id in self.loop) or not(self.loop[guild_id]) or self.loop[guild_id].is_closed():
                self.loop[guild_id]=asyncio.get_event_loop()
            future=self.loop[guild_id].create_future()
            self.v_cl[guild_id].play(discord.FFmpegPCMAudio(src),after=lambda err:future.set_result(0))
            await future
        if ch_before!=None:
            await self.v_cl[guild_id].move_to(ch_before)

    def sel_bot(self,guild_id,cat_id,flg_connect=False):
        if not(guild_id in Cog.cat2bot):
            if not(flg_connect) or self.bot_id!=0: return False
            Cog.cat2bot[guild_id]={cat_id:self.bot_id}
            Cog.bot2cat[guild_id]={self.bot_id:cat_id}
        if cat_id in Cog.cat2bot[guild_id]:
            if Cog.cat2bot[guild_id][cat_id]!=self.bot_id:
                return False
        else:
            if not(flg_connect): return False
            if self.bot_id in Cog.bot2cat[guild_id]:
                return False
            for i in range(self.bot_id):
                if not(i in Cog.bot2cat[guild_id]): return False
            Cog.cat2bot[guild_id][cat_id]=self.bot_id
            Cog.bot2cat[guild_id][self.bot_id]=cat_id
        return True

    @commands.Cog.listener()
    async def on_reaction_add(self,reaction,user):
        if not(check_priv_user(user)): return
        if not(reaction.message.content.startswith(Cog.prefix_ui)): return
        if not(reaction.emoji.name in self.emoji_func): return
        await self.emoji_func[reaction.emoji.name]()

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        orig_error = getattr(error, "original", error)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        await ctx.send(error_msg)

    async def l_in(self,guild_id,cat_id):
        if not(self.sel_bot(guild_id,cat_id)): return
        if guild_id in self.v_cl and self.v_cl[guild_id]:
            await self.v_cl[guild_id].disconnect()
            del self.v_cl[guild_id]
        del Cog.cat2bot[guild_id][Cog.bot2cat[guild_id][self.bot_id]]
        del Cog.bot2cat[guild_id][self.bot_id]

    @commands.command()
    @commands.check(check_priv)
    async def l(self,ctx):
        await self.l_in(ctx.guild.id,ctx.channel.category_id)
    
    async def s_in(self,guild,ch,author):
        if not(self.sel_bot(guild.id,ch.category_id)): return
        if guild.id in self.future and self.future[guild.id]:
            if not(guild.id in self.loop) or not(self.loop[guild.id]) or self.loop[guild.id].is_closed():
                self.loop[guild.id]=asyncio.get_event_loop()
            dt=datetime.timedelta(seconds=self.task[guild.id].when()-self.loop[guild.id].time())
            self.future[guild.id].set_result(False)
            self.task[guild.id].cancel()
            self.task[guild.id]=None
            await ch.send(f"Timer stopped: {dt.seconds//60} min {dt.seconds%60} sec left.")
            voice_state=author.voice
            if not((not voice_state) or (not voice_state.channel)):
                flg_self_play=True
                if guild.id in self.flg_call and self.flg_call[guild.id]:
                    cat=guild.get_channel(ch.category_id)
                    if cat!=None:
                        vc_list=cat.voice_channels
                        flg_self_play=False
                        await self.se(guild.id,vc_list,"audio/fin.mp3")
                if flg_self_play:
                    flg_vc=not((not voice_state) or (not voice_state.channel))
                    if not flg_vc:
                        await ch.send("You have to join a voice channnel first.")
                    elif not(guild.id in self.v_cl) or self.v_cl[guild.id]==None or not(self.v_cl[guild.id].is_connected()):
                        self.v_cl[guild.id]=await voice_state.channel.connect()
                    else:
                        if self.v_cl[guild.id].is_playing(): self.v_cl[guild.id].stop()
                        if self.v_cl[guild.id].channel!=voice_state.channel:
                            await self.v_cl[guild.id].move_to(voice_state.channel)
                    self.v_cl[guild.id].play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        else:
            await ch.send("Timer is not running.")

    @commands.command()
    @commands.check(check_priv)
    async def s(self,ctx):
        await self.s_in(ctx.guild,ctx.channel,ctx.author)

    async def t_in(self,guild,ch,author,arg_t,arg_b):
        if not(self.sel_bot(guild.id,ch.category_id,True)): return
        if arg_t==None or not(arg_t.isdecimal()):
            await ch.send('Error: no time input.')
            return
        if not(arg_t.isdecimal()):
            await ch.send('Error: invalid time.')
            return
        if len(arg_t)>=3:
            dt=datetime.timedelta(minutes=int(arg_t[0:-2]),seconds=int(arg_t[-2:]))
        else:
            dt=datetime.timedelta(minutes=int(arg_t))
        self.flg_call[guild.id]=(arg_b in ['Y','Yes','y','yes'])
    #    ch=ctx.channel
    #    cat=ctx.guild.get_channel(ch.category_id)
    #    vc_list=cat.voice_channels
    #    await se(vc_list,se_start)

        voice_state=author.voice
        flg_vc=not((not voice_state) or (not voice_state.channel))
        if not flg_vc:
            await ch.send("You have to join a voice channel first.")
        elif not(guild.id in self.v_cl) or self.v_cl[guild.id]==None or not(self.v_cl[guild.id].is_connected()):
            self.v_cl[guild.id]=await voice_state.channel.connect()
        else:
            if self.v_cl[guild.id].is_playing(): self.v_cl[guild.id].stop()
            if self.v_cl[guild.id].channel!=voice_state.channel:
                await self.v_cl[guild.id].move_to(voice_state.channel)
        if self.v_cl[guild.id]:
            self.v_cl[guild.id].play(discord.FFmpegPCMAudio("audio/start.mp3"))
        await ch.send(f"Timer set: {dt.seconds//60} min {dt.seconds%60} sec.")
        self.loop[guild.id]=asyncio.get_event_loop()
        self.future[guild.id]=self.loop[guild.id].create_future()
        self.task[guild.id]=self.loop[guild.id].call_later(dt.total_seconds(),self.future[guild.id].set_result,True)
        result_future=await self.future[guild.id]
        if result_future:
            await ch.send('Finished!')    
            voice_state=author.voice
            if not((not voice_state) or (not voice_state.channel)):
                flg_self_play=True
                if guild.id in self.flg_call and self.flg_call[guild.id]:
                    cat=guild.get_channel(ch.category_id)
                    if cat!=None:
                        vc_list=cat.voice_channels
                        flg_self_play=False
                        await self.se(guild.id,vc_list,"audio/fin.mp3")
                if flg_self_play:
                    if not(guild.id in self.v_cl) or self.v_cl[guild.id]==None or not(self.v_cl[guild.id].is_connected()):
                        self.v_cl[guild.id]=await voice_state.channel.connect()
                    else:
                        if self.v_cl[guild.id].is_playing(): self.v_cl[guild.id].stop()
                        if self.v_cl[guild.id].channel!=voice_state.channel:
                            await self.v_cl[guild.id].move_to(voice_state.channel)
                    self.v_cl[guild.id].play(discord.FFmpegPCMAudio("audio/fin.mp3"))
        if self.future[guild.id]: self.future[guild.id]=None
        if self.task[guild.id]: self.task[guild.id]=None

    @commands.command()
    @commands.check(check_priv)
    async def t(self,ctx,arg_t=None,arg_b='No'):
        await self.t_in(ctx.guild,ctx.channel,ctx.author,arg_t,arg_b)

loop=asyncio.get_event_loop()
for i in range(N_BOTS):
    bot[i].add_cog(Cog(bot=bot[i],bot_id=i))
    loop.run_until_complete(bot[i].login(token[i]))
    loop.create_task(bot[i].connect())
loop.run_forever()