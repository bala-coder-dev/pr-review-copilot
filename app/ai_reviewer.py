"""
Groq AI integration.
Send PR diff to Groq and get structured code review.
"""

import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY)

REVIEW_PROMPT = """You are a senior software engineer with 10+ years of experience doing a thorough code review.

Analyze the following code diff carefully and provide a detailed, structured review.

Your review MUST follow this exact format:

## 🐛 BUGS & ERRORS
List any bugs, logic errors, null pointer risks, or incorrect implementations.
If none found, write: "No bugs detected."

## 🔒 SECURITY ISSUES
List any security vulnerabilities, injection risks, exposed secrets, or unsafe practices.
If none found, write: "No security issues detected."

## ⚡ PERFORMANCE
List any performance bottlenecks, inefficient loops, unnecessary database calls, or memory issues.
If none found, write: "No performance issues detected."

## 📝 CODE QUALITY
List improvements for readability, naming conventions, code duplication, and best practices.

## ✅ WHAT'S DONE WELL
List specific things the developer did correctly or impressively.

## 💡 SUGGESTIONS
List 2-3 concrete, actionable suggestions the developer should implement.

## 📊 SCORE: X/10
Give an overall score out of 10. Be honest and strict.
Format exactly as: 📊 SCORE: 7/10

Scoring guide:
9-10: Exceptional code, production ready
7-8: Good code with minor improvements needed
5-6: Average code with several issues
3-4: Poor code with major issues
1-2: Needs complete rewrite

CODE DIFF TO REVIEW:
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
            max_tokens=1500,
        )

        review = chat_completion.choices[0].message.content
        print("[ai_reviewer] Review received from Groq AI")
        return review

    except Exception as e:
        print(f"[ai_reviewer] Groq API error: {e}")
        return f"AI review failed: {str(e)}"