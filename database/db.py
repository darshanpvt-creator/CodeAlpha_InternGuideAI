import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / "internguide.db"


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                message_id INTEGER,
                rating TEXT NOT NULL CHECK(rating IN ('helpful', 'not_helpful')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS unanswered_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                question TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)


def save_message(conversation_id, role, content):
    if not conversation_id or role not in ("user", "assistant"):
        raise ValueError("Invalid conversation ID or message role.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Message content cannot be empty.")

    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO conversations (id) VALUES (?)",
            (conversation_id,)
        )

        cursor = connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content.strip())
        )

        return cursor.lastrowid


def get_messages(conversation_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

    return [dict(row) for row in rows]


def save_feedback(conversation_id, message_id, rating):
    if not conversation_id:
        raise ValueError("Conversation ID is required.")

    if rating not in ("helpful", "not_helpful"):
        raise ValueError("Invalid feedback rating.")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO feedback (conversation_id, message_id, rating)
            VALUES (?, ?, ?)
            """,
            (conversation_id, message_id, rating)
        )


def save_unanswered_question(conversation_id, question, confidence):
    if not conversation_id:
        raise ValueError("Conversation ID is required.")

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO conversations (id) VALUES (?)",
            (conversation_id,)
        )

        connection.execute(
            """
            INSERT INTO unanswered_questions
            (conversation_id, question, confidence)
            VALUES (?, ?, ?)
            """,
            (conversation_id, question.strip(), confidence)
        )


if __name__ == "__main__":
    init_db()
    print("InternGuide AI database initialized successfully!")
