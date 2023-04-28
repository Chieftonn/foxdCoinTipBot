#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import subprocess
import logging
from typing import Any
import pickledb
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

''' begin configuration section '''

BOTNAME  = '____CHANGEME____'
TOKEN    = '____CHANGEME____'
LOG_FILE = '____CHANGEME____'
DB_FILE  = '____CHANGEME____'
CLI_EXE  = '____CHANGEME____'
RPC_USER = '____CHANGEME____'
RPC_PASS = '____CHANGEME____'

''' end configuration section '''



''' DO NOT EDIT BELLOW THS LINE '''

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)
ft = logging.Formatter('%(asctime)-15s - %(message)s')
fh.setFormatter(ft)
logger = logging.getLogger(BOTNAME)
logger.setLevel(logging.INFO)
logger.addHandler(fh)
db = pickledb.load(DB_FILE, True)

def main():
    updater = Updater(TOKEN, workers=10)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('balance', balance))
    dp.add_handler(CommandHandler('withdraw', withdraw))
    dp.add_handler(CommandHandler('deposit', deposit))
    dp.add_handler(CommandHandler('tip', tip))
    dp.add_handler(MessageHandler(Filters.all, events))
    updater.start_polling()
    updater.idle()


def getUserID(bot, update, username):
    cid = update.message.chat_id
    value = None
    users = db.getall()
    for uid in users:
        user = db.get(uid)
        if user != username: continue
        user_data = bot.getChatMember(cid, uid)
        user_name = user_data.user.username
        db.set(str(uid), user_name)
        if username == user_name:
            value = uid
    return value


def events(bot, update):
    from_user = update.message.from_user
    user_name = from_user.username
    user_uuid = from_user.id
    db.set(str(user_uuid), user_name)
    return True


def receive_message(message):
    msg  = message.text
    user = message.from_user.username
    uuid = message.from_user.id
    logger.info(f"@{user} [#{uuid}]: {msg}")
    return True


def send_message(bot, cid, msg, mode):
    if "commands" not in msg and "cryptopia" not in msg:
        logger.info(f"{BOTNAME}: {msg}")
    mode = ParseMode.MARKDOWN or False
    bot.send_message(chat_id=cid, text=msg, parse_mode=mode)
    return True


def info(bot, update):
    msg = \
    """
      ```
                  INFO SECTION
      ```
      commands like */tip* & */withdraw* have a specfic format,\
    use them like so:
     
     Tipping format: 
       `/tip @[user] [amount]        (without brackets)`
     
     Withdrawing format: 
       `/withdraw [address] [amount] (without brackets)`

     WHERE:
    ` 
       [address] = withdraw #FoxdCoin address
          [user] = telegram username 
        [amount] = amount of #foxdCoin to utilise 
    `

     *NOTE*:
      - don't deposit a significant amount of #FoxdCoin through this #BOT
      - make sure that you enter a valid #FoxdCoin address when you perform a withdraw
      - we are not responsible of your funds if something bad happen to this #BOT 
     ```
          USE THIS #BOT AT YOUR OWN RISK
     ```
    """
    chat_uuid = update.message.chat_id
    send_message(bot, chat_uuid, msg, True)
    return True


def help(bot, update):
    msg = \
    """
      The following commands are at your disposal:
       /info, /balance, /deposit, /withdraw, /tip and /price
    """
    chat_uuid = update.message.chat_id
    send_message(bot, chat_uuid, msg, True)
    return True


def tip(bot, update):
    chat_uuid = update.message.chat_id
    receive_message(update.message)
    user_name = update.message.from_user.username
    user_uuid = update.message.from_user.id
    message = update.message.text.split(' ')
    if len(message) != 3:
        msg = "Please use /tip <username> <amount>!"
        send_message(bot, chat_uuid, msg, False)
        return False
    if user_name is None:
        msg = "Please set a #telegram username!"
        send_message(bot, chat_uuid, msg, False)
        return False
    if not isValidUsername(message[1]):
        msg = "Please input a valid username (ex: @JonDoe)!"
        send_message(bot, chat_uuid, msg, False)
        return False
    if not isValidAmount(message[2]):
        msg = "Please input a valid amount (ex: 1000)!"
        send_message(bot, chat_uuid, msg, False)
        return False
    amount = float(message[2])
    target = (message[1])[1:]
    if amount > 100000:
        msg = "Please send a lower amount (max: 100,000 FoxdCoin)!"
        send_message(bot, chat_uuid, msg, False)
        return False
    if target == user_name:
        msg = "You can't tip yourself silly.!"
        send_message(bot, chat_uuid, msg, False)
        return False
    if target == BOTNAME:
        bot.send_message(chat_id=chat_uuid, text='HODL.')
        return False
    target_uuid = getUserID(bot, update, target)
    if not target_uuid:
        msg = f'@{target} has no activity in this chat!'
        send_message(bot, chat_uuid, msg, False)
        return False
    balance = rpc_call('getbalance', [str(user_uuid)])
    if balance < amount:
        msg = f'@{user_name} you have insufficent funds.'
        send_message(bot, chat_uuid, msg, False)
        return False
    rpc_call('move', [str(user_uuid), str(target_uuid), str(amount)])
    msg = f'@{user_name} tipped @{target} of {amount} FoxdCoin'
    send_message(bot, chat_uuid, msg, False)
    return True


def balance(bot, update):
    chat_uuid = update.message.chat_id
    user_name = update.message.from_user.username
    user_uuid = update.message.from_user.id
    if user_name is None:
        msg = "Please set a telegram username in your profile settings!"
        send_message(bot, chat_uuid, msg, False)
        return False
    result = rpc_call('getbalance', [str(user_uuid)])
    balance = str(round(float(result), 8))
    msg = f'@{user_name} your current balance is: {balance} FoxdCoin'
    send_message(bot, chat_uuid, msg, False)
    return True


def deposit(bot, update):
    chat_uuid = update.message.chat_id
    user_name = update.message.from_user.username
    user_uuid = update.message.from_user.id
    if user_name is None:
        msg = 'Please set a telegram username in your profile settings!'
        send_message(bot, chat_uuid, msg, False)
        return False
    p2pkh = rpc_call('getaccountaddress', [str(user_uuid)])
    msg = f'@{user_name} your depositing address is: {p2pkh}'
    send_message(bot, chat_uuid, msg, False)
    return True


def withdraw(bot, update):
    chat_uuid = update.message.chat_id
    receive_message(update.message)
    user_name = update.message.from_user.username
    user_uuid = update.message.from_user.id
    if user_name is None:
        msg = 'Please set a telegram username!'
        send_message(bot, chat_uuid, msg, False)
        return False
    message = update.message.text.split(' ')
    if len(message) != 3:
        msg = 'Please use /withdraw <address> <amount>!'
        send_message(bot, chat_uuid, msg, False)
        return False
    is_valid = rpc_call('validateaddress', [message[1]])['isvalid']
    if not is_valid:
        msg = 'Please input a valid FoxdCoin address!'
        send_message(bot, chat_uuid, msg, False)
        return False
    if not isValidAmount(message[2]):
        msg = 'Please input a valid amount (ex: 1000)!'
        send_message(bot, chat_uuid, msg, False)
        return False
    amount = float(message[2])
    address = message[1]
    balance = float(rpc_call('getbalance', [str(user_uuid)]))
    if balance < amount:
        msg = f'@{user_name} you have insufficent funds.'
        send_message(bot, chat_uuid, msg, False)
        return False
    rpc_call('sendfrom', [str(user_uuid), str(address), str(amount)])
    msg = f'@{user_name} has successfully withdrew {amount} FoxdCoin to address: {address}'
    send_message(bot, chat_uuid, msg, False)
    return True


def rpc_call(method: str, params: list[Any]) -> dict[str, Any] | None:
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
    if len(user) < 7: return False
    elif len(user) > 35: return False
    elif not re.match('^@[0-9A-Za-z_]+$', user): return False
    else: return True


def isValidAmount(amount):
    try:
        float(amount)
        return True
    except ValueError: pass
    if amount.isnumeric(): return True
    return False


if __name__ == '__main__':
    main()
