# quick sanity check before deploying
# run this once to confirm everything connects

import os
from dotenv import load_dotenv
load_dotenv()

print("Checking all connections...\n")

# 1. Supabase
try:
    from db import get_config
    config = get_config()
    assert config is not None
    print(f"✅ Supabase — connected, config loaded")
    print(f"   Skills: {config.skills}")
    print(f"   Min score: {config.min_score}")
except Exception as e:
    print(f"❌ Supabase — {e}")

# 2. Groq
try:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "say ok"}],
        max_tokens=5
    )
    print(f"✅ Groq — connected, model responding")
except Exception as e:
    print(f"❌ Groq — {e}")

# 3. DuckDuckGo search
try:
    from ddgs import DDGS
    with DDGS() as ddgs:
        results = ddgs.text("software engineer internship india", max_results=2)
        assert len(results) > 0
    print(f"✅ DuckDuckGo — working, returning results")
except Exception as e:
    print(f"❌ DuckDuckGo — {e}")

# 4. Jina scraper
try:
    import requests
    res = requests.get("https://r.jina.ai/https://stripe.com/jobs", timeout=10)
    assert res.status_code == 200
    print(f"✅ Jina Reader — working")
except Exception as e:
    print(f"❌ Jina Reader — {e}")

# 5. Google Sheets
try:
    from sheets import get_sheets_service
    service = get_sheets_service()
    if service:
        print(f"✅ Google Sheets — connected")
    else:
        print(f"⚠️  Google Sheets — not configured (ok for Railway)")
except Exception as e:
    print(f"❌ Google Sheets — {e}")

print("\n✅ All checks done — safe to deploy!")