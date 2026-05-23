"""
Groq AI integration.
Week 2: Send PR diff to Groq and get structured code review.
"""

import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY)

REVIEW_PROMPT = """You are a senior software engineer doing a code review.
Analyze the following code diff and provide a structured review.

Your review must include:
1. 🐛 BUGS - Any bugs or errors you found
2. ⚡ IMPROVEMENTS - Code quality improvements
3. ✅ GOOD PARTS - What was done well
4. 📊 SCORE - Overall score out of 10

Be specific and mention line numbers where possible.
Keep your review clear and helpful for a junior developer.

CODE DIFF:
{diff}
"""


async def review_code(diff: str) -> str:
    if not diff:
        return "No diff content found to review."

    if len(diff) > 8000:
        diff = diff[:8000] + "\n... (diff truncated for length)"

    try:
        print("[ai_reviewer] Sending diff to Groq AI...")

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": REVIEW_PROMPT.format(diff=diff),
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1000,
        )

        review = chat_completion.choices[0].message.content
        print("[ai_reviewer] Review received from Groq AI")
        return review

    except Exception as e:
        print(f"[ai_reviewer] Groq API error: {e}")
        return f"AI review failed: {str(e)}"