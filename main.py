import logging
import os
import django
from dotenv import load_dotenv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PythonMeetup.settings')
django.setup()
load_dotenv()

from telegram._inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram._inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram._update import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters

from Meetup.models import User, Event, Speaker, Question

from django.db.models import QuerySet
from asgiref.sync import sync_to_async



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пример списка зарегистрированных пользователей
registered_users = {'karaman56', '@eugenedow'}
user_ids = set()
waiting_for_question = set()

# Получаем ключ бота из переменной окружения
TG_BOT_KEY = os.getenv('TG_BOT_KEY')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Используйте команду /register для регистрации.')


# Оборачиваем вызов модели в асинхронную функцию
@sync_to_async
def register_user(user_id, user_name):
    user, created = User.objects.get_or_create(telegram_id=user_id, defaults={'username': user_name})
    return user, created


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.username
    user_id = update.effective_user.id

    try:
        user, created = await register_user(user_id, user_name)  # Используем асинхронную версию
        if created:
            await update.message.reply_text('Вы успешно зарегистрированы!')
        else:
            await update.message.reply_text('Вы уже зарегистрированы!')
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при регистрации: {e}")

    if user.is_speaker:
        await show_speaker_menu(update.message.chat_id, context)
    else:
        await show_listener_menu(update.message.chat_id, context)


async def show_speaker_menu(chat_id, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Расписание докладов", callback_data='schedule')],
        [InlineKeyboardButton("Начать доклад", callback_data='start_talk')],
        [InlineKeyboardButton("Окончить доклад", callback_data='end_talk')],
        [InlineKeyboardButton("Задать вопрос", callback_data='question_talk')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text='Вы в меню докладчика! Выберите действие:',
                                   reply_markup=reply_markup)


async def show_listener_menu(chat_id, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Расписание докладов", callback_data='schedule')],
        [InlineKeyboardButton("Задать вопрос", callback_data='question_talk')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text='Вы в меню слушателя!', reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
        username = query.from_user.username

        if query.data == 'schedule':
            await query.edit_message_text(text="Вот расписание докладов...")
        elif query.data == 'start_talk':
            event, created = Event.objects.get_or_create(title="Доклад от " + username)
            event.speakers.add(Speaker.objects.get(user__telegram_id=user_id))
            await query.edit_message_text(text="Вы начали доклад!")
        elif query.data == 'end_talk':
            await query.edit_message_text(text="Вы закончили доклад!")
        elif query.data == 'question_talk':
            await query.edit_message_text(text="Какой у вас вопрос?")
            waiting_for_question.add(user_id)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in waiting_for_question:
        question = update.message.text
        user_name = update.effective_user.username or update.effective_user.first_name
        speaker = Speaker.objects.filter(user__telegram_id=user_id).first()

        # Сохраняем вопрос
        new_question = Question.objects.create(
            speaker=speaker,
            text=question,
            user_name=user_name
        )
        waiting_for_question.remove(user_id)
        await update.message.reply_text(f"Ваш вопрос: '{question}' был отправлен докладчику!")


def main():
    load_dotenv()
    TG_BOT_KEY = os.getenv('TG_BOT_KEY')
    if not TG_BOT_KEY:
        raise ValueError("Bot token is not set. Please check your .env file.")
    application = Application.builder().token(TG_BOT_KEY).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()