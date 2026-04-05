from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
import config
import os
from datetime import datetime, timedelta
import secrets
import threading

from backend.pdf_reader import read_pdf
from backend.ocr import read_image
from backend.ai_engine import ask_ai
from backend.quiz_generator import generate_quiz
from backend.flashcards import generate_flashcards
from backend.planner import create_plan
from backend.helpers import save_file
from backend.db_manager import (
    init_db, add_user, verify_user, get_user_by_id, get_user_by_email,
    save_study_session, get_user_history, get_session_by_id,
    update_user_reset_token, verify_reset_token, update_password
)

app = Flask(__name__, template_folder='template')
app.secret_key = config.SECRET_KEY

# Mail Configuration
app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

mail = Mail(app)

# Initialize Database
init_db()

# Configure Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Mail delivery failed: {str(e)}")

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    summary = ""
    quiz = ""
    flashcards = ""
    plan = ""
    error = ""

    if request.method == "POST":
        notes = request.form.get("notes")
        file = request.files.get("file")
        text = ""

        if notes:
            text += notes
        if file:
            path = save_file(file)
            if file.filename.lower().endswith(".pdf"):
                text += read_pdf(path)
            elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                text += read_image(path)

        if text:
            try:
                summary = ask_ai(f"Summarize these notes:\n{text}")
                quiz = generate_quiz(text)
                flashcards = generate_flashcards(text)
                plan = create_plan(text)
                
                # Save to History
                title = (notes[:30] + "...") if notes else (file.filename if file else "New Session")
                save_study_session(
                    current_user.id, title, text, summary, quiz, flashcards, plan
                )
                flash("Study guide generated and saved to history!", "success")
            except Exception as e:
                error = f"AI Error: {str(e)}"
        else:
            error = "Please provide some notes or upload a file."

    return render_template("index.html",
        summary=summary,
        quiz=quiz,
        flashcards=flashcards,
        plan=plan,
        error=error
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_data = verify_user(username, password)
        
        if user_data:
            user = User(user_data)
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "error")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
        elif add_user(username, email, password):
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username or Email already exists.", "error")
            
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = get_user_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            expiry = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            update_user_reset_token(email, token, expiry)
            
            # Send Real Email
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(
                "Password Reset Request - Smart Study Assistant",
                recipients=[email]
            )
            msg.body = f"""Hello {user['username']},

To reset your password, please click the following link:
{reset_url}

If you did not make this request, simply ignore this email and no changes will be made.
This link will expire in 1 hour.

Regards,
Smart Study Assistant Team
"""
            # Send in background thread
            threading.Thread(target=send_async_email, args=(app, msg)).start()
            
            flash("A recovery link has been sent to your email address.", "success")
            return redirect(url_for('login'))
        else:
            flash("If an account exists for that email, a recovery link has been sent.", "success") # Security: don't reveal email presence
            
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash("Invalid or expired reset token.", "error")
        return redirect(url_for('forgot_password'))
        
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            update_password(user['id'], password)
            flash("Password updated successfully! Please login.", "success")
            return redirect(url_for('login'))
            
    return render_template("reset_password.html", token=token)

@app.route("/history")
@login_required
def history():
    user_history = get_user_history(current_user.id)
    return render_template("history.html", history=user_history)

@app.route("/history/<int:session_id>")
@login_required
def view_session(session_id):
    session = get_session_by_id(session_id, current_user.id)
    if session:
        return render_template("index.html",
            summary=session['summary'],
            quiz=session['quiz'],
            flashcards=session['flashcards'],
            plan=session['plan'],
            restored=True
        )
    flash("Session not found.", "error")
    return redirect(url_for('history'))

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)