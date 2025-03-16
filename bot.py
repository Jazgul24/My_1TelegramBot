import telebot

# Ваш токен
TOKEN = '7862488950:AAHbx3yt1OlGAvphOGVyrN2hzMuaJywVCv4'

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения данных пользователей
user_data = {}

# Вопросы для трех уровней сложности
questions_easy = [
    {
        'question': 'Что такое переменная?',
        'answers': ['Место для хранения данных', 'Инструкция для вычислений', 'Тип данных'],
        'correct': 'Место для хранения данных'
    },
    {
        'question': 'Что такое цикл for?',
        'answers': ['Цикл с условием', 'Цикл с заданным количеством повторений', 'Тип данных'],
        'correct': 'Цикл с заданным количеством повторений'
    }
]

questions_medium = [
    {
        'question': 'Как работает конструкция if-else?',
        'answers': ['Если условие истинно, выполняется один блок кода', 'Если условие ложно, выполняется блок кода', 'Если условие истинно, выполняется другой блок кода'],
        'correct': 'Если условие истинно, выполняется один блок кода'
    },
    {
        'question': 'Что такое функция в Python?',
        'answers': ['Механизм вызова кода с параметрами', 'Механизм создания объектов', 'Инструкция для вычислений'],
        'correct': 'Механизм вызова кода с параметрами'
    }
]

questions_hard = [
    {
        'question': 'Напишите программу для вычисления факториала числа.',
        'answers': ['def factorial(n): return 1 if n == 0 else n * factorial(n-1)', 'for i in range(1, n): return i * i', 'int n = 1'],
        'correct': 'def factorial(n): return 1 if n == 0 else n * factorial(n-1)'
    },
    {
        'question': 'Как реализовать рекурсию в Python?',
        'answers': ['Вызов функции внутри самой себя', 'Использование условных операторов', 'Циклическое выполнение блоков кода'],
        'correct': 'Вызов функции внутри самой себя'
    }
]

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Давай начнем с небольшого теста по Python. Напиши /test, чтобы начать!")

# Команда /test
@bot.message_handler(commands=['test'])
def start_test(message):
    bot.reply_to(message, "Тест начался! Пожалуйста, отвечайте на вопросы.")
    # Инициализация данных для пользователя
    user_data[message.chat.id] = {'question_index': 0, 'score': 0, 'difficulty': 'easy'}
    ask_question(message)

# Функция для отправки вопроса
def ask_question(message):
    user_id = message.chat.id
    difficulty = user_data[user_id]['difficulty']
    
    # Выбираем список вопросов в зависимости от сложности
    if difficulty == 'easy':
        question_data = questions_easy[user_data[user_id]['question_index']]
    elif difficulty == 'medium':
        question_data = questions_medium[user_data[user_id]['question_index']]
    else:
        question_data = questions_hard[user_data[user_id]['question_index']]
    
    # Формируем вопрос и варианты ответов
    question_text = question_data['question']
    answers = '\n'.join([f"{i+1}. {answer}" for i, answer in enumerate(question_data['answers'])])
    
    # Отправляем вопрос и варианты
    bot.send_message(user_id, f"{question_text}\n\n{answers}")
    bot.send_message(user_id, "Выберите номер правильного ответа (например, 1, 2, или 3)")

# Обработчик ответов пользователя
@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    user_id = message.chat.id

    # Если пользователя нет в словаре, он не начал тест
    if user_id not in user_data:
        return

    # Получаем текущий вопрос и ответы
    difficulty = user_data[user_id]['difficulty']
    
    if difficulty == 'easy':
        question_data = questions_easy[user_data[user_id]['question_index']]
    elif difficulty == 'medium':
        question_data = questions_medium[user_data[user_id]['question_index']]
    else:
        question_data = questions_hard[user_data[user_id]['question_index']]

    # Проверяем, правильный ли ответ
    try:
        user_answer = int(message.text) - 1  # Преобразуем в индекс (минус 1)
        if question_data['answers'][user_answer] == question_data['correct']:
            user_data[user_id]['score'] += 1
            bot.reply_to(message, "Правильный ответ!")
            # Если правильный ответ, повышаем сложность
            if difficulty == 'easy':
                user_data[user_id]['difficulty'] = 'medium'
            elif difficulty == 'medium':
                user_data[user_id]['difficulty'] = 'hard'
        else:
            bot.reply_to(message, "Неправильный ответ!")
            # Если неправильный ответ, понижаем сложность
            if difficulty == 'hard':
                user_data[user_id]['difficulty'] = 'medium'
            elif difficulty == 'medium':
                user_data[user_id]['difficulty'] = 'easy'

        # Переходим к следующему вопросу или заканчиваем тест
        user_data[user_id]['question_index'] += 1
        if (difficulty == 'easy' and user_data[user_id]['question_index'] < len(questions_easy)) or \
           (difficulty == 'medium' and user_data[user_id]['question_index'] < len(questions_medium)) or \
           (difficulty == 'hard' and user_data[user_id]['question_index'] < len(questions_hard)):
            ask_question(message)
        else:
            bot.reply_to(message, f"Тест завершен! Ваш результат: {user_data[user_id]['score']} из {len(questions_easy) + len(questions_medium) + len(questions_hard)}.")
            del user_data[user_id]  # Удаляем данные после завершения
    except (ValueError, IndexError):
        bot.reply_to(message, "Пожалуйста, введите номер правильного ответа (1, 2 или 3).")

# Запуск бота
bot.polling()
