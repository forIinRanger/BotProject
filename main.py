import logging
import validators
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, CallbackQueryHandler, \
    ConversationHandler

from change_id import change_ids
from data import db_session
from config import TOKEN
from data.users import User
from data.websites import Website
import time
import hashlib
from urllib.request import urlopen, Request

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

db_session.global_init('gt.db')
db_sess = db_session.create_session()


def string_resources(user: User) -> str:
    result = 'Tracking websites:\n--------------------------------------------------------\n'
    counter = 0
    for i in user.news:
        counter += 1
        result += f"""{counter}. {i.address}
--------------------------------------------------------
"""
    if not user.news:
        result += 'Чтобы добавить ресурсы для отслеживания, обратите внимание на кнопки под данным сообщением'
    return result


async def registration(update, context):
    # reply_keyboard = [['/auth'],
    #                   ['/sh'],
    #                   ['/cancel']]
    # markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    match db_sess.query(User).filter(User.id == update.effective_user.id).first():
        case None:
            user = User()
            user.id = update.effective_user.id
            user.state = 0
            db_sess.add(user)
            db_sess.commit()
            await update.message.reply_text('✅Пользователь зарегистрирован')
        case _:
            await update.message.reply_text('✅Пользователь уже в системе')


async def add_website_str(update, context):
    await update.callback_query.edit_message_reply_markup()
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="""Введите адрес ресурса:
(P.S. Отмена операции - /cancel)""")
    db_sess.query(User).filter(User.id == update.effective_user.id).first().state = 1
    db_sess.commit()
    return ADD


async def remove_website_str(update, context):
    await update.callback_query.edit_message_reply_markup()
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="""Введите номер ресурса для удаления:
(P.S. Отмена операции - /cancel)""")
    db_sess.query(User).filter(User.id == update.effective_user.id).first().state = 1
    db_sess.commit()
    return REMOVE


async def add_main(update, context):
    address = update.message.text.rstrip('/')
    if validators.url(address):
        if db_sess.query(Website).filter(Website.address == address,
                                         Website.user_id == update.effective_user.id).first():
            await update.message.reply_text("""Вы отслеживаете этот сайт, повторите попытку ввода
(P.S. Не добавлять сайт - /cancel)""")
            return ADD
        else:
            website = Website()
            website.address = address
            website.user_id = update.effective_user.id
            url = Request(f'{address}',
                          headers={'User-Agent': 'Mozilla/5.0'})
            response = urlopen(url).read()
            website.version = hashlib.sha224(response).hexdigest()
            match address.split():
                case [*_, ".climbingcompetition.ru", _]:
                    website.climb = True
                case _:
                    website.climb = False
            db_sess.add(website)
            db_sess.commit()
            await update.message.reply_text('✅Успешно добавлено')
    else:
        await update.message.reply_text("""Некорректный адрес сайта, повторите попытку ввода
(P.S. Не добавлять сайт - /cancel)""")
        return ADD
    db_sess.query(User).filter(User.id == update.effective_user.id).first().state = 0
    db_sess.commit()
    return ConversationHandler.END


async def remove_main(update, context):
    user = db_sess.query(User).filter(User.id == update.effective_user.id).first()
    number = update.message.text
    if number.isnumeric():
        number = int(number)
        if 0 < number <= len(user.news):
            s = user.news[number - 1]
            db_sess.delete(s)
            db_sess.commit()
            await update.message.reply_text('✅Успешно удалено')
            change_ids(db_sess)
            user.state = 0
            db_sess.commit()
            return ConversationHandler.END
        else:
            await update.message.reply_text('🚫Некорректное число')
            return REMOVE
    else:
        await update.message.reply_text('🚫Не число')
        return REMOVE


async def for_wtf(update, context):
    await context.bot.send_photo(update.effective_user.id, 'static/bear.jpg', caption="""Я - бот🦾, 
    который поможет тебе отслеживать обновления заданных тобой сайтов🕵🏽. Добавляй сайты в свой список и 
    получай уведомления об обновлениях первым (-ой). Мои основные команды: 
    /auth - регистрация в боте 
    /sh - просмотр отслеживаемых ресурсов 
    /cancel - отмена какой либо операции 
    Удачи😉""")


async def cancel(update, context):
    user = db_sess.query(User).filter(User.id == update.effective_user.id).first()
    if user:
        match user.state:
            case 0:
                await context.bot.send_photo(update.effective_user.id, 'static/bear.jpg', caption="""Я - бот🦾, 
который поможет тебе отслеживать обновления заданных тобой сайтов🕵🏽. Добавляй сайты в свой список и 
получай уведомления об обновлениях первым (-ой). Мои основные команды: 
/auth - регистрация в боте 
/sh - просмотр отслеживаемых ресурсов 
/cancel - отмена какой либо операции 
Удачи😉""")
            case 1:
                await update.message.reply_text('🔙Действие отменено')
                db_sess.query(User).filter(User.id == update.effective_user.id).first().state = 0
                db_sess.commit()
                return ConversationHandler.END
    else:
        await update.message.reply_text('❗️Вы должны зарегистрироваться перед началом работы с ботом❗️')


async def he(update, context):
    await update.message.reply_text('хули ебать')


async def show_sites(update, context):
    user_from_db = db_sess.query(User).filter(User.id == update.effective_user.id).first()
    if user_from_db:
        user_from_db.state = 1
        db_sess.commit()
        result = string_resources(user_from_db)
        keybut = [[InlineKeyboardButton('add resource', callback_data='add')]]
        if user_from_db.news:
            keybut.append([InlineKeyboardButton('remove resource', callback_data='remove')])
        keyboard = InlineKeyboardMarkup(keybut)

        await update.message.reply_text(result, reply_markup=keyboard)
        return FOR_ALL
    else:
        await update.message.reply_text('❗️Вы должны зарегистрироваться перед началом работы с ботом❗️')


async def check_site_on_upd(context):
    for site in db_sess.query(Website).all():
        url = Request(f'{site.address}',
                      headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(url).read()
        current_hash = hashlib.sha224(response).hexdigest()
        if site.version != current_hash:
            site.version = current_hash
            db_sess.commit()
            await context.bot.send_message(site.user_id, f'На сайте {site.address} произошли изменения!')


FOR_ALL, ADD, REMOVE = range(3)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('sh', show_sites)],
        states={
            FOR_ALL: [CallbackQueryHandler(add_website_str, pattern='add'),
                      CallbackQueryHandler(remove_website_str, pattern='remove'),
                      CommandHandler('cancel', cancel)],
            ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_main)],
            REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_main)]

        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('cancel', cancel))
    app.add_handler(CommandHandler('auth', registration))
    app.add_handler(MessageHandler(filters.TEXT, for_wtf))
    job = app.job_queue
    job.run_repeating(check_site_on_upd, interval=15)
    app.run_polling()


if __name__ == '__main__':
    main()
