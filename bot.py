#!/usr/bin/env python3

from aiogram import Bot, Dispatcher, executor, types
import json
import toml
import re


help_text = """I mean, if you really wanted to know :/

`/help` - Nah, you figured this one out
`/join groupname` - join the group :o
`/leave groupname` - exercise for reader
`/groups` - lists available groups
`/addgroup grouptag Membersname` - create a new group with eg switch_peeps, Switcheroos"""


with open("groups.json") as f:
    groups = json.load(f)


with open("config.toml") as f:
    config = toml.load(f)


bot = Bot(token=config["bot_token"])
dp = Dispatcher(bot)

# Utilities
def titlecase_replace(match):
    if match.group(0).islower():
        return match.group(0)[0].upper() + match.group(0)[1:]
    else:
        return match.group(0)


def titlecase(s):
    return re.sub(r'[a-zA-Z]+([\'"a-zA-Z]*)', titlecase_replace, s)


# Programming and group name changes
#@dp.message_handler(regexp=r'(?i)^Programming( (?:&|&&|and|et|en|und|y|och|og|и|ו|e) [\S ]+?)+$')
async def programming_et_al(message: types.Message):
    pieces = re.split(
        r" (?:&|&&|and|et|en|und|y|och|og|и|ו|e) ", message.text, re.IGNORECASE
    )
    pieces[0] = "Programming"  # only sacred thing
    new_title = " & ".join(titlecase(piece) for piece in pieces)

    await message.chat.set_title(new_title)


@dp.message_handler(regexp=f"^/join(?:@{config['bot_username']})? \\S+$")
async def join(message: types.Message):
    args = message.text.split(" ")
    group = args[1]

    if group[0] == "@":
        group = group[1:]

    str_id = str(message.from_user.id)

    if group in groups:
        if str_id in groups[group]:
            return_text = f"You were already a part of {group}"
        else:
            name = message.from_user.username or message.from_user.fullname()
            groups[group]['members'][str_id] = {
                "name": name,
                "notify": True,
            }
            return_text = f"You are now a part of {group}"
    else:
        return_text = f"No group found with name {group}"

    await bot.send_message(
        message.chat.id, return_text, reply_to_message_id=message.message_id
    )


@dp.message_handler(regexp=f"^/leave(?:@{config['bot_username']})? \\S+$")
async def leave_group(message: types.Message):
    args = message.text.split(" ")
    group = args[1]

    if group[0] == "@":
        group = group[1:]

    str_id = str(message.from_user.id)

    if group in groups:
        if str_id in groups[group]:
            del groups[group][str_id]
            return_text = f"You are no longer a part of {group}"
        else:
            return_text = f"You were never a part of {group}"
    else:
        return_text = f"No group found with name {group}"

    await bot.send_message(
        message.chat.id, return_text, reply_to_message_id=message.message_id
    )


@dp.message_handler(regexp=f"^/list(?:@{config['bot_username']})? \\S+$")
async def list(message: types.Message):
    args = message.text.split(" ")
    group = args[1]

    if group[0] == "@":
        group = group[1:]

    if group in groups:
        return_text = f"{groups[group]['name']}s:\n"

        for user_id,data in groups[group]['members'].items():
            return_text += f" • {data['name']}\n"
    else:
        return_text = f"No group found with name {group}"

    await bot.send_message(
        message.chat.id, return_text, reply_to_message_id=message.message_id
    )


@dp.message_handler(regexp=f"^/groups(?:@{config['bot_username']})?")
async def list_groups(message: types.Message):
    return_text = "Groups:\n" + "\n".join(f" • {group}" for group in groups) or "None"

    await bot.send_message(
        message.chat.id, return_text, reply_to_message_id=message.message_id
    )


@dp.message_handler(regexp=f"^/help(?:@{config['bot_username']})?")
async def help(message: types.Message):
    await bot.send_message(
        message.chat.id, help_text, reply_to_message_id=message.message_id
    )


@dp.message_handler(regexp=f"^/addgroup(?:@{config['bot_username']})? \\S+ \\S+")
async def add_group(message: types.Message):
    args = message.text.split(" ")
    group = args[1]

    if group[0] == "@":
        group = group[1:]
    member = titlecase(' '.join(args[2:]))

    if group in groups:
        return_text = f"Group {group} already exists. call `/join {group}` to join"
    else:
        str_id = str(message.from_user.id)
        name = message.from_user.username or message.from_user.fullname()

        groups[group] = {
            'name': member,
            'members': {
                str_id: {
                    "name": name,
                    "notify": True,
                }
            }
        }

        with open("groups.json", "w") as outfile:
            json.dump(groups, outfile, indent=2)

        return_text = f"You are now a part of {group}"

    await bot.send_message(
        message.chat.id, return_text, reply_to_message_id=message.message_id
    )


async def tag_group(group_name, chat_id):
    text = f"Tagging all {groups[group_name]['name']}s"

    for user_id in groups[group_name]['members']:
        text += f"[!](tg://user?id={user_id})"

    await bot.send_message(chat_id, text, parse_mode="Markdown")


# @tagging
@dp.message_handler()
async def catchall(message: types.Message):
    for group_name in groups:
        if re.search(f"(^|\W)[#@]{group_name}\\b", message.text):
            await tag_group(group_name, message.chat.id)
            break

    # await bot.send_message(message.chat.id, message.text)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
