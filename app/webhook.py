"""
GitHub webhook receiver.
Week 2: Fetch diff → Send to Groq AI → Post review comment on PR.
"""

import hashlib
import hmac
import json
import os

from fastapi import APIRouter, Header, HTTPException, Request

from app.github_client import fetch_pr_diff, post_pr_comment
from app.ai_reviewer import review_code

router = APIRouter()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def verify_github_signature(payload_body: bytes, signature_header: str | None) -> None:
    if not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_WEBHOOK_SECRET is not set.",
        )
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


def format_review_comment(review: str, pr_title: str, author: str) -> str:
    return f"""## 🤖 PR Review Copilot

**PR:** {pr_title}
**Author:** @{author}

---

{review}

---
*Automated review by PR Review Copilot using Groq AI*
"""


@router.post("/webhook")
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    body = await request.body()
    verify_github_signature(body, x_hub_signature_256)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if x_github_event == "ping":
        print("[webhook] GitHub ping received — webhook is connected.")
        return {"status": "pong"}

    print(f"[debug] event={x_github_event} action={payload.get('action')}")

    if x_github_event == "pull_request" and payload.get("action") in ["opened", "reopened"]:
        pull_request = payload.get("pull_request", {})
        repo = payload.get("repository", {})

        title = pull_request.get("title", "")
        author = pull_request.get("user", {}).get("login", "")
        diff_url = pull_request.get("diff_url", "")
        pr_number = pull_request.get("number", 0)
        repo_full_name = repo.get("full_name", "")

        print(f"\n{'='*60}")
        print(f"  PR OPENED - PR Review Copilot")
        print(f"{'='*60}")
        print(f"  Title:    {title}")
        print(f"  Author:   {author}")
        print(f"  Diff URL: {diff_url}")
        print(f"{'='*60}\n")

        # Step 1 - Fetch the diff
        diff = await fetch_pr_diff(diff_url)

        # Step 2 - Send to Groq AI
        review = await review_code(diff)

        # Step 3 - Post comment on GitHub PR
        comment = format_review_comment(review, title, author)
        await post_pr_comment(repo_full_name, pr_number, comment)

    return {"status": "received", "event": x_github_event}