import datetime
import os

import pymongo
import requests as rq
import telebot
from flask import Flask, request

# Важные переменные
TOKEN = str(os.getenv('TOKKEN'))
twitch_bearer = str(os.getenv('twitch_bearer'))
streamer_url = str(os.getenv('streamer_url'))
client_id = str(os.getenv('client_id'))
url_update_token = str(os.getenv('url_update_token'))
admin_id = int(os.getenv('admin_id'))
twitch_secret = str(os.getenv('twitch_secret'))
# Создание бота и приложения Flask
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
# MongoDB_MLab
mongodb_url = str(os.getenv('mongodb_url'))
client = pymongo.MongoClient(mongodb_url, retryWrites=False)
db = client.get_database(str(os.getenv('db_name')))
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


@bot.message_handler(commands=['updatetoken'])
def command_update_token(message):
    update_token()


def update_token():
    params = {'client_id': client_id,
              'client_secret': twitch_secret,
              'grant_type': 'client_credentials'}
    request_update_token = rq.post(url_update_token, data=params)
    if request_update_token.status_code == 200:
        update_json = request_update_token.json()
        new_token = update_json.get('access_token')
        os.environ['twitch_bearer'] = new_token
        bot.send_message(admin_id, "Token has been update\nNew token: %s" % new_token)
    else:
        bot.send_message(admin_id, "Не удалось обновить токен доступа twitch")


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


# TODO: Добавить проверку на валидность запроса, проверка на то что запрос из Twitch или нет, добавить авто подписку
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
                try:
                    bot.send_message(int(user.get("_id")), "Ау !!! Тут стрим начался!!!!")
                    bot.send_message(int(user.get("_id")), streamer_url)
                except:
                    bot.send_message(admin_id, "Проблемы с отправкой в методе twitch alert")
        return "Done", 200
    else:
        return "Nope", 404


@server.route('/VkUpdate', methods=['GET', 'POST'])
def vk_get_wall():
    """
    Принимает запросы от ВК, проверяет их валидность с ключем
    Обрабатывает запрос
    Выделяет от поста вложения, смотрит репост ли ето
    вызывает ф-ю обработки вложений
    :return:
    """
    reqs = request.get_json()
    if request.method == 'GET':
        return "Not Supported", 404
    confirmation_rq = {'type': 'confirmation', 'group_id': 118525812, 'secret': 'MySeecretKeyIsNotForYou21'}
    if reqs == confirmation_rq:
        if request.method == 'POST':
            return "2cd011e5", 200
        else:
            return "NotSupported", 404
    else:
        if reqs.get('secret') == 'MySeecretKeyIsNotForYou21':
            if request.method == 'POST':
                post_obj = reqs['object']  # Берем объект поста
                post_attachments = post_obj.get('attachments')  # Забираем с него вложения
                post_repost = post_obj.get('copy_history')  # Забираем с него репост
                post_text = str(post_obj.get('text'))  # Забираем текст поста

                for user in records.find({}, {"_id": 1}):  # Отправляем всем пользователям оповещение о новом посте
                    try:
                        bot.send_message(int(user.get("_id")), "В группе новый пост:")
                    except:
                        bot.send_message(admin_id, "Проблемы с отправкой в методе vk get wall")
                # Смотрим есть ли в посте текст,ткк без этого бот улетает
                if post_text == "":
                    print("Post haven't text")
                else:
                    # Отправляем текст
                    for user in records.find({}, {"_id": 1}):
                        bot.send_message(int(user.get("_id")), post_text)
                # Обрабатываем тип поста и вложения (пост/репост)
                if post_attachments is None:
                    print("Haven't attachment")
                    if post_repost is not None:
                        print("Tyt bil repost")
                        for history in post_repost:
                            h_attachments = history.get('attachments')
                            vk_attachemnts(h_attachments)
                else:
                    vk_attachemnts(post_attachments)
                return "Ok", 200
            else:
                return "NotSupported", 404
        else:
            return 'Forbidden', 403


def vk_attachemnts(attachments):
    """
    На входе получает словарь(список) вложений
    Для каждого вложения определяет тип
    Согласно типу обрабатывает его
    Бот отправляет вложение
    :param attachments:
    :return:
    """
    for attachment in attachments:
        # Определяем тип вложения
        attachment_type = attachment.get('type')
        # Обрабатываем вложение
        try:
            if attachment_type == 'photo':
                post = attachment['photo']['sizes'][-1]
                for user in records.find({}, {"_id": 1}):
                    bot.send_photo(int(user.get("_id")), post.get('url'))
            elif attachment_type == 'link':
                post = attachment['link']['url']
                for user in records.find({}, {"_id": 1}):
                    bot.send_message(int(user.get("_id")), post)
            else:
                for user in records.find({}, {"_id": 1}):
                    bot.send_message(int(user.get("_id")),
                                     "\n К сожалению там есть вложение что не поддерживаеться")
        except:
            bot.send_message(admin_id, "Пиздец, не отправляет вложения")


def twitch_hook_set():
    '''
    Установка хука на стрим
    :return: Код, установленно или нет
    '''
    # Куда Twitch будет стучать
    # Подписка/отписка от ивента
    # Ивент, передаю сразу параметром id пользователя
    # Время на сколько будет действовать отслежевание подписки, 864000 -макс
    headers = {"Authorization": "Bearer %s" % twitch_bearer}
    # Заголовок с авторизацией
    payload = {'hub.callback': 'https://marymildred-bot.herokuapp.com/mildredStatus',
               'hub.mode': 'subscribe',
               'hub.topic': 'https://api.twitch.tv/helix/streams?user_id=247494838',
               'hub.lease_seconds': 864000}
    r = rq.post('https://api.twitch.tv/helix/webhooks/hub', data=payload, headers=headers)
    if r.status_code == 200:
        bot.send_message(admin_id, "Подписка продленна, автоматически")
    else:
        bot.send_message(admin_id, "Что-то пошло не так")


@bot.message_handler(commands=['check'])
def twitch_hook_check(message):
    response = rq.get('https://api.twitch.tv/helix/webhooks/subscriptions',
                      headers={"Authorization": "Bearer %s" % twitch_bearer})
    response_json = response.json()
    print(response_json)
    if response_json == "":
        twitch_hook_set()
    elif response.status_code == 401:
        update_token()
    else:
        date = datetime.datetime.strptime(response_json.get('data')[0].get('expires_at'), '%Y-%m-%dT%H:%M:%SZ')
        bot.send_message(admin_id, "Date to expiration of hook:" + str(date))
        return date


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
