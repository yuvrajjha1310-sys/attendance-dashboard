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

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
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
        session["user"] = request.form["username"]
        return redirect("/dashboard")
    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html", user=session["user"])

# ================= SAVE =================
@app.route("/save", methods=["POST"])
def save():
    if "user" not in session:
        return jsonify({"success": False, "error": "Not logged in"})

    try:
        data = request.json
        date = data["date"]
        semester = data["semester"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        for index, status in data["data"].items():

            subject = get_subject_by_index(int(index))

            # delete old
            c.execute("""
            DELETE FROM attendance
            WHERE user=? AND subject=? AND date=? AND semester=?
            """, (session["user"], subject, date, semester))

            # insert new
            c.execute("""
            INSERT INTO attendance (user, subject, date, status, semester)
            VALUES (?, ?, ?, ?, ?)
            """, (session["user"], subject, date, status, semester))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False, "error": str(e)})

# ================= SUBJECT MAP =================
def get_subject_by_index(i):
    subjects = [
        "Introduction to Data Science",
        "Digital Marketing",
        "Software Testing",
        "Operating System",
        "Logical & Critical Thinking",
        "Cyber Laws"
    ]
    return subjects[i] if i < len(subjects) else "Unknown"

# ================= STATS =================
@app.route("/stats")
def stats():
    semester = request.args.get("semester")
    user = session.get("user")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT COUNT(DISTINCT date) FROM attendance
    WHERE user=? AND semester=?
    """, (user, semester))
    total_days = c.fetchone()[0] or 0

    c.execute("""
    SELECT COUNT(*) FROM attendance
    WHERE user=? AND semester=? AND status='P'
    """, (user, semester))
    present = c.fetchone()[0] or 0

    c.execute("""
    SELECT COUNT(*) FROM attendance
    WHERE user=? AND semester=? AND status='A'
    """, (user, semester))
    absent = c.fetchone()[0] or 0

    conn.close()

    total = present + absent
    percent = int((present / total) * 100) if total else 0

    return jsonify({
        "total_days": total_days,
        "present": present,
        "absent": absent,
        "percentage": percent
    })

# ================= ANALYTICS =================
@app.route("/analytics")
def analytics():
    semester = request.args.get("semester")
    user = session.get("user")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT subject,
           SUM(CASE WHEN status='P' THEN 1 ELSE 0 END),
           SUM(CASE WHEN status='A' THEN 1 ELSE 0 END)
    FROM attendance
    WHERE user=? AND semester=?
    GROUP BY subject
    """, (user, semester))

    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "subject": r[0],
            "present": r[1],
            "absent": r[2]
        })

    return jsonify(result)

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)