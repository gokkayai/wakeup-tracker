from flask import Flask, jsonify, request
import sqlite3
from datetime import datetime, date

app = Flask(__name__)

DB_FILE = "wakeups.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS wakeups (
            day TEXT PRIMARY KEY,
            wake_time TEXT NOT NULL,
            sleep_time TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def parse_day(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except Exception:
        return None


def parse_hhmm(value):
    try:
        datetime.strptime(value, "%H:%M")
        return value
    except Exception:
        return None


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def compute_streak(rows, target_time, tolerance_min):
    if not rows:
        return 0, 0

    tol = int(tolerance_min)
    target_limit = minutes(target_time) + tol

    def is_success(wake_time):
        return minutes(wake_time) <= target_limit

    best = 0
    run = 0
    prev_day = None

    # rows must be sorted ASC by day
    for r in rows:
        d = r["day"]
        w = r["wake_time"]

        if prev_day is not None:
            prev_date = datetime.strptime(prev_day, "%Y-%m-%d").date()
            cur_date = datetime.strptime(d, "%Y-%m-%d").date()

            if (cur_date - prev_date).days != 1:
                run = 0

        if is_success(w):
            run += 1
            if run > best:
                best = run
        else:
            run = 0

        prev_day = d

    current = 0
    prev_day = None

    # walk backwards from the latest entry
    for r in reversed(rows):
        d = r["day"]
        w = r["wake_time"]

        if prev_day is not None:
            cur_date = datetime.strptime(d, "%Y-%m-%d").date()
            prev_date = datetime.strptime(prev_day, "%Y-%m-%d").date()

            if (prev_date - cur_date).days != 1:
                break

        if is_success(w):
            current += 1
        else:
            break

        prev_day = d

    return current, best



@app.route("/wakeups", methods=["GET"])
def get_wakeups():
    day_from = request.args.get("from")
    day_to = request.args.get("to")

    if day_from and not parse_day(day_from):
        return jsonify({"error": "Invalid 'from' date. Use YYYY-MM-DD."}), 400
    if day_to and not parse_day(day_to):
        return jsonify({"error": "Invalid 'to' date. Use YYYY-MM-DD."}), 400

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT day, wake_time, sleep_time, note, created_at FROM wakeups"
    params = []

    if day_from and day_to:
        query += " WHERE day BETWEEN ? AND ?"
        params += [day_from, day_to]
    elif day_from:
        query += " WHERE day >= ?"
        params += [day_from]
    elif day_to:
        query += " WHERE day <= ?"
        params += [day_to]

    query += " ORDER BY day ASC"
    rows = cur.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows]), 200


@app.route("/wakeups/<day>", methods=["GET"])
def get_wakeup_by_day(day):
    if not parse_day(day):
        return jsonify({"error": "Invalid date. Use YYYY-MM-DD."}), 400

    conn = get_db()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT day, wake_time, sleep_time, note, created_at FROM wakeups WHERE day = ?",
        (day,),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Day '{day}' not found."}), 404

    return jsonify(dict(row)), 200


@app.route("/wakeups", methods=["POST"])
def add_wakeup():
    body = request.get_json(silent=True) or {}

    day = body.get("day")
    wake_time = body.get("wake_time")
    sleep_time = body.get("sleep_time")
    note = body.get("note")

    if not day or not parse_day(day):
        return jsonify({"error": "Missing/invalid 'day'. Use YYYY-MM-DD."}), 400
    if not wake_time or not parse_hhmm(wake_time):
        return jsonify({"error": "Missing/invalid 'wake_time'. Use HH:MM."}), 400
    if sleep_time is not None and sleep_time != "" and not parse_hhmm(sleep_time):
        return jsonify({"error": "Invalid 'sleep_time'. Use HH:MM."}), 400

    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO wakeups(day, wake_time, sleep_time, note, created_at) VALUES(?,?,?,?,?)",
            (day, wake_time, sleep_time or None, note, created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"Day '{day}' already exists. Use PUT to update."}), 409

    row = cur.execute(
        "SELECT day, wake_time, sleep_time, note, created_at FROM wakeups WHERE day = ?",
        (day,),
    ).fetchone()
    conn.close()

    return jsonify(dict(row)), 201


@app.route("/wakeups/<day>", methods=["PUT"])
def update_wakeup(day):
    if not parse_day(day):
        return jsonify({"error": "Invalid date. Use YYYY-MM-DD."}), 400

    body = request.get_json(silent=True) or {}
    wake_time = body.get("wake_time")
    sleep_time = body.get("sleep_time")
    note = body.get("note")

    if wake_time is not None and wake_time != "" and not parse_hhmm(wake_time):
        return jsonify({"error": "Invalid 'wake_time'. Use HH:MM."}), 400
    if sleep_time is not None and sleep_time != "" and not parse_hhmm(sleep_time):
        return jsonify({"error": "Invalid 'sleep_time'. Use HH:MM."}), 400

    fields = []
    params = []

    if wake_time is not None:
        fields.append("wake_time = ?")
        params.append(wake_time)
    if sleep_time is not None:
        fields.append("sleep_time = ?")
        params.append(sleep_time or None)
    if note is not None:
        fields.append("note = ?")
        params.append(note)

    if not fields:
        return jsonify({"error": "Nothing to update."}), 400

    params.append(day)

    conn = get_db()
    cur = conn.cursor()

    existing = cur.execute("SELECT 1 FROM wakeups WHERE day = ?", (day,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": f"Day '{day}' not found."}), 404

    cur.execute(f"UPDATE wakeups SET {', '.join(fields)} WHERE day = ?", params)
    conn.commit()

    row = cur.execute(
        "SELECT day, wake_time, sleep_time, note, created_at FROM wakeups WHERE day = ?",
        (day,),
    ).fetchone()
    conn.close()

    return jsonify(dict(row)), 200


@app.route("/wakeups/<day>", methods=["DELETE"])
def delete_wakeup(day):
    if not parse_day(day):
        return jsonify({"error": "Invalid date. Use YYYY-MM-DD."}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM wakeups WHERE day = ?", (day,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": f"Day '{day}' not found."}), 404

    return jsonify({"message": f"Day '{day}' deleted."}), 200


@app.route("/streak", methods=["GET"])
def get_streak():
    target_time = request.args.get("target_time", "07:00")
    tolerance_min = request.args.get("tolerance_min", "0")

    if not parse_hhmm(target_time):
        return jsonify({"error": "Invalid 'target_time'. Use HH:MM."}), 400
    try:
        int(tolerance_min)
    except Exception:
        return jsonify({"error": "Invalid 'tolerance_min'. Use an integer."}), 400

    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT day, wake_time FROM wakeups ORDER BY day ASC"
    ).fetchall()
    conn.close()

    current, best = compute_streak(rows, target_time, tolerance_min)
    return jsonify(
        {
            "target_time": target_time,
            "tolerance_min": int(tolerance_min),
            "current_streak": current,
            "best_streak": best,
        }
    ), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
