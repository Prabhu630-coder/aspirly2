

import os

import re

import urllib.request

import urllib.parse

import json

import time

from html.parser import HTMLParser

from datetime import datetime, timedelta

from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash

from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import inspect, text

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.metrics.pairwise import cosine_similarity



app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-before-deploy")

url = os.environ.get("DATABASE_URL", "sqlite:///aspirly.db")

if url.startswith("postgres://"):

    url = url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "certificates")

ALLOWED_CERTIFICATES = {"pdf", "png", "jpg", "jpeg", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)



db = SQLAlchemy(app)



ROLE_SKILLS = {

 "Full-Stack Developer":["HTML","CSS","JavaScript","Python","Flask","SQL","Git","REST APIs"],

 "Frontend Developer":["HTML","CSS","JavaScript","React","Git","UI/UX"],

 "Backend Developer":["Python","Flask","SQL","REST APIs","Git","Authentication"],

 "Data Analyst":["Python","SQL","Excel","Statistics","Data Visualization","Pandas"],

 "AI/ML Engineer":["Python","Statistics","Linear Algebra","Machine Learning","Pandas","NumPy"],

 "Cybersecurity Analyst":["Networking","Linux","Python","Security Fundamentals","OWASP","Risk Analysis"],

 "Cloud Engineer":["Linux","Networking","Git","Cloud Fundamentals","Docker","CI/CD"],

 "UI/UX Designer":["UI/UX","Wireframing","Figma","Design Thinking","Prototyping"]

}

RESOURCES = {

 "HTML":("MDN HTML Guide","https://developer.mozilla.org/en-US/docs/Learn/HTML"),

 "CSS":("MDN CSS Guide","https://developer.mozilla.org/en-US/docs/Learn/CSS"),

 "JavaScript":("JavaScript.info","https://javascript.info/"),

 "Python":("Python Tutorial","https://docs.python.org/3/tutorial/"),

 "Flask":("Flask Documentation","https://flask.palletsprojects.com/"),

 "SQL":("SQLBolt","https://sqlbolt.com/"),

 "Git":("Git Book","https://git-scm.com/book/en/v2"),

 "REST APIs":("MDN HTTP Guide","https://developer.mozilla.org/en-US/docs/Web/HTTP"),

 "React":("React Learn","https://react.dev/learn"),

 "UI/UX":("Figma Learn","https://help.figma.com/"),

 "Excel":("Microsoft Excel Help","https://support.microsoft.com/excel"),

 "Statistics":("Khan Academy Statistics","https://www.khanacademy.org/math/statistics-probability"),

 "Data Visualization":("Matplotlib Tutorials","https://matplotlib.org/stable/tutorials/"),

 "Pandas":("Pandas Getting Started","https://pandas.pydata.org/docs/getting_started/"),

 "NumPy":("NumPy Learn","https://numpy.org/learn/"),

 "Machine Learning":("Google ML Crash Course","https://developers.google.com/machine-learning/crash-course"),

 "Networking":("Cisco Networking Academy","https://www.netacad.com/"),

 "Linux":("Linux Journey","https://linuxjourney.com/"),

 "Security Fundamentals":("OWASP Top 10","https://owasp.org/www-project-top-ten/"),

 "OWASP":("OWASP Top 10","https://owasp.org/www-project-top-ten/"),

 "Cloud Fundamentals":("AWS Cloud Essentials","https://aws.amazon.com/getting-started/cloud-essentials/"),

 "Docker":("Docker Get Started","https://docs.docker.com/get-started/"),

 "CI/CD":("GitHub Actions Docs","https://docs.github.com/en/actions"),

 "Authentication":("Flask Documentation","https://flask.palletsprojects.com/"),

 "Linear Algebra":("Khan Academy Linear Algebra","https://www.khanacademy.org/math/linear-algebra"),

 "Risk Analysis":("NIST Cybersecurity Framework","https://www.nist.gov/cyberframework"),

 "Figma":("Figma Learn","https://help.figma.com/"),

 "Wireframing":("Figma Learn","https://help.figma.com/"),

 "Design Thinking":("IDEO Design Thinking","https://designthinking.ideo.com/"),

 "Prototyping":("Figma Prototyping","https://help.figma.com/")

}



class User(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    email=db.Column(db.String(160),unique=True,nullable=False,index=True)

    password_hash=db.Column(db.String(255),nullable=False)

    role=db.Column(db.String(20),nullable=False,default="student")

    created_at=db.Column(db.DateTime,default=datetime.utcnow)

    student=db.relationship("Student",backref="user",uselist=False,cascade="all, delete-orphan")

    company=db.relationship("Company",backref="user",uselist=False,cascade="all, delete-orphan")

    def set_password(self,p): self.password_hash=generate_password_hash(p)

    def check_password(self,p): return check_password_hash(self.password_hash,p)



class Student(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),unique=True,nullable=True)

    name=db.Column(db.String(100),nullable=False,default="Student")

    email=db.Column(db.String(160),default="")

    education=db.Column(db.String(100),default="")

    branch=db.Column(db.String(100),default="")

    year=db.Column(db.String(40),default="")

    current_skills=db.Column(db.Text,default="")

    soft_skills=db.Column(db.Text,default="")

    interests=db.Column(db.Text,default="")

    target_role=db.Column(db.String(100),default="Full-Stack Developer")

    preferred_types=db.Column(db.Text,default="Internship,Hackathon,Competition,Project,Course")

    learning_hours=db.Column(db.Integer,default=5)

    github_username=db.Column(db.String(100),default="")

    github_profile_url=db.Column(db.String(500),default="")



class Company(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),unique=True,nullable=False)

    company_name=db.Column(db.String(180),nullable=False)

    website=db.Column(db.String(500),default="")

    description=db.Column(db.Text,default="")



