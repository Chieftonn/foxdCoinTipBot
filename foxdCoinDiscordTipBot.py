#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import subprocess
from typing import Any
import time as time_util
from datetime import datetime
import logging
import discord
from discord.ext import commands
from pytz import timezone

''' begin configuration section '''

TOKEN    = '____CHANGEME____'
BOTNAME  = '____CHANGEME____'
BOTUUID  = '____CHANGEME____'
BOTCHID  = '____CHANGEME____'
CLI_EXE  = '____CHANGEME____'
RPC_USER = '____CHANGEME____'
RPC_PASS = '____CHANGEME____'
LOG_FILE = '____CHANGEME____'

''' end configuration section '''


''' DO NOT EDIT BELLOW THS LINE '''

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)
ft = logging.Formatter('%(asctime)-15s - %(message)s')
fh.setFormatter(ft)

logger = logging.getLogger(BOTNAME)
logger.setLevel(logging.INFO)
logger.addHandler(fh)

bot = commands.Bot(command_prefix='!') 
bot.remove_command('help')


@bot.command(pass_context=True)
async def help():
    n="The following commands are at your disposal:"
    v="!info, !balance, !deposit, !withdraw, !tip, !rain, !price, and !time"
    msg = discord.Embed(color=0x00b3b3)
    msg.add_field(name=n, value=v, inline=False)
    await bot.say(embed=msg)


@bot.command(pass_context=True)
async def info(ctx):
    msg = \
    """
      ```
                  INFO SECTION
      ```
      commands like *!tip* & *!withdraw* have a specfic format,\
    use them like so:
     
     Tipping format: 
       `!tip @[user] [amount]        (without brackets)`
       
     Rain format: 
       `!rain [amount]               (without brackets)`
          
     Withdrawing format: 
       `!withdraw [address] [amount] (without brackets)`


        WHERE:
            `[address] = withdraw #$FOXD address`
            `[user] = discord username`
            `[amount] = amount of #$FOXD to utilise`

     *NOTE*:
      - don't deposit a significant amount of #$FOXD through this #BOT
      - make sure that you enter a valid #$FOXD address when you perform a withdraw
      - we are not responsible of your funds if something bad happen to this #BOT 
     ```
          USE THIS #BOT AT YOUR OWN RISK
     ```
    """
    embed = discord.Embed(color=0x00b3b3)
    embed.add_field(name="\a", value=msg, inline=False)
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def balance(ctx):
    user_name = ctx.message.author.name
    user_uuid = ctx.message.author.id
    if user_name is None:
        msg = "Invalid username!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if user_uuid is None:
        msg = "Invalid userid!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    ret = rpc_call('getbalance', [str(user_uuid)])
    if ret is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    balance = float(ret)
    balance = str('{:,.8f}'.format(balance))
    msg = f'@{user_name} your current balance is: {balance} $FOXD'
    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name="BALANCE", value=msg, inline=True)
    await bot.send_message(ctx.message.author, embed=embed)


@bot.command(pass_context=True)
async def deposit(ctx):
    user_name = ctx.message.author.name
    user_uuid = ctx.message.author.id
    if user_name is None:
        msg = "Invalid username!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if user_uuid is None:
        msg = "Invalid userid!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    ret = rpc_call('getaccountaddress', str(user_uuid))
    if ret is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    msg = f'@{user_name} your depositing address is: `{ret}`'
    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name="DEPOSIT", value=msg, inline=True)
    await bot.send_message(ctx.message.author, embed=embed)


@bot.command(pass_context=True)
async def tip(ctx):
    user_name = ctx.message.author.name
    user_uuid = ctx.message.author.id
    if user_name is None:
        msg = "Invalid username!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if user_uuid is None:
        msg = "Invalid userid!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    message = ctx.message.content.split(' ')
    if len(message) != 3:
        msg = "Please use !tip <username> <amount>!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if not isValidUsername(message[1]):
        msg = "Please input a valid username (ex: @JonDoe01#0964)!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if not isValidAmount(message[2]):
        msg = "Please input a valid amount (ex: 1000)!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    amount = float(message[2])
    target = message[1]
    uuid = list(filter(str.isdigit, target))
    target_uuid = str(''.join(uuid))
    if amount > 100000 or amount < 1:
        msg = "Please send value between 1 and 100,000 $FOXD!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if target_uuid == user_uuid:
        msg = "You can't tip yourself!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if target_uuid == BOTUUID:
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value="HODL.", inline=True)
        await bot.say(embed=embed)
        return False
    if not target_uuid:
        msg = f'@{target} has no activity in this chat!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    ret = await rpc_call('getbalance', [str(user_uuid)])
    if ret is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    balance = float(ret)
    if balance < amount:
        msg = f'@{user_name} you have insufficent funds.'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    tx = rpc_call('move', [str(user_uuid), str(target_uuid), str(amount)])
    if tx is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    msg = f'@{user_name} tipped {target} of {amount} $FOXD'
    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name="TIP", value=msg, inline=True)
    await bot.say(embed=embed)

    
