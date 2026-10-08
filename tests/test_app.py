"""Automated tests for CareerCompass AI - run: python -m unittest discover -s tests -v"""
import os, re, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data, engine
from app import create_app

RES = {"name": "Asha Patil", "email": "asha@mail.com", "phone": "98765 43210", "city": "Nashik", "target": "Data Analyst",
       "summary": " ".join(["motivated"] * 40), "skills": "Python, SQL, Excel, Power BI, Communication",
       "edu0_degree": "BSc IT", "edu0_institute": "Mumbai University", "edu0_year": "2026", "edu0_score": "8.5 CGPA",
       "proj0_title": "Sales Dashboard", "proj0_points": "Built a dashboard used by 50 users\nReduced reporting time by 40%",
       "exp0_role": "Intern", "exp0_org": "TechCorp", "exp0_duration": "2 months", "exp0_points": "Analyzed 10,000 records\nCreated 5 reports"}


class EngineTests(unittest.TestCase):
    def test_data_integrity(self):
        for k, (t, c, w, sal, d, r, a, desc) in data.ROLES.items():
            self.assertTrue(all(s in data.SKILLS and s in data.LEARN for s in w), k)
            self.assertIn(k, data.TECH_QUESTIONS); self.assertLess(sal[0], sal[1]); self.assertEqual(len(a), 3)
        self.assertEqual(set(data.SKILLS), set(data.LEARN))

    def test_match_ranking(self):
        r = engine.match_careers(["excel", "sql", "data_viz", "statistics"], "1")
        self.assertEqual(r[0]["key"], "data_analyst"); self.assertEqual(len(r), len(data.ROLES))
        self.assertTrue(all(r[i]["score"] >= r[i + 1]["score"] for i in range(len(r) - 1)))
        self.assertEqual(len(engine.match_careers(["python"], "2", top=3)), 3)

    def test_perfect_skills_full_score(self):
        w = data.ROLES["accountant"][2]
        r = engine.match_careers(list(w), "3")[0]
        self.assertEqual((r["key"], r["score"], r["skill_match"], r["missing"]), ("accountant", 100, 100, []))

    def test_location_effect(self):
        s = ["python", "linux", "networking", "cybersecurity_basics", "problem_solving"]
        t1 = [x for x in engine.match_careers(s, "1") if x["key"] == "cyber_analyst"][0]["score"]
        t3 = [x for x in engine.match_careers(s, "3") if x["key"] == "cyber_analyst"][0]["score"]
        self.assertGreater(t1, t3)
        rem = [x for x in engine.match_careers(["python", "sql"], "3", remote=True) if x["key"] == "software_dev"][0]
        loc = [x for x in engine.match_careers(["python", "sql"], "3", remote=False) if x["key"] == "software_dev"][0]
        self.assertGreater(rem["score"], loc["score"]); self.assertEqual(rem["local"], "High")
        cy = [x for x in engine.match_careers(s, "3", remote=True) if x["key"] == "cyber_analyst"][0]
        self.assertEqual(cy["local"], "Limited")  # not remote-friendly so remote flag does not help

    def test_match_validation(self):
        for a in (([], "2"), (["nope"], "2"), (["python"], "9"), (["python"], "")):
            with self.assertRaises(engine.ValidationError): engine.match_careers(*a)

    def test_roadmap(self):
        rm = engine.build_roadmap("data_analyst", ["sql", "excel"])
        self.assertNotIn("SQL", [s["name"] for s in rm["steps"]]); self.assertEqual(rm["total_weeks"], sum(s["weeks"] for s in rm["steps"]))
        self.assertEqual(rm["steps"][0]["priority"], "Must-have")
        self.assertEqual(engine.build_roadmap("accountant", list(data.ROLES["accountant"][2]))["steps"], [])
        with self.assertRaises(engine.ValidationError): engine.build_roadmap("ghost", [])

    def test_resume_clean_and_score(self):
        r = engine.clean_resume(RES); self.assertEqual(r["phone"], "9876543210"); self.assertEqual(len(r["skills"]), 5)
        score, checks = engine.score_resume(r); self.assertEqual(score, 100); self.assertEqual(sum(c["max"] for c in checks), 100)
        weak = engine.clean_resume({"name": "Ab", "email": "a@b.co", "phone": "9876543210", "edu0_degree": "BA", "edu0_institute": "X"})
        s2, c2 = engine.score_resume(weak); self.assertLess(s2, 50); self.assertTrue(any(c["tip"] for c in c2))

    def test_resume_validation(self):
        base = dict(RES)
        for k, v in (("name", "A"), ("email", "bad"), ("phone", "12345"), ("phone", "5876543210")):
            with self.assertRaises(engine.ValidationError, msg=k): engine.clean_resume({**base, k: v})
        no_edu = {k: v for k, v in base.items() if not k.startswith("edu")}
        with self.assertRaises(engine.ValidationError): engine.clean_resume(no_edu)
        with self.assertRaises(engine.ValidationError): engine.clean_resume({**base, "edu0_institute": ""})
        with self.assertRaises(engine.ValidationError): engine.clean_resume({**base, "proj0_title": "", "proj0_points": "x"})
        with self.assertRaises(engine.ValidationError): engine.clean_resume({**base, "exp0_org": ""})
        self.assertEqual(engine.clean_resume({**base, "phone": "+91 98765-43210"})["phone"], "9876543210")

    def test_action_verbs_and_numbers_scoring(self):
        r = engine.clean_resume({**RES, "proj0_points": "Responsible for stuff\nDid things", "exp0_points": "Helped team"})
        s, c = engine.score_resume(r); d = {x["label"]: x["earned"] for x in c}
        self.assertEqual(d["Bullets start with action verbs"], 0); self.assertEqual(d["Quantified achievements (numbers)"], 0)

    def test_interview(self):
        q = engine.interview_question("web_dev", 0); self.assertEqual(q["total"], 6)
        good = "I am a student with strong skills. In my project I built a website and I am learning every day. My goal is to join your company with this experience and interest."
        r = engine.score_answer("web_dev", 0, good); self.assertGreaterEqual(r["score"], 75); self.assertEqual(r["feedback"][0], "Excellent answer!")
        weak = engine.score_answer("web_dev", 0, "I am okay person yes"); self.assertLess(weak["score"], 50)
        for a in (("web_dev", 99, "hello there friend ok"), ("web_dev", "x", "hello there friend ok"), ("ghost", 0, "hello there friend ok"), ("web_dev", 0, "hi")):
            with self.assertRaises(engine.ValidationError): engine.score_answer(*a)
        for k in data.ROLES: self.assertEqual(engine.interview_question(k, 5)["total"], 6)


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False); self.tmp.close()
        self.app = create_app({"TESTING": True, "DATABASE": self.tmp.name, "SECRET_KEY": "t"}); self.c = self.app.test_client()

    def tearDown(self): os.unlink(self.tmp.name)

    def tok(self, c=None, path="/login"):
        return re.search(r'name="csrf" value="([0-9a-f]+)"', (c or self.c).get(path).get_data(as_text=True)).group(1)

    def post(self, path, c=None, **form):
        c = c or self.c; form["csrf"] = self.tok(c); return c.post(path, data=form, follow_redirects=True)

    def signup(self, email="a@b.com", name="Asha Patil", c=None):
        return self.post("/register", c=c, name=name, email=email, password="secret1")

    def test_public_pages(self):
        for p in ("/", "/matcher", "/careers", "/careers?cat=Tech", "/roadmap/data_analyst", "/roadmap/data_analyst?have=sql&have=bogus", "/resume", "/interview",
                  "/interview?role=accountant&q=5", "/interview?role=bogus", "/login", "/register", "/static/style.css"):
            self.assertEqual(self.c.get(p).status_code, 200, p)
        for p in ("/nope", "/roadmap/ghost", "/interview?q=99", "/interview?q=abc"):
            self.assertEqual(self.c.get(p).status_code, 404, p)

    def test_protected_and_csrf(self):
        for p in ("/dashboard", "/resume/1", "/resume/1/pdf"):
            r = self.c.get(p); self.assertEqual(r.status_code, 302); self.assertIn("/login", r.location)
        self.assertEqual(self.c.post("/matcher", data={"skills": "python"}).status_code, 400)
        self.assertEqual(self.c.post("/logout").status_code, 400)

    def test_auth_flow(self):
        self.assertIn("Hello, Asha Patil", self.signup().get_data(as_text=True)); self.post("/logout")
        self.assertEqual(self.c.get("/dashboard").status_code, 302)
        self.assertIn("Incorrect", self.post("/login", email="a@b.com", password="nope").get_data(as_text=True))
        self.assertIn("Hello, Asha", self.post("/login", email="a@b.com", password="secret1").get_data(as_text=True)); self.post("/logout")
        self.assertIn("already exists", self.signup().get_data(as_text=True))
        for kw, msg in ((dict(name="A", email="x@y.com", password="secret1"), "your name"), (dict(name="Abc", email="bad", password="secret1"), "valid email"), (dict(name="Abc", email="x@y.com", password="12"), "6 characters")):
            self.assertIn(msg, self.post("/register", **kw).get_data(as_text=True))

    def test_matcher_page(self):
        t = self.post("/matcher", skills=["excel", "sql", "data_viz"], tier="2").get_data(as_text=True)
        self.assertIn("Data Analyst", t); self.assertIn("View roadmap", t)
        self.assertIn("Select at least one", self.post("/matcher", tier="2").get_data(as_text=True))
        self.assertIn("valid city", self.post("/matcher", skills="python", tier="7").get_data(as_text=True))
        self.assertIn("Remote-friendly", self.post("/matcher", skills=["python"], tier="3", remote="on").get_data(as_text=True))

    def test_plan_lifecycle_and_isolation(self):
        self.signup()
        self.post("/plan/save", role="data_analyst", have=["sql"])
        t = self.c.get("/dashboard").get_data(as_text=True); self.assertIn("Data Analyst", t); self.assertIn("0% complete", t); self.assertNotIn("SQL</td>", t)
        t = self.post("/plan/1/toggle/excel").get_data(as_text=True); self.assertIn("Done", t); self.assertIn("20% complete", t)
        self.post("/plan/save", role="data_analyst", have=["sql", "excel"])  # re-saving replaces
        self.assertEqual(self.c.get("/dashboard").get_data(as_text=True).count("Delete"), 1 + 0)
        self.assertEqual(self.post("/plan/save", role="ghost").status_code, 404)
        other = self.app.test_client(); self.signup("o@o.com", "Other One", c=other)
        self.assertEqual(self.post("/plan/2/toggle/excel", c=other).status_code, 404); self.assertEqual(self.post("/plan/2/delete", c=other).status_code, 404)
        self.post("/plan/2/delete"); self.assertIn("No plans yet", self.c.get("/dashboard").get_data(as_text=True))

    def test_roadmap_save_requires_login(self):
        r = self.post("/plan/save", role="data_analyst"); self.assertIn("Log in", r.get_data(as_text=True))

    def test_resume_guest_and_user(self):
        t = self.post("/resume", **RES).get_data(as_text=True); self.assertIn("100/100", t); self.assertIn("Asha Patil", t); self.assertIn("Log in</a> to save", t)
        self.assertIn("valid email", self.post("/resume", **{**RES, "email": "bad"}).get_data(as_text=True))
        self.signup(); t = self.post("/resume", **RES).get_data(as_text=True); self.assertIn("Download PDF", t)
        pdf = self.c.get("/resume/1/pdf"); self.assertEqual(pdf.status_code, 200); self.assertTrue(pdf.data.startswith(b"%PDF"))
        self.assertEqual(self.c.get("/resume/1").status_code, 200); self.assertIn("Data Analyst", self.c.get("/dashboard").get_data(as_text=True))
        other = self.app.test_client(); self.signup("o@o.com", "Other One", c=other)
        self.assertEqual(other.get("/resume/1").status_code, 404); self.assertEqual(other.get("/resume/1/pdf").status_code, 404); self.assertEqual(self.post("/resume/1/delete", c=other).status_code, 404)
        self.post("/resume/1/delete"); self.assertEqual(self.c.get("/resume/1").status_code, 404)

    def test_resume_special_chars(self):
        self.signup(name="A<b>&Co")
        self.post("/resume", **{**RES, "name": "Ravi <script>x</script> & Co", "proj0_points": "Built <b>tool</b> for 5 users"})
        self.assertEqual(self.c.get("/resume/1/pdf").status_code, 200)
        self.assertNotIn("<script>x", self.c.get("/resume/1").get_data(as_text=True))

    def test_interview_flow(self):
        good = "I am a student with strong skills. In my project I built a website and I am learning every day. My goal is to join your company with this experience."
        self.assertIn("Excellent answer", self.post("/interview", role="web_dev", q="0", answer=good).get_data(as_text=True))
        self.assertIn("at least 5 words", self.post("/interview", role="web_dev", q="0", answer="hi").get_data(as_text=True))
        self.signup(); self.post("/interview", role="web_dev", q="0", answer=good)
        self.assertIn("Web Developer: ", self.c.get("/dashboard").get_data(as_text=True))

    def test_xss_in_dashboard(self):
        self.signup(name="<script>alert(1)</script>"); t = self.c.get("/dashboard").get_data(as_text=True)
        self.assertNotIn("<script>alert", t); self.assertIn("&lt;script&gt;", t)


if __name__ == "__main__":
    unittest.main()