class RoadmapTask(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    student_id=db.Column(db.Integer,db.ForeignKey("student.id"),nullable=False)

    skill=db.Column(db.String(100),nullable=False)

    resource_name=db.Column(db.String(160),default="")

    resource_url=db.Column(db.String(500),default="")

    mini_project=db.Column(db.String(250),default="")

    completed=db.Column(db.Boolean,default=False)

    order_no=db.Column(db.Integer,default=0)



class SkillVerification(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    student_id=db.Column(db.Integer,db.ForeignKey("student.id"),nullable=False)

    skill=db.Column(db.String(100),nullable=False)

    method=db.Column(db.String(30),nullable=False)  # test / certificate

    status=db.Column(db.String(30),nullable=False,default="pending")

    score=db.Column(db.Integer,nullable=True)

    certificate_file=db.Column(db.String(300),default="")

    created_at=db.Column(db.DateTime,default=datetime.utcnow)



class Opportunity(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    title=db.Column(db.String(180),nullable=False)

    kind=db.Column(db.String(50),nullable=False)

    description=db.Column(db.Text,default="")

    skills=db.Column(db.Text,default="")

    eligibility=db.Column(db.String(250),default="Check the organizer's official page")

    deadline=db.Column(db.String(80),default="Not specified")

    location=db.Column(db.String(100),default="Online")

    source_name=db.Column(db.String(120),default="ASPIRLY illustrative sample")

    source_url=db.Column(db.String(500),default="")

    is_sample=db.Column(db.Boolean,default=True)

    company_id=db.Column(db.Integer,db.ForeignKey("company.id"),nullable=True)

    company=db.relationship("Company",backref="opportunities")



class InternshipNotification(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    student_id=db.Column(db.Integer,db.ForeignKey("student.id"),nullable=False,index=True)

    opportunity_id=db.Column(db.Integer,db.ForeignKey("opportunity.id"),nullable=False)

    match_score=db.Column(db.Integer,default=0)

    matched_skills=db.Column(db.Text,default="")

    seen=db.Column(db.Boolean,default=False)

    created_at=db.Column(db.DateTime,default=datetime.utcnow)

    opportunity=db.relationship("Opportunity")



def items(s): return [x.strip() for x in (s or "").split(",") if x.strip()]

def current_user(): return User.query.get(session.get("user_id")) if session.get("user_id") else None



@app.context_processor

def inject_user(): return {"current_user": current_user()}



def login_required(fn):

    @wraps(fn)

    def wrapper(*a,**kw):

        if not current_user():

            flash("Please log in to continue.","warning")

            return redirect(url_for("login",next=request.path))

        return fn(*a,**kw)

    return wrapper



def role_required(role):

    def deco(fn):

        @wraps(fn)

        def wrapper(*a,**kw):

            u=current_user()

            if not u: return redirect(url_for("login"))

            if u.role != role: abort(403)

            return fn(*a,**kw)

        return wrapper

    return deco



def student_record():

    u=current_user()

    if not u or u.role!="student": return None

    s=u.student

    if not s:

        s=Student(user_id=u.id,name="Student",email=u.email,target_role="Full-Stack Developer")

        db.session.add(s); db.session.commit()

    return s



def gaps_for(s):

    needed=ROLE_SKILLS.get(s.target_role,ROLE_SKILLS["Full-Stack Developer"])

    verified={v.skill.lower() for v in SkillVerification.query.filter_by(student_id=s.id,status="verified").all()}

    have={x.lower() for x in items(s.current_skills)} | verified

    return [x for x in needed if x.lower() not in have]



def make_roadmap(s):

    present={t.skill.lower() for t in RoadmapTask.query.filter_by(student_id=s.id).all()}

    project_examples={"HTML":"Build a personal portfolio page","CSS":"Make your portfolio responsive","JavaScript":"Build an interactive task tracker","Python":"Create a command-line study planner","Flask":"Build a small Flask CRUD app","SQL":"Design a database for a student portal","Git":"Publish and document a project repository","REST APIs":"Build and test a JSON API"}

    for i,skill in enumerate(gaps_for(s)):

        if skill.lower() in present: continue

        rn,ru=RESOURCES.get(skill,("Search learning resources","https://www.google.com/search?q="+skill.replace(" ","+")+"+tutorial"))

        db.session.add(RoadmapTask(student_id=s.id,skill=skill,resource_name=rn,resource_url=ru,mini_project=project_examples.get(skill,f"Build a small practical project using {skill}"),order_no=i))

    db.session.commit()





# ---- AspirlyAI: web-aware open-model career agent --------------------------

# The previous TF-IDF assistant is kept as a safe fallback, but the primary

# path now retrieves fresh public web information and asks an open-weight LLM

# to synthesize a personalized, source-grounded answer.

ASPERLYAI_KNOWLEDGE = [

    ("What should I learn next?", "Use your Learning Roadmap as the priority list. Start with the first unfinished skill, study the linked resource, build its mini-project, and then verify the skill through the assessment or certificate upload."),

    ("How can I improve my skills?", "Pick one roadmap skill at a time, learn the fundamentals, practice with small exercises, build a project, and verify the skill. Consistency beats trying to learn many technologies at once."),

    ("How do I verify a skill?", "Open My Profile or Learning Roadmap and choose the skill test. A score of 70% or higher verifies the skill. You can also upload a completed course certificate."),

    ("What are my skill gaps?", "Your skill gaps are the skills required for your target role that are not yet in your current skills or verified skills. I can use your profile to explain which gaps should be prioritized."),

    ("How should I prepare for an internship?", "Build 2–3 practical projects, verify your core skills, keep your GitHub profile updated, and review opportunities that match your skills. Focus on evidence of what you can build, not only certificates."),

    ("How should I build my resume?", "Keep your resume focused on your target role: education, verified technical skills, 2–3 strong projects, GitHub, measurable project outcomes, and relevant experience. Avoid listing skills you cannot demonstrate."),

    ("How can I prepare for an interview?", "Revise fundamentals for your target role, practise explaining your projects, prepare common technical questions, and rehearse concise answers about your decisions, challenges and results."),

    ("Which project should I build?", "Choose a project that uses one or more skills from your roadmap and solves a real student or community problem. A small finished project with a clear README is stronger than an unfinished large idea."),

    ("What is GitHub useful for?", "GitHub is your public proof of practical work. Keep repositories organized, add READMEs, meaningful commits and working demos where possible, then link your profile in ASPIRLY."),

    ("What career should I choose?", "Start from your interests and strengths, then compare them with the skills required by roles you are considering. ASPIRLY's target role and roadmap can help you turn that choice into an actionable learning plan."),

    ("How can I use ASPIRLY?", "Use My Profile to describe your goals and skills, Learning Roadmap to learn and verify skills, Opportunities to explore matches, and AspirlyAI for personalized guidance."),

    ("What should I do today?", "Choose one unfinished roadmap skill, spend a focused study session on it, and complete a small practical task. If you have enough confidence, take the skill assessment and work toward verification."),

]

ASPERLYAI_VECTORIZER = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2))

ASPERLYAI_MATRIX = ASPERLYAI_VECTORIZER.fit_transform([q for q, _ in ASPERLYAI_KNOWLEDGE])



class _SearchParser(HTMLParser):

    def __init__(self):

        super().__init__(); self.results=[]; self._a=None; self._buf=[]

    def handle_starttag(self, tag, attrs):

        if tag.lower()=="a":

            self._a=dict(attrs); self._buf=[]

    def handle_data(self, data):

        if self._a is not None: self._buf.append(data)

    def handle_endtag(self, tag):

        if tag.lower()=="a" and self._a is not None:

            href=self._a.get("href",""); title=" ".join("".join(self._buf).split())

            if href.startswith("http") and title:

                self.results.append((title,href))

            self._a=None; self._buf=[]



class _TextParser(HTMLParser):

    def __init__(self):

        super().__init__(); self.parts=[]; self.skip=0

    def handle_starttag(self, tag, attrs):

        if tag.lower() in {"script","style","noscript","svg"}: self.skip+=1

    def handle_endtag(self, tag):

        if tag.lower() in {"script","style","noscript","svg"} and self.skip: self.skip-=1

    def handle_data(self, data):

        if not self.skip:

            x=" ".join(data.split())

            if x: self.parts.append(x)



def _html_text(html, limit=7000):

    parser=_TextParser()

    try: parser.feed(html)

    except Exception: pass

    return " ".join(parser.parts)[:limit]



def _fetch_url(url, timeout=8):
    req=urllib.request.Request(
        url,
        headers={
            "User-Agent":"AspirlyAI/3.0 (+https://aspirly.app; student-career-research)",
            "Accept":"text/html,application/json;q=0.9,*/*;q=0.8"
        }
    )

    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw=r.read(120000)
        charset=r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="ignore")



_WEB_CACHE={}



def _duck_search(query,max_results=6):

    q=" ".join((query or "").split())[:400]

    if not q: return []

    html=_fetch_url("https://html.duckduckgo.com/html/?q="+urllib.parse.quote(q),timeout=10)

    parser=_SearchParser(); parser.feed(html)

    sources=[]; seen=set()

    for title,url in parser.results:

        low=url.lower()

        if url in seen or any(x in low for x in ["duckduckgo.com","facebook.com","instagram.com","youtube.com"]): continue

        seen.add(url)

        try: page=_html_text(_fetch_url(url,timeout=7),7000)

        except Exception: page=""

        if page:

            sources.append({"title":title[:220],"url":url[:700],"text":page,"source":"DuckDuckGo"})

        if len(sources)>=max_results: break

    return sources



def aspirly_web_search(query, max_results=6):

    """Real public-web retrieval. Tavily is preferred; DDG is a no-key fallback.

    Results are cached briefly so one student question does not repeatedly hit the web.

    """

    q=" ".join((query or "").split())[:500]

    if not q: return []

    key=q.lower()

    now=time.time()

    cached=_WEB_CACHE.get(key)

    if cached and now-cached[0] < 300: return cached[1]

    sources=[]

    try:

        # Public web retrieval needs no second API key. The reasoning and

        # synthesis model is provided by Gemini via GEMINI_API_KEY.

        sources=_duck_search(q,max_results)

    except Exception as exc:

        app.logger.warning("Public web search failed: %s",exc)

    # De-duplicate by URL and cap context size.

    unique=[]; seen=set()

    for x in sources:

        u=x.get("url","")

        if u and u not in seen:

            seen.add(u); unique.append(x)

        if len(unique)>=max_results: break

    _WEB_CACHE[key]=(now,unique)

    return unique



def _student_context(s):

    verified=[v.skill for v in SkillVerification.query.filter_by(student_id=s.id,status="verified").all()]

    tasks=RoadmapTask.query.filter_by(student_id=s.id).order_by(RoadmapTask.order_no,RoadmapTask.id).all()

    next_task=next((t for t in tasks if not t.completed),None)

    return {

        "name":s.name,"education":s.education,"branch":s.branch,"year":s.year,

        "current_skills":items(s.current_skills),"verified_skills":verified,

        "interests":items(s.interests),"soft_skills":items(s.soft_skills),

        "target_role":s.target_role,"preferred_types":items(s.preferred_types),

        "learning_hours":s.learning_hours,"skill_gaps":gaps_for(s),

        "next_roadmap_skill":next_task.skill if next_task else None,

        "next_roadmap_project":next_task.mini_project if next_task else None,

    }



def _fallback_aspirlyai(message,s):

    # This is intentionally only a failure/status response. AspirlyAI no longer

    # pretends a canned answer is an AI research answer when the model is unavailable.

    return ("I can't produce a real research-backed answer right now because the AI "

            "reasoning service is unavailable. Please configure GEMINI_API_KEY on the server "

            "and try again. I won't substitute a canned answer for your question.")



def _json_from_model(text):

    text=(text or "").strip()

    if text.startswith("```"):

        text=text.strip("`")

        if text.startswith("json"): text=text[4:]

    try: return json.loads(text)

    except Exception: pass

    m=re.search(r"**{**.***}**",text,re.S)

    if m:

        try: return json.loads(m.group(0))

        except Exception: pass

    return None



def _gemini_chat(messages,max_tokens=700,temperature=0.2):

    token=os.environ.get("GEMINI_API_KEY","").strip()

    if not token:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured on the server"
        )

    model=os.environ.get(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    ).strip()

    if not model:
        model="gemini-3.8-flash"

    system_parts=[]
    contents=[]

    for message in messages or []:

        if not isinstance(message,dict):
            continue

        role=str(message.get("role") or "").strip().lower()
        content=message.get("content","")

        if not isinstance(content,str):
            if isinstance(content,list):
                pieces=[]
                for part in content:
                    if isinstance(part,dict):
                        part_text=part.get("text")
                        if isinstance(part_text,str):
                            pieces.append(part_text)
                content="\n".join(pieces)
            else:
                content=str(content or "")

        content=content.strip()

        if not content:
            continue

        if role=="system":
            system_parts.append(content)
        elif role=="assistant" or role=="model":
            contents.append({
                "role":"model",
                "parts":[{"text":content}]
            })
        else:
            contents.append({
                "role":"user",
                "parts":[{"text":content}]
            })

    if not contents:
        raise RuntimeError(
            "Gemini request contained no usable messages"
        )

    payload={
        "contents":contents,
        "generationConfig":{
            "maxOutputTokens":max_tokens
        }
    }

    if system_parts:
        payload["systemInstruction"]={
            "parts":[
                {"text":"\n\n".join(system_parts)}
            ]
        }

    endpoint=(
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        + urllib.parse.quote(model,safe="")
        + ":generateContent"
    )

    req=urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key":token,
            "Content-Type":"application/json",
            "Accept":"application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(req,timeout=90) as r:
            body=r.read().decode(
                "utf-8",
                errors="ignore"
            )
            data=json.loads(body)

        candidates=data.get("candidates") or []

        if not candidates:
            prompt_feedback=data.get("promptFeedback") or {}
            raise RuntimeError(
                "Gemini returned no candidates"
                + (
                    f": {json.dumps(prompt_feedback,ensure_ascii=False)}"
                    if prompt_feedback else ""
                )
            )

        parts=(
            (candidates[0].get("content") or {}).get("parts")
            or []
        )

        answer_parts=[]

        for part in parts:
            if isinstance(part,dict):
                part_text=part.get("text")

                if isinstance(part_text,str):
                    answer_parts.append(part_text)

        answer="\n".join(answer_parts).strip()

        if answer:
            return answer

        finish_reason=candidates[0].get("finishReason")

        raise RuntimeError(
            "Gemini returned no usable text content"
            + (
                f" (finish reason: {finish_reason})"
                if finish_reason else ""
            )
        )

    except urllib.error.HTTPError as exc:

        body=""

        try:
            body=exc.read().decode(
                "utf-8",
                errors="ignore"
            )[:1600]
        except Exception:
            pass

        msg=(
            f"HTTP {exc.code} from Gemini "
            f"for {model}: "
            f"{body or exc.reason}"
        )

        app.logger.error(msg)

        raise RuntimeError(msg) from exc

    except urllib.error.URLError as exc:

        msg=f"Gemini connection error for {model}: {exc}"

        app.logger.error(msg)

        raise RuntimeError(msg) from exc

    except RuntimeError:

        raise

    except Exception as exc:

        msg=(
            f"{type(exc).__name__} from Gemini "
            f"for {model}: {exc}"
        )

        app.logger.exception(msg)

        raise RuntimeError(msg) from exc


