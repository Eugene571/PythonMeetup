from django.utils.timezone import now
import logging

from telegram._update import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PythonMeetup.settings')
django.setup()
from asgiref.sync import sync_to_async
from django.utils import timezone
from dotenv import load_dotenv
from Meetup.models import User, Event, Speaker, Question
import gunicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@sync_to_async
def refresh_user_states():
    users = User.objects.all()
    for user in users:
        user_states[user.telegram_id] = 'speaker' if user.is_speaker else 'listener'


@sync_to_async
def fetch_schedule():
    # Используем UTC для вычисления времени начала и конца сегодняшнего дня
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
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
    # Получаем события для сегодняшнего дня в UTC
    event_list = Event.objects.filter(start_time__date=timezone.now().date())
    events_text = ""
    for event in event_list:
        events_text += f"Название: {event.title}\nДата начала: {event.start_time}\n\n"
    return events_text


@sync_to_async
def get_today_events_async():
    return get_today_events()


registered_users = {'karaman56', 'eugenedow', }  # Пример зарегистрированных пользователей
user_ids = set()  # для хранения идентификаторов пользователей
user_states = {}  # для хранения состояния пользователей
reports = get_today_events()
waiting_for_question = set()  # Пользователи, ожидающие ввода вопроса


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await refresh_user_states()
    await update.message.reply_text('Привет! Используйте команду /register для регистрации.')


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    user_id = update.effective_user.id

    # Создание или обновление пользователя в базе данных
    user, created = await sync_to_async(User.objects.get_or_create)(
        telegram_id=user_id,
        defaults={'tg_nick': user_name, 'username': user_name}
    )

    if not created:
        # Обновляем информацию о пользователе, если он уже существует
        user.tg_nick = user_name
        user.username = user_name
        await sync_to_async(user.save)()

    # Проверка и создание объекта Speaker, если это необходимо
    if user.is_speaker and not hasattr(user, 'speaker'):
        await sync_to_async(Speaker.objects.create)(user=user, name=user.username)

    # Устанавливаем актуальное состояние пользователя
    user_states[user_id] = 'speaker' if user.is_speaker else 'listener'

    # Отправляем сообщение пользователю в зависимости от его статуса
    if user.is_speaker:
        await update.message.reply_text(
            'Вы уже зарегистрированы как докладчик. Перевожу вас в меню докладчика...'
        )
    else:
        await update.message.reply_text(
            'Вы зарегистрированы как слушатель. Здесь вы можете слушать доклады и задавать вопросы.'
        )

    # Показать меню в зависимости от статуса пользователя
    await show_menu_for_user(user_id, context)


async def show_speaker_menu(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Расписание докладов", callback_data='schedule')],
        [InlineKeyboardButton("Начать доклад", callback_data='start_talk')],
        [InlineKeyboardButton("Окончить доклад", callback_data='end_talk')],
        [InlineKeyboardButton("Задать вопрос", callback_data='question_talk')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text='Вы в меню докладчика! Выберите действие:',
                                   reply_markup=reply_markup)


async def show_listener_menu(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Расписание докладов", callback_data='schedule')],
        [InlineKeyboardButton("Задать вопрос", callback_data='question_talk')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text='Вы в меню слушателя!', reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query:
        await query.answer()
        user_id = query.from_user.id
        username = query.from_user.username

        if query.data == 'schedule':
            schedule_text = await fetch_schedule()
            await query.edit_message_text(text=schedule_text)
            await show_menu_for_user(user_id, context)

        elif query.data == 'start_talk':
            await query.edit_message_text(text="Вы начали доклад!")
            await notify_all_users(context, f"Докладчик {username} начал доклад!")
            user_states[user_id] = 'speaker'
            await show_menu_for_user(user_id, context)

        elif query.data == 'end_talk':
            await query.edit_message_text(text="Вы закончили доклад!")
            await notify_all_users(context, f"Докладчик {username} закончил доклад!")
            user_states[user_id] = 'listener'
            await show_menu_for_user(user_id, context)

        elif query.data == 'question_talk':
            await query.edit_message_text(text="Какой у вас вопрос?")
            waiting_for_question.add(user_id)
            return  # Текущий пользователь вводит вопрос




async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id in waiting_for_question:
        question = update.message.text
        username = update.effective_user.username or update.effective_user.first_name
        # Отправляем вопрос докладчику и всем другим пользователям
        message = f"Вопрос от {username}: {question}"
        await notify_all_users(context, message)
        waiting_for_question.remove(user_id)  # Убираем пользователя из ожидания
        await update_menus_for_all_users(context)  # Обновляем меню
        await show_menu_for_user(user_id, context)
    else:
        # Обработать случай, когда пользователь не ожидает вопрос
        await update.message.reply_text('Вы не находитесь в процессе задавания вопроса.')


@sync_to_async
def get_users():
    return list(User.objects.all())

# Асинхронная функция для уведомления всех пользователей
async def notify_all_users(context: ContextTypes.DEFAULT_TYPE, message: str):
    # Получаем пользователей асинхронно
    users = await get_users()  # Прямо используем get_users
    for user in users:
        try:
            # Отправляем сообщение Telegram
            await context.bot.send_message(chat_id=user.telegram_id, text=message)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user.telegram_id}: {e}")

async def update_menus_for_all_users(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_ids:
        if user_states.get(user_id) == 'speaker':
            await show_speaker_menu(user_id, context)
        else:
            await show_listener_menu(user_id, context)


async def show_menu_for_user(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    if user_states.get(user_id) == 'speaker':
        await show_speaker_menu(user_id, context)
    else:
        await show_listener_menu(user_id, context)


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
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Current time: {now()}")
    main()

