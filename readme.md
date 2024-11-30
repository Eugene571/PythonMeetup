# Telegram бот для управления конференцией

Это Telegram-бот, предназначенный для управления регистрацией пользователей и взаимодействиями во время конференции. Бот позволяет пользователям зарегистрироваться в качестве докладчиков или слушателей, просматривать расписание, задавать вопросы и уведомляет всех пользователей о таких событиях, как начало или окончание доклада.

## Возможности

- **Регистрация пользователей**: Пользователи могут зарегистрироваться с помощью команды `/register`.
- **Управление ролями**: Пользователи могут быть зарегистрированы в качестве докладчиков или слушателей на основе заранее заданных имен пользователей.
- **Динамические меню**: Каждой роли соответствует свой набор доступных действий, отображаемый с помощью кнопок встроенной клавиатуры.
- **Задание вопросов**: Докладчики и слушатели могут задавать вопросы, которые затем транслируются всем пользователям.
- **Уведомления**: Все пользователи получают уведомления, когда докладчик начинает или заканчивает доклад.
- **Автоматическое обновление меню**: После любого действия или вопроса пользователям показывается обновленное меню.

## Начало работы

### Необходимые условия

- Python 3.7+
- Библиотека `python-telegram-bot`

### Установка

1. Клонируйте репозиторий:
sh git clone https://github.com/your-username/your-repo-name.git cd your-repo-name

2. Установите необходимые пакеты: 
```
pip install -r requirements.txt
```
3. Замените `'YOUR_TOKEN_HERE'` в функции `main()` на ваш действительный токен Telegram-бота.

### Использование

Запустите бота:
`python main.py`

## Обзор кода

- **Управление пользователями**: Поддерживает список зарегистрированных пользователей и их роли (докладчик или слушатель).
- **Обработка состояний**: Управляет состояниями пользователей для отображения соответствующих меню и обработки взаимодействий.
- **Асинхронная обработка**: Использует асинхронные функции для обработки команд, колбэков и текстовых сообщений.
- **Логирование**: Использует логирование для отображения информации и сообщений об ошибках.

## Обработчики

- **Обработчики команд**: 
  - `/start`: Приветствует пользователей.
  - `/register`: Регистрирует пользователей и назначает роли.

- **Обработчик колбэк-запросов**:
  - Управляет взаимодействиями с кнопками для различных ролей.

- **Обработчик текстовых сообщений**:
  - Обрабатывает текстовые вопросы пользователей.

## Как это работает

1. **Запуск бота**: Команда `/start` приветствует пользователей и направляет их к регистрации.
2. **Регистрация**: Команда `/register` проверяет, является ли пользователь докладчиком или слушателем на основе его имени пользователя.
3. **Навигация по меню**: Пользователи взаимодействуют с ботом через кнопки встроенной клавиатуры, вызывающие разные действия.
4. **Вопрос и ответ**: Пользователи, нажавшие "Задать вопрос", должны ввести вопрос. Бот затем отправляет этот вопрос всем пользователям.
5. **Уведомления о событиях**: Все пользователи уведомляются о ключевых событиях, таких как начало или окончание доклада.

## Логирование

Бот использует библиотеку `logging` для вывода логов на уровне `INFO`, что полезно для отладки и отслеживания активности бота.