def _research_queries(question, context):

    """Build several focused public-web queries without spending an extra AI call.

    The actual reasoning/synthesis is performed by the Gemini model.

    """

    q=" ".join((question or "").split())[:500]

    role=str(context.get("target_role") or "").strip()

    queries=[q]

    if role and role.lower() not in q.lower():

        queries.append(f"{q} {role}")

    # Bias searches toward primary sources when the question is about current facts.

    low=q.lower()

    if any(k in low for k in ("internship","intern","job","hiring","deadline","salary","company","course","latest","current","2026")):

        queries.append(f"{q} official")

    return list(dict.fromkeys(x for x in queries if x.strip()))[:3]



def _research_agent(question, context, history=None):

    """One Gemini reasoning call + live public-web evidence.



    Keeping research planning local avoids wasting a second inference call. The

    Gemini provides the generative AI used for the final answer.

    """

    queries=_research_queries(question,context)

    sources=[]

    for q in queries:

        sources.extend(aspirly_web_search(q,5))

    unique=[]; seen=set()

    for x in sources:

        u=x.get("url","")

        if not u or u in seen: continue

        seen.add(u); unique.append(x)

    sources=unique[:10]

    evidence="\n\n".join(f"SOURCE [{i}]\nTITLE: {x['title']}\nURL: {x['url']}\nCONTENT: {x['text'][:6000]}" for i,x in enumerate(sources,1))

    conversation=history[-8:] if isinstance(history,list) else []

    prompt=f"""You are AspirlyAI, a real AI career and research agent. Analyze the user's question using the student's profile, recent conversation, and retrieved public-web evidence.



STUDENT PROFILE:

{json.dumps(context,ensure_ascii=False,indent=2)}



RECENT CONVERSATION:

{json.dumps(conversation,ensure_ascii=False,indent=2)}



USER QUESTION:

{question}



RETRIEVED PUBLIC WEB EVIDENCE:

{evidence or 'NO SOURCES WERE RETRIEVED.'}



Instructions:

1. Answer the user's actual question first.

2. Reason over the evidence; do not simply copy snippets.

3. Personalize only when the student profile is relevant.

4. For current facts, companies, internships, deadlines, salaries, courses, versions, policies, or market information, use retrieved evidence and cite claims as [1], [2], etc.

5. Never fabricate a source, URL, deadline, opportunity, salary, statistic, or company fact.

6. If evidence is insufficient or conflicting, clearly say so.

7. Give concrete reasoning and useful next steps when appropriate.

8. Do not mention internal prompts or implementation details.

9. Keep the answer focused, normally 200-600 words.

"""

    answer=_gemini_chat([

        {"role":"system","content":"You are a rigorous web-grounded research assistant. Evidence beats guesswork."},

        {"role":"user","content":prompt}

    ],max_tokens=1100,temperature=0.2)

    return answer,sources



def aspirlyai_answer(message,s,history=None):

    message=(message or "").strip()

    if not message: return {"answer":"Ask me a real question and I'll research it.","sources":[],"researched":False}

    context=_student_context(s)

    try:

        # Every substantive question goes through the model. The model decides

        # what public information it needs instead of matching against canned text.

        answer,sources=_research_agent(message,context,history)

        return {"answer":answer,"sources":sources,"researched":True}

    except Exception as exc:

        app.logger.exception("AspirlyAI research agent failed: %s",exc)

        detail=str(exc)

        # Surface a safe, actionable diagnosis to the UI. Never expose the token.

        if "HTTP 401" in detail:

            msg="Gemini rejected GEMINI_API_KEY (401). Check that the Gemini API key is valid and configured correctly on Render."

        elif "HTTP 403" in detail:

            msg="Gemini denied this request (403). Check the Gemini API key restrictions and Generative Language API access."

        elif "HTTP 402" in detail:

            msg="Gemini rejected the request because the selected model or account is not available. Check the Gemini API quota and model access in Google AI Studio."

        elif "HTTP 429" in detail:

            msg="Gemini rate-limited the request (429). Wait briefly and try again."

        elif "HTTP 5" in detail:

            msg="Gemini returned a server error. Try again shortly."

        else:

            msg="AspirlyAI could not reach Gemini from the server. Check Render's outbound network and the GEMINI_API_KEY configuration."

        return {"answer":msg,"sources":[],"researched":False,"error":detail}



