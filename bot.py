import telebot
from telebot import types

TOKEN = "7862488950:AAHbx3yt1OlGAvphOGVyrN2hzMuaJywVCv4"  # Вставьте сюда ваш токен
bot = telebot.TeleBot(TOKEN)

# Вопросы с вариантами ответов
questions = {
    'easy': [
        {
            'question': "Какие из этих языков программирования существуют? (выберите один)",
            'answers': ['Python', 'Java', 'HTML', 'Banana', 'C++'],
            'correct_answers': ['Python'],  # Один правильный ответ
            'type': 'multiple_choice'  # Тип вопроса - выбор одного
        },
        {
            'question': "Какие операторы существуют в Python? (выберите все правильные)",
            'answers': ['+', '-', '*', '/', '&&'],
            'correct_answers': ['+', '-', '*', '/'],  # Несколько правильных ответов
            'type': 'multiple_choice'  # Тип вопроса - выбор нескольких
        }
    ]
}

# Текущее состояние пользователя
user_data = {}

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для адаптивного тестирования. Используй /help для получения списка команд.")

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Вот доступные команды:\n/start - начать общение с ботом\n/help - показать список команд\n/test - начать тестирование")

# Команда /test для начала теста
@bot.message_handler(commands=['test'])
def start_test(message):
    print(f"Test started for user {message.chat.id}")  # Логирование старта теста
    user_data[message.chat.id] = {'question_index': 0, 'score': 0, 'difficulty': 'easy'}
    ask_question(message)

# Функция для задания вопроса
def ask_question(message):
    user_id = message.chat.id
    difficulty = user_data[user_id]['difficulty']
    question_index = user_data[user_id]['question_index']
    
    print(f"Current question index: {question_index}")  # Логирование индекса вопроса
    questions_list = questions[difficulty]
    
    if question_index < len(questions_list):
        question = questions_list[question_index]
        print(f"Asking question: {question['question']}")  # Логирование вопроса
        if question['type'] == 'multiple_choice':
            # Создание клавиатуры для выбора из нескольких вариантов
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for answer in question['answers']:
                markup.add(answer)
            bot.send_message(message.chat.id, question['question'], reply_markup=markup)
        user_data[user_id]['current_question'] = question  # Сохраняем текущий вопрос
    else:
        bot.send_message(message.chat.id, f"Тест завершен! Ваш результат: {user_data[user_id]['score']} из {len(questions[difficulty])}.")
        del user_data[user_id]

# Обработка ответа пользователя
@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    user_id = message.chat.id
    if user_id not in user_data:
        return  # Игнорируем ответы, если тест не был начат

    difficulty = user_data[user_id]['difficulty']
    question_index = user_data[user_id]['question_index']
    questions_list = questions[difficulty]

    if question_index < len(questions_list):
        question = questions_list[question_index]
        user_answer = message.text

        if question['type'] == 'multiple_choice':
            # Проверяем, если ответ пользователя правильный
            if user_answer in question['correct_answers']:
                user_data[user_id]['score'] += 1

        # Переход к следующему вопросу
        user_data[user_id]['question_index'] += 1
        ask_question(message)

# Запуск бота
bot.polling(none_stop=True)
