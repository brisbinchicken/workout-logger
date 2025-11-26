import os, datetime, pytz, sqlite3, openpyxl, pathlib
TZ = os.getenv("TIMEZONE","UTC")
tz = pytz.timezone(TZ)
today = datetime.datetime.now(tz).date()
db_path = "/data/workouts.sqlite"
conn = sqlite3.connect(db_path)
c = conn.cursor()
start = today - datetime.timedelta(days=6)
c.execute(
    "SELECT date, time, e.name, s.reps, s.weight_kg, s.sets, s.notes "
    "FROM sets s JOIN exercises e ON s.exercise_id=e.id "
    "WHERE date BETWEEN ? AND ? "
    "ORDER BY date, time",
    (start.isoformat(), today.isoformat()),
)
rows = c.fetchall()
conn.close()
if rows:
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Weekly"
    headers = ["date","time","exercise","reps","weight (kg)","sets","notes"]; ws.append(headers)
    for r in rows: ws.append(list(r))
    dl_name = f"{start.strftime('%d-%m-%Y')} to {today.strftime('%d-%m-%Y')} - weekly.xlsx"
    out_local = f"/exports/{dl_name}"; out_smb = f"/smb/exports/{dl_name}"
    wb.save(out_local)
    try:
        pathlib.Path("/smb/exports").mkdir(parents=True, exist_ok=True)
        wb.save(out_smb)
    except Exception: pass
