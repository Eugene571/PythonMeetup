from django.utils.timezone import now
import logging


from telegram._update import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PythonMeetup.settings')
django.setup()
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.utils.timezone import localdate
from dotenv import load_dotenv
from Meetup.models import User, Event, Speaker, Question
import gunicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@sync_to_async
def fetch_schedule():
    today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    events = Event.objects.filter(start_time__gte=today_start, start_time__lt=today_end)
    if not events.exists():
        return "Сегодня нет запланированных мероприятий."

    schedule_text = "Вот расписание на сегодня:\n\n"
    for event in events:
        schedule_text += (
            f"Название: {event.title}\n"
            f"Дата начала: {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"Описание: {event.description}\n\n"
        )
    return schedule_text


def get_today_events():
    event_list = Event.objects.filter(start_time__date=localdate())
    events_text = ""
    for event in event_list:
        events_text += f"Название: {event.title}\nДата начала: {event.start_time}\n\n"
    return events_text


@sync_to_async
def get_today_events_async():
    return get_today_events()


registered_users = {'karaman56', '@eugenedow'}  # Пример зарегистрированных пользователей
user_ids = set()  # для хранения идентификаторов пользователей
user_states = {}  # для хранения состояния пользователей
reports = get_today_events()
waiting_for_question = set()  # Пользователи, ожидающие ввода вопроса


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Используйте команду /register для регистрации.')


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    user_id = update.effective_user.id
    user_ids.add(user_id)

    if user_name in registered_users:
        await update.message.reply_text('Вы уже зарегистрированы! Перевожу вас в меню докладчика...')
        user_states[user_id] = 'speaker'  # Устанавливаем состояние как докладчик
    else:
        await update.message.reply_text(
            'Вы успешно зарегистрированы! Здесь вы можете слушать доклады и задать вопросы.')
        user_states[user_id] = 'listener'  # Устанавливаем состояние как слушатель
    await show_menu_for_user(user_id, update.message, context)


async def show_speaker_menu(chat_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Расписание докладов", callback_data='schedule')],
        [InlineKeyboardButton("Начать доклад", callback_data='start_talk')],
        [InlineKeyboardButton("Окончить доклад", callback_data='end_talk')],
        [InlineKeyboardButton("Задать вопрос", callback_data='question_talk')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text='Вы в меню докладчика! Выберите действие:',
                                   reply_markup=reply_markup)


async def show_listener_menu(chat_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Расписание докладов", callback_data='schedule')],
        [InlineKeyboardButton("Задать вопрос", callback_data='question_talk')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text='Вы в меню слушателя!', reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query:
        await query.answer()
        user_id = query.from_user.id
        username = query.from_user.username

        if query.data == 'schedule':
            schedule_text = await fetch_schedule()
            await query.edit_message_text(text=schedule_text)
        elif query.data == 'start_talk':
            await query.edit_message_text(text="Вы начали доклад!")
            await notify_all_users(context, f"Докладчик {username} начал доклад!")
        elif query.data == 'end_talk':
            await query.edit_message_text(text="Вы закончили доклад!")
            await notify_all_users(context, f"Докладчик {username} закончил доклад!")
        elif query.data == 'question_talk':
            await query.edit_message_text(text="Какой у вас вопрос?")
            waiting_for_question.add(user_id)
            return  # текущий пользователь вводит вопрос
        # После любого действия, обновляем меню для всех
        await update_menus_for_all_users(context)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id in waiting_for_question:
        question = update.message.text
        username = update.effective_user.username or update.effective_user.first_name
        # Отправляем вопрос докладчику и всем другим пользователям
        message = f"Вопрос от {username}: {question}"
        await notify_all_users(context, message)
        waiting_for_question.remove(user_id)
        await update_menus_for_all_users(context)


async def notify_all_users(context: ContextTypes.DEFAULT_TYPE, message: str):
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")


async def update_menus_for_all_users(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_ids:
        if user_states.get(user_id) == 'speaker':
            await show_speaker_menu(user_id, context)
        else:
            await show_listener_menu(user_id, context)


async def show_menu_for_user(user_id: int, message, context: ContextTypes.DEFAULT_TYPE) -> None:
    if user_states.get(user_id) == 'speaker':
        await show_speaker_menu(message.chat_id, context)
    else:
        await show_listener_menu(message.chat_id, context)


def main():
    load_dotenv()
    tg_bot_key = os.getenv('TG_BOT_KEY')
    application = Application.builder().token(tg_bot_key).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.run_polling()


if __name__ == '__main__':
    main()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Current time: {now()}")