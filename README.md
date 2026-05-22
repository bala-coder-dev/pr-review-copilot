# PR Review Copilot 🤖

An automated Pull Request review bot that uses AI to analyze code changes 

and post structured review comments directly on GitHub PRs.

Built to demonstrate real-world GitHub integration, webhook architecture, 

and practical LLM usage in a developer tooling context.

## What It Does

When a developer opens a Pull Request:

1. GitHub sends a webhook event to this server
2. Server fetches the PR diff (what code changed)
3. Diff is parsed and sent to an LLM (Groq / Llama3)
4. AI generates a structured code review
5. Review is posted automatically as a GitHub PR comment

# Tech Stack

| Layer | Technology |

| Backend | Python + FastAPI |

| AI / LLM | Groq API (Llama3-70b) |

| GitHub Integration | GitHub Webhooks + PyGithub|

| Code Parsing | tree-sitter |

| Database | SQLite + SQLAlchemy |

| Deployment | [Render.com](http://Render.com) |

# System Architecture

                GitHub PR Opened 

```
               ↓
```

           Webhook → FastAPI Server 

```
               ↓ 
```

      Signature Verification (HMAC-SHA256)

```
               ↓ 
```

            Fetch PR Diff (GitHub API) 

```
               ↓ 
```

        Parse Changed Code (tree-sitter) 

```
               ↓ 
```

   Send to Groq AI → Structured Review 

```
               ↓
```

        Post Comment on GitHub PR



