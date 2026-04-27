from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

DB = "attendance.db"

# ================= DB INIT =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    # attendance table
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        subject TEXT,
        date TEXT,
        status TEXT,
        semester TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
    except:
        return "User already exists"

    conn.close()
    return redirect("/")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html", user=session["user"])


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)