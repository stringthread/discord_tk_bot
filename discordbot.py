import discord
from discord.ext import commands
import os
import traceback
from typing import ClassVar,Dict,List
import asyncio
import datetime
import re
from random import random
from copy import deepcopy
import textwrap

N_BOTS=int(os.environ['N_BOTS'])
bot = [commands.Bot(command_prefix='!') for i in range(N_BOTS)]
token = [os.environ['DISCORD_BOT_TOKEN_'+str(i)] for i in range(1,N_BOTS+1)]
loop=asyncio.get_event_loop()

async def check_priv(ctx):
  return check_priv_user(ctx.author)

def check_priv_user(user):
  for i in user.roles:
    if i.name=='JUDGE': return True
  return False

class Cog(commands.Cog):
  cat2bot: ClassVar[Dict[int,Dict[int,int]]]={} #Guild_id->[Category_id->Bot id]
  bot2cat: ClassVar[Dict[int,Dict[int,int]]]={} #Guild_id->[Bot_id->Category_id] (Can use for checking if bot is used)
  prefix_ui_everyone: str=' (Everyone)'
  prefix_ui: str='>Discord TK Bot UI:'
  prefix_ui_flex: str=prefix_ui+' Flex'
  prefix_s: str='Timer stopped:'
  emoji_point_five: ClassVar[Dict[int,str]]={}
  emoji_syn={
    'one':'one',
    '1️⃣':'one',
    'two':'two',
    '2️⃣':'two',
    'three':'three',
    '3️⃣':'three',
    'four':'four',
    '4️⃣':'four',
    'six':'six',
    '6️⃣':'six',
    'loudspeaker':'loudspeaker',
    '📢':'loudspeaker',
    'regional_indicator_a':'regional_indicator_a',
    b'\xf0\x9f\x87\xa6'.decode():'regional_indicator_a',
    'regional_indicator_n':'regional_indicator_n',
    b'\xf0\x9f\x87\xb3'.decode():'regional_indicator_n',
    'pause_button':'pause_button',
    'double_vertical_bar':'pause_button',
    b'\xe2\x8f\xb8\xef\xb8\x8f'.decode():'pause_button',
    'play':'play',
    'arrow_forward':'play',
    '▶️':'play',
    'reset':'reset',
    'arrows_counterclockwise':'reset',
    '🔄':'reset',
    'check':'check',
    'white_check_mark':'check',
    '✅':'check',
    'leave':'leave',
    'wave':'leave',
    '👋':'leave',
    'point_five':'point_five'
  }
  emoji_list_c=['1️⃣','2️⃣','3️⃣','4️⃣','6️⃣',
    b'\xe2\x8f\xb8\xef\xb8\x8f'.decode(),
    '📢',
    '✅',
    b'\xf0\x9f\x87\xa6'.decode(),
    b'\xf0\x9f\x87\xb3'.decode(),
    '🔄',
    '👋'
  ]
  emoji_list_d=['1️⃣','2️⃣','3️⃣','4️⃣','6️⃣',
    b'\xe2\x8f\xb8\xef\xb8\x8f'.decode(),
    '📢',
    '✅',
    b'\xf0\x9f\x87\xa6'.decode(),
    b'\xf0\x9f\x87\xb3'.decode(),
    '👋'
  ]
  timer_def_c={'Aff':'8','Neg':'8'}
  timer_name_syn={'A':'Aff','a':'Aff','aff':'Aff','N':'Neg','n':'Neg','neg':'Neg'}
  def __init__(self,bot,bot_id):
    self.bot: commands.Bot=bot
    self.bot_id: int=bot_id
    self.fut_connect: Dict[int,asyncio.Future]={}
    self.v_cl: Dict[int,discord.VoiceClient]={}
    self.task: Dict[int,asyncio.Task]={}
    self.future: Dict[int,asyncio.Future]={}
    self.task_msg: Dict[int,asyncio.Task]={}
    self.future_msg: Dict[int,asyncio.Future]={}
    self.flg_call: Dict[int,bool]={}
    self.timer_def=deepcopy(Cog.timer_def_c)
    self.left_time: Dict[int,Dict[int,Dict[str,str]]]={}#g_id->[cat_id->[name->time]]
    self.timer_name: Dict[int,Dict[int,str]]={}#g_id->[cat_id->name(currently running)]
    self.emoji_func_jda={
      'point_five': lambda g,c,u:self.t_in(g,c,u,'030'),
      'one': lambda g,c,u:self.t_in(g,c,u,'1'),
      'two': lambda g,c,u:self.t_in(g,c,u,'2'),
      'three': lambda g,c,u:self.t_in(g,c,u,'3'),
      'four': lambda g,c,u:self.t_in(g,c,u,'4'),
      'six': lambda g,c,u:self.t_in(g,c,u,'6'),
      'regional_indicator_a': lambda g,c,u:self.t_in(g,c,u,'Aff'),
      'regional_indicator_n': lambda g,c,u:self.t_in(g,c,u,'Neg'),
      'loudspeaker': lambda g,c,u:self.t_in(g,c,u,'0','Y',flg_loudspeaker=True),
      'pause_button': lambda g,c,u:self.s_in(g,c,u),
      'reset': lambda g,c,u:self.r_in(g.id,c),
      'check': lambda g,c,u:self.time_msg(g.id,c),
      'leave': lambda g,c,u:self.l_in(g.id,c.category_id)
    }
    self.emoji_func_dk={
      'point_five': lambda g,c,u:self.t_in(g,c,u,'030'),
      'one': lambda g,c,u:self.t_in(g,c,u,'1'),
      'two': lambda g,c,u:self.t_in(g,c,u,'2'),
      'three': lambda g,c,u:self.t_in(g,c,u,'3'),
      'four': lambda g,c,u:self.t_in(g,c,u,'4'),
      'six': lambda g,c,u:self.t_in(g,c,u,'6'),
      'regional_indicator_a': lambda g,c,u:self.e_in(g,c.category_id,'aff'),
      'regional_indicator_n': lambda g,c,u:self.e_in(g,c.category_id,'neg'),
      'loudspeaker': lambda g,c,u:self.t_in(g,c,u,'0','Y',flg_loudspeaker=True),
      'pause_button': lambda g,c,u:self.s_in(g,c,u),
      'reset': lambda g,c,u:self.r_in(g.id,c),
      'check': lambda g,c,u:self.time_msg(g.id,c),
      'leave': lambda g,c,u:self.l_in(g.id,c.category_id)
    }

  @staticmethod
  async def send(sendable,content,flg_del=True):
    if not(getattr(sendable,'send',False)): return
    msg=await sendable.send(content)
    if flg_del:
      loop.create_task(msg.delete(delay=15*60))
    return msg

  async def move_ch(self,guild_id,ch):
    if guild_id in self.fut_connect and not(self.fut_connect[guild_id].done()): await self.fut_connect[guild_id]
    if not(guild_id in self.v_cl) or self.v_cl[guild_id]==None or not(self.v_cl[guild_id].is_connected()):
      for v_cl in self.bot.voice_clients:
        if v_cl.guild.id==guild_id and v_cl.is_connected():
          self.v_cl[guild_id]=v_cl
          break
    if not(guild_id in self.v_cl) or self.v_cl[guild_id]==None or not(self.v_cl[guild_id].is_connected()):
      self.fut_connect[guild_id]=loop.create_future()
      self.v_cl[guild_id]=await ch.connect()
      if guild_id in self.fut_connect and self.fut_connect[guild_id]: self.fut_connect[guild_id].set_result(True)
    else:
      if self.v_cl[guild_id].is_playing(): self.v_cl[guild_id].stop()
      if self.v_cl[guild_id].channel!=ch:
        self.fut_connect[guild_id]=loop.create_future()
        #print('call: move from '+self.v_cl[guild_id].channel.name+' to '+ch.name)
        await self.v_cl[guild_id].disconnect()
        self.v_cl[guild_id]=await ch.connect()
        if guild_id in self.fut_connect and self.fut_connect[guild_id]: self.fut_connect[guild_id].set_result(True)

  async def call(self,guild_id,ch,src):
    await self.move_ch(guild_id,ch)
    future=loop.create_future()
    self.v_cl[guild_id].play(discord.FFmpegPCMAudio(src),after=lambda err:loop.call_soon_threadsafe(future.set_result,0))
    #print('call: connecting to '+self.v_cl[guild_id].channel.name)
    await future

  async def se(self,guild_id,vc_list,src):
    ch_before=None
    if guild_id in self.v_cl and self.v_cl[guild_id]!=None: ch_before=self.v_cl[guild_id].channel
    for ch in vc_list:
      #print('se: '+ch.name)
      await self.call(guild_id,ch,src)
    if ch_before!=None:
      await self.move_ch(guild_id,ch_before)

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
  async def on_ready(self):
    for guild in self.bot.guilds:
      if guild.id in Cog.emoji_point_five: return
      emoji_id=discord.utils.get(guild.emojis, name='point_five')
      if emoji_id:Cog.emoji_point_five[guild.id]=emoji_id
  @commands.Cog.listener()
  async def on_guild_emojis_update(self,guild,before,after):
    emoji_id=discord.utils.get(guild.emojis, name='point_five')
    if emoji_id and not(guild.id in Cog.emoji_point_five):Cog.emoji_point_five[guild.id]=emoji_id
    elif not(emoji_id) and guild.id in Cog.emoji_point_five: del Cog.emoji_point_five[guild.id]
  @commands.Cog.listener()
  async def on_guild_available(self,guild):
    if guild.id in Cog.emoji_point_five: return
    emoji_id=discord.utils.get(guild.emojis, name='point_five')
    if emoji_id:Cog.emoji_point_five[guild.id]=emoji_id
  @commands.Cog.listener()
  async def on_guild_unavailable(self,guild):
    if guild.id in Cog.emoji_point_five: del Cog.emoji_point_five[guild.id]

  @commands.Cog.listener()
  async def on_voice_state_update(self,member,before,after):
    if not(before.channel): return
    if not(self.sel_bot(before.channel.guild.id,before.channel.category_id)): return
    if member.id==self.bot.user.id: return
    if after.channel and after.channel.category_id==before.channel.category_id: return
    cat=self.bot.get_channel(before.channel.category_id)
    if not(isinstance(cat,discord.CategoryChannel)): return
    flg=True
    for ch in cat.voice_channels:
      if len(ch.members)>=2: flg=False;break
      if len(ch.members)==1 and ch.members[0].id!=self.bot.user.id: flg=False;break
    if flg: await self.l_in(before.channel.guild.id,before.channel.category_id)

  @commands.Cog.listener()
  async def on_reaction_add(self,reaction,user):
    try:
      if not(self.sel_bot(reaction.message.guild.id,reaction.message.channel.category_id)): return
      prefix=reaction.message.content.splitlines()[0]
      if (not(prefix.endswith(Cog.prefix_ui_everyone)) and not(check_priv_user(user))) or user.bot: return
      if prefix.startswith(Cog.prefix_ui_everyone): re.sub(Cog.prefix_ui_everyone+'$','',prefix)#prefix.replace(Cog.prefix_ui_everyone,'',1)
      if prefix.startswith(Cog.prefix_ui_flex):
        e_name=re.match(r':?([^:]+):?',reaction.emoji if isinstance(reaction.emoji,str) else reaction.emoji.name).group(1)
        if not(e_name in Cog.emoji_syn and self.emoji_func_jda[Cog.emoji_syn[e_name]]):
          #await Cog.send(reaction.message.channel,e_name)
          return
        #await Cog.send(reaction.message.channel,Cog.emoji_syn[e_name])
        await reaction.remove(user)
        await self.emoji_func_jda[Cog.emoji_syn[e_name]](reaction.message.guild,reaction.message.channel,user)
      elif prefix.startswith(Cog.prefix_ui):
        e_name=re.match(r'^:?([^:]+):?$',reaction.emoji if isinstance(reaction.emoji,str) else reaction.emoji.name).group(1)
        if not(e_name in Cog.emoji_syn and self.emoji_func_dk[Cog.emoji_syn[e_name]]):
          #await Cog.send(reaction.message.channel,e_name.encode())
          return
        #await Cog.send(reaction.message.channel,Cog.emoji_syn[e_name])
        await reaction.remove(user)
        await self.emoji_func_dk[Cog.emoji_syn[e_name]](reaction.message.guild,reaction.message.channel,user)
      elif prefix.startswith(Cog.prefix_s):
        e_name=re.match(r'^:?([^:]+):?$',reaction.emoji if isinstance(reaction.emoji,str) else reaction.emoji.name).group(1)
        if e_name in Cog.emoji_syn and Cog.emoji_syn[e_name]=='play':
          match=re.search(r'(?m:^(?:__\*\*([^/d ]+)\*\*__ ?: ?)?(\d+) ?min ?(\d+) ?sec)',reaction.message.content)
          if match==None: return
          n=match.group(1)
          m=int(match.group(2))
          s=int(match.group(3))
          if n in Cog.timer_name_syn: n=Cog.timer_name_syn[n]
          await reaction.remove(user)
          await self.t_in(reaction.message.guild,reaction.message.channel,user,n if n else f'{m}{s:02}')
    except discord.Forbidden:
      await Cog.send(reaction.message.channel,"Error: the Bot does not have the manage_messages permission.")
    except Exception as error:
      orig_error = getattr(error, "original", error)
      error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
      #await Cog.send(reaction.message.channel,error_msg)
      await Cog.send(reaction.message.channel,f"{datetime.datetime.now()}: Error occured. Please check system logs and contact the developer.")
      print(error_msg)

  @commands.Cog.listener()
  async def on_command_error(self,ctx, error):
    if isinstance(error,commands.CheckFailure):
      if self.sel_bot(ctx.guild.id,ctx.channel.category_id,True): await Cog.send(ctx,f"{ctx.author.name}: You don't have permission to use this bot.")
      return
    if isinstance(error,commands.CommandNotFound):
      return
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    #await Cog.send(ctx,error_msg)
    await Cog.send(ctx,f"{datetime.datetime.now()}: Error occured. Please check system logs and contact the developer.")
    print(error_msg)

  @commands.command()
  @commands.check(check_priv)
  async def an(self,ctx,n1,n2=''):
    if not(self.sel_bot(ctx.guild.id,ctx.channel.category_id,True)): return
    if not n1:
      await Cog.send(ctx,'Error: no name input')
      return
    if random()<0.5: n1,n2=n2,n1
    msg=''
    if n1: msg+=f'Aff：{n1}'
    if n2:
      if msg: msg+='\n'
      msg+=f'Neg：{n2}'
    await Cog.send(ctx,msg,False)

  async def c_in(self,ctx,pre=''):
    if not(self.sel_bot(ctx.guild.id,ctx.channel.category_id,True)): return
    content=(Cog.prefix_ui_flex+pre+textwrap.dedent(f'''
    {Cog.emoji_point_five[ctx.guild.id] if ctx.guild.id in Cog.emoji_point_five else ':one:'}～:six:：タイマー開始
    :pause_button:：タイマー停止
    :white_check_mark:：残り時間チェック''')
    #:loudspeaker:：準備室の呼び出し
    +textwrap.dedent('''
    :regional_indicator_a::regional_indicator_n:：準備時間タイマー開始
    :arrows_counterclockwise:：準備時間タイマーリセット
    :wave:：Botの退出
    '''))
    msg=await Cog.send(ctx,content,False)
    if ctx.guild.id in Cog.emoji_point_five :await msg.add_reaction(Cog.emoji_point_five[ctx.guild.id])
    for i in Cog.emoji_list_c:
      await msg.add_reaction(i)

  @commands.command()
  @commands.check(check_priv)
  async def c(self,ctx):
    await self.c_in(ctx)
    
  @commands.command()
  async def pc(self,ctx):
    await self.c_in(ctx,Cog.prefix_ui_everyone)

  async def d_in(self,ctx,pre=''):
    if not(self.sel_bot(ctx.guild.id,ctx.channel.category_id,True)): return
    content=Cog.prefix_ui+pre+textwrap.dedent(f'''
    {Cog.emoji_point_five[ctx.guild.id] if ctx.guild.id in Cog.emoji_point_five else ':one:'}～:six:：タイマー開始
    :pause_button:：タイマー停止
    :white_check_mark:：残り時間チェック
    :wave:：Botの退出
    ''')
    #:loudspeaker:：準備室の呼び出し
    #:regional_indicator_a: :regional_indicator_n:：資料請求呼び出し
    #''')
    msg=await Cog.send(ctx,content,False)
    if ctx.guild.id in Cog.emoji_point_five :await msg.add_reaction(Cog.emoji_point_five[ctx.guild.id])
    for i in Cog.emoji_list_d:
      await msg.add_reaction(i)

  @commands.command()
  @commands.check(check_priv)
  async def d(self,ctx):
    await self.d_in(ctx)

  @commands.command()
  async def p(self,ctx):
    await self.d_in(ctx,Cog.prefix_ui_everyone)

  async def l_in(self,guild_id,cat_id):
    if not(self.sel_bot(guild_id,cat_id)): return
    if not(guild_id in self.v_cl) or self.v_cl[guild_id]==None or not(self.v_cl[guild_id].is_connected()):
      for v_cl in self.bot.voice_clients:
        if v_cl.guild.id==guild_id and v_cl.is_connected():
          self.v_cl[guild_id]=v_cl
          break
    if guild_id in self.v_cl and self.v_cl[guild_id]:
      await self.v_cl[guild_id].disconnect()
      del self.v_cl[guild_id]
    if guild_id in self.task and isinstance(self.task[guild_id],asyncio.TimerHandle):
      self.task[guild_id].cancel()
      del self.task[guild_id]
    if guild_id in self.future:
      if isinstance(self.future[guild_id],asyncio.Future) and not(self.future[guild_id].done()): self.future[guild_id].set_result(True)
      del self.future[guild_id]
    if guild_id in self.task_msg and isinstance(self.task_msg[guild_id],asyncio.TimerHandle):
      self.task_msg[guild_id].cancel()
      del self.task_msg[guild_id]
    if guild_id in self.future_msg:
      if isinstance(self.future_msg[guild_id],asyncio.Future) and not(self.future_msg[guild_id].done()): self.future_msg[guild_id].set_result(True)
      del self.future_msg[guild_id]
    if guild_id in self.flg_call: del self.flg_call[guild_id]
    self.timer_def=Cog.timer_def_c
    if cat_id in self.left_time.get(guild_id,{}): del self.left_time[guild_id][cat_id]
    if cat_id in self.timer_name.get(guild_id,{}): del self.timer_name[guild_id][cat_id]
    del Cog.cat2bot[guild_id][Cog.bot2cat[guild_id][self.bot_id]]
    del Cog.bot2cat[guild_id][self.bot_id]

  @commands.command()
  @commands.check(check_priv)
  async def l(self,ctx):
    await self.l_in(ctx.guild.id,ctx.channel.category_id)
  
  async def r_in(self,guild_id,ch,arg_n='',arg_t=''):
    if not(self.sel_bot(guild_id,ch.category_id,True)): return
    if not(arg_n):
      if guild_id in self.left_time: self.left_time[guild_id][ch.category_id]=deepcopy(self.timer_def)
      else: self.left_time[guild_id]={ch.category_id:deepcopy(self.timer_def)}
    else:
      if arg_n in Cog.timer_name_syn: arg_n=Cog.timer_name_syn[arg_n]
      if re.fullmatch(r'\d+',arg_n):
        await Cog.send(ch,'Error: timer name cannot be number.')
        return
      if arg_n and arg_t:
        if not(re.fullmatch(r'\d+',arg_t)):
          await Cog.send(ch,'Error: invalid time input.')
          return
        self.timer_def[arg_n]=arg_t
      elif not(arg_n in self.timer_def):
        await Cog.send(ch,'Error: timer name not found.')
        return
      if not(guild_id in self.left_time): self.left_time[guild_id]={ch.category_id:deepcopy(self.timer_def)}
      elif not(ch.category_id in self.left_time[guild_id]): self.left_time[guild_id][ch.category_id]=deepcopy(self.timer_def)
      else: self.left_time[guild_id][ch.category_id][arg_n]=self.timer_def[arg_n]
    
  @commands.command()
  @commands.check(check_priv)
  async def r(self,ctx,arg_n='',arg_t=''):
    await self.r_in(ctx.guild.id,ctx.channel,arg_n,arg_t)

  async def e_in(self,guild,cat_id,arg):
    if not(self.sel_bot(guild.id,cat_id,True)): return
    cat=self.bot.get_channel(cat_id)
    vc_list=getattr(cat,'voice_channels',None)
    if not(vc_list): return
    for ch in cat.voice_channels:
      if arg in ch.name:
        await self.se(guild.id,filter(lambda ch: arg in ch.name,cat.voice_channels),"audio/evi.wav")

  @commands.command()
  @commands.check(check_priv)
  async def e(self,ctx,arg):
    await self.e_in(ctx.guild,ctx.channel.category_id,arg)

  async def s_in(self,guild,ch,author):
    if not(self.sel_bot(guild.id,ch.category_id)): return
    if guild.id in self.future and self.future[guild.id]:
      dt=datetime.timedelta(seconds=self.task[guild.id].when()-loop.time())
      name=''
      if ch.category_id in self.timer_name.get(guild.id,{}):
        name=self.timer_name[guild.id][ch.category_id]
        if not(ch.category_id in self.left_time.get(guild.id,{}) and name in self.left_time[guild.id].get(ch.category_id,{})): name=''
        else:
          self.left_time[guild.id][ch.category_id][name]=f'{dt.seconds//60}{dt.seconds%60:02}'
        del self.timer_name[guild.id][ch.category_id]
        if name: name=f'__**{name}**__ : '
      self.future[guild.id].set_result(False)
      self.task[guild.id].cancel()
      self.task[guild.id]=None
      #self.future_msg[guild.id].set_result(False)
      #self.future_msg[guild.id]=None
      #self.task_msg[guild.id].cancel()
      #self.task_msg[guild.id]=None
      msg=await Cog.send(ch,Cog.prefix_s+f"\n{name}{dt.seconds//60} min {dt.seconds%60} sec left.")
      await msg.add_reaction('▶️')
      voice_state=author.voice
      if not((not voice_state) or (not voice_state.channel)):
        flg_self_play=True
        if guild.id in self.flg_call and self.flg_call[guild.id]:
          cat=guild.get_channel(ch.category_id)
          if cat!=None:
            vc_list=cat.voice_channels
            flg_self_play=False
            await self.se(guild.id,vc_list,"audio/fin.wav")
        if flg_self_play:
          await self.call(guild.id,voice_state.channel,"audio/fin.wav")
    else:
      await Cog.send(ch,"Timer is not running.")

  @commands.command()
  @commands.check(check_priv)
  async def s(self,ctx):
    await self.s_in(ctx.guild,ctx.channel,ctx.author)

  async def time_msg(self,guild_id,ch):
    if not(self.sel_bot(guild_id,ch.category_id)): return
    if not(guild_id in self.task and self.task[guild_id]):
      await Cog.send(ch,"Timer is not running.")
      return
    dt=datetime.timedelta(seconds=self.task[guild_id].when()-loop.time())
    name=''
    if ch.category_id in self.timer_name.get(guild_id,{}): name=f'\n__**{self.timer_name[guild_id][ch.category_id]}**__ : '
    await Cog.send(ch,f"Timer Running: {name}{(dt.seconds+1)//60} min {(dt.seconds+1)%60:02} sec left.")

  async def t_in(self,guild,ch,author,arg_t,arg_b='No',flg_loudspeaker=False):
    if not(self.sel_bot(guild.id,ch.category_id,True)): return
    if arg_t==None:
      await Cog.send(ch,'Error: no time input.')
      return
    if not(arg_t.isdecimal()):
      if not(guild.id in self.left_time): self.left_time[guild.id]={ch.category_id:deepcopy(self.timer_def)}
      elif not ch.category_id in self.left_time[guild.id]: self.left_time[guild.id][ch.category_id]=deepcopy(self.timer_def)
      if arg_t in Cog.timer_name_syn:
        arg_t=Cog.timer_name_syn[arg_t]
      if arg_t in self.left_time[guild.id][ch.category_id]:
        if not(guild.id in self.timer_name): self.timer_name[guild.id]={ch.category_id:arg_t}
        else: self.timer_name[guild.id][ch.category_id]=arg_t
        arg_t=self.left_time[guild.id][ch.category_id][arg_t]
    if not(arg_t.isdecimal()):
      await Cog.send(ch,'Error: invalid time.')
      return
    if len(arg_t)>=3:
      dt=datetime.timedelta(minutes=int(arg_t[0:-2]),seconds=int(arg_t[-2:]))
    else:
      dt=datetime.timedelta(minutes=int(arg_t))
    self.flg_call[guild.id]=(arg_b in ['Y','Yes','y','yes'])
  #  ch=ctx.channel
  #  cat=ctx.guild.get_channel(ch.category_id)
  #  vc_list=cat.voice_channels
  #  await se(vc_list,se_start)

    voice_state=author.voice
    flg_vc=not((not voice_state) or (not voice_state.channel))
    if not flg_vc:
      await Cog.send(ch,"You have to join a voice channel first.")
    if not(flg_loudspeaker):
      if flg_vc:
        await self.call(guild.id,voice_state.channel, "audio/start.wav")
      await Cog.send(ch,f"Timer set: {dt.seconds//60} min {dt.seconds%60} sec.")
      self.future[guild.id]=loop.create_future()
      self.task[guild.id]=loop.call_later(dt.total_seconds(),self.future[guild.id].set_result,True)
      #await self.time_msg(guild.id,ch)
      result_future=await self.future[guild.id]
      if not(guild.id in self.future) or not(self.future[guild.id]): return
    if not(flg_loudspeaker):
      if self.future[guild.id]: self.future[guild.id]=None
      if self.task[guild.id]: self.task[guild.id]=None
    if flg_loudspeaker or result_future:
      if not(flg_loudspeaker):
        name=''
        if ch.category_id in self.timer_name.get(guild.id,{}):
          name=self.timer_name[guild.id][ch.category_id]
          if not(ch.category_id in self.left_time.get(guild.id,{}) and name in self.left_time[guild.id].get(ch.category_id,{})): name=''
          else:
            self.left_time[guild.id][ch.category_id][name]='0'
          del self.timer_name[guild.id][ch.category_id]
          if name: name=f'__**{name}**__ : '
        await Cog.send(ch,f'{name}Finished!')  
      voice_state=author.voice
      if not((not voice_state) or (not voice_state.channel)):
        flg_self_play=True
        if guild.id in self.flg_call and self.flg_call[guild.id]:
          cat=guild.get_channel(ch.category_id)
          if cat!=None:
            vc_list=cat.voice_channels
            if flg_loudspeaker: vc_list=list(filter(lambda vc:vc!=voice_state.channel,vc_list))
            flg_self_play=False
            await self.se(guild.id,vc_list,"audio/fin.wav")
        if flg_self_play:
          await self.call(guild.id,voice_state.channel,"audio/fin.wav")

  @commands.command()
  @commands.check(check_priv)
  async def t(self,ctx,arg_t=None,arg_b='No'):
    await self.t_in(ctx.guild,ctx.channel,ctx.author,arg_t,arg_b)

for i in range(N_BOTS):
  bot[i].add_cog(Cog(bot=bot[i],bot_id=i))
  loop.run_until_complete(bot[i].login(token[i]))
  loop.create_task(bot[i].connect())
loop.run_forever()