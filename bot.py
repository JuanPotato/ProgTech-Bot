#!/usr/bin/env python3

from aiogram import Bot, Dispatcher, executor, types
from pony.orm import *
import json
import toml
import re


help_text = '''I mean, if you really wanted to know :/

`/help` - Nah, you figured this one out
`/join groupname` - join the group :o
`/leave groupname` - exercise for reader
`/groups` - lists available groups'''


with open('groups.json') as f:
    groups = json.load(f)

with open('config.toml') as f:
    config = toml.load(f)

bot = Bot(token=config['bot_token'])
dp = Dispatcher(bot)
db = Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)

for group in groups:
    groups[group] = type(groups[group], (db.Entity,), {
        'id': PrimaryKey(int),
        'name': Required(str),
        'notify': Required(bool, default=True)
    })

db.generate_mapping(create_tables=True)


# Utilities
def titlecase_replace(match):
    if match.group(0).islower():
        return match.group(0)[0].upper() + match.group(0)[1:]
    else:
        return match.group(0)


def titlecase(s):
    return re.sub(r'[a-zA-Z]+([\'"a-zA-Z]*)', titlecase_replace, s)


# Programming and group name changes
#@dp.message_handler(regexp=r'(?i)^Programming( (?:&|&&|and|et|en|und|y|och|og|и|ו|e) .+?)+$')
async def programming_et_al(message: types.Message):
    pieces = re.split(r' (?:&|&&|and|et|en|und|y|och|og|и|ו|e) ', message.text, re.IGNORECASE)
    pieces[0] = 'Programming' # only sacred thing
    new_title = ' & '.join(titlecase(piece) for piece in pieces)

    await message.chat.set_title(new_title)


@dp.message_handler(regexp=r'^/join \S+$')
async def join(message: types.Message):
    group = message.text[6:]
    if group[0] == '@':
        group = group[1:]

    if group in groups:
        with db_session:
            if groups[group].exists(id=message.from_user.id):
                return_text = f'You were already a part of {group}'
            else:
                name=message.from_user.username or message.from_user.fullname()
                groups[group](id=message.from_user.id, name=name)
                return_text = f'You are now a part of {group}'
    else:
        return_text = f'No group found with name {group}'

    await bot.send_message(message.chat.id, return_text, reply_to_message_id=message.message_id)


@dp.message_handler(regexp=r'^/leave \S+$')
async def join(message: types.Message):
    group = message.text[7:]
    if group[0] == '@':
        group = group[1:]

    if group in groups:
        with db_session:
            if groups[group].exists(id=message.from_user.id):
                groups[group][message.from_user.id].delete()
                return_text = f'You are no longer a part of {group}'
            else:
                return_text = f'You were never a part of {group}'
    else:
        return_text = f'No group found with name {group}'

    await bot.send_message(message.chat.id, return_text, reply_to_message_id=message.message_id)


@dp.message_handler(regexp=r'^/list \S+$')
async def list(message: types.Message):
    group = message.text[6:]
    if group[0] == '@':
        group = group[1:]

    if group in groups:
        return_text = f'{groups[group].__name__}s:\n'
        with db_session:
            for user in groups[group].select():
                return_text += f' - {user.name}\n'
    else:
        return_text = f'No group found with name {group}'

    await bot.send_message(message.chat.id, return_text, reply_to_message_id=message.message_id)


@dp.message_handler(regexp=r'^/groups')
async def list_groups(message: types.Message):
    return_text = 'Groups:\n' + '\n'.join(f' - {group}' for group in groups) or 'None'

    await bot.send_message(message.chat.id, return_text, reply_to_message_id=message.message_id)


@dp.message_handler(regexp=r'^/help')
async def help(message: types.Message):
    await bot.send_message(message.chat.id, help_text, reply_to_message_id=message.message_id)


async def tag_group(group_name, chat_id):
    text = f'Tagging all {groups[group_name].__name__}s'

    with db_session:
        for user in groups[group_name].select():
            text += f'[!](tg://user?id={user.id})'

    await bot.send_message(chat_id, text, parse_mode='Markdown')

# @tagging
@dp.message_handler()
async def catchall(message: types.Message):
    for group_name in groups:
        if re.search(f'(^|\W)[#@]{group_name}\\b', message.text):
            await tag_group(group_name, message.chat.id)
            break

    #await bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
