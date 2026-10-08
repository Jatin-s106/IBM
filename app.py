"""CareerCompass AI - Skill-based career recommender, resume builder and interview coach (Flask)."""
import io, json, os, re, secrets, sqlite3
from datetime import datetime
from functools import wraps
from xml.sax.saxutils import escape

from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import data
import engine

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, pw TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, role_key TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS plan_steps(plan_id INTEGER NOT NULL, skill TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(plan_id, skill));
CREATE TABLE IF NOT EXISTS resumes(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, created TEXT NOT NULL, score INTEGER NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS interviews(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, role_key TEXT NOT NULL, qidx INTEGER NOT NULL, score INTEGER NOT NULL, created TEXT NOT NULL);
"""
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
now = lambda: datetime.now().isoformat(timespec="minutes")


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"), DATABASE=os.path.join(app.root_path, "careercompass.db"))
    if config:
        app.config.update(config)

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    with sqlite3.connect(app.config["DATABASE"]) as init:
        init.executescript(SCHEMA)

    @app.teardown_appcontext
    def close_db(_):
        conn = g.pop("db", None)
        if conn:
            conn.close()

    @app.before_request
    def load_user_and_csrf():
        g.user = None
        if "uid" in session:
            g.user = db().execute("SELECT id,name,email FROM users WHERE id=?", (session["uid"],)).fetchone()
            if g.user is None:
                session.clear()
        session.setdefault("csrf", secrets.token_hex(16))
        if request.method == "POST" and not secrets.compare_digest(request.form.get("csrf", ""), session["csrf"]):
            abort(400, "Invalid or missing security token. Please go back and retry.")

    @app.context_processor
    def inject():
        return {"csrf": session.get("csrf", ""), "user": g.get("user"), "SKILLS": data.SKILLS, "ROLES": data.ROLES}

    def login_required(view):
        @wraps(view)
        def wrapped(*a, **kw):
            if g.user is None:
                flash("Please log in to continue.", "warn")
                return redirect(url_for("login"))
            return view(*a, **kw)
        return wrapped

    @app.errorhandler(400)
    @app.errorhandler(404)
    def err(e):
        return render_template("error.html", e=e), e.code

    def known(keys):
        return [k for k in keys if k in data.SKILLS]

    # ---------- auth ----------
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name, email, pw = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
            if len(name) < 2: flash("Please enter your name.", "error")
            elif not EMAIL_RE.match(email): flash("Enter a valid email address.", "error")
            elif len(pw) < 6: flash("Password must be at least 6 characters.", "error")
            elif db().execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone(): flash("An account with this email already exists.", "error")
            else:
                cur = db().execute("INSERT INTO users(name,email,pw,created) VALUES(?,?,?,?)", (name, email, generate_password_hash(pw), now()))
                db().commit(); session.clear(); session["uid"] = cur.lastrowid
                flash("Welcome to CareerCompass AI!", "ok")
                return redirect(url_for("dashboard"))
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            row = db().execute("SELECT * FROM users WHERE email=?", (request.form.get("email", "").strip().lower(),)).fetchone()
            if row and check_password_hash(row["pw"], request.form.get("password", "")):
                session.clear(); session["uid"] = row["id"]
                return redirect(url_for("dashboard"))
            flash("Incorrect email or password.", "error")
        return render_template("auth.html", mode="login")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear(); flash("Logged out.", "ok")
        return redirect(url_for("home"))

    # ---------- careers ----------
    @app.route("/matcher", methods=["GET", "POST"])
    def matcher():
        results, chosen, tier, remote = None, [], "2", False
        if request.method == "POST":
            chosen, tier, remote = request.form.getlist("skills"), request.form.get("tier", "2"), bool(request.form.get("remote"))
            try:
                results = engine.match_careers(chosen, tier, remote, top=6)
            except engine.ValidationError as e:
                flash(str(e), "error")
        return render_template("matcher.html", results=results, chosen=chosen, tier=tier, remote=remote)

    @app.route("/careers")
    def careers():
        return render_template("careers.html", q=request.args.get("cat", ""))

    @app.route("/roadmap/<role>")
    def roadmap(role):
        if role not in data.ROLES:
            abort(404)
        have = known(request.args.getlist("have"))
        return render_template("roadmap.html", rm=engine.build_roadmap(role, have), role=role, have=have)

    @app.route("/plan/save", methods=["POST"])
    @login_required
    def plan_save():
        role = request.form.get("role", "")
        try:
            rm = engine.build_roadmap(role, known(request.form.getlist("have")))
        except engine.ValidationError:
            abort(404)
        old = db().execute("SELECT id FROM plans WHERE user_id=? AND role_key=?", (g.user["id"], role)).fetchone()
        if old:
            db().execute("DELETE FROM plan_steps WHERE plan_id=?", (old["id"],)); db().execute("DELETE FROM plans WHERE id=?", (old["id"],))
        pid = db().execute("INSERT INTO plans(user_id,role_key,created) VALUES(?,?,?)", (g.user["id"], role, now())).lastrowid
        db().executemany("INSERT INTO plan_steps(plan_id,skill) VALUES(?,?)", [(pid, s["skill"]) for s in rm["steps"]])
        db().commit(); flash("Learning plan saved to your dashboard.", "ok")
        return redirect(url_for("dashboard"))

    def own_plan(pid):
        row = db().execute("SELECT * FROM plans WHERE id=? AND user_id=?", (pid, g.user["id"])).fetchone()
        if not row: abort(404)
        return row

    @app.route("/plan/<int:pid>/toggle/<skill>", methods=["POST"])
    @login_required
    def plan_toggle(pid, skill):
        own_plan(pid)
        db().execute("UPDATE plan_steps SET done=1-done WHERE plan_id=? AND skill=?", (pid, skill)); db().commit()
        return redirect(url_for("dashboard"))

    @app.route("/plan/<int:pid>/delete", methods=["POST"])
    @login_required
    def plan_delete(pid):
        own_plan(pid)
        db().execute("DELETE FROM plan_steps WHERE plan_id=?", (pid,)); db().execute("DELETE FROM plans WHERE id=?", (pid,)); db().commit()
        flash("Plan deleted.", "ok")
        return redirect(url_for("dashboard"))

    # ---------- resume ----------
    @app.route("/resume", methods=["GET", "POST"])
    def resume():
        res, score, checks, rid = None, None, None, None
        if request.method == "POST":
            try:
                res = engine.clean_resume(request.form)
                score, checks = engine.score_resume(res)
                if g.user:
                    rid = db().execute("INSERT INTO resumes(user_id,created,score,payload) VALUES(?,?,?,?)", (g.user["id"], now(), score, json.dumps(res))).lastrowid
                    db().commit()
            except engine.ValidationError as e:
                flash(str(e), "error")
        return render_template("resume.html", res=res, score=score, checks=checks, rid=rid, form=request.form)

    def own_resume(rid):
        row = db().execute("SELECT * FROM resumes WHERE id=? AND user_id=?", (rid, g.user["id"])).fetchone()
        if not row: abort(404)
        return row

    @app.route("/resume/<int:rid>")
    @login_required
    def resume_view(rid):
        row = own_resume(rid); res = json.loads(row["payload"]); score, checks = engine.score_resume(res)
        return render_template("resume.html", res=res, score=score, checks=checks, rid=rid, form={}, readonly=True)

    @app.route("/resume/<int:rid>/pdf")
    @login_required
    def resume_pdf(rid):
        row = own_resume(rid)
        return send_file(build_resume_pdf(json.loads(row["payload"])), mimetype="application/pdf", as_attachment=True, download_name=f"resume_{rid}.pdf")

    @app.route("/resume/<int:rid>/delete", methods=["POST"])
    @login_required
    def resume_delete(rid):
        own_resume(rid)
        db().execute("DELETE FROM resumes WHERE id=?", (rid,)); db().commit(); flash("Resume deleted.", "ok")
        return redirect(url_for("dashboard"))

    # ---------- interview ----------
    @app.route("/interview", methods=["GET", "POST"])
    def interview():
        role = request.values.get("role", "software_dev")
        if role not in data.ROLES:
            role = "software_dev"
        idx = request.values.get("q", "0")
        out = None
        try:
            q = engine.interview_question(role, idx)
            if request.method == "POST":
                try:
                    out = engine.score_answer(role, idx, request.form.get("answer", ""))
                    if g.user:
                        db().execute("INSERT INTO interviews(user_id,role_key,qidx,score,created) VALUES(?,?,?,?,?)", (g.user["id"], role, q["index"], out["score"], now()))
                        db().commit()
                except engine.ValidationError as e:
                    flash(str(e), "error")
        except engine.ValidationError:
            abort(404)
        return render_template("interview.html", role=role, q=q, out=out, answer=request.form.get("answer", ""))

    # ---------- dashboard ----------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        uid = g.user["id"]
        plans = []
        for p in db().execute("SELECT * FROM plans WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall():
            steps = db().execute("SELECT skill,done FROM plan_steps WHERE plan_id=?", (p["id"],)).fetchall()
            rows = [{"skill": s["skill"], "name": data.SKILLS[s["skill"]][0], "done": s["done"], "weeks": data.LEARN[s["skill"]][0], "resource": data.LEARN[s["skill"]][1]} for s in steps]
            pct = round(100 * sum(r["done"] for r in rows) / len(rows)) if rows else 100
            plans.append({"id": p["id"], "title": data.ROLES[p["role_key"]][0], "steps": rows, "pct": pct})
        resumes = db().execute("SELECT id,created,score,payload FROM resumes WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
        resumes = [{"id": r["id"], "created": r["created"], "score": r["score"], "target": json.loads(r["payload"]).get("target") or "General"} for r in resumes]
        iv = db().execute("SELECT role_key,score,created FROM interviews WHERE user_id=? ORDER BY id DESC LIMIT 5", (uid,)).fetchall()
        return render_template("dashboard.html", plans=plans, resumes=resumes, interviews=iv)

    return app


def build_resume_pdf(r):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle as PS
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
    e_ = escape
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm, bottomMargin=15 * mm, title=f"{r['name']} - Resume")
    ink, acc = colors.HexColor("#1e1b4b"), colors.HexColor("#4338ca")
    N = PS("n", fontName="Helvetica", fontSize=10, leading=14, textColor=ink)
    H = PS("h", fontName="Helvetica-Bold", fontSize=11.5, leading=16, textColor=acc, spaceBefore=8)
    T = PS("t", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=ink)
    B = PS("b", parent=N, leftIndent=10, bulletIndent=0)
    contact = " | ".join(x for x in (r["email"], r["phone"], r.get("city"), r.get("linkedin")) if x)
    el = [Paragraph(e_(r["name"]), T), Paragraph(e_(contact), N)]
    if r.get("target"): el.append(Paragraph(f"<b>{e_(r['target'])}</b>", N))
    def head(t): el.extend([Paragraph(t.upper(), H), HRFlowable(width="100%", thickness=0.8, color=acc, spaceAfter=3)])
    if r["summary"]: head("Summary"); el.append(Paragraph(e_(r["summary"]), N))
    if r["skills"]: head("Skills"); el.append(Paragraph(e_(", ".join(r["skills"])), N))
    if r["experience"]:
        head("Experience")
        for x in r["experience"]:
            el.append(Paragraph(f"<b>{e_(x['role'])}</b>, {e_(x['org'])} <font color='#64748b'>{e_(x['duration'])}</font>", N))
            el += [Paragraph(e_(b), B, bulletText="\u2022") for b in engine._lines(x["points"])]
    if r["projects"]:
        head("Projects")
        for p in r["projects"]:
            el.append(Paragraph(f"<b>{e_(p['title'])}</b>", N))
            el += [Paragraph(e_(b), B, bulletText="\u2022") for b in engine._lines(p["points"])]
    head("Education")
    for x in r["education"]:
        el.append(Paragraph(f"<b>{e_(x['degree'])}</b>, {e_(x['institute'])} <font color='#64748b'>{e_(x['year'])} {('| ' + e_(x['score'])) if x['score'] else ''}</font>", N))
    doc.build(el); buf.seek(0)
    return buf


if __name__ == "__main__":
    create_app().run(debug=False, host="127.0.0.1", port=5000)
