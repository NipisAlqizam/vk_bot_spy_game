import json
import os
import random

from vkbottle.bot import Bot, MessageMin

import locations

admin_ids = [203760080, 357855054, 513143028, 526421484]  # я, Лиза, Лёня, Антон
players_list = []  # TODO: позволить игру из разных бесед
current_game = False
all_players = False

bot = Bot(os.environ["token"])


async def send_pm(to_id: int, message: str):
    print(to_id, message)
    await bot.api.messages.send(to_id, random_id=random.randint(1, 2 ** 63), message=message)


async def get_username(user_id: int) -> str:
    users_info = await bot.api.users.get(user_id)
    user_info = users_info[0]
    return f"{user_info.first_name} {user_info.last_name}"


@bot.on.chat_message(func=lambda m: "шпионвойти" in m.text.lower())
async def join_handler(message: MessageMin):
    if current_game and all_players:
        return "А всё, всех набрали"
    if not await check_pm(message.from_id):
        return "Вы запретили боту писать вам в лс. Напишите что-нибудь ему или разблокируйте"
    if message.from_id in players_list:
        return "Ты уже играешь"
    if current_game:
        players_list.append(message.from_id)
        username = await get_username(message.from_id)
        forward = json.dumps({
            "conversation_message_ids": [message.conversation_message_id],
            "peer_id": message.peer_id,
            "is_reply": True})
        await message.answer(f"{username}, тебя добавили", forward=forward)
        return
    return "Игру ещё не начали"


@bot.on.chat_message(func=lambda m: "шпионстарт" in m.text.lower())
async def start_handler(message: MessageMin):
    if message.from_id not in admin_ids:
        return "Вы должны быть избраны создателем для этого действия :)"
    if not await check_pm(message.from_id):
        return "Вы запретили боту писать вам в лс. Напишите что-нибудь ему или разблокируйте"
    global current_game
    global all_players
    if current_game and all_players:
        return "Игра уже идёт"
    if current_game:
        all_players = True
        await assign_roles()
        return "Игра начата"
    current_game = True
    players_list.append(message.from_id)
    return "Начат набор в игру"


@bot.on.chat_message(func=lambda m: "шпионстоп" in m.text.lower())
async def stop_handler(message: MessageMin):
    if message.from_id not in admin_ids:
        return "Вы должны быть избраны создателем для этого действия :)"
    global current_game
    global all_players
    if current_game:
        players_list.clear()
        current_game = False
        all_players = False
        return "Игра остановлена"
    return "Игра ещё не идёт"


async def assign_roles():
    location = locations.choose_location()
    spy = random.choice(players_list)
    for player in players_list:
        print(player, location, spy)
        if player == spy:
            await send_pm(player, "Шпион")
        else:
            await send_pm(player, location)


async def check_pm(user_id: int) -> bool:
    conversation = await bot.api.messages.get_conversations_by_id([user_id])
    can_write = conversation.items[0].can_write.allowed
    return can_write


bot.run_forever()
