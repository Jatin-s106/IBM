"""Knowledge base for CareerCompass AI. Salaries are indicative entry-level figures (LPA, India) and vary by company/city."""

# key: (name, category)
SKILLS = {
 "python": ("Python", "Tech"), "java": ("Java", "Tech"), "javascript": ("JavaScript", "Tech"), "sql": ("SQL", "Tech"),
 "html_css": ("HTML & CSS", "Tech"), "c_cpp": ("C / C++", "Tech"), "git": ("Git & GitHub", "Tech"), "react": ("React", "Tech"),
 "nodejs": ("Node.js", "Tech"), "linux": ("Linux", "Tech"), "networking": ("Computer Networks", "Tech"), "cloud": ("Cloud (AWS/Azure)", "Tech"),
 "docker": ("Docker", "Tech"), "cybersecurity_basics": ("Cybersecurity Basics", "Tech"), "testing": ("Manual Testing", "Tech"), "selenium": ("Selenium Automation", "Tech"),
 "excel": ("Advanced Excel", "Data"), "statistics": ("Statistics", "Data"), "data_viz": ("Power BI / Tableau", "Data"), "machine_learning": ("Machine Learning", "Data"), "pandas": ("Pandas & NumPy", "Data"),
 "figma": ("Figma", "Creative"), "photoshop": ("Photoshop / Canva", "Creative"), "ux_research": ("UX Research", "Creative"),
 "seo": ("SEO", "Marketing"), "social_media": ("Social Media Marketing", "Marketing"), "content_writing": ("Content Writing", "Marketing"),
 "copywriting": ("Copywriting", "Marketing"), "email_marketing": ("Email Marketing", "Marketing"), "analytics": ("Google Analytics", "Marketing"),
 "accounting": ("Accounting Basics", "Business"), "tally": ("Tally", "Business"), "gst": ("GST & Taxation", "Business"), "recruitment": ("Recruitment / Sourcing", "Business"),
 "sales": ("Sales & Lead Generation", "Business"), "negotiation": ("Negotiation", "Business"), "customer_service": ("Customer Service", "Business"), "typing": ("Fast Typing", "Business"),
 "ms_office": ("MS Office", "Business"), "communication": ("Communication", "Soft"), "problem_solving": ("Problem Solving", "Soft"), "teamwork": ("Teamwork", "Soft"),
}

