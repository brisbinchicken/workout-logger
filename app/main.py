from flask import session
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import os, pathlib, datetime, pytz, sqlite3, openpyxl, io, bcrypt

DB_PATH = "/data/workouts.sqlite"
TIMEZONE = os.getenv("TIMEZONE","UTC")
tz = pytz.timezone(TIMEZONE)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY","dev-secret")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript(
        """        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS exercises(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          is_active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS sets(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          date TEXT NOT NULL,
          time TEXT NOT NULL,
          exercise_id INTEGER NOT NULL,
          reps INTEGER NOT NULL,
          weight_kg REAL NOT NULL,
          sets INTEGER NOT NULL,
          notes TEXT,
          user_id INTEGER,
          FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
        """
    )
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM exercises")
    if cur.fetchone()[0] == 0:
        seed = [
            "Leg Press","Machine Chest Press","Lat Pulldown","Seated Cable Row","Bicep Curls",
            "Machine Shoulder Press","Leg Curl","Leg Extension","Calf Extension","Tricep Pushdown",
            "Pec Fly","Vertical Chest Press","Treadmill","Exercise Bike","Rowing Machine"
        ]
        cur.executemany("INSERT INTO exercises(name) VALUES (?)", [(n,) for n in seed])
        conn.commit()
    admin_user = os.getenv("ADMIN_USERNAME","admin")
    admin_hash = os.getenv("ADMIN_PASSWORD_HASH","")
    cur.execute("SELECT id FROM users WHERE username=?", (admin_user,))
    if cur.fetchone() is None and admin_hash:
        import datetime as dt
        cur.execute("INSERT INTO users(username, password_hash, created_at) VALUES (?,?,?)",
                    (admin_user, admin_hash, dt.datetime.now(tz).isoformat()))
        conn.commit()
    conn.close()

