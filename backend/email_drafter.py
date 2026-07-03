# email_drafter.py — Groq writes a personalised cold email
# uses the bigger model since writing quality matters here
# only called when you click "Send cold email" on a job

import os
import json
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
from prompts import EMAIL_DRAFT_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ─── DRAFT COLD EMAIL ─────────────────────────────────────

def draft_cold_email(
    candidate_name: str,
    skills: list,
    background: str,
    recruiter_name: str,
    company: str,
    role: str,
    stack: list,
    description: str = ""
) -> Optional[dict]:
    """
    Generate a personalised cold email for a specific job + recruiter
    returns {"subject": ..., "body": ...}
    """
    try:
        prompt = EMAIL_DRAFT_PROMPT.format(
            candidate_name=candidate_name,
            skills=", ".join(skills),
            background=background,
            recruiter_name=recruiter_name,
            company=company,
            role=role,
            stack=", ".join(stack) if stack else "not specified",
            description=description or "not available"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # better writing quality
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7  # a bit of creativity for natural tone
        )

        result = response.choices[0].message.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()

        # extract just the JSON portion in case of extra text
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            result = result[start:end]

        data = json.loads(result)

        subject = data.get("subject", f"{role} at {company}")
        body = data.get("body", "")

        print(f"✅ Email drafted for {recruiter_name} at {company}")
        return {"subject": subject, "body": body}

    except Exception as e:
        print(f"❌ Email drafting failed: {e}")
        return None


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing email_drafter.py...\n")

    result = draft_cold_email(
        candidate_name="Riya Sharma",
        skills=["React", "Node.js", "Python", "PostgreSQL"],
        background="3rd year CS student, built a full-stack expense tracker "
                    "and contributed to 2 open source projects",
        recruiter_name="Shobana K",
        company="Razorpay",
        role="Full Stack Development Intern",
        stack=["React", "Node.js", "MongoDB"],
        description="Building payment infrastructure for Indian businesses"
    )

    if result:
        print(f"\n--- Subject ---")
        print(result["subject"])
        print(f"\n--- Body ---")
        print(result["body"])
    else:
        print("\n❌ Drafting failed")