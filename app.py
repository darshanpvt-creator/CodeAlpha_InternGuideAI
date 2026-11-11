import json
import os
import uuid
import hmac
from functools import wraps

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS

from chatbot.matcher import FAQMatcher
from database.db import (
    init_db,
    save_message,
    get_messages,
    save_feedback,
    save_unanswered_question,
    get_connection
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
    "SESSION_COOKIE_SECURE", "0"
) == "1"
CORS(app)


def admin_required(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if not app.config.get("SECRET_KEY") or not os.environ.get("ADMIN_PASSWORD"):
            return jsonify({
                "error": "Admin authentication is not configured."
            }), 503

        if not session.get("is_admin"):
            if request.path == "/admin":
                return redirect(url_for("admin_login"))
            return jsonify({"error": "Authentication required."}), 401

        return view_function(*args, **kwargs)

    return wrapped

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAQ_PATH = os.path.join(BASE_DIR, "data", "faqs.json")

with open(FAQ_PATH, "r", encoding="utf-8") as file:
    faqs = json.load(file)

matcher = FAQMatcher(faqs)
def reload_faqs():
    global faqs, matcher

    with open(FAQ_PATH, "r", encoding="utf-8") as file:
        updated_faqs = json.load(file)

    updated_matcher = FAQMatcher(updated_faqs)

    faqs = updated_faqs
    matcher = updated_matcher

    return len(faqs)

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "InternGuide AI backend is running!",
        "faq_count": len(faqs)
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Please send a valid JSON request."}), 400

        question = data.get("question", "")
        conversation_id = data.get("conversation_id")

        if not isinstance(question, str) or not question.strip():
            return jsonify({"error": "Please enter a valid question."}), 400

        if len(question) > 500:
            return jsonify({
                "error": "Question is too long. Maximum 500 characters."
            }), 400

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        else:
            try:
                conversation_id = str(uuid.UUID(conversation_id))
            except (ValueError, TypeError, AttributeError):
                return jsonify({"error": "Invalid conversation ID."}), 400

        clean_question = question.strip()
        result = matcher.find_answer(clean_question)

        if not result["matched"]:
            save_unanswered_question(
                conversation_id,
                clean_question,
                result["confidence"]
            )

        save_message(conversation_id, "user", clean_question)

        message_id = save_message(
            conversation_id,
            "assistant",
            result["answer"]
        )

        return jsonify({
            "status": "success",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "question": clean_question,
            "matched": result["matched"],
            "answer": result["answer"],
            "confidence": result["confidence"],
            "category": result.get("category"),
            "matched_question": result.get("matched_question")
        }), 200

    except Exception:
        app.logger.exception("Chat endpoint failed")
        return jsonify({
            "error": "Something went wrong while processing your question."
        }), 500


@app.route("/api/history/<conversation_id>", methods=["GET"])
def conversation_history(conversation_id):
    try:
        conversation_id = str(uuid.UUID(conversation_id))
    except (ValueError, TypeError, AttributeError):
        return jsonify({"error": "Invalid conversation ID."}), 400

    messages = get_messages(conversation_id)

    return jsonify({
        "status": "success",
        "conversation_id": conversation_id,
        "messages": messages
    }), 200


@app.route("/api/feedback", methods=["POST"])
def feedback():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Please send valid JSON."}), 400

        conversation_id = data.get("conversation_id")
        message_id = data.get("message_id")
        rating = data.get("rating")

        try:
            conversation_id = str(uuid.UUID(conversation_id))
        except (ValueError, TypeError, AttributeError):
            return jsonify({"error": "Invalid conversation ID."}), 400

        if rating not in ("helpful", "not_helpful"):
            return jsonify({"error": "Invalid feedback rating."}), 400

        if (
            isinstance(message_id, bool)
            or not isinstance(message_id, int)
            or message_id <= 0
        ):
            return jsonify({"error": "A valid message ID is required."}), 400

        with get_connection() as connection:
            message = connection.execute(
                """
                SELECT id FROM messages
                WHERE id = ? AND conversation_id = ?
                AND role = 'assistant'
                """,
                (message_id, conversation_id)
            ).fetchone()

        if message is None:
            return jsonify({"error": "Assistant message not found."}), 404

        save_feedback(conversation_id, message_id, rating)

        return jsonify({
            "status": "success",
            "message": "Thank you for your feedback!"
        }), 201

    except Exception:
        app.logger.exception("Feedback endpoint failed")
        return jsonify({
            "error": "Unable to save feedback."
        }), 500



@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    try:
        with get_connection() as connection:
            rows = connection.execute("""
                SELECT
                    c.id,
                    c.created_at,
                    COALESCE(
                        (SELECT content FROM messages
                         WHERE conversation_id = c.id
                         AND role = 'user'
                         ORDER BY id ASC LIMIT 1),
                        'New conversation'
                    ) AS title,
                    COALESCE(
                        (SELECT content FROM messages
                         WHERE conversation_id = c.id
                         ORDER BY id DESC LIMIT 1),
                        ''
                    ) AS last_message,
                    (SELECT created_at FROM messages
                     WHERE conversation_id = c.id
                     ORDER BY id DESC LIMIT 1) AS updated_at,
                    (SELECT COUNT(*) FROM messages
                     WHERE conversation_id = c.id) AS message_count
                FROM conversations c
                WHERE EXISTS (
                    SELECT 1 FROM messages
                    WHERE conversation_id = c.id
                )
                ORDER BY (
                    SELECT MAX(id) FROM messages
                    WHERE conversation_id = c.id
                ) DESC
                LIMIT 50
            """).fetchall()

        return jsonify({
            "status": "success",
            "conversations": [dict(row) for row in rows]
        }), 200

    except Exception:
        app.logger.exception("Unable to retrieve conversations.")
        return jsonify({
            "status": "error",
            "error": "Unable to retrieve conversations."
        }), 500



@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not app.config.get("SECRET_KEY") or not admin_password:
        return "Admin authentication is not configured.", 503

    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        submitted_password = request.form.get("password", "")

        if hmac.compare_digest(submitted_password, admin_password):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        return render_template(
            "admin_login.html",
            error="Incorrect password. Please try again."
        ), 401

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    try:
        with get_connection() as connection:
            total_conversations = connection.execute(
                "SELECT COUNT(*) AS total FROM conversations"
            ).fetchone()["total"]

            total_messages = connection.execute(
                "SELECT COUNT(*) AS total FROM messages"
            ).fetchone()["total"]

            total_unanswered = connection.execute(
                "SELECT COUNT(*) AS total FROM unanswered_questions"
            ).fetchone()["total"]

            feedback_counts = connection.execute("""
                SELECT rating, COUNT(*) AS total
                FROM feedback
                GROUP BY rating
            """).fetchall()

            feedback = {
                "helpful": 0,
                "not_helpful": 0
            }

            for row in feedback_counts:
                feedback[row["rating"]] = row["total"]

            total_feedback = feedback["helpful"] + feedback["not_helpful"]

            helpful_rate = (
                round(feedback["helpful"] / total_feedback * 100, 2)
                if total_feedback else 0
            )

            top_questions = connection.execute("""
                SELECT content, COUNT(*) AS frequency
                FROM messages
                WHERE role = 'user'
                GROUP BY content
                ORDER BY frequency DESC
                LIMIT 5
            """).fetchall()

        return jsonify({
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_unanswered": total_unanswered,
            "feedback": feedback,
            "helpful_rate": helpful_rate,
            "top_questions": [
                {
                    "question": row["content"],
                    "frequency": row["frequency"]
                }
                for row in top_questions
            ]
        }), 200

    except Exception:
        app.logger.exception("Admin statistics endpoint failed")
        return jsonify({
            "error": "Unable to retrieve admin statistics."
        }), 500

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html")


@app.route("/api/admin/unanswered", methods=["GET"])
@admin_required
def admin_unanswered():
    from database.db import get_connection

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, question, confidence, created_at
            FROM unanswered_questions
            ORDER BY id DESC
        """).fetchall()

    return jsonify({
        "total": len(rows),
        "questions": [dict(row) for row in rows]
    })




@app.route("/api/admin/faqs", methods=["POST"])
@admin_required
def add_faq():
    global faqs

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Please send valid JSON."}), 400

        category = data.get("category")
        question = data.get("question")
        answer = data.get("answer")
        variations = data.get("variations", [])
        tags = data.get("tags", [])

        if not all(isinstance(value, str) and value.strip()
                   for value in [category, question, answer]):
            return jsonify({
                "error": "Category, question and answer are required."
            }), 400

        if not isinstance(variations, list) or not all(
            isinstance(item, str) for item in variations
        ):
            return jsonify({"error": "Variations must be a list of strings."}), 400

        if not isinstance(tags, list) or not all(
            isinstance(item, str) for item in tags
        ):
            return jsonify({"error": "Tags must be a list of strings."}), 400

        if any(faq["question"].strip().lower() == question.strip().lower()
               for faq in faqs):
            return jsonify({"error": "This FAQ question already exists."}), 409

        new_faq = {
            "id": max((faq["id"] for faq in faqs), default=0) + 1,
            "category": category.strip(),
            "question": question.strip(),
            "variations": [item.strip() for item in variations if item.strip()],
            "answer": answer.strip(),
            "tags": [item.strip() for item in tags if item.strip()]
        }

        updated_faqs = faqs + [new_faq]

        with open(FAQ_PATH, "w", encoding="utf-8") as file:
            json.dump(updated_faqs, file, indent=2, ensure_ascii=False)

        try:
            reload_faqs()
        except Exception:
            app.logger.exception("FAQ reload failed")
            with open(FAQ_PATH, "w", encoding="utf-8") as file:
                json.dump(faqs, file, indent=2, ensure_ascii=False)
            return jsonify({"error": "FAQ could not be loaded. Previous data restored."}), 500

        return jsonify({
            "status": "success",
            "message": "FAQ added successfully.",
            "faq": new_faq,
            "total_faqs": len(faqs)
        }), 201

    except Exception:
        app.logger.exception("Add FAQ endpoint failed")
        return jsonify({"error": "Unable to add FAQ."}), 500


@app.route("/api/admin/faqs", methods=["GET"])
@admin_required
def list_faqs():
    return jsonify({
        "total": len(faqs),
        "faqs": faqs
    }), 200


@app.route("/api/admin/faqs/<int:faq_id>", methods=["DELETE"])
@admin_required
def delete_faq(faq_id):
    global faqs

    existing_faq = next(
        (faq for faq in faqs if faq["id"] == faq_id),
        None
    )

    if existing_faq is None:
        return jsonify({"error": "FAQ not found."}), 404

    updated_faqs = [
        faq for faq in faqs if faq["id"] != faq_id
    ]

    try:
        with open(FAQ_PATH, "w", encoding="utf-8") as file:
            json.dump(updated_faqs, file, indent=2, ensure_ascii=False)

        try:
            reload_faqs()
        except Exception:
            with open(FAQ_PATH, "w", encoding="utf-8") as file:
                json.dump(faqs, file, indent=2, ensure_ascii=False)

            return jsonify({
                "error": "FAQ deletion failed. Previous data restored."
            }), 500

        return jsonify({
            "status": "success",
            "message": "FAQ deleted successfully.",
            "deleted_faq": existing_faq,
            "total_faqs": len(faqs)
        }), 200

    except Exception:
        app.logger.exception("Delete FAQ endpoint failed")
        return jsonify({"error": "Unable to delete FAQ."}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )

