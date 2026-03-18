from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "segredo123"

def conectar():
    return sqlite3.connect("banco.db", check_same_thread=False)

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lancamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT NOT NULL,
        usuario_id INTEGER,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)

    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nome = request.form["nome"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE nome=? AND senha=?", (nome, senha))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["usuario_id"] = user[0]
            session["nome"] = user[1]
            return redirect("/dashboard")
        else:
            return "Login inválido"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect("/")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, descricao, valor, tipo 
    FROM lancamentos 
    WHERE usuario_id=?
    """, (session["usuario_id"],))

    dados = cursor.fetchall()

    cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo='receita' AND usuario_id=?", (session["usuario_id"],))
    receitas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo='despesa' AND usuario_id=?", (session["usuario_id"],))
    despesas = cursor.fetchone()[0] or 0

    saldo = receitas - despesas

    conn.close()

    return render_template("dashboard.html", dados=dados, saldo=saldo, nome=session["nome"])

@app.route("/add", methods=["POST"])
def add():
    if "usuario_id" not in session:
        return redirect("/")

    descricao = request.form["descricao"]
    valor = request.form["valor"]
    tipo = request.form["tipo"]

    if not descricao or not valor:
        return "Preencha os campos!"

    if float(valor) <= 0:
        return "Valor deve ser maior que zero"

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO lancamentos (descricao, valor, tipo, usuario_id) VALUES (?, ?, ?, ?)",
        (descricao, valor, tipo, session["usuario_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "usuario_id" not in session:
        return redirect("/")

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        descricao = request.form["descricao"]
        valor = request.form["valor"]
        tipo = request.form["tipo"]

        cursor.execute(
            "UPDATE lancamentos SET descricao=?, valor=?, tipo=? WHERE id=? AND usuario_id=?",
            (descricao, valor, tipo, id, session["usuario_id"])
        )

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    cursor.execute("SELECT * FROM lancamentos WHERE id=? AND usuario_id=?", (id, session["usuario_id"]))
    dado = cursor.fetchone()
    conn.close()

    if not dado:
        return "Registro não encontrado"

    return render_template("edit.html", dado=dado)

@app.route("/delete/<int:id>")
def delete(id):
    if "usuario_id" not in session:
        return redirect("/")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM lancamentos WHERE id=? AND usuario_id=?", (id, session["usuario_id"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    criar_banco()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO usuarios (id, nome, senha) VALUES (1, 'admin', '123')")
    
    conn.commit()
    conn.close()

    app.run(debug=True)