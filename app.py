import hmac
import os
import secrets
import time
from functools import wraps
from threading import Lock
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.ai_engine import AIEngine
from models.safety_checker import SafetyChecker
from utils.chemical_loader import load_all_chemicals
from utils.file_handler import add_history, get_history, load_json, update_history
from utils.gemini_usage import get_usage

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

ai = AIEngine()
safety_checker = SafetyChecker()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
ADMIN_RESET_TOKEN = os.environ.get("ADMIN_RESET_TOKEN", "").strip()
ADMIN_CONFIGURED = bool(ADMIN_USERNAME and ADMIN_PASSWORD_HASH)

# Lightweight development protection against repeated admin password guesses.
# For a public production deployment, put a real rate limiter/reverse proxy in front.
_admin_attempts = {}
_admin_attempts_lock = Lock()
ADMIN_MAX_ATTEMPTS = 5
ADMIN_LOCKOUT_SECONDS = 300
RESET_MAX_ATTEMPTS = 5
RESET_LOCKOUT_SECONDS = 300
_reset_attempts = {}
_reset_attempts_lock = Lock()


def _visitor_id():
    """Create a stable anonymous browser-session identifier for user history."""
    session.permanent = True
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = secrets.token_hex(12)
        session["visitor_id"] = visitor_id
    return visitor_id


def _history_actor():
    """Return the server-controlled actor identity for a new history record."""
    if session.get("admin_authenticated") is True:
        return "admin", "admin", "Admin"

    visitor_id = _visitor_id()
    return "user", visitor_id, "User"


def _csrf_token():
    token = session.get("admin_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["admin_csrf_token"] = token
    return token


def _valid_csrf(token):
    expected = session.get("admin_csrf_token", "")
    return bool(token) and bool(expected) and hmac.compare_digest(str(token), str(expected))


def _admin_rate_limited(client_key):
    now = time.monotonic()
    with _admin_attempts_lock:
        entry = _admin_attempts.get(client_key)
        if not entry:
            return False
        failures, locked_until = entry
        if locked_until <= now:
            _admin_attempts.pop(client_key, None)
            return False
        return failures >= ADMIN_MAX_ATTEMPTS


def _record_admin_failure(client_key):
    now = time.monotonic()
    with _admin_attempts_lock:
        failures, _ = _admin_attempts.get(client_key, (0, 0))
        failures += 1
        locked_until = now + ADMIN_LOCKOUT_SECONDS if failures >= ADMIN_MAX_ATTEMPTS else 0
        _admin_attempts[client_key] = (failures, locked_until)


def _clear_admin_failures(client_key):
    with _admin_attempts_lock:
        _admin_attempts.pop(client_key, None)


def _reset_rate_limited(client_key):
    now = time.monotonic()
    with _reset_attempts_lock:
        entry = _reset_attempts.get(client_key)
        if not entry:
            return False
        failures, locked_until = entry
        if locked_until <= now:
            _reset_attempts.pop(client_key, None)
            return False
        return failures >= RESET_MAX_ATTEMPTS


def _record_reset_failure(client_key):
    now = time.monotonic()
    with _reset_attempts_lock:
        failures, _ = _reset_attempts.get(client_key, (0, 0))
        failures += 1
        locked_until = now + RESET_LOCKOUT_SECONDS if failures >= RESET_MAX_ATTEMPTS else 0
        _reset_attempts[client_key] = (failures, locked_until)


def _clear_reset_failures(client_key):
    with _reset_attempts_lock:
        _reset_attempts.pop(client_key, None)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("admin_authenticated") is not True:
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_admin_state():
    return {
        "admin_authenticated": session.get("admin_authenticated") is True,
    }


@app.route("/")
def splash():
    return render_template("splash.html")


@app.route("/dashboard")
def dashboard():
    experiments = load_json("experiments.json")
    chemicals = load_all_chemicals()
    safety = load_json("safety_rules.json")
    history = get_history(actor_id=_visitor_id())

    green_count = sum(1 for chemical in chemicals if chemical.get("green_alternative"))

    return render_template(
        "dashboard.html",
        experiments_count=len(experiments),
        green_count=green_count,
        chemicals_count=len(chemicals),
        safety_count=len(safety),
        history_count=len(history),
    )


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    question = ""
    answer = ""
    actor_type, actor_id, actor_label = _history_actor()

    if request.method == "POST":
        question = request.form.get("question", "").strip()

        if question:
            history_id = add_history(
                "AI Assistant",
                f'Asked: "{question}"',
                history_type="ai_question",
                status="pending",
                status_message="",
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )

            try:
                answer = ai.get_response(question)
                success = bool(answer and not str(answer).lstrip().startswith("⚠️"))
                update_history(
                    history_id,
                    "success" if success else "error",
                    "The Respond is Given" if success else "The Respond is Getting Error",
                )
            except Exception:
                update_history(history_id, "error", "The Respond is Getting Error")
                answer = "⚠️ Chemai is temporarily unavailable. Please try again in a moment."

    return render_template("chatbot.html", question=question, answer=answer)


@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    question = request.form.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please enter a question."})

    actor_type, actor_id, actor_label = _history_actor()
    history_id = add_history(
        "AI Assistant",
        f'Asked: "{question}"',
        history_type="ai_question",
        status="pending",
        status_message="",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
    )

    try:
        answer = ai.get_response(question)
        success = bool(answer and not str(answer).lstrip().startswith("⚠️"))
        update_history(
            history_id,
            "success" if success else "error",
            "The Respond is Given" if success else "The Respond is Getting Error",
        )
    except Exception:
        update_history(history_id, "error", "The Respond is Getting Error")
        answer = "⚠️ Chemai is temporarily unavailable. Please try again in a moment."

    return jsonify({"answer": answer})


@app.route("/ask_ai_stream", methods=["POST"])
def ask_ai_stream():
    question = request.form.get("question", "").strip()

    if not question:
        return Response("Please enter a question.", mimetype="text/plain")

    actor_type, actor_id, actor_label = _history_actor()
    history_id = add_history(
        "AI Assistant",
        f'Asked: "{question}"',
        history_type="ai_question",
        status="pending",
        status_message="",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
    )

    def generate():
        answer = ""
        try:
            for chunk in ai.get_response_stream(question):
                answer += chunk
                yield chunk

            success = bool(answer.strip()) and not answer.lstrip().startswith("⚠️")
            update_history(
                history_id,
                "success" if success else "error",
                "The Respond is Given" if success else "The Respond is Getting Error",
            )

        except Exception:
            update_history(history_id, "error", "The Respond is Getting Error")
            raise

    return Response(generate(), mimetype="text/plain")


@app.route("/add_history", methods=["POST"])
def add_history_route():
    """Record calculator usage with server-controlled actor/status fields."""
    module = request.form.get("module", "").strip()
    activity = request.form.get("activity", "").strip()

    # This endpoint exists for the current calculator's client-side logging.
    # Do not allow callers to choose actor identity or fabricate error/success states.
    if module != "Chemical Calculator" or not activity or len(activity) > 500:
        return jsonify({"status": "error", "message": "Invalid history activity."}), 400

    actor_type, actor_id, actor_label = _history_actor()
    add_history(
        module,
        activity,
        history_type="calculation",
        status="success",
        status_message="Calculation Completed",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
    )

    return jsonify({"status": "success"})


@app.route("/experiment")
def experiment():
    experiments = load_json("experiments.json")
    return render_template("experiment.html", experiments=experiments)


@app.route("/experiment/<int:experiment_id>")
def experiment_details(experiment_id):
    experiments = load_json("experiments.json")
    selected_experiment = next(
        (experiment for experiment in experiments if experiment["id"] == experiment_id),
        None,
    )

    if selected_experiment:
        actor_type, actor_id, actor_label = _history_actor()
        add_history(
            "Experiment Guide",
            f'Opened: {selected_experiment["name"]}',
            history_type="opened",
            status="not_applicable",
            status_message="Opened",
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
        )

    return render_template("experiment_details.html", experiment=selected_experiment)


@app.route("/recommendation")
def recommendation():
    chemicals = load_all_chemicals()
    return render_template("recommendation.html", chemicals=chemicals)


@app.route("/recommendation/<int:index>")
def recommendation_details(index):
    chemicals = load_all_chemicals()

    if index < 0 or index >= len(chemicals):
        return "Chemical not found", 404

    chemical = chemicals[index]
    actor_type, actor_id, actor_label = _history_actor()
    add_history(
        "Green Recommendations",
        f'Opened Recommendation: {chemical["name"]}',
        history_type="opened",
        status="not_applicable",
        status_message="Opened",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
    )

    return render_template("recommendation_details.html", chemical=chemical)


@app.route("/safety")
def safety():
    chemicals = load_all_chemicals()
    safety_rules = safety_checker.get_all_rules()
    return render_template("safety.html", chemicals=chemicals, safety_rules=safety_rules)


@app.route("/safety/<int:index>")
def safety_details(index):
    chemicals = load_all_chemicals()

    if index < 0 or index >= len(chemicals):
        return "Chemical not found", 404

    chemical = chemicals[index]
    actor_type, actor_id, actor_label = _history_actor()
    add_history(
        "Safety Checker",
        f'Opened Safety: {chemical["name"]}',
        history_type="opened",
        status="not_applicable",
        status_message="Opened",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
    )

    return render_template("safety_details.html", chemical=chemical)


@app.route("/safety-rule/<int:rule_id>")
def safety_rule_details(rule_id):
    rule = safety_checker.get_rule_by_id(rule_id)

    if not rule:
        return "Safety rule not found", 404

    actor_type, actor_id, actor_label = _history_actor()
    add_history(
        "Laboratory Safety",
        f'Opened Rule: {rule["title"]}',
        history_type="opened",
        status="not_applicable",
        status_message="Opened",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
    )

    return render_template("safety_rule_details.html", rule=rule)


@app.route("/calculator")
def calculator():
    return render_template("calculator.html")


@app.route("/history")
def history():
    history_data = get_history(actor_id=_visitor_id())
    return render_template("history.html", history=history_data)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_authenticated") is True:
        return redirect(url_for("admin_dashboard"))

    next_url = request.args.get("next", "")

    if request.method == "POST":
        if not _valid_csrf(request.form.get("csrf_token")):
            return "Invalid security token.", 400

        if not ADMIN_CONFIGURED:
            flash("Admin access is not configured yet. Run setup_admin.py first.", "error")
            return render_template("admin_login.html", csrf_token=_csrf_token()), 503

        client_key = request.remote_addr or "unknown"
        if _admin_rate_limited(client_key):
            flash("Too many failed login attempts. Please try again in a few minutes.", "error")
            return render_template("admin_login.html", csrf_token=_csrf_token()), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        valid_username = hmac.compare_digest(username, ADMIN_USERNAME)
        valid_password = check_password_hash(ADMIN_PASSWORD_HASH, password) if password else False

        if valid_username and valid_password:
            _clear_admin_failures(client_key)
            session.clear()
            session.permanent = True
            session["admin_authenticated"] = True
            session["admin_csrf_token"] = secrets.token_urlsafe(32)
            session["visitor_id"] = secrets.token_hex(12)
            return redirect(next_url if next_url.startswith("/admin/") else url_for("admin_dashboard"))

        _record_admin_failure(client_key)
        flash("Invalid admin credentials.", "error")

    return render_template("admin_login.html", csrf_token=_csrf_token())


@app.route("/admin/forgot-password", methods=["GET", "POST"])
def admin_forgot_password():
    if session.get("admin_authenticated") is True:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        if not _valid_csrf(request.form.get("csrf_token")):
            return "Invalid security token.", 400

        client_key = request.remote_addr or "unknown"
        if _reset_rate_limited(client_key):
            flash("Too many reset attempts. Please try again in a few minutes.", "error")
            return render_template("admin_forgot_password.html", csrf_token=_csrf_token()), 429

        if not ADMIN_CONFIGURED or not ADMIN_RESET_TOKEN:
            flash("Password recovery is not configured. Run setup_admin.py to create a recovery key.", "error")
            return render_template("admin_forgot_password.html", csrf_token=_csrf_token()), 503

        username = request.form.get("username", "").strip()
        recovery_key = request.form.get("recovery_key", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        valid_username = hmac.compare_digest(username, ADMIN_USERNAME)
        valid_recovery_key = hmac.compare_digest(recovery_key, ADMIN_RESET_TOKEN)

        if not (valid_username and valid_recovery_key):
            _record_reset_failure(client_key)
            flash("Invalid admin ID or recovery key.", "error")
            return render_template("admin_forgot_password.html", csrf_token=_csrf_token())

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "error")
            return render_template("admin_forgot_password.html", csrf_token=_csrf_token())

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("admin_forgot_password.html", csrf_token=_csrf_token())

        # The password hash is stored in the environment file, never in the browser.
        from dotenv import set_key
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        set_key(env_file, "ADMIN_PASSWORD_HASH", generate_password_hash(new_password, method="scrypt"))

        # Keep the in-process value synchronized until the application is restarted.
        global ADMIN_PASSWORD_HASH
        ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
        # set_key updates the file, not os.environ; reload the value explicitly.
        from dotenv import dotenv_values
        ADMIN_PASSWORD_HASH = dotenv_values(env_file).get("ADMIN_PASSWORD_HASH", "") or ""

        _clear_reset_failures(client_key)
        _clear_admin_failures(client_key)
        session.clear()
        flash("Admin password reset successfully. You can now log in with your new password.", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin_forgot_password.html", csrf_token=_csrf_token())


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    if not _valid_csrf(request.form.get("csrf_token")):
        return "Invalid security token.", 400

    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    history_data = get_history()
    response_count = sum(1 for item in history_data if item.get("status") == "success")
    error_count = sum(
        1
        for item in history_data
        if item.get("status") in {"error", "pending", "legacy_unknown"}
    )

    ai_usage = get_usage()
    ai_status = "Available" if ai_usage.get("last_status") in {"never", "success"} else "Last request failed"
    if ai_usage.get("last_status") == "never":
        ai_status_class = "neutral"
    elif ai_usage.get("last_status") == "success":
        ai_status_class = "success"
    else:
        ai_status_class = "error"

    return render_template(
        "admin_dashboard.html",
        total_count=len(history_data),
        response_count=response_count,
        error_count=error_count,
        ai_usage=ai_usage,
        ai_status=ai_status,
        ai_status_class=ai_status_class,
        csrf_token=_csrf_token(),
    )


@app.route("/admin/history")
@admin_required
def admin_history():
    filter_name = request.args.get("filter", "all").lower()
    allowed_filters = {"all", "responded", "not_responded"}
    if filter_name not in allowed_filters:
        filter_name = "all"

    status_filter = None if filter_name == "all" else filter_name
    history_data = get_history(status_filter=status_filter)

    return render_template(
        "admin_history.html",
        history=history_data,
        active_filter=filter_name,
        csrf_token=_csrf_token(),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
