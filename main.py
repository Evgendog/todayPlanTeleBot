import telebot
import datetime
import config
from db import BotDB
from utility import stat_mes_request, earned_request, plan_request, delete_call_request, stat_file_request, \
    stats_to_file, remove_stat_file


bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    db = BotDB()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_exist = db.user_exist(user_id)
    if user_exist:
        text = f"Привет ещё раз, {user_name} :)\nТы уже есть в базе, если ты что-нибудь " \
               f"забыл(-а),  используй /help"
    else:
        db.add_user(user_id)
        text = f"Привет, {user_name} :)\nЯ помогу тебе отслеживать план на день. Для помощи используй /help\nДля " \
               f"начала давай введём твой план на сегодня. Для этого отправь сообщение в формате - 'План 3000'.\n" \
               f"P.S. Не обязательно писать с большой буквы, я регистронезависимый 😉"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['showtodaystats'])
def show_today_stats(message):
    db = BotDB()
    user_id = message.from_user.id
    user_exist = db.user_exist(user_id)
    if user_exist:
        today = db.get_today()
        data = db.get_stats(user_id, today, today)
        if data:
            text = f"План на сегодня     ➡    {data[0][2]};\n" \
                   f"уже заработано      ➡    {data[0][3]};\n" \
                   f"План выполнен на    ➡    {100 if data[0][2] == 0 else round((data[0][3] / data[0][2]) * 100, 2)}%"
        else:
            text = 'Данных нету, всё по нулям 🤷‍♀️'
    else:
        text = "Эвона как вышло то. Тебя нету в базе, чтоб добавиться, используй /start"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['deletedata'])
def delete_data(message):
    db = BotDB()
    user_id = message.from_user.id
    user_exist = db.user_exist(user_id)
    if user_exist:
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        button1 = telebot.types.InlineKeyboardButton('Удалить', callback_data='delete')
        button2 = telebot.types.InlineKeyboardButton('Отмена', callback_data='abort')
        markup.add(button1, button2)
        text = "Вернуть данные не выйдет, советую сначала экспортировать их сначала) Но если уже всё сделано или не " \
               "нужны тебе данные, то жми кнопку, отговорить я тебя не в силах"
    else:
        text = "Эвона как вышло то. Тебя нету в базе, чтоб добавиться, используй /start"
        markup = None
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=delete_call_request)
def delete_callback(call):
    if call.data == 'delete':
        db = BotDB()
        user_id = call.from_user.id
        db.delete_data(user_id)
        text = 'Все твои данные удалены. Жаль расставаться 🙁, но с тобой приятно было иметь дело, удачи ✋'
    else:
        text = 'Удаление отменено'
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text,
                          reply_markup=None)
    bot.send_message(call.message.chat.id, text)


@bot.message_handler(commands=['help'])
def helping(message):
    bot.send_message(message.chat.id, 'Список доступных команд:\n'
                                      '/start ➡ Запишу тебя в базу и подскажу с чего начать;\n'
                                      '/help ➡ Покажу список доступных команд;\n'
                                      '/showtodaystats ➡ Покажу данные за сегодня.\n\n'
                                      '/deletedata ➡ ‼💀 Удалю все записи о тебе без возможности восстановления.\n\n'
                                      'Чтобы переназначить план, просто заново отправь сообщение формата "План 3000".\n'
                                      'Чтобы добавить зароботок, просто напиши его целым числом. Например, "235".\n'
                                      'Чтобы получить статистику за сегодня, неделю, месяц, год, всё время, пиши что-то'
                                      'вроде "Стат неделя". Главное чтоб 2 слова было, первое из которых "стат" или '
                                      '"статистика", а второе - одно из: "день", "неделя", "нед", "месяц", "мес", '
                                      '"год", "вся", "всё", "все". Регистр не важен 😉\n'
                                      'P.S. Если вдруг введёшь не то число, или надо будет отменить какой-нибудь '
                                      'доход по иной причине, то можешь отправить отрицательное число. Но в минус '
                                      'доход (план тоже) загнать не дам (вместо этого сделаю его 0), а то % выполнения '
                                      'потом не сосчитаем 🤯\n'
                                      'P.P.S. Но можешь ставить нулевой план (по умолчанию он как раз 0), тогда % '
                                      'поставлю просто в 100, да и всё :)\n'
                                      'P.P.P.S. Запись за день создастся, только если отправишь план или доход. Если '
                                      'ничего не отправишь, день в базе вообще не запишется. Такие дела 🙂')