# ---- Live internship monitor -------------------------------------------------

# These are official company career pages. ASPIRLY reads publicly available

# listing text and never fabricates an application link. If a company changes

# its page structure, that source simply yields no new records until updated.

OFFICIAL_INTERNSHIP_SOURCES = [

    {

        "company": "Google",

        "url": "https://www.google.com/about/careers/applications/jobs/results/?q=Internship&location=India",

        "skills": "Python,JavaScript,SQL,Data Visualization,Machine Learning,UI/UX,Cloud Fundamentals",

    },

    {

        "company": "Microsoft",

        "url": "https://careers.microsoft.com/v2/global/en/students?country=251",

        "skills": "Python,JavaScript,C++,SQL,Azure,Cloud Fundamentals,AI,Machine Learning,UI/UX",

    },

    {

        "company": "Amazon",

        "url": "https://www.amazon.jobs/en/search?base_query=intern&country=IND&loc_query=India",

        "skills": "Python,Java,JavaScript,SQL,Data Analytics,Machine Learning,Cloud Fundamentals,Software Development",

    },

    {

        "company": "IBM",

        "url": "https://www.ibm.com/careers/search?field_keyword_05%5B0%5D=internship",

        "skills": "Python,Java,SQL,Cloud Fundamentals,Machine Learning,Data Analytics,AI,Cybersecurity",

    },

]



class _CareerLinkParser(HTMLParser):

    def __init__(self):

        super().__init__()

        self.links=[]

        self.href=None

        self.parts=[]

    def handle_starttag(self,tag,attrs):

        if tag.lower()=="a":

            self.href=dict(attrs).get("href")

            self.parts=[]

    def handle_data(self,data):

        if self.href is not None: self.parts.append(data.strip())

    def handle_endtag(self,tag):

        if tag.lower()=="a" and self.href is not None:

            title=" ".join(x for x in self.parts if x).strip()

            if title: self.links.append((title,self.href))

            self.href=None; self.parts=[]



def _fetch_official(url):

    req=urllib.request.Request(url,headers={"User-Agent":"ASPIRLY Internship Monitor/1.0"})

    with urllib.request.urlopen(req,timeout=12) as r:

        return r.read().decode("utf-8","ignore")



def _absolute_url(base,href):

    return urllib.parse.urljoin(base,href)



def sync_official_internships(force=False):

    """Fetch official career pages and add only new internship listings.

    Returns (added_count, failed_sources). It is intentionally best-effort:

    career sites may block automated requests or change their markup.

    """

    added=0; failed=[]

    seen_urls={o.source_url for o in Opportunity.query.filter_by(is_sample=False).all()}

    for src in OFFICIAL_INTERNSHIP_SOURCES:

        try:

            html=_fetch_official(src["url"])

            parser=_CareerLinkParser(); parser.feed(html)

            found=0

            for raw_title,href in parser.links:

                title=re.sub(r"\s+"," ",raw_title).strip()

                low=title.lower()

                if not any(k in low for k in ("intern","internship","student program","university intern","explore")):

                    continue

                if len(title)<8 or len(title)>180: continue

                link=_absolute_url(src["url"],href)

                if not link.startswith("http") or link in seen_urls: continue

                # Keep this monitor internship-focused; avoid unrelated navigation.

                skills=src["skills"]

                desc=f"Live internship/student opportunity discovered from {src['company']}'s official careers site. Verify eligibility, location and closing date on the official listing before applying."

                o=Opportunity(title=title,kind="Internship",description=desc,skills=skills,eligibility="See the official company listing for current eligibility.",deadline="See official listing",location="India / varies",source_name=src["company"]+" Careers (official)",source_url=link,is_sample=False)

                db.session.add(o); db.session.flush(); seen_urls.add(link); added+=1; found+=1

                if found>=12: break

            db.session.commit()

        except Exception as exc:

            db.session.rollback(); failed.append(src["company"])

    return added, failed



_last_live_sync=None

def maybe_sync_official_internships(force=False):

    global _last_live_sync

    if force or _last_live_sync is None or datetime.utcnow()-_last_live_sync>timedelta(hours=6):

        result=sync_official_internships(force=force)

        _last_live_sync=datetime.utcnow()

        return result

    return (0,[])



def create_internship_notifications(s):

    """Create in-app alerts only for live internships that match profile skills."""

    live=Opportunity.query.filter_by(kind="Internship",is_sample=False).order_by(Opportunity.id.desc()).all()

    existing={n.opportunity_id for n in InternshipNotification.query.filter_by(student_id=s.id).all()}

    created=0

    for o in live:

        score,matched,missing,why=score_for(s,o)

        if score<=0 or o.id in existing: continue

        db.session.add(InternshipNotification(student_id=s.id,opportunity_id=o.id,match_score=score,matched_skills=", ".join(matched),seen=False))

        created+=1

    if created: db.session.commit()

    return created



def score_for(s,o):

    have={x.lower() for x in items(s.current_skills)}

    have |= {v.skill.lower() for v in SkillVerification.query.filter_by(student_id=s.id,status="verified").all()}

    need={x.lower() for x in items(o.skills)}

    matched=sorted(have & need); missing=sorted(need-have)

    score=round(100*len(matched)/max(1,len(need)))

    why=("Your profile includes "+", ".join(matched[:4])) if matched else "This may help you explore a related skill area"

    return score,matched,missing,why



# Small built-in question generator. It creates a different assessment set per skill.

QUESTION_BANK = {

 "Python":[("Which keyword defines a function in Python?",["func","def","function","define"],1),

           ("What data type stores key-value pairs?",["list","tuple","dict","set"],2),

           ("What does len([1,2,3]) return?",["2","3","4","None"],1),

           ("Which symbol starts a comment?",["//","#","<!--","--"],1),

           ("Which is immutable?",["list","dict","set","tuple"],3)],

 "HTML":[("Which tag creates a hyperlink?",["<link>","<a>","<href>","<url>"],1),

         ("Which tag is the largest heading?",["<h6>","<head>","<h1>","<title>"],2),

         ("Which attribute provides image alternative text?",["src","alt","href","title"],1),

         ("Which tag creates a form?",["<input>","<form>","<fieldset>","<button>"],1),

         ("Which tag creates a paragraph?",["<p>","<para>","<text>","<pg>"],0)],

 "CSS":[("Which property changes text color?",["font-style","color","text-style","background"],1),

        ("Which layout system uses display:flex?",["Flexbox","GridBox","FloatBox","BlockBox"],0),

        ("Which selector targets an id?",[".","#","*","@"],1),

        ("Which property controls spacing inside an element?",["margin","padding","gap","border"],1),

        ("Which unit is relative to the root font size?",["px","em","rem","vh"],2)],

 "JavaScript":[("Which keyword declares a block-scoped variable?",["var","let","define","dim"],1),

               ("Which method converts JSON text to an object?",["JSON.parse","JSON.stringify","JSON.object","parse.JSON"],0),

               ("Which symbol is strict equality?",["=","==","===","=>"],2),

               ("Which is an array method?",["map","loop","each","arrayify"],0),

               ("Which keyword defines a constant binding?",["fixed","const","static","final"],1)],

 "SQL":[("Which command reads rows from a table?",["GET","SELECT","READ","FETCH"],1),

        ("Which clause filters rows?",["SORT","WHERE","FILTER","HAVING"],1),

        ("Which command adds a row?",["ADD","INSERT","APPEND","PUSH"],1),

        ("Which keyword sorts results?",["ORDER BY","GROUP","SORT BY","ARRANGE"],0),

        ("Which command changes existing rows?",["CHANGE","UPDATE","MODIFY","ALTER"],1)],

 "Git":[("Which command copies a remote repository?",["git pull","git clone","git copy","git fork"],1),

        ("Which command records staged changes?",["git save","git commit","git push","git record"],1),

        ("Which command sends commits to a remote?",["git send","git upload","git push","git publish"],2),

        ("Which command creates a new branch?",["git branch","git new","git split","git line"],0),

        ("Which file commonly stores ignored paths?",[".gitignore",".ignoregit","git.ignore",".gitfiles"],0)]

}



def questions_for(skill):

    qs=QUESTION_BANK.get(skill)

    if qs: return qs

    # Generic skill assessment: tests fundamentals, terminology and application.

    return [

      (f"What is the main purpose of {skill}?",[f"To apply {skill} concepts to solve problems","Only to browse the web","Only to edit images","None"],0),

      (f"Which approach is best when learning {skill}?",["Practice and build projects","Memorize without practice","Avoid documentation","Skip fundamentals"],0),

      (f"What should you use to verify a result in {skill}?",["Evidence, tests, or a reproducible example","A random guess","No validation","Only a screenshot"],0),

      (f"Which is a strong beginner habit for {skill}?",["Read documentation and practice","Copy everything blindly","Never debug","Avoid examples"],0),

      (f"What demonstrates practical {skill} ability best?",["A working project or assessment","A blank file","A username","A wallpaper"],0)

    ]



def seed():

    if Opportunity.query.first(): return

    data=[

     ("Build for Impact Mini Hackathon","Hackathon","A beginner-friendly team challenge to prototype a useful digital solution.","Python,JavaScript,HTML,CSS,Git","Student teams; confirm organizer rules.","Demo deadline: 30 Nov 2026","Online","ASPIRLY illustrative sample","https://example.com/hackathon"),

     ("Campus Project Collaborator","Project","Collaborate on a small web application and build a portfolio project.","HTML,CSS,JavaScript,Python,Git","Students interested in web development.","Rolling / sample","Remote","ASPIRLY illustrative sample","https://example.com/project"),

     ("Python Foundations Learning Track","Course","A beginner learning path with practice exercises.","Python","Open to beginners.","No deadline listed","Online","Python.org","https://docs.python.org/3/tutorial/"),

     ("Junior Web Developer Internship","Internship","Illustrative internship listing for students building web fundamentals.","HTML,CSS,JavaScript,Git,REST APIs","Sample eligibility: students with basic web projects.","Demo deadline: 15 Dec 2026","Hybrid / sample","ASPIRLY illustrative sample","https://example.com/internship"),

     ("Student Data Challenge","Competition","Analyze a dataset and present evidence-based insights.","Python,SQL,Statistics,Data Visualization","Check official competition rules.","Demo deadline: 10 Dec 2026","Online","ASPIRLY illustrative sample","https://example.com/competition")]

    for d in data:

        db.session.add(Opportunity(title=d[0],kind=d[1],description=d[2],skills=d[3],eligibility=d[4],deadline=d[5],location=d[6],source_name=d[7],source_url=d[8],is_sample=True))

    db.session.commit()



def migrate_old_schema():

    # Adds the new student user_id column when an older SQLite/Postgres database is reused.

    insp=inspect(db.engine)

    tables=insp.get_table_names()

    if "student" in tables:

        cols={c["name"] for c in insp.get_columns("student")}

        with db.engine.begin() as con:

            if "user_id" not in cols:

                con.execute(text("ALTER TABLE student ADD COLUMN user_id INTEGER"))

            if "github_username" not in cols:

                con.execute(text("ALTER TABLE student ADD COLUMN github_username VARCHAR(100) DEFAULT ''"))

            if "github_profile_url" not in cols:

                con.execute(text("ALTER TABLE student ADD COLUMN github_profile_url VARCHAR(500) DEFAULT ''"))

    db.create_all()

    # Attach the old single profile to a local migration account if an old DB exists.

    old=Student.query.filter(Student.user_id.is_(None)).first()

    if old and not User.query.filter_by(email="migrated@aspirly.local").first():

        u=User(email="migrated@aspirly.local",role="student")

        u.set_password("ChangeMe123!")

        db.session.add(u); db.session.flush()

        old.user_id=u.id

        old.email=old.email or u.email

        db.session.commit()



@app.route("/login",methods=["GET","POST"])

def login():

    if current_user(): return redirect(url_for("index") if current_user().role=="student" else url_for("company_dashboard"))

    if request.method=="POST":

        email=request.form.get("email","").strip().lower()

        password=request.form.get("password","")

        u=User.query.filter_by(email=email).first()

        if not u or not u.check_password(password):

            flash("Invalid email or password.","error")

        else:

            session.clear(); session["user_id"]=u.id

            flash("Welcome back!","success")

            return redirect(request.args.get("next") or (url_for("index") if u.role=="student" else url_for("company_dashboard")))

    return render_template("login.html")



@app.route("/register",methods=["GET","POST"])

def register():

    if current_user(): return redirect(url_for("index"))

    if request.method=="POST":

        role=request.form.get("role","student")

        email=request.form.get("email","").strip().lower()

        password=request.form.get("password","")

        confirm=request.form.get("confirm_password","")

        if role not in ("student","company"): flash("Choose a valid account type.","error")

        elif "@" not in email: flash("Enter a valid email address.","error")

        elif len(password)<8: flash("Password must be at least 8 characters.","error")

        elif password!=confirm: flash("Passwords do not match.","error")

        elif User.query.filter_by(email=email).first(): flash("An account with this email already exists.","error")

        else:

            u=User(email=email,role=role); u.set_password(password); db.session.add(u); db.session.flush()

            if role=="student":

                db.session.add(Student(user_id=u.id,name=request.form.get("name","Student").strip() or "Student",email=email,target_role="Full-Stack Developer"))

            else:

                db.session.add(Company(user_id=u.id,company_name=request.form.get("company_name","Company").strip() or "Company",website=request.form.get("website","").strip()))

            db.session.commit()

            session.clear(); session["user_id"]=u.id

            flash("Account created successfully.","success")

            return redirect(url_for("index") if role=="student" else url_for("company_dashboard"))

    return render_template("register.html")



@app.get("/logout")

def logout():

    session.clear(); flash("You have been logged out.","success"); return redirect(url_for("login"))



@app.route("/settings",methods=["GET","POST"])

@login_required

def settings():

    u=current_user()

    if request.method=="POST":

        old=request.form.get("current_password","")

        new=request.form.get("new_password","")

        confirm=request.form.get("confirm_password","")

        if not u.check_password(old): flash("Current password is incorrect.","error")

        elif len(new)<8: flash("New password must be at least 8 characters.","error")

        elif new!=confirm: flash("New passwords do not match.","error")

        else:

            u.set_password(new); db.session.commit(); flash("Password updated successfully.","success")

    return render_template("settings.html",u=u,company=u.company if u.role=="company" else None)





@app.get("/asperlyai")

@login_required

@role_required("student")

def asperlyai():

    s=student_record()

    return render_template("asperlyai.html", s=s)



@app.post("/api/asperlyai")

@login_required

@role_required("student")

def asperlyai_api():

    # Never let a web/LLM/DB-side failure turn into a generic browser

    # "could not reach AspirlyAI" message. Return JSON even when the

    # advanced AI layer is unavailable.

    try:

        data=request.get_json(silent=True) or {}

        message=str(data.get("message", ""))[:1000]

        if not message.strip():

            return {"answer":"Hi! I'm AspirlyAI. Ask me anything about your career journey.","assistant":"AspirlyAI","web_research":False}

        history=data.get("history",[])

        if not isinstance(history,list): history=[]

        result=aspirlyai_answer(message, student_record(), history=history[-8:])

        return {"answer":result["answer"],"sources":result.get("sources",[]),"assistant":"AspirlyAI","web_research":result.get("researched",False)}

    except Exception as exc:

        # Keep the endpoint usable if an external service or optional AI

        # component fails. The actual exception is logged on the server.

        app.logger.exception("AspirlyAI API error: %s", exc)

        try:

            s=student_record()

            fallback=_fallback_aspirlyai(message if 'message' in locals() else "", s)

        except Exception:

            fallback="AspirlyAI's advanced research service is temporarily unavailable. Please try again in a moment."

        return {"answer":fallback,"assistant":"AspirlyAI","web_research":False,"degraded":True}, 200



@app.route("/")

@login_required

@role_required("student")

def index():

    s=student_record(); make_roadmap(s)

    maybe_sync_official_internships()

    create_internship_notifications(s)

    tasks=RoadmapTask.query.filter_by(student_id=s.id).order_by(RoadmapTask.order_no, RoadmapTask.id).all()

    opps=Opportunity.query.all()

    matches=[(o,*score_for(s,o)) for o in opps]; matches.sort(key=lambda x:x[1],reverse=True)

    verified=SkillVerification.query.filter_by(student_id=s.id,status="verified").all()

    notifications=InternshipNotification.query.filter_by(student_id=s.id,seen=False).order_by(InternshipNotification.created_at.desc()).limit(5).all()

    return render_template("index.html",s=s,tasks=tasks,gaps=gaps_for(s),matches=matches[:3],done=sum(t.completed for t in tasks),total=len(tasks),verified=verified,notifications=notifications)



@app.route("/profile",methods=["GET","POST"])

@login_required

@role_required("student")

def profile():

    s=student_record(); roles=list(ROLE_SKILLS); types=["Internship","Hackathon","Competition","Project","Course"]

    if request.method=="POST":

        s.name=request.form.get("name","").strip() or "Student"; s.email=current_user().email

        s.education=request.form.get("education",""); s.branch=request.form.get("branch",""); s.year=request.form.get("year","")

        s.current_skills=request.form.get("current_skills","").strip(); s.soft_skills=request.form.get("soft_skills","").strip()

        s.interests=request.form.get("interests","").strip(); s.target_role=request.form.get("target_role","Full-Stack Developer")

        s.github_username=request.form.get("github_username","").strip()

        s.github_profile_url=request.form.get("github_profile_url","").strip()

        s.preferred_types=",".join(request.form.getlist("preferred_types"))

        try: s.learning_hours=max(1,min(40,int(request.form.get("learning_hours",5))))

        except ValueError: s.learning_hours=5

        db.session.commit(); make_roadmap(s); flash("Profile saved and roadmap refreshed.","success"); return redirect(url_for("profile"))

    verified_skills=SkillVerification.query.filter_by(student_id=s.id,status="verified").order_by(SkillVerification.created_at.desc()).all()

    return render_template("profile.html",s=s,roles=roles,types=types,verified_skills=verified_skills)



@app.get("/skill-verification/<skill>")

@login_required

@role_required("student")

def skill_test(skill):

    if skill not in ROLE_SKILLS and skill not in {x for v in ROLE_SKILLS.values() for x in v}:

        abort(404)

    qs=questions_for(skill)

    return render_template("skill_test.html",skill=skill,questions=qs)



@app.post("/skill-verification/<skill>/test")

@login_required

@role_required("student")

def submit_skill_test(skill):

    qs=questions_for(skill); score=sum(1 for i,q in enumerate(qs) if request.form.get(f"q{i}") is not None and int(request.form.get(f"q{i}"))==q[2])

    percent=round(score/len(qs)*100)

    status="verified" if percent>=70 else "failed"

    db.session.add(SkillVerification(student_id=student_record().id,skill=skill,method="test",status=status,score=percent))

    db.session.commit()

    if status=="verified":

        task=RoadmapTask.query.filter_by(student_id=student_record().id,skill=skill).first()

        if task: task.completed=True

        db.session.commit()

        flash(f"{skill} verified through the AI-generated assessment ({percent}%).","success")

    else: flash(f"Assessment completed: {percent}%. Score 70% or higher to verify {skill}.","warning")

    return redirect(url_for("profile"))



@app.post("/skill-verification/certificate")

@login_required

@role_required("student")

def certificate_upload():

    skill=request.form.get("skill","").strip()

    f=request.files.get("certificate")

    if not skill or not f or not f.filename: flash("Choose a skill and certificate file.","error"); return redirect(url_for("profile"))

    ext=f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""

    if ext not in ALLOWED_CERTIFICATES: flash("Allowed certificate files: PDF, PNG, JPG, JPEG or WEBP.","error"); return redirect(url_for("profile"))

    filename=f"{student_record().id}_{int(datetime.utcnow().timestamp())}_{secure_filename(f.filename)}"

    f.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))

    db.session.add(SkillVerification(student_id=student_record().id,skill=skill,method="certificate",status="verified",certificate_file=filename))

    task=RoadmapTask.query.filter_by(student_id=student_record().id,skill=skill).first()

    if task: task.completed=True

    db.session.commit()

    flash(f"{skill} marked verified from the uploaded certificate.","success")

    return redirect(url_for("profile"))



@app.get("/certificate/<int:verification_id>")

@login_required

@role_required("student")

def certificate(verification_id):

    v=SkillVerification.query.get_or_404(verification_id)

    if v.student_id!=student_record().id or not v.certificate_file: abort(403)

    return send_from_directory(app.config["UPLOAD_FOLDER"],v.certificate_file,as_attachment=False)



@app.route("/roadmap")

@login_required

@role_required("student")

def roadmap():

    s=student_record(); make_roadmap(s)

    tasks=RoadmapTask.query.filter_by(student_id=s.id).order_by(RoadmapTask.order_no,RoadmapTask.id).all()

    return render_template("roadmap.html",s=s,tasks=tasks,gaps=gaps_for(s))



@app.post("/task/<int:task_id>/toggle")

@login_required

@role_required("student")

def toggle(task_id):

    t=RoadmapTask.query.get_or_404(task_id)

    if t.student_id!=student_record().id: abort(403)

    t.completed=not t.completed; db.session.commit(); flash("Progress updated.","success")

    return redirect(request.referrer or url_for("roadmap"))



@app.route("/opportunities")

@login_required

@role_required("student")

def opportunities():

    s=student_record(); kind=request.args.get("type",""); level=request.args.get("level","")

    maybe_sync_official_internships()

    create_internship_notifications(s)

    q=Opportunity.query

    if kind: q=q.filter_by(kind=kind)

    results=[]

    for o in q.all():

        score,matched,missing,why=score_for(s,o)

        if level=="some" and score==0: continue

        if level=="strong" and score<30: continue

        results.append((o,score,matched,missing,why))

    results.sort(key=lambda x:x[1],reverse=True)

    return render_template("opportunities.html",results=results,types=["Internship","Hackathon","Competition","Project","Course"],selected_type=kind,selected_level=level)



@app.get("/internship-notifications")

@login_required

@role_required("student")

def internship_notifications():

    s=student_record()

    maybe_sync_official_internships()

    create_internship_notifications(s)

    notices=InternshipNotification.query.filter_by(student_id=s.id).order_by(InternshipNotification.created_at.desc()).limit(30).all()

    for n in notices: n.seen=True

    db.session.commit()

    return render_template("internship_notifications.html",notices=notices)



@app.post("/internship-notifications/read")

@login_required

@role_required("student")

def mark_internship_notifications_read():

    s=student_record()

    InternshipNotification.query.filter_by(student_id=s.id,seen=False).update({"seen":True})

    db.session.commit()

    return redirect(request.referrer or url_for("index"))



@app.route("/company/dashboard",methods=["GET","POST"])

@login_required

@role_required("company")

def company_dashboard():

    c=current_user().company

    if request.method=="POST":

        title=request.form.get("title","").strip()

        if not title: flash("Opportunity title is required.","error")

        else:

            o=Opportunity(title=title,kind=request.form.get("kind","Internship"),description=request.form.get("description",""),skills=request.form.get("skills",""),eligibility=request.form.get("eligibility",""),deadline=request.form.get("deadline","Not specified"),location=request.form.get("location","Online"),source_name=c.company_name,source_url=c.website,is_sample=False,company_id=c.id)

            db.session.add(o); db.session.commit(); flash("Opportunity published for students.","success")

        return redirect(url_for("company_dashboard"))

    return render_template("company_dashboard.html",company=c,opportunities=Opportunity.query.filter_by(company_id=c.id).order_by(Opportunity.id.desc()).all())



@app.post("/company/opportunity/<int:opportunity_id>/delete")

@login_required

@role_required("company")

def delete_opportunity(opportunity_id):

    o=Opportunity.query.get_or_404(opportunity_id)

    if o.company_id!=current_user().company.id: abort(403)

    db.session.delete(o); db.session.commit(); flash("Opportunity removed.","success")

    return redirect(url_for("company_dashboard"))



@app.post("/refresh")

@login_required

@role_required("student")

def refresh():

    s=student_record(); make_roadmap(s)

    added,failed=maybe_sync_official_internships(force=True)

    create_internship_notifications(s)

    if failed:

        flash(f"Recommendations refreshed. Added {added} live internship listing(s); some official career sources could not be read right now.","warning")

    else:

        flash(f"Recommendations refreshed. Checked official career sources and added {added} new internship listing(s).","success")

    return redirect(url_for("index"))



@app.get("/health")

def health(): return {"status":"ok","app":"Aspirly"}



with app.app_context():

    db.create_all()

    migrate_old_schema()

    seed()



if __name__=="__main__":

    app.run(debug=True)
