from discord.ext import commands
import os
import traceback
import asyncio

bot = commands.Bot(command_prefix='!')
token = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def t(ctx,arg):
    if not(arg.isdecimal()):
        await ctx.send('Error: invalid time.')
        return
    sec=int(arg)
    if sec>=100:
        sec=sec//100*60+sec%100
    else:
        sec*=60
    await asyncio.sleep(sec)
    await ctx.send('Finished!')


bot.run(token)