init_db()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return User(row["id"], row["username"])
    return None

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").encode()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()
        if row and bcrypt.checkpw(password, row["password_hash"].encode()):
            user = User(row["id"], row["username"])
            from datetime import timedelta
            login_user(user, remember=False, duration=timedelta(minutes=120))
            return redirect(url_for("workout"))
        flash("Invalid credentials", "error")
    return render_template("login.html", title="Discipline = Freedom")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def workout():
    now = datetime.datetime.now(tz)
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM exercises WHERE is_active=1 ORDER BY name")
    exercises = cur.fetchall()
    cur.execute(
        "SELECT s.id, s.date, s.time, e.name as exercise, s.reps, s.weight_kg, s.sets, s.notes "
        "FROM sets s JOIN exercises e ON s.exercise_id=e.id "
        "WHERE s.date = ? ORDER BY s.ts ASC",
        (today,),
    )
    todays = cur.fetchall()
    conn.close()
    return render_template("workout.html", exercises=exercises, today=today, current_time=current_time, rows=todays)

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    date = request.form.get("date")
    time = request.form.get("time")
    exercise_id = int(request.form.get("exercise"))
    reps = int(request.form.get("reps"))
    sets_ct = int(request.form.get("sets"))
    weight = float(request.form.get("weight"))
    notes = request.form.get("notes","")[:500]
    now = datetime.datetime.now(tz).isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sets(ts,date,time,exercise_id,reps,weight_kg,sets,notes,user_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (now,date,time,exercise_id,reps,weight,sets_ct,notes,current_user.id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("workout"))

@app.route("/finish", methods=["POST"])
@login_required
def finish():
    target_date = request.form.get("date")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT s.date, s.time, e.name, s.reps, s.weight_kg, s.sets, s.notes "
        "FROM sets s JOIN exercises e ON s.exercise_id=e.id "
        "WHERE s.date = ? ORDER BY s.ts ASC",
        (target_date,),
    )
    rows = cur.fetchall()
    conn.close()
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = target_date
    headers = ["date","time","exercise","reps","weight (kg)","sets","notes"]; ws.append(headers)
    for r in rows: ws.append(list(r))
    import io
    dt = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    fname = dt.strftime("%d-%m-%Y") + " - workout.xlsx"
    local_path = f"/exports/{fname}"; smb_path = f"/smb/exports/{fname}"
    wb.save(local_path)
    try:
        pathlib.Path("/smb/exports").mkdir(parents=True, exist_ok=True)
        wb.save(smb_path)
    except Exception: pass
    bio = io.BytesIO(); wb.save(bio); bio.seek(0)
    return send_file(bio, as_attachment=True, download_name=fname, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/history")
@login_required
def history():
    start = request.args.get("start")
    end = request.args.get("end")
    conn = get_db()
    cur = conn.cursor()
    if start and end:
        cur.execute(
            "SELECT s.date, s.time, e.name as exercise, s.reps, s.weight_kg, s.sets, s.notes "
            "FROM sets s JOIN exercises e ON s.exercise_id=e.id "
            "WHERE s.date BETWEEN ? AND ? ORDER BY s.date, s.time",
            (start, end),
        )
    else:
        cur.execute(
            "SELECT s.date, s.time, e.name as exercise, s.reps, s.weight_kg, s.sets, s.notes "
            "FROM sets s JOIN exercises e ON s.exercise_id=e.id "
            "ORDER BY s.date DESC, s.time DESC LIMIT 200"
        )
    rows = cur.fetchall()
    conn.close()
    return render_template("history.html", rows=rows)

@app.route("/admin", methods=["GET","POST"])
@login_required
def admin():
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_ex":
            name = request.form.get("name","").strip()
            if name:
                try:
                    cur.execute("INSERT INTO exercises(name) VALUES (?)", (name,))
                    conn.commit()
                except Exception:
                    flash("Exercise may already exist.", "error")
        elif action == "toggle_ex":
            ex_id = int(request.form.get("id"))
            cur.execute("UPDATE exercises SET is_active=1-is_active WHERE id=?", (ex_id,))
            conn.commit()
        elif action == "set_password":
            new = request.form.get("new_password","").encode()
            if len(new) < 6:
                flash("Password too short.", "error")
            else:
                h = bcrypt.hashpw(new, bcrypt.gensalt()).decode()
                cur.execute("UPDATE users SET password_hash=? WHERE id=?", (h, current_user.id))
                conn.commit()
                flash("Password updated.", "ok")
    cur.execute("SELECT id,name,is_active FROM exercises ORDER BY name")
    ex = cur.fetchall()
    conn.close()
    return render_template("admin.html", exercises=ex)

def create_app(): return app

# ---- Reset feature helpers & route ----
def _guess_main_table(conn):
    # Find the table that has our expected columns
    q = """
      SELECT name, sql
      FROM sqlite_master
      WHERE type='table'
    """
    for name, sql in conn.execute(q):
        s = (sql or '').lower()
        if all(k in s for k in ('date', 'time', 'exercise', 'reps', 'weight', 'sets', 'notes')):
            return name
    # Fallback: first table
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
    return row[0] if row else None

def _export_filename_for(date_str):
    # date_str expected as YYYY-MM-DD (from <input type="date">)
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.strftime("%d-%m-%Y - workout.xlsx")

def _is_finalized(date_str):
    fname = _export_filename_for(date_str)
    # If the export file exists locally or on SMB, consider it finalized
    paths = [Path("/exports")/fname, Path("/smb/exports")/fname]
    return any(p.exists() for p in paths)

@app.context_processor
def inject_finalized_flag():
    # Provide finalized_today to templates without changing existing render calls
    try:
        # TIMEZONE already used in the app
        now = datetime.datetime.now(TZ)
    except Exception:
        now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    try:
        fin = _is_finalized(date_str)
    except Exception:
        fin = False
    return dict(finalized_today=fin)



@app.post("/reset")


@app.get("/reset")
@app.get("/reset_day")
@app.get("/wipe_today")
@login_required
def _wipe_today_get_redirect():
    # Avoid 500s if someone browses these URLs directly.
    from flask import redirect, url_for
    return redirect(url_for("workout"))

@app.post("/wipe_today")
@login_required
def _wipe_today_post():
    # Clear ALL sets for the given date unless finalized. Works even if table names differ.
    from flask import request, redirect, url_for
    date = request.form.get("date")
    if not date:
        return redirect(url_for("workout"))

    conn = get_db()
    cur = conn.cursor()

    # Respect 'finalized' table if present
    finalized = False
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='finalized'")
        if cur.fetchone():
            cur.execute("SELECT 1 FROM finalized WHERE date = ?", (date,))
            finalized = cur.fetchone() is not None
    except Exception:
        finalized = False

    if finalized:
        conn.close()
        return redirect(url_for("workout"))

    # Delete from any table that has a 'date' column
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        for tname in tables:
            try:
                cur.execute(f"PRAGMA table_info({tname})")
                cols = [c[1] for c in cur.fetchall()]
                if "date" in cols:
                    cur.execute(f'DELETE FROM "{tname}" WHERE date = ?', (date,))
            except Exception:
                conn.rollback()
                continue
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for("workout"))

@app.post("/reset_day")
@login_required
def reset_day():
    date = request.form.get("date")
    if not date:
        return redirect(url_for("workout"))

    conn = get_db()
    cur = conn.cursor()

    # Block reset if date is finalized (ignore if table missing)
    finalized = False
    try:
        cur.execute("SELECT 1 FROM finalized WHERE date = ?", (date,))
        finalized = cur.fetchone() is not None
    except Exception:
        finalized = False
    if finalized:
        conn.close()
        return redirect(url_for("workout"))

    try:
        cur.execute("DELETE FROM sets WHERE date = ?", (date,))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("workout"))
