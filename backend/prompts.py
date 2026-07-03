SEARCH_QUERY_PROMPT = """
You are a job search assistant helping an Indian CS student
find off-campus internships with PPO opportunity.

Skills: {skills}
Role type: {role_type}
Seniority: {seniority}
Previously searched topics (avoid repeating these): {previous_searches}

Generate 8 DIVERSE search queries. Use a MIX of these strategies:

STRATEGY A — Direct company career pages:
"site:careers.stripe.com internship"
"site:careers.razorpay.com software intern"
"site:jobs.flipkart.com fresher"

STRATEGY B — Startup job boards:
"wellfound.com backend intern india 2025"
"cutshort.io react nodejs internship"
"instahyre.com software intern ppo"

STRATEGY C — Specific companies known for PPO:
"[company name] software engineering internship PPO 2025"
Use companies like: Groww, CRED, Meesho, PhonePe, Zepto, 
Swiggy, Zomato, Juspay, Setu, Postman, BrowserStack,
Freshworks, Zoho, Chargebee, Hasura, Clevertap

STRATEGY D — LinkedIn specific:
"site:linkedin.com/jobs intern {role_type} india react"
"site:linkedin.com/jobs fresher python node.js bangalore"

STRATEGY E — Naukri/job boards:
"naukri.com react nodejs internship ppo india"
"internshala.com full stack intern stipend ppo"

STRATEGY F — Google indexed career pages:
"intitle:careers intitle:internship react node python 2025 india"
"inurl:careers software engineering intern india ppo apply"

Rules:
- Use ALL 6 strategies, at least 1 query per strategy
- Never repeat a strategy twice in the same run
- Rotate companies in Strategy C — never use the same company twice
- Make queries specific, not generic
- Focus on Indian market and remote opportunities

Return JSON only:
{{"queries": ["query1", "query2", ...]}}
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
}}

If this page contains multiple job listings, return a JSON array
of objects with the same structure.

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

SCORING CRITERIA (total 10 points)


SKILLS MATCH (4 points)
- Strong match (3+ skills overlap) → 4 pts
- Partial match (1-2 skills overlap) → 2 pts  
- No overlap → 0 pts

ROLE TYPE (3 points)
- Internship with PPO mentioned → 3 pts
- Internship (PPO not mentioned) → 2 pts
- Fresher / entry level full-time (0-1 yrs) → 1 pt
- Mid-level (2-4 yrs required) → 0 pts
- Senior / Staff / Principal / Manager / Lead / 5+ yrs → 0 pts

HARD RULE: If the role title contains the word "Senior", "Staff", 
"Principal", "Lead", or "Manager", the maximum possible total score 
is 3, regardless of how well skills match. These are not appropriate 
for an internship-seeking junior candidate.

COMPANY QUALITY (2 points)
- Well known / funded / product company → 2 pts
- Mid tier / unknown startup → 1 pt
- Service company / body shop → 0 pts

BONUS (1 point)
- PPO explicitly mentioned → +0.5
- Fintech / AI / devtools / SaaS domain → +0.5
- Equity or ESOPs mentioned → +0.5
- Apply within 7 days → flag urgent

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

A duplicate means same company + same role (ignore minor 
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