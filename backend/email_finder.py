# email_finder.py — rewritten without Apollo
# uses DuckDuckGo (already proven working) + email pattern guessing
# completely free, no paid plan needed

from typing import Optional, List
from search import search_linkedin_profiles


# ─── GUESS COMPANY EMAIL DOMAIN ──────────────────────────

def guess_company_domain(company: str) -> str:
    """
    Most companies use their main domain for email
    simple heuristic — lowercase, remove spaces/special chars
    """
    domain = company.lower().strip()
    domain = domain.replace(" ", "").replace(",", "").replace(".", "")
    # remove common suffixes
    for suffix in ["inc", "llc", "ltd", "private", "limited", "pvt"]:
        domain = domain.replace(suffix, "")
    return f"{domain}.com"


# ─── PATTERN GUESS EMAIL ─────────────────────────────────

def guess_email_pattern(full_name: str, company_domain: str) -> Optional[str]:
    """
    Guess email using most common corporate pattern
    firstname.lastname@domain.com
    """
    if not full_name or not company_domain:
        return None

    parts = full_name.lower().strip().split()
    parts = [p for p in parts if p.isalpha()]  # remove junk tokens

    if len(parts) < 2:
        return None

    first, last = parts[0], parts[-1]
    return f"{first}.{last}@{company_domain}"


# ─── MAIN FUNCTION ────────────────────────────────────────

def find_recruiter_email(company: str, role: str = "", company_domain: str = None) -> Optional[dict]:
    """
    Full pipeline: find LinkedIn profile via DDG, guess their email
    prefers actual recruiters/talent acquisition over random employees
    """
    people = search_linkedin_profiles(company, role)

    if not people:
        print(f"   No recruiters found at {company}")
        return None

    if not company_domain:
        company_domain = guess_company_domain(company)

    # prefer people whose title mentions recruiting/talent acquisition
    priority_keywords = ["recruit", "talent acquisition", "hiring", "people"]

    best_match = None
    for person in people:
        title_lower = person.get("title", "").lower()
        if any(kw in title_lower for kw in priority_keywords):
            best_match = person
            break

    # fallback to first result if no clear recruiter found
    if not best_match:
        best_match = people[0]

    guessed_email = guess_email_pattern(best_match["name"], company_domain)

    return {
        "name": best_match["name"],
        "title": best_match["title"],
        "linkedin_url": best_match["linkedin_url"],
        "email": guessed_email,
        "email_guessed": True,
        "company": company
    }
# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing email_finder.py (DuckDuckGo version)...\n")

    test_company = "Razorpay"
    print(f"Searching for recruiters at {test_company}...\n")

    result = find_recruiter_email(test_company, "software engineer")

    if result:
        print(f"\n--- Result ---")
        print(f"Name:     {result.get('name')}")
        print(f"Title:    {result.get('title')}")
        print(f"LinkedIn: {result.get('linkedin_url')}")
        print(f"Email:    {result.get('email')} (guessed)")
    else:
        print("\n❌ No recruiter found")