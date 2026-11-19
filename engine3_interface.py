import math
from datetime import date, datetime
from flask import Flask, request, redirect, url_for, render_template_string, flash

app = Flask(__name__)
app.secret_key = "kletech-bca-engine3-secret"

STUDENTS = [
    {"usn": "01FE24BCA274", "name": "Soumya Sunkad"},
    {"usn": "01FE24BCA275", "name": "Divya Sunkad"},
    {"usn": "01FE24BCA276", "name": "Akkamma S R"},
]
SESSIONS = [{"course": "24BCA401", "date": "2026-10-01", "period": 1}]
ATTENDANCE = {
    "01FE24BCA274": {"held": 1, "attended": 1},
    "01FE24BCA275": {"held": 1, "attended": 0},
    "01FE24BCA276": {"held": 1, "attended": 1},
}

HTML_TEMPLATE = """
<!DOCTYPE html>python
<html>
<head>
    <title>KLE Tech BCA Attendance</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
<div class="container" style="max-width: 900px;">
    <div class="bg-primary text-white p-3 rounded mb-3 shadow-sm d-flex justify-content-between align-items-center">
        <h5 class="m-0">Student Attendance Shortage System (Engine 3)</h5>
        <span class="badge bg-light text-primary">Web Tech & Server-Side Checks</span>
    </div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}{% for cat, msg in messages %}
        <div class="alert alert-{{ cat }}">{{ msg }}</div>
      {% endfor %}{% endif %}
    {% endwith %}
    <div class="row g-3">
        <!-- FACULTY MARKING SCREEN -->
        <div class="col-md-6">
            <div class="card shadow-sm h-100">
                <div class="card-header bg-dark text-white fw-bold">Faculty Attendance Form</div>
                <div class="card-body">
                    <form method="POST" action="/mark_attendance">
                        <input type="hidden" name="course" value="24BCA401">
                        <div class="row g-2 mb-2">
                            <div class="col"><label class="small fw-bold">Date:</label><input type="date" name="session_date" class="form-control form-control-sm" required></div>
                            <div class="col"><label class="small fw-bold">Period (1-8):</label><input type="number" name="period" class="form-control form-control-sm" min="1" max="8" required></div>
                        </div>
                        <label class="small fw-bold mt-2">Mark Student Attendance:</label>
                        {% for s in students %}
                        <div class="d-flex justify-content-between align-items-center border-bottom py-1">
                            <span class="small">{{ s.name }}</span>
                            <div class="btn-group btn-group-sm">
                                <input type="radio" class="btn-check" name="status_{{ s.usn }}" id="p_{{ s.usn }}" value="P" checked><label class="btn btn-outline-success" for="p_{{ s.usn }}">P</label>
                                <input type="radio" class="btn-check" name="status_{{ s.usn }}" id="a_{{ s.usn }}" value="A"><label class="btn btn-outline-danger" for="a_{{ s.usn }}">A</label>
                                <input type="radio" class="btn-check" name="status_{{ s.usn }}" id="od_{{ s.usn }}" value="OD"><label class="btn btn-outline-warning" for="od_{{ s.usn }}">OD</label>
                            </div>
                        </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-primary btn-sm w-100 mt-3">Submit & Verify Server-Side</button>
                    </form>
                </div>
            </div>
        </div>
        <!-- STUDENT SHORTAGE REPORT SCREEN -->
        <div class="col-md-6">
            <div class="card shadow-sm h-100">
                <div class="card-header bg-secondary text-white fw-bold">Live Shortage Roster</div>
                <div class="card-body p-0">
                    <table class="table table-sm table-striped m-0">
                        <thead class="table-dark small"><tr><th>Name</th><th>Held</th><th>Att</th><th>%</th><th>Status</th><th>Recovery</th></tr></thead>
                        <tbody class="small">
                            {% for r in report %}
                            <tr>
                                <td>{{ r.name }}</td><td>{{ r.held }}</td><td>{{ r.attended }}</td>
                                <td><b>{{ r.pct }}%</b></td>
                                <td><span class="badge bg-{{ r.badge_color }}">{{ r.status }}</span></td>
                                <td>{{ r.recovery }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""

@app.route("/")
def index():
    report = []
    for s in STUDENTS:
        d = ATTENDANCE[s["usn"]]
        held, att = d["held"], d["attended"]
        pct = round((att / held) * 100.0, 1) if held > 0 else 0.0
        rec = max(0, math.ceil(((0.75 * held) - att) / 0.25))
        status = "Safe" if pct >= 75.0 else ("Warning" if pct >= 65.0 else "Detention")
        badge = "success" if pct >= 75.0 else ("warning" if pct >= 65.0 else "danger")
        report.append({"name": s["name"], "held": held, "attended": att, "pct": pct, "status": status, "badge_color": badge, "recovery": f"{rec} classes" if rec > 0 else "0"})
    return render_template_string(HTML_TEMPLATE, students=STUDENTS, report=report)

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    course = request.form.get("course")
    session_date = request.form.get("session_date")
    period = int(request.form.get("period", 0))

    # SERVER-SIDE DOUBLE CHECKING
    if not (1 <= period <= 8):
        flash(f"Server-Side Error: Period {period} is invalid! Must be 1 to 8.", "danger")
        return redirect(url_for("index"))
    if datetime.strptime(session_date, "%Y-%m-%d").date() > date.today():
        flash("Server-Side Error: Attendance cannot be marked for future dates!", "danger")
        return redirect(url_for("index"))
    for s in SESSIONS:
        if s["course"] == course and s["date"] == session_date and s["period"] == period:
            flash(f"Server-Side Duplicate Rejected: Slot {course} on {session_date} Period {period} already marked!", "danger")
            return redirect(url_for("index"))

    SESSIONS.append({"course": course, "date": session_date, "period": period})
    for s in STUDENTS:
        st = request.form.get(f"status_{s['usn']}", "A")
        ATTENDANCE[s["usn"]]["held"] += 1
        if st in ("P", "OD"): ATTENDANCE[s["usn"]]["attended"] += 1

    flash("Success: Session recorded and double-checked on server!", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000) 