@bot.message_handler(func=plan_request)
def set_plan(message):
    db = BotDB()
    user_id = message.from_user.id
    user_exist = db.user_exist(user_id)
    if user_exist:
        plan = int(message.text.split()[1])
        plan = 0 if plan < 0 else plan
        updated = db.update_data(user_id, 'plan', plan)
        if updated == 0:
            db.insert_data(user_id, plan=plan)
            text = f"Запись на сегодня создана.\nПлан ➡ {plan}, заработано ➡ {0} (дефолт).\nПроверить можешь" \
                   f" с помощью /showtodaystats"
        else:
            text = f"План на сегодня обновлён и составляет ➡ {plan}\nПроверить можешь с помощью /showtodaystats"
    else:
        text = "Эвона как вышло то. Тебя нету в базе, чтоб добавиться, используй /start"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=earned_request)
def set_earned(message):
    db = BotDB()
    user_id = message.from_user.id
    user_exist = db.user_exist(user_id)
    if user_exist:
        earned = int(message.text)
        today_earned = db.get_today_earned(user_id)
        if today_earned is None:
            db.insert_data(user_id, earned=earned)
            text = f"Запись на сегодня создана.\nЗаработано ➡ {earned}, план ➡ {0} (дефолт, не забудь поменять, " \
                   f"если надо).\nПроверить можешь с помощью /showtodaystats"
        else:
            temp_earned = today_earned[0] + earned
            temp_earned = 0 if temp_earned < 0 else temp_earned
            db.update_data(user_id, 'earned', temp_earned)
            text = f"Доход за сегодня обновлён и составляет ➡ {temp_earned}\nПроверить можешь с помощью /showtodaystats"
    else:
        text = "Эвона как вышло то. Тебя нету в базе, чтоб добавиться, используй /start"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=stat_mes_request)
def get_mes_stats(message):
    db = BotDB()
    user_id = message.from_user.id
    user_exist = db.user_exist(user_id)
    if user_exist:
        bot.send_message(message.chat.id, "Формирую отчёт 🔄")
        today = db.get_today()
        other_day = today if message.text.split()[1].lower() == 'день' else today - datetime.timedelta(days=6)
        data = db.get_stats(user_id, other_day, today)
        if data:
            text = '***********************\n'
            for row in data:
                text += f"Дата        ➡   {row[1]};\n" \
                        f"План        ➡   {row[2]};\n" \
                        f"Заработано  ➡   {row[3]};\n" \
                        f"Выполнено   ➡   {100 if row[2] == 0 else round((row[3] / row[2]) * 100, 2)}%\n" \
                        f"***********************\n"
        else:
            text = 'Данных нету, всё по нулям 🤷‍♀️'
    else:
        text = "Эвона как вышло то. Тебя нету в базе, чтоб добавиться, используй /start"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=stat_file_request)
def get_file_stats(message):
    db = BotDB()
    user_id = message.from_user.id
    user_exist = db.user_exist(user_id)
    if user_exist:
        bot.send_message(message.chat.id, "Формирую отчёт 🔄")
        today = db.get_today()
        mes_time = message.text.split()[1].lower()
        if mes_time in ['всё', 'все', 'вся']:
            other_day = datetime.datetime.strptime('2021-10-30', '%Y-%m-%d')
        elif mes_time == 'год':
            other_day = today - datetime.timedelta(days=364)
        else:
            other_day = today - datetime.timedelta(days=29)
        data = db.get_stats(user_id, other_day, today)
        if data:
            file_name = stats_to_file(data)
            file = open(file_name, 'rb')
            bot.send_document(message.chat.id, file, caption="Готово, качай ☝")
            file.close()
            remove_stat_file(file_name)
        else:
            bot.send_message(message.chat.id, 'Данных нету, всё по нулям 🤷‍♀️')
    else:
        bot.send_message(message.chat.id, "Эвона как вышло то. Тебя нету в базе, чтоб добавиться, используй /start")


@bot.message_handler(content_types=['text'])
def messages(message):
    bot.send_message(message.chat.id, "Такой команды я не знаю, а разговорный модуль в разработке (если разраб мой"
                                      "не обленился там совсем) 🙁.\nЕсли нужна помощь, используй /help")


if __name__ == '__main__':
    bot.infinity_polling()
