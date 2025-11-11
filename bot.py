import os
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DATABASE = os.path.join(app.root_path, "app.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                group_name TEXT,
                score INTEGER NOT NULL DEFAULT 0,
                total_questions INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                topic TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                chosen_option INTEGER NOT NULL,
                correct_option INTEGER NOT NULL,
                FOREIGN KEY (attempt_id) REFERENCES attempts(id)
            )
            """
        )
        conn.commit()


QUESTIONS: Dict[str, List[Dict[str, object]]] = {
    "easy": [
        {
            "id": "variables_overview",
            "question": "Что такое переменная в Python?",
            "options": [
                "Имя, которое хранит ссылку на значение",
                "Встроенная функция для вывода данных",
                "Инструкция для создания цикла",
            ],
            "correct": 0,
            "topic": "Переменные и типы",
        },
        {
            "id": "print_function",
            "question": "Какой командой в Python можно вывести текст на экран?",
            "options": ["show()", "display()", "print()"],
            "correct": 2,
            "topic": "Ввод-вывод",
        },
        {
            "id": "list_create",
            "question": "Как создать список из чисел 1, 2 и 3?",
            "options": ["{1, 2, 3}", "[1, 2, 3]", "(1, 2, 3)"],
            "correct": 1,
            "topic": "Списки",
        },
    ],
    "medium": [
        {
            "id": "if_usage",
            "question": "Как работает конструкция if-elif-else?",
            "options": [
                "Проверяет условия последовательно, пока одно не выполнится",
                "Всегда выполняет все ветки подряд",
                "Выбирает случайную ветку",
            ],
            "correct": 0,
            "topic": "Условия",
        },
        {
            "id": "for_loop",
            "question": "Какой результат выполнения выражения sum(range(1, 5))?",
            "options": ["10", "15", "5"],
            "correct": 0,
            "topic": "Циклы",
        },
        {
            "id": "function_definition",
            "question": "Как определить функцию в Python?",
            "options": [
                "function my_func():",
                "def my_func():",
                "create function my_func():",
            ],
            "correct": 1,
            "topic": "Функции",
        },
    ],
    "hard": [
        {
            "id": "recursion_base",
            "question": "Что обязательно должно быть в рекурсивной функции?",
            "options": [
                "Бесконечный цикл",
                "Базовый случай, при котором рекурсия остановится",
                "Вызов random.randint",
            ],
            "correct": 1,
            "topic": "Рекурсия",
        },
        {
            "id": "list_comprehension",
            "question": "Как записать генератор списка для квадратов чисел от 0 до 4?",
            "options": [
                "[n^2 for n in range(5)]",
                "[n**2 for n in range(5)]",
                "(n**2 for n in range(5))",
            ],
            "correct": 1,
            "topic": "Генераторы списков",
        },
        {
            "id": "dict_methods",
            "question": "Как получить значение по ключу 'age' со значением по умолчанию 0 из словаря data?",
            "options": ["data['age'] or 0", "data.get('age', 0)", "data.age(0)"],
            "correct": 1,
            "topic": "Словари",
        },
    ],
}

TOPIC_RESOURCES: Dict[str, str] = {
    "Переменные и типы": "Повторить основы переменных: https://docs.python.org/3/tutorial/introduction.html#using-python-as-a-calculator",
    "Ввод-вывод": "Перечитать про функцию print: https://docs.python.org/3/library/functions.html#print",
    "Списки": "Изучить список операций со списками: https://docs.python.org/3/tutorial/datastructures.html",
    "Условия": "Практиковать ветвления if/elif/else: https://docs.python.org/3/tutorial/controlflow.html#if-statements",
    "Циклы": "Повторить циклы for и range: https://docs.python.org/3/tutorial/controlflow.html#for-statements",
    "Функции": "Посмотреть раздел про функции: https://docs.python.org/3/tutorial/controlflow.html#defining-functions",
    "Рекурсия": "Пройти гайд по рекурсии: https://realpython.com/python-recursion/",
    "Генераторы списков": "Разобраться с генераторами списков: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions",
    "Словари": "Повторить методы словарей: https://docs.python.org/3/tutorial/datastructures.html#dictionaries",
}

MAX_QUESTIONS = 6
TEACHER_CODE = os.getenv("TEACHER_CODE", "python")
DIFFICULTY_ORDER = {
    "easy": ["easy", "medium", "hard"],
    "medium": ["medium", "easy", "hard"],
    "hard": ["hard", "medium", "easy"],
}


def reset_session_state() -> None:
    session["attempt_id"] = None
    session["questions_asked"] = []
    session["difficulty"] = "easy"
    session["questions_answered"] = 0
    session["score"] = 0
    session["current_question_id"] = None


def choose_question(difficulty: str, asked: List[str]) -> Optional[Dict[str, object]]:
    for level in DIFFICULTY_ORDER.get(difficulty, ["easy", "medium", "hard"]):
        available = [q for q in QUESTIONS[level] if q["id"] not in asked]
        if available:
            question = random.choice(available).copy()
            question["difficulty_level"] = level
            return question
    return None


def find_question(question_id: str) -> Tuple[Optional[Dict[str, object]], Optional[str]]:
    for level, items in QUESTIONS.items():
        for q in items:
            if q["id"] == question_id:
                return q, level
    return None, None


def get_question_by_id(question_id: str) -> Optional[Dict[str, object]]:
    question, _ = find_question(question_id)
    return question


def record_attempt(student_name: str, group_name: str) -> int:
    started_at = datetime.utcnow().isoformat()
    with get_db_connection() as conn:
        cur = conn.execute(
            "INSERT INTO attempts(student_name, group_name, started_at) VALUES(?, ?, ?)",
            (student_name, group_name, started_at),
        )
        conn.commit()
        return cur.lastrowid


def update_attempt_summary(attempt_id: int, score: int, total_questions: int) -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE attempts
            SET score = ?, total_questions = ?, completed_at = ?
            WHERE id = ?
            """,
            (score, total_questions, datetime.utcnow().isoformat(), attempt_id),
        )
        conn.commit()


