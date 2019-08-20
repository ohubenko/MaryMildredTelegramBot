import os

import pymongo
import telebot
from flask import Flask, request
import json

# Важные переменные
TOKEN = "938388032:AAHeRssyrFPieF6WRYCkLz827NA6Paslj_s"
twitch_bearer = 'xsb1hqrxomj5y5mf01gq620gjp6uvo'
streamer_url = "https://www.twitch.tv/mary_mildred"
admin_id = 548488172
group_id = -118525812
twitch_secret = "8jpst72r4dcubejbstj5x6axqcdar0"
# Создание бота и приложения Flask
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
# MongoDB_MLab
client = pymongo.MongoClient("mongodb://MildredBot:SaMp4721@ds261377.mlab.com:61377/heroku_03snt0h5")
db = client.get_database('heroku_03snt0h5')
records = db["users"]


# Body
@bot.message_handler(commands=['start'])
def command_start(message):
    """
    Ищет пользователя в БД, если находит тогда выводит сообщение что он уже подписан на уведомления.
    Если нет тогда добавляет chat_id, first_name, username в БД
    :param message:
    :return:
    """
    user = records.find({"_id": message.chat.id})  # Забирает колекцию пользователя(ей)
    find_user = None  # Нужно для опредиления найден ли пользователь если нету то он остаеться None
    for find_user in user:
        find_user = user

    if find_user is None:
        new_user = {"_id": message.chat.id,
                    "first_name": message.chat.first_name,
                    "username": message.chat.username}
        records.insert(new_user)
        bot.reply_to(message,
                     'Привет, ' + message.from_user.first_name +
                     '. Теперь ты будешь получать уведомления о начале стрима, а также о новых постах в группе VK')
    else:
        bot.reply_to(message,
                     'Привет, ' + message.from_user.first_name +
                     ". Ты уже подписан на уведомелния. Чтобы отменить подписку используй комманду /stop")


@bot.message_handler(commands=['stop'])
def command_stop(message):
    """
    Отписывает конкретного пользователя от рассылки и удаляет его из БД
    :param message:
    :return:
    """
    records.find_one_and_delete({"_id": message.chat.id})
    bot.reply_to(message, "Ты больше не будешь получать уведомления. Надеюсь ты вернешься.")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    """
    Отвечает на любые сообщение, на которых нет ответа.
    :param message:
    :return:
    """
    bot.reply_to(message,
                 "Извини, я ище не умею отвечать на обычные сообщения. Но скоро я смогу с тобой полноценно общаться")


@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    """
    Через хук забирает новые сообщения которые приходят боту
    :return:
    """
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


# TODO: Добавить проверку на валидность запроса, проверка на то что запрос из Twitch или нет
@server.route('/' + 'mildredStatus', methods=['GET', 'POST'])
def twitch_hook_alert():
    """
    Ответ на GET запрос от Twitch, нужен для установки WebHook, отвечает hub.challenge
    Отправляет каждому пользователю из БД уведомление о том что стрим уже начался
    :return:
    """
    if request.method == 'GET':
        rd = request.args.get('hub.challenge')
        if rd is None:
            return "Nope", 404
        else:
            bot.send_message(admin_id, "WebHook установлен")
            return str(rd), 200
    elif request.method == 'POST':
        rq_json = request.get_json()
        if rq_json == {'data': []}:
            print("\n")
            print("Stream has been end")
            print("\n")
        else:
            for user in records.find({}, {"_id": 1}):  # Выборка всех пользователей с выводом только chat_id
                # потом из колекции мы берём значение ключа
                bot.send_message(int(user.get("_id")), "Ау !!! Тут стрим начался!!!!")
                bot.send_message(int(user.get("_id")), streamer_url)
        return "Done", 200
    else:
        return "Nope", 404


@server.route('/' + 'AdminTest', methods=['GET', 'POST'])
def twitch_test_hook_alert():
    """
    Ответ на GET запрос от Twitch, нужен для установки WebHook, отвечает hub.challenge
    Отправляет каждому пользователю из БД уведомление о том что стрим уже начался
    :return:
    """
    if request.method == 'GET':
        rd = request.args.get('hub.challenge')
        if rd is None:
            return "Nope", 404
        else:
            bot.send_message(admin_id, "WebHook установлен")
            return str(rd), 200
    elif request.method == 'POST':
        rq_json = request.get_json()
        if rq_json == {'data': []}:
            print("\n")
            print("Stream has been end")
            print("\n")
        else:
            bot.send_message(admin_id, "Test alert dev has been live")
        return "Done", 200
    else:
        return "Nope", 404


@server.route('/VkUpdate', methods=['GET', 'POST'])
def vk_get_wall():
    rq = request.get_json()
    confirmation_rq = {'type': 'confirmation', 'group_id': 185560511, 'secret': 'MySeecretKeyIsNotForYou21'}
    if rq == confirmation_rq:
        if request.method == 'POST':
            return "26d6836b", 200
        elif request.method == 'GET':
            return 'NotSupported', 200
        else:
            return "NotSupported", 404
    else:
        if rq.get('secret') == 'MySeecretKeyIsNotForYou21':
            if request.method == 'POST':
                post_obj = rq['object']
                post_dd = post_obj['attachments']
                print(post_obj)
                print('\n')
                print(type(post_dd))
                print(type(post_dd[0]))
                print(type(post_dd[1]))
                return "Ok", 200
            elif request.method == 'GET':
                return "NotSupported", 404
            else:
                return "NotSupported", 404
        else:
            return 'Forbidden', 403


@server.route('/')
def webhook():
    """
    Установка WebHook для telegram, выполняеться каждый раз когда запускаеться скрипт
    :return:
    """
    bot.remove_webhook()
    bot.set_webhook(url='https://marymildred-bot.herokuapp.com/' + TOKEN)
    return "Bot has been work!", 200


# Запуск сервера
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