@bot.command(pass_context=True)
async def rain(ctx):
    user_name = ctx.message.author.name
    user_uuid = ctx.message.author.id
    if user_name is None:
        msg = "Invalid username!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if user_uuid is None:
        msg = "Invalid userid!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    message = ctx.message.content.split(' ')
    if len(message) != 2:
        msg = "Please use !rain <amount>!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if not isValidAmount(message[1]):
        msg = "Please input a valid amount (ex: 1000)!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    amount = float(message[1])
    if amount > 100000 or amount < 1:
        msg = "Please send value between 1 and 100,000 $FOXD!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    ret = await rpc_call('getbalance', [str(user_uuid)])
    if ret is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    balance = float(ret)
    if balance < amount:
        msg = f'@{user_name} you have insufficent funds.'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    users_online = {}
    for server in bot.servers:
        for u in server.members:
            if str(u.status) is 'online': users_online[u.id] = u.name
    online  = len(users_online)
    pamount = str(float(amount/online))
    for key in sorted(users_online):
        time_util.sleep(0.1)
        target_uuid = key
        target_name = users_online[target_uuid]
        tx = await rpc_call('move', [str(user_uuid), str(target_uuid), str(pamount)])
        if tx is None:
            msg = f"failed to #tip @{target_name}!"
            embed = discord.Embed(color=discord.Color.red())
            embed.add_field(name="ERROR", value=msg, inline=True)
            await bot.say(embed=embed)
            return False
    sub_list = list(users_online.values())
    user_list = ",".join(sub_list[0:2])
    other_list = online - 50
    _msg = f"{user_name} invoked rain spell with {pamount} $FOXD over #{online}"
    if online > 50: msg = f"{_msg} 50 users ({user_list}) and {other_list} other people"
    else: msg = f"{_msg} users ({user_list})"
    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name="RAIN", value=msg, inline=True)
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def withdraw(ctx):
    user_name = ctx.message.author.name
    user_uuid = ctx.message.author.id
    if user_name is None:
        msg = "Invalid username!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if user_uuid is None:
        msg = "Invalid userid!"
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    message = ctx.message.content.split(' ')
    if len(message) != 3:
        msg = 'Please use !withdraw <address> <amount>!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    is_valid = await rpc_call('validateaddress', [message[1]])['isvalid']
    if not is_valid:
        msg = 'Please input a valid $FOXD address!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    if not isValidAmount(message[2]):
        msg = 'Please input a valid amount (ex: 1000)!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    amount = float(message[2])
    address = message[1]
    ret = await rpc_call('getbalance', [str(user_uuid)])
    if ret is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    balance = float(ret)
    if balance < amount+1:
        msg = f'@{user_name} you have insufficent funds.'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    tx = await rpc_call('sendfrom', (str(user_uuid), str(address), str(amount)))
    if tx is None:
        msg = 'rpc internal error!'
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="ERROR", value=msg, inline=True)
        await bot.say(embed=embed)
        return False
    msg = f'@{user_name} has successfully withdrew {amount} $FOXD to address: {address}'
    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name="WITHDRAW", value=msg, inline=True)
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def time(ctx):
    msg = datetime.utcnow().strftime("%a %b %d %H:%M:%S %Y") + " UTC\n"
    msg += datetime.now(timezone('EST')).strftime("%a %b %d %H:%M:%S %Y %Z")
    embed = discord.Embed(color=0x00b3b3)
    embed.add_field(name="TIME", value=msg, inline=True)
    await bot.say(embed=embed)


@bot.event
async def on_ready(): print('Bot is ready for use!')


@bot.event
async def on_message(message, user: discord.Member = None):
    if message is None: return
    if user is None: user = message.author
    msg  = message.content
    uuid = user.id
    user = user.name
    logger.info(f"@{user} [#{uuid}]: {msg}")
    cuid = str(message.channel.id)
    if cuid != BOTCHID and message.content.startswith('!'):
        logger.info(f"wrong #BOTCHID [@{BOTCHID}]")
        await bot.delete_message(message)
    else: await bot.process_commands(message)


async def rpc_call(method: str, params: list[Any]) -> dict[str, Any] | None:
    try: result = subprocess.run((
        lambda m, p: [CLI_EXE,
            f'-rpcuser={RPC_USER}',
            f'-rpcpassword={RPC_PASS}',
            m, *p])(method, params),
            stdout = subprocess.PIPE)
    except: return
    ret = result.stdout.strip().decode('utf-8')
    if len(ret) == 0: return
    else: return json.loads(ret)


def isValidUsername(user): 
    if re.match('^<@\!?[0-9]+>$', user): return True
    else: return False


def isValidAmount(amount): 
    try: 
        if type(amount) is not float: raise ValueError
        else: return True
    except ValueError: return False


def main(): bot.run(TOKEN)


if __name__ == '__main__':
    main()