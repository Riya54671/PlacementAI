SEARCH_QUERY_PROMPT = """
You are a job search assistant helping an Indian CS student find 
off-campus internships with PPO (Pre-Placement Offer).

Skills: {skills}
Role type: {role_type}
Seniority: {seniority}
Previously searched (avoid repeating): {previous_searches}

Generate 8 search queries that will ONLY find actual job listings,
not articles, blogs or tutorials.

USE THESE EXACT FORMATS:

Format A — Direct apply pages on job boards:
site:wellfound.com/jobs "intern" "react" OR "node.js" OR "python"
site:cutshort.io "internship" "backend" OR "full stack" india
site:internshala.com/internship "react" OR "node" OR "python" 2025

Format B — Specific funded Indian startups careers pages:
"[company] careers" internship 2025 apply now
Use companies: Groww, CRED, PhonePe, Zepto, Meesho, Swiggy, 
Razorpay, BrowserStack, Postman, Freshworks, Juspay, Setu,
Hasura, Chargebee, Clevertap, Darwinbox, Leadsquared,
Unacademy, Vedantu, Byju's, Cashfree, Perfios

Format C — LinkedIn job listings only:
site:linkedin.com/jobs "software engineer intern" india 2025
site:linkedin.com/jobs "backend intern" "node.js" OR "python" india

Format D — Naukri specific:
site:naukri.com "react developer" intern fresher apply 2025
site:naukri.com "java developer" internship ppo india

STRICT RULES:
- Every query must target ONLY job listing pages
- Include "2025" or "2026" in every query for freshness
- Include "apply" or "intern" or "internship" in every query
- Never generate queries that could return tutorials or articles
- Rotate companies — never repeat the same company twice
- Focus on product companies, NOT service companies

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