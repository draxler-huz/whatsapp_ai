import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# Supported Google Generative Language models in priority order.
# Stable models first, then the "latest" alias, then preview models as fallback.
GOOGLE_MODELS = [
    "models/gemini-3.8-flash",
    "models/gemini-flash-latest",
    "models/gemini-3-flash-preview",
    "models/gemini-3.1-pro-preview",
]

def call_google_api(prompt: str, api_key: str) -> str:
    """
    Calls Google's native Generative Language API using the user's Google API Key.
    Includes automatic fallback across available models.
    """
    payload = json.dumps({
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }).encode("utf-8")

    last_error = None
    for model in GOOGLE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            last_error = f"HTTP {e.code} on {model}: {err_body}"
            # If 404, 429, or 503, try next model in the list
            continue
        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"Google API call failed: {last_error}")

def call_openai_api(prompt: str, api_key: str) -> str:
    """Calls OpenAI API if user provides an OpenAI key."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def format_announcement(raw_text: str, template: str = "General") -> str:
    """
    Takes messy notes/instructions and turns them into a clean, 
    professional WhatsApp announcement with bold text and emojis.
    
    Supports Google API Key (primary) and OpenAI API Key.
    """
    if not raw_text or not raw_text.strip():
        return ""

    # Check for Google API Key
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # If Google key was pasted into OPENAI_API_KEY
    if openai_key and (openai_key.startswith("AQ.") or openai_key.startswith("AIza")):
        google_key = openai_key
        openai_key = None

    template_tones = {
        "General": "A professional, clear, and well-balanced announcement.",
        "Meeting Reminder": "Urgent and punctual tone emphasizing date, time, meeting link/room, agenda, and required preparation.",
        "Urgent Alert": "High-priority alert style with eye-catching warning emojis (🚨, ⚠️), immediate action items, and clear deadlines.",
        "Casual Event": "Warm, engaging, fun, and friendly tone for social gatherings, celebrations, or team offsites.",
        "Project Update": "Structured status report with key milestones, current progress, blockers, and next sprint goals."
    }
    tone_instruction = template_tones.get(template, template_tones["General"])

    prompt = f"""
You are an expert corporate communications assistant. Transform the following raw notes, 
instructions, or casual text into a professional, engaging WhatsApp announcement.

Target Context / Style: {tone_instruction}

Rules for formatting:
- Use *bold text* for headers, titles, and key points (WhatsApp bold format uses single asterisks: *Title*).
- Use _italics_ sparingly for dates, times, or secondary notes if appropriate.
- Add relevant, professional emojis to make it lively, readable, and easy to scan.
- Structure it cleanly with:
  1. A clear, catchy Title/Header
  2. Bullet points (using emojis or hyphens) for specific details
  3. A clear Call-to-Action (CTA) or Next Step
- Keep it concise, high-impact, and ready to send directly to a WhatsApp group.
- Do NOT use Markdown headings like '#', '##', or markdown link syntax '[link](url)'. Keep it native WhatsApp text.

Raw Input:
{raw_text}
"""

    if google_key and google_key.strip() and not google_key.startswith("your_"):
        return call_google_api(prompt, google_key.strip())

    if openai_key and openai_key.strip() and not openai_key.startswith("your_"):
        return call_openai_api(prompt, openai_key.strip())

    raise ValueError(
        "No API key configured! Please open your .env file and set GOOGLE_API_KEY."
    )

if __name__ == "__main__":
    sample = "Tell everyone the staging server will be down for maintenance tonight from 11 PM to 1 AM UTC"
    print("Testing AI Agent with Google API Key...")
    try:
        res = format_announcement(sample)
        print("Success! Generated announcement length:", len(res))
    except Exception as err:
        print(f"Error: {err}")
