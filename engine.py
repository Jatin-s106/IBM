"""Core logic for CareerCompass AI: career matching, roadmap, resume scoring, interview scoring."""
import re
import data


class ValidationError(ValueError):
    pass


def match_careers(selected, tier="2", remote=False, top=None):
    selected = list(dict.fromkeys(selected))
    if not selected:
        raise ValidationError("Select at least one skill.")
    for s in selected:
        if s not in data.SKILLS:
            raise ValidationError(f"Unknown skill: {s}")
    if str(tier) not in ("1", "2", "3"):
        raise ValidationError("Choose a valid city tier.")
    ti = int(tier) - 1
    out = []
    for key, (title, cat, weights, sal, demand, rem, avail, desc) in data.ROLES.items():
        total = sum(weights.values())
        have = [s for s in weights if s in selected]
        skill_pct = 100 * sum(weights[s] for s in have) / total
        a = 3 if (remote and rem) else avail[ti]
        final = round(0.85 * skill_pct + 15 * a / 3)
        missing = sorted((s for s in weights if s not in selected), key=lambda s: -weights[s])
        out.append({"key": key, "title": title, "category": cat, "score": final, "skill_match": round(skill_pct),
                    "matched": [data.SKILLS[s][0] for s in have], "missing": [data.SKILLS[s][0] for s in missing],
                    "missing_keys": missing, "salary": f"{sal[0]:g} - {sal[1]:g} LPA", "demand": demand, "remote": rem,
                    "local": {3: "High", 2: "Medium", 1: "Limited"}[a], "desc": desc})
    out.sort(key=lambda r: (-r["score"], r["title"]))
    return out[:top] if top else out


def build_roadmap(role_key, have):
    if role_key not in data.ROLES:
        raise ValidationError("Unknown career.")
    have = set(have or [])
    weights = data.ROLES[role_key][2]
    steps = []
    for s in sorted((s for s in weights if s not in have), key=lambda s: (-weights[s], s)):
        wk, res = data.LEARN[s]
        steps.append({"skill": s, "name": data.SKILLS[s][0], "weeks": wk, "resource": res, "priority": "Must-have" if weights[s] == 3 else "Good-to-have"})
    return {"role": data.ROLES[role_key][0], "steps": steps, "total_weeks": sum(x["weeks"] for x in steps)}


def _lines(text):
    return [l.strip() for l in (text or "").replace("\r", "").split("\n") if l.strip()]


def clean_resume(form):
    """Turn raw form dict into a structured resume dict, validating the essentials."""
    g = lambda k: (form.get(k) or "").strip()
    name, email, phone = g("name"), g("email"), re.sub(r"[\s\-+()]", "", g("phone"))
    if len(name) < 2:
        raise ValidationError("Enter your full name.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValidationError("Enter a valid email address.")
    if not re.match(r"^(91)?[6-9]\d{9}$", phone):
        raise ValidationError("Enter a valid 10-digit Indian mobile number.")
    skills = [s.strip() for s in re.split(r"[,\n]", g("skills")) if s.strip()][:30]
    def rows(prefix, fields, n):
        out = []
        for i in range(n):
            r = {f: g(f"{prefix}{i}_{f}") for f in fields}
            if any(r.values()):
                out.append(r)
        return out
    edu = rows("edu", ("degree", "institute", "year", "score"), 2)
    if not edu:
        raise ValidationError("Add at least one education entry.")
    for e in edu:
        if not e["degree"] or not e["institute"]:
            raise ValidationError("Each education entry needs a degree and an institute.")
    proj = rows("proj", ("title", "points"), 2)
    exp = rows("exp", ("role", "org", "duration", "points"), 2)
    for p in proj:
        if not p["title"]:
            raise ValidationError("Each project needs a title.")
    for x in exp:
        if not x["role"] or not x["org"]:
            raise ValidationError("Each experience entry needs a role and an organisation.")
    return {"name": name, "email": email, "phone": phone[-10:], "city": g("city"), "linkedin": g("linkedin"), "target": g("target"),
            "summary": g("summary"), "skills": skills, "education": edu, "projects": proj, "experience": exp}


def score_resume(r):
    """Returns (score out of 100, list of (label, earned, max, tip))."""
    bullets = [b for sec in (r["projects"], r["experience"]) for item in sec for b in _lines(item.get("points"))]
    words = len(r["summary"].split())
    first_words = [re.sub(r"[^a-z]", "", b.split()[0].lower()) for b in bullets if b.split()]
    checks = [
        ("Contact details complete", 15, 15 if r["name"] and r["email"] and r["phone"] else 0, "Add name, email and phone."),
        ("Professional summary (30-80 words)", 15, 15 if 30 <= words <= 80 else (8 if 10 <= words < 30 or 80 < words <= 120 else 0), "Write a 30-80 word summary of your goal and strengths."),
        ("At least 5 skills listed", 15, 15 if len(r["skills"]) >= 5 else 3 * len(r["skills"]), "List 5 or more relevant skills."),
        ("Education added", 10, 10 if r["education"] else 0, "Add your education."),
        ("Projects or experience", 15, 15 if bullets else (5 if (r["projects"] or r["experience"]) else 0), "Add projects/internships with bullet points (one per line)."),
        ("Bullets start with action verbs", 15, round(15 * sum(w in data.ACTION_VERBS for w in first_words) / len(first_words)) if first_words else 0, "Start bullets with verbs like Built, Led, Designed."),
        ("Quantified achievements (numbers)", 15, round(15 * min(1, sum(bool(re.search(r"\d", b)) for b in bullets) / max(1, min(len(bullets), 3)))) if bullets else 0, "Add numbers: users, % improvement, team size."),
    ]
    return sum(c[2] for c in checks), [{"label": l, "max": m, "earned": e, "tip": "" if e == m else t} for l, m, e, t in checks]


def interview_question(role_key, idx):
    qs = data.HR_QUESTIONS + (data.TECH_QUESTIONS.get(role_key) or [])
    if role_key not in data.ROLES:
        raise ValidationError("Unknown career.")
    try:
        idx = int(idx)
    except (TypeError, ValueError):
        raise ValidationError("Invalid question.")
    if not 0 <= idx < len(qs):
        raise ValidationError("Invalid question.")
    return {"index": idx, "total": len(qs), "question": qs[idx][0], "keywords": qs[idx][1].split(",")}


def score_answer(role_key, idx, answer):
    q = interview_question(role_key, idx)
    answer = (answer or "").strip()
    words = re.findall(r"[a-zA-Z']+", answer.lower())
    if len(words) < 5:
        raise ValidationError("Write a proper answer (at least 5 words).")
    text = " ".join(words)
    hit = [k for k in q["keywords"] if k in text]
    miss = [k for k in q["keywords"] if k not in text]
    kw = round(60 * len(hit) / len(q["keywords"]))
    length = 20 if len(words) >= 40 else 12 if len(words) >= 20 else 5
    example = 20 if re.search(r"\b(for example|for instance|i built|i created|i worked|my project|in my|result|learned)\b", text) else 0
    total = min(100, kw + length + example)
    fb = []
    if length < 20: fb.append("Give a fuller answer (aim for 40+ words).")
    if not example: fb.append("Add a real example from a project, internship or college work.")
    if miss: fb.append("Try covering: " + ", ".join(miss[:4]) + ".")
    if total >= 75: fb.insert(0, "Excellent answer!")
    elif total >= 50: fb.insert(0, "Good answer - can be stronger.")
    else: fb.insert(0, "Needs improvement.")
    return {"score": total, "hit": hit, "missing": miss, "feedback": fb, "question": q}