def _w(s): return {k: int(v) for k, v in (p.split(":") for p in s.split(","))}
# key: (title, category, weights, (min,max LPA), demand, remote_friendly, availability by city tier (T1,T2,T3), description)
ROLES = {
 "software_dev": ("Software Developer", "Tech", _w("python:3,sql:2,git:2,problem_solving:3,java:2,c_cpp:1"), (3.5, 8), "High", True, (3, 2, 1), "Designs, codes and tests software applications."),
 "web_dev": ("Web Developer", "Tech", _w("html_css:3,javascript:3,react:2,git:2,nodejs:2,problem_solving:1"), (3, 7), "High", True, (3, 2, 2), "Builds websites and web apps used by businesses."),
 "data_analyst": ("Data Analyst", "Data", _w("excel:3,sql:3,data_viz:3,statistics:2,python:1,communication:1"), (3.5, 7), "High", True, (3, 2, 1), "Turns raw data into insights and dashboards."),
 "ml_engineer": ("Data Scientist / ML Engineer", "Data", _w("python:3,statistics:3,machine_learning:3,pandas:2,sql:2,data_viz:1"), (5, 12), "High", True, (3, 1, 1), "Builds predictive models and AI solutions."),
 "digital_marketer": ("Digital Marketer", "Marketing", _w("seo:3,social_media:3,content_writing:2,analytics:2,email_marketing:2,communication:1"), (2.5, 6), "High", True, (3, 3, 2), "Grows brands online through SEO, social and ads."),
 "ux_designer": ("UI/UX Designer", "Creative", _w("figma:3,ux_research:3,photoshop:1,communication:2,problem_solving:1"), (3, 8), "Medium", True, (3, 2, 1), "Designs user-friendly app and website experiences."),
 "cyber_analyst": ("Cybersecurity Analyst", "Tech", _w("cybersecurity_basics:3,networking:3,linux:3,python:1,problem_solving:2"), (4, 9), "High", False, (3, 1, 1), "Protects systems and data from cyber threats."),
 "cloud_devops": ("Cloud / DevOps Engineer", "Tech", _w("linux:3,cloud:3,docker:3,git:2,networking:2,python:1"), (4, 10), "High", True, (3, 2, 1), "Automates deployment and runs applications in the cloud."),
 "qa_tester": ("QA / Software Tester", "Tech", _w("testing:3,selenium:2,sql:1,communication:1,problem_solving:2,java:1"), (2.5, 6), "Medium", True, (3, 3, 2), "Finds bugs and ensures software quality."),
 "accountant": ("Accountant / Finance Executive", "Business", _w("accounting:3,tally:3,gst:3,excel:2,ms_office:1,communication:1"), (2.2, 5), "High", False, (3, 3, 3), "Maintains books, taxes and financial records."),
 "content_writer": ("Content Writer", "Marketing", _w("content_writing:3,copywriting:3,seo:2,communication:2,social_media:1"), (2, 5), "Medium", True, (3, 3, 3), "Writes blogs, ads and web content."),
 "customer_support": ("Customer Support Executive", "Business", _w("customer_service:3,communication:3,typing:2,problem_solving:1,ms_office:1"), (2, 4), "High", True, (3, 3, 3), "Helps customers by chat, call and email."),
 "hr_exec": ("HR Executive", "Business", _w("recruitment:3,communication:3,ms_office:2,teamwork:1,negotiation:1"), (2.5, 5), "Medium", False, (3, 3, 2), "Hires talent and supports employee processes."),
 "sales_exec": ("Sales / Business Development Executive", "Business", _w("sales:3,communication:3,negotiation:2,customer_service:1,ms_office:1"), (2.5, 6), "High", False, (3, 3, 3), "Finds customers and closes deals."),
 "graphic_designer": ("Graphic Designer", "Creative", _w("photoshop:3,figma:2,communication:1,social_media:1"), (2.2, 5.5), "Medium", True, (3, 3, 2), "Creates logos, posters and social media visuals."),
}

# skill: (weeks to learn basics, free resource)
LEARN = {
 "python": (6, "CS50P / freeCodeCamp Python"), "java": (8, "NPTEL Java / Java Brains"), "javascript": (6, "freeCodeCamp JavaScript"), "sql": (3, "Khan Academy SQL / SQLBolt"),
 "html_css": (3, "freeCodeCamp Responsive Web Design"), "c_cpp": (8, "NPTEL C Programming"), "git": (1, "GitHub Skills"), "react": (4, "react.dev tutorial"),
 "nodejs": (4, "The Odin Project"), "linux": (3, "Linux Journey"), "networking": (5, "Cisco Networking Academy (free intro)"), "cloud": (6, "AWS Skill Builder / Microsoft Learn"),
 "docker": (2, "Docker official getting started"), "cybersecurity_basics": (6, "IBM SkillsBuild Cybersecurity / TryHackMe"), "testing": (3, "ISTQB foundation free notes"),
 "selenium": (3, "Selenium docs + Test Automation University"), "excel": (3, "Microsoft Learn Excel"), "statistics": (5, "Khan Academy Statistics"), "data_viz": (3, "Microsoft Learn Power BI"),
 "machine_learning": (8, "Kaggle Learn / Andrew Ng ML course"), "pandas": (3, "Kaggle Learn Pandas"), "figma": (2, "Figma learn resources"), "photoshop": (3, "Canva Design School / Adobe tutorials"),
 "ux_research": (4, "Google UX Design (audit)"), "seo": (3, "Google Search Central / HubSpot Academy"), "social_media": (2, "Meta Blueprint"), "content_writing": (3, "HubSpot Content Marketing"),
 "copywriting": (3, "Practice daily: rewrite ads"), "email_marketing": (2, "HubSpot Email Marketing"), "analytics": (2, "Google Analytics Academy"), "accounting": (5, "NPTEL / Khan Academy Accounting"),
 "tally": (3, "Tally Education free material"), "gst": (3, "GST portal tutorials"), "recruitment": (3, "LinkedIn Learning (audit) / HR blogs"), "sales": (3, "HubSpot Sales training"),
 "negotiation": (2, "Coursera audit: Negotiation"), "customer_service": (2, "Alison free course"), "typing": (2, "TypingClub (free)"), "ms_office": (2, "Microsoft Learn Office"),
 "communication": (4, "Toastmasters / practise speaking daily"), "problem_solving": (6, "Solve daily on HackerRank / puzzles"), "teamwork": (2, "Group projects & volunteering"),
}

HR_QUESTIONS = [
 ("Tell me about yourself.", "student,skills,project,learning,interest,goal,college,experience"),
 ("What are your strengths and weaknesses?", "strength,weakness,improve,learning,example,practice,team"),
 ("Describe a challenge you faced and how you solved it.", "challenge,problem,solved,action,result,team,learned"),
 ("Why should we hire you?", "skills,learn,contribute,company,value,passion,team,project"),
]
# role: [(question, keywords), ...]
TECH_QUESTIONS = {
 "software_dev": [("What is the difference between a list and a tuple in Python?", "mutable,immutable,list,tuple,memory,faster"), ("Explain object-oriented programming.", "class,object,inheritance,encapsulation,polymorphism,abstraction")],
 "web_dev": [("What is the difference between let, const and var?", "scope,block,reassign,hoisting,constant,function"), ("How do you make a website responsive?", "media,queries,flexbox,grid,viewport,mobile,relative")],
 "data_analyst": [("What is the difference between INNER JOIN and LEFT JOIN?", "matching,rows,left,null,tables,all,common"), ("How do you handle missing data?", "remove,fill,mean,median,impute,null,analysis")],
 "ml_engineer": [("Explain overfitting and how to prevent it.", "training,test,generalize,regularization,cross-validation,data,complexity"), ("Difference between supervised and unsupervised learning?", "labels,labelled,clustering,classification,regression,unlabeled")],
 "digital_marketer": [("What is SEO and how does it work?", "keywords,search,ranking,content,backlinks,traffic,optimization"), ("How do you measure a campaign's success?", "ctr,conversion,roi,traffic,analytics,engagement,cost")],
 "ux_designer": [("What is the UX design process?", "research,wireframe,prototype,test,user,iterate,feedback"), ("How do you conduct usability testing?", "users,tasks,observe,feedback,prototype,insights,improve")],
 "cyber_analyst": [("What is the CIA triad?", "confidentiality,integrity,availability,security,data,access"), ("Explain phishing and how to prevent it.", "email,fake,links,awareness,verify,mfa,training")],
 "cloud_devops": [("What is Docker and why is it used?", "container,image,portable,isolation,deploy,environment,lightweight"), ("What is CI/CD?", "continuous,integration,delivery,automation,pipeline,build,deploy,test")],
 "qa_tester": [("Difference between smoke and regression testing?", "build,stable,basic,existing,changes,functionality,retest"), ("What makes a good bug report?", "steps,reproduce,expected,actual,severity,screenshot,environment")],
 "accountant": [("What are debit and credit?", "debit,credit,ledger,account,double,entry,balance"), ("What is GST and who must register?", "tax,goods,services,turnover,registration,input,credit")],
 "content_writer": [("How do you research and structure an article?", "research,audience,outline,headings,keywords,edit,sources"), ("How do you write SEO-friendly content?", "keywords,readability,headings,meta,links,intent,original")],
 "customer_support": [("How do you handle an angry customer?", "listen,empathy,apologize,solution,calm,follow,resolve"), ("How do you prioritise multiple tickets?", "urgent,priority,impact,sla,queue,customers,resolve")],
 "hr_exec": [("How do you shortlist candidates from many resumes?", "skills,requirements,screening,keywords,experience,criteria,interview"), ("What is onboarding and why is it important?", "new,employee,orientation,training,culture,retention,productivity")],
 "sales_exec": [("How do you handle rejection?", "learn,feedback,persistent,follow,positive,improve,next"), ("Describe your sales process.", "lead,qualify,pitch,objection,close,follow,needs")],
 "graphic_designer": [("What are the principles of good design?", "balance,contrast,hierarchy,alignment,colour,typography,spacing"), ("How do you choose colours for a brand?", "brand,audience,emotion,palette,contrast,consistency,psychology")],
}
ACTION_VERBS = {"developed", "built", "created", "designed", "led", "managed", "implemented", "analyzed", "analysed", "improved", "launched",
                "organized", "organised", "automated", "increased", "reduced", "coordinated", "delivered", "wrote", "optimized", "trained", "achieved", "tested", "presented"}
