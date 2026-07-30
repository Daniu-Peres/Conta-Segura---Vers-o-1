import os
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'
import sqlite3
from flask import Flask, render_template
from flask_assets import Bundle, Environment
from werkzeug.security import generate_password_hash
from database import criar_banco, conectar
from utils import brl_format, limiter
from routes.auth import auth_bp, oauth
from routes.dashboard import dashboard_bp
from routes.api import api_bp



def load_secret_key():
    configured_secret = os.getenv("SECRET_KEY")
    if configured_secret:
        return configured_secret

    os.makedirs("instance", exist_ok=True)
    secret_path = os.path.join("instance", "secret.key")

    if os.path.exists(secret_path):
        with open(secret_path, "r", encoding="utf-8") as secret_file:
            return secret_file.read().strip()

    generated_secret = os.urandom(32).hex()
    with open(secret_path, "w", encoding="utf-8") as secret_file:
        secret_file.write(generated_secret)

    return generated_secret


app = Flask(__name__)
app.secret_key = load_secret_key()
oauth.init_app(app)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
)

limiter.init_app(app)

criar_banco()

app.template_filter('brl')(brl_format)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)

assets = Environment(app)
assets.config['ASSETS_DEBUG'] = True

css_bundle = Bundle(
    'css/base.css',
    'css/layout.css',
    'css/components.css',
    'css/pages.css',
    filters='cssmin',
    output='css/style.min.css'
)

assets.register('main_css', css_bundle)

@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/contato")
def contato():
    return render_template("contato.html")


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("login.html"), 429

if __name__ == "__main__":
    if os.getenv("SEED_DEFAULT_ADMIN") == "1":
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                    ("Administrador", "admin@admin.com", generate_password_hash("123")),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            pass

    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