def record_response(
    attempt_id: int,
    question: Dict[str, object],
    difficulty: str,
    is_correct: bool,
    chosen_option: int,
) -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO responses(
                attempt_id, question_id, difficulty, topic, is_correct, chosen_option, correct_option
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                question["id"],
                difficulty,
                question["topic"],
                1 if is_correct else 0,
                chosen_option,
                question["correct"],
            ),
        )
        conn.commit()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        group_name = request.form.get("group_name", "").strip()
        if not student_name:
            error = "Пожалуйста, укажите имя."
            return render_template("home.html", error=error)

        attempt_id = record_attempt(student_name, group_name)
        reset_session_state()
        session["attempt_id"] = attempt_id
        return redirect(url_for("question"))

    reset_session_state()
    return render_template("home.html")


@app.route("/question", methods=["GET", "POST"])
def question():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return redirect(url_for("index"))

    if request.method == "POST":
        chosen_option = request.form.get("answer")
        question_id = request.form.get("question_id")
        adaptive_difficulty = session.get("difficulty", "easy")

        if chosen_option is None or question_id is None:
            return redirect(url_for("question"))

        chosen_option_int = int(chosen_option)
        current_question, question_level = find_question(question_id)
        if not current_question:
            return redirect(url_for("question"))

        is_correct = chosen_option_int == current_question["correct"]
        if is_correct:
            session["score"] = session.get("score", 0) + 1
            if session["difficulty"] == "easy":
                session["difficulty"] = "medium"
            elif session["difficulty"] == "medium":
                session["difficulty"] = "hard"
        else:
            if session["difficulty"] == "hard":
                session["difficulty"] = "medium"
            elif session["difficulty"] == "medium":
                session["difficulty"] = "easy"

        record_response(
            attempt_id,
            current_question,
            question_level or adaptive_difficulty,
            is_correct,
            chosen_option_int,
        )

        asked = session.get("questions_asked", [])
        asked.append(question_id)
        session["questions_asked"] = asked
        session["questions_answered"] = session.get("questions_answered", 0) + 1
        session["current_question_id"] = None

        if session["questions_answered"] >= MAX_QUESTIONS:
            update_attempt_summary(
                attempt_id,
                session.get("score", 0),
                session["questions_answered"],
            )
            return redirect(url_for("results"))

    asked = session.get("questions_asked", [])
    current_question_id = session.get("current_question_id")
    if current_question_id and current_question_id not in asked:
        question_data, level = find_question(current_question_id)
        if question_data:
            question_copy = question_data.copy()
            question_copy["difficulty_level"] = level
            return render_template("question.html", question=question_copy)
        session["current_question_id"] = None

    next_question = choose_question(session.get("difficulty", "easy"), asked)
    if not next_question:
        update_attempt_summary(attempt_id, session.get("score", 0), session.get("questions_answered", 0))
        session["current_question_id"] = None
        return redirect(url_for("results"))

    session["current_question_id"] = next_question["id"]
    return render_template("question.html", question=next_question)


@app.route("/results")
def results():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return redirect(url_for("index"))

    with get_db_connection() as conn:
        attempt_row = conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone()
        responses_rows = conn.execute(
            "SELECT * FROM responses WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchall()

    if attempt_row is None:
        return redirect(url_for("index"))

    attempt = dict(attempt_row)
    responses = [dict(row) for row in responses_rows]

    incorrect_topics = {
        row["topic"] for row in responses if not row["is_correct"]
    }
    recommendations = [TOPIC_RESOURCES[topic] for topic in sorted(incorrect_topics)]

    if attempt["total_questions"] == 0:
        update_attempt_summary(
            attempt_id,
            session.get("score", 0),
            session.get("questions_answered", 0),
        )
        attempt["total_questions"] = session.get("questions_answered", 0)
        attempt["score"] = session.get("score", 0)
    return render_template(
        "results.html",
        attempt=attempt,
        responses=responses,
        recommendations=recommendations,
    )


@app.route("/teacher", methods=["GET", "POST"])
def teacher_dashboard():
    code = request.values.get("code")
    if code != TEACHER_CODE:
        error = "" if code is None else "Неверный код доступа."
        return render_template("teacher_login.html", error=error)

    with get_db_connection() as conn:
        attempts_rows = conn.execute(
            """
            SELECT id, student_name, group_name, score, total_questions, started_at, completed_at
            FROM attempts
            ORDER BY started_at DESC
            """
        ).fetchall()

    attempts = [dict(row) for row in attempts_rows]

    return render_template("teacher_dashboard.html", attempts=attempts, code=code)


@app.route("/teacher/attempt/<int:attempt_id>")
def teacher_attempt_detail(attempt_id: int):
    code = request.values.get("code")
    if code != TEACHER_CODE:
        return redirect(url_for("teacher_dashboard"))

    with get_db_connection() as conn:
        attempt_row = conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone()
        responses_rows = conn.execute(
            "SELECT * FROM responses WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchall()

    if attempt_row is None:
        return redirect(url_for("teacher_dashboard", code=code))

    return render_template(
        "teacher_attempt_detail.html",
        attempt=dict(attempt_row),
        responses=[dict(row) for row in responses_rows],
        code=code,
    )


@app.context_processor
def inject_globals():
    return {
        "max_questions": MAX_QUESTIONS,
        "QUESTIONS": QUESTIONS,
        "get_question": get_question_by_id,
    }


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
