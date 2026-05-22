"""
GitHub webhook receiver.

Week 1: verify signature, log PR title / author / diff URL on pull_request opened.
"""

import hashlib
import hmac
import json
import os

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def verify_github_signature(payload_body: bytes, signature_header: str | None) -> None:
    """
    GitHub signs every webhook with HMAC-SHA256.
    Header format: X-Hub-Signature-256: sha256=<hex>
    """
    if not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_WEBHOOK_SECRET is not set. Add it to your .env file.",
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


def log_pr_opened(pull_request: dict) -> None:
    title = pull_request.get("title", "(no title)")
    author = pull_request.get("user", {}).get("login", "(unknown)")
    diff_url = pull_request.get("diff_url", "(no diff_url)")

    print("\n" + "=" * 60)
    print("  PR OPENED - PR Review Copilot")
    print("=" * 60)
    print(f"  Title:    {title}")
    print(f"  Author:   {author}")
    print(f"  Diff URL: {diff_url}")
    print("=" * 60 + "\n")


@router.post("/webhook")
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    # Raw bytes are required for signature verification (must match GitHub's input).
    body = await request.body()
    verify_github_signature(body, x_hub_signature_256)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    # GitHub sends "ping" when you first save the webhook — acknowledge it.
    if x_github_event == "ping":
        print("[webhook] GitHub ping received — webhook is connected.")
        return {"status": "pong"}
    print(f"[debug] event={x_github_event} action={payload.get('action')}")
    if x_github_event == "pull_request" and payload.get("action") in ["opened", "reopened"]:
        pull_request = payload.get("pull_request")
        if pull_request:
            log_pr_opened(pull_request)

    return {"status": "received", "event": x_github_event}
