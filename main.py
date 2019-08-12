import logging
import os

import telebot
from flask import Flask, request

TOKEN = "938388032:AAHeRssyrFPieF6WRYCkLz827NA6Paslj_s"
twitch_bearer = 'xsb1hqrxomj5y5mf01gq620gjp6uvo'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.

print("ITS a LIVE!!!!")


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 'Привет, ' + message.from_user.first_name +
                 '. Теперь ты будешь получать уведомления о начале стрима, а также о новых постах в группе VK')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message,
                 "Извини, я ищё не умею отвечать на обычные сообщения. Но скоро я смогу с тобой полноценно общаться")


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route('/' + "mildredStatus", methods=['GET'])
def get_stream_status():
    rd = request.args.get('hub.challenge')
    return rd, 200


@server.route('/mildredStatus', methods=['POST'])
def aler_about_stream():
    bot.send_message(548488172, "Маша стримит")
    return "", 200


# @server.route('/' + "EagleStatus", methods=['GET'])
# def get_stream_status():
#
#     bot.send_message(548488172, "WebHook установлен")
#     rd2 = request.args.get('hub.challenge')
#     return rd2, 200


# @server.route('/' + "EagleStatus", methods=['POST'])
# def get_stream_status():
#     print(request.method.name)
#     bot.send_message(548488172, "Разработчик начал стрим!!")
#     return "", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://marymildred-bot.herokuapp.com/' + TOKEN)
    return "Bot has been work!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
