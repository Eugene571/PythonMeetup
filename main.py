from telegram._update import Update
from telegram._inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram._inline.inlinekeyboardmarkup import  InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


registered_users = {'karaman56', '@eugenedow'}  # Пример зарегистрированных пользователей
user_ids = set()  # для хранения идентификаторов пользователей
user_states = {}  # для хранения состояния пользователей
reports = ['Бухать под селедочку', 'Бухать по черному']
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
            await query.edit_message_text(text=f"Вот расписание докладов: {reports}")
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
    TOKEN = '7825479539:AAHTshs9UnHl3Rih2DNol6NFnEj-q5K7UrE'
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.run_polling()


if __name__ == '__main__':
    main()
