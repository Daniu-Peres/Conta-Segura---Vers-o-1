from flask import session, flash, redirect
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def brl_format(valor):
    if valor is None:
        valor = 0
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login primeiro.", "warning")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated