# ASPIRLY — Multi-user Student + Company Career Platform

Updated hackathon prototype with separate student and company accounts, password management, skill verification, and company opportunity publishing.

## What's new

### 1. Multi-user authentication
- Every account has a unique email address and password.
- Student and Company account types are selected during registration.
- Login routes each account to its own workspace.
- Passwords are stored as secure password hashes, not plain text.
- Students only see/edit their own profile, roadmap and skill verification data.
- Companies only manage their own opportunity listings.
- Settings includes **Change Password**.
- Existing single-profile databases are migrated to a temporary account:
  - Email: `migrated@aspirly.local`
  - Password: `ChangeMe123!`
  - Change this password immediately after first login.

### 2. Student skill verification
Students can verify a skill in two ways:
- **AI-generated assessment:** a skill-specific short test is generated from the built-in assessment question bank. A score of 70%+ marks the skill as verified.
- **Certificate upload:** PDF/JPG/PNG/WEBP certificate upload is stored against the student's account and marks the selected skill as verified in this demo workflow.

Verified skills are included when calculating skill gaps and opportunity matches.

### 3. Company workspace
Company accounts get a separate dashboard where they can:
- Publish internships, projects, courses, hackathons and competitions.
- Specify required skills, eligibility, deadline and location.
- See their own published listings.
- Delete their own listings.

Students see company-created opportunities alongside the existing clearly-labelled sample opportunities.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

SQLite is used automatically for local development. PostgreSQL/Neon works through `DATABASE_URL`.

## Deploy on Render + Neon

Build command:
```text
pip install -r requirements.txt
```

Start command:
```text
gunicorn app:app
```

Environment variables:
- `DATABASE_URL` = Neon PostgreSQL connection string
- `SECRET_KEY` = long random secret

Never commit database credentials or uploaded certificates to GitHub.

## Demo flow

1. Open **Create account**.
2. Create a Student account with one email.
3. Complete the profile.
4. Open **My profile → Skill verification center**.
5. Take a skill test or upload a completed certificate.
6. Verified skills reduce the displayed skill gaps and improve opportunity matching.
7. Log out.
8. Create a separate Company account with another email.
9. Publish an opportunity from the Company dashboard.
10. Log out and return to the Student account to see the company opportunity.

## Important production notes

This is a hackathon/demo implementation. For production deployment, certificate verification should be reviewed by a company/admin or verified against the issuing institution rather than automatically trusting an uploaded file. Add CSRF protection, rate limiting, email verification, password reset, malware scanning for uploads, secure object storage, and stronger authorization/privacy controls before real-world use.


## AspirlyAI 2.0 — Web-aware AI career agent

AspirlyAI now supports a retrieval + generation flow instead of relying only on predefined TF-IDF responses. It can search public web results, fetch readable page text, combine that evidence with the logged-in student's ASPIRLY profile/roadmap, and ask an open-weight chat model to synthesize a personalized answer.

### Environment variables
- `OPENROUTER_API_KEY` — OpenRouter token with Inference Providers permission.
- `ASPIRLYAI_MODEL` — optional model override. Default: `openrouter/free`.

The app uses the OpenRouter OpenAI-compatible chat endpoint and does not require the OpenAI Python package. If `OPENROUTER_API_KEY` is absent or inference is temporarily unavailable, AspirlyAI falls back to its local guidance engine. Web retrieval is best-effort because some public sites block automated requests or render content only with JavaScript.
