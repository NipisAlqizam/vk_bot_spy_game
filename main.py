import json
import os
import random
import re

from loguru import logger
from vkbottle.bot import Bot, MessageMin
from typing import Optional

import locations
from strings import GAME_STOPPED, NO_CURRENT_GAME, RECRUITMENT_STARTED, GAME_STARTED, GAME_ALREADY_STARTED, \
    ERROR_NO_RIGHTS, ALREADY_PLAYING, ERROR_MESSAGES_FORBIDDEN, ALREADY_ALL_PLAYERS, HELP_MESSAGE, \
    LOCATIONS_UPDATED, NOT_ENOUGH_PLAYERS, PLAYING_NOW, GAME_RULES

admin_ids = list(map(int, os.environ['admin_ids'].split()))
players_list = []  # TODO: позволить игру из разных бесед
current_game = False
all_players = False
spy = 0
current_location = ''

bot = Bot(os.environ["token"])

bot.labeler.vbml_ignore_case = True

async def send_pm(to_id: int, message: str):
    print(to_id, message)
    await bot.api.messages.send(to_id, random_id=random.randint(1, 2 ** 63), message=message)


async def get_user_ping(user_id: int) -> str:
    users_info = await bot.api.users.get(user_id, fields=['screen_name'])
    user_info = users_info[0]
    user_nickname = user_info.screen_name
    logger.debug(f'User nickname is {user_nickname}')
    return f"@{user_nickname} ({user_info.first_name} {user_info.last_name})"


@bot.on.chat_message(text="шпионвойти")
async def join_handler(message: MessageMin):
    logger.debug(f'Происходит попытка входа в игру игрока {message.from_id}')
    if current_game and all_players:
        return ALREADY_ALL_PLAYERS
    if not await check_pm(message.from_id):
        return ERROR_MESSAGES_FORBIDDEN
    if message.from_id in players_list:
        return ALREADY_PLAYING
    if current_game:
        players_list.append(message.from_id)
        username = await get_user_ping(message.from_id)
        forward = json.dumps({
            "conversation_message_ids": [message.conversation_message_id],
            "peer_id": message.peer_id,
            "is_reply": True})
        await message.answer(f"{username}, тебя добавили", forward=forward, disable_mentions=True)
        return
    return NO_CURRENT_GAME


@bot.on.chat_message(text="шпионстарт")
async def start_handler(message: MessageMin):
    logger.debug('Происходит попытка запуска игры')
    if message.from_id not in admin_ids:
        return ERROR_NO_RIGHTS
    if not await check_pm(message.from_id):
        return ERROR_MESSAGES_FORBIDDEN
    global current_game
    global all_players
    if current_game and all_players:
        return GAME_ALREADY_STARTED
    if current_game:
        if len(players_list) < 3:
            return NOT_ENOUGH_PLAYERS
        all_players = True
        await assign_roles()
        return GAME_STARTED
    current_game = True
    players_list.append(message.from_id)
    return RECRUITMENT_STARTED


@bot.on.chat_message(text="шпионстоп")
async def stop_handler(message: MessageMin):
    logger.debug('Происходит попытка остановки игры')
    if message.from_id not in admin_ids:
        return ERROR_NO_RIGHTS
    global current_game
    global all_players
    if current_game:
        global spy, current_location
        no_spy = spy == 0
        players_list.clear()
        current_game = False
        all_players = False
        if no_spy:
            return GAME_STOPPED
        spy_ping = await get_user_ping(spy)
        result_string = f"{GAME_STOPPED}\nШпионом был(а) {spy_ping}\nЛокация - {current_location}"
        spy = 0
        current_location = ''
        return {"message": result_string, "disable_mentions": True}
    return NO_CURRENT_GAME


@bot.on.message(text="шпионкоманды")
async def help_handler(message: MessageMin):
    return HELP_MESSAGE


@bot.on.message(text=["шпионлокации <location>", "шпионлокации"])
async def location_handler(message: MessageMin, location: Optional[str] = None):
    logger.debug('Получена комманда на локации')
    if location is not None:
        if message.from_id not in admin_ids:
            return ERROR_NO_RIGHTS
        logger.debug(f'Происходит добавление локации {location}')
        locations.add_location(location)
    return 'Текущие локации:\n' + '\n'.join(locations.locations)


@bot.on.chat_message(regexp=r"(?i)^шпионобновить[ \n]*((?:.+\n?)+)")
async def location_update_handler(message: MessageMin, match: list[str]):
    logger.debug('Попытка обновления локаций')
    if message.from_id not in admin_ids:
        return ERROR_NO_RIGHTS
    await message.answer('Текущие локации:\n' + "\n".join(locations.locations))
    new_locations = match[0].splitlines()
    locations.update_location_list(new_locations)
    return LOCATIONS_UPDATED + "\n".join(locations.locations)


@bot.on.chat_message(text="шпионучастники")
async def people_handler(message: MessageMin, match: list[str]):
    if not current_game:
        return NO_CURRENT_GAME
    people = [await get_user_ping(user) for user in players_list]
    await message.answer("{}\n{}".format(PLAYING_NOW, "\n".join(people)), disable_mentions=True)


@bot.on.message(text="шпионправила")
async def rules_handler(message: MessageMin):
    return GAME_RULES


async def assign_roles():
    global spy, current_location
    current_location = locations.choose_location()
    spy = random.choice(players_list)
    for player in players_list:
        print(player, current_location, spy)
        if player == spy:
            await send_pm(player, "Шпион")
        else:
            await send_pm(player, current_location)


async def check_pm(user_id: int) -> bool:
    conversation = await bot.api.messages.get_conversations_by_id([user_id])
    can_write = conversation.items[0].can_write.allowed
    return can_write


bot.run_forever()
