"""
GitHub API client.
Week 2: Fetch PR diff and post review comments.
"""

import os
import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.diff",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def fetch_pr_diff(diff_url: str) -> str:
    """
    Fetch the raw diff content of a PR.
    diff_url looks like: https://github.com/owner/repo/pull/1.diff
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(diff_url, headers=HEADERS, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"[github_client] Failed to fetch diff: {response.status_code}")
            return ""
        
        print("[github_client] Diff fetched successfully")
        return response.text


async def post_pr_comment(repo_full_name: str, pr_number: int, comment: str) -> bool:
    """
    Post a comment on a GitHub PR.
    repo_full_name looks like: owner/repo
    """
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json={"body": comment},
        )
        
        if response.status_code == 201:
            print("[github_client] Comment posted successfully")
            return True
        else:
            print(f"[github_client] Failed to post comment: {response.status_code}")
            return False