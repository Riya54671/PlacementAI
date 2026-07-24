SEARCH_QUERY_PROMPT = """
You are a job search assistant helping an Indian CS student find 
off-campus internships with PPO.

Skills: {skills}
Role type: {role_type}  
Seniority: {seniority}
Previously searched (avoid repeating): {previous_searches}

Generate exactly 8 search queries. Mix these strategies:

STRATEGY A — Known job boards (2 queries):
site:wellfound.com/jobs "intern" "react" OR "node" OR "python" india
site:cutshort.io "internship" "backend" OR "full stack" india 2026

STRATEGY B — Funded Indian startups you haven't searched before (3 queries):
Pick from: Groww, CRED, PhonePe, Zepto, Meesho, Razorpay, Juspay,
Setu, BrowserStack, Postman, Freshworks, Chargebee, Hasura, Clevertap,
Darwinbox, Sarvam AI, Krutrim, Purplle, Cashfree, Perfios,
Sprinklr, LeadSquared, Unacademy, Vedantu, upGrad, Byju's,
Slice, Jupiter, Jar, Fi Money, Smallcase, Streak, Weekday,
Fueler, Superset, Reelo, Toplyne, Hyperface, Decentro
Format: "[company] software engineering intern 2026 apply now"

STRATEGY C — YC and funded startups broadly (2 queries):
"YC startup" OR "Y Combinator" India software intern 2026 apply
"seed funded" OR "series A" India tech startup intern backend react

STRATEGY D — LinkedIn fresh listings (1 query):
site:linkedin.com/jobs "software engineer intern" india 2026 -senior -lead

STRICT RULES:
- Include "intern" OR "internship" OR "fresher" in EVERY query
- Include "2026" in every query for freshness
- Never repeat companies from previous searches
- Rotate Strategy B companies every run
- Do not put the same application link with different company names 
- Check for duplicate urls and strict check for experience level, the experience level should be 0-2 years 

Return JSON only — no explanation, just the JSON:
{{"queries": ["query1", "query2", "query3", "query4", "query5", "query6", "query7", "query8"]}}
"""

EXTRACTION_PROMPT = """
You are a job listing parser. You must respond with ONLY valid JSON.
Do not write Python code. Do not write explanations. Do not write 
regex. Output raw JSON and nothing else — no markdown fences, no 
commentary, no code.

Extract structured data from this raw text scraped from a 
career page or job board. The text may be messy — extract 
what you can, use null for missing fields.

Raw text:
{raw_text}

Your entire response must be ONLY this JSON structure, nothing else:
{{
  "company": "company name",
  "role": "exact job title",
  "stack": ["tech1", "tech2"],
  "deadline": "date string or null",
  "url": "direct apply URL or null",
  "description": "2 sentence summary"
  "experience":"experience"
}}

If this page contains multiple job listings, return a JSON array
of objects with the same structure.
if the experience is greater than 1 year then skip it 

If this is not a job listing at all, respond with exactly:
{{"skip": true}}

Remember: respond with ONLY the JSON. No code, no regex, no explanation.
"""


# ─── SCORING ─────────────────────────────────────────────
SCORING_PROMPT = """
Score this job for a candidate with these details:

CANDIDATE PROFILE
Skills: {skills}
Looking for: {role_type}
Seniority: {seniority}

JOB DETAILS
Company: {company}
Role: {role}
Tech stack: {stack}
Description: {description}

PRE-SCREENING RULES (check these first, they override everything):
1. If the role requires 2+ years of experience → score = 2, stop
2. If the role title has "Senior/Staff/Lead/Principal/Manager" → score = 2, stop  
3. If it's clearly a non-tech role (sales, marketing, HR) → score = 1, stop
4. If the company is a pure service/outsourcing company (Infosys, TCS, Wipro, Accenture, Capgemini) → score = 2, stop

Only if none of the above apply, continue scoring:

SKILLS MATCH (4 points)
- Strong match (3+ skills overlap) → 4 pts
- Partial match (1-2 skills overlap) → 2 pts
- No overlap → 0 pts

ROLE TYPE (3 points)
- Internship with PPO mentioned → 3 pts
- Internship (PPO not mentioned) → 2 pts
- Fresher / entry level (0-1 yrs) → 2 pt

COMPANY QUALITY (2 points)
- Well known / funded / product company → 2 pts
- Mid tier / unknown startup → 2 pt
- Service company → 0 pts

BONUS (1 point)
- PPO explicitly mentioned → +0.5
- Fintech / AI / devtools / SaaS → +0.5

Return JSON only:
{{
  "score": 8,
  "reason": "strong React+Node match, internship with PPO, funded startup",
  "urgent": false
}}
"""

# ─── DUPLICATE CHECK ─────────────────────────────────────
DUPLICATE_CHECK_PROMPT = """
Check if this new job is the same as any existing job.

New job: {new_job}

Existing jobs:
{existing_jobs}

A duplicate means same company + same role + application url (ignore minor 
title differences like "Engineer" vs "Developer").

Return JSON only:
{{"is_duplicate": true}} or {{"is_duplicate": false}}
"""

# ─── COLD EMAIL DRAFT ────────────────────────────────────
EMAIL_DRAFT_PROMPT = """
Write a short, personalised cold email from a candidate 
to a recruiter about a specific job opening.

CANDIDATE
Name: {candidate_name}
Skills: {skills}
Background: {background}

RECRUITER
Name: {recruiter_name}
Company: {company}
Role they hire for: {role}

JOB
Role: {role}
Stack: {stack}
Description: {description}

RULES
- Maximum 150 words
- Sound human, not templated
- One specific line about the company that shows genuine interest
- Mention 2 relevant skills max
- End with a soft ask, not pushy
- Subject line should be specific, not generic

Return JSON only:
{{
  "subject": "email subject line",
  "body": "full email body"
}}
"""

# ─── LINKEDIN DM DRAFT ───────────────────────────────────
DM_DRAFT_PROMPT = """
Write a short LinkedIn DM from a candidate to a recruiter 
or employee at a company they want to work at.

CANDIDATE
Name: {candidate_name}
Skills: {skills}

PERSON
Name: {person_name}
Title: {person_title}
Company: {company}

JOB
Role: {role}

RULES
- Maximum 60 words
- Very casual and direct
- No fluff, get to the point fast
- Sound like a real person, not a bot
- One genuine reason you want to work there

Return JSON only:
{{"message": "the DM text"}}
"""

# ─── RECRUITER FINDER ────────────────────────────────────
RECRUITER_RANK_PROMPT = """
From this list of people at {company}, pick the best 2-3 
people for a fresher/intern to reach out to about a 
{role} position.

People:
{people_list}

Prefer: recruiters, talent acquisition, engineering managers,
HR, people who post about hiring.
Avoid: CEOs of large companies, very senior technical people.

Return JSON only:
{{
  "ranked": [
    {{"name": "...", "title": "...", "reason": "why reach out to them"}}
  ]
}}
"